from datetime import timedelta

from fastapi import APIRouter, Depends
from pymongo.errors import DuplicateKeyError

from ..db import db
from ..deps import TripCtx, current_user, organizer, trip_member
from ..errors import AppError
from ..ratelimit import limiter
from ..schemas import CATEGORIES, BudgetSaveIn, JoinIn, MemberPatch, TripIn, TripPatch
from ..security import new_invite_code, norm_code, sha
from ..services import ledger
from ..utils import audit, clean, now, oid

router = APIRouter(prefix="/trips", tags=["trips"])


def trip_out(trip):
    t = clean(trip)
    b = trip.get("budget")
    t["budget_stale"] = bool(b) and sum(b["categories"].values()) != trip["budget_total"]
    for k in ("start_date", "end_date", "deadline"):
        if t.get(k) is not None:
            t[k] = str(t[k])
    return t


def trip_card(trip, member):
    tid = str(trip["_id"])
    s = ledger.summary(tid)
    paid = ledger.paid_map(tid).get(member["user_id"], 0)
    return {
        **trip_out(trip),
        "role": member["role"],
        "my_target": member["target_amount"],
        "my_paid": paid,
        "verified": s["verified"],
        "member_count": db.trip_members.count_documents({"trip_id": tid, "status": "active"}),
    }


def issue_invite(tid):
    code = new_invite_code()
    expires = now() + timedelta(days=7)
    db.trips.update_one({"_id": oid(tid)}, {"$set": {"invite_hash": sha(norm_code(code)), "invite_expires_at": expires}})
    return code, expires


@router.post("", status_code=201)
def create_trip(body: TripIn, user=Depends(current_user)):
    doc = body.model_dump()
    for k in ("start_date", "end_date", "deadline"):
        doc[k] = doc[k].isoformat() if doc[k] else None
    uid = str(user["_id"])
    doc.update(owner_user_id=uid, status="active", budget=None, budget_history=[], version=1, created_at=now(), invite_hash=None)
    res = db.trips.insert_one(doc)
    tid = str(res.inserted_id)
    db.trip_members.insert_one(
        {"trip_id": tid, "user_id": uid, "role": "organizer", "target_amount": body.budget_total // body.group_size, "joined_at": now(), "status": "active"}
    )
    code, expires = issue_invite(tid)
    audit(tid, uid, "trip_created")
    trip = db.trips.find_one({"_id": res.inserted_id})
    return {"trip": trip_out(trip), "invite": {"code": code, "expires_at": expires.isoformat()}}


@router.get("")
def list_trips(user=Depends(current_user)):
    members = {m["trip_id"]: m for m in db.trip_members.find({"user_id": str(user["_id"]), "status": "active"})}
    docs = db.trips.find({"_id": {"$in": [oid(t) for t in members]}}).sort("created_at", -1)
    return [trip_card(t, members[str(t["_id"])]) for t in docs]


@router.post("/join")
def join(body: JoinIn, user=Depends(current_user), _=Depends(limiter("join", 10, 60))):
    trip = db.trips.find_one({"invite_hash": sha(norm_code(body.code))})
    if not trip:
        raise AppError("INVITE_INVALID", "Invite code not found or revoked", 404)
    if not trip.get("invite_expires_at") or trip["invite_expires_at"] < now():
        raise AppError("INVITE_EXPIRED", "This invite has expired", 410)
    if trip["status"] != "active":
        raise AppError("TRIP_NOT_ACTIVE", "This trip is not accepting members", 409)
    tid = str(trip["_id"])
    if db.trip_members.count_documents({"trip_id": tid, "status": "active"}) >= trip["group_size"]:
        raise AppError("TRIP_FULL", "This trip already has its full group", 409)
    uid = str(user["_id"])
    try:
        db.trip_members.insert_one(
            {"trip_id": tid, "user_id": uid, "role": "member", "target_amount": trip["budget_total"] // trip["group_size"], "joined_at": now(), "status": "active"}
        )
    except DuplicateKeyError:
        existing = db.trip_members.find_one({"trip_id": tid, "user_id": uid})
        if existing and existing["status"] == "removed":
            raise AppError("NOT_TRIP_MEMBER", "You were removed from this trip", 403)
        raise AppError("ALREADY_MEMBER", "You are already in this trip", 409)
    audit(tid, uid, "member_joined")
    return {"trip_id": tid}


@router.get("/{trip_id}")
def get_trip(ctx: TripCtx = Depends(trip_member)):
    return {**trip_out(ctx.trip), "my_user_id": ctx.uid, "role": ctx.member["role"], "my_target": ctx.member["target_amount"], "members": ledger.member_rows(ctx.trip)}


@router.patch("/{trip_id}")
def patch_trip(body: TripPatch, ctx: TripCtx = Depends(organizer)):
    data = body.model_dump(exclude_unset=True)
    if ctx.trip["status"] == "closed":
        raise AppError("TRIP_CLOSED", "Closed trips cannot be edited", 409)
    for k in ("start_date", "end_date", "deadline"):
        if data.get(k):
            data[k] = data[k].isoformat()
    if data:
        db.trips.update_one({"_id": ctx.trip["_id"]}, {"$set": data, "$inc": {"version": 1}})
        audit(ctx.tid, ctx.uid, "trip_edited", {"fields": list(data)})
    return trip_out(db.trips.find_one({"_id": ctx.trip["_id"]}))


@router.post("/{trip_id}/invites")
def rotate_invite(ctx: TripCtx = Depends(organizer)):
    code, expires = issue_invite(ctx.tid)
    audit(ctx.tid, ctx.uid, "invite_rotated")
    return {"code": code, "expires_at": expires.isoformat()}


@router.delete("/{trip_id}/invites", status_code=204)
def revoke_invite(ctx: TripCtx = Depends(organizer)):
    db.trips.update_one({"_id": ctx.trip["_id"]}, {"$set": {"invite_hash": None, "invite_expires_at": None}})
    audit(ctx.tid, ctx.uid, "invite_revoked")


@router.patch("/{trip_id}/members/{user_id}")
def set_target(user_id: str, body: MemberPatch, ctx: TripCtx = Depends(organizer)):
    if ctx.trip["status"] != "active":
        raise AppError("TRIP_NOT_ACTIVE", "Trip is not active", 409)
    res = db.trip_members.update_one({"trip_id": ctx.tid, "user_id": user_id, "status": "active"}, {"$set": {"target_amount": body.target_amount}})
    if not res.matched_count:
        raise AppError("NOT_FOUND", "Member not found", 404)
    audit(ctx.tid, ctx.uid, "target_changed", {"user_id": user_id, "target": body.target_amount})
    return {"user_id": user_id, "target_amount": body.target_amount}


@router.delete("/{trip_id}/members/{user_id}", status_code=204)
def remove_member(user_id: str, ctx: TripCtx = Depends(organizer)):
    if user_id == ctx.uid:
        raise AppError("CANNOT_REMOVE_ORGANIZER", "The organizer cannot be removed", 409)
    if ledger.paid_map(ctx.tid).get(user_id, 0) != 0:
        raise AppError("MEMBER_HAS_CONTRIBUTIONS", "Members with verified contributions cannot be removed", 409)
    res = db.trip_members.update_one({"trip_id": ctx.tid, "user_id": user_id, "status": "active"}, {"$set": {"status": "removed"}})
    if not res.matched_count:
        raise AppError("NOT_FOUND", "Member not found", 404)
    audit(ctx.tid, ctx.uid, "member_removed", {"user_id": user_id})


@router.delete("/{trip_id}/leave", status_code=204)
def leave(ctx: TripCtx = Depends(trip_member)):
    if ctx.is_organizer:
        raise AppError("CANNOT_REMOVE_ORGANIZER", "The organizer cannot leave", 409)
    if ledger.paid_map(ctx.tid).get(ctx.uid, 0) != 0:
        raise AppError("MEMBER_HAS_CONTRIBUTIONS", "Members with verified contributions cannot leave", 409)
    db.trip_members.update_one({"trip_id": ctx.tid, "user_id": ctx.uid}, {"$set": {"status": "left"}})


@router.post("/{trip_id}/budget")
def save_budget(body: BudgetSaveIn, ctx: TripCtx = Depends(organizer)):
    if ctx.trip["status"] != "active":
        raise AppError("TRIP_NOT_ACTIVE", "Trip is not active", 409)
    cats = body.categories
    if set(cats) != set(CATEGORIES) or any(v < 0 for v in cats.values()):
        raise AppError("BUDGET_INVALID", "Budget must contain every category with non-negative amounts", 422)
    if sum(cats.values()) != ctx.trip["budget_total"]:
        raise AppError("BUDGET_TOTAL_MISMATCH", "Category amounts must add up to the trip target", 422)
    version = len(ctx.trip.get("budget_history", [])) + 1
    entry = {"version": version, "categories": cats, "approved_by": ctx.uid, "approved_at": now()}
    db.trips.update_one({"_id": ctx.trip["_id"]}, {"$set": {"budget": entry}, "$push": {"budget_history": entry}, "$inc": {"version": 1}})
    audit(ctx.tid, ctx.uid, "budget_approved", {"version": version})
    return clean(entry)


@router.get("/{trip_id}/fund")
def fund(ctx: TripCtx = Depends(trip_member)):
    s = ledger.summary(ctx.tid)
    target = ctx.trip["budget_total"]
    return {
        "currency": ctx.trip["currency"],
        "target": target,
        "verified": s["verified"],
        "remaining": max(0, target - s["verified"]),
        "approved_spend": s["spend"],
        "available": s["available"],
        "progress_pct": min(100, round(s["verified"] * 100 / target)) if target else 0,
        "status": ctx.trip["status"],
        "members": ledger.member_rows(ctx.trip),
    }


@router.post("/{trip_id}/close")
def close_trip(ctx: TripCtx = Depends(organizer)):
    if ctx.trip["status"] == "closed":
        raise AppError("TRIP_CLOSED", "Trip is already closed", 409)
    pending = db.payment_orders.count_documents({"trip_id": ctx.tid, "state": "captured"})
    drafts = db.trip_expenses.count_documents({"trip_id": ctx.tid, "approval_status": "draft"})
    if pending or drafts:
        raise AppError("OUTSTANDING_ITEMS", "Resolve processing payments and draft expenses before closing", 409)
    db.trips.update_one({"_id": ctx.trip["_id"]}, {"$set": {"status": "closed", "closed_at": now(), "invite_hash": None}})
    audit(ctx.tid, ctx.uid, "trip_closed")
    return {"status": "closed"}

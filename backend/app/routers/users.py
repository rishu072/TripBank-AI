from fastapi import APIRouter, Depends

from ..db import db
from ..deps import current_user
from ..errors import AppError
from ..schemas import UserPatch
from ..security import hash_password, verify_password
from ..utils import clean, oid
from .auth import public_user
from .trips import trip_card
from ..services import ledger

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def me(user=Depends(current_user)):
    return public_user(user)


@router.patch("/me")
def patch_me(body: UserPatch, user=Depends(current_user)):
    data = body.model_dump(exclude_unset=True)
    upd = {k: data[k] for k in ("name", "avatar_url", "theme", "notifications") if k in data}
    if data.get("new_password"):
        if not data.get("current_password") or not verify_password(data["current_password"], user["password_hash"]):
            raise AppError("INVALID_CREDENTIALS", "Current password is incorrect", 401)
        upd["password_hash"] = hash_password(data["new_password"])
    ops = {"$set": upd}
    if "password_hash" in upd:
        ops["$inc"] = {"token_version": 1}
    if upd:
        db.users.update_one({"_id": user["_id"]}, ops)
    fresh = db.users.find_one({"_id": user["_id"]})
    out = public_user(fresh)
    if "password_hash" in upd:
        from ..security import create_token

        out["access_token"] = create_token(fresh)
    return out


@router.get("/me/dashboard")
def dashboard(user=Depends(current_user)):
    uid = str(user["_id"])
    members = list(db.trip_members.find({"user_id": uid, "status": "active"}))
    trips = {m["trip_id"]: m for m in members}
    docs = list(db.trips.find({"_id": {"$in": [oid(t) for t in trips]}}))
    cards = [trip_card(t, trips[str(t["_id"])]) for t in docs]
    names = {str(t["_id"]): t["name"] for t in docs}
    acts = db.ledger_entries.find({"trip_id": {"$in": list(trips)}}).sort("created_at", -1).limit(10)
    activity = []
    for a in acts:
        row = clean(a)
        row["trip_name"] = names.get(a["trip_id"], "")
        activity.append(row)
    return {"trips": cards, "activity": activity}

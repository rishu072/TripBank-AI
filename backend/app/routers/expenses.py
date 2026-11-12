from fastapi import APIRouter, Depends

from ..config import settings
from ..db import db
from ..deps import TripCtx, organizer, trip_member
from ..errors import AppError
from ..schemas import ExpenseIn, ExpensePatch
from ..services import ledger
from ..utils import audit, clean, now, oid

router = APIRouter(prefix="/trips/{trip_id}/expenses", tags=["expenses"])


def check_receipt(url):
    if url and not url.startswith(f"https://res.cloudinary.com/{settings.cloudinary_cloud_name}/"):
        raise AppError("RECEIPT_INVALID", "Receipt must be uploaded through TripBank", 422)


def out(e):
    d = clean(e)
    d["date"] = str(d["date"])
    return d


def find(ctx, expense_id):
    e = db.trip_expenses.find_one({"_id": oid(expense_id), "trip_id": ctx.tid})
    if not e:
        raise AppError("NOT_FOUND", "Expense not found", 404)
    return e


@router.post("", status_code=201)
def create(body: ExpenseIn, ctx: TripCtx = Depends(organizer)):
    if ctx.trip["status"] != "active":
        raise AppError("TRIP_NOT_ACTIVE", "Trip is not active", 409)
    check_receipt(body.receipt_url)
    doc = body.model_dump()
    doc["date"] = doc["date"].isoformat()
    doc.update(trip_id=ctx.tid, created_by=ctx.uid, currency=ctx.trip["currency"], approval_status="draft", created_at=now())
    res = db.trip_expenses.insert_one(doc)
    audit(ctx.tid, ctx.uid, "expense_created", {"expense_id": str(res.inserted_id)})
    return out(db.trip_expenses.find_one({"_id": res.inserted_id}))


@router.get("")
def list_expenses(ctx: TripCtx = Depends(trip_member)):
    q = {"trip_id": ctx.tid}
    if not ctx.is_organizer:
        q["approval_status"] = "approved"
    return [out(e) for e in db.trip_expenses.find(q).sort("date", -1)]


@router.patch("/{expense_id}")
def edit(expense_id: str, body: ExpensePatch, ctx: TripCtx = Depends(organizer)):
    e = find(ctx, expense_id)
    if e["approval_status"] != "draft":
        raise AppError("EXPENSE_LOCKED", "Approved expenses cannot be edited", 409)
    data = body.model_dump(exclude_unset=True)
    check_receipt(data.get("receipt_url"))
    if data.get("date"):
        data["date"] = data["date"].isoformat()
    if data:
        db.trip_expenses.update_one({"_id": e["_id"]}, {"$set": data})
        audit(ctx.tid, ctx.uid, "expense_edited", {"expense_id": expense_id, "fields": list(data)})
    return out(db.trip_expenses.find_one({"_id": e["_id"]}))


@router.patch("/{expense_id}/approve")
def approve(expense_id: str, ctx: TripCtx = Depends(organizer)):
    e = find(ctx, expense_id)
    if e["approval_status"] != "draft":
        raise AppError("DUPLICATE_EVENT", "Expense is already approved", 409)
    if e["amount"] > ledger.summary(ctx.tid)["available"]:
        raise AppError("INSUFFICIENT_BALANCE", "Approved spend cannot exceed the available balance", 409)
    db.trip_expenses.update_one({"_id": e["_id"]}, {"$set": {"approval_status": "approved", "approved_by": ctx.uid, "approved_at": now()}})
    ledger.post(ctx.tid, "expense", expense_id, -e["amount"], e["currency"], ctx.uid)
    audit(ctx.tid, ctx.uid, "expense_approved", {"expense_id": expense_id})
    return out(db.trip_expenses.find_one({"_id": e["_id"]}))

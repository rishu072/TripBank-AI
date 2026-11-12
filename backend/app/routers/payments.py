import uuid

from fastapi import APIRouter, Depends, Header, Query
from pymongo.errors import DuplicateKeyError

from ..config import settings
from ..db import db
from ..deps import TripCtx, current_user, trip_member
from ..errors import AppError
from ..ratelimit import limiter
from ..schemas import OrderIn
from ..services import ledger, paypal
from ..services.payments import UI_STATUS, settle
from ..utils import clean, now, oid

router = APIRouter(tags=["payments"])


@router.post("/trips/{trip_id}/payment-orders", status_code=201)
def create_order(
    body: OrderIn,
    ctx: TripCtx = Depends(trip_member),
    idem: str | None = Header(default=None, alias="Idempotency-Key"),
    _=Depends(limiter("orders", 20, 60)),
):
    if ctx.trip["status"] != "active":
        raise AppError("TRIP_NOT_ACTIVE", "This trip is not accepting contributions", 409)
    key = f"{ctx.uid}:{idem or uuid.uuid4()}"
    existing = db.payment_orders.find_one({"idempotency_key": key})
    if existing:
        return {"order_id": str(existing["_id"]), "provider_order_id": existing["provider_order_id"], "amount": existing["amount"], "currency": existing["currency"], "state": existing["state"]}
    paid = ledger.paid_map(ctx.tid).get(ctx.uid, 0)
    remaining = ctx.member["target_amount"] - paid
    if body.amount > settings.max_contribution_minor or body.amount > remaining:
        raise AppError("AMOUNT_INVALID", "Amount exceeds your remaining target", 400)
    doc = {
        "trip_id": ctx.tid,
        "member_id": ctx.uid,
        "provider": "paypal",
        "provider_order_id": None,
        "amount": body.amount,
        "currency": ctx.trip["currency"],
        "state": "created",
        "idempotency_key": key,
        "created_at": now(),
    }
    try:
        res = db.payment_orders.insert_one(doc)
    except DuplicateKeyError:
        raise AppError("DUPLICATE_EVENT", "Duplicate request", 409)
    local_id = str(res.inserted_id)
    try:
        provider_id = paypal.create_order(local_id, body.amount, doc["currency"], ctx.trip["name"])
    except AppError:
        db.payment_orders.update_one({"_id": res.inserted_id}, {"$set": {"state": "failed"}})
        raise
    db.payment_orders.update_one({"_id": res.inserted_id}, {"$set": {"provider_order_id": provider_id}})
    return {"order_id": local_id, "provider_order_id": provider_id, "amount": body.amount, "currency": doc["currency"], "state": "created"}


@router.post("/payments/{order_id}/capture")
def capture_order(order_id: str, user=Depends(current_user)):
    order = db.payment_orders.find_one({"_id": oid(order_id)})
    if not order or order["member_id"] != str(user["_id"]):
        raise AppError("NOT_ORDER_OWNER", "Order not found for this account", 403)
    if not order.get("provider_order_id"):
        raise AppError("ORDER_NOT_APPROVED", "Order was never created at the provider", 409)
    duplicate = settle(order)
    c = db.contributions.find_one({"order_id": order_id})
    return {
        "status": "posted",
        "duplicate": duplicate,
        "order_id": order_id,
        "amount": c["amount"],
        "currency": c["currency"],
        "provider_ref": c["provider_ref"],
        "captured_at": c["captured_at"].isoformat(),
    }


@router.get("/trips/{trip_id}/contributions")
def contributions(scope: str = Query("mine", pattern="^(mine|group)$"), ctx: TripCtx = Depends(trip_member)):
    if scope == "group":
        names = {r["user_id"]: r["name"] for r in ledger.member_rows(ctx.trip)}
        rows = db.contributions.find({"trip_id": ctx.tid}).sort("captured_at", -1)
        return {
            "contributions": [
                {"member": names.get(c["member_id"], "Member"), "amount": c["amount"], "currency": c["currency"], "status": "Refunded" if c["status"] == "reversed" else "Verified", "captured_at": c["captured_at"].isoformat()}
                for c in rows
            ],
            "orders": [],
        }
    rows = db.contributions.find({"trip_id": ctx.tid, "member_id": ctx.uid}).sort("captured_at", -1)
    orders = db.payment_orders.find({"trip_id": ctx.tid, "member_id": ctx.uid, "state": {"$ne": "posted"}}).sort("created_at", -1).limit(20)
    return {
        "contributions": [{**clean(c), "status": "Refunded" if c["status"] == "reversed" else "Verified"} for c in rows],
        "orders": [{"id": str(o["_id"]), "amount": o["amount"], "currency": o["currency"], "status": UI_STATUS.get(o["state"], "Pending"), "created_at": o["created_at"].isoformat()} for o in orders],
    }

import json

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool
from pymongo.errors import DuplicateKeyError

from ..db import db
from ..errors import AppError
from ..money import from_value
from ..services import paypal
from ..services.payments import reverse_contribution, settle
from ..utils import now

router = APIRouter(tags=["webhooks"])


def handle(event):
    kind = event.get("event_type")
    res = event.get("resource", {})
    if kind == "PAYMENT.CAPTURE.COMPLETED":
        pid = res.get("supplementary_data", {}).get("related_ids", {}).get("order_id")
        order = db.payment_orders.find_one({"provider_order_id": pid}) if pid else None
        if not order:
            return "unmatched"
        settle(order, paypal.get_order(pid))
        return "settled"
    if kind in ("PAYMENT.CAPTURE.REFUNDED", "PAYMENT.CAPTURE.REVERSED"):
        up = next((l["href"] for l in res.get("links", []) if l.get("rel") == "up"), "")
        capture_id = up.rstrip("/").split("/")[-1]
        amt = from_value(res["amount"]["value"]) if res.get("amount") else None
        done = reverse_contribution(capture_id, res.get("id", event["id"]), amt, kind)
        return "reversed" if done else "ignored"
    if kind == "PAYMENT.CAPTURE.DENIED":
        pid = res.get("supplementary_data", {}).get("related_ids", {}).get("order_id")
        db.payment_orders.update_one({"provider_order_id": pid, "state": {"$ne": "posted"}}, {"$set": {"state": "denied"}})
        return "denied"
    return "recorded"


def process(headers, raw):
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        raise AppError("WEBHOOK_INVALID", "Invalid payload", 400)
    if not paypal.verify_webhook(headers, event):
        raise AppError("WEBHOOK_INVALID", "Signature verification failed", 400)
    try:
        db.webhook_events.insert_one({"event_id": event["id"], "type": event.get("event_type"), "received_at": now()})
    except DuplicateKeyError:
        return {"status": "duplicate"}
    try:
        outcome = handle(event)
    except Exception:
        db.webhook_events.delete_one({"event_id": event["id"]})
        raise
    db.webhook_events.update_one({"event_id": event["id"]}, {"$set": {"outcome": outcome}})
    return {"status": outcome}


@router.post("/webhooks/paypal")
async def paypal_webhook(request: Request):
    raw = await request.body()
    return await run_in_threadpool(process, dict(request.headers), raw)

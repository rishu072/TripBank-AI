from pymongo.errors import DuplicateKeyError

from ..config import settings
from ..db import db
from ..errors import AppError
from ..money import from_value
from ..utils import audit, now
from . import ledger, paypal

UI_STATUS = {"created": "Pending", "captured": "Processing", "posted": "Verified", "failed": "Failed", "mismatch": "Failed", "denied": "Failed"}


def verify_payload(order, payload):
    if payload.get("id") != order.get("provider_order_id"):
        raise AppError("CAPTURE_MISMATCH", "Order reference does not match", 409)
    if payload.get("status") != "COMPLETED":
        raise AppError("ORDER_NOT_APPROVED", "Payment is not completed", 409)
    try:
        unit = payload["purchase_units"][0]
        cap = unit["payments"]["captures"][0]
        if cap["status"] != "COMPLETED":
            raise AppError("ORDER_NOT_APPROVED", "Capture is not completed", 409)
        amount = cap["amount"]
        if amount["currency_code"] != order["currency"] or from_value(amount["value"]) != order["amount"]:
            raise AppError("CAPTURE_MISMATCH", "Captured amount or currency differs", 409)
        merchant = settings.paypal_merchant_id
        if merchant and unit.get("payee", {}).get("merchant_id") != merchant:
            raise AppError("CAPTURE_MISMATCH", "Unexpected payee", 409)
        return cap["id"]
    except (KeyError, IndexError, TypeError):
        raise AppError("CAPTURE_MISMATCH", "Malformed capture payload", 409)


def post_verified(order, capture_id):
    oid_ = str(order["_id"])
    db.payment_orders.update_one({"_id": order["_id"]}, {"$set": {"state": "captured", "capture_id": capture_id}})
    try:
        db.contributions.insert_one(
            {
                "trip_id": order["trip_id"],
                "member_id": order["member_id"],
                "order_id": oid_,
                "amount": order["amount"],
                "currency": order["currency"],
                "status": "verified",
                "provider_ref": capture_id,
                "captured_at": now(),
            }
        )
    except DuplicateKeyError:
        pass
    ledger.post(order["trip_id"], "contribution", oid_, order["amount"], order["currency"], order["member_id"], order["member_id"])
    db.payment_orders.update_one({"_id": order["_id"]}, {"$set": {"state": "posted", "posted_at": now()}})


def settle(order, payload=None):
    if order["state"] == "posted":
        return True
    if payload is None:
        try:
            payload = paypal.capture(order["provider_order_id"])
        except AppError as e:
            if e.code != "ORDER_ALREADY_CAPTURED":
                raise
            payload = paypal.get_order(order["provider_order_id"])
    try:
        capture_id = verify_payload(order, payload)
    except AppError as e:
        if e.code == "CAPTURE_MISMATCH":
            db.payment_orders.update_one({"_id": order["_id"]}, {"$set": {"state": "mismatch"}})
            audit(order["trip_id"], order["member_id"], "capture_mismatch", {"order_id": str(order["_id"])})
        raise
    post_verified(order, capture_id)
    return False


def reverse_contribution(capture_id, refund_id, refund_amount, reason):
    c = db.contributions.find_one({"provider_ref": capture_id})
    if not c:
        return False
    amount = min(refund_amount or c["amount"], c["amount"])
    posted = ledger.post(c["trip_id"], "reversal", refund_id, -amount, c["currency"], "provider", c["member_id"], reason)
    if posted and amount >= c["amount"]:
        db.contributions.update_one({"_id": c["_id"]}, {"$set": {"status": "reversed"}})
    return posted

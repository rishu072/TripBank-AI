from pymongo.errors import DuplicateKeyError

from ..db import db
from ..utils import now, oid


def post(trip_id, type_, source_id, amount, currency, actor_id, member_id=None, reason=""):
    try:
        db.ledger_entries.insert_one(
            {
                "trip_id": trip_id,
                "type": type_,
                "source_id": source_id,
                "amount": amount,
                "currency": currency,
                "actor_id": actor_id,
                "member_id": member_id,
                "reason": reason,
                "created_at": now(),
            }
        )
        return True
    except DuplicateKeyError:
        return False


def summary(trip_id):
    rows = db.ledger_entries.aggregate(
        [{"$match": {"trip_id": trip_id}}, {"$group": {"_id": "$type", "total": {"$sum": "$amount"}}}]
    )
    t = {r["_id"]: r["total"] for r in rows}
    verified = t.get("contribution", 0) + t.get("reversal", 0)
    spend = -t.get("expense", 0)
    return {"verified": verified, "spend": spend, "available": verified - spend}


def paid_map(trip_id):
    rows = db.ledger_entries.aggregate(
        [
            {"$match": {"trip_id": trip_id, "type": {"$in": ["contribution", "reversal"]}}},
            {"$group": {"_id": "$member_id", "total": {"$sum": "$amount"}}},
        ]
    )
    return {r["_id"]: r["total"] for r in rows}


def status_of(target, paid):
    if target > 0 and paid >= target:
        return "paid"
    return "partial" if paid > 0 else "pending"


def member_rows(trip):
    tid = str(trip["_id"])
    members = list(db.trip_members.find({"trip_id": tid, "status": "active"}))
    users = {str(u["_id"]): u for u in db.users.find({"_id": {"$in": [oid(m["user_id"]) for m in members]}})}
    paid = paid_map(tid)
    rows = []
    for m in members:
        p = paid.get(m["user_id"], 0)
        u = users.get(m["user_id"], {})
        rows.append(
            {
                "user_id": m["user_id"],
                "name": u.get("name", "Member"),
                "avatar_url": u.get("avatar_url"),
                "role": m["role"],
                "target_amount": m["target_amount"],
                "paid": p,
                "remaining": max(0, m["target_amount"] - p),
                "status": status_of(m["target_amount"], p),
                "joined_at": m["joined_at"].isoformat(),
            }
        )
    rows.sort(key=lambda r: (r["role"] != "organizer", r["name"].lower()))
    return rows


def category_spend(trip_id):
    rows = db.trip_expenses.aggregate(
        [
            {"$match": {"trip_id": trip_id, "approval_status": "approved"}},
            {"$group": {"_id": "$category", "total": {"$sum": "$amount"}}},
        ]
    )
    return {r["_id"]: r["total"] for r in rows}

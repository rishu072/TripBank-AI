from pymongo import ASCENDING, DESCENDING, MongoClient

from .config import settings

client = MongoClient(settings.database_url, tz_aware=True, serverSelectionTimeoutMS=8000)
db = client[settings.database_name]


def ensure_indexes():
    db.users.create_index("email_normalized", unique=True)
    db.trips.create_index([("owner_user_id", ASCENDING), ("status", ASCENDING)])
    db.trips.create_index("invite_hash", sparse=True)
    db.trip_members.create_index([("trip_id", ASCENDING), ("user_id", ASCENDING)], unique=True)
    db.trip_members.create_index("user_id")
    db.payment_orders.create_index(
        "provider_order_id", unique=True, partialFilterExpression={"provider_order_id": {"$type": "string"}}
    )
    db.payment_orders.create_index("idempotency_key", unique=True)
    db.payment_orders.create_index([("trip_id", ASCENDING), ("member_id", ASCENDING)])
    db.contributions.create_index("order_id", unique=True)
    db.contributions.create_index("trip_id")
    db.trip_expenses.create_index("trip_id")
    db.ledger_entries.create_index([("source_id", ASCENDING), ("type", ASCENDING)], unique=True)
    db.ledger_entries.create_index([("trip_id", ASCENDING), ("created_at", DESCENDING)])
    db.ai_insights.create_index([("trip_id", ASCENDING), ("created_at", DESCENDING)])
    db.webhook_events.create_index("event_id", unique=True)
    db.audit_events.create_index([("trip_id", ASCENDING), ("created_at", DESCENDING)])

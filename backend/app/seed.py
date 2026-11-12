import sys
from datetime import date, timedelta

from .config import settings
from .db import db, ensure_indexes
from .routers.trips import issue_invite
from .security import hash_password
from .services import ledger
from .utils import now

PASSWORD = "Demo@12345"
PEOPLE = [("Asha", 1000000), ("Ravi", 1000000), ("Meera", 600000), ("Kiran", 600000), ("Nisha", 0)]


def run(reset=False):
    ensure_indexes()
    emails = [f"{n.lower()}@demo.test" for n, _ in PEOPLE]
    if reset:
        users = list(db.users.find({"email_normalized": {"$in": emails}}))
        for t in db.trips.find({"demo": True}):
            tid = str(t["_id"])
            for c in ("trip_members", "payment_orders", "contributions", "trip_expenses", "ledger_entries", "ai_insights", "audit_events"):
                db[c].delete_many({"trip_id": tid})
            db.trips.delete_one({"_id": t["_id"]})
        db.users.delete_many({"_id": {"$in": [u["_id"] for u in users]}})
    if db.users.find_one({"email_normalized": emails[0]}):
        print("Demo data already present. Use --reset to rebuild.")
        return
    ids = []
    for n, _ in PEOPLE:
        r = db.users.insert_one(
            {"name": n, "email_normalized": f"{n.lower()}@demo.test", "password_hash": hash_password(PASSWORD), "avatar_url": None, "theme": "system", "notifications": {"email": True}, "token_version": 0, "created_at": now(), "demo": True}
        )
        ids.append(str(r.inserted_id))
    start = date.today() + timedelta(days=30)
    total = 5000000
    trip = db.trips.insert_one(
        {
            "name": "Goa Escape (Demo)",
            "destination": "Goa",
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=3)).isoformat(),
            "group_size": 5,
            "budget_total": total,
            "currency": settings.default_currency,
            "deadline": (start - timedelta(days=7)).isoformat(),
            "description": "Demo trip with illustrative figures",
            "owner_user_id": ids[0],
            "status": "active",
            "budget": None,
            "budget_history": [],
            "version": 1,
            "created_at": now(),
            "invite_hash": None,
            "demo": True,
        }
    )
    tid = str(trip.inserted_id)
    cats = {"Stay": 1600000, "Transport": 1000000, "Food": 1000000, "Activities": 650000, "Local travel": 400000, "Reserve": 350000}
    entry = {"version": 1, "categories": cats, "approved_by": ids[0], "approved_at": now()}
    db.trips.update_one({"_id": trip.inserted_id}, {"$set": {"budget": entry}, "$push": {"budget_history": entry}})
    for i, (uid, (_n, paid)) in enumerate(zip(ids, PEOPLE)):
        db.trip_members.insert_one({"trip_id": tid, "user_id": uid, "role": "organizer" if i == 0 else "member", "target_amount": total // 5, "joined_at": now(), "status": "active"})
        if paid:
            src = f"seed-{i}"
            db.contributions.insert_one({"trip_id": tid, "member_id": uid, "order_id": src, "amount": paid, "currency": settings.default_currency, "status": "verified", "provider_ref": f"DEMO-{i}", "captured_at": now(), "demo": True})
            ledger.post(tid, "contribution", src, paid, settings.default_currency, uid, uid)
    exp = db.trip_expenses.insert_one(
        {"trip_id": tid, "created_by": ids[0], "title": "Hotel advance", "category": "Stay", "amount": 1200000, "currency": settings.default_currency, "date": date.today().isoformat(), "paid_by": "Asha", "description": "Demo expense", "receipt_url": None, "approval_status": "approved", "approved_by": ids[0], "approved_at": now(), "created_at": now()}
    )
    ledger.post(tid, "expense", str(exp.inserted_id), -1200000, settings.default_currency, ids[0])
    code, _ = issue_invite(tid)
    print(f"Demo ready. Login asha@demo.test / {PASSWORD} (others: ravi, meera, kiran, nisha @demo.test)")
    print(f"Invite code for a new account: {code}")


if __name__ == "__main__":
    run("--reset" in sys.argv)

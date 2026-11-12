from ..db import db
from ..utils import now
from . import ledger


def trip_facts(trip):
    tid = str(trip["_id"])
    s = ledger.summary(tid)
    rows = ledger.member_rows(trip)
    spent = ledger.category_spend(tid)
    budget = (trip.get("budget") or {}).get("categories") or {}
    return {
        "trip": trip["name"],
        "destination": trip["destination"],
        "currency": trip["currency"],
        "unit": "minor units (divide by 100)",
        "deadline": trip.get("deadline"),
        "target": trip["budget_total"],
        "verified": s["verified"],
        "remaining": max(0, trip["budget_total"] - s["verified"]),
        "approved_spend": s["spend"],
        "available": s["available"],
        "members": [
            {"first_name": r["name"].split()[0], "target": r["target_amount"], "paid": r["paid"], "status": r["status"]} for r in rows
        ],
        "categories": [{"category": c, "budget": budget[c], "spent": spent.get(c, 0)} for c in budget],
        "snapshot_at": now().isoformat(),
    }


def rule_answer(facts, question):
    q = question.lower()
    cur = facts["currency"]

    def m(v):
        return f"{cur} {v / 100:,.2f}"

    counts = {k: sum(1 for x in facts["members"] if x["status"] == k) for k in ("paid", "partial", "pending")}
    if any(w in q for w in ("who", "pending", "partial")):
        return "; ".join(f"{x['first_name']}: {x['status']} ({m(x['paid'])} of {m(x['target'])})" for x in facts["members"])
    if any(w in q for w in ("spend", "budget", "over", "categor")):
        if not facts["categories"]:
            return "No official budget has been approved yet."
        return "; ".join(f"{c['category']}: {m(c['spent'])} of {m(c['budget'])}" + (" (over budget)" if c["spent"] > c["budget"] else "") for c in facts["categories"])
    if any(w in q for w in ("balance", "available")):
        return f"Available app balance is {m(facts['available'])} ({m(facts['verified'])} verified minus {m(facts['approved_spend'])} approved spend). This is a ledger figure, not a PayPal balance."
    return f"{m(facts['remaining'])} remains from the {m(facts['target'])} target. Members: {counts['paid']} paid, {counts['partial']} partial, {counts['pending']} pending."


def store(trip_id, user_id, feature, result, source, model):
    r = db.ai_insights.insert_one(
        {"trip_id": trip_id, "user_id": user_id, "feature": feature, "prompt_version": "v1", "model": model, "source": source, "snapshot_at": now(), "result": result, "flagged": False, "created_at": now()}
    )
    return str(r.inserted_id)

from fastapi import APIRouter, Depends

from ..db import db
from ..deps import TripCtx, trip_member
from ..schemas import CATEGORIES
from ..services import ledger
from ..utils import clean

router = APIRouter(tags=["statements"])


@router.get("/trips/{trip_id}/statement")
def statement(ctx: TripCtx = Depends(trip_member)):
    t = ctx.trip
    s = ledger.summary(ctx.tid)
    spent = ledger.category_spend(ctx.tid)
    budget = (t.get("budget") or {}).get("categories") or {}
    entries = list(db.ledger_entries.find({"trip_id": ctx.tid}).sort("created_at", 1))
    names = {r["user_id"]: r["name"] for r in ledger.member_rows(t)}
    rows = []
    for e in entries:
        d = clean(e)
        d["member"] = names.get(e.get("member_id"), "")
        rows.append(d)
    return {
        "trip": {"id": ctx.tid, "name": t["name"], "destination": t["destination"], "currency": t["currency"], "status": t["status"], "start_date": str(t["start_date"]), "end_date": str(t["end_date"])},
        "planned_budget": t["budget_total"],
        "collected": s["verified"],
        "approved_expenses": s["spend"],
        "balance": s["available"],
        "categories": [{"category": c, "budget": budget.get(c, 0), "spent": spent.get(c, 0)} for c in CATEGORIES],
        "members": ledger.member_rows(t),
        "ledger": rows,
    }

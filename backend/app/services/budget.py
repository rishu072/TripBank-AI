from ..errors import AppError
from ..schemas import CATEGORIES

DEFAULT_PCT = {"Stay": 32, "Transport": 20, "Food": 20, "Activities": 13, "Local travel": 8, "Reserve": 7}

SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "shares": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "category": {"type": "STRING"},
                    "percent": {"type": "INTEGER"},
                    "explanation": {"type": "STRING"},
                },
                "required": ["category", "percent", "explanation"],
            },
        },
        "assumptions": {"type": "ARRAY", "items": {"type": "STRING"}},
        "confidence": {"type": "STRING"},
    },
    "required": ["shares", "assumptions", "confidence"],
}


def allocate(total, pct):
    out = {}
    used = 0
    for c in CATEGORIES[:-1]:
        out[c] = total * pct[c] // 100
        used += out[c]
    out[CATEGORIES[-1]] = total - used
    return out


def parse_plan(data, total):
    try:
        shares = {s["category"]: int(s["percent"]) for s in data["shares"]}
        notes = {s["category"]: str(s["explanation"])[:300] for s in data["shares"]}
        assumptions = [str(a)[:300] for a in data["assumptions"]][:8]
        confidence = str(data["confidence"]).lower()
    except (KeyError, TypeError, ValueError):
        raise AppError("AI_INVALID_OUTPUT", "Malformed budget draft", 502)
    if set(shares) != set(CATEGORIES) or any(v < 0 for v in shares.values()) or sum(shares.values()) != 100:
        raise AppError("AI_INVALID_OUTPUT", "Budget shares are invalid", 502)
    if confidence not in ("low", "medium", "high"):
        confidence = "medium"
    amounts = allocate(total, shares)
    return {
        "categories": [{"category": c, "amount": amounts[c], "share_pct": shares[c], "explanation": notes[c]} for c in CATEGORIES],
        "assumptions": assumptions,
        "confidence": confidence,
    }


def rule_plan(total):
    amounts = allocate(total, DEFAULT_PCT)
    return {
        "categories": [{"category": c, "amount": amounts[c], "share_pct": DEFAULT_PCT[c], "explanation": "Default starting share"} for c in CATEGORIES],
        "assumptions": ["Rule-based starting split used because no AI draft was available", "Edit every category before approving"],
        "confidence": "low",
    }

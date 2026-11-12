from decimal import Decimal, InvalidOperation

from .errors import AppError


def to_value(minor: int) -> str:
    return f"{minor // 100}.{minor % 100:02d}"


def from_value(value: str) -> int:
    try:
        d = Decimal(str(value))
    except InvalidOperation:
        raise AppError("AMOUNT_INVALID", "Invalid amount", 400)
    if d != d.quantize(Decimal("0.01")) or d < 0:
        raise AppError("AMOUNT_INVALID", "Invalid amount", 400)
    return int(d * 100)

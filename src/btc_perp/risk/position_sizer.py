from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PositionSide(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass(frozen=True, slots=True)
class PositionSizeResult:
    """Position sizing result based on monetary risk."""

    side: PositionSide
    equity: float
    risk_pct: float
    risk_amount: float
    entry_price: float
    stop_price: float
    stop_distance: float
    raw_quantity: float
    quantity: float
    notional_value: float
    effective_leverage: float
    capped_by_leverage: bool


def calculate_position_size(
    *,
    equity: float,
    risk_pct: float,
    entry_price: float,
    stop_price: float,
    side: PositionSide | str,
    max_notional_pct: float = 1.0,
    max_leverage: float = 10.0,
) -> PositionSizeResult:
    """Calculate position quantity from monetary risk.

    The primary sizing rule is:

        quantity = (equity * risk_pct) / abs(entry - stop)

    ``max_notional_pct`` limits position notional relative to equity.
    ``max_leverage`` provides a second independent safety cap.
    """
    if equity <= 0:
        raise ValueError("equity must be > 0")
    if not 0 < risk_pct <= 1:
        raise ValueError("risk_pct must be > 0 and <= 1")
    if entry_price <= 0:
        raise ValueError("entry_price must be > 0")
    if stop_price <= 0:
        raise ValueError("stop_price must be > 0")
    if entry_price == stop_price:
        raise ValueError("entry_price and stop_price must be different")
    if max_notional_pct <= 0:
        raise ValueError("max_notional_pct must be > 0")
    if max_leverage <= 0:
        raise ValueError("max_leverage must be > 0")

    try:
        side = PositionSide(side)
    except ValueError as exc:
        raise ValueError("side must be LONG or SHORT") from exc

    if side is PositionSide.LONG and stop_price >= entry_price:
        raise ValueError("LONG stop_price must be below entry_price")
    if side is PositionSide.SHORT and stop_price <= entry_price:
        raise ValueError("SHORT stop_price must be above entry_price")

    stop_distance = abs(entry_price - stop_price)
    risk_amount = equity * risk_pct
    raw_quantity = risk_amount / stop_distance

    max_notional = equity * max_leverage

    max_quantity = max_notional / entry_price
    quantity = min(raw_quantity, max_quantity)
    notional_value = quantity * entry_price
    effective_leverage = notional_value / equity

    return PositionSizeResult(
        side=side,
        equity=equity,
        risk_pct=risk_pct,
        risk_amount=risk_amount,
        entry_price=entry_price,
        stop_price=stop_price,
        stop_distance=stop_distance,
        raw_quantity=raw_quantity,
        quantity=quantity,
        notional_value=notional_value,
        effective_leverage=effective_leverage,
        capped_by_leverage=raw_quantity > max_quantity
    )

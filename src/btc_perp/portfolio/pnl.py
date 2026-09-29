from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from btc_perp.risk import PositionSide


class TradeSide(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass(frozen=True, slots=True)
class TradePnL:
    """Realized PnL for one completed perpetual-futures trade."""

    side: PositionSide
    quantity: float
    intended_entry_price: float
    intended_exit_price: float
    entry_fill_price: float
    exit_fill_price: float
    entry_notional: float
    exit_notional: float
    gross_pnl: float
    fee: float
    slippage_cost: float
    funding_cost: float
    net_pnl: float
    return_on_equity: float


@dataclass(frozen=True, slots=True)
class PortfolioState:
    """Minimal portfolio state for the backtest pipeline."""

    initial_equity: float
    equity: float
    realized_pnl: float = 0.0
    total_fees: float = 0.0
    total_slippage: float = 0.0
    total_funding: float = 0.0
    trade_count: int = 0

    @property
    def total_cost(self) -> float:
        return self.total_fees + self.total_slippage + self.total_funding

    @property
    def cumulative_return(self) -> float:
        return self.equity / self.initial_equity - 1.0


def calculate_trade_pnl(
    *,
    side: PositionSide | str,
    quantity: float,
    entry_price: float,
    exit_price: float,
    fee_rate: float = 0.0005,
    slippage_rate: float = 0.0,
    funding_cost: float = 0.0,
    equity: float | None = None,
) -> TradePnL:
    """Calculate realized PnL for one completed trade.

    Slippage is modeled as adverse execution on both entry and exit:

    LONG:
        entry_fill = entry * (1 + slippage)
        exit_fill  = exit  * (1 - slippage)

    SHORT:
        entry_fill = entry * (1 - slippage)
        exit_fill  = exit  * (1 + slippage)

    Fees are charged on both entry and exit notional.
    ``funding_cost`` is an explicit cash adjustment. Positive values are
    funding expenses; negative values can represent funding received.
    """
    if quantity <= 0:
        raise ValueError("quantity must be > 0")
    if entry_price <= 0:
        raise ValueError("entry_price must be > 0")
    if exit_price <= 0:
        raise ValueError("exit_price must be > 0")
    if fee_rate < 0:
        raise ValueError("fee_rate must be >= 0")
    if not 0 <= slippage_rate < 1:
        raise ValueError("slippage_rate must be >= 0 and < 1")
    if equity is not None and equity <= 0:
        raise ValueError("equity must be > 0 when provided")

    try:
        side = PositionSide(side)
    except ValueError as exc:
        raise ValueError("side must be LONG or SHORT") from exc

    if side is PositionSide.LONG:
        entry_fill_price = entry_price * (1.0 + slippage_rate)
        exit_fill_price = exit_price * (1.0 - slippage_rate)
        gross_pnl = (exit_fill_price - entry_fill_price) * quantity
    else:
        entry_fill_price = entry_price * (1.0 - slippage_rate)
        exit_fill_price = exit_price * (1.0 + slippage_rate)
        gross_pnl = (entry_fill_price - exit_fill_price) * quantity

    entry_notional = entry_fill_price * quantity
    exit_notional = exit_fill_price * quantity
    fee = (entry_notional + exit_notional) * fee_rate

    # Difference between ideal-price PnL and executed-price PnL.
    ideal_gross_pnl = (
        (exit_price - entry_price) * quantity
        if side is PositionSide.LONG
        else (entry_price - exit_price) * quantity
    )
    slippage_cost = ideal_gross_pnl - gross_pnl

    net_pnl = gross_pnl - fee - funding_cost
    return_on_equity = net_pnl / equity if equity is not None else 0.0

    return TradePnL(
        side=side,
        quantity=quantity,
        intended_entry_price=entry_price,
        intended_exit_price=exit_price,
        entry_fill_price=entry_fill_price,
        exit_fill_price=exit_fill_price,
        entry_notional=entry_notional,
        exit_notional=exit_notional,
        gross_pnl=gross_pnl,
        fee=fee,
        slippage_cost=slippage_cost,
        funding_cost=funding_cost,
        net_pnl=net_pnl,
        return_on_equity=return_on_equity,
    )


def apply_trade_to_equity(
    portfolio: PortfolioState,
    trade: TradePnL,
) -> PortfolioState:
    """Apply one realized trade to portfolio equity and accounting totals."""
    if portfolio.initial_equity <= 0:
        raise ValueError("initial_equity must be > 0")
    if portfolio.equity <= 0:
        raise ValueError("portfolio equity must be > 0 before applying a trade")

    return PortfolioState(
        initial_equity=portfolio.initial_equity,
        equity=portfolio.equity + trade.net_pnl,
        realized_pnl=portfolio.realized_pnl + trade.net_pnl,
        total_fees=portfolio.total_fees + trade.fee,
        total_slippage=portfolio.total_slippage + trade.slippage_cost,
        total_funding=portfolio.total_funding + trade.funding_cost,
        trade_count=portfolio.trade_count + 1,
    )

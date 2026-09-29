import pytest

from btc_perp.portfolio import PortfolioState, apply_trade_to_equity, calculate_trade_pnl
from btc_perp.risk import PositionSide


def test_long_profitable_trade_net_pnl():
    trade = calculate_trade_pnl(
        side=PositionSide.LONG,
        quantity=1.0,
        entry_price=100_000,
        exit_price=110_000,
        fee_rate=0.0,
        slippage_rate=0.0,
    )

    assert trade.gross_pnl == pytest.approx(10_000)
    assert trade.fee == pytest.approx(0)
    assert trade.slippage_cost == pytest.approx(0)
    assert trade.net_pnl == pytest.approx(10_000)


def test_long_losing_trade():
    trade = calculate_trade_pnl(
        side="LONG",
        quantity=0.25,
        entry_price=100_000,
        exit_price=97_000,
        fee_rate=0.0,
        slippage_rate=0.0,
    )

    assert trade.gross_pnl == pytest.approx(-750)
    assert trade.net_pnl == pytest.approx(-750)


def test_short_profitable_trade():
    trade = calculate_trade_pnl(
        side="SHORT",
        quantity=0.25,
        entry_price=100_000,
        exit_price=97_000,
        fee_rate=0.0,
        slippage_rate=0.0,
    )

    assert trade.gross_pnl == pytest.approx(750)


def test_short_losing_trade():
    trade = calculate_trade_pnl(
        side="SHORT",
        quantity=0.25,
        entry_price=100_000,
        exit_price=103_000,
        fee_rate=0.0,
        slippage_rate=0.0,
    )

    assert trade.gross_pnl == pytest.approx(-750)


def test_fee_is_charged_on_entry_and_exit():
    trade = calculate_trade_pnl(
        side="LONG",
        quantity=1.0,
        entry_price=100_000,
        exit_price=110_000,
        fee_rate=0.001,
        slippage_rate=0.0,
    )

    assert trade.fee == pytest.approx(210)
    assert trade.net_pnl == pytest.approx(9_790)


def test_slippage_reduces_long_pnl():
    trade = calculate_trade_pnl(
        side="LONG",
        quantity=1.0,
        entry_price=100_000,
        exit_price=110_000,
        fee_rate=0.0,
        slippage_rate=0.001,
    )

    assert trade.gross_pnl < 10_000
    assert trade.slippage_cost > 0
    assert trade.net_pnl == pytest.approx(trade.gross_pnl)


def test_funding_is_subtracted_from_net_pnl():
    trade = calculate_trade_pnl(
        side="LONG",
        quantity=1.0,
        entry_price=100_000,
        exit_price=110_000,
        fee_rate=0.0,
        slippage_rate=0.0,
        funding_cost=100,
    )

    assert trade.net_pnl == pytest.approx(9_900)
    assert trade.funding_cost == pytest.approx(100)


def test_return_on_equity():
    trade = calculate_trade_pnl(
        side="LONG",
        quantity=0.25,
        entry_price=100_000,
        exit_price=97_000,
        fee_rate=0.0,
        slippage_rate=0.0,
        equity=100_000,
    )

    assert trade.return_on_equity == pytest.approx(-0.0075)


def test_apply_trade_to_equity():
    portfolio = PortfolioState(initial_equity=100_000, equity=100_000)
    trade = calculate_trade_pnl(
        side="LONG",
        quantity=0.25,
        entry_price=100_000,
        exit_price=103_000,
        fee_rate=0.0,
        slippage_rate=0.0,
    )

    updated = apply_trade_to_equity(portfolio, trade)

    assert updated.equity == pytest.approx(100_750)
    assert updated.realized_pnl == pytest.approx(750)
    assert updated.trade_count == 1
    assert updated.cumulative_return == pytest.approx(0.0075)


def test_invalid_inputs():
    with pytest.raises(ValueError, match="quantity"):
        calculate_trade_pnl(
            side="LONG", quantity=0, entry_price=100, exit_price=101
        )

    with pytest.raises(ValueError, match="fee_rate"):
        calculate_trade_pnl(
            side="LONG", quantity=1, entry_price=100, exit_price=101, fee_rate=-1
        )

    with pytest.raises(ValueError, match="side"):
        calculate_trade_pnl(
            side="BAD", quantity=1, entry_price=100, exit_price=101
        )

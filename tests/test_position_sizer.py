import pytest

from btc_perp.risk import PositionSide, calculate_position_size


def test_long_position_size_uses_monetary_risk():
    result = calculate_position_size(
        equity=100_000,
        risk_pct=0.0075,
        entry_price=100_000,
        stop_price=97_000,
        side=PositionSide.LONG,
        max_notional_pct=10.0,
        max_leverage=10.0,
    )

    assert result.risk_amount == pytest.approx(750.0)
    assert result.stop_distance == pytest.approx(3_000.0)
    assert result.raw_quantity == pytest.approx(0.25)
    assert result.quantity == pytest.approx(0.25)
    assert result.notional_value == pytest.approx(25_000.0)
    assert result.effective_leverage == pytest.approx(0.25)


def test_short_position_size_uses_same_risk_formula():
    result = calculate_position_size(
        equity=100_000,
        risk_pct=0.003,
        entry_price=100_000,
        stop_price=103_000,
        side="SHORT",
        max_notional_pct=10.0,
        max_leverage=10.0,
    )

    assert result.risk_amount == pytest.approx(300.0)
    assert result.quantity == pytest.approx(0.1)
    assert result.notional_value == pytest.approx(10_000.0)


def test_max_notional_caps_position():
    result = calculate_position_size(
        equity=100_000,
        risk_pct=0.02,
        entry_price=100_000,
        stop_price=99_900,
        side="LONG",
        max_notional_pct=1.0,
        max_leverage=10.0,
    )

    assert result.raw_quantity == pytest.approx(20.0)
    assert result.quantity == pytest.approx(10.0)
    assert result.notional_value == pytest.approx(1000_000.0)


def test_max_leverage_caps_position_when_notional_limit_is_higher():
    result = calculate_position_size(
        equity=100_000,
        risk_pct=0.5,
        entry_price=100_000,
        stop_price=99_900,
        side="LONG",
        max_notional_pct=20.0,
        max_leverage=5.0,
    )

    assert result.quantity == pytest.approx(5.0)
    assert result.notional_value == pytest.approx(500_000.0)
    assert result.effective_leverage == pytest.approx(5.0)
    assert result.capped_by_leverage is True


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"equity": 0}, "equity"),
        ({"risk_pct": 0}, "risk_pct"),
        ({"risk_pct": 1.1}, "risk_pct"),
        ({"entry_price": 0}, "entry_price"),
        ({"stop_price": 0}, "stop_price"),
        ({"entry_price": 100_000, "stop_price": 100_000}, "different"),
    ],
)
def test_invalid_inputs(kwargs, message):
    base = {
        "equity": 100_000,
        "risk_pct": 0.0075,
        "entry_price": 100_000,
        "stop_price": 97_000,
        "side": "LONG",
    }
    base.update(kwargs)

    with pytest.raises(ValueError, match=message):
        calculate_position_size(**base)


def test_long_stop_must_be_below_entry():
    with pytest.raises(ValueError, match="LONG"):
        calculate_position_size(
            equity=100_000,
            risk_pct=0.0075,
            entry_price=100_000,
            stop_price=101_000,
            side="LONG",
        )


def test_short_stop_must_be_above_entry():
    with pytest.raises(ValueError, match="SHORT"):
        calculate_position_size(
            equity=100_000,
            risk_pct=0.0075,
            entry_price=100_000,
            stop_price=99_000,
            side="SHORT",
        )

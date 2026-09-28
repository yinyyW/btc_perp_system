import pandas as pd
import pytest

from btc_perp.data import OHLCVData
from btc_perp.features.volatility import (
    add_atr_features,
    calculate_atr,
    calculate_atr_pct,
    calculate_true_range,
)


def make_data() -> OHLCVData:
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range(
                "2026-01-01",
                periods=20,
                freq="4h",
                tz="UTC",
            ),
            "open": [
                100, 102, 104, 103, 105,
                107, 106, 108, 110, 109,
                111, 113, 112, 114, 116,
                115, 117, 119, 118, 120,
            ],
            "high": [
                105, 107, 108, 107, 110,
                112, 109, 111, 114, 112,
                115, 117, 116, 118, 120,
                119, 121, 123, 122, 125,
            ],
            "low": [
                98, 100, 101, 100, 103,
                104, 103, 105, 108, 106,
                108, 110, 109, 111, 113,
                112, 114, 116, 115, 117,
            ],
            "close": [
                102, 104, 103, 106, 108,
                105, 108, 110, 109, 111,
                114, 112, 115, 117, 116,
                119, 121, 118, 122, 122,
            ],
            "volume": [100] * 20,
        }
    )

    return OHLCVData(frame)


def test_true_range_first_candle():
    data = make_data()

    tr = calculate_true_range(data)

    # 第一根 K 线没有 previous close
    # TR = High - Low = 105 - 98 = 7
    assert tr.iloc[0] == pytest.approx(7.0)


def test_true_range_uses_previous_close():
    data = make_data()

    tr = calculate_true_range(data)

    # 第二根：
    #
    # High - Low = 107 - 100 = 7
    # |High - PreviousClose| = |107 - 102| = 5
    # |Low - PreviousClose|  = |100 - 102| = 2
    #
    # TR = 7
    assert tr.iloc[1] == pytest.approx(7.0)


def test_atr_period():
    data = make_data()

    atr = calculate_atr(data, period=14)

    assert atr.name == "atr_14"

    # 前 13 个值没有完整的 14 根数据
    assert atr.iloc[:13].isna().all()

    # 第 14 根开始有 ATR
    assert pd.notna(atr.iloc[13])


def test_atr_is_positive():
    data = make_data()

    atr = calculate_atr(data, period=14)

    assert (atr.dropna() > 0).all()


def test_atr_pct():
    data = make_data()

    atr = calculate_atr(data, period=14)
    atr_pct = calculate_atr_pct(data, period=14)

    expected = atr / data.frame["close"]

    pd.testing.assert_series_equal(
        atr_pct,
        expected.rename("atr_pct_14"),
    )


def test_add_atr_features():
    data = make_data()

    result = add_atr_features(
        data,
        period=14,
    )

    assert "tr" in result.columns
    assert "atr_14" in result.columns
    assert "atr_pct_14" in result.columns

    assert len(result) == len(data)


def test_invalid_period():
    data = make_data()

    with pytest.raises(
        ValueError,
        match="ATR period must be > 0",
    ):
        calculate_atr(data, period=0)
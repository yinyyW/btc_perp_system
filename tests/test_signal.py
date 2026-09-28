import pandas as pd
import pytest

from btc_perp.data import OHLCVData
from btc_perp.strategy import Signal, generate_signal


def make_data() -> OHLCVData:
    """
    Construct deterministic OHLCV data.

    The last candle breaks the previous 5-candle high,
    so it should generate LONG.
    """

    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range(
                "2026-01-01",
                periods=25,
                freq="4h",
                tz="UTC",
            ),

            "open": [
                100, 101, 102, 101, 103,
                104, 103, 105, 106, 105,
                107, 108, 107, 109, 110,
                109, 111, 112, 111, 113,
                114, 115, 114, 116, 125,
            ],

            "high": [
                102, 103, 104, 103, 105,
                106, 105, 107, 108, 107,
                109, 110, 109, 111, 112,
                111, 113, 114, 113, 115,
                116, 117, 116, 118, 130,
            ],

            "low": [
                98, 99, 100, 99, 101,
                102, 101, 103, 104, 103,
                105, 106, 105, 107, 108,
                107, 109, 110, 109, 111,
                112, 113, 112, 114, 120,
            ],

            "close": [
                101, 102, 103, 102, 104,
                105, 104, 106, 107, 106,
                108, 109, 108, 110, 111,
                110, 112, 113, 112, 114,
                115, 116, 115, 117, 128,
            ],

            "volume": [100] * 25,
        }
    )

    return OHLCVData(frame)


def test_signal_is_wait_before_warmup():
    data = make_data()

    signals = generate_signal(
        data,
        breakout_period=5,
        atr_period=14,
    )

    # ATR 尚未完成 warm-up
    assert all(
        signal == Signal.WAIT
        for signal in signals.iloc[:13]
    )


def test_long_breakout():
    data = make_data()

    signals = generate_signal(
        data,
        breakout_period=5,
        atr_period=14,
    )

    # 最后一根 close=128
    # 前 5 根 high 最大值=118
    # 因此突破成立
    assert signals.iloc[-1] == Signal.LONG


def test_no_lookahead():
    data = make_data()

    signals = generate_signal(
        data,
        breakout_period=5,
        atr_period=14,
    )

    df = data.frame

    previous_high = (
        df["high"]
        .rolling(5)
        .max()
        .shift(1)
    )

    # 当前 K 线的 high=130
    #
    # 如果错误地使用当前 candle:
    #
    # rolling(5).max()
    #
    # 当前 close=128 < 130
    #
    # 会错误地阻止 breakout。
    #
    # 正确实现必须使用 previous_high。
    assert previous_high.iloc[-1] == 118
    assert signals.iloc[-1] == Signal.LONG


def test_invalid_breakout_period():
    data = make_data()

    with pytest.raises(
        ValueError,
        match="breakout_period must be > 0",
    ):
        generate_signal(
            data,
            breakout_period=0,
        )


def test_invalid_atr_period():
    data = make_data()

    with pytest.raises(
        ValueError,
        match="atr_period must be > 0",
    ):
        generate_signal(
            data,
            atr_period=0,
        )


def test_invalid_atr_pct():
    data = make_data()

    with pytest.raises(
        ValueError,
        match="min_atr_pct must be >= 0",
    ):
        generate_signal(
            data,
            min_atr_pct=-0.01,
        )
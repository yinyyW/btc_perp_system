from __future__ import annotations

from enum import StrEnum

import pandas as pd

from btc_perp.data import OHLCVData
from btc_perp.features.volatility import (
    calculate_atr,
    calculate_atr_pct,
)


class Signal(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"
    WAIT = "WAIT"


def generate_signal(
    data: OHLCVData,
    breakout_period: int = 20,
    atr_period: int = 14,
    min_atr_pct: float = 0.0,
) -> pd.Series:
    """
    Generate LONG / SHORT / WAIT signals.

    Long:
        Close > previous N-period high
        AND ATR% >= min_atr_pct

    Short:
        Close < previous N-period low
        AND ATR% >= min_atr_pct

    Otherwise:
        WAIT

    Important:
        Breakout levels use shift(1) so the current candle
        is NOT included in the breakout calculation.
    """

    if breakout_period <= 0:
        raise ValueError("breakout_period must be > 0")

    if atr_period <= 0:
        raise ValueError("atr_period must be > 0")

    if min_atr_pct < 0:
        raise ValueError("min_atr_pct must be >= 0")

    df = data.frame

    # --------------------------------
    # 1. Previous N-period high / low
    # --------------------------------

    previous_high = (
        df["high"]
        .rolling(breakout_period)
        .max()
        .shift(1)
    )

    previous_low = (
        df["low"]
        .rolling(breakout_period)
        .min()
        .shift(1)
    )

    # --------------------------------
    # 2. ATR filter
    # --------------------------------

    atr_pct = calculate_atr_pct(
        data,
        period=atr_period,
    )

    volatility_ok = atr_pct >= min_atr_pct

    # --------------------------------
    # 3. Breakout conditions
    # --------------------------------

    long_condition = (
        (df["close"] > previous_high)
        & volatility_ok
    )

    short_condition = (
        (df["close"] < previous_low)
        & volatility_ok
    )

    # --------------------------------
    # 4. Generate signals
    # --------------------------------

    signal = pd.Series(
        Signal.WAIT,
        index=df.index,
        dtype="object",
    )

    signal.loc[long_condition] = Signal.LONG
    signal.loc[short_condition] = Signal.SHORT

    return signal.rename("signal")
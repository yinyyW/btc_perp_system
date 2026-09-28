from __future__ import annotations

import pandas as pd

from btc_perp.data import OHLCVData


def calculate_true_range(data: OHLCVData) -> pd.Series:
    """
    Calculate True Range.

    TR = max(
        High - Low,
        abs(High - Previous Close),
        abs(Low - Previous Close),
    )
    """
    df = data.frame

    previous_close = df["close"].shift(1)

    high_low = df["high"] - df["low"]
    high_prev_close = (df["high"] - previous_close).abs()
    low_prev_close = (df["low"] - previous_close).abs()

    tr = pd.concat(
        [
            high_low,
            high_prev_close,
            low_prev_close,
        ],
        axis=1,
    ).max(axis=1)

    return tr.rename("tr")


def calculate_atr(
    data: OHLCVData,
    period: int = 14,
) -> pd.Series:
    """
    Calculate ATR using Wilder's smoothing.
    """
    if period <= 0:
        raise ValueError("ATR period must be > 0")

    tr = calculate_true_range(data)

    atr = tr.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    return atr.rename(f"atr_{period}")


def calculate_atr_pct(
    data: OHLCVData,
    period: int = 14,
) -> pd.Series:
    """
    ATR percentage.

    ATR% = ATR / Close
    """
    atr = calculate_atr(data, period)
    close = data.frame["close"]

    return (atr / close).rename(f"atr_pct_{period}")


def add_atr_features(
    data: OHLCVData,
    period: int = 14,
) -> pd.DataFrame:
    """
    Return OHLCV + TR + ATR + ATR%.
    """
    frame = data.frame

    frame["tr"] = calculate_true_range(data)
    frame[f"atr_{period}"] = calculate_atr(data, period)
    frame[f"atr_pct_{period}"] = calculate_atr_pct(data, period)

    return frame
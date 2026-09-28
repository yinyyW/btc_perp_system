from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import pandas as pd

OHLCV_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]

@dataclass(frozen=True, slots=True)
class OHLCVBar:
    timestamp: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float

class OHLCVData:
    def __init__(self, frame: pd.DataFrame):
        self._df = self._validate(frame)

    @property
    def frame(self) -> pd.DataFrame:
        return self._df.copy()

    def __len__(self) -> int:
        return len(self._df)

    def __getitem__(self, index: int) -> OHLCVBar:
        row = self._df.iloc[index]
        return OHLCVBar(row["timestamp"], float(row["open"]), float(row["high"]),
                        float(row["low"]), float(row["close"]), float(row["volume"]))

    @classmethod
    def from_csv(cls, path: str | Path) -> "OHLCVData":
        return cls(pd.read_csv(path))

    @classmethod
    def from_parquet(cls, path: str | Path) -> "OHLCVData":
        return cls(pd.read_parquet(path))

    def to_csv(self, path: str | Path) -> None:
        self._df.to_csv(path, index=False)

    def to_parquet(self, path: str | Path) -> None:
        self._df.to_parquet(path, index=False)

    def slice(self, start=None, end=None) -> "OHLCVData":
        frame = self._df
        if start is not None:
            frame = frame[frame["timestamp"] >= _to_utc_timestamp(start)]
        if end is not None:
            frame = frame[frame["timestamp"] <= _to_utc_timestamp(end)]
        return OHLCVData(frame.reset_index(drop=True))

    def _validate(self, frame: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(frame, pd.DataFrame):
            raise TypeError("OHLCVData requires a pandas DataFrame")
        missing = [c for c in OHLCV_COLUMNS if c not in frame.columns]
        if missing:
            raise ValueError(f"Missing OHLCV columns: {missing}")
        df = frame[OHLCV_COLUMNS].copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="raise")
        for col in OHLCV_COLUMNS[1:]:
            df[col] = pd.to_numeric(df[col], errors="raise")
        if df["timestamp"].duplicated().any():
            raise ValueError("Duplicate timestamps found")
        if not df["timestamp"].is_monotonic_increasing:
            df = df.sort_values("timestamp").reset_index(drop=True)
        prices = ["open", "high", "low", "close"]
        if (df[prices] <= 0).any().any():
            raise ValueError("OHLC prices must be > 0")
        if (df["volume"] < 0).any():
            raise ValueError("Volume must be >= 0")
        invalid_high = df["high"] < df[["open", "close", "low"]].max(axis=1)
        invalid_low = df["low"] > df[["open", "close", "high"]].min(axis=1)
        if invalid_high.any():
            raise ValueError("Invalid OHLC rows: high is too low")
        if invalid_low.any():
            raise ValueError("Invalid OHLC rows: low is too high")
        return df.reset_index(drop=True)

def _to_utc_timestamp(value) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")

import pandas as pd
import pytest
from btc_perp.data import OHLCVData

def frame():
    return pd.DataFrame({
        "timestamp": ["2026-01-01T01:00:00Z", "2026-01-01T00:00:00Z"],
        "open": [101, 100], "high": [105, 103], "low": [99, 98],
        "close": [103, 101], "volume": [12, 10],
    })

def test_normalize():
    d = OHLCVData(frame())
    assert len(d) == 2
    assert d.frame["timestamp"].is_monotonic_increasing
    assert str(d.frame["timestamp"].dt.tz) == "UTC"

def test_bar():
    bar = OHLCVData(frame())[0]
    assert bar.open == 100 and bar.high == 103 and bar.low == 98 and bar.close == 101

def test_duplicate_rejected():
    f = frame()
    f.loc[1, "timestamp"] = f.loc[0, "timestamp"]
    with pytest.raises(ValueError, match="Duplicate timestamps"):
        OHLCVData(f)

def test_invalid_ohlc_rejected():
    f = frame()
    f.loc[0, "high"] = 90
    with pytest.raises(ValueError, match="high is too low"):
        OHLCVData(f)

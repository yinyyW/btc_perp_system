from pathlib import Path
from .models import OHLCVData

def load_ohlcv(path: str | Path) -> OHLCVData:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"OHLCV data file not found: {path}")
    if path.suffix.lower() == ".csv":
        return OHLCVData.from_csv(path)
    if path.suffix.lower() == ".parquet":
        return OHLCVData.from_parquet(path)
    raise ValueError(f"Unsupported OHLCV file format: {path.suffix}")

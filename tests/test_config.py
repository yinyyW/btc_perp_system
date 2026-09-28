from pathlib import Path
from btc_perp.config import load_config
ROOT = Path(__file__).resolve().parents[1]

def test_load_backtest_config():
    c = load_config(ROOT/"configs/base.yaml", ROOT/"configs/backtest.yaml")
    assert c.market.symbol == "BTCUSDT"
    assert c.environment.mode == "backtest"
    assert c.backtest.initial_equity == 100000
    assert c.risk.bull == 0.0075

def test_environment_override():
    c = load_config(ROOT/"configs/base.yaml", ROOT/"configs/paper.yaml")
    assert c.environment.mode == "paper"
    assert c.data.source == "exchange"
    assert c.execution.simulate is True

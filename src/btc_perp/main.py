from pathlib import Path
from btc_perp.config import load_config

ROOT = Path(__file__).resolve().parents[2]

def main():
    config = load_config(ROOT / "configs/base.yaml", ROOT / "configs/backtest.yaml")
    print("BTC Perpetual Quant System")
    print("==========================")
    if config.environment is not None:
        print(f"Environment : {config.environment.mode}")
    print(f"Symbol      : {config.market.symbol}")
    print(f"Timeframe   : {config.market.timeframe}")
    if config.backtest is not None:
        print(f"Initial Equity : ${config.backtest.initial_equity:,.2f}")
    print(f"ATR Period     : {config.atr.period}")
    print(f"ATR Stop       : {config.atr.stop_multiple}")
    print("Risk:")
    print(f"  Bull    : {config.risk.bull:.2%}")
    print(f"  Neutral : {config.risk.neutral:.2%}")
    print(f"  Bear    : {config.risk.bear:.2%}")
    print("Leverage:")
    print(f"  Default : {config.leverage.default}x")
    print(f"  Max     : {config.leverage.max}x")
    print("Status: CONFIG OK")

if __name__ == "__main__":
    main()

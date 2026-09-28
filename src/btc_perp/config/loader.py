from __future__ import annotations
from pathlib import Path
from typing import Literal
import yaml
from pydantic import BaseModel, ConfigDict, Field

class ProjectConfig(BaseModel):
    name: str
    version: str

class MarketConfig(BaseModel):
    symbol: str
    timeframe: str
    higher_timeframe: str

class StrategyConfig(BaseModel):
    name: str
    direction: Literal["long", "short", "both"]

class RegimeConfig(BaseModel):
    bull_score: int = 2
    bear_score: int = -2

class ATRConfig(BaseModel):
    period: int = Field(gt=0)
    stop_multiple: float = Field(gt=0)

class RiskConfig(BaseModel):
    bull: float = Field(gt=0, lt=1)
    neutral: float = Field(gt=0, lt=1)
    bear: float = Field(gt=0, lt=1)
    max_portfolio_risk: float = Field(gt=0, lt=1)
    daily_loss_limit: float = Field(gt=0, lt=1)
    weekly_loss_limit: float = Field(gt=0, lt=1)

class PositionConfig(BaseModel):
    max_notional_pct: float = Field(gt=0)

class LeverageConfig(BaseModel):
    default: int = Field(gt=0)
    max: int = Field(gt=0)

class ManagementConfig(BaseModel):
    breakeven_r: float = Field(gt=0)
    trailing_start_r: float = Field(gt=0)

class CostConfig(BaseModel):
    fee_rate: float = Field(ge=0, lt=1)
    slippage_rate: float = Field(ge=0, lt=1)

class EnvironmentConfig(BaseModel):
    mode: Literal["backtest", "paper", "live"]

class BacktestConfig(BaseModel):
    start: str
    end: str
    initial_equity: float = Field(gt=0)

class DataConfig(BaseModel):
    source: Literal["local", "exchange"]
    path: str | None = None

class ExecutionConfig(BaseModel):
    simulate: bool

class AccountConfig(BaseModel):
    initial_equity: float = Field(gt=0)

class ExchangeConfig(BaseModel):
    name: str
    testnet: bool

class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project: ProjectConfig
    market: MarketConfig
    strategy: StrategyConfig
    regime: RegimeConfig
    atr: ATRConfig
    risk: RiskConfig
    position: PositionConfig
    leverage: LeverageConfig
    management: ManagementConfig
    cost: CostConfig
    environment: EnvironmentConfig | None = None
    backtest: BacktestConfig | None = None
    data: DataConfig | None = None
    execution: ExecutionConfig | None = None
    account: AccountConfig | None = None
    exchange: ExchangeConfig | None = None

def load_yaml(path: str | Path) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a mapping: {path}")
    return data

def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def load_config(base_path: str | Path, environment_path: str | Path | None = None) -> AppConfig:
    config = load_yaml(base_path)
    if environment_path is not None:
        config = _deep_merge(config, load_yaml(environment_path))
    return AppConfig.model_validate(config)

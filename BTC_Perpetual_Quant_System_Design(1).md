# BTC 永续合约量化交易系统设计

> 版本：V1.0  
> 目标：构建一个适用于 BTC 永续合约、5–10 倍杠杆、支持多空双向交易的中低频量化交易系统。  
> 核心周期：4H；1D 用于大级别状态辅助。  
> 设计原则：先控制风险，再追求收益；先做可回测最小系统，再逐步增加因子。

---

## 1. 系统核心思想

系统不直接预测“下一根 K 线涨还是跌”，而采用以下流程：

```text
市场数据
  ↓
Feature Engine
  ↓
Market Regime
  ↓
Signal
  ↓
Risk Budget
  ↓
ATR Stop
  ↓
Position Sizing
  ↓
Leverage / Margin
  ↓
Order Execution
  ↓
Position Management
  ↓
PnL / Risk Monitor
  ↓
Backtest / Analysis
```

核心原则：

1. **Regime 决定风险预算，不直接决定仓位。**
2. **ATR 决定止损距离。**
3. **止损距离 + 最大亏损金额决定仓位。**
4. **杠杆只是保证金效率工具，不是风险预算工具。**
5. **单笔风险和组合总风险都必须受控。**
6. **正常止损应该先于强平发生。**
7. **先完成最小可回测系统，再增加复杂指标。**

---

# 2. 系统总体架构

```text
                    BTC Perpetual Quant System
                              │
                ┌─────────────┴─────────────┐
                │                           │
             Market Data                Account Data
                │                           │
      ┌─────────┼─────────┐          ┌──────┴──────┐
      │         │         │          │             │
     Price      OI     Funding      Equity      Position
      │         │         │
      ├─────────┼─────────┤
      │         │         │
     ATR    ETF Flow   Liquidation
      │         │         │
      └─────────┼─────────┘
                ↓
          Feature Engine
                ↓
          Regime Detector
                ↓
       ┌────────┼────────┐
       ↓        ↓        ↓
     BULL    NEUTRAL    BEAR
       │        │        │
       └────────┼────────┘
                ↓
          Signal Engine
                ↓
           Risk Engine
                ↓
         Position Sizing
                ↓
         Order Management
                ↓
          Execution Engine
                ↓
         Position / PnL
                ↓
          Risk Monitor
```

---

# 3. 第一版数据

第一版只需要以下数据：

## 3.1 BTC OHLCV

```text
timestamp
open
high
low
close
volume
```

周期：

```text
1H
4H
1D
```

其中：

- **4H：主要交易周期**
- **1D：大级别趋势/状态辅助**
- **1H：后续可用于更精细的入场**

## 3.2 衍生品数据

```text
Open Interest
Funding Rate
Liquidation
```

## 3.3 BTC ETF

```text
BTC ETF Net Flow
```

第一版 Feature：

```text
Price
Volume
ATR
OI
Funding
Liquidation
ETF Flow
```

后续再加入：

```text
Stablecoin Supply
Exchange BTC Balance
MVRV
NUPL
DXY
US10Y
Fed / Global Liquidity
```

---

# 4. ATR：波动率与止损

ATR（Average True Range）用于衡量市场的典型波动幅度。

True Range：

```text
TR = max(
    High - Low,
    abs(High - PreviousClose),
    abs(Low - PreviousClose)
)
```

第一版：

```text
ATR(14)
```

同时计算：

```text
ATR% = ATR / Close
```

## 4.1 ATR 的作用

ATR 不判断涨跌，而是回答：

> 当前市场通常波动多大？

因此主要用于：

- 止损距离
- 仓位大小
- 波动率调整
- Trailing Stop

## 4.2 ATR 止损

第一版：

```text
Stop Distance = 1.5 × ATR
```

Long：

```text
Stop = Entry - 1.5 × ATR
```

Short：

```text
Stop = Entry + 1.5 × ATR
```

---

# 5. Bull / Neutral / Bear 市场状态

系统将市场划分为三个状态：

```text
BULL
NEUTRAL
BEAR
```

Regime 不等于交易信号。

例如：

```text
BULL ≠ 立即做多
```

而表示：

> 当前环境优先寻找多头机会。

---

# 6. Regime Score

第一版可以使用：

```text
Regime Score =
    Price Score
  + ETF Score
  + Leverage Score
  + Momentum Score
```

每个因子：

```text
+1 = Bullish
 0 = Neutral
-1 = Bearish
```

总分：

```text
-4 ~ +4
```

映射：

| Score | Regime |
|---:|---|
| +3 ~ +4 | Bull |
| +1 ~ +2 | Bull-lite |
| -1 ~ +1 | Neutral |
| -2 ~ -1 | Bear-lite |
| -4 ~ -3 | Bear |

为了减少交易频率，正式策略可以简化为：

```python
if score >= 2:
    regime = "BULL"
elif score <= -2:
    regime = "BEAR"
else:
    regime = "NEUTRAL"
```

---

# 7. Price Score

研究阶段可以先使用固定结构，例如：

```text
BTC > 87K
4H Close Confirmation
    → +1

BTC < 81K
4H Close Confirmation
    → -1

81K ~ 87K
    → 0
```

但正式回测不建议永久写死这些价格。

更合理的动态结构：

```text
20D High
20D Low
Swing High
Swing Low
Volume Profile
ATR
```

用于动态计算支撑与阻力。

---

# 8. ETF Flow Score

ETF Flow 不建议简单使用正负号。

例如：

```text
+10M
+50M
+500M
```

虽然都是正数，但市场意义不同。

第一版可以使用标准化：

```text
ETF Z-Score = ZScore(ETF Flow, 30)
```

例如：

```text
Z > +1       → +1
-1 ~ +1      → 0
Z < -1       → -1
```

---

# 9. OI + Funding：杠杆状态

不能单独使用 OI 判断 Bull / Bear。

例如：

### 健康上涨

```text
Price ↑
OI ↑
Funding 正常
```

可以偏 Bullish。

### 杠杆拥挤

```text
Price ↑
OI ↑↑
Funding ↑↑
```

不能简单认为更 Bullish。

因为可能意味着：

```text
Long Crowding
```

存在较高的清算风险。

因此 OI 和 Funding 应联合判断。

---

# 10. Signal Engine

Regime 与 Signal 分离。

## 10.1 Bull

主要寻找：

```text
Breakout
Pullback
Trend Continuation
```

逻辑：

```text
BULL
  │
  ├── Breakout → LONG
  ├── Pullback → LONG
  └── No Setup → WAIT
```

## 10.2 Neutral

主要寻找：

```text
Range Long
Range Short
```

例如：

```text
Range Low → Long
Range High → Short
Range Middle → WAIT
```

Neutral 状态不追涨杀跌。

## 10.3 Bear

主要寻找：

```text
Breakdown
Failed Rebound
Trend Continuation
```

以 Short 为主。

---

# 11. Risk Engine

Risk Engine 是整个系统的核心。

建议第一版参数：

```yaml
risk:
  bull: 0.0075
  neutral: 0.0035
  bear: 0.003

  max_portfolio_risk: 0.02

  daily_loss_limit: 0.02
  weekly_loss_limit: 0.05
```

含义：

```text
Bull      单笔风险 0.75%
Neutral   单笔风险 0.35%
Bear      单笔风险 0.30%
```

这些是第一版研究参数，不应直接视为实盘最优参数，最终需要通过回测验证。

---

# 12. Position Sizing

最重要的公式：

```text
Position Size =
    Account Equity × Risk %
    ------------------------
        |Entry - Stop|
```

例如：

```text
账户权益 = $100,000
单笔风险 = 0.5%
最大亏损 = $500

Entry = $84,000
Stop  = $80,000

Position =
500 / 4,000
= 0.125 BTC
```

名义仓位：

```text
0.125 × 84,000
= $10,500
```

---

# 13. 杠杆设计

核心原则：

```text
Leverage ≠ Position Size
```

例如：

```text
Notional = $10,500
```

5x：

```text
Margin ≈ $2,100
```

10x：

```text
Margin ≈ $1,050
```

但在正确的 Position Sizing 下：

```text
最大止损亏损 ≈ $500
```

因此：

> 杠杆改变的是保证金占用，不应该主动改变你的最大风险。

第一版建议：

```text
默认：5x
最大：10x
```

甚至第一阶段可以统一使用：

```text
5x
```

先验证策略，再研究保证金效率。

---

# 14. Portfolio Risk

不能只控制单笔风险。

例如：

```text
BTC Long  = 0.5% risk
BTC Short = 0.5% risk
Another   = 0.5% risk
```

组合风险：

```text
1.5%
```

因此必须设置：

```text
max_portfolio_risk
```

例如：

```text
Bull      ≤ 2%
Neutral   ≤ 1%
Bear      ≤ 0.75%
```

当：

```text
Current Risk + New Trade Risk
    >
Max Portfolio Risk
```

则：

```text
Reject Order
```

---

# 15. Daily / Weekly Kill Switch

## Daily

```text
Daily PnL <= -2%
    ↓
停止开新仓
```

## Weekly

```text
Weekly PnL <= -5%
    ↓
进入 Defensive Mode
    ↓
Risk × 0.5
```

目的：

> 防止策略在异常市场环境中连续亏损。

---

# 16. Position Management

开仓后需要管理：

```text
Stop Loss
Take Profit
Break Even
Trailing Stop
Time Stop
Regime Change
```

第一版不要过度复杂。

## 16.1 初始止损

```text
1.5 ATR
```

## 16.2 1R

定义：

```text
1R = 初始止损对应的资金风险
```

例如：

```text
Entry = 84K
Stop = 79.5K

Stop Distance = 4.5K

1R = $4.5K 的价格波动
```

## 16.3 Break Even

```text
Profit >= 1R
    ↓
Stop → Entry
```

## 16.4 Trailing

```text
Profit >= 2R
    ↓
启动 ATR Trailing
```

---

# 17. Liquidation Safety

对于 5–10x 永续合约，必须同时监控：

```text
Entry
Position Size
Leverage
Margin
Stop Price
Liquidation Price
```

要求：

```text
正常 Stop Price
        ↓
应该明显早于
        ↓
Liquidation Price
```

如果：

```text
Stop ≈ Liquidation Price
```

说明杠杆、保证金或仓位设计存在问题。

---

# 18. 完整状态机

```text
                  ┌─────────────┐
                  │    FLAT     │
                  └──────┬──────┘
                         ↓
                  Detect Regime
                         │
             ┌───────────┼───────────┐
             ↓           ↓           ↓
           BULL       NEUTRAL       BEAR
             │           │           │
           LONG       RANGE         SHORT
           SETUP       SETUP         SETUP
             │           │           │
             └───────────┼───────────┘
                         ↓
                    Risk Check
                         │
                  ┌──────┴──────┐
                  │             │
                 PASS          FAIL
                  │             │
                  ↓             ↓
                ORDER          WAIT
                  │
                  ↓
              POSITION
                  │
        ┌─────────┼──────────┐
        ↓         ↓          ↓
       SL        TP       Regime Change
        │         │          │
        └─────────┼──────────┘
                  ↓
                FLAT
```

---

# 19. Backtest Engine

建议采用事件驱动架构：

```text
MarketEvent
    ↓
FeatureEngine
    ↓
RegimeDetector
    ↓
SignalEngine
    ↓
RiskManager
    ↓
Order
    ↓
Execution
    ↓
Portfolio
    ↓
PnL
```

不要把所有逻辑塞进一个：

```python
for candle in candles:
    ...
```

的大函数。

---

# 20. 回测必须模拟

至少包括：

```text
Trading Fee
Slippage
Funding Fee
```

净收益：

```text
Net PnL =
Gross PnL
- Trading Fee
- Slippage
- Funding
```

永续合约回测尤其不能忽略 Funding。

---

# 21. 回测指标

至少统计：

```text
Total Return
CAGR
Sharpe
Sortino
Max Drawdown
Calmar
Win Rate
Profit Factor
Expectancy
Number of Trades
Average Holding Time
Long PnL
Short PnL
Bull PnL
Neutral PnL
Bear PnL
```

---

# 22. R Multiple

建议使用 R 作为统一风险单位：

```text
R = PnL / Initial Risk
```

例如：

```text
+2R
-1R
+0.5R
-1R
```

这样可以避免不同账户规模、不同仓位对策略研究造成干扰。

---

# 23. 策略消融实验

不要直接问：

> 策略能不能赚钱？

应该逐步验证每个因子的贡献。

```text
Strategy A
Price

Strategy B
Price + ATR

Strategy C
Price + ATR + OI

Strategy D
Price + ATR + OI + Funding

Strategy E
Price + ATR + OI + Funding + ETF
```

比较：

```text
Sharpe
Max Drawdown
Expectancy
Profit Factor
Turnover
```

目标是找出：

> 哪些因子真正改善了风险收益特征。

---

# 24. 第一版配置

```yaml
market:
  symbol: BTCUSDT
  timeframe: 4h

regime:
  bull_score: 2
  bear_score: -2

risk:
  bull: 0.0075
  neutral: 0.0035
  bear: 0.003

  max_portfolio_risk: 0.02
  daily_loss_limit: 0.02
  weekly_loss_limit: 0.05

atr:
  period: 14
  stop_multiple: 1.5

leverage:
  default: 5
  max: 10

management:
  breakeven_r: 1.0
  trailing_start_r: 2.0
```

这些参数仅作为第一版研究基线，需要通过历史数据、样本外测试和压力测试验证。

---

# 25. Python 项目结构

```text
btc-perp-system/
│
├── config/
│   └── settings.py
│
├── data/
│   ├── loader.py
│   ├── market_data.py
│   └── storage.py
│
├── features/
│   ├── price.py
│   ├── volatility.py
│   ├── derivatives.py
│   └── etf.py
│
├── regime/
│   └── detector.py
│
├── strategy/
│   └── signal.py
│
├── risk/
│   ├── risk_manager.py
│   ├── position_sizer.py
│   └── stop.py
│
├── portfolio/
│   ├── position.py
│   └── pnl.py
│
├── execution/
│   └── executor.py
│
├── backtest/
│   ├── engine.py
│   ├── event.py
│   └── metrics.py
│
├── tests/
│
└── main.py
```

---

# 26. 开发路线

## Phase 1：最小可回测系统

```text
BTC OHLCV
    ↓
ATR
    ↓
Long / Short Signal
    ↓
1.5 ATR Stop
    ↓
Position Sizing
    ↓
Fee / Slippage
    ↓
Backtest
```

目标：

> 先把交易、风险和回测链路跑通。

## Phase 2：加入 Regime

```text
Price
+ ATR
+ OI
+ Funding
    ↓
Bull / Neutral / Bear
    ↓
Regime-based Risk
```

## Phase 3：增加资金流

```text
ETF Flow
Liquidation
```

完善 Regime Score。

## Phase 4：真实永续合约回测

加入：

```text
Funding
Fee
Slippage
Leverage
Liquidation
```

## Phase 5：增加宏观 / 链上因子

```text
Stablecoin
Exchange Balance
MVRV
NUPL
DXY
US10Y
Global Liquidity
```

## Phase 6：Paper Trading

```text
Real-time Data
    ↓
Signal
    ↓
Simulated Order
    ↓
Real-time Risk Monitor
```

## Phase 7：小资金实盘

只有在：

```text
Backtest
+
Out-of-Sample
+
Paper Trading
+
Risk Validation
```

均通过后，再考虑小资金实盘。

---

# 27. 最终核心规则

整个系统可以浓缩成：

```text
┌─────────────────────────────────────┐
│  1. 判断 Market Regime              │
│     Bull / Neutral / Bear           │
├─────────────────────────────────────┤
│  2. 判断 Trading Setup              │
│     Long / Short / Wait             │
├─────────────────────────────────────┤
│  3. 根据 Regime 确定 Risk Budget    │
│     0.75% / 0.35% / 0.30%           │
├─────────────────────────────────────┤
│  4. ATR 确定 Stop Distance          │
│     1.5 × ATR                       │
├─────────────────────────────────────┤
│  5. 根据风险反推 Position Size      │
│     Risk $ / Stop Distance          │
├─────────────────────────────────────┤
│  6. 检查 Portfolio Risk             │
├─────────────────────────────────────┤
│  7. 检查 Liquidation Safety         │
├─────────────────────────────────────┤
│  8. 执行订单                        │
├─────────────────────────────────────┤
│  9. 1R → Break Even                 │
│     2R → ATR Trailing               │
├─────────────────────────────────────┤
│ 10. Daily / Weekly Kill Switch      │
└─────────────────────────────────────┘
```

**一句话总结：**

> **Regime 决定“允许承担多少风险”，Signal 决定“做多还是做空”，ATR 决定“止损多远”，Position Sizing 决定“应该开多大仓”，Leverage 决定“占用多少保证金”，Risk Manager 决定“什么时候不能再交易”。**

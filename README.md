# 📈 WRSE QUANT ENGINE (Walkforward-Regime-Shock-Execution)

[🚀 Interactive Backtest Dashboard (HTML Viewer)](https://hoioioio.github.io/WRSE-QUANT-ENGINE/)
[📄 Dashboard Source (docs/index.html)](docs/index.html) (Served via GitHub Pages `/docs`; update URL if repo name changes.)

*"From problem definition to an execution-aware quantitative pipeline."*\
This project is a **crypto futures quantitative research and backtesting engine** engineered to survive real market frictions (fees, slippage, funding) and **regime changes**. It fundamentally rejects in-sample curve-fitting and has been validated exclusively via strict **Walk-Forward Out-of-Sample (OOS)** testing.

***

## 📑 Table of Contents

1. [Project Overview](#1-project-overview-)
2. [Problem Statement](#2-problem-statement-)
3. [Hypothesis](#3-hypothesis-)
4. [Data & Research Methodology](#4-data--research-methodology-)
5. [Strategy Design](#5-strategy-design-)
6. [Risk Management](#6-risk-management-)
7. [Backtest Results (WFO OOS)](#7-backtest-results-wfo-oos-20212024-train-starts-2020-)
8. [Engine Architecture](#8-engine-architecture-)
9. [Live Trading Results](#9-live-trading-results-)
10. [Failures & Improvements](#10-failures--improvements-)
11. [Conclusion](#11-conclusion-)

***

## 1. Project Overview 🔭

- **Core Goal**: Build an engine that translates theoretical research hypotheses into a repeatable, institutional-grade pipeline: `Data` → `Hypothesis` → `OOS Validation` → `Execution-aware Simulation` → `Reporting`.
- **Output Artifacts**: Live GitHub Pages dashboard (`docs/`), reproducible CLI benchmarking, and automated PNG/JSON tear sheets.
- **Related Analytics (Dune)**: [LST/LRT Monitor – stETH (Ethereum)](https://dune.com/hoin/lst-lrt-monitor-steth-ethereum) (may require login if Cloudflare blocks anonymous access).

## 2. Problem Statement 🚨

*Most retail crypto futures strategies fail in live markets because they ignore structural realities.* This engine was built to solve four critical problems:

1. **Regime Changes**: Static parameters break when market regimes shift (e.g., bull trends vs. overlapping chop), leading to drawdown expansion.
2. **Volatility Clustering**: Expanding volatility inherently increases leverage risk and exposes liquidity tails.
3. **Execution Frictions**: Theoretical 'paper alpha' is frequently erased by maker/taker fees and order-book slippage.
4. **Funding Rate Extremes**: Overcrowded derivatives markets introduce structural return headwinds when funding rates spike.

> **Execution Mandate**: "I am not just designing a curve-fitted 'signal', but engineering an **OOS-validated, execution-aware system** where backtests mirror realizable PnL."

## 3. Hypothesis 🧪

The engine's logic is grounded in three core quantitative hypotheses:

- **Hypothesis I (Trend)**: Volatility expansion accompanied by directional flow is exploitable, provided risk is aggressively clipped during shock/overcrowded states.
- **Hypothesis II (Reversal/Shock)**: Funding rate extremes and liquidity vacuums should probabilistically trigger mean-reversion counter-trades or force immediate portfolio de-risking.
- **Hypothesis III (Robustness)**: A dual-model ensemble (Trend + Shock Defense) utilizing dynamic weight allocations via *Walk-Forward Parameter Locking* will structurally defend against data-snooping bias and regime shifts.

## 4. Data & Research Methodology 📊

To bridge the gap between backtests and reality, WRSE adheres to a strict quantitative protocol:

- **Evaluation Protocol**: **Walk-Forward Analysis (WFO)**. The optimizer scans a historical `Train` window, locks the optimal ensemble parameters, and accumulates performance solely on the unseen future `Test (OOS)` window.
- **Bias Control**: Zero Look-Ahead Bias and Survivorship-Bias resistant logic.
- **Microstructure Frictions**: Hardcoded Maker/Taker limits. Real dynamic slippage (bps) is incurred upon limit-order fallbacks or market impacts.
- **Reproducibility**: Clear data schemas and execution pathways documented in [`docs/reproducibility.md`](docs/reproducibility.md).

## 5. Strategy Design ⚙️

WRSE operates as a cohesive systemic engine rather than a monolithic script.

- 📡 **Signal Engine**:
  - *Trend Component*: Evaluates multi-timeframe directional momentum (`v2xa-style`).
  - *Shock Component*: Normalizes 9 dimensions of market features to train a **Ridge Regression Signed Classifier**, producing a predictive `shock_score`.
- ⚖️ **Portfolio Engine**: Conducts a grid search across localized Train windows to optimize the capital allocation weight between the Trend and Shock models.
- ⚡ **Execution Engine**: Models L2 order book micro-deviations. If an optimal limit order is not filled (`maker`), the system forces a delayed market order execution (`taker`) while incurring heavy slippage penalties.

## 6. Risk Management 🛡️

*Risk is treated as a first-class citizen, operating independently from the signal generation.*

- **Volatility Targeting**: Dynamic portfolio slot limits and per-trade risk scaling based on current market state.
- **Funding Shock Suppression**: Z-score normalization of funding rates to hard-cap positional entries during over-leveraged market extremes.
- **Drawdown Control**: Hard-stop logic mapped separately for both trend and mean-reverting components.
- **Stress-Test Execution**: Evaluates performance by comparing `AB Hybrid` (realistic limits) against a hyper-pessimistic `Taker-only` environment.

## 7. Backtest Results (WFO OOS, 2021→2024; Train starts 2020) 📈

> 💡 *All metrics below are 100% Out-of-Sample. The engine has never "seen" the data it is being evaluated against.*

### 7.1 Aggregate Metrics (AB Hybrid vs Stress Test)

Interpretation note:

- Sharpe is computed from the daily equity curve produced by a 4h bar simulator, with fees/slippage/funding applied (execution-aware realism tends to suppress headline Sharpe).

| Metric                 | AB Hybrid (Execution-Aware) | Taker-only (Pessimistic Penalty) |
| :--------------------- | :-------------------------: | :------------------------------: |
| **Total Return**       |         **+55.74%**         |              +43.10%             |
| **Annualized (CAGR)**  |          **11.74%**         |               9.39%              |
| **Max Drawdown (MDD)** |         **-11.99%**         |              -12.73%             |
| **Sharpe Ratio**       |           **0.78**          |               0.64               |
| **Trading Days**       |          1,457 Days         |            1,457 Days            |

![Strategy Equity vs Bitcoin Benchmark](docs/assets_public/equity_vs_btc_log.png)

### 7.2 Yearly OOS Splits (Train → Test)

|    📅 Test Year    | OOS Return (AB) | MDD (AB) | Sharpe Ratio (AB/Taker) | Ensemble Weight (Locked) |
| :----------------: | :-------------: | :------: | :---------------------: | :----------------------: |
| **2021** (Split 1) |      +9.80%     |  -11.99% |       0.61 / 0.47       |    0.5 (*Train: 2020*)   |
| **2022** (Split 2) |      +0.56%     |  -10.81% |       0.11 / -0.15      | 0.3 (*Train: 2020-2021*) |
| **2023** (Split 3) |     +28.39%     |  -9.59%  |       1.19 / 1.10       | 0.7 (*Train: 2020-2022*) |
| **2024** (Split 4) |      +9.86%     |  -2.88%  |       1.38 / 1.08       | 0.3 (*Train: 2020-2023*) |

> 🔍 **Regime Analysis**: In the 2022 deleveraging cycle, entries were aggressively suppressed under funding/volatility chaos, stalling growth while containing drawdowns. In the directional trends of 2023, the trend component dominated and drove most of the upside.

![WFO OOS Sharpe](docs/assets_public/wfo_oos_sharpe.png)

## 8. Engine Architecture 🧩


Optional native acceleration:
- A Rust port of the execution pricing logic is included under `wrse_rust/` (optional). The Python implementation is the default fallback.

```text
📁 C:\wrse\
 ├── 📁 alpha/
 │    └── shock.py         # Ridge-based Jump Risk & Reversal Classifier
 ├── 📁 backtest/
 │    ├── simulators.py    # High-fidelity Bar-level Simulator (TCA)
 │    ├── walkforward.py   # Rolling WFO Optimizer & Weight Allocator
 │    └── metrics.py       # PnL Evaluator (Sharpe, MDD, Compounding)
 ├── 📁 data/
 │    └── loader.py        # Cached historical universe parser
 ├── 📁 execution/
 │    └── models.py        # L2 Maker→Taker Execution slippage logic
 ├── 📁 utils/
 │    └── config.py        # TOML configuration loader
 ├── 📁 config/
 │    └── strategy_params.example.toml # Environment Constraints
 ├── 📁 docs/                      # Interactive HTML Dashboard
 ├── 📁 wrse_rust/                 # (Optional) Rust port of execution logic
 ├── cli.py                     # Command-line Execution Interface
 ├── report.py                  # Graphical tear-sheet & JSON generator
 ├── verify_portfolio.py        # Output consistency checker
 └── requirements.txt
```

### Key Files (clickable)

- Signal: [alpha/shock.py](alpha/shock.py)
- WFO & ensemble: [backtest/walkforward.py](backtest/walkforward.py)
- Simulator (fees/slippage/funding): [backtest/simulators.py](backtest/simulators.py)
- Metrics & yearly tables: [backtest/metrics.py](backtest/metrics.py)
- Execution model (maker→taker): [execution/models.py](execution/models.py)
- Config loader: [utils/config.py](utils/config.py)
- Example config: [config/strategy_params.example.toml](config/strategy_params.example.toml)
- Report exporter (PNG/JSON): [report.py](report.py)

## 9. Live Trading Results 🌐

- Live trading results are not included in this repository.
- The codebase decouples `Signal`, `Risk`, and `Execution` layers so the same mechanics can be integrated into a WebSocket-driven live environment without changing the research logic.

## 10. Failures & Improvements 🛠️

A healthy quant engine is never finished. Core areas currently identified for future upgrades:

1. **Regime Over-Sensitivity**: In 2022, extreme shock suppression choked out too many neutral trades. Adding a Gaussian Mixture Model (GMM) or HMM to identify micro-regimes could decouple macro-fear from localized opportunities.
2. **Path Dependency Verification**: Incorporating Monte Carlo (MC) resampling on the trade sequence will help tighten statistical confidence intervals around the estimated Sharpe ratio and profit factors.
3. **Execution Latency Improvements**: Python is optimal for research but sub-optimal for L2 parsing latency. Moving the `execution/models.py` equivalent mechanics into a Rust/C++ module would minimize the queue-position latency currently modeled statistically.

## 11. Conclusion 🏁

The WRSE Quant Engine demonstrates a mature approach to crypto-derivatives systems: prioritizing **problem-driven design**, **data-snooping eradication**, and **execution-aware realism** over naive strategy curve-fitting.

***

### 🖥️ Quick Reproduce

```bash
cd C:\wrse
pip install -r requirements.txt
python cli.py wfo --config config/strategy_params.example.toml --write_csv ./outputs
python report.py --config config/strategy_params.example.toml --public
python verify_portfolio.py
```

Optional (Rust extension):

```bash
cd wrse_rust
pip install maturin
maturin develop --release
```

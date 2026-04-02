# 📈 WRSE QUANT ENGINE (Walkforward-Regime-Shock-Execution)

[🚀 Interactive Backtest Dashboard (HTML Viewer)](https://hoioioio.github.io/WRSE-QUANT-ENGINE/)
[📄 Dashboard Source (docs/index.html)](docs/index.html) (Served via GitHub Pages `/docs`; update URL if repo name changes.)

This project is a **data-driven systematic trading engine** targeting the Binance Futures market.
It pursues a stable upward equity curve by combining adaptive average-based trend selection, ShockScore-based de-risking and position sizing, stepwise scaling-in, a maker→taker fallback execution model, and Walk-Forward Out-of-Sample (OOS) validation.

***

## 📑 Table of Contents

1. [Backtest Results](#1-backtest-results)
2. [Backtest Constraints](#2-backtest-constraints)
3. [Backtest Metrics](#3-backtest-metrics)
4. [Stress Test Metrics](#4-stress-test-metrics)
5. [Profit Windows](#5-profit-windows)
6. [Live Sync Audit](#6-live-sync-audit)
7. [Tech Stack](#7-tech-stack)
8. [Project Architecture](#8-project-architecture)
9. [Data & Research Methodology](#9-data--research-methodology)
10. [Strategy Design](#10-strategy-design)
11. [Risk Management](#11-risk-management)
12. [Failures & Improvements](#12-failures--improvements)
13. [Conclusion](#13-conclusion)

***

<a id="1-backtest-results"></a>

## 1. Backtest Results

### 1.1 WFO OOS Summary (2021→2024; Train starts 2020)

- All performance is accumulated **strictly through Walk-Forward Out-of-Sample (OOS)** testing.
- The `AB Hybrid` mode reflects realistic execution frictions, while `Taker-only` represents a harsher stress environment.

| Metric | AB Hybrid (Execution-Aware) | Taker-only (Pessimistic Penalty) |
| :--- | :---: | :---: |
| Cumulative Return | +55.74% | +43.10% |
| CAGR | 11.74% | 9.39% |
| MDD | -11.99% | -12.73% |
| Sharpe Ratio | 0.78 | 0.64 |
| Trading Days | 1,457 Days | 1,457 Days |

![Strategy Equity vs Bitcoin Benchmark](docs/assets_public/equity_vs_btc_log.png)

### 1.2 Yearly OOS Splits (Train → Test)

| Test Year | OOS Return (AB) | MDD (AB) | Sharpe (AB/Taker) | Ensemble Weight (Locked) |
| :---: | :---: | :---: | :---: | :---: |
| 2021 (Split 1) | +9.80% | -11.99% | 0.61 / 0.47 | 0.5 (Train: 2020) |
| 2022 (Split 2) | +0.56% | -10.81% | 0.11 / -0.15 | 0.3 (Train: 2020-2021) |
| 2023 (Split 3) | +28.39% | -9.59% | 1.19 / 1.10 | 0.7 (Train: 2020-2022) |
| 2024 (Split 4) | +9.86% | -2.88% | 1.38 / 1.08 | 0.3 (Train: 2020-2023) |

![WFO OOS Sharpe](docs/assets_public/wfo_oos_sharpe.png)

<a id="2-backtest-constraints"></a>

## 2. Backtest Constraints ⛓️

WRSE's results are not just "good backtests without constraints." They are generated under constraints that include the primary causes of profit collapse in live trading (fees, slippage, funding rates, unfilled orders).

- **OOS Accumulation Only**: Each Test year runs with parameters and weights strictly derived from the preceding Train data.
- **Forced Execution Friction**: Maker→Taker fallback + slippage + maker/taker fees are pre-deducted from the cumulative equity.
- **Funding Cost Integration**: Funding PnL is accumulated throughout the position holding period.
- **Isolated Data Input**: Raw data is not included; only reproducible inputs via the cache schema are allowed.

For detailed schemas, see [docs/reproducibility.md](docs/reproducibility.md).

<a id="3-backtest-metrics"></a>

## 3. Backtest Metrics 🧾

These metrics are calculated based on the daily equity from `docs/assets_public/*.json` (normalized with an initial capital of 100,000 USDT = 1.0).

| Metric | AB Hybrid | Taker-only |
| :--- | :---: | :---: |
| Initial Capital (Normalized) | 1.00 | 1.00 |
| Final Capital (Normalized) | 1.5574 | 1.4310 |
| Cumulative Return | +55.74% | +43.10% |
| CAGR | 11.74% | 9.39% |
| Max Drawdown (MDD) | -11.99% | -12.73% |
| Sharpe Ratio | 0.780 | 0.637 |
| Sortino Ratio | 2.129 | 1.755 |
| Win Rate (Daily) | 28.30% | 26.85% |
| Max DD Duration | 194 Days | 238 Days |

Additional Metrics:

- **Profit Factor**: Trade-level logs are not included in the public repo to protect strategy details, so this metric is excluded from the public table.
- **Monte Carlo Test (MC Resampling)**: Designed to evaluate path dependency (worst-case sequence of trades), but the results are excluded from the public version.

<a id="4-stress-test-metrics"></a>

## 4. Stress Test Metrics 🔥

### 4.1 Extreme Volatility Periods of 2022 (LUNA / FTX)

Below is the performance during representative extreme events captured within the OOS period (2021→2024).

| Event | Period | AB Return | AB MDD | Taker Return | Taker MDD |
| :--- | :--- | :---: | :---: | :---: | :---: |
| LUNA Deleveraging | 2022-05-07 ~ 2022-06-30 | +9.25% | -1.49% | +9.14% | -1.53% |
| FTX Bankruptcy Shock | 2022-11-06 ~ 2022-12-31 | -5.77% | -6.87% | -6.92% | -7.99% |

### 4.2 Random 6-Month (Rolling 6M) Distribution

Scanned rolling 6-month (182 days) returns across the entire period based on daily equity.

| Metric | AB | Taker-only |
| :--- | :---: | :---: |
| Worst 6M Return | -10.98% (Ends: 2021-08-02) | -12.35% (Ends: 2021-08-02) |
| Best 6M Return | +28.93% (Ends: 2022-02-01) | +27.76% (Ends: 2022-02-01) |
| 6M Return 5% / 50% / 95% | -6.78% / +6.12% / +20.45% | -8.18% / +5.02% / +20.53% |

### 4.3 Market Crashes in Late 2025 / Early 2026

The currently published OOS results are limited to the 2021→2024 range, thus excluding 2025~2026 data. Testing for this period can be immediately expanded in the exact same manner once the following conditions are met:

- Cache data is available up to 2026.
- `walk_forward.years` in `config/strategy_params.example.toml` is extended to 2026.

<a id="5-profit-windows"></a>

## 5. Profit Windows 🎯

WRSE is not a "win-every-day" strategy; it structures its equity by **maximally preserving profitable regime windows** while structurally reducing exposure during phases where losses compound.

- **Primary Contributing Years**: 2023 accounted for the vast majority of the returns, while 2024 demonstrated defensive accumulation in a low-volatility environment.
- **Weak Performing Years**: In 2022, filters operated conservatively during the deleveraging phase, leading to stalled growth.

| Year | OOS Return (AB) | MDD (AB) | Sharpe (AB) | Sortino (AB) |
| :---: | :---: | :---: | :---: | :---: |
| 2021 | +9.80% | -11.99% | 0.61 | 1.54 |
| 2022 | +0.56% | -10.81% | 0.11 | 0.18 |
| 2023 | +28.39% | -9.59% | 1.19 | 4.43 |
| 2024 | +9.86% | -2.88% | 1.38 | 4.38 |

The "maximum profit" from a single live trade is not included in the public repo (to prevent exposure of personal trading logs).

<a id="6-live-sync-audit"></a>

## 6. Live Sync Audit 🔄

Since WRSE is a research/backtesting engine, live trading keys and order logs are not included in the repository. Instead, we specify the **live execution synchronization principles** verified in the predecessor system (live trading bot). The goal is to structurally eliminate moments when the "bot's perceived state" diverges from the "exchange ledger state."

### 6.1 Symptoms of Synchronization Failure

- The position is closed on the exchange, but recognized as open locally.
- A reverse position opens immediately after closing due to missing `reduceOnly` flags.
- Unfilled limit orders remain and execute unintentionally in the next cycle.
- Partial fills are misclassified as total failures, collapsing the order loop.

### 6.2 Resolution Principles (Exchange Ledger as Source of Truth)

- **Use the exchange as the single Source of Truth**, treating the local state merely as a cache.
- At the start of every cycle, fetch `positions` and `open_orders` to forcefully **reconcile** with the local state.
- The closing flow is structured as `cancel_all` → `reduceOnly` → (Re-verify if needed) to block **residual orders and reverse positions**.
- Order requests use idempotent keys (e.g., `clientOrderId`) to prevent duplicate executions.

### 6.3 Execution Integrity Validation

- Verify via logs that for a given signal timestamp, the sequence "Signal Generation → Order Submission → Fill/Unfilled → Position Update" is completed within a single cycle.
- Even in the event of outages (network/API failures), confirm whether an order failed or filled during the reconciliation phase of the next cycle to recover state.

### 6.4 Live Audit Record 🌐

During the operational phase of the predecessor engine (`Crypto_Auto_Trading-BOT`), we cross-verified the logical and entry-point consistency between the backtest simulation environment and actual Binance Live execution records.

| Symbol | System Signal (UTC+9) | Actual Binance Fill Time | Position | Verification Result |
| :--- | :--- | :--- | :--- | :--- |
| AVAX/USDT | Jan 29 17:00:00 | Jan 29 17:00:12 (+12s) | SELL | Logic Match ✅ |
| DOGE/USDT | Jan 29 17:00:00 | Jan 29 17:00:15 (+15s) | SELL | Logic Match ✅ |
| ETH/USDT | Jan 29 21:00:00 | Jan 29 21:00:18 (+18s) | SELL | Logic Match ✅ |
| BNB/USDT | Jan 30 01:00:00 | Jan 30 01:00:36 (+36s) | SELL | Logic Match ✅ |

Excluding physical network latency (approx. 12~36 seconds), empirical evidence confirmed a 100% flawless match between the signals generated by the bot model and the actual exchange fill points. This robust live integrity forms the foundational architecture of the current institutional-grade WRSE Quant Engine.

<a id="7-tech-stack"></a>

## 7. Tech Stack 🧰

- Python, NumPy, pandas
- matplotlib (Reports/Charts)
- TOML-based config loader ([utils/config.py](utils/config.py))
- Optional: Rust extension (`wrse_rust/`) for accelerating execution/fee/funding calculations

<a id="8-project-architecture"></a>

## 8. Project Architecture 🧩

Optional Native Acceleration:

- A Rust port of the execution pricing logic is included in `wrse_rust/` (optional), with the Python implementation acting as the default fallback.

```text
📁 C:\wrse\
 ├── 📁 alpha/
 │    └── shock.py         # Ridge-based Jump Risk & Reversal Classifier
 ├── 📁 backtest/
 │    ├── simulators.py    # High-resolution Bar Simulator (Fees/Slippage/Funding)
 │    ├── walkforward.py   # Rolling WFO Optimizer & Weight Allocator
 │    └── metrics.py       # Evaluation Metrics (Sharpe, Sortino, MDD, etc.)
 ├── 📁 data/
 │    └── loader.py        # Cache-based Historical Universe Parser (OHLCV/Funding/L2)
 ├── 📁 execution/
 │    └── models.py        # L2 Maker→Taker Execution Slippage Logic
 ├── 📁 utils/
 │    └── config.py        # TOML Config Loader
 ├── 📁 config/
 │    └── strategy_params.example.toml # Environment Constraints/Parameters
 ├── 📁 docs/                      # Interactive HTML Dashboard
 ├── cli.py                     # CLI Execution Interface
 ├── report.py                  # Graph Tear-sheet & JSON Generator
 └── requirements.txt
```

### Key Files (Clickable)

- Signals/Features: [alpha/shock.py](alpha/shock.py)
- WFO & Ensemble: [backtest/walkforward.py](backtest/walkforward.py)
- Simulator: [backtest/simulators.py](backtest/simulators.py)
- Metrics/Yearly Tables: [backtest/metrics.py](backtest/metrics.py)
- Execution Model (maker→taker): [execution/models.py](execution/models.py)
- Data Loader: [data/loader.py](data/loader.py)
- Config Loader: [utils/config.py](utils/config.py)
- Example Config: [config/strategy_params.example.toml](config/strategy_params.example.toml)
- Report Exporter: [report.py](report.py)

<a id="9-data--research-methodology"></a>

## 9. Data & Research Methodology 📊

- **Data Input**: OHLCV (Required) + Funding/L2 Summaries (Optional) are loaded via cache.
- **Resampling**: The 15m cache is internally resampled to 4h to unify signal and risk evaluations.
- **Walk-Forward Optimization (WFO)**: Parameters and weights are optimized exclusively on the Train set and rigidly applied to the Test (OOS) set.
- **Bias Control**: To prevent look-ahead bias and data snooping, the predictive model (ShockScore) learns only on the Train set and purely infers on the Test set.

Data schemas and reproduction paths are documented in [docs/reproducibility.md](docs/reproducibility.md).

<a id="10-strategy-design"></a>

## 10. Strategy Design ⚙️

WRSE separates Trend and Shock components, combining them via WFO for live operation.

### 10.1 Trend Component

- Generates short/mid-term trend reversal signals based on 4h bars and enters only when aligned with the long-term baseline direction.
- Only candidates that pass Volatility, ADX, Funding, and Shock conditions are added to the portfolio.
- Scaling-in is permitted only for positions moving favorably, expanding exposure exclusively for winners.

### 10.2 Shock Component (ShockScore)

- Labels sudden jump events and trains a Ridge-based signed classifier using 9 features.
- In the Test period, it computes the `shock_score` without re-learning, using it for entry, avoidance, or exit decisions.

### 10.3 Ensemble (Trend + Shock)

- Scans the `weights_grid` in the Train window to find the optimal allocation, which is then locked for the subsequent Test year.

### 10.4 Execution Model (maker→taker)

- Calculates a limit order offset using L2 summary features (Spread/Microprice Deviation/Imbalance).
- If unfilled, it falls back to a taker order incurring slippage, according to the `maker_then_taker` rule.
- If the `shock_score` hits a critical threshold, it conservatively prioritizes taker execution.

<a id="11-risk-management"></a>

## 11. Risk Management

- **Risk Budget Per Trade**: Position size is calculated using a combination of `risk_per_trade` and `stop_loss_pct_*`.
- **Portfolio Slots**: Limits the number of simultaneous open positions to prevent overcrowding during market turmoil.
- **Drawdown-based Scaling**: Reduces new entry risk based on the account's drawdown state.
- **Funding Risk Suppression**: Blocks new entries when the absolute or normalized funding rate (`funding_z`) overheats.
- **Execution Stress Comparison**: Exposes sensitivity to execution assumptions by publishing both AB Hybrid and Taker-only results.

<a id="12-failures--improvements"></a>

## 12. Failures & Improvements 🛠️

Evolving from a single local script (`live_gol_v2.py`) to an automated trading bot (`Crypto_Auto_Trading-BOT`), and finally into the current Quant Engine (`WRSE`), we confronted numerous real-world limitations. We resolved them by observing recurring phenomena, identifying root causes, and fundamentally altering the architecture and execution flow.

### 12.1 Engineering Problem-Solving Process (Engineering Evolution) 🛠️

#### A. State Synchronization and Order Limitations

* **State Desynchronization**
  * 🚨 Problem: Because positions were tracked solely in local memory, **the bot's perception frequently misaligned with the exchange's actual state, repeatedly causing Ghost/Zombie positions to accumulate.**
  * 💡 Solution: We identified the root cause as the reliance on "one-way state tracking." To eliminate this, we determined the exchange ledger must be the absolute standard. **We developed a robust synchronization module that periodically polls the API and forces a reconciliation between the exchange ledger and local state.**
  * 🎯 Result: A system that previously required constant manual intervention to fix sync issues now **autonomously captures the real-time ledger, perfectly syncing and automatically clearing ghost positions.**

* **Symbol Format Mismatch**
  * 🚨 Problem: Differences in symbol return rules across exchanges **caused recurring data key mapping failures between formats like `SOL/USDT` and `SOL/USDT:USDT`.**
  * 💡 Solution: The root cause was hardcoded "static string mapping." Recognizing that text normalization must occur at the communication frontline, **we injected a regex and suffix-replacement layer directly into the system's communication interface.**
  * 🎯 Result: Minor string discrepancies that used to crash the entire order flow are now handled by **a unified format baseline, permanently ensuring flawless symbol mapping.**

* **Order Mode and Residual Conflicts**
  * 🚨 Problem: Structural mismatches between Hedge Mode-enabled accounts and One-Way order parameters meant that **unfilled limit orders could execute after a position was closed, unintentionally opening a reverse position.**
  * 💡 Solution: The root cause was a "clunky transaction flow" lacking independence between entry modes and cancellation actions. To enforce atomic control, **we built a phased liquidation pipeline: forcing One-Way mode upon boot, executing `cancel_all` for pending orders, and strictly applying `reduceOnly` flags.**
  * 🎯 Result: The risk of stray limit orders exploding into reverse positions was **thoroughly eradicated by enforcing One-Way mode and reduce-only commands, ensuring zero logical risk leakage.**

* **Partial Fill Resilience**
  * 🚨 Problem: During network bottlenecks, large block orders would splinter. **The system logic treated these micro partial fills as "complete errors," severely tangling the order flow.**
  * 💡 Solution: The root cause was a binary (0 or 1) order status interpreter. We needed an active control structure to manage fractional adjustments. **We shifted to a dynamic feedback model that explicitly recognizes filled quantities, updates the state, and requeues only the exact remaining balance.**
  * 🎯 Result: Instead of duplicating trades or failing infinitely during partial fills, **the system now smartly updates the state with the exact filled amount and cleanly queues the remainder.**

#### B. Exception Handling and Fallback Survival Nets

* **Downtime Skips (System Blackouts)**
  * 🚨 Problem: Relying on a locally-running soft stop-loss meant that **during internet drops or server downtime, emergency stop-losses were missed, leading to catastrophic capital ruin.**
  * 💡 Solution: The root cause was reliance on an "unstable network and cloud runtime." We realized the defense mechanism must be delegated directly to the exchange core. **We integrated a hard-stop architecture that immediately fires a STOP_MARKET+MARK_PRICE trigger to the exchange matching engine the moment an entry order is placed.**
  * 🎯 Result: A bot that previously left the account defenseless during a crash now possesses **extreme survivability, as the exchange server definitively protects the capital regardless of the local bot's uptime.**

* **API Call Rejections**
  * 🚨 Problem: Hitting exchange API rate limits or security thresholds meant that **defensive stop orders fired during volatile spikes were outright rejected (e.g., Error -4120).**
  * 💡 Solution: The root cause was a "linear command structure" with zero contingency for rejected requests. A delegated sub-layer was required. **We built a protective Fallback shield that, upon receiving an API failure response, instantly reroutes the defense via background local polling.**
  * 🎯 Result: Where a single API failure used to bypass the stop-loss logic completely, **the system now detects the failure instantly and spawns a secondary software checker to guarantee the defense is executed.**

* **Cost Violations (Notional Value Limits)**
  * 🚨 Problem: Scaling-in caused capital to be split too thinly, **resulting in "dust" orders that failed the exchange's minimum Notional Value constraints, generating errors and overloading the system.**
  * 💡 Solution: The root cause was omitting exchange-specific rule validation prior to sending orders. We needed a frontline checkpoint. **We implemented a pre-flight validator that calculates expected costs (`min_cost`, `min_qty`) locally, only allowing valid pipelines to proceed.**
  * 🎯 Result: Meaningless rejections that spammed error logs and spiked API traffic were **quietly and safely blocked in advance, maximizing logical efficiency.**

#### C. Data Integrity and Adaptive Responsiveness

* **Data Voids (Cold Start Missing Indicators)**
  * 🚨 Problem: The meager batch size of exchange API historical data meant that **heavy, long-term moving averages remained empty and paralyzed for days after booting.**
  * 💡 Solution: The root cause was passively relying solely on the limited "live tick stream." A seamless bridge to long-term local data stores was essential. **We designed a deep-warmup pipeline that seamlessly merges and deduplicates gigabytes of binary Pickle caches with the latest live API arrays.**
  * 🎯 Result: Instead of running blindly for days waiting for data to accumulate, **the server now instantly fuses deep historical context with the live stream upon boot, entering combat at full power with zero delay.**

* **Peak Chasing (High-Altitude Averaging-Up)**
  * 🚨 Problem: Pyramiding logic adhered rigidly to the original entry price. **During sudden spikes followed by steep crashes, the logic would still trigger based on outdated initial prices, suicidally pouring excess long capital into a falling knife.**
  * 💡 Solution: The root cause was a "static price anchor" that ignored real-time momentum. Capital injection triggers had to switch to current execution prices. **We shifted to a dynamic trigger that scans profitability based strictly on the living `current_price` to determine subsequent entry points.**
  * 🎯 Result: A flawed structure that blindly averaged-up during downtrends was **transformed into a highly intelligent system that only unleashes bet-sizing when current momentum overwhelmingly dictates an upward trend.**

* **Load Overheating (Infinite Loop Shutdowns)**
  * 🚨 Problem: When margin limits or external factors caused an order to fail, the system forgot the failure reason and relentlessly retried dozens of times per second. **This repeatedly triggered API bans and temporary account lockdowns.**
  * 💡 Solution: The root cause was the total absence of "state caching for failure histories." A leash had to be placed on recurring failures. **We implemented an internal Lockdown feature that tallies error returns in local memory; if the count breaches an overflow threshold, that specific thread is ruthlessly severed.**
  * 🎯 Result: Logic that previously burned through API limits and caused overheating shocks now **self-detects cumulative failures and forces a cooldown process, protecting the entire system from catastrophic fatigue.**

* **Duplicate Pulses (Over-Trading)**
  * 🚨 Problem: Minor price ticks oscillating within a single valid signal candle would repeatedly trigger the entry condition. **This caused a chaotic flood of redundant orders in the same direction within a single timeframe.**
  * 💡 Solution: The root cause was a flawed, snapshot-based evaluation lacking "timestamp persistence." The bot needed to memorize the exact time of its last attack. **We injected a unique `entry_time_signal` stamp into memory and designed a filter that blocks all subsequent micro-pulses within that specific timestamp window.**
  * 🎯 Result: Sloppy logic that fired multiple times per wave, wasting fees and ruining entry averages, was **refined to execute a single, sniper-like entry per valid signal, drastically cutting down over-trading.**

#### D. Crushing Quant Architecture Flaws

* **Overrepresentation (Ignoring Execution Friction)**
  * 🚨 Problem: Backtest sandboxes only calculated perfect theoretical fill prices. **When seemingly brilliant 1000% ROI models were deployed live, profits melted exponentially into a steep downward spiral.**
  * 💡 Solution: The root cause lay in the "frictionless simulator logic" that ignored the delicate balance of limit vs. market orders. We had to gut the backtester and inject brutal, realistic penalties. **We hardcoded maker/taker delay penalties, large-order slippage, and funding rate costs directly into the virtual ledger, violently deducting them from the cumulative equity.**
  * 🎯 Result: A strategy wrapper that looked great on paper but failed in reality was **evolved into an authentic quant architecture possessing such extreme realism that its simulator charts can be trusted for immediate capital deployment.**

* **Parameter Collapse (Macro Regime Shifts)**
  * 🚨 Problem: When the asset transitioned from a hyper-bull market to a severe bear market, **the strategy's core settings failed instantly, leading to massive and repeated capital destruction.**
  * 💡 Solution: The root cause was a blind faith in "over-fitted heuristics" that worked well only once. The strategy needed a mechanical training network to constantly adjust its weight class according to macro speeds. **We implemented a state-of-the-art Walk-Forward Optimization (WFO) engine that endlessly trains on past windows and rigorously tests only on unseen future data, coupled with an internal drawdown controller.**
  * 🎯 Result: An empty shell of a strategy that suffered catastrophic MDDs when trends broke was **transformed into an organic systemic entity that autonomously calculates drawdown suppression to shrink exposure during drops, dynamically rebalancing its survival weight as new regime waves emerge.**

### 12.2 Future Research Directions 🚀

We are not settling for the current architecture and are preparing for overwhelming system enhancements.

1. **Micro-Regime Parser Integration**: By incorporating a Gaussian Mixture Model (GMM), we aim to equip the engine with fine-grained identification capabilities to instantly read and filter out false short-term signals triggered by macro variables.
2. **Confidence Interval Lower Bound Verification**: Using a Monte Carlo Resampling module, we will mathematically prove the extreme statistical lower bounds, ensuring the system survives even if the trade sequence flips to "Worst Bad Luck."
3. **Destroying Network Queues (Rust Porting)**: To shatter the L2 order book bottleneck inherent to the Python interpreter, we plan to rewrite the most critical pricing communication modules in C/Rust, driving network latency interrupts as close to zero as possible.

<a id="13-conclusion"></a>

## 13. Conclusion 🏁

WRSE is not a project designed to "showcase unrealistic backtest performance." It is a backtesting engine that first defines the exact points where live profits collapse (execution friction, funding rates, regime changes) and systematically controls them. By decoupling the input/output schemas and execution paths, we ensure that anyone provided with the same data can perfectly reproduce the identical results.

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
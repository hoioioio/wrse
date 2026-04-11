## HyroTrader (25k, Swing DD) - WRSE Prop Profile

Decisions (WRSE fit):
- Program: Two-step (Daily DD 5%, Max loss 10%)
- Daily DD type: Swing (Fixed)
- Platform: Bybit
- Universe: BTC_USDT, ETH_USDT only

Why:
- Two-step provides more total loss headroom than One-step (10% vs 6%), which matters more than speed for an automated system.
- BTC/ETH reduce slippage/liq shock risk and simplify “per-asset position” rule compliance.
- Swing DD removes intraday peak-tightening and is materially more compatible with systematic strategies.

### Run

From repository root:

```bash
python prop/hyrotrader_25k_swing_bybit/run_wfo_prop.py --config prop/hyrotrader_25k_swing_bybit/strategy_params.hyrotrader_25k_swing.toml --out ./outputs_hyro_25k
```

Outputs:
- `equity_ab.csv`, `equity_ab_taker.csv` (includes `capital` and `equity`)
- `trades_ab.csv`, `trades_ab_taker.csv` (includes `trade_value`, `pnl_pct`, `risk_to_sl`)
- `hyro_rules_report.json` (rule checks summary)

### What is checked (rule-oriented)

- Minimum 10 distinct trading days (based on exit timestamp date):
  - trade_value >= 5% of initial capital
  - abs(pnl_pct) >= 1%
- Profit distribution rule (Phase 1/2): no day contributes more than 40% of total positive profit (excess is effectively not counted)
- Max risk per position proxy: `risk_to_sl` <= 3% of initial capital
- Swing daily drawdown: per UTC day, `min_equity` must stay above `start_equity - initial_capital * daily_dd_pct`
- Max loss: `min_equity` must stay above `initial_capital * (1 - max_loss_pct)`

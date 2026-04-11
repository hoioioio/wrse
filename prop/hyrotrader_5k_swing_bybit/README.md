## HyroTrader (5k, Swing DD) - WRSE Prop Profile

Decisions:
- Program: Two-step (Phase 1: 10% / Phase 2: 5%)
- Daily DD type: Swing (Fixed)
- Platform: Bybit
- Universe: BTC_USDT, ETH_USDT only

Key numbers (5,000 USDT initial):
- Profit target: Phase 1 +500, Phase 2 +250
- Daily DD (5%): 250
- Max loss (10%): 500
- Valid trading day minimum trade value (5%): 250

### Run

From repository root:

```bash
python prop/hyrotrader_5k_swing_bybit/run_wfo_prop.py --config prop/hyrotrader_5k_swing_bybit/strategy_params.hyrotrader_5k_swing.toml --out ./outputs_hyro_5k
```

### Outputs

- `hyro_rules_report.json` (rule checks summary)
- `equity_ab.csv`, `equity_ab_taker.csv`
- `trades_ab.csv`, `trades_ab_taker.csv`

## HyroTrader Live (5k, Swing DD) - Bybit Runner

Default is DRY_RUN (no orders). Enable orders only with `LIVE_MODE=1`.

### Required environment variables

- `BYBIT_API_KEY`
- `BYBIT_API_SECRET`

### Run (dry-run)

```bash
python -m live.hyrotrader_5k_swing_bybit.bot --config live/hyrotrader_5k_swing_bybit/live_config.toml
```

### Run (live)

```bash
set LIVE_MODE=1
python -m live.hyrotrader_5k_swing_bybit.bot --config live/hyrotrader_5k_swing_bybit/live_config.toml
```

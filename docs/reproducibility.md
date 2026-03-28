# Reproducibility & Data Schema

## Quick Re-run (local)

```bash
pip install -r requirements.txt
python cli.py wfo --config config/strategy_params.example.toml --write_csv ./outputs_tmp
python report.py --config config/strategy_params.example.toml --public
```

`config/strategy_params.example.toml` expects the example cache locations below to exist:
- `c:/backtest_cache`
- `c:/alpha_cache`

Note:
- Raw market data is not included in this repository (size/licensing constraints). WRSE is designed to read cached OHLCV/funding/L2 summaries via the schema below.
- `report.py --public` exports normalized equity (`docs/assets_public/*.json`) used by the GitHub Pages dashboard.

## Data Inputs

WRSE loads a per-symbol OHLCV backtest cache and optionally joins funding and L2 summary features.

### 1) OHLCV backtest cache (required)

Path pattern:
- `{backtest_cache_dir}/bt_{SYMBOL}_{timeframe}.pkl`

Example:
- `c:/backtest_cache/bt_BTC_USDT_15m.pkl`

Expected format:
- Pickled pandas DataFrame
- Index: `datetime` or a `datetime` column (converted to index)
- Must contain at least: `open`, `high`, `low`, `close`, `volume`

Notes:
- The loader resamples to 4h bars internally.
- Timestamps are expected to be timezone-naive (or will be converted to timezone-naive).

### 2) Funding rate cache (optional)

Path pattern:
- `{regime_cache_dir}/funding_{SYMBOL}.pkl`

Expected format:
- Pickled pandas DataFrame with columns:
  - `fundingTime` (timestamp)
  - `fundingRate` (float)

If missing, funding is assumed to be 0.

### 3) L2 summary cache (optional)

Path pattern:
- `{regime_cache_dir}/l2_{SYMBOL}_{timeframe}.csv`

Expected format:
- CSV with `ts` timestamp column
- Supported feature columns:
  - `spread_bps`
  - `micro_dev_bps` (or `microprice`, `bid_px`, `ask_px` to derive it)
  - `imb`

If missing, L2 features are set to 0/NaN and execution falls back to OHLC-based spread estimation.

## Outputs

When `--write_csv` is provided, `cli.py wfo` writes:
- `wfo_splits.csv`
- `yearly_ab.csv`
- `yearly_ab_taker.csv`
- `equity_ab.csv`
- `equity_ab_taker.csv`

`report.py` writes the figures and dashboard JSON into `docs/assets_public/`:
- `equity_ab.json`, `equity_ab_taker.json`
- `yearly_ab.json`, `yearly_ab_taker.json`
- `wfo_splits.json`

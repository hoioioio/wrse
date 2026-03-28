from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd


def calc_awma(series: pd.Series, length: int = 10, fast_end: int = 2, slow_end: int = 30) -> pd.Series:
    change = series.diff(length).abs()
    volatility = series.diff().abs().rolling(window=length).sum()
    er = (change / volatility).fillna(0)
    fast_sc = 2 / (fast_end + 1)
    slow_sc = 2 / (slow_end + 1)
    sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
    ama = np.full(len(series), np.nan, dtype=float)
    if length < len(series):
        ama[length - 1] = float(np.mean(series.iloc[:length]))
        for i in range(length, len(series)):
            c = float(sc.iloc[i]) if np.isfinite(float(sc.iloc[i])) else 0.0
            ama[i] = ama[i - 1] + c * (float(series.iloc[i]) - ama[i - 1])
    return pd.Series(ama, index=series.index)


def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def calc_adx(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / length, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(alpha=1 / length, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(alpha=1 / length, adjust=False).mean() / atr)
    dx = (100 * (plus_di - minus_di).abs() / (plus_di + minus_di)).replace([np.inf, -np.inf], np.nan)
    return dx.ewm(alpha=1 / length, adjust=False).mean()


def calc_zscore(series: pd.Series, window: int = 200) -> pd.Series:
    m = series.rolling(window).mean()
    s = series.rolling(window).std().replace(0, np.nan)
    return (series - m) / s


def _read_pickle(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    df = pd.read_pickle(path)
    if df is None or len(df) == 0:
        return None
    return df


def load_funding_rate(regime_dir: str | Path, symbol: str) -> pd.Series | None:
    p = Path(regime_dir) / f"funding_{symbol}.pkl"
    df = _read_pickle(p)
    if df is None:
        return None
    if "fundingTime" in df.columns:
        df = df.copy()
        df["fundingTime"] = pd.to_datetime(df["fundingTime"], utc=True, errors="coerce")
        df = df.dropna(subset=["fundingTime"]).set_index("fundingTime")
    if "fundingRate" not in df.columns:
        return None
    s = pd.to_numeric(df["fundingRate"], errors="coerce").dropna().sort_index()
    if isinstance(s.index, pd.DatetimeIndex) and s.index.tz is not None:
        s.index = s.index.tz_convert(None)
    return s


def load_l2(regime_dir: str | Path, symbol: str, tf: str) -> pd.DataFrame | None:
    p = Path(regime_dir) / f"l2_{symbol}_{str(tf).lower()}.csv"
    if not p.exists():
        return None
    l2 = pd.read_csv(p)
    if l2 is None or len(l2) == 0 or "ts" not in l2.columns:
        return None
    l2["ts"] = pd.to_datetime(l2["ts"], utc=True, errors="coerce")
    l2 = l2.dropna(subset=["ts"]).set_index("ts").sort_index()
    if l2.index.tz is not None:
        l2.index = l2.index.tz_convert(None)
    if "micro_dev_bps" not in l2.columns and {"microprice", "bid_px", "ask_px"}.issubset(set(l2.columns)):
        mid = (pd.to_numeric(l2["bid_px"], errors="coerce") + pd.to_numeric(l2["ask_px"], errors="coerce")) / 2.0
        mp = pd.to_numeric(l2["microprice"], errors="coerce")
        l2["micro_dev_bps"] = ((mp / mid) - 1.0) * 10000.0
    return l2


@dataclass(frozen=True)
class DataSpec:
    backtest_cache_dir: str
    regime_cache_dir: str
    timeframe: str


def prepare_symbol_frame(spec: DataSpec, symbol: str) -> pd.DataFrame | None:
    fpath = Path(spec.backtest_cache_dir) / f"bt_{symbol}_{spec.timeframe}.pkl"
    df_15m = _read_pickle(fpath)
    if df_15m is None:
        return None
    if "datetime" in df_15m.columns:
        df_15m = df_15m.set_index("datetime")
    df_15m = df_15m[~df_15m.index.duplicated(keep="first")].sort_index()
    df = (
        df_15m.resample("4h")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
        .dropna()
    )

    df["fast_awma"] = calc_awma(df["close"], 1, 2, 30)
    df["slow_awma"] = calc_awma(df["close"], 16, 2, 30)
    df["kama_8"] = calc_awma(df["close"], 8, 2, 30)
    df["kama_16"] = df["slow_awma"]
    df["kama_32"] = calc_awma(df["close"], 32, 2, 30)

    df["fast_sma"] = df["close"].rolling(5).mean()
    df["slow_sma"] = df["close"].rolling(10).mean()
    df["exit_line"] = df["close"].rolling(140).mean()
    df["rev_ma"] = df["close"].rolling(3).mean()

    df["rsi"] = calc_rsi(df["close"], 14)
    df["bb_mid"] = df["close"].rolling(20).mean()
    df["bb_std"] = df["close"].rolling(20).std()
    df["bb_z"] = (df["close"] - df["bb_mid"]) / df["bb_std"].replace(0, np.nan)
    df["adx"] = calc_adx(df["high"], df["low"], df["close"], 14)
    ret = df["close"].pct_change()
    df["ret_ac"] = ret.rolling(20).corr(ret.shift(1))
    rng = (df["high"] - df["low"]).replace(0, np.nan)
    upper_wick = df["high"] - np.maximum(df["open"], df["close"])
    lower_wick = np.minimum(df["open"], df["close"]) - df["low"]
    vol_spike = df["volume"] / df["volume"].rolling(20).mean().replace(0, np.nan)
    df["tai"] = ((lower_wick - upper_wick) / rng) * vol_spike

    tr1 = df["high"] - df["low"]
    tr2 = (df["high"] - df["close"].shift(1)).abs()
    tr3 = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["atr"] = tr.rolling(14).mean()
    df["atr_sma"] = df["atr"].rolling(20).mean()
    df["vol_ratio"] = np.where(df["atr_sma"] != 0, df["atr"] / df["atr_sma"], 0.0)

    tp = (df["high"] + df["low"] + df["close"]) / 3
    rmf = tp * df["volume"]
    pos_flow = pd.Series(np.where(tp > tp.shift(1), rmf, 0.0), index=df.index)
    neg_flow = pd.Series(np.where(tp < tp.shift(1), rmf, 0.0), index=df.index)
    pos_mf = pos_flow.rolling(14).sum()
    neg_mf = neg_flow.rolling(14).sum()
    mfi_ratio = pos_mf / neg_mf.replace(0, np.nan)
    df["mfi"] = 100 - (100 / (1 + mfi_ratio))

    df["roc"] = df["close"].pct_change(14) * 100
    df["momentum_score"] = df["roc"] * df["vol_ratio"]

    fr = load_funding_rate(spec.regime_cache_dir, symbol)
    if fr is not None:
        fr4 = fr.resample("4h").last().ffill()
        df = df.join(fr4.rename("funding_rate"), how="left")
        df["funding_rate"] = df["funding_rate"].ffill().fillna(0.0)
    else:
        df["funding_rate"] = 0.0
    df["funding_z"] = calc_zscore(df["funding_rate"], 200).fillna(0.0)

    l2 = load_l2(spec.regime_cache_dir, symbol, spec.timeframe)
    if l2 is not None:
        cols = [c for c in ["imb", "spread_bps", "micro_dev_bps"] if c in l2.columns]
        if cols:
            agg = l2[cols].resample("4h").mean()
            df["l2_imb"] = agg.get("imb", pd.Series(index=df.index, dtype=float)).reindex(df.index, method="ffill")
            df["l2_spread_bps"] = agg.get("spread_bps", pd.Series(index=df.index, dtype=float)).reindex(df.index, method="ffill")
            df["l2_micro_dev_bps"] = agg.get("micro_dev_bps", pd.Series(index=df.index, dtype=float)).reindex(df.index, method="ffill")
        else:
            df["l2_imb"] = np.nan
            df["l2_spread_bps"] = np.nan
            df["l2_micro_dev_bps"] = np.nan
    else:
        df["l2_imb"] = np.nan
        df["l2_spread_bps"] = np.nan
        df["l2_micro_dev_bps"] = np.nan

    df["l2_imb_z"] = calc_zscore(df["l2_imb"].astype(float), 200).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    df["l2_imb"] = df["l2_imb"].fillna(0.0)
    df["l2_spread_bps"] = df["l2_spread_bps"].fillna(0.0)
    df["l2_micro_dev_bps"] = df["l2_micro_dev_bps"].fillna(0.0)

    df = df.replace([np.inf, -np.inf], np.nan).dropna()
    return df


def load_universe(spec: DataSpec, symbols: list[str]) -> dict[str, pd.DataFrame]:
    out = {}
    for s in symbols:
        df = prepare_symbol_frame(spec, s)
        if df is not None and not df.empty:
            out[s] = df
    return out

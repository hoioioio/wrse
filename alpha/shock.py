from __future__ import annotations

import numpy as np
import pandas as pd


def label_jump_events(df: pd.DataFrame, horizon: int = 6, thr: float = 0.08) -> pd.Series:
    close = df["close"].astype(float)
    highs = []
    lows = []
    for k in range(1, int(horizon) + 1):
        highs.append((df["high"].shift(-k).astype(float) / close) - 1.0)
        lows.append((df["low"].shift(-k).astype(float) / close) - 1.0)
    fwd_up = pd.concat(highs, axis=1).max(axis=1)
    fwd_dn = pd.concat(lows, axis=1).min(axis=1)
    y = np.zeros(len(df), dtype=float)
    up_hit = fwd_up >= float(thr)
    dn_hit = fwd_dn <= -float(thr)
    both = up_hit & dn_hit
    y[up_hit.values] = 1.0
    y[dn_hit.values] = -1.0
    if both.any():
        up_abs = fwd_up[both].abs()
        dn_abs = fwd_dn[both].abs()
        y[both.values] = np.where(up_abs.values >= dn_abs.values, 1.0, -1.0)
    y[-int(horizon) :] = 0.0
    return pd.Series(y, index=df.index, name="jump_label")


def build_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    x = pd.DataFrame(index=df.index)
    x["funding_z"] = df.get("funding_z", 0.0).astype(float)
    x["funding_rate"] = df.get("funding_rate", 0.0).astype(float)
    x["vol_ratio"] = df["vol_ratio"].astype(float)
    x["adx"] = df["adx"].astype(float)
    x["ret_ac"] = df["ret_ac"].astype(float)
    x["tai"] = df["tai"].astype(float)
    x["bb_z"] = df["bb_z"].astype(float)
    x["mfi"] = df["mfi"].astype(float)
    x["roc"] = df["roc"].astype(float)
    x = x.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    return x


def fit_ridge_signed_classifier(x: pd.DataFrame, y: pd.Series, l2: float = 10.0) -> dict:
    x = x.astype(float)
    y = y.astype(float)
    cols = list(x.columns)
    xm = x.values
    ym = y.values.reshape(-1, 1)
    ones = np.ones((xm.shape[0], 1), dtype=float)
    xm1 = np.hstack([ones, xm])
    xtx = xm1.T @ xm1
    reg = np.eye(xtx.shape[0], dtype=float) * float(l2)
    reg[0, 0] = 0.0
    w = np.linalg.solve(xtx + reg, xm1.T @ ym).reshape(-1)
    return {"cols": cols, "w": w}


def predict_score(model: dict, x: pd.DataFrame) -> pd.Series:
    cols = model["cols"]
    w = model["w"]
    xm = x[cols].astype(float).values
    ones = np.ones((xm.shape[0], 1), dtype=float)
    xm1 = np.hstack([ones, xm])
    return pd.Series((xm1 @ w).astype(float), index=x.index, name="shock_score")


def build_train_matrix(
    df_dict: dict[str, pd.DataFrame],
    years: list[int],
    horizon: int = 6,
    thr: float = 0.08,
    neg_ratio: float = 2.0,
    min_pos: int = 50,
) -> tuple[pd.DataFrame | None, pd.Series | None, pd.Series | None, pd.Series | None]:
    xs = []
    ys = []
    for _, df in df_dict.items():
        for y in years:
            try:
                d = df.loc[str(y)].copy()
            except KeyError:
                continue
            if len(d) < (int(horizon) + 50):
                continue
            lab = label_jump_events(d, horizon=int(horizon), thr=float(thr))
            feat = build_feature_frame(d)
            pos = lab != 0
            neg = lab == 0
            pos_idx = lab.index[pos]
            neg_idx = lab.index[neg]
            if len(pos_idx) < int(min_pos):
                continue
            n_neg = int(min(len(neg_idx), max(int(len(pos_idx) * float(neg_ratio)), 200)))
            rng = np.random.default_rng(1000 + int(y))
            neg_samp = rng.choice(neg_idx.values, size=n_neg, replace=False)
            take_idx = pd.Index(np.concatenate([pos_idx.values, neg_samp]))
            xs.append(feat.loc[take_idx])
            ys.append(lab.loc[take_idx])
    if not xs:
        return None, None, None, None
    x = pd.concat(xs).sort_index()
    y = pd.concat(ys).sort_index()
    mu = x.mean()
    sig = x.std().replace(0, 1.0)
    xz = (x - mu) / sig
    return xz, y, mu, sig

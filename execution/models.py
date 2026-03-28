from __future__ import annotations

import numpy as np


def apply_slip(price: float, side: str, slip_bps: float) -> float:
    slip = float(slip_bps) / 10000.0
    if side == "buy":
        return float(price) * (1.0 + slip)
    return float(price) * (1.0 - slip)


def fee_cost(notional: float, fee_rate: float) -> float:
    return abs(float(notional)) * float(fee_rate)


def funding_pnl_per_bar(side: str, funding_rate: float, notional: float, bar_hours: float = 4.0, funding_hours: float = 8.0) -> float:
    fr = float(funding_rate)
    mult = -1.0 if side == "buy" else 1.0
    return mult * fr * float(notional) * (float(bar_hours) / float(funding_hours))


def est_spread_bps(row: dict) -> float:
    v = row.get("l2_spread_bps", np.nan)
    try:
        v = float(v)
    except Exception:
        v = float("nan")
    if np.isfinite(v) and v > 0:
        return v
    c = float(row.get("close", 0.0))
    h = float(row.get("high", c))
    l = float(row.get("low", c))
    if c <= 0:
        return 2.0
    rng_bps = ((h - l) / c) * 10000.0
    return float(np.clip(rng_bps * 0.08, 1.0, 15.0))


def exec_price(
    side: str,
    open_px: float,
    bar_high: float,
    bar_low: float,
    row: dict,
    slip_bps: float,
    exec_mode: str,
    maker_fee_rate: float,
    taker_fee_rate: float,
    maker_base_offset_bps: float = 0.2,
    maker_spread_mult: float = 0.6,
    maker_micro_mult: float = 0.35,
    maker_imb_mult: float = 2.0,
    shock_aggr_th: float = 0.12,
) -> tuple[float, float, bool]:
    s = float(row.get("shock_score", 0.0))
    if abs(s) >= float(shock_aggr_th):
        px = apply_slip(open_px, side, slip_bps)
        return float(px), float(taker_fee_rate), True
    if str(exec_mode).lower() == "taker":
        px = apply_slip(open_px, side, slip_bps)
        return float(px), float(taker_fee_rate), True

    spread_bps = est_spread_bps(row)
    micro_dev = row.get("l2_micro_dev_bps", 0.0)
    try:
        micro_dev = float(micro_dev)
    except Exception:
        micro_dev = 0.0
    imb = row.get("l2_imb", 0.0)
    try:
        imb = float(imb)
    except Exception:
        imb = 0.0

    side_sign = 1.0 if side == "buy" else -1.0
    offset_bps = float(maker_base_offset_bps) + float(maker_spread_mult) * float(spread_bps)
    offset_bps = offset_bps - float(maker_micro_mult) * (side_sign * float(micro_dev))
    offset_bps = offset_bps - float(maker_imb_mult) * (side_sign * float(imb))
    offset_bps = float(np.clip(offset_bps, 0.0, max(2.0, float(spread_bps) * 2.5)))

    limit_px = float(open_px) * (1.0 - side_sign * (offset_bps / 10000.0))
    touched = (float(bar_low) <= limit_px) if side == "buy" else (float(bar_high) >= limit_px)
    if touched:
        return float(limit_px), float(maker_fee_rate), True
    if str(exec_mode).lower() == "maker_then_taker":
        px = apply_slip(open_px, side, slip_bps)
        return float(px), float(taker_fee_rate), True
    return float("nan"), 0.0, False

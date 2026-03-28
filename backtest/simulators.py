from __future__ import annotations

import numpy as np
import pandas as pd

from wrse.execution.models import exec_price, fee_cost, funding_pnl_per_bar, apply_slip


def simulate_v2xa(
    df_dict: dict[str, pd.DataFrame],
    year: int,
    fund_params: dict,
    avoid_th: float,
    exit_on_flip: bool,
    taker_fee_rate: float,
    maker_fee_rate: float,
    slip_bps: float,
    sl_pct: float,
    size_k: float,
    min_mult: float,
    max_mult: float,
    exec_mode: str,
    portfolio_slots: int = 5,
    risk_per_trade: float = 0.0125,
    base_size_mult: float = 0.3,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    capital = 100000.0
    positions: dict[str, dict] = {}
    trades = []
    equity = []
    all_times = pd.DatetimeIndex([])
    for _, df in df_dict.items():
        try:
            d = df.loc[str(year)].copy()
        except KeyError:
            continue
        all_times = all_times.union(d.index)
    all_times = all_times.sort_values().unique()

    for t_idx in range(2, len(all_times) - 1):
        t = all_times[t_idx]
        t_next = all_times[t_idx + 1]
        closed = []
        for sym in list(positions.keys()):
            pos = positions[sym]
            df = df_dict[sym]
            if t not in df.index:
                continue
            row = df.loc[t]
            nxt_row = df.loc[t_next] if t_next in df.index else row
            nxt_open = float(nxt_row["open"])
            nxt_high = float(nxt_row.get("high", nxt_open))
            nxt_low = float(nxt_row.get("low", nxt_open))

            notional = float(row["close"]) * float(pos["qty"])
            capital += funding_pnl_per_bar(pos["side"], float(row.get("funding_rate", 0.0)), notional)

            pos["bars"] += 1
            sl_hit = False
            if pos["side"] == "buy" and float(row["low"]) <= float(pos["sl"]):
                sl_hit = True
            if pos["side"] == "sell" and float(row["high"]) >= float(pos["sl"]):
                sl_hit = True

            reason = None
            px = nxt_open
            if sl_hit:
                reason = "SL"
                px = float(pos["sl"])
            else:
                if pos["side"] == "buy":
                    if float(row["mfi"]) > 90 and float(row["close"]) < float(row["rev_ma"]):
                        reason = "Rev"
                    elif float(row["close"]) < float(row["exit_line"]):
                        reason = "TrendEnd"
                else:
                    if float(row["mfi"]) < 12 and float(row["close"]) > float(row["rev_ma"]):
                        reason = "Rev"
                    elif float(row["close"]) > float(row["exit_line"]):
                        reason = "TrendEnd"
                if reason is None and bool(exit_on_flip):
                    s = float(row.get("shock_score", 0.0))
                    if pos["side"] == "buy" and s < -float(avoid_th):
                        reason = "ShockFlip"
                    if pos["side"] == "sell" and s > float(avoid_th):
                        reason = "ShockFlip"

            if reason is not None:
                exit_side = "sell" if pos["side"] == "buy" else "buy"
                if reason == "SL":
                    px = apply_slip(px, exit_side, slip_bps)
                    fee_r = float(taker_fee_rate)
                else:
                    px, fee_r, ok = exec_price(exit_side, px, nxt_high, nxt_low, row.to_dict(), slip_bps, exec_mode, maker_fee_rate, taker_fee_rate)
                    if not ok:
                        px = apply_slip(px, exit_side, slip_bps)
                        fee_r = float(taker_fee_rate)
                pnl = (float(px) - float(pos["entry"])) * float(pos["qty"]) if pos["side"] == "buy" else (float(pos["entry"]) - float(px)) * float(pos["qty"])
                capital += pnl
                capital -= fee_cost(float(px) * float(pos["qty"]), float(fee_r))
                trades.append({"time": t, "symbol": sym, "side": pos["side"], "pnl": pnl, "reason": reason})
                closed.append(sym)
            else:
                if int(pos.get("stage", 1)) == 1:
                    ret = (float(row["close"]) - float(pos["entry"])) / float(pos["entry"]) if pos["side"] == "buy" else (float(pos["entry"]) - float(row["close"])) / float(pos["entry"])
                    if ret >= float(fund_params.get("pyr_trig", 0.01)):
                        add_qty = float(pos["qty"])
                        fill_px, fee_r, ok = exec_price(pos["side"], nxt_open, nxt_high, nxt_low, row.to_dict(), slip_bps, exec_mode, maker_fee_rate, taker_fee_rate)
                        if not ok:
                            fill_px = apply_slip(nxt_open, pos["side"], slip_bps)
                            fee_r = float(taker_fee_rate)
                        capital -= fee_cost(float(fill_px) * add_qty, float(fee_r))
                        new_qty = float(pos["qty"]) + add_qty
                        new_entry = (float(pos["entry"]) * float(pos["qty"]) + float(fill_px) * add_qty) / new_qty
                        pos["qty"] = new_qty
                        pos["entry"] = new_entry
                        pos["stage"] = 2

        for sym in closed:
            del positions[sym]

        slots = int(portfolio_slots) - len(positions)
        if slots > 0:
            cands = []
            for sym, df in df_dict.items():
                if sym in positions:
                    continue
                if t not in df.index or t_next not in df.index:
                    continue
                prev_t = all_times[t_idx - 1]
                if prev_t not in df.index:
                    continue
                row = df.loc[t]
                prev = df.loc[prev_t]
                if float(row["vol_ratio"]) < 0.8:
                    continue
                if abs(float(row.get("funding_rate", 0.0))) > float(fund_params.get("fund_abs_max", 0.00025)):
                    continue
                if abs(float(row.get("funding_z", 0.0))) > float(fund_params.get("fund_z_max", 1.0)):
                    continue
                gold = (float(prev["fast_sma"]) < float(prev["slow_sma"])) and (float(row["fast_sma"]) > float(row["slow_sma"]))
                dead = (float(prev["fast_sma"]) > float(prev["slow_sma"])) and (float(row["fast_sma"]) < float(row["slow_sma"]))
                signal = None
                if gold and float(row["close"]) > float(row["exit_line"]):
                    signal = "buy"
                if dead and float(row["close"]) < float(row["exit_line"]):
                    signal = "sell"
                if signal is None:
                    continue
                s = float(row.get("shock_score", 0.0))
                if signal == "buy" and s < -float(avoid_th):
                    continue
                if signal == "sell" and s > float(avoid_th):
                    continue
                nxt_row = df.loc[t_next]
                px = float(nxt_row["open"])
                px_h = float(nxt_row.get("high", px))
                px_l = float(nxt_row.get("low", px))
                score = abs(float(row["momentum_score"]))
                cands.append((score, sym, signal, px, px_h, px_l, s, row))

            cands.sort(reverse=True, key=lambda x: x[0])
            for _, sym, side, px, px_h, px_l, s, row in cands[:slots]:
                risk = capital * float(risk_per_trade)
                base_usd = (risk / float(sl_pct)) * float(base_size_mult)
                mult = 1.0
                if float(size_k) > 0:
                    align = 1.0 if (side == "buy" and s > 0) or (side == "sell" and s < 0) else -1.0
                    mult = 1.0 + align * float(size_k) * min(2.0, abs(float(s)))
                    mult = float(np.clip(mult, float(min_mult), float(max_mult)))
                pos_usd = base_usd * mult
                fill_px, fee_r, ok = exec_price(side, px, px_h, px_l, row.to_dict(), slip_bps, exec_mode, maker_fee_rate, taker_fee_rate)
                if not ok:
                    continue
                qty = float(pos_usd) / float(fill_px)
                sl = float(fill_px) * (1 - float(sl_pct)) if side == "buy" else float(fill_px) * (1 + float(sl_pct))
                capital -= fee_cost(float(fill_px) * qty, float(fee_r))
                positions[sym] = {"side": side, "entry": float(fill_px), "qty": qty, "sl": sl, "stage": 1, "bars": 0}

        if t.hour == 0 and t.minute == 0:
            equity.append({"time": t, "capital": capital})

    return pd.DataFrame(trades), pd.DataFrame(equity)


def simulate_shockscore(
    df_dict: dict[str, pd.DataFrame],
    year: int,
    entry_th: float,
    max_hold: int,
    sl_pct: float,
    taker_fee_rate: float,
    maker_fee_rate: float,
    slip_bps: float,
    size_pow: float,
    max_mult: float,
    exec_mode: str,
    portfolio_slots: int = 5,
    risk_per_trade: float = 0.0125,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    capital = 100000.0
    positions: dict[str, dict] = {}
    trades = []
    equity = []
    all_times = pd.DatetimeIndex([])
    for _, df in df_dict.items():
        try:
            d = df.loc[str(year)].copy()
        except KeyError:
            continue
        all_times = all_times.union(d.index)
    all_times = all_times.sort_values().unique()

    for t_idx in range(1, len(all_times) - 1):
        t = all_times[t_idx]
        t_next = all_times[t_idx + 1]
        closed = []
        for sym in list(positions.keys()):
            pos = positions[sym]
            df = df_dict[sym]
            if t not in df.index:
                continue
            row = df.loc[t]
            nxt_row = df.loc[t_next] if t_next in df.index else row
            nxt_open = float(nxt_row["open"])
            nxt_high = float(nxt_row.get("high", nxt_open))
            nxt_low = float(nxt_row.get("low", nxt_open))

            notional = float(row["close"]) * float(pos["qty"])
            capital += funding_pnl_per_bar(pos["side"], float(row.get("funding_rate", 0.0)), notional)
            pos["bars"] += 1

            sl_hit = False
            if pos["side"] == "buy" and float(row["low"]) <= float(pos["sl"]):
                sl_hit = True
            if pos["side"] == "sell" and float(row["high"]) >= float(pos["sl"]):
                sl_hit = True

            reason = None
            px = nxt_open
            if sl_hit:
                reason = "SL"
                px = float(pos["sl"])
            else:
                s = float(row.get("shock_score", 0.0))
                if int(pos["bars"]) >= int(max_hold):
                    reason = "T"
                elif pos["side"] == "buy" and s < 0:
                    reason = "Flip"
                elif pos["side"] == "sell" and s > 0:
                    reason = "Flip"

            if reason is not None:
                exit_side = "sell" if pos["side"] == "buy" else "buy"
                if reason == "SL":
                    px = apply_slip(px, exit_side, slip_bps)
                    fee_r = float(taker_fee_rate)
                else:
                    px, fee_r, ok = exec_price(exit_side, px, nxt_high, nxt_low, row.to_dict(), slip_bps, exec_mode, maker_fee_rate, taker_fee_rate)
                    if not ok:
                        px = apply_slip(px, exit_side, slip_bps)
                        fee_r = float(taker_fee_rate)
                pnl = (float(px) - float(pos["entry"])) * float(pos["qty"]) if pos["side"] == "buy" else (float(pos["entry"]) - float(px)) * float(pos["qty"])
                capital += pnl
                capital -= fee_cost(float(px) * float(pos["qty"]), float(fee_r))
                trades.append({"time": t, "symbol": sym, "side": pos["side"], "pnl": pnl, "reason": reason})
                closed.append(sym)

        for sym in closed:
            del positions[sym]

        slots = int(portfolio_slots) - len(positions)
        if slots > 0:
            cands = []
            for sym, df in df_dict.items():
                if sym in positions:
                    continue
                if t not in df.index or t_next not in df.index:
                    continue
                row = df.loc[t]
                s = float(row.get("shock_score", 0.0))
                if abs(s) < float(entry_th):
                    continue
                nxt_row = df.loc[t_next]
                px = float(nxt_row["open"])
                px_h = float(nxt_row.get("high", px))
                px_l = float(nxt_row.get("low", px))
                side = "buy" if s > 0 else "sell"
                cands.append((abs(s), sym, side, px, px_h, px_l, s, row))

            cands.sort(reverse=True, key=lambda x: x[0])
            for _, sym, side, px, px_h, px_l, s, row in cands[:slots]:
                risk = capital * float(risk_per_trade)
                base_usd = risk / float(sl_pct)
                mult = min(float(max_mult), max(0.2, abs(float(s)) ** float(size_pow)))
                pos_usd = base_usd * mult
                fill_px, fee_r, ok = exec_price(side, px, px_h, px_l, row.to_dict(), slip_bps, exec_mode, maker_fee_rate, taker_fee_rate)
                if not ok:
                    continue
                qty = float(pos_usd) / float(fill_px)
                sl = float(fill_px) * (1 - float(sl_pct)) if side == "buy" else float(fill_px) * (1 + float(sl_pct))
                capital -= fee_cost(float(fill_px) * qty, float(fee_r))
                positions[sym] = {"side": side, "entry": float(fill_px), "qty": qty, "sl": sl, "bars": 0}

        if t.hour == 0 and t.minute == 0:
            equity.append({"time": t, "capital": capital})

    return pd.DataFrame(trades), pd.DataFrame(equity)

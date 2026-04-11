import argparse
import json
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backtest.metrics import calc_equity_metrics_ext
from backtest.walkforward import run_wfo_fast
from prop.hyrotrader_25k_swing_bybit.validate_hyro_rules import validate
from utils.config import Config


def _trade_stats(path: Path) -> dict:
    if not path.exists():
        return {}
    tr = pd.read_csv(path)
    if tr is None or len(tr) == 0:
        return {"trades": 0}
    for c in ["pnl_net", "pnl", "pnl_pct", "trade_value"]:
        if c in tr.columns:
            tr[c] = pd.to_numeric(tr[c], errors="coerce")
    win = float((tr["pnl_net"] > 0).mean()) if "pnl_net" in tr.columns else float("nan")
    gross_pos = float(tr.loc[tr["pnl_net"] > 0, "pnl_net"].sum()) if "pnl_net" in tr.columns else float("nan")
    gross_neg = float(tr.loc[tr["pnl_net"] < 0, "pnl_net"].sum()) if "pnl_net" in tr.columns else float("nan")
    pf = float(gross_pos / abs(gross_neg)) if gross_neg < 0 else float("inf")
    return {"trades": int(len(tr)), "win_rate": float(win), "profit_factor": float(pf), "pnl_net_sum": float(tr["pnl_net"].sum()) if "pnl_net" in tr.columns else float("nan")}


def _write_df(p: Path, df: pd.DataFrame) -> None:
    if df is None or df.empty:
        return
    df.to_csv(p, index=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_root", required=True, type=str)
    args = ap.parse_args()

    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    candidates = [
        ("v1_exec_aware", "prop/hyrotrader_25k_swing_bybit/candidates/strategy_params.hyro_25k_swing_v1_exec_aware.toml"),
        ("v2_wider_sl", "prop/hyrotrader_25k_swing_bybit/candidates/strategy_params.hyro_25k_swing_v2_wider_sl.toml"),
        ("v3_trend_only", "prop/hyrotrader_25k_swing_bybit/candidates/strategy_params.hyro_25k_swing_v3_trend_only.toml"),
    ]

    rows = []
    for name, cfg_path in candidates:
        print(name)
        cfg = Config.load(cfg_path).raw
        res = run_wfo_fast(cfg)

        out_dir = out_root / name
        out_dir.mkdir(parents=True, exist_ok=True)

        _write_df(out_dir / "equity_ab.csv", res.get("equity_AB"))
        _write_df(out_dir / "equity_ab_taker.csv", res.get("equity_AB_taker"))
        _write_df(out_dir / "trades_ab.csv", res.get("trades_AB"))
        _write_df(out_dir / "trades_ab_taker.csv", res.get("trades_AB_taker"))
        _write_df(out_dir / "yearly_ab.csv", res.get("year_AB"))
        _write_df(out_dir / "yearly_ab_taker.csv", res.get("year_AB_taker"))

        rep = validate(cfg_path=cfg_path, out_dir=str(out_dir))
        (out_dir / "hyro_rules_report.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")

        eq_ab = res.get("equity_AB")
        eq_t = res.get("equity_AB_taker")
        m_ab = calc_equity_metrics_ext(eq_ab, periods_per_year=2190) if eq_ab is not None else {}
        m_t = calc_equity_metrics_ext(eq_t, periods_per_year=2190) if eq_t is not None else {}
        ts_ab = _trade_stats(out_dir / "trades_ab.csv")
        ts_t = _trade_stats(out_dir / "trades_ab_taker.csv")

        rows.append(
            {
                "name": name,
                "total_return_pct": float(m_ab.get("Total Return", float("nan"))) * 100.0,
                "cagr_pct": float(m_ab.get("CAGR", float("nan"))) * 100.0,
                "mdd_pct": float(m_ab.get("MDD", float("nan"))) * 100.0,
                "sharpe": float(m_ab.get("Sharpe Ratio", float("nan"))),
                "trades": int(ts_ab.get("trades", 0)),
                "trade_win_rate_pct": float(ts_ab.get("win_rate", float("nan"))) * 100.0,
                "profit_factor": float(ts_ab.get("profit_factor", float("nan"))),
                "taker_total_return_pct": float(m_t.get("Total Return", float("nan"))) * 100.0,
                "taker_mdd_pct": float(m_t.get("MDD", float("nan"))) * 100.0,
                "taker_sharpe": float(m_t.get("Sharpe Ratio", float("nan"))),
                "taker_trade_win_rate_pct": float(ts_t.get("win_rate", float("nan"))) * 100.0,
                "valid_days": int(rep.get("valid_trading_days_count", 0)),
                "profit_distribution_ok": bool(rep.get("profit_distribution", {}).get("ok", False)),
                "risk_violations": int(rep.get("max_risk_per_position", {}).get("violations", 0)),
                "swing_dd_ok": bool(rep.get("swing_daily_dd", {}).get("ok", False)),
                "max_loss_ok": bool(rep.get("max_loss", {}).get("ok", False)),
            }
        )

    summary = pd.DataFrame(rows)
    summary.to_csv(out_root / "summary.csv", index=False)
    print(out_root / "summary.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

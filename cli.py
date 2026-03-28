import argparse
import sys
from pathlib import Path

import numpy as np

_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from wrse.utils.config import Config
from wrse.backtest.walkforward import run_wfo_fast


def _fmt_pct(x):
    if x is None or not np.isfinite(float(x)):
        return "nan"
    return f"{float(x)*100:.2f}%"


def _fmt_f(x):
    if x is None or not np.isfinite(float(x)):
        return "nan"
    return f"{float(x):.2f}"


def cmd_wfo(args) -> int:
    cfg = Config.load(args.config).raw
    res = run_wfo_fast(cfg)

    print("WFO_FAST")
    splits = res.get("splits")
    if splits is not None and not splits.empty:
        print("SPLITS")
        print(splits.to_string(index=False))

    for k in ["oos_AB", "oos_AB_taker"]:
        m = res.get(k, {})
        if not m:
            continue
        print(
            k,
            {
                "Total Return": _fmt_pct(m.get("Total Return")),
                "Annual Return": _fmt_pct(m.get("Annual Return")),
                "MDD": _fmt_pct(m.get("MDD")),
                "Sharpe": _fmt_f(m.get("Sharpe Ratio")),
                "Days": int(m.get("Days", 0)),
            },
        )

    if args.write_csv:
        out_dir = Path(args.write_csv)
        out_dir.mkdir(parents=True, exist_ok=True)
        if splits is not None and not splits.empty:
            splits.to_csv(out_dir / "wfo_splits.csv", index=False)
        e1 = res.get("equity_AB")
        if e1 is not None and not e1.empty:
            e1.to_csv(out_dir / "equity_ab.csv", index=False)
        e2 = res.get("equity_AB_taker")
        if e2 is not None and not e2.empty:
            e2.to_csv(out_dir / "equity_ab_taker.csv", index=False)
        y1 = res.get("year_AB")
        if y1 is not None and not y1.empty:
            y1.to_csv(out_dir / "yearly_ab.csv", index=False)
        y2 = res.get("year_AB_taker")
        if y2 is not None and not y2.empty:
            y2.to_csv(out_dir / "yearly_ab_taker.csv", index=False)

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="wrse")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_wfo = sub.add_parser("wfo", help="Run fast walk-forward evaluation")
    ap_wfo.add_argument("--config", type=str, required=True)
    ap_wfo.add_argument("--write_csv", type=str, default="")
    ap_wfo.set_defaults(func=cmd_wfo)

    args = ap.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

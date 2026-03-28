import json
import math
from pathlib import Path

import numpy as np


def _load_json(p: Path):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _equity_stats(equity_rows):
    vals = np.asarray([float(x["capital"]) for x in equity_rows], dtype=float)
    if len(vals) < 2:
        return {"days": int(len(vals))}
    rets = vals[1:] / vals[:-1] - 1.0
    total = float(vals[-1] / vals[0] - 1.0)
    cummax = np.maximum.accumulate(vals)
    mdd = float(((vals - cummax) / cummax).min())
    std = float(rets.std(ddof=1)) if len(rets) > 1 else 0.0
    sharpe = float(math.sqrt(365.0) * float(rets.mean()) / std) if std > 0 else 0.0
    return {"days": int(len(vals)), "total": total, "mdd": mdd, "sharpe": sharpe}


def main() -> int:
    base = Path(r"c:\wrse\docs\assets_public")
    eq_ab = _load_json(base / "equity_ab.json")
    eq_t = _load_json(base / "equity_ab_taker.json")

    for name, eq in [("AB", eq_ab), ("TAKER", eq_t)]:
        s = _equity_stats(eq)
        t0 = eq[0]["time"] if eq else None
        t1 = eq[-1]["time"] if eq else None
        print(name, "range", t0, "→", t1, "days", s.get("days"))
        print(name, "total", f"{s.get('total', 0.0)*100:.2f}%", "mdd", f"{s.get('mdd', 0.0)*100:.2f}%", "sharpe", f"{s.get('sharpe', 0.0):.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

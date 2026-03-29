import json
import math
import re
from pathlib import Path

import numpy as np


def _load_json(p: Path):
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _equity_stats(equity_rows):
    vals = np.asarray([float(x["capital"]) for x in equity_rows], dtype=float)
    rets = vals[1:] / vals[:-1] - 1.0
    total = float(vals[-1] / vals[0] - 1.0)
    yrs = float(len(vals)) / 365.0
    cagr = float((vals[-1] / vals[0]) ** (1.0 / yrs) - 1.0)
    cum = np.maximum.accumulate(vals)
    mdd = float(((vals - cum) / cum).min())
    sharpe = float(math.sqrt(365.0) * float(rets.mean()) / float(rets.std(ddof=1)))
    return total, cagr, mdd, sharpe


def main() -> int:
    base = Path(__file__).resolve().parent
    idx = (base / "docs" / "index.html").read_text(encoding="utf-8")

    pat = re.compile(
        r"\{ train: \[[^\]]*\], test: (\d+), AB_return_pct: ([\d\.\-]+), AB_mdd_pct: ([\d\.\-]+), AB_sharpe: ([\d\.\-]+), AB_taker_sharpe: ([\d\.\-]+), best_w: ([\d\.\-]+) \}"
    )
    hardcoded = []
    for mm in pat.finditer(idx):
        hardcoded.append(
            {
                "test": int(mm.group(1)),
                "AB_return_pct": float(mm.group(2)),
                "AB_mdd_pct": float(mm.group(3)),
                "AB_sharpe": float(mm.group(4)),
                "AB_taker_sharpe": float(mm.group(5)),
                "best_w": float(mm.group(6)),
            }
        )

    wfo = _load_json(base / "docs" / "assets_public" / "wfo_splits.json")
    y_ab = _load_json(base / "docs" / "assets_public" / "yearly_ab.json")
    y_by = {int(r["year"]): r for r in y_ab}

    errors = []
    for s in hardcoded:
        t = int(s["test"])
        row = next(r for r in wfo if int(r["test"]) == t)
        if round(float(row["AB_sharpe"]), 4) != round(float(s["AB_sharpe"]), 4):
            errors.append(("hardcoded_split_AB_sharpe", t))
        if round(float(row["AB_taker_sharpe"]), 4) != round(float(s["AB_taker_sharpe"]), 4):
            errors.append(("hardcoded_split_AB_taker_sharpe", t))
        if round(float(row["best_w"]), 1) != round(float(s["best_w"]), 1):
            errors.append(("hardcoded_split_best_w", t))
        if round(float(y_by[t]["total_return_pct"]), 2) != round(float(s["AB_return_pct"]), 2):
            errors.append(("hardcoded_split_AB_return_pct", t))
        if round(float(y_by[t]["mdd_pct"]), 2) != round(float(s["AB_mdd_pct"]), 2):
            errors.append(("hardcoded_split_AB_mdd_pct", t))

    fb = re.search(
        r"const fallbackSummary = \{\s*ab: \{ total: ([\d\.]+), cagr: ([\d\.]+), mdd: (-?[\d\.]+), sharpe: ([\d\.]+) \},\s*taker: \{ total: ([\d\.]+), cagr: ([\d\.]+), mdd: (-?[\d\.]+), sharpe: ([\d\.]+) \}\s*\};",
        idx,
    )
    if not fb:
        errors.append(("fallbackSummary_parse_failed", 0))
    else:
        fb_ab = [float(fb.group(i)) for i in range(1, 5)]
        fb_t = [float(fb.group(i)) for i in range(5, 9)]
        ab = _equity_stats(_load_json(base / "docs" / "assets_public" / "equity_ab.json"))
        t = _equity_stats(_load_json(base / "docs" / "assets_public" / "equity_ab_taker.json"))
        if [round(x, 4) for x in ab] != [round(x, 4) for x in fb_ab]:
            errors.append(("fallbackSummary_ab_mismatch", 0))
        if [round(x, 4) for x in t] != [round(x, 4) for x in fb_t]:
            errors.append(("fallbackSummary_taker_mismatch", 0))

    print("hardcoded_splits:", len(hardcoded))
    print("errors:", len(errors))
    for e in errors[:50]:
        print(" -", e)
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())


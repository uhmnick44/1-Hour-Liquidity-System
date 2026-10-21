"""Replay a TradingView export of ``tools/tradingview/bsl_ssl_parity_export.pine``
through the Python port and compare state on every bar.

Usage: python scripts/run_parity.py [path/to/export.csv] [--tie-rule RULE]

The export's first rows carry state from bars that precede the export, so the
port (which starts empty) cannot match them. Eviction is a pure FIFO on new
pivots, so once ``max_levels`` new pivots have formed on each side inside the
export, both sides hold exactly the same levels and the port must match on every
later bar. The script reports the convergence bar and all mismatches after it.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lsr.liquidity_engine import EngineParams, LiquidityEngine, PivotTieRule  # noqa: E402

DEFAULT_CSV = Path(__file__).resolve().parents[1] / "data/tradingview/CME_MINI_MNQ1_60_parity_export.csv"
MAX = 8


def load_export(path: Path, drop_last: bool = True) -> pd.DataFrame:
    df = pd.read_csv(path)
    if drop_last:
        df = df.iloc[:-1].reset_index(drop=True)  # last exported row is an unfinished bar
    return df


def replay(df: pd.DataFrame, params: EngineParams) -> pd.DataFrame:
    eng = LiquidityEngine(params)
    rows = []
    for r in df.itertuples(index=False):
        ev = eng.on_bar(float(r.high), float(r.low), float(r.close))
        row = {
            "new_bsl_px": ev.new_bsl_px, "new_ssl_px": ev.new_ssl_px,
            "bsl_swept_now": int(ev.bsl_swept_now), "ssl_swept_now": int(ev.ssl_swept_now),
            "bsl_reclaim_now": int(ev.bsl_reclaim_now), "ssl_reclaim_now": int(ev.ssl_reclaim_now),
            "bsl_count": len(eng.bsl), "ssl_count": len(eng.ssl),
        }
        for side, arr in (("bsl", eng.bsl), ("ssl", eng.ssl)):
            for k in range(MAX):
                row[f"{side}_px_{k}"] = arr[k].price if k < len(arr) else math.nan
                row[f"{side}_swept_{k}"] = float(arr[k].swept) if k < len(arr) else math.nan
        rows.append(row)
    return pd.DataFrame(rows)


def compare(tv: pd.DataFrame, port: pd.DataFrame) -> dict:
    slot_cols = [f"{s}_{w}_{k}" for s in ("bsl", "ssl") for w in ("px", "swept") for k in range(MAX)]
    event_cols = ["new_bsl_px", "new_ssl_px", "bsl_swept_now", "ssl_swept_now",
                  "bsl_reclaim_now", "ssl_reclaim_now", "bsl_count", "ssl_count"]

    def eq(a: pd.Series, b: pd.Series) -> pd.Series:
        a = a.astype(float); b = b.astype(float)
        return (a == b) | (a.isna() & b.isna())

    slot_match = pd.concat([eq(tv[c], port[c]) for c in slot_cols], axis=1).all(axis=1)
    # convergence: first bar from which the slots never diverge again
    conv = None
    ok = slot_match.values
    for i in range(len(ok)):
        if ok[i:].all():
            conv = i
            break
    result = {"bars": len(tv), "convergence_bar": conv}
    if conv is None:
        result["slot_mismatch_bars"] = int((~slot_match).sum())
        result["first_slot_mismatch"] = int((~slot_match).idxmax())
        return result
    after = slice(conv, None)
    mism = {}
    for c in event_cols:
        bad = ~eq(tv[c].iloc[after].reset_index(drop=True), port[c].iloc[after].reset_index(drop=True))
        if bad.any():
            mism[c] = {"count": int(bad.sum()), "first_bar": int(conv + bad.idxmax())}
    result["event_mismatches_after_convergence"] = mism
    return result


def count_tie_cases(df: pd.DataFrame, n: int) -> dict:
    """Count candidate pivots whose classification depends on the tie rule."""
    highs, lows = df["high"].values, df["low"].values
    out = {"high_ties": 0, "low_ties": 0}
    for c in range(n, len(df) - n):
        for key, s, hi in (("high_ties", highs, True), ("low_ties", lows, False)):
            cand = s[c]; nb = list(s[c - n:c]) + list(s[c + 1:c + n + 1])
            strict = all(cand > x for x in nb) if hi else all(cand < x for x in nb)
            loose = all(cand >= x for x in nb) if hi else all(cand <= x for x in nb)
            if loose and not strict:
                out[key] += 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?", default=str(DEFAULT_CSV))
    ap.add_argument("--all-rules", action="store_true", help="try every tie rule")
    ap.add_argument("--tie-rule", default=PivotTieRule.LEFT_GE_RIGHT_STRICT.value)
    args = ap.parse_args()

    df = load_export(Path(args.csv))
    print(f"export: {args.csv}\nbars used: {len(df)} (last unfinished bar dropped)")
    print("tie-dependent candidate pivots in data:", count_tie_cases(df, 5))
    rules = list(PivotTieRule) if args.all_rules else [PivotTieRule(args.tie_rule)]
    overall_ok = False
    for rule in rules:
        params = EngineParams(tie_rule=rule)
        res = compare(df, replay(df, params))
        clean = res.get("convergence_bar") is not None and not res.get("event_mismatches_after_convergence")
        overall_ok |= clean
        print(f"\n[{rule.value}] {'PASS' if clean else 'FAIL'}: {res}")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

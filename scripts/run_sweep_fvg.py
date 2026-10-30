"""Development run and walk-forward for the 10-MNQ liquidity sweep -> first 1-minute FVG strategy.

    python scripts/run_sweep_fvg.py --start 2022-10-02 --end 2024-10-21            # development, 9 scenarios
    python scripts/run_sweep_fvg.py --start 2024-10-21 --end 2026-10-21 --offsets 2 --slips 1,2,3 --label holdout

The holdout (most recent two years) is run only on the user's explicit approval.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lsr.backtest_sweep import run_sweep_fvg_backtest  # noqa: E402
from lsr.config import DATASETS, BacktestConfig  # noqa: E402
from lsr.data import build_market_data  # noqa: E402
from lsr.report import bootstrap_mean_ci, max_drawdown, wilson_interval  # noqa: E402

NY = "America/New_York"


def scenario_cfg(offset: int, slip: int) -> BacktestConfig:
    cfg = BacktestConfig()
    return dataclasses.replace(cfg, data=DATASETS["2022_2026"],
                               risk=dataclasses.replace(cfg.risk, fixed_contracts=10, min_stop_points=0.0),
                               strategy=dataclasses.replace(cfg.strategy, exit_mode="be_at_1r_tp_2r"),
                               costs=dataclasses.replace(cfg.costs, slippage_ticks=slip),
                               sweepfvg=dataclasses.replace(cfg.sweepfvg, stop_offset_ticks=offset))


def metrics(tr: pd.DataFrame) -> dict:
    if tr.empty:
        return dict(trades=0)
    w = tr[tr.net_pnl_usd > 0]; l = tr[tr.net_pnl_usd <= 0]
    r = tr.r_net.to_numpy(); lo, hi = bootstrap_mean_ci(r); wl, wh = wilson_interval(len(w), len(tr))
    eq = pd.concat([pd.Series([0.0]), tr.net_pnl_usd.cumsum()], ignore_index=True)
    dd = float((eq - eq.cummax()).min())
    gp = w.net_pnl_usd.sum(); gl = -l.net_pnl_usd.sum()
    return dict(trades=int(len(tr)), win_rate=len(w) / len(tr), win_rate_ci95=[wl, wh], expectancy_r=float(r.mean()),
                expectancy_r_ci95=[lo, hi], avg_win_r=float(w.r_net.mean()) if len(w) else float("nan"),
                avg_loss_r=float(l.r_net.mean()) if len(l) else float("nan"), profit_factor=float(gp / gl) if gl > 0 else float("inf"),
                net_pnl_usd=float(tr.net_pnl_usd.sum()), max_drawdown_usd=dd, fees_usd=float(tr.fees_usd.sum()),
                slippage_usd=float(((tr.entry_slippage_ticks + tr.exit_slippage_ticks) * 0.5 * tr.contracts).sum()),
                exits=tr.exit_reason.value_counts().to_dict(), ambiguous=int(tr.trade_flags.fillna("").str.contains("ambiguous").sum()))


def with_sources(res) -> pd.DataFrame:
    tr = res.trades.copy()
    if tr.empty:
        return tr
    ev = res.setups.set_index("event_id")
    tr["event_id"] = tr.setup_ref.astype(int)
    for col in ("window", "levels", "n_levels", "extreme_level", "first_penetration_ts", "confirmed_at", "fvg_confirmed_at", "fvg_candle1_ts", "stop_reference"):
        tr[col] = tr.event_id.map(ev[col])
    tr["entry_ts_et"] = pd.to_datetime(tr.entry_ts, utc=True).dt.tz_convert(NY)
    tr["exit_ts_et"] = pd.to_datetime(tr.exit_ts, utc=True).dt.tz_convert(NY)
    tr["entry_price_contract"] = tr.entry_price_raw; tr["exit_price_contract"] = tr.exit_price_raw
    return tr


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2022-10-02"); ap.add_argument("--end", default="2024-10-21")
    ap.add_argument("--offsets", default="1,2,4"); ap.add_argument("--slips", default="1,2,3")
    ap.add_argument("--folds", type=int, default=4); ap.add_argument("--label", default="dev")
    ap.add_argument("--out", default=str(ROOT / "results" / "sweep_fvg"))
    args = ap.parse_args()
    offsets = [int(x) for x in args.offsets.split(",")]; slips = [int(x) for x in args.slips.split(",")]
    start = pd.Timestamp(args.start, tz="UTC"); end = pd.Timestamp(args.end, tz="UTC")
    edges = pd.date_range(start, end, periods=args.folds + 1)

    base = scenario_cfg(2, 2)
    md = build_market_data(base.data, base.strategy)
    print("data:", {k: md.validation[k] for k in ("m1_bars", "h1_bars", "dropped_outside_session", "first_ts", "last_ts")}, flush=True)
    out = Path(args.out) / args.label; out.mkdir(parents=True, exist_ok=True)
    summary = {"label": args.label, "start": str(start), "end": str(end), "folds": [str(e) for e in edges], "scenarios": {}}
    for off in offsets:
        for sl in slips:
            cfg = scenario_cfg(off, sl)
            res = run_sweep_fvg_backtest(md, cfg, start_ts=start, end_ts=end)
            tr = with_sources(res)
            key = f"stop{off}_slip{sl}"
            folds = []
            for i in range(args.folds):
                f = tr[(pd.to_datetime(tr.entry_ts, utc=True) >= edges[i]) & (pd.to_datetime(tr.entry_ts, utc=True) < edges[i + 1])] if not tr.empty else tr
                folds.append(dict(fold=i + 1, start=str(edges[i].date()), end=str(edges[i + 1].date()), **metrics(f)))
            sessions = {w: metrics(g) for w, g in tr.groupby("window")} if not tr.empty else {}
            ev = res.setups
            summary["scenarios"][key] = dict(stop_offset_ticks=off, slippage_ticks=sl, overall=metrics(tr), folds=folds, by_session=sessions,
                                             events=ev.status.value_counts().to_dict() if not ev.empty else {},
                                             skipped_entries=res.skipped_entries.reason.value_counts().to_dict() if not res.skipped_entries.empty else {},
                                             ignored_sweeps=res.ignored_sweeps.reason.value_counts().to_dict() if not res.ignored_sweeps.empty else {},
                                             levels_created=int(len(res.levels)), force_closes=res.engine_events.get("force_closes"),
                                             ambiguity=res.ambiguity)
            tr.to_csv(out / f"trades_{key}.csv", index=False)
            ev.to_csv(out / f"events_{key}.csv", index=False)
            res.equity_curve.to_csv(out / f"equity_{key}.csv", index=False)
            if key == "stop2_slip2":
                res.levels.to_csv(out / "levels_stop2_slip2.csv", index=False)
            m = summary["scenarios"][key]["overall"]
            print(f"{key}: trades {m.get('trades')} expR {m.get('expectancy_r', float('nan')):+.3f} CI {m.get('expectancy_r_ci95')} PF {m.get('profit_factor', float('nan')):.2f} net {m.get('net_pnl_usd', 0):,.0f} | folds "
                  + " ".join(f"{f['expectancy_r']:+.2f}({f['trades']})" if f.get('trades') else "n/a" for f in folds), flush=True)
    # selection rule, fixed in advance: best worst-fold expectancy at 2-tick slippage
    cands = {off: min(f["expectancy_r"] for f in summary["scenarios"][f"stop{off}_slip2"]["folds"] if f.get("trades")) for off in offsets if f"stop{off}_slip2" in summary["scenarios"]}
    if cands:
        best = max(cands, key=cands.get)
        summary["selection"] = dict(rule="max over stop offsets of the minimum fold expectancy at 2-tick slippage", worst_fold_by_offset=cands, selected_stop_offset=best)
        print("selection:", summary["selection"], flush=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

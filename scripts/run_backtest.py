"""Run the V1 backtest. Example:
    python scripts/run_backtest.py --slippage-ticks 2 --label baseline
    python scripts/run_backtest.py --sensitivity          # 1, 2 and 4 ticks
"""
from __future__ import annotations

import argparse
import dataclasses
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lsr.backtest import run_backtest  # noqa: E402
from lsr.config import DATASETS, BacktestConfig, CostConfig, SplitConfig  # noqa: E402
from lsr.data import build_market_data  # noqa: E402
from lsr.report import render_markdown, write_outputs  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slippage-ticks", type=int, default=2)
    ap.add_argument("--label", default=None)
    ap.add_argument("--out", default=str(ROOT / "results"))
    ap.add_argument("--sensitivity", action="store_true")
    ap.add_argument("--entry-mode", default="market_and_limit", choices=["market_and_limit", "market_only"],
                    help="market_and_limit = V1 baseline; market_only = V2 experiment")
    ap.add_argument("--exit-mode", default="fixed_1r", choices=["fixed_1r", "be_at_1r_tp_2r"],
                    help="fixed_1r = V1/V2; be_at_1r_tp_2r = V3 experiment")
    ap.add_argument("--prefix", default="", help="results sub-directory prefix, e.g. v2_")
    ap.add_argument("--dataset", default="2025_2026", choices=sorted(DATASETS))
    ap.add_argument("--single-block", action="store_true",
                    help="no development split: the whole dataset is one out-of-sample block (for a frozen rule)")
    args = ap.parse_args()
    base = BacktestConfig()
    base = dataclasses.replace(base, data=DATASETS[args.dataset],
                               strategy=dataclasses.replace(base.strategy, entry_mode=args.entry_mode, exit_mode=args.exit_mode),
                               split=SplitConfig(dev_fraction=0.0) if args.single_block else base.split)
    md = build_market_data(base.data, base.strategy)
    v = dict(md.validation); print("data:", {k: v[k] for k in ("m1_bars", "h1_bars", "dropped_outside_session", "first_ts", "last_ts", "tick_valid")})
    print("rolls:"); [print("  ", r) for r in v["rolls"]]
    runs = [(1, "optimistic_1tick"), (2, "baseline_2ticks"), (4, "conservative_4ticks")] if args.sensitivity \
        else [(args.slippage_ticks, args.label or f"slippage_{args.slippage_ticks}ticks")]
    for ticks, label in runs:
        cfg = dataclasses.replace(base, costs=dataclasses.replace(base.costs, slippage_ticks=ticks))
        res = run_backtest(md, cfg)
        out = Path(args.out) / (args.prefix + label)
        rep = write_outputs(res, md, out, args.prefix + label)
        md_text = render_markdown(rep)
        (out / "summary.md").write_text(md_text)
        print(md_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

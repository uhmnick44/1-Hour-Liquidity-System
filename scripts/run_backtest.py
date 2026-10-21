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
from lsr.config import BacktestConfig, CostConfig  # noqa: E402
from lsr.data import build_market_data  # noqa: E402
from lsr.report import render_markdown, write_outputs  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slippage-ticks", type=int, default=2)
    ap.add_argument("--label", default=None)
    ap.add_argument("--out", default=str(ROOT / "results"))
    ap.add_argument("--sensitivity", action="store_true")
    args = ap.parse_args()
    base = BacktestConfig()
    md = build_market_data(base.data, base.strategy)
    runs = [(1, "optimistic_1tick"), (2, "baseline_2ticks"), (4, "conservative_4ticks")] if args.sensitivity \
        else [(args.slippage_ticks, args.label or f"slippage_{args.slippage_ticks}ticks")]
    for ticks, label in runs:
        cfg = dataclasses.replace(base, costs=dataclasses.replace(base.costs, slippage_ticks=ticks))
        res = run_backtest(md, cfg)
        out = Path(args.out) / label
        rep = write_outputs(res, md, out, label)
        md_text = render_markdown(rep)
        (out / "summary.md").write_text(md_text)
        print(md_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

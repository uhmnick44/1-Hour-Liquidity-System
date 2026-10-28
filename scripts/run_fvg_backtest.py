"""Run the 1H sweep -> 1M FVG strategy. Writes the setup log, ignored-sweep log,
trade log and a sample trade trace. Section 16 decisions are PROVISIONAL inputs
(see FvgConfig); no performance claim is made from this script's output.

    python scripts/run_fvg_backtest.py --dataset 2025_2026 --sweep-mode intrabar_1m
"""
from __future__ import annotations

import argparse
import dataclasses
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lsr.backtest import run_fvg_backtest  # noqa: E402
from lsr.config import DATASETS, BacktestConfig, FvgConfig, SplitConfig  # noqa: E402
from lsr.data import build_market_data  # noqa: E402
from lsr.report import render_markdown, write_outputs  # noqa: E402

NY = "America/New_York"


import pandas as pd


def trace(res, md, setup_id: int) -> str:
    s = res.setups[res.setups.sweep_id == setup_id].iloc[0]
    t = res.trades[res.trades.signal_bar_ts == s.fvg_candle_c_ts]
    m1 = md.m1
    lines = [f"Setup {setup_id}: {s.sweep_direction} after level {s.level_price} ({s.level_id}) swept",
             f"  sweep timestamp      {pd.Timestamp(s.sweep_timestamp).tz_convert(NY)}  (close of the first 1m bar through the level)",
             f"  expiration           {pd.Timestamp(s.expiration_timestamp).tz_convert(NY)}",
             f"  FVG A candle open    {pd.Timestamp(s.fvg_candle_a_ts).tz_convert(NY)}",
             f"  FVG C candle open    {pd.Timestamp(s.fvg_candle_c_ts).tz_convert(NY)}  confirmed at {pd.Timestamp(s.fvg_confirmation_timestamp).tz_convert(NY)}",
             f"  reversal extreme     {s.reversal_extreme} at {pd.Timestamp(s.reversal_extreme_ts).tz_convert(NY)} over {s.window_candles} candles",
             f"  entry                {pd.Timestamp(s.entry_timestamp).tz_convert(NY)} fill {s.entry_fill_price} ({s.setup_status})",
             f"  original distance    {s.original_stop_distance}  doubled {s.doubled_stop_distance}  placed distance {s.final_stop_distance}  final stop {s.final_stop_price}"]
    w = m1[(m1.index >= pd.Timestamp(s.sweep_timestamp) - pd.Timedelta(minutes=1)) & (m1.index <= pd.Timestamp(s.entry_timestamp))]
    lines.append("  1-minute candles, sweep candle through entry candle (adjusted prices):")
    for r in w.itertuples():
        lines.append(f"    {r.Index.tz_convert(NY).strftime('%H:%M')}  O {r.open:9.2f} H {r.high:9.2f} L {r.low:9.2f} C {r.close:9.2f}")
    if len(t):
        r = t.iloc[0]
        lines.append(f"  exit                 {pd.Timestamp(r.exit_ts).tz_convert(NY)} at {r.exit_price} ({r.exit_reason}) net ${r.net_pnl_usd:.2f}, {r.contracts} contracts  [exit rule PROVISIONAL]")
    return "\n".join(lines)


def main() -> int:
    import pandas as pd  # noqa: F401
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="2025_2026", choices=sorted(DATASETS))
    ap.add_argument("--sweep-mode", default="intrabar_1m", choices=["intrabar_1m", "h1_close"])
    ap.add_argument("--slippage-ticks", type=int, default=2)
    ap.add_argument("--single-block", action="store_true")
    ap.add_argument("--stop-multiple", type=float, default=2.0, help="2.0 = original doubled stop; 1.0 = (doubled * 0.5), stop at the reversal wick")
    ap.add_argument("--exit-mode", default="fixed_1r", choices=["fixed_1r", "be_at_1r_tp_2r"])
    ap.add_argument("--min-stop-points", type=float, default=None, help="override the 10-point minimum (0 disables)")
    ap.add_argument("--session", default=None, help="entry session New York, e.g. 09:30-11:30")
    ap.add_argument("--out", default=str(ROOT / "results"))
    args = ap.parse_args()
    base = BacktestConfig()
    cfg = dataclasses.replace(base, data=DATASETS[args.dataset], costs=dataclasses.replace(base.costs, slippage_ticks=args.slippage_ticks),
                              fvg=dataclasses.replace(base.fvg, sweep_timestamp_mode=args.sweep_mode,
                                                      session_start=args.session.split("-")[0] if args.session else None,
                                                      session_end=args.session.split("-")[1] if args.session else None),
                              strategy=dataclasses.replace(base.strategy, stop_multiple=args.stop_multiple, exit_mode=args.exit_mode),
                              risk=dataclasses.replace(base.risk, min_stop_points=args.min_stop_points) if args.min_stop_points is not None else base.risk,
                              split=SplitConfig(dev_fraction=0.0) if args.single_block else base.split)
    md = build_market_data(cfg.data, cfg.strategy)
    res = run_fvg_backtest(md, cfg)
    label = f"fvg_{args.dataset}_{args.sweep_mode}_{args.slippage_ticks}ticks"
    if args.stop_multiple != 2.0 or args.exit_mode != "fixed_1r" or args.min_stop_points is not None:
        label += f"_stop{args.stop_multiple:g}x_{args.exit_mode}_min{cfg.risk.min_stop_points:g}"
    if args.session:
        label += "_session" + args.session.replace(":", "")
    out = Path(args.out) / label
    rep = write_outputs(res, md, out, label)
    res.setups.to_csv(out / "setups.csv", index=False)
    res.ignored_sweeps.to_csv(out / "ignored_sweeps.csv", index=False)
    (out / "summary.md").write_text(render_markdown(rep))
    st = res.setups
    print(f"{label}: setups {len(st)} | status counts {st.setup_status.value_counts().to_dict()} | reject reasons {st.reject_reason.value_counts().to_dict()} | ignored sweeps {len(res.ignored_sweeps)} | trades {len(res.trades)}")
    entered = st[st.setup_status == "ENTRY_TRIGGERED"]
    if len(entered):
        tr = trace(res, md, int(entered.sweep_id.iloc[0]))
        (out / "sample_trace.txt").write_text(tr); print(tr)
    return 0


if __name__ == "__main__":
    import pandas as pd
    raise SystemExit(main())

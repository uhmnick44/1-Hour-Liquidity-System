"""Performance reporting with development / out-of-sample separation."""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

from .backtest import BacktestResult
from .config import BacktestConfig
from .data import MarketData

NY = "America/New_York"


def split_boundary(md: MarketData, cfg: BacktestConfig) -> pd.Timestamp:
    """Chronological boundary fixed from the data span alone: start + dev_fraction * span."""
    start = md.h1.index[0]; end = md.h1.close_ts.iloc[-1]
    return start + (end - start) * cfg.split.dev_fraction


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n; d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (centre - half, centre + half)


def bootstrap_mean_ci(x: np.ndarray, n_boot: int = 5000, seed: int = 7) -> tuple[float, float]:
    if len(x) == 0:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    means = np.array([rng.choice(x, size=len(x), replace=True).mean() for _ in range(n_boot)])
    return (float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5)))


def max_drawdown(equity: pd.Series) -> tuple[float, float]:
    peak = equity.cummax(); dd = equity - peak
    i = dd.idxmin() if len(dd) else None
    if i is None or len(dd) == 0:
        return (0.0, 0.0)
    return (float(dd.min()), float((dd / peak).min()))


def summarize_trades(tr: pd.DataFrame, starting_equity: float) -> Dict[str, object]:
    if tr.empty:
        return {"total_trades": 0}
    wins = tr[tr.net_pnl_usd > 0]; losses = tr[tr.net_pnl_usd <= 0]
    eq = pd.concat([pd.Series([starting_equity]), starting_equity + tr.net_pnl_usd.cumsum()], ignore_index=True)
    mdd_usd, mdd_pct = max_drawdown(eq)
    gp = wins.net_pnl_usd.sum(); gl = -losses.net_pnl_usd.sum()
    r = tr.r_net.to_numpy()
    lo, hi = wilson_interval(len(wins), len(tr)); rlo, rhi = bootstrap_mean_ci(r)
    # longest losing streak
    streak = best = 0
    for v in tr.net_pnl_usd:
        streak = streak + 1 if v <= 0 else 0; best = max(best, streak)
    return {
        "total_trades": int(len(tr)), "winning_trades": int(len(wins)), "losing_trades": int(len(losses)),
        "win_rate": len(wins) / len(tr), "win_rate_ci95": [lo, hi],
        "avg_win_r": float(wins.r_net.mean()) if len(wins) else float("nan"),
        "avg_loss_r": float(losses.r_net.mean()) if len(losses) else float("nan"),
        "avg_win_usd": float(wins.net_pnl_usd.mean()) if len(wins) else float("nan"),
        "avg_loss_usd": float(losses.net_pnl_usd.mean()) if len(losses) else float("nan"),
        "expectancy_r": float(r.mean()), "expectancy_r_ci95": [rlo, rhi], "expectancy_usd": float(tr.net_pnl_usd.mean()),
        "profit_factor": float(gp / gl) if gl > 0 else float("inf"),
        "gross_pnl_usd": float(tr.gross_pnl_usd.sum()), "fees_usd": float(tr.fees_usd.sum()),
        "slippage_usd": float(((tr.entry_slippage_ticks + tr.exit_slippage_ticks) * 0.5 * tr.contracts).sum()),
        "net_pnl_usd": float(tr.net_pnl_usd.sum()), "ending_equity": float(eq.iloc[-1]),
        "max_drawdown_usd": mdd_usd, "max_drawdown_pct": mdd_pct, "longest_losing_streak": int(best),
        "avg_contracts": float(tr.contracts.mean()), "avg_planned_risk_usd": float(tr.planned_risk_usd.mean()),
        "avg_planned_risk_pct_of_equity": float((tr.planned_risk_usd / tr.equity_at_entry).mean()),
        "avg_stop_distance_points": float(tr.stop_distance.mean()),
        "exit_reasons": tr.exit_reason.value_counts().to_dict(),
        "by_entry_type": {k: {"trades": int(len(g)), "win_rate": float((g.net_pnl_usd > 0).mean()), "expectancy_r": float(g.r_net.mean())}
                          for k, g in tr.groupby("entry_type")},
        "by_direction": {k: {"trades": int(len(g)), "win_rate": float((g.net_pnl_usd > 0).mean()), "expectancy_r": float(g.r_net.mean())}
                         for k, g in tr.groupby("direction")},
    }


def order_stats(ev: pd.DataFrame, tr: pd.DataFrame, sig: pd.DataFrame) -> Dict[str, object]:
    ev = ev if not ev.empty else pd.DataFrame(columns=["outcome", "reason", "entry_type"])
    limit_filled = int((tr.entry_type == "limit").sum()) if not tr.empty else 0
    limit_expired = int(((ev.outcome == "expired")).sum())
    limit_invalidated = int(((ev.outcome == "invalidated")).sum())
    limit_flatten = int(((ev.outcome == "flatten_cancel") & (ev.entry_type == "limit")).sum())
    limit_placed = limit_filled + limit_expired + limit_invalidated + limit_flatten
    skipped = ev[ev.outcome == "skipped"].reason.value_counts().to_dict()
    return {
        "signals": int(len(sig)), "limit_orders_placed": limit_placed, "limit_orders_filled": limit_filled,
        "limit_fill_rate": limit_filled / limit_placed if limit_placed else float("nan"),
        "expired_orders": limit_expired, "invalidated_orders": limit_invalidated, "flatten_cancelled_orders": limit_flatten,
        "invalidation_reasons": ev[ev.outcome == "invalidated"].reason.value_counts().to_dict(),
        "skipped_setups_by_reason": skipped, "no_setup_by_reason": ev[ev.outcome == "no_setup"].reason.value_counts().to_dict(),
    }


def monthly_table(tr: pd.DataFrame) -> pd.DataFrame:
    if tr.empty:
        return pd.DataFrame()
    m = tr.assign(month=tr.exit_ts.dt.tz_convert(NY).dt.strftime("%Y-%m"))
    return m.groupby("month").agg(trades=("net_pnl_usd", "size"), wins=("net_pnl_usd", lambda s: int((s > 0).sum())),
                                  net_pnl_usd=("net_pnl_usd", "sum"), expectancy_r=("r_net", "mean")).reset_index()


def hourly_table(tr: pd.DataFrame) -> pd.DataFrame:
    if tr.empty:
        return pd.DataFrame()
    h = tr.assign(hour_et=tr.entry_ts.dt.tz_convert(NY).dt.hour)
    return h.groupby("hour_et").agg(trades=("net_pnl_usd", "size"), wins=("net_pnl_usd", lambda s: int((s > 0).sum())),
                                    net_pnl_usd=("net_pnl_usd", "sum"), expectancy_r=("r_net", "mean")).reset_index()


def _periodize(res: BacktestResult, boundary: pd.Timestamp):
    tr = res.trades; ev = res.events; sg = res.signals
    key_tr = tr.signal_close_ts if not tr.empty else pd.Series(dtype="datetime64[ns, UTC]")
    key_ev = ev.ts if not ev.empty else pd.Series(dtype="datetime64[ns, UTC]")
    key_sg = sg.close_ts if not sg.empty else pd.Series(dtype="datetime64[ns, UTC]")
    dev = (tr[key_tr <= boundary], ev[key_ev <= boundary], sg[key_sg <= boundary])
    oos = (tr[key_tr > boundary], ev[key_ev > boundary], sg[key_sg > boundary])
    return dev, oos


def build_report(res: BacktestResult, md: MarketData, label: str) -> Dict[str, object]:
    cfg = res.config
    boundary = split_boundary(md, cfg)
    (dtr, dev_ev, dsg), (otr, oev, osg) = _periodize(res, boundary)
    start_eq = cfg.risk.starting_equity
    # OOS period starts from the equity realized at the end of development
    oos_start_eq = float(dtr.equity_after.iloc[-1]) if not dtr.empty else start_eq
    rep = {
        "label": label,
        "config": {"slippage_ticks": cfg.costs.slippage_ticks, "fees_per_side": cfg.costs.fees_per_side,
                   "starting_equity": start_eq, "risk_fraction": cfg.risk.risk_fraction, "max_contracts": cfg.risk.max_contracts,
                   "min_stop_points": cfg.risk.min_stop_points, "limit_window_candles": cfg.strategy.limit_window_candles},
        "data": {"h1_bars": res.h1_count, "m1_bars": res.m1_count, "first_bar": str(md.h1.index[0]), "last_bar_close": str(md.h1.close_ts.iloc[-1]),
                 "engine_new_levels": res.engine_events.get("new_levels"), "engine_sweeps": res.engine_events.get("sweeps")},
        "split": {"boundary_utc": str(boundary), "boundary_et": str(boundary.tz_convert(NY)), "dev_fraction": cfg.split.dev_fraction},
        "full_sample": {"performance": summarize_trades(res.trades, start_eq), "orders": order_stats(res.events, res.trades, res.signals)},
        "development": {"performance": summarize_trades(dtr, start_eq), "orders": order_stats(dev_ev, dtr, dsg)},
        "out_of_sample": {"performance": summarize_trades(otr, oos_start_eq), "orders": order_stats(oev, otr, osg)},
        "ambiguity": res.ambiguity,
        "flagged_trades": res.trades.trade_flags.replace("", np.nan).dropna().value_counts().to_dict() if not res.trades.empty else {},
        "rolls": md.validation.get("rolls"),
        "calendar_overrides": [dict(date=str(s.date.date()), close_et=str(s.close.tz_convert(NY)), note=s.override_note)
                               for s in md.sessions if s.override_note],
    }
    return rep


def write_outputs(res: BacktestResult, md: MarketData, out_dir: Path, label: str) -> Dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    rep = build_report(res, md, label)
    (out_dir / "summary.json").write_text(json.dumps(rep, indent=2, default=str))
    res.trades.to_csv(out_dir / "trades.csv", index=False)
    res.events.to_csv(out_dir / "order_events.csv", index=False)
    res.signals.to_csv(out_dir / "signals.csv", index=False)
    res.equity_curve.to_csv(out_dir / "equity_curve.csv", index=False)
    monthly_table(res.trades).to_csv(out_dir / "monthly.csv", index=False)
    hourly_table(res.trades).to_csv(out_dir / "hourly_et.csv", index=False)
    pd.DataFrame(md.validation.get("rolls")).to_csv(out_dir / "rolls.csv", index=False)
    return rep


def render_markdown(rep: Dict[str, object]) -> str:
    def perf_rows(p):
        if p.get("total_trades", 0) == 0:
            return "| trades | 0 |\n"
        rows = [("Trades", p["total_trades"]), ("Wins / losses", f"{p['winning_trades']} / {p['losing_trades']}"),
                ("Win rate", f"{p['win_rate']:.1%} (95% CI {p['win_rate_ci95'][0]:.1%} to {p['win_rate_ci95'][1]:.1%})"),
                ("Avg win R / avg loss R", f"{p['avg_win_r']:.3f} / {p['avg_loss_r']:.3f}"),
                ("Expectancy R", f"{p['expectancy_r']:+.3f} (95% CI {p['expectancy_r_ci95'][0]:+.3f} to {p['expectancy_r_ci95'][1]:+.3f})"),
                ("Profit factor", f"{p['profit_factor']:.2f}"), ("Net profit after costs", f"${p['net_pnl_usd']:,.2f}"),
                ("Fees / price slippage", f"${p['fees_usd']:,.2f} / ${p['slippage_usd']:,.2f}"),
                ("Ending equity", f"${p['ending_equity']:,.2f}"),
                ("Max drawdown", f"${p['max_drawdown_usd']:,.2f} ({p['max_drawdown_pct']:.1%})"),
                ("Longest losing streak", p["longest_losing_streak"]),
                ("Avg contracts / avg planned risk", f"{p['avg_contracts']:.2f} / {p['avg_planned_risk_pct_of_equity']:.2%} of equity"),
                ("Exits", ", ".join(f"{k} {v}" for k, v in p["exit_reasons"].items()))]
        return "".join(f"| {k} | {v} |\n" for k, v in rows)

    def order_rows(o):
        return (f"| Signals | {o['signals']} |\n| Limit orders placed / filled | {o['limit_orders_placed']} / {o['limit_orders_filled']} "
                f"({o['limit_fill_rate']:.1%}) |\n| Expired / invalidated / cancelled at flatten | {o['expired_orders']} / {o['invalidated_orders']} / {o['flatten_cancelled_orders']} |\n"
                f"| Skipped setups | {o['skipped_setups_by_reason']} |\n")

    s = [f"# {rep['label']}\n", f"Slippage {rep['config']['slippage_ticks']} ticks per eligible fill, fees ${rep['config']['fees_per_side']:.2f} per side, "
         f"starting equity ${rep['config']['starting_equity']:,.0f}, risk {rep['config']['risk_fraction']:.0%}, max {rep['config']['max_contracts']} contracts.\n",
         f"Data: {rep['data']['h1_bars']} 1H bars from {rep['data']['first_bar']} to {rep['data']['last_bar_close']}. "
         f"Split boundary {rep['split']['boundary_et']}.\n"]
    for sec, title in (("development", "Development period"), ("out_of_sample", "Out-of-sample period"), ("full_sample", "Full sample")):
        s.append(f"\n## {title}\n\n| Metric | Value |\n|---|---|\n" + perf_rows(rep[sec]["performance"]) + order_rows(rep[sec]["orders"]))
    s.append(f"\nAmbiguous 1-minute sequences: {rep['ambiguity']}. Flagged trades: {rep['flagged_trades']}.\n")
    return "".join(s)

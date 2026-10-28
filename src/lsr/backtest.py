"""Chronological backtest loop.

For each 1H bar, in time order:
1. feed its 1-minute bars to the simulator (orders created at earlier 1H closes
   execute here; positions are managed here),
2. tell the simulator the 1H candle closed (limit-window expiry),
3. update the liquidity engine with the closed candle and evaluate the signal,
4. hand any signal to the simulator, which creates at most one order.

Step order guarantees that nothing created at a 1H close can act before the
first 1-minute bar of the next hour, and that the engine never sees a candle
before it has closed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .config import BacktestConfig
from .data import MarketData
from .execution import MinuteBar, Simulator
from .fvg import Candle, SetupManager, SetupStatus, SweepTimestampMode
from .liquidity_engine import EngineParams, LiquidityEngine, PivotTieRule
from .signals import evaluate_candle


@dataclass
class BacktestResult:
    trades: pd.DataFrame
    events: pd.DataFrame
    signals: pd.DataFrame
    equity_curve: pd.DataFrame
    ambiguity: Dict[str, int]
    config: BacktestConfig
    h1_count: int
    m1_count: int
    engine_events: Dict[str, int] = field(default_factory=dict)
    setups: Optional[pd.DataFrame] = None          # FVG strategy only
    ignored_sweeps: Optional[pd.DataFrame] = None  # FVG strategy only


def engine_params(cfg: BacktestConfig) -> EngineParams:
    s = cfg.strategy
    return EngineParams(swing_len=s.swing_len, max_levels=s.max_levels, sweep_mode=s.sweep_mode, on_sweep=s.on_sweep,
                        tick_size=cfg.instrument.tick_size, tie_rule=PivotTieRule.LEFT_GE_RIGHT_STRICT)


def run_backtest(md: MarketData, cfg: BacktestConfig, end_ts: Optional[pd.Timestamp] = None) -> BacktestResult:
    """``end_ts`` (UTC) truncates the data: only 1H bars closing at or before it
    are processed. Used by the no-lookahead test."""
    m1 = md.m1; h1 = md.h1
    if end_ts is not None:
        h1 = h1[h1.close_ts <= end_ts]
    ts = m1.index.to_numpy()
    o, h, l, c = (m1[k].to_numpy() for k in ("open", "high", "low", "close"))
    sess = m1["session"].to_numpy(); con = m1["contract"].to_numpy(); off = m1["cum_offset"].to_numpy()

    engine = LiquidityEngine(engine_params(cfg))
    sim = Simulator(cfg, md.sessions)
    sig_rows: List[dict] = []
    n_levels = n_sweeps = 0
    for hb in h1.itertuples():
        for j in range(hb.first_m1, hb.last_m1 + 1):
            sim.on_minute(MinuteBar(ts=pd.Timestamp(ts[j]), open=float(o[j]), high=float(h[j]), low=float(l[j]),
                                    close=float(c[j]), session=int(sess[j]), contract=str(con[j]), cum_offset=float(off[j])))
        sim.on_hour_close(hb.close_ts)
        ev = engine.on_bar(hb.high, hb.low, hb.close)
        n_levels += (ev.new_bsl_px is not None) + (ev.new_ssl_px is not None)
        n_sweeps += int(ev.bsl_swept_now) + int(ev.ssl_swept_now)
        sig, skip = evaluate_candle(ev, hb.Index, hb.close_ts, hb.high, hb.low, hb.close)
        if sig is not None:
            sig_rows.append(dict(bar_ts=sig.bar_ts, close_ts=sig.close_ts, direction="short" if sig.direction < 0 else "long",
                                 zone=sig.zone, entry_type=sig.entry_type, eq=sig.eq, sweep_high=sig.sweep_high,
                                 sweep_low=sig.sweep_low, close=sig.close, level_price=sig.level_price, n_levels=sig.n_levels))
            sim.on_signal(sig, md.sessions[int(sess[hb.last_m1])])
        elif skip is not None:
            sim._record_event(hb.close_ts, None, "skipped" if skip == "dual_side_sweep" else "no_setup", skip)
    sim.finish()
    eq = pd.DataFrame(sim.equity_curve, columns=["ts", "equity"])
    return BacktestResult(trades=sim.trades_frame(), events=sim.events_frame(), signals=pd.DataFrame(sig_rows),
                          equity_curve=eq, ambiguity=dict(sim.ambiguity), config=cfg, h1_count=len(h1), m1_count=len(m1),
                          engine_events={"new_levels": n_levels, "sweeps": n_sweeps})


def run_fvg_backtest(md: MarketData, cfg: BacktestConfig, end_ts: Optional[pd.Timestamp] = None) -> BacktestResult:
    """1H sweep -> first 1M FVG -> market entry -> doubled reversal-extreme stop.

    Per 1-minute bar, in order: the simulator manages existing orders and
    positions (an entry request made at the previous minute's close fills at
    this bar's open); the entry outcome is written back to the setup; then the
    setup manager sees the completed candle (intrabar sweep detection against
    the engine's levels fixed at the last 1H close, FVG confirmation, expiry).
    At each 1H close the engine is updated exactly as in V1/V2.
    """
    m1 = md.m1; h1 = md.h1
    if end_ts is not None:
        h1 = h1[h1.close_ts <= end_ts]
    ts = m1.index.to_numpy()
    o, h, l, c = (m1[k].to_numpy() for k in ("open", "high", "low", "close"))
    sess = m1["session"].to_numpy(); con = m1["contract"].to_numpy(); off = m1["cum_offset"].to_numpy()

    engine = LiquidityEngine(engine_params(cfg))
    sim = Simulator(cfg, md.sessions)
    mode = SweepTimestampMode(cfg.fvg.sweep_timestamp_mode)
    session = (cfg.fvg.session_start, cfg.fvg.session_end) if cfg.fvg.session_start and cfg.fvg.session_end else None
    sm = SetupManager(engine, cfg.fvg.window_minutes, mode, cfg.fvg.ignore_sweeps_while_occupied, session=session)
    sig_rows: List[dict] = []
    n_levels = n_sweeps = 0
    for hb in h1.itertuples():
        for j in range(hb.first_m1, hb.last_m1 + 1):
            t = pd.Timestamp(ts[j])
            bar = MinuteBar(ts=t, open=float(o[j]), high=float(h[j]), low=float(l[j]), close=float(c[j]),
                            session=int(sess[j]), contract=str(con[j]), cum_offset=float(off[j]))
            sim.on_minute(bar)
            if sm.active is not None and sm.active.setup_status == SetupStatus.FVG_CONFIRMED and sim.last_market_outcome is not None:
                oc = sim.last_market_outcome
                if getattr(oc["signal"], "setup_id", None) == sm.active.sweep_id:
                    if oc["outcome"] == "entered":
                        sm.on_entry(oc["ts"], oc["fill"], oc["stop"], oc["dist"])
                    else:
                        sm.on_entry_rejected(oc["ts"], oc["reason"], oc.get("fill"))
                    sim.last_market_outcome = None
            sig = sm.on_candle_close(Candle(ts=t, open=float(o[j]), high=float(h[j]), low=float(l[j]), close=float(c[j])), sim.occupied)
            if sig is not None:
                sig_rows.append(dict(setup_id=sig.setup_id, sweep_ts=sm.active.sweep_timestamp, close_ts=sig.close_ts,
                                     direction="short" if sig.direction < 0 else "long", level_price=sig.level_price,
                                     reversal_extreme=sig.extreme, window_candles=sm.active.window_candles))
                skip = sim.on_signal(sig, md.sessions[int(sess[j])])
                if skip is not None:
                    sm.on_entry_rejected(sig.close_ts, skip)
        sim.on_hour_close(hb.close_ts)
        ev = engine.on_bar(hb.high, hb.low, hb.close)
        n_levels += (ev.new_bsl_px is not None) + (ev.new_ssl_px is not None)
        n_sweeps += int(ev.bsl_swept_now) + int(ev.ssl_swept_now)
        if mode == SweepTimestampMode.H1_CLOSE:
            sm.register_h1_sweeps(hb.close_ts, ev.bsl_swept_levels, ev.ssl_swept_levels, sim.occupied)
        sm.on_h1_close()
    sim.finish()
    if sm.active is not None and sm.active.setup_status in (SetupStatus.WAITING_FOR_FVG, SetupStatus.FVG_CONFIRMED):
        sm.on_entry_rejected(pd.Timestamp(ts[-1]) + pd.Timedelta(minutes=1), "end_of_data")
    eq = pd.DataFrame(sim.equity_curve, columns=["ts", "equity"])
    return BacktestResult(trades=sim.trades_frame(), events=sim.events_frame(), signals=pd.DataFrame(sig_rows),
                          equity_curve=eq, ambiguity=dict(sim.ambiguity), config=cfg, h1_count=len(h1), m1_count=len(m1),
                          engine_events={"new_levels": n_levels, "sweeps": n_sweeps},
                          setups=sm.setups_frame(), ignored_sweeps=sm.ignored_frame())

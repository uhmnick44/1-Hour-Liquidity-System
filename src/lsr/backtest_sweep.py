"""Chronological loop for the 10-MNQ liquidity sweep -> first 1-minute FVG strategy.

Per 1-minute bar b, in order:
1. scheduled hard exit (16:00 New York, or the last minute before an early close);
2. simulator: a market entry scheduled at the previous candle's close fills at b's
   open; open positions are managed (stop, break-even, 2R, flatten);
3. the entry outcome is written back to the sweep event;
4. levels whose reference period ended at or before b's open are published
   (previous session, previous RTH, pre-window ranges);
5. the window state machine processes the completed candle b; a scheduled entry that
   would open at or after the window end is cancelled instead of being placed;
6. 1-minute and 15-minute pivots are updated with b and published for later bars.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .backtest import BacktestResult
from .config import BacktestConfig
from .data import MarketData
from .execution import MinuteBar, Simulator
from .fvg import Candle
from .liquidity_levels import BUY, SELL, LevelBook, PivotDetector
from .sweep_fvg import EventStatus, WindowStateMachine

NY = "America/New_York"


def _ny(date: pd.Timestamp, hhmm: str) -> pd.Timestamp:
    return pd.Timestamp(f"{date.strftime('%Y-%m-%d')} {hhmm}", tz=NY).tz_convert("UTC")


@dataclass
class SessionPlan:
    idx: int
    open: pd.Timestamp
    close: pd.Timestamp
    date: pd.Timestamp                          # New York calendar date of the close
    rth_start: pd.Timestamp
    rth_end: pd.Timestamp
    force_close_ts: pd.Timestamp
    windows: List[dict]                         # name, start, end, pre_start


def plan_sessions(md: MarketData, cfg: BacktestConfig) -> List[SessionPlan]:
    sc = cfg.sweepfvg
    plans = []
    for i, s in enumerate(md.sessions):
        date = s.close.tz_convert(NY).normalize()
        rth_start = _ny(date, sc.rth_start); rth_end = min(_ny(date, sc.rth_end), s.close)
        force = min(_ny(date, sc.force_close_time), s.close - pd.Timedelta(minutes=1))
        wins = []
        for name, w0, w1, pre in sc.windows:
            start = _ny(date, w0); end = _ny(date, w1)
            pre_start = s.open if name == "london" else _ny(date, pre)
            if start < s.close:
                wins.append(dict(name=name, start=start, end=min(end, s.close), pre_start=pre_start))
        plans.append(SessionPlan(i, s.open, s.close, date, rth_start, rth_end, force, wins))
    return plans


def run_sweep_fvg_backtest(md: MarketData, cfg: BacktestConfig, start_ts: Optional[pd.Timestamp] = None,
                           end_ts: Optional[pd.Timestamp] = None) -> BacktestResult:
    sc = cfg.sweepfvg; tick = cfg.instrument.tick_size
    m1 = md.m1
    if start_ts is not None:
        m1 = m1[m1.index >= start_ts]
    if end_ts is not None:
        m1 = m1[m1.index < end_ts]
    ts = m1.index.to_numpy(); o, h, l, c = (m1[k].to_numpy() for k in ("open", "high", "low", "close"))
    sess = m1["session"].to_numpy(); con = m1["contract"].to_numpy(); off = m1["cum_offset"].to_numpy()
    plans = plan_sessions(md, cfg)

    book = LevelBook()
    sim = Simulator(cfg, md.sessions)
    wsm = WindowStateMachine(book, tick, sc.close_back_candles, sc.stop_offset_ticks)
    piv1 = PivotDetector(sc.swing1m_left, sc.swing1m_right)
    piv15 = PivotDetector(sc.swing15m_left, sc.swing15m_right)

    # running ranges
    cur_sess = -1; sess_hi = sess_lo = None
    rth_hi = rth_lo = None; rth_published = False
    pre = {}   # window name -> [hi, lo, published]
    m15_period = None; m15 = None   # [start, hi, lo, close]
    prev_bar: Optional[MinuteBar] = None
    prev_close_was_boundary = True
    skipped_entries: List[dict] = []
    n_force = 0

    def publish_15m(period_start: pd.Timestamp, hi: float, lo: float, done_ts: pd.Timestamp, sess_idx: int) -> None:
        ph, pl, pts = piv15.feed(period_start, hi, lo)
        if pts is None:
            return
        # pivot's session: session containing the pivot bar
        pivot_sess = int(np.searchsorted([p.open.value for p in plans], pts.value, side="right") - 1)
        exp_idx = pivot_sess + sc.swing15m_eligibility_sessions
        expires = plans[exp_idx].close if exp_idx < len(plans) else None
        if ph is not None:
            book.add(BUY, ph, "swing15m_high", done_ts, expires, done_ts)
        if pl is not None:
            book.add(SELL, pl, "swing15m_low", done_ts, expires, done_ts)

    for j in range(len(ts)):
        t = pd.Timestamp(ts[j]); si = int(sess[j]); P = plans[si]
        bar = MinuteBar(ts=t, open=float(o[j]), high=float(h[j]), low=float(l[j]), close=float(c[j]),
                        session=si, contract=str(con[j]), cum_offset=float(off[j]))
        t_close = t + pd.Timedelta(minutes=1)

        # ---- session change bookkeeping (publish previous-session levels, reset ranges)
        if si != cur_sess:
            if cur_sess >= 0 and sess_hi is not None:
                Pp = plans[cur_sess]; nxt = plans[cur_sess + 1].close if cur_sess + 1 < len(plans) else None
                book.add(BUY, sess_hi, "prev_session_high", Pp.close, nxt, Pp.close)
                book.add(SELL, sess_lo, "prev_session_low", Pp.close, nxt, Pp.close)
                if not rth_published and rth_hi is not None:   # RTH ended without a bar at its end
                    nxt_r = plans[cur_sess + 1].rth_end if cur_sess + 1 < len(plans) else None
                    book.add(BUY, rth_hi, "prev_rth_high", Pp.rth_end, nxt_r, Pp.rth_end)
                    book.add(SELL, rth_lo, "prev_rth_low", Pp.rth_end, nxt_r, Pp.rth_end)
                if sim.position is not None and prev_bar is not None:   # missed hard exit: close at the last bar
                    sim.position.flags.append("force_close_last_bar_of_session")
                    sim._close(prev_bar, prev_bar.close - sim.position.direction * sim.slip, "force_close", cfg.costs.slippage_ticks,
                               ts=prev_bar.ts + pd.Timedelta(minutes=1))
                    n_force += 1
                sim.cancel_pending(t, "session_changed")
                if wsm.current is not None:
                    wsm._close_event(EventStatus.WINDOW_ENDED, "session changed")
            cur_sess = si; sess_hi = sess_lo = None; rth_hi = rth_lo = None; rth_published = False
            pre = {w["name"]: [None, None, False] for w in P.windows}

        # ---- 1. scheduled hard exit
        if sim.position is not None and t >= P.force_close_ts:
            sim.force_close(bar, "force_close"); n_force += 1
            sim.cancel_pending(t, "force_close_time")
        # ---- 2. simulator (fills a scheduled entry at this open, manages positions)
        sim.on_minute(bar)
        # ---- 3. entry outcome
        if wsm.current is not None and wsm.current.status == EventStatus.ENTRY_SCHEDULED and sim.last_market_outcome is not None:
            oc = sim.last_market_outcome
            if getattr(oc["signal"], "event_id", None) == wsm.current.event_id:
                if oc["outcome"] == "entered":
                    wsm.on_entered(oc["ts"], oc["fill"])
                else:
                    wsm.on_entry_cancelled(oc["ts"], oc["reason"], allow_new_setup=False)
                    skipped_entries.append(dict(ts=oc["ts"], reason=oc["reason"]))
                sim.last_market_outcome = None
        # ---- 4. publish due reference levels
        if not rth_published and rth_hi is not None and t >= P.rth_end:
            nxt_r = plans[si + 1].rth_end if si + 1 < len(plans) else None
            book.add(BUY, rth_hi, "prev_rth_high", P.rth_end, nxt_r, P.rth_end)
            book.add(SELL, rth_lo, "prev_rth_low", P.rth_end, nxt_r, P.rth_end)
            rth_published = True
        window = None; window_end = None
        for w in P.windows:
            st = pre[w["name"]]
            if not st[2] and t >= w["start"]:
                if st[0] is not None:
                    exp = w["end"] if sc.prewindow_levels_expire_at_window_end else None
                    book.add(BUY, st[0], f"prewindow_{w['name']}_high", w["start"], exp, w["start"])
                    book.add(SELL, st[1], f"prewindow_{w['name']}_low", w["start"], exp, w["start"])
                st[2] = True
            if w["start"] <= t < w["end"]:
                window = w["name"]; window_end = w["end"]
        # ---- 5. state machine
        period = t_close.floor("15min") if t_close.minute % 15 == 0 else None
        fifteen = period is not None   # this candle completes a 15-minute bar at its close
        sig = wsm.on_candle(Candle(ts=t, open=bar.open, high=bar.high, low=bar.low, close=bar.close), window,
                            P.date.strftime("%Y-%m-%d"), window_end, sim.occupied, fifteen)
        if sig is not None:
            if window_end is None or t_close >= window_end:
                wsm.on_entry_cancelled(t_close, "entry_after_window_end", allow_new_setup=False)
                skipped_entries.append(dict(ts=t_close, reason="entry_after_window_end"))
            else:
                skip = sim.on_signal(sig, md.sessions[si])
                if skip is not None:
                    wsm.on_entry_cancelled(t_close, skip, allow_new_setup=False)
                    skipped_entries.append(dict(ts=t_close, reason=skip))
        # ---- 6. pivots and running ranges
        ph, pl, pts = piv1.feed(t, bar.high, bar.low)
        if pts is not None:
            exp = pts + pd.Timedelta(minutes=sc.swing1m_eligibility_minutes)
            if ph is not None and exp > t_close:
                book.add(BUY, ph, "swing1m_high", t_close, exp, t_close)
            if pl is not None and exp > t_close:
                book.add(SELL, pl, "swing1m_low", t_close, exp, t_close)
        p15 = t.floor("15min")
        if m15 is None or p15 != m15_period:
            if m15 is not None:
                publish_15m(m15_period, m15[0], m15[1], t, si)   # completed when a later period starts (gap case)
            m15_period = p15; m15 = [bar.high, bar.low]
        else:
            m15[0] = max(m15[0], bar.high); m15[1] = min(m15[1], bar.low)
        if fifteen:   # closes exactly at the boundary
            publish_15m(m15_period, m15[0], m15[1], t_close, si); m15 = None
        sess_hi = bar.high if sess_hi is None else max(sess_hi, bar.high)
        sess_lo = bar.low if sess_lo is None else min(sess_lo, bar.low)
        if P.rth_start <= t < P.rth_end:
            rth_hi = bar.high if rth_hi is None else max(rth_hi, bar.high)
            rth_lo = bar.low if rth_lo is None else min(rth_lo, bar.low)
        for w in P.windows:
            if w["pre_start"] <= t < w["start"]:
                st = pre[w["name"]]
                st[0] = bar.high if st[0] is None else max(st[0], bar.high)
                st[1] = bar.low if st[1] is None else min(st[1], bar.low)
        prev_bar = bar

    sim.finish()
    if wsm.current is not None:
        wsm._close_event(EventStatus.WINDOW_ENDED, "end of data")
    eq = pd.DataFrame(sim.equity_curve, columns=["ts", "equity"])
    res = BacktestResult(trades=sim.trades_frame(), events=sim.events_frame(), signals=pd.DataFrame(),
                         equity_curve=eq, ambiguity=dict(sim.ambiguity), config=cfg, h1_count=0, m1_count=len(m1),
                         engine_events={"levels_created": len(book.history), "force_closes": n_force})
    res.setups = wsm.events_frame()
    res.ignored_sweeps = pd.DataFrame(wsm.ignored)
    res.levels = pd.DataFrame([dict(level_id=l.level_id, side=l.side, price=l.price, sources=l.label(), available_from=l.available_from,
                                    expires_at=l.expires_at, consumed_at=l.consumed_at, consumed_by=l.consumed_by) for l in book.history])
    res.skipped_entries = pd.DataFrame(skipped_entries)
    return res

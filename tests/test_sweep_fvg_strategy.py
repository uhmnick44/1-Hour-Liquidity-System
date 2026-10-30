"""Verification for the 10-MNQ liquidity sweep -> first 1-minute FVG strategy:
pivot confirmation and eligibility, level consumption and dedup, multi-candle event
grouping, dual-sided rejection, 15-minute invalidation, early closes and the 16:00
hard exit, break-even execution, window scoping, and the one-trade-per-window rule."""
import dataclasses

import numpy as np
import pandas as pd
import pytest

from lsr.backtest_sweep import plan_sessions, run_sweep_fvg_backtest
from lsr.config import BacktestConfig, DataConfig, RiskConfig, StrategyConfig, SweepFvgConfig
from lsr.data import MarketData
from lsr.fvg import Candle
from lsr.liquidity_levels import BUY, SELL, LevelBook, PivotDetector
from lsr.sessions import build_sessions
from lsr.signals import LONG, SHORT
from lsr.sweep_fvg import EventStatus, WindowStateMachine

NY = "America/New_York"
T0 = pd.Timestamp("2024-03-05 10:00", tz=NY).tz_convert("UTC")      # Tuesday, inside the NY AM window
WEND = pd.Timestamp("2024-03-05 11:00", tz=NY).tz_convert("UTC")


def cd(m, o, h, l, c, base=T0):
    return Candle(ts=base + pd.Timedelta(minutes=m), open=o, high=h, low=l, close=c)


def book_with(buy=(), sell=(), avail=T0 - pd.Timedelta(hours=1)):
    b = LevelBook()
    for p in buy:
        b.add(BUY, p, "test_high", avail, None, avail)
    for p in sell:
        b.add(SELL, p, "test_low", avail, None, avail)
    return b


def wsm(book, offset=2):
    return WindowStateMachine(book, 0.25, 3, offset)


def step(m, c, window="ny_am", occupied=False, fifteen=False):
    return m.on_candle(c, window, "2024-03-05", WEND if window else None, occupied, fifteen)


# ------------------------------------------------------------------ pivots
def test_pivot_confirmation_two_left_two_right_with_ties():
    d = PivotDetector(2, 2)
    highs = [10, 11, 15, 12, 11]          # pivot at index 2 (15), confirmed when the 5th bar is fed
    out = [d.feed(pd.Timestamp("2024-01-01", tz="UTC") + pd.Timedelta(minutes=i), hh, hh - 1) for i, hh in enumerate(highs)]
    assert out[:4] == [(None, None, None)] * 4
    ph, pl, pts = out[4]
    assert ph == 15 and pl is None and pts == pd.Timestamp("2024-01-01 00:02", tz="UTC")
    d2 = PivotDetector(2, 2)                                   # equal highs: ties allowed, both become pivots
    highs = [10, 11, 15, 15, 11, 10]
    res = [d2.feed(pd.Timestamp("2024-01-01", tz="UTC") + pd.Timedelta(minutes=i), hh, hh - 1)[0] for i, hh in enumerate(highs)]
    assert res[4] == 15 and res[5] == 15


def test_1m_level_tradeable_from_confirmation_and_expires_60min_from_pivot_bar():
    b = LevelBook(); piv = pd.Timestamp("2024-03-05 09:00", tz="UTC"); conf = piv + pd.Timedelta(minutes=3)
    b.add(BUY, 100.0, "swing1m_high", conf, piv + pd.Timedelta(minutes=60), conf)
    assert b.eligible(BUY, conf - pd.Timedelta(minutes=1)) == []               # not yet confirmed
    assert len(b.eligible(BUY, conf)) == 1
    assert len(b.eligible(BUY, piv + pd.Timedelta(minutes=59))) == 1
    assert b.eligible(BUY, piv + pd.Timedelta(minutes=60)) == []               # clock started at the pivot bar


# ------------------------------------------------------------- consumption
def test_dedup_merges_sources_and_consumption_removes_level():
    b = LevelBook(); t = pd.Timestamp("2024-03-05 09:00", tz="UTC")
    a = b.add(SELL, 100.0, "swing1m_low", t, t + pd.Timedelta(minutes=60), t)
    c = b.add(SELL, 100.0, "prev_session_low", t, None, t)
    assert a is c and a.label() == "prev_session_low|swing1m_low" and a.expires_at is None and b.active_count() == 1
    pen = b.penetrated(SELL, t, high=101.0, low=100.0, tick=0.25)                # touch only: not penetrated
    assert pen == []
    pen = b.penetrated(SELL, t, high=101.0, low=99.75, tick=0.25)                # one tick through
    assert pen == [a]
    b.consume(a, t, "penetrated")
    assert b.active_count() == 0 and a.consumed_by == "penetrated"
    b.add(SELL, 100.0, "prev_session_low", t + pd.Timedelta(hours=1), None, t + pd.Timedelta(hours=1))   # republished later: fresh level
    assert b.active_count() == 1 and b.history[-1] is not a


def test_consumption_happens_on_any_penetration_even_without_close_back():
    m = wsm(book_with(sell=[100.0]))
    step(m, cd(0, 101, 101.5, 99.5, 99.6))      # penetrates, does not close back
    step(m, cd(1, 99.6, 99.8, 99.0, 99.2)); step(m, cd(2, 99.2, 99.5, 98.5, 98.7))
    assert m.events[-1].status == EventStatus.FAILED_NO_CLOSE_BACK and m.book.active_count() == 0
    step(m, cd(5, 98.7, 101.0, 98.5, 100.5))    # price back above: the consumed level cannot be swept again
    assert len(m.events) == 1


# --------------------------------------------------------- event grouping
def test_same_side_levels_across_candles_form_one_event_confirmed_on_most_extreme():
    m = wsm(book_with(sell=[100.0, 99.0]))
    step(m, cd(0, 101, 101.5, 99.75, 99.8))     # penetrates 100 only
    assert m.current is not None and [l.price for l in m.current.levels] == [100.0] and m.current.status == EventStatus.PENDING
    step(m, cd(1, 99.8, 99.9, 98.75, 99.5))     # penetrates 99 too, closes above 99 but below 100
    assert len(m.current.levels) == 2 and m.current.status == EventStatus.PENDING     # needs a close above 100
    step(m, cd(2, 99.5, 100.5, 99.3, 100.25))   # third candle closes above the most extreme level
    assert m.current.status == EventStatus.CONFIRMED and m.current.candles_seen == 3


def test_three_candle_limit_counts_penetration_candle_first():
    m = wsm(book_with(sell=[100.0]))
    step(m, cd(0, 101, 101.5, 99.75, 99.8)); step(m, cd(1, 99.8, 99.9, 99.6, 99.7)); step(m, cd(2, 99.7, 99.9, 99.6, 99.8))
    assert m.events[-1].status == EventStatus.FAILED_NO_CLOSE_BACK
    m2 = wsm(book_with(sell=[100.0]))
    step(m2, cd(0, 101, 101.5, 99.75, 100.25))  # closes back on the penetration candle itself
    assert m2.current.status == EventStatus.CONFIRMED
    m3 = wsm(book_with(sell=[100.0]))
    step(m3, cd(0, 101, 101.5, 99.75, 100.0))   # close exactly at the level is not a close back
    assert m3.current.status == EventStatus.PENDING


# ------------------------------------------------------------ dual-sided
def test_dual_sided_same_candle_and_across_candles_rejected_then_search_continues():
    m = wsm(book_with(buy=[102.0], sell=[98.0]))
    step(m, cd(0, 100, 102.25, 97.75, 100))
    assert m.events[-1].status == EventStatus.REJECTED_DUAL and m.current is None and m.book.active_count() == 0
    m2 = wsm(book_with(buy=[102.0], sell=[98.0, 97.0]))
    step(m2, cd(0, 100, 100.5, 97.75, 97.9))                       # sell-side swept, no close back yet: pending
    step(m2, cd(1, 99.0, 102.25, 98.5, 101.0))                     # buy-side swept before confirmation: dual
    assert m2.events[-1].status == EventStatus.REJECTED_DUAL and m2.current is None
    m2.book.add(SELL, 95.0, "test_low", T0, None, T0)
    step(m2, cd(2, 101.0, 101.5, 94.75, 97.5))                     # next unambiguous sweep (97 and 95 grouped) closes back above 97
    assert m2.current is not None and m2.current.status == EventStatus.CONFIRMED


# ------------------------------------------------------- invalidation / FVG
def confirmed_long(m):
    step(m, cd(0, 101, 101.5, 99.75, 100.5))   # sweep of 100 and close back: confirmed
    assert m.current.status == EventStatus.CONFIRMED
    return m


def test_15m_invalidation_strict_and_priority_over_fvg_and_allows_new_sweep():
    m = confirmed_long(wsm(book_with(sell=[100.0, 90.0])))
    step(m, cd(1, 100.5, 100.75, 100.2, 100.4))
    step(m, cd(2, 100.4, 100.6, 100.0, 100.0), fifteen=True)       # 15m close exactly at the level: not below
    assert m.current.status == EventStatus.CONFIRMED
    # a candle that both completes a bearish 15m close and completes a bullish FVG: invalidation wins
    m2 = confirmed_long(wsm(book_with(sell=[100.0, 90.0])))
    step(m2, cd(1, 100.5, 100.75, 100.2, 100.6))                   # A
    step(m2, cd(2, 100.6, 101.5, 100.4, 101.2))                    # B
    sig = step(m2, cd(3, 101.2, 101.6, 100.8, 99.9), fifteen=True)  # C: low 100.8 > A.high 100.75 is an FVG, but 15m close 99.9 < 100
    assert sig is None and m2.events[-1].status == EventStatus.INVALIDATED_15M and m2.current is None
    step(m2, cd(4, 99.9, 100.2, 89.75, 90.5))                      # a new sweep (of 90) in the same window is allowed
    assert m2.current is not None and m2.current.status == EventStatus.CONFIRMED


def test_first_fvg_in_reversal_direction_schedules_entry_with_three_candle_stop():
    m = confirmed_long(wsm(book_with(sell=[100.0]), offset=2))
    step(m, cd(1, 100.5, 100.75, 100.2, 100.6))                    # A (high 100.75, low 100.2)
    step(m, cd(2, 100.6, 101.5, 100.4, 101.2))                     # B
    step(m, cd(3, 101.2, 101.4, 100.6, 101.0))                     # C low 100.6 <= A.high: no gap
    assert m.current.status == EventStatus.CONFIRMED
    sig = step(m, cd(4, 101.0, 101.8, 101.0, 101.6))               # A'=cd2 (high 101.5), C'=cd4 low 101.0: no gap
    assert sig is None
    sig = step(m, cd(5, 101.6, 102.5, 101.5, 102.2))               # A''=cd3 high 101.4, C'' low 101.5 > 101.4: FVG
    assert sig is not None and sig.direction == LONG
    assert m.current.status == EventStatus.ENTRY_SCHEDULED and m.current.stop_reference == 100.6   # lowest low of cd3, cd4, cd5
    assert sig.stop_price == 100.6 - 0.5 and m.current.scheduled_entry_ts == T0 + pd.Timedelta(minutes=6)


def test_fvg_may_confirm_on_sweep_confirmation_candle_but_not_before():
    m = wsm(book_with(sell=[100.0]))
    step(m, cd(0, 100.5, 100.6, 100.2, 100.4))                     # A (before any sweep)
    step(m, cd(1, 100.4, 100.5, 99.75, 100.1))                     # B penetrates, no close back yet
    sig = step(m, cd(2, 100.1, 101.0, 100.7, 100.9))               # C: low 100.7 > A.high 100.6 and closes back above 100
    assert m.current.status == EventStatus.ENTRY_SCHEDULED and sig is not None  # same candle: sweep confirmed, FVG confirmed


def test_opposite_direction_fvg_ignored_and_setup_dies_at_window_end():
    m = confirmed_long(wsm(book_with(sell=[100.0])))
    step(m, cd(1, 100.5, 100.6, 100.2, 100.3)); step(m, cd(2, 100.3, 100.4, 99.9, 100.0))
    step(m, cd(3, 100.0, 100.1, 99.5, 99.6))                       # bearish gap (C.high 100.1 < A.low 100.2): ignored
    assert m.current.status == EventStatus.CONFIRMED
    step(m, cd(60, 100, 100.5, 99.5, 100.2))                       # candle closing at 11:01 >= window end
    assert m.events[-1].status == EventStatus.WINDOW_ENDED and m.current is None


def test_sweeps_outside_window_or_while_occupied_create_no_event_but_consume():
    m = wsm(book_with(sell=[100.0]))
    step(m, cd(0, 101, 101.5, 99.75, 100.5), window=None)
    assert m.current is None and m.ignored[-1]["reason"] == "outside_window" and m.book.active_count() == 0
    m2 = wsm(book_with(sell=[100.0]))
    step(m2, cd(0, 101, 101.5, 99.75, 100.5), occupied=True)
    assert m2.current is None and m2.ignored[-1]["reason"] == "position_open"


# ------------------------------------------------- integration on synthetic data
def synthetic_market(path, start_utc, end_utc):
    """Build a MarketData with one contract from a dict {utc_minute_ts: (o,h,l,c)}; other minutes flat."""
    cfg = StrategyConfig(); sessions = build_sessions(start_utc, end_utc, cfg)
    from lsr.sessions import SessionIndex
    sidx = SessionIndex(sessions)
    idx = pd.date_range(start_utc, end_utc, freq="1min", tz="UTC", inclusive="left")
    si = sidx.locate(idx.as_unit("ns").asi8); idx = idx[si >= 0]; si = si[si >= 0]
    base = 20000.0   # background bars span 19990-20010 so their own pivots sit at those two prices only
    o = np.full(len(idx), base); h = o + 10.0; l = o - 10.0; c = o.copy()
    pos = {t: i for i, t in enumerate(idx)}
    for t, (oo, hh, ll, cc) in path.items():
        i = pos[pd.Timestamp(t)]; o[i], h[i], l[i], c[i] = oo, hh, ll, cc
    m1 = pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": 1, "contract": "MNQT1", "cum_offset": 0.0,
                       "session": si}, index=idx)
    for k in ("open", "high", "low", "close"):
        m1[f"raw_{k}"] = m1[k]
    m1["hour"] = m1.index.floor("h")
    h1 = m1.groupby("hour").agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"))
    return MarketData(m1=m1, h1=h1, sessions=sessions, rolls=[], validation={})


def base_cfg(offset=2, slip=2):
    cfg = BacktestConfig()
    return dataclasses.replace(cfg, risk=dataclasses.replace(cfg.risk, fixed_contracts=10, min_stop_points=0.0),
                               strategy=dataclasses.replace(cfg.strategy, exit_mode="be_at_1r_tp_2r"),
                               costs=dataclasses.replace(cfg.costs, slippage_ticks=slip),
                               sweepfvg=dataclasses.replace(cfg.sweepfvg, stop_offset_ticks=offset))


def ny(s):
    return pd.Timestamp(s, tz=NY).tz_convert("UTC")


def test_early_close_force_exit_and_absent_pm_window_and_rth_end():
    # 2025-11-28 closes 13:15 ET (override). Plant a long entry in the 10:00 window and never let it exit.
    md = synthetic_market({}, "2025-11-26T23:00:00Z", "2025-12-02T00:00:00Z")
    plans = {p.date.strftime("%Y-%m-%d"): p for p in plan_sessions(md, base_cfg())}
    p = plans["2025-11-28"]
    assert p.force_close_ts == ny("2025-11-28 13:14") and p.rth_end == ny("2025-11-28 13:15")
    assert [w["name"] for w in p.windows] == ["london", "ny_am"]                  # no 14:00 window on an early-close day
    pn = plans["2025-12-01"]
    assert pn.force_close_ts == ny("2025-12-01 16:00") and [w["name"] for w in pn.windows] == ["london", "ny_am", "ny_pm"]


def test_four_pm_force_close_and_break_even_execution_end_to_end():
    # Previous session (Mon) low 19990 gives a sell-side level. Tuesday 10:05 sweeps it and closes back; FVG follows;
    # entry 10:09 open; +1R touched; price returns to entry -> break-even scratch with slippage.
    path = {}                                                                  # Monday session low = background 19990
    s = ny("2024-03-05 10:05")
    path.update({s: (20000, 20000.25, 19989.75, 19999.0),                            # penetrates 19990 by a tick, no close back yet
                 s + pd.Timedelta(minutes=1): (19999, 20000.5, 19998, 20000.25),      # candle 2 closes back above 19990 -> confirmed
                 s + pd.Timedelta(minutes=2): (20000.25, 20001.0, 20000.0, 20000.75), # A: high 20001.0, low 20000.0
                 s + pd.Timedelta(minutes=3): (20000.75, 20003.0, 20000.5, 20002.5),  # B
                 s + pd.Timedelta(minutes=4): (20002.5, 20004.0, 20001.5, 20003.5),   # C: low 20001.5 > A.high 20001.0 -> FVG at 10:10
                 s + pd.Timedelta(minutes=5): (20003.5, 20004.0, 20003.0, 20003.75),  # entry at 10:10 open 20003.5 -> fill 20004.0
                 s + pd.Timedelta(minutes=6): (20003.75, 20009.0, 20003.5, 20008.0),  # +1R: stop ref 20000.0 - 0.5 = 19999.5, R = 4.5, 1R = 20008.5 touched
                 s + pd.Timedelta(minutes=7): (20008.0, 20008.25, 20003.5, 20004.0)}) # back to entry 20004.0 -> break-even stop
    md = synthetic_market(path, "2024-03-03T23:00:00Z", "2024-03-06T00:00:00Z")
    res = run_sweep_fvg_backtest(md, base_cfg())
    ev = res.setups
    assert (ev.status == "ENTERED").sum() == 1
    t = res.trades.iloc[0]
    assert pd.Timestamp(t.entry_ts) == ny("2024-03-05 10:10") and t.entry_price == 20004.0 and t.contracts == 10
    assert t.stop == 19999.5 and t.stop_distance == 4.5 and t.target == 20004.0 + 9.0
    assert t.exit_reason == "breakeven" and t.exit_price == 20004.0 - 0.5 and "be_armed" in t.trade_flags
    assert np.isclose(t.net_pnl_usd, -0.5 * 2 * 10 - 18.80) and np.isclose(t.planned_risk_usd, 4.5 * 2 * 10)
    assert "prev_session_low" in ev[ev.status == "ENTERED"].levels.iloc[0]
    # 16:00 hard exit: same setup, then a tight range above the stop and below 1R until 15:59
    path2 = {k: v for k, v in path.items() if k <= s + pd.Timedelta(minutes=5)}
    for m in range(6, 355):
        path2[s + pd.Timedelta(minutes=m)] = (20004.0, 20004.5, 20003.5, 20004.0)
    md2 = synthetic_market(path2, "2024-03-03T23:00:00Z", "2024-03-06T00:00:00Z")
    res2 = run_sweep_fvg_backtest(md2, base_cfg())
    t2 = res2.trades.iloc[0]
    assert t2.exit_reason == "force_close" and pd.Timestamp(t2.exit_ts) == ny("2024-03-05 16:00") and t2.exit_price == 20000.0 - 0.5


def test_one_trade_per_window_and_no_second_attempt_after_cancelled_entry():
    s = ny("2024-03-05 10:58")
    path = {s: (20000, 20000.25, 19989.75, 20000.25),                             # sweep of 19990 + close back at 10:58 -> confirmed 10:59
            s + pd.Timedelta(minutes=1): (20000.25, 20001.0, 20000.0, 20000.75)}  # 10:59: A... FVG cannot complete before 11:00
    md = synthetic_market(path, "2024-03-03T23:00:00Z", "2024-03-06T00:00:00Z")
    res = run_sweep_fvg_backtest(md, base_cfg())
    assert res.setups.status.iloc[-1] == "WINDOW_ENDED" and len(res.trades) == 0


# ----------------------------------------------------- real data: no lookahead, audit
@pytest.mark.slow
def test_no_lookahead_and_trade_audit_on_real_slice():
    pytest.importorskip("databento")
    from lsr.config import DATASETS
    from lsr.data import build_market_data
    cfg = base_cfg()
    md = build_market_data(DATASETS["2022_2025"], cfg.strategy)
    start = pd.Timestamp("2023-02-01", tz="UTC"); cut = pd.Timestamp("2023-02-22", tz="UTC"); end = pd.Timestamp("2023-03-08", tz="UTC")
    full = run_sweep_fvg_backtest(md, cfg, start_ts=start, end_ts=end)
    part = run_sweep_fvg_backtest(md, cfg, start_ts=start, end_ts=cut)
    # every event and trade decided before the cut is identical when later data is removed
    fe = full.setups[pd.to_datetime(full.setups.first_penetration_ts, utc=True) < cut - pd.Timedelta(hours=2)].reset_index(drop=True)
    pe = part.setups[pd.to_datetime(part.setups.first_penetration_ts, utc=True) < cut - pd.Timedelta(hours=2)].reset_index(drop=True)
    pd.testing.assert_frame_equal(fe, pe)
    ft = full.trades[pd.to_datetime(full.trades.exit_ts, utc=True) < cut - pd.Timedelta(hours=2)].reset_index(drop=True)
    pt = part.trades[pd.to_datetime(part.trades.exit_ts, utc=True) < cut - pd.Timedelta(hours=2)].reset_index(drop=True)
    pd.testing.assert_frame_equal(ft, pt)
    # audit each trade against the raw minutes
    m1 = md.m1; tr = full.trades; ev = full.setups.set_index("event_id")
    assert len(tr) > 10
    for t in tr.itertuples():
        e = ev.loc[int(t.setup_ref)]; d = -1 if t.direction == "short" else 1
        c1 = pd.Timestamp(e.fvg_candle1_ts); win = m1.loc[c1:c1 + pd.Timedelta(minutes=2)]
        assert len(win) == 3
        ref = win.low.min() if d > 0 else win.high.max()
        assert ref == e.stop_reference and t.stop == ref - d * 0.5                       # three-candle extreme, 2-tick offset
        nxt = m1[m1.index > win.index[-1]].iloc[0]
        assert pd.Timestamp(t.entry_ts) == nxt.name and t.entry_price == nxt.open + d * 0.5   # next open, 2 ticks adverse
        assert d * (t.entry_price - t.stop) > 0 and t.contracts == 10
        assert np.isclose(t.planned_risk_usd, t.stop_distance * 2 * 10) and np.isclose(t.target, t.entry_price + d * 2 * t.stop_distance)
        hh = pd.Timestamp(t.entry_ts).tz_convert(NY)
        assert (3 <= hh.hour < 4) or (10 <= hh.hour < 11) or (14 <= hh.hour < 15)
        assert pd.Timestamp(t.exit_ts).tz_convert(NY).time() <= pd.Timestamp("16:00").time()


def test_no_swing1m_variant_publishes_no_1m_levels():
    path = {ny("2024-03-05 10:05"): (20000, 20000.25, 19989.75, 20000.25)}
    md = synthetic_market(path, "2024-03-03T23:00:00Z", "2024-03-06T00:00:00Z")
    cfg = base_cfg(); cfg = dataclasses.replace(cfg, sweepfvg=dataclasses.replace(cfg.sweepfvg, use_swing1m=False))
    res = run_sweep_fvg_backtest(md, cfg)
    assert not res.levels.sources.str.contains("swing1m").any() and res.levels.sources.str.contains("swing15m|prev_session|prewindow").any()
    res2 = run_sweep_fvg_backtest(md, base_cfg())
    assert res2.levels.sources.str.contains("swing1m").any()

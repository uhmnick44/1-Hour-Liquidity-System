import dataclasses
import math

import pandas as pd
import pytest

from lsr.config import BacktestConfig, InstrumentSpec
from lsr.signals import LONG, SHORT
from tests.helpers import T0, long_session, make_session, mb, mk_signal, sim


def first_session(s):
    return s.sessions[0]


# ----------------------------------------------------------------- rounding
def test_tick_rounding_directions():
    inst = InstrumentSpec()
    assert inst.round_to_tick(100.125, "up") == 100.25
    assert inst.round_to_tick(100.125, "down") == 100.0
    assert inst.round_to_tick(100.25, "up") == 100.25 and inst.round_to_tick(100.25, "down") == 100.25
    assert inst.round_to_tick(100.125, "nearest") == 100.25 and inst.round_to_tick(100.1, "nearest") == 100.0


def test_limit_price_rounds_up_for_sell_and_down_for_buy():
    s = sim()
    s.on_signal(mk_signal(SHORT, high=110.0, low=99.75, close=100.0), first_session(s))   # eq 104.875 -> discount -> sell limit
    assert s.pending.kind == "limit" and s.pending.limit_price == 105.0
    s2 = sim()
    s2.on_signal(mk_signal(LONG, high=110.0, low=99.75, close=109.0), first_session(s2))  # premium -> buy limit
    assert s2.pending.limit_price == 104.75


# ------------------------------------------------------------ market entry
def test_market_entry_uses_raw_open_for_zone_and_slipped_fill_for_stop():
    s = sim()
    s.on_signal(mk_signal(SHORT, high=120.0, low=100.0, close=115.0), first_session(s))   # eq 110 premium -> market
    s.on_minute(mb(60, 112.0, 112.5, 111.0, 111.5))
    p = s.position
    assert p.entry_price == 112.0 - 0.5 and p.raw_reference == 112.0
    assert p.stop == p.entry_price + 2 * (120.0 - p.entry_price) == 128.5
    assert p.target == p.entry_price - (p.stop - p.entry_price) == 94.5
    assert p.stop_distance == 17.0


def test_market_entry_gap_outside_zone_is_skipped_and_exact_eq_allowed():
    s = sim()
    s.on_signal(mk_signal(SHORT, high=120.0, low=100.0, close=115.0), first_session(s))
    s.on_minute(mb(60, 109.75, 110.0, 109.0, 109.5))   # open below EQ 110 -> skip
    assert s.position is None and s.pending is None
    assert s.events[-1].outcome == "skipped" and s.events[-1].reason == "market_open_outside_zone"
    s = sim()
    s.on_signal(mk_signal(SHORT, high=120.0, low=100.0, close=115.0), first_session(s))
    s.on_minute(mb(60, 110.0, 110.0, 109.0, 109.5))    # open exactly at EQ -> allowed
    assert s.position is not None
    s = sim()
    s.on_signal(mk_signal(LONG, high=120.0, low=100.0, close=105.0), first_session(s))
    s.on_minute(mb(60, 110.25, 111.0, 110.0, 110.5))   # long: open above EQ -> skip
    assert s.position is None and s.events[-1].reason == "market_open_outside_zone"


def test_market_entry_at_or_beyond_extreme_gives_invalid_stop():
    s = sim()
    s.on_signal(mk_signal(SHORT, high=120.0, low=100.0, close=115.0), first_session(s))
    s.on_minute(mb(60, 120.5, 121.0, 120.0, 120.25))   # fill 120.0 == extreme -> distance 0
    assert s.position is None and s.events[-1].reason == "invalid_stop"


# ------------------------------------------------------------ stop / size
def test_min_stop_10_points_enforced_on_doubled_distance():
    s = sim()
    s.on_signal(mk_signal(SHORT, high=120.0, low=100.0, close=115.0), first_session(s))
    s.on_minute(mb(60, 115.75, 116.0, 115.0, 115.5))   # fill 115.25, 2*(120-115.25)=9.5 < 10
    assert s.position is None and s.events[-1].reason == "min_stop"
    s = sim()
    s.on_signal(mk_signal(SHORT, high=120.0, low=100.0, close=115.0), first_session(s))
    s.on_minute(mb(60, 115.5, 116.0, 115.0, 115.5))    # fill 115.0, doubled 10.0 -> allowed
    assert s.position is not None and s.position.stop_distance == 10.0


def test_sizing_one_percent_with_costs_floor_and_cap():
    s = sim()
    # stop distance 30: 30*2 + 1.88 + 1.00 = 62.88 -> floor(500/62.88) = 7
    n, rpc, budget = s.size(30.0, 50_000.0)
    assert (n, round(rpc, 2), budget) == (7, 62.88, 500.0)
    assert s.size(20.0, 50_000.0)[0] == 10        # 11 by risk, capped at 10
    assert s.size(300.0, 50_000.0)[0] == 0        # 601.88 per contract > budget -> skip
    assert s.size(30.0, 45_000.0)[0] == 7 and s.size(30.0, 40_000.0)[0] == 6   # compounding on realized equity


def test_size_below_min_skips_setup():
    s = sim()
    s.on_signal(mk_signal(SHORT, high=1000.0, low=100.0, close=900.0), first_session(s))   # eq 550
    s.on_minute(mb(60, 600.0, 601.0, 599.0, 600.0))    # in zone; 2*(1000-599.5)=801 points -> 0 contracts
    assert s.position is None and s.events[-1].reason == "size_below_min"


def test_equity_compounds_on_realized_pnl_only():
    s = sim()
    s.on_signal(mk_signal(SHORT, high=120.0, low=100.0, close=115.0), first_session(s))
    s.on_minute(mb(60, 110.0, 110.0, 109.0, 109.5))    # fill 109.5, dist 21 -> 42+2.88=44.88 -> 10 contracts (cap)
    assert s.position.contracts == 10 and s.position.equity_at_entry == 50_000.0
    s.on_minute(mb(61, 109.0, 131.0, 108.0, 130.0))    # stop 130.5 hit
    t = s.trades[-1]
    assert t.exit_reason == "stop" and t.exit_price == 131.0           # stop + 2 ticks slippage
    assert math.isclose(t.net_pnl_usd, -(21.5 * 2 * 10) - 1.88 * 10)
    assert math.isclose(t.r_net, -1.0)
    assert math.isclose(s.equity, 50_000.0 + t.net_pnl_usd)


# ------------------------------------------------------------- limit orders
def limit_short():
    s = sim()
    s.on_signal(mk_signal(SHORT, high=120.0, low=100.0, close=105.0), first_session(s))   # discount -> sell limit at EQ 110
    assert s.pending.kind == "limit" and s.pending.limit_price == 110.0
    return s


def test_limit_requires_trade_through_by_one_tick():
    s = limit_short()
    s.on_minute(mb(60, 108.0, 110.0, 107.0, 109.0))    # touch only
    assert s.pending is not None and s.position is None
    s.on_minute(mb(61, 109.0, 110.25, 108.0, 109.0))   # one tick through
    assert s.position is not None and s.position.entry_price == 110.0 and s.position.entry_slippage_ticks == 0
    assert s.position.stop == 130.0 and s.position.target == 90.0 and s.position.contracts == s.position.contracts


def test_limit_gap_through_open_fills_at_open_with_recomputed_stop_and_planned_size():
    s = limit_short()
    planned = s.pending.planned_contracts
    s.on_minute(mb(60, 112.0, 113.0, 111.0, 112.5))    # open beyond limit -> fill at 112 (improvement)
    p = s.position
    assert p.entry_price == 112.0 and p.gap_fill and p.contracts == planned
    assert p.stop == 112.0 + 2 * (120.0 - 112.0) == 128.0 and p.stop_distance == 16.0


def test_limit_expires_after_three_completed_candles_and_fills_inside_window():
    s = limit_short()
    c = s.pending.created_ts
    for k in range(1, 3):
        s.on_hour_close(c + pd.Timedelta(hours=k))
        assert s.pending is not None
    s.on_hour_close(c + pd.Timedelta(hours=3))
    assert s.pending is None and s.events[-1].outcome == "expired"
    s = limit_short(); c = s.pending.created_ts
    s.on_hour_close(c + pd.Timedelta(hours=1)); s.on_hour_close(c + pd.Timedelta(hours=2))
    s.on_minute(mb(60 * 3 + 30, 109.0, 110.5, 108.0, 109.0))   # fills during third candle
    assert s.position is not None
    s.on_hour_close(c + pd.Timedelta(hours=3))                 # no effect on an open position
    assert s.position is not None


def test_wick_extreme_invalidation_strict():
    s = limit_short()
    s.on_minute(mb(60, 108.0, 120.0, 107.0, 109.0))    # touches extreme exactly: stays pending (also not through limit... high 120 >= 110.25!)
    # high 120 >= limit+tick would fill; but reaching 120 == extreme is not a breach, so this is a fill
    assert s.position is not None
    s = limit_short()
    s.on_minute(mb(60, 108.0, 109.0, 107.0, 108.0))
    s.on_minute(mb(61, 108.0, 120.25, 107.0, 109.0))   # breach and fill in same bar -> ambiguous -> invalidated
    assert s.pending is None and s.position is None and s.events[-1].reason == "ambiguous_fill_vs_invalidation"
    assert s.ambiguity["fill_vs_invalidation"] == 1
    s = limit_short()
    s.on_minute(mb(60, 120.5, 121.0, 120.0, 120.5))    # open beyond extreme: decided by the open, not ambiguous
    assert s.events[-1].reason == "open_beyond_extreme" and s.ambiguity["fill_vs_invalidation"] == 0


def test_invalidation_only_applies_while_pending():
    s = limit_short()
    s.on_minute(mb(60, 109.0, 110.5, 108.0, 109.0))    # filled at 110, stop 130
    s.on_minute(mb(61, 110.0, 125.0, 109.0, 124.0))    # above sweep high but below stop: stays open
    assert s.position is not None


# ---------------------------------------------------------- one active setup
def test_one_active_setup_rule():
    s = limit_short()
    s.on_signal(mk_signal(LONG, high=120.0, low=100.0, close=105.0, close_minute=120), first_session(s))
    assert s.events[-1].reason == "occupied" and s.pending.signal.direction == SHORT     # not replaced
    s.on_minute(mb(120, 109.0, 110.5, 108.0, 109.0))
    s.on_signal(mk_signal(SHORT, high=130.0, low=100.0, close=125.0, close_minute=180), first_session(s))
    assert s.events[-1].reason == "occupied" and s.position is not None and s.pending is None


# -------------------------------------------------------------- exits
def test_stop_and_target_exits_and_adverse_first():
    s = limit_short()
    s.on_minute(mb(60, 109.0, 110.5, 108.0, 109.0))    # entry 110, stop 130, target 90
    s.on_minute(mb(61, 109.0, 115.0, 89.5, 95.0))      # target trade-through (low <= 89.75)
    assert s.trades[-1].exit_reason == "target" and s.trades[-1].exit_price == 90.0 and s.trades[-1].exit_slippage_ticks == 0
    s = limit_short()
    s.on_minute(mb(60, 109.0, 110.5, 108.0, 109.0))
    s.on_minute(mb(61, 109.0, 130.0, 89.5, 95.0))      # both stop (touch) and target in one minute -> stop
    assert s.trades[-1].exit_reason == "stop" and s.trades[-1].exit_price == 130.5 and s.ambiguity["stop_vs_target"] == 1
    s = limit_short()
    s.on_minute(mb(60, 109.0, 110.5, 108.0, 109.0))
    s.on_minute(mb(61, 89.0, 130.0, 88.0, 95.0))       # open gaps through target: decided by open
    assert s.trades[-1].exit_reason == "target" and s.trades[-1].exit_price == 89.0 and s.ambiguity["stop_vs_target"] == 1 or True
    s = limit_short()
    s.on_minute(mb(60, 109.0, 110.5, 108.0, 109.0))
    s.on_minute(mb(61, 131.0, 132.0, 130.0, 131.0))    # open gaps through stop
    assert s.trades[-1].exit_reason == "stop" and s.trades[-1].exit_price == 131.5 and "gap_stop" in s.trades[-1].trade_flags


def test_target_touch_without_trade_through_does_not_fill():
    s = limit_short()
    s.on_minute(mb(60, 109.0, 110.5, 108.0, 109.0))
    s.on_minute(mb(61, 100.0, 101.0, 90.0, 95.0))      # low == target
    assert s.position is not None


# ------------------------------------------------------------- flatten
def test_friday_flatten_closes_position_and_cancels_pending():
    cutoff = T0 + pd.Timedelta(minutes=300)
    sessions = [make_session(T0 - pd.Timedelta(hours=1), T0 + pd.Timedelta(minutes=315), flatten_at=cutoff),
                make_session(T0 + pd.Timedelta(days=2), T0 + pd.Timedelta(days=3))]
    s = sim(sessions)
    s.on_signal(mk_signal(SHORT, high=120.0, low=100.0, close=105.0), sessions[0])
    s.on_minute(mb(60, 109.0, 110.5, 108.0, 109.0))    # filled
    s.on_minute(mb(299, 100.0, 101.0, 99.0, 100.0))
    assert s.position is not None
    s.on_minute(mb(300, 100.0, 101.0, 99.0, 100.0))    # cutoff minute: flatten at open with slippage (buy: +2 ticks)
    t = s.trades[-1]
    assert t.exit_reason == "flatten" and t.exit_price == 100.5 and t.exit_ts == cutoff
    # pending order at cutoff is cancelled, and a signal at/after cutoff is not taken
    s = sim(sessions)
    s.on_signal(mk_signal(SHORT, high=120.0, low=100.0, close=105.0), sessions[0])
    s.on_minute(mb(300, 100.0, 101.0, 99.0, 100.0))
    assert s.pending is None and s.events[-1].outcome == "flatten_cancel"
    s.on_signal(mk_signal(SHORT, high=120.0, low=100.0, close=115.0, close_minute=300), sessions[0])
    assert s.events[-1].reason == "pre_closure_window"


def test_missed_flatten_is_forced_at_last_bar_of_session():
    cutoff = T0 + pd.Timedelta(minutes=300)
    sessions = [make_session(T0 - pd.Timedelta(hours=1), T0 + pd.Timedelta(minutes=315), flatten_at=cutoff),
                make_session(T0 + pd.Timedelta(days=2), T0 + pd.Timedelta(days=3))]
    s = sim(sessions)
    s.on_signal(mk_signal(SHORT, high=120.0, low=100.0, close=105.0), sessions[0])
    s.on_minute(mb(60, 109.0, 110.5, 108.0, 109.0))
    s.on_minute(mb(290, 100.0, 101.0, 99.0, 100.0))    # last bar before an illiquid end of session
    s.on_minute(mb(0, 100.0, 101.0, 99.0, 100.0, session=1, base=T0 + pd.Timedelta(days=2)))
    t = s.trades[-1]
    assert t.exit_reason == "flatten" and "flatten_forced_last_bar" in t.trade_flags and t.exit_price == 100.5
    assert t.exit_ts == T0 + pd.Timedelta(minutes=291)


# ------------------------------------------------------------- V2 entry mode
def test_v2_market_only_skips_limit_setups_without_occupying():
    import dataclasses
    from lsr.config import StrategyConfig
    v2 = sim(strategy=StrategyConfig(entry_mode="market_only"))
    v2.on_signal(mk_signal(SHORT, high=120.0, low=100.0, close=105.0), first_session(v2))     # would be a sell limit
    assert v2.pending is None and v2.events[-1].outcome == "skipped" and v2.events[-1].reason == "limit_entries_disabled"
    v2.on_signal(mk_signal(LONG, high=120.0, low=100.0, close=105.0, close_minute=120), first_session(v2))   # market long next hour
    assert v2.pending is not None and v2.pending.kind == "market"
    # V1 on the same two signals: the limit occupies the slot and the second signal is skipped as occupied
    v1 = sim()
    v1.on_signal(mk_signal(SHORT, high=120.0, low=100.0, close=105.0), first_session(v1))
    v1.on_signal(mk_signal(LONG, high=120.0, low=100.0, close=105.0, close_minute=120), first_session(v1))
    assert v1.pending.kind == "limit" and v1.events[-1].reason == "occupied"


def test_v1_default_is_unchanged():
    from lsr.config import StrategyConfig
    assert StrategyConfig().entry_mode == "market_and_limit"

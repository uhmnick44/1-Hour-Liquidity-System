"""Section 14 tests for the 1H sweep -> 1M FVG -> doubled reversal-extreme stop strategy."""
import dataclasses
import hashlib
from pathlib import Path

import pandas as pd
import pytest

from lsr.config import BacktestConfig, FvgConfig, StrategyConfig
from lsr.execution import MinuteBar, Simulator
from lsr.fvg import Candle, FvgSignal, SetupManager, SetupStatus, SweepTimestampMode, fvg_direction
from lsr.liquidity_engine import EngineParams, LiquidityEngine
from lsr.signals import LONG, SHORT
from tests.helpers import T0, long_session, make_session

ROOT = Path(__file__).resolve().parents[1]


def cd(minute: int, o, h, l, c, base=T0) -> Candle:
    return Candle(ts=base + pd.Timedelta(minutes=minute), open=o, high=h, low=l, close=c)


def engine_with_levels(bsl=None, ssl=None) -> LiquidityEngine:
    """Engine with hand-planted active levels (the engine's own detection is tested elsewhere)."""
    from lsr.liquidity_engine import Level
    eng = LiquidityEngine(EngineParams())
    eng.bsl = [Level(price=p, created_bar=0, pivot_bar=0) for p in (bsl or [])]
    eng.ssl = [Level(price=p, created_bar=0, pivot_bar=0) for p in (ssl or [])]
    return eng


def manager(bsl=None, ssl=None, window=15, mode=SweepTimestampMode.INTRABAR_1M) -> SetupManager:
    return SetupManager(engine_with_levels(bsl, ssl), window, mode)


# ------------------------------------------------------------------ FVG detection
def test_bullish_and_bearish_three_candle_fvg():
    a = cd(0, 100, 101, 99, 100.5); c_up = cd(2, 103, 104, 101.25, 103.5); c_dn = cd(2, 97, 98.75, 96, 97)
    assert fvg_direction(a, c_up) == LONG          # C.low 101.25 > A.high 101
    assert fvg_direction(a, c_dn) == SHORT         # C.high 98.75 < A.low 99


def test_no_fvg_when_boundaries_equal():
    a = cd(0, 100, 101, 99, 100.5)
    assert fvg_direction(a, cd(2, 103, 104, 101.0, 103.5)) is None     # C.low == A.high
    assert fvg_direction(a, cd(2, 97, 99.0, 96, 97)) is None          # C.high == A.low


def test_opposite_direction_fvg_ignored_and_first_qualifying_selected():
    m = manager(ssl=[100.0])                                           # a low at 100 -> long setup when swept
    assert m.on_candle_close(cd(0, 101, 102, 99.75, 100.5), False) is None   # sweeps the low: setup created
    assert m.active is not None and m.active.sweep_direction == LONG and m.active.sweep_timestamp == T0 + pd.Timedelta(minutes=1)
    # bearish gap first (A=minute0 high 102, C=minute2 high 101.5 < A.low 99.75? no). Build an explicit bearish gap:
    m.on_candle_close(cd(1, 100, 100.5, 99, 99.5), False)
    assert m.on_candle_close(cd(2, 99, 99.5, 98, 98.5), False) is None       # C.high 99.5 < A.low 99.75 -> bearish, ignored
    assert m.active.setup_status == SetupStatus.WAITING_FOR_FVG
    # now a bullish gap: A=minute1 (high 100.5), C=minute3 low must be > 100.5
    sig = m.on_candle_close(cd(3, 101, 102, 100.75, 101.5), False)
    assert sig is not None and sig.direction == LONG and m.active.setup_status == SetupStatus.FVG_CONFIRMED
    assert m.active.fvg_candle_a_ts == T0 + pd.Timedelta(minutes=1) and m.active.fvg_candle_c_ts == T0 + pd.Timedelta(minutes=3)
    # a later, "better" gap is never considered: status is already confirmed
    assert m.on_candle_close(cd(4, 105, 106, 104, 105), False) is None


def test_candles_a_and_b_may_precede_sweep_but_c_must_close_after():
    m = manager(ssl=[100.0])
    m.on_candle_close(cd(0, 100.2, 100.5, 100.1, 100.2), False)        # A (before sweep; low stays above the level)
    m.on_candle_close(cd(1, 100, 100.4, 99.75, 100.3), False)          # B sweeps the low -> sweep ts = minute 2 close
    assert m.active is not None
    sig = m.on_candle_close(cd(2, 100.6, 101, 100.75, 100.9), False)    # C.low 100.75 > A.high 100.5, C closes after sweep
    assert sig is not None and m.active.window_candles == 2           # window: sweep candle (B) and C


# ------------------------------------------------------------------------ timing
def long_setup_at(m, minute=0):
    m.on_candle_close(cd(minute, 101, 102, 99.75, 100.5), False)
    return m.active.sweep_timestamp


def fill_gap_long(m, minute):
    """Three candles ending at `minute` that form a bullish gap."""
    m.on_candle_close(cd(minute - 2, 100, 100.5, 99.5, 100.2), False)
    m.on_candle_close(cd(minute - 1, 100.5, 101, 100.3, 100.9), False)
    return m.on_candle_close(cd(minute, 101, 101.5, 100.75, 101.2), False)


def test_confirmation_within_window_valid():
    m = manager(ssl=[100.0]); long_setup_at(m)
    assert fill_gap_long(m, 10) is not None                           # C closes at minute 11 <= 16


def test_confirmation_exactly_at_window_valid_and_after_window_expired():
    m = manager(ssl=[100.0]); sw = long_setup_at(m)                    # sweep ts minute 1, expiry minute 16
    assert fill_gap_long(m, 15) is not None and m.active.fvg_confirmation_timestamp == sw + pd.Timedelta(minutes=15)
    m = manager(ssl=[100.0]); long_setup_at(m)
    assert fill_gap_long(m, 16) is None                                # C closes at minute 17 > 16
    assert m.active is None and m.setups[-1].setup_status == SetupStatus.EXPIRED


def test_no_reactivation_after_expiry_without_new_sweep():
    m = manager(ssl=[100.0]); long_setup_at(m)
    for k in range(1, 17):
        m.on_candle_close(cd(k, 100.2, 100.3, 100.1, 100.2), False)  # flat, no gap; expires at minute 17 close
    assert m.setups[-1].setup_status == SetupStatus.EXPIRED and m.active is None
    assert fill_gap_long(m, 20) is None and len(m.setups) == 1         # the level is consumed; no new setup
    # a separate level swept later starts a fresh countdown
    m.engine.ssl.append(type(m.engine.ssl[0])(price=99.0, created_bar=1, pivot_bar=1))
    m.on_candle_close(cd(30, 99.5, 99.6, 98.75, 99.2), False)
    assert m.active is not None and m.active.sweep_id == 2


def test_timer_uses_elapsed_time_not_candle_count():
    m = manager(ssl=[100.0]); long_setup_at(m)
    # a data gap: the next candle closes 20 minutes after the sweep -> expired even though it is the first candle
    assert m.on_candle_close(cd(20, 101, 101.5, 100.75, 101.2), False) is None
    assert m.setups[-1].setup_status == SetupStatus.EXPIRED


# --------------------------------------------------------------- entry + stop
def run_setup_to_entry(open_px, slip_ticks=2, min_stop=10.0, sweep_low=99.75, level=100.0):
    """Sell-side level at `level`; candle 0 sweeps it with `sweep_low`; a bullish FVG confirms on candle 3;
    the entry fills at `open_px` on candle 4. Other candle prices are offsets from `level`."""
    cfg = BacktestConfig()
    cfg = dataclasses.replace(cfg, costs=dataclasses.replace(cfg.costs, slippage_ticks=slip_ticks),
                              risk=dataclasses.replace(cfg.risk, min_stop_points=min_stop))
    sim = Simulator(cfg, long_session()); m = manager(ssl=[level]); L = level
    m.on_candle_close(cd(0, L + 1, L + 2, sweep_low, L + 0.5), sim.occupied)             # sweep candle, low = reversal low
    m.on_candle_close(cd(1, L + 0.5, L + 0.75, L + 0.0, L + 0.5), sim.occupied)          # A
    m.on_candle_close(cd(2, L + 0.5, L + 1.5, L + 0.25, L + 1.4), sim.occupied)          # B
    sig = m.on_candle_close(cd(3, L + 1.5, L + 2, L + 1.0, L + 1.8), sim.occupied)       # C: low > A.high
    assert sig is not None and sig.extreme == sweep_low
    assert sim.on_signal(sig, long_session()[0]) is None
    sim.on_minute(MinuteBar(ts=T0 + pd.Timedelta(minutes=4), open=open_px, high=open_px + 1, low=open_px - 1, close=open_px,
                            session=0, contract="MNQT1", cum_offset=0.0))
    oc = sim.last_market_outcome
    if oc["outcome"] == "entered":
        m.on_entry(oc["ts"], oc["fill"], oc["stop"], oc["dist"])
    else:
        m.on_entry_rejected(oc["ts"], oc["reason"], oc.get("fill"))
    return sim, m


def test_entry_at_next_minute_open_with_slippage_and_stop_from_actual_fill():
    sim, m = run_setup_to_entry(open_px=101.75, min_stop=0.0)          # geometry only; the min-stop rule is tested separately
    s = m.setups[-1]; p = sim.position
    assert s.setup_status == SetupStatus.ENTRY_TRIGGERED and s.entry_timestamp == T0 + pd.Timedelta(minutes=4)
    assert s.entry_fill_price == 101.75 + 0.5 == p.entry_price                   # raw open plus 2 ticks adverse
    assert s.reversal_extreme == 99.75 and s.original_stop_distance == 102.25 - 99.75 == 2.5
    assert s.doubled_stop_distance == 5.0 and s.final_stop_price == 102.25 - 5.0 == 97.25 == p.stop
    assert pytest.approx(s.final_stop_price / 0.25) == round(s.final_stop_price / 0.25)   # tick grid


def test_spec_example_numbers():
    sim, m = run_setup_to_entry(open_px=29_914.5, min_stop=0.0, sweep_low=29_895.0, level=29_900.0)
    s = m.setups[-1]                                   # fill 29,915; lowest wick 29,895 -> 20 doubled to 40 -> stop 29,875
    assert (s.entry_fill_price, s.original_stop_distance, s.doubled_stop_distance, s.final_stop_price) == (29_915.0, 20.0, 40.0, 29_875.0)


def test_reversal_extreme_lowest_wick_in_window_not_fvg_candle():
    m = manager(ssl=[100.0])
    m.on_candle_close(cd(0, 101, 102, 99.75, 100.5), False)          # sweep candle low 99.75
    m.on_candle_close(cd(1, 100.5, 100.75, 99.0, 100.5), False)      # a lower wick after the sweep (bearish candle)
    m.on_candle_close(cd(2, 100.5, 101.5, 100.25, 101.4), False)
    sig = m.on_candle_close(cd(3, 101.5, 102, 101.0, 101.8), False)
    assert sig.extreme == 99.0 and m.active.reversal_extreme_ts == T0 + pd.Timedelta(minutes=1)


def test_window_excludes_candles_before_sweep_and_after_c():
    """For a short setup the reversal high is scanned; a tall wick before the sweep candle must not count,
    and nothing after candle C may change the extreme."""
    m = manager(bsl=[100.0])
    m.on_candle_close(cd(0, 99, 99.9, 90.0, 99.5), False)            # before the sweep: high 99.9 (no sweep), irrelevant
    m.on_candle_close(cd(1, 99.5, 100.25, 99, 99.6), False)          # sweep candle, high 100.25
    m.on_candle_close(cd(2, 99.5, 99.75, 99.0, 99.5), False)         # A
    m.on_candle_close(cd(3, 99.4, 99.5, 98.5, 98.6), False)          # B
    sig = m.on_candle_close(cd(4, 98.5, 98.75, 97.5, 97.6), False)   # C: high 98.75 < A.low 99.0 -> bearish
    assert sig.direction == SHORT and sig.extreme == 100.25 and m.active.window_candles == 4
    assert m.active.reversal_extreme_ts == T0 + pd.Timedelta(minutes=1)
    m.on_candle_close(cd(5, 110, 111, 109, 110), False)              # after C: ignored
    assert m.active.reversal_extreme == 100.25
    # and the pre-sweep candle is excluded even when its wick is the most extreme: plant a huge pre-sweep high
    m2 = manager(bsl=[100.0]); m2.on_candle_close(cd(0, 99, 99.95, 99, 99.5), False)
    m2._recent[-1].high = 150.0                                      # mutate after the sweep check: simulates a pre-window wick
    m2.on_candle_close(cd(1, 99.5, 100.25, 99, 99.6), False); m2.on_candle_close(cd(2, 99.5, 99.75, 99.0, 99.5), False)
    m2.on_candle_close(cd(3, 99.4, 99.5, 98.5, 98.6), False); sig2 = m2.on_candle_close(cd(4, 98.5, 98.75, 97.5, 97.6), False)
    assert sig2.extreme == 100.25


def test_bearish_mirror_highest_wick_and_stop():
    sim = Simulator(BacktestConfig(), long_session()); m = manager(bsl=[100.0])
    m.on_candle_close(cd(0, 99, 100.25, 98, 99.5), False)            # sweeps the high; high 100.25
    m.on_candle_close(cd(1, 99.5, 100.5, 99.0, 99.5), False)         # higher wick 100.5 = reversal high
    m.on_candle_close(cd(2, 99.5, 99.75, 98.5, 98.6), False)
    sig = m.on_candle_close(cd(3, 98.5, 98.75, 97.5, 97.6), False)   # C.high 98.75 < A.low 99.0 -> bearish
    assert sig.direction == SHORT and sig.extreme == 100.5
    sim.on_signal(sig, long_session()[0])
    sim.on_minute(MinuteBar(ts=T0 + pd.Timedelta(minutes=4), open=90.5, high=91, low=90, close=90.5, session=0, contract="MNQT1", cum_offset=0.0))
    p = sim.position
    assert p.entry_price == 90.0 and p.stop == 90.0 + 2 * (100.5 - 90.0) == 111.0


def test_invalid_stop_geometry_rejected():
    sim, m = run_setup_to_entry(open_px=99.25)                       # fill 99.75 == reversal low -> distance 0
    assert m.setups[-1].setup_status == SetupStatus.ENTRY_REJECTED and m.setups[-1].reject_reason == "invalid_stop"
    assert sim.position is None
    sim, m = run_setup_to_entry(open_px=98.0)                        # gapped below the reversal low
    assert m.setups[-1].reject_reason == "invalid_stop"


def test_existing_min_stop_rule_applies_when_enabled_and_is_flagged_provisional():
    sim, m = run_setup_to_entry(open_px=101.75, min_stop=10.0)       # doubled 5.0 < 10 -> existing rule rejects
    assert m.setups[-1].setup_status == SetupStatus.ENTRY_REJECTED and m.setups[-1].reject_reason == "min_stop"
    sim, m = run_setup_to_entry(open_px=101.75, min_stop=0.0)
    assert m.setups[-1].setup_status == SetupStatus.ENTRY_TRIGGERED
    assert FvgConfig().apply_existing_min_stop is True                # provisional, see report


def test_stop_fixed_after_entry():
    sim, m = run_setup_to_entry(open_px=101.75, min_stop=0.0)
    p = sim.position; stop0 = p.stop
    sim.on_minute(MinuteBar(ts=T0 + pd.Timedelta(minutes=5), open=105, high=110, low=104, close=109, session=0, contract="MNQT1", cum_offset=0.0))
    assert sim.position is None or sim.position.stop == stop0        # exited at target or still with the same stop
    sim2, m2 = run_setup_to_entry(open_px=101.75, min_stop=0.0)
    sim2.on_minute(MinuteBar(ts=T0 + pd.Timedelta(minutes=5), open=103, high=103.5, low=102.5, close=103, session=0, contract="MNQT1", cum_offset=0.0))
    assert sim2.position.stop == 97.25                                # unchanged after a favourable minute


def test_sizing_and_costs_are_the_existing_policy():
    sim, m = run_setup_to_entry(open_px=101.75, min_stop=0.0)
    p = sim.position; cfg = BacktestConfig()
    rpc = p.stop_distance * 2 + cfg.costs.fees_round_trip + cfg.costs.slippage_ticks * cfg.instrument.tick_value
    assert p.contracts == min(10, int(500 // rpc)) and p.planned_risk_per_contract == pytest.approx(rpc)


# --------------------------------------------------------------- integration
def test_one_entry_per_sweep_and_no_duplicate_entries():
    sim, m = run_setup_to_entry(open_px=101.75, min_stop=0.0)
    assert len(m.setups) == 1 and m.active is None
    # the same level cannot produce another setup; a new breach of it does nothing
    assert m.on_candle_close(cd(10, 101, 102, 99.5, 100.5), sim.occupied) is None and len(m.setups) == 1


def test_sweeps_ignored_while_setup_or_position_active():
    m = manager(ssl=[100.0, 98.0]); long_setup_at(m)
    m.on_candle_close(cd(1, 99, 99.5, 97.75, 98.5), False)           # second level swept while waiting
    assert len(m.setups) == 1 and m.ignored[-1]["reason"] == "setup_active"
    m2 = manager(ssl=[100.0])
    m2.on_candle_close(cd(0, 101, 102, 99.75, 100.5), True)          # occupied by an open position
    assert m2.active is None and m2.ignored[-1]["reason"] == "position_or_order_active"


def test_both_sides_swept_same_minute_ignored():
    m = manager(bsl=[102.0], ssl=[98.0])
    m.on_candle_close(cd(0, 100, 102.25, 97.75, 100), False)
    assert m.active is None and {x["reason"] for x in m.ignored} == {"both_sides_swept_same_minute"}


def test_intrabar_sweep_set_matches_engine_h1_events():
    """On real data, the minute-level detection must flag exactly the (level, hour) pairs the engine sweeps."""
    pytest.importorskip("databento")
    from lsr.config import DATASETS
    from lsr.data import build_market_data
    md = build_market_data(DATASETS["2025_2026"], StrategyConfig())
    eng = LiquidityEngine(EngineParams()); m1 = md.m1
    mism = 0; checked = 0
    for hb in md.h1.iloc[:2000].itertuples():
        active = {("bsl", l.created_bar, l.price) for l in eng.active_levels("bsl")} | {("ssl", l.created_bar, l.price) for l in eng.active_levels("ssl")}
        sub = m1.iloc[hb.first_m1:hb.last_m1 + 1]
        intrabar = {k for k in active if (k[0] == "bsl" and (sub.high > k[2]).any()) or (k[0] == "ssl" and (sub.low < k[2]).any())}
        ev = eng.on_bar(hb.high, hb.low, hb.close)
        engine_set = {("bsl", l.created_bar, l.price) for l in ev.bsl_swept_levels} | {("ssl", l.created_bar, l.price) for l in ev.ssl_swept_levels}
        mism += int(intrabar != engine_set); checked += len(engine_set)
    assert mism == 0 and checked > 50


def test_original_engine_unchanged():
    """The Pine source and the verified port are byte-identical to the versions that passed parity."""
    assert hashlib.md5((ROOT / "engine" / "bsl_ssl.pine").read_bytes()).hexdigest() == "ee49700535649fe62a8ecc6742f6e142"
    assert hashlib.md5((ROOT / "src" / "lsr" / "liquidity_engine.py").read_bytes()).hexdigest() == "030525e3b09cbaebcbd1c06f73e24fa9"


# ------------------------------------------------- 2026-10-28 stop update: (doubled * 0.5)
def run_half_doubled(open_px, min_stop, exit_mode="be_at_1r_tp_2r", level=100.0, sweep_low=99.75):
    cfg = BacktestConfig()
    cfg = dataclasses.replace(cfg, risk=dataclasses.replace(cfg.risk, min_stop_points=min_stop),
                              strategy=dataclasses.replace(cfg.strategy, stop_multiple=1.0, exit_mode=exit_mode))
    sim = Simulator(cfg, long_session()); m = manager(ssl=[level]); L = level
    m.on_candle_close(cd(0, L + 1, L + 2, sweep_low, L + 0.5), sim.occupied)
    m.on_candle_close(cd(1, L + 0.5, L + 0.75, L + 0.0, L + 0.5), sim.occupied)
    m.on_candle_close(cd(2, L + 0.5, L + 1.5, L + 0.25, L + 1.4), sim.occupied)
    sig = m.on_candle_close(cd(3, L + 1.5, L + 2, L + 1.0, L + 1.8), sim.occupied)
    sim.on_signal(sig, long_session()[0])
    sim.on_minute(MinuteBar(ts=T0 + pd.Timedelta(minutes=4), open=open_px, high=open_px + 0.5, low=open_px - 0.5, close=open_px, session=0, contract="MNQT1", cum_offset=0.0))
    oc = sim.last_market_outcome
    if oc["outcome"] == "entered":
        m.on_entry(oc["ts"], oc["fill"], oc["stop"], oc["dist"])
    else:
        m.on_entry_rejected(oc["ts"], oc["reason"], oc.get("fill"))
    return sim, m


def test_half_doubled_stop_sits_at_reversal_wick_and_targets_2r():
    sim, m = run_half_doubled(open_px=29_914.5, min_stop=0.0, level=29_900.0, sweep_low=29_895.0)
    s = m.setups[-1]; p = sim.position
    assert s.entry_fill_price == 29_915.0 and s.original_stop_distance == 20.0 and s.doubled_stop_distance == 40.0
    assert s.final_stop_distance == 20.0 and s.final_stop_price == 29_895.0 == p.stop == s.reversal_extreme
    assert p.be_level == 29_935.0 and p.target == 29_955.0                       # 1R arms break-even, 2R target
    assert p.stop < p.entry_price                                                 # correct side for a long
    assert p.contracts == min(10, int(500 // (20.0 * 2 + 1.88 + 1.0)))           # sizing from the new distance


def test_half_doubled_bearish_side_and_invalid_geometry():
    sim = Simulator(dataclasses.replace(BacktestConfig(), strategy=StrategyConfig(stop_multiple=1.0, exit_mode="be_at_1r_tp_2r"),
                                        risk=dataclasses.replace(BacktestConfig().risk, min_stop_points=0.0)), long_session())
    m = manager(bsl=[100.0])
    m.on_candle_close(cd(0, 99, 100.25, 98, 99.5), False); m.on_candle_close(cd(1, 99.5, 100.5, 99.0, 99.5), False)
    m.on_candle_close(cd(2, 99.5, 99.75, 98.5, 98.6), False); sig = m.on_candle_close(cd(3, 98.5, 98.75, 97.5, 97.6), False)
    sim.on_signal(sig, long_session()[0])
    sim.on_minute(MinuteBar(ts=T0 + pd.Timedelta(minutes=4), open=90.5, high=91, low=90, close=90.5, session=0, contract="MNQT1", cum_offset=0.0))
    p = sim.position
    assert p.entry_price == 90.0 and p.stop == 100.5 and p.stop > p.entry_price and p.target == 90.0 - 2 * 10.5
    sim2, m2 = run_half_doubled(open_px=99.25, min_stop=0.0)                      # fill at the wick: distance 0 -> rejected
    assert m2.setups[-1].reject_reason == "invalid_stop"


def test_half_doubled_min_stop_applies_only_when_enabled():
    sim, m = run_half_doubled(open_px=101.75, min_stop=10.0)                      # distance 2.5 < 10
    assert m.setups[-1].reject_reason == "min_stop"
    sim, m = run_half_doubled(open_px=101.75, min_stop=0.0)
    assert m.setups[-1].setup_status == SetupStatus.ENTRY_TRIGGERED and sim.position.stop == 99.75


def test_stop_multiple_default_preserves_v1_behaviour():
    assert StrategyConfig().stop_multiple == 2.0


# ------------------------------------------------------------- session filter
def test_session_filter_on_sweep_and_on_confirmation():
    NYT = pd.Timestamp("2026-01-06 09:25", tz="America/New_York").tz_convert("UTC")   # 09:25 ET base
    m = SetupManager(engine_with_levels(ssl=[100.0]), 15, SweepTimestampMode.INTRABAR_1M, session=("09:30", "11:30"))
    m.on_candle_close(cd(0, 101, 102, 99.75, 100.5, base=NYT), False)                 # sweep at 09:26 close -> outside
    assert m.active is None and m.ignored[-1]["reason"] == "outside_session"
    m.engine.ssl.append(type(m.engine.ssl[0])(price=99.0, created_bar=1, pivot_bar=1))
    m.on_candle_close(cd(5, 99.5, 99.6, 98.75, 99.2, base=NYT), False)                # 09:31 close -> inside
    assert m.active is not None
    m2 = SetupManager(engine_with_levels(ssl=[100.0]), 15, SweepTimestampMode.INTRABAR_1M, session=("09:30", "11:30"))
    late = pd.Timestamp("2026-01-06 11:20", tz="America/New_York").tz_convert("UTC")
    m2.on_candle_close(cd(0, 101, 102, 99.75, 100.5, base=late), False)               # sweep 11:21, inside
    m2.on_candle_close(cd(8, 100, 100.5, 99.5, 100.2, base=late), False)              # A
    m2.on_candle_close(cd(9, 100.5, 101, 100.3, 100.9, base=late), False)             # B
    assert m2.on_candle_close(cd(10, 101, 101.5, 100.75, 101.2, base=late), False) is None   # C closes 11:31 -> rejected
    assert m2.setups[-1].setup_status == SetupStatus.ENTRY_REJECTED and m2.setups[-1].reject_reason == "fvg_confirmed_outside_session"
    m3 = SetupManager(engine_with_levels(ssl=[100.0]), 15, SweepTimestampMode.INTRABAR_1M, session=("09:30", "11:30"))
    m3.on_candle_close(cd(0, 101, 102, 99.75, 100.5, base=late), False)
    m3.on_candle_close(cd(7, 100, 100.5, 99.5, 100.2, base=late), False); m3.on_candle_close(cd(8, 100.5, 101, 100.3, 100.9, base=late), False)
    assert m3.on_candle_close(cd(9, 101, 101.5, 100.75, 101.2, base=late), False) is not None   # C closes 11:30 exactly -> allowed

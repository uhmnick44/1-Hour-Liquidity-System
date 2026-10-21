"""Strict breach semantics of the ported engine on synthetic bars."""
from lsr.liquidity_engine import EngineParams, LiquidityEngine


def feed(engine, bars):
    return [engine.on_bar(*b) for b in bars]


def pivot_series(level=100.0, n=5):
    # highs rising to a pivot at `level` then falling: pivot confirmed n bars later
    highs = [90 + i for i in range(n)] + [level] + [level - 1 - i for i in range(n)]
    return [(h, h - 2, h - 1) for h in highs]


def test_level_confirms_n_bars_after_pivot_and_not_before():
    eng = LiquidityEngine(EngineParams(swing_len=5))
    evs = feed(eng, pivot_series())
    assert all(e.new_bsl_px is None for e in evs[:-1])
    assert evs[-1].new_bsl_px == 100.0
    assert eng.active_levels("bsl")[0].price == 100.0


def test_touch_does_not_sweep_but_strict_breach_does():
    eng = LiquidityEngine(EngineParams(swing_len=5))
    feed(eng, pivot_series())
    ev = eng.on_bar(100.0, 95.0, 96.0)       # high == level: touch
    assert not ev.bsl_swept_now and not eng.bsl[-1].swept
    ev = eng.on_bar(100.25, 95.0, 96.0)      # high > level by one tick
    assert ev.bsl_swept_now and eng.bsl[-1].swept and eng.bsl[-1].swept_bar == eng.bar_index


def test_level_is_consumed_once_and_evicted_by_cap():
    eng = LiquidityEngine(EngineParams(swing_len=1, max_levels=2))
    # alternating highs produce a pivot every other bar
    bars = [(h, h - 5, h - 1) for h in [10, 20, 10, 30, 10, 40, 10]]
    feed(eng, bars)
    assert [l.price for l in eng.bsl] == [30.0, 40.0]     # 20 evicted (oldest first), cap 2
    ev = eng.on_bar(100.0, 50.0, 60.0)
    assert ev.bsl_swept_now and all(l.swept for l in eng.bsl)
    ev = eng.on_bar(200.0, 150.0, 160.0)                  # already swept: no second sweep event
    assert not ev.bsl_swept_now


def test_sell_side_mirror():
    eng = LiquidityEngine(EngineParams(swing_len=2))
    lows = [50, 49, 40, 48, 51]
    feed(eng, [(l + 2, l, l + 1) for l in lows])
    assert eng.active_levels("ssl")[0].price == 40.0
    assert not eng.on_bar(45.0, 40.0, 42.0).ssl_swept_now   # touch
    assert eng.on_bar(45.0, 39.75, 42.0).ssl_swept_now      # strict

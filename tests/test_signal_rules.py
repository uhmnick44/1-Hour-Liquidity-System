import pandas as pd

from lsr.liquidity_engine import BarEvents, Level
from lsr.signals import LONG, SHORT, classify_zone, entry_type_for, evaluate_candle

TS = pd.Timestamp("2026-01-05 15:00", tz="UTC"); CTS = TS + pd.Timedelta(hours=1)


def lvl(px):
    return Level(price=px, created_bar=0, pivot_bar=0, swept=True)


def ev(bsl=(), ssl=()):
    return BarEvents(bar=10, bsl_swept_now=bool(bsl), ssl_swept_now=bool(ssl),
                     bsl_swept_levels=[lvl(p) for p in bsl], ssl_swept_levels=[lvl(p) for p in ssl])


def test_same_candle_close_back_required():
    sig, skip = evaluate_candle(ev(bsl=[100.0]), TS, CTS, high=101.0, low=95.0, close=99.75)
    assert sig is not None and sig.direction == SHORT and sig.level_price == 100.0
    sig, skip = evaluate_candle(ev(bsl=[100.0]), TS, CTS, high=101.0, low=95.0, close=100.0)   # close at level
    assert sig is None and skip == "sweep_without_close_back"
    sig, skip = evaluate_candle(ev(bsl=[100.0]), TS, CTS, high=101.0, low=95.0, close=100.5)   # closed above
    assert sig is None and skip == "sweep_without_close_back"


def test_dual_side_sweep_skipped_even_with_one_sided_close_back():
    sig, skip = evaluate_candle(ev(bsl=[100.0], ssl=[90.0]), TS, CTS, high=101.0, low=89.0, close=99.0)
    assert sig is None and skip == "dual_side_sweep"


def test_bullish_mirror_and_level_choice():
    sig, _ = evaluate_candle(ev(ssl=[90.0, 92.0]), TS, CTS, high=95.0, low=89.0, close=93.0)
    assert sig.direction == LONG and sig.level_price == 90.0 and sig.n_levels == 2
    sig, _ = evaluate_candle(ev(ssl=[90.0, 92.0]), TS, CTS, high=95.0, low=89.0, close=91.0)
    assert sig.level_price == 90.0 and sig.n_levels == 1   # 92 was swept but not closed back above


def test_zone_classification_and_entry_type():
    assert classify_zone(100.5, 100.0) == "premium" and classify_zone(99.5, 100.0) == "discount" and classify_zone(100.0, 100.0) == "equilibrium"
    assert entry_type_for(SHORT, "premium") == "market" and entry_type_for(SHORT, "equilibrium") == "market" and entry_type_for(SHORT, "discount") == "limit"
    assert entry_type_for(LONG, "discount") == "market" and entry_type_for(LONG, "equilibrium") == "market" and entry_type_for(LONG, "premium") == "limit"


def test_eq_uses_full_candle_including_wicks_and_exact_eq_close_is_market():
    sig, _ = evaluate_candle(ev(bsl=[100.0]), TS, CTS, high=101.0, low=95.0, close=98.0)
    assert sig.eq == 98.0 and sig.zone == "equilibrium" and sig.entry_type == "market"

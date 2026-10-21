import numpy as np
import pandas as pd
import pytest

from lsr.config import DataConfig, StrategyConfig
from lsr.data import build_market_data, expiry_date, roll_schedule, third_friday
from lsr.sessions import build_sessions


def test_third_friday_and_holiday_shift():
    assert third_friday(2025, 12) == pd.Timestamp("2025-12-19")
    assert third_friday(2026, 6) == pd.Timestamp("2026-06-19")
    import pandas_market_calendars as mcal
    nyse = mcal.get_calendar("NYSE").valid_days("2025-01-01", "2027-12-31").tz_localize(None)
    assert expiry_date("MNQM6", nyse) == pd.Timestamp("2026-06-18")    # Juneteenth
    assert expiry_date("MNQZ5", nyse) == pd.Timestamp("2025-12-19")


def test_fixed_friday_roll_schedule():
    sessions = build_sessions("2025-10-01", "2026-10-21", StrategyConfig())
    rolls = roll_schedule(["MNQZ5", "MNQH6", "MNQM6", "MNQU6", "MNQZ6"], sessions)
    assert [str(r.roll_session_date.date()) for r in rolls] == ["2025-12-12", "2026-03-13", "2026-06-12", "2026-09-11"]
    assert all(r.roll_session_date.weekday() == 4 for r in rolls)
    assert all(r.roll_session_date < r.expiry - pd.Timedelta(days=r.expiry.weekday()) for r in rolls)


def synthetic_contracts():
    """Two contracts over a week; the new one trades 100 points above the old."""
    idx = pd.date_range("2025-12-08 00:00", "2025-12-16 23:59", freq="1min", tz="UTC")
    base = 20000 + np.cumsum(np.random.default_rng(1).integers(-2, 3, len(idx))) * 0.25
    old = pd.DataFrame({"open": base, "high": base + 0.5, "low": base - 0.5, "close": base + 0.25, "volume": 10}, index=idx)
    new = old.copy(); new[["open", "high", "low", "close"]] += 100.0
    old.index.name = new.index.name = "ts"
    return {"MNQZ5": old, "MNQH6": new}


def test_forward_adjustment_is_continuous_and_recoverable():
    cfg = DataConfig(start_utc="2025-12-08T00:00:00Z", end_utc="2025-12-17T00:00:00Z")
    md = build_market_data(cfg, StrategyConfig(), front_contracts=("MNQZ5", "MNQH6"), contracts=synthetic_contracts())
    r = md.rolls[0]
    assert str(r.roll_session_date.date()) == "2025-12-12" and r.offset == 100.0
    m1 = md.m1
    before = m1[m1.index < r.boundary_utc]; after = m1[m1.index >= r.boundary_utc]
    assert (before.contract == "MNQZ5").all() and (after.contract == "MNQH6").all()
    assert (after.cum_offset == -100.0).all() and (before.cum_offset == 0.0).all()
    assert np.allclose(after.close - after.cum_offset, after.raw_close)       # executable price recoverable
    # no artificial jump: adjusted close just after the boundary ~ adjusted close just before
    assert abs(after.close.iloc[0] - before.close.iloc[-1]) < 60.0     # only the weekend random-walk drift remains
    # exact continuity at the boundary itself: adjusted new close at the roll minute equals the old close
    new_raw = synthetic_contracts()["MNQH6"]
    assert new_raw.loc[r.new_close_ts].close - 100.0 == r.old_close
    assert md.sessions[[s.date for s in md.sessions].index(r.roll_session_date)].roll_boundary
    assert (md.m1.contract.values[md.h1.first_m1.values] == md.m1.contract.values[md.h1.last_m1.values]).all()


def test_offsets_are_tick_valid_on_real_data():
    pytest.importorskip("databento")
    md = build_market_data(DataConfig(), StrategyConfig())
    for r in md.rolls:
        assert abs(r.offset / 0.25 - round(r.offset / 0.25)) < 1e-9
        assert r.old_close_ts.tz_convert("America/New_York").strftime("%H:%M") == "16:59"
    assert md.validation["dropped_outside_session"] == 0

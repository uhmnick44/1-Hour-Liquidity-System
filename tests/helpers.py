"""Builders for synthetic sessions, bars and signals used by the rule tests."""
from __future__ import annotations

from typing import List, Optional

import pandas as pd

from lsr.config import BacktestConfig
from lsr.execution import MinuteBar, Simulator
from lsr.sessions import Session
from lsr.signals import Signal, SHORT, LONG, classify_zone, entry_type_for

NY = "America/New_York"
T0 = pd.Timestamp("2026-01-05 18:00", tz=NY).tz_convert("UTC")   # Monday session open (Jan 4 18:00 ET is Sunday; use Mon)


def make_session(open_utc: pd.Timestamp, close_utc: pd.Timestamp, flatten_at: Optional[pd.Timestamp] = None) -> Session:
    return Session(date=close_utc.tz_convert(NY).normalize().tz_localize(None), open=open_utc, close=close_utc,
                   break_start=close_utc - pd.Timedelta(minutes=45), break_end=close_utc - pd.Timedelta(minutes=30),
                   flatten_at=flatten_at)


def long_session(flatten_at: Optional[pd.Timestamp] = None) -> List[Session]:
    """One wide session so synthetic bars never cross a boundary unless a test wants it."""
    return [make_session(T0 - pd.Timedelta(days=10), T0 + pd.Timedelta(days=10), flatten_at)]


def mb(minutes: int, o: float, h: float, l: float, c: float, session: int = 0, base: pd.Timestamp = T0) -> MinuteBar:
    return MinuteBar(ts=base + pd.Timedelta(minutes=minutes), open=o, high=h, low=l, close=c, session=session,
                     contract="MNQT1", cum_offset=0.0)


def mk_signal(direction: int, high: float, low: float, close: float, close_minute: int = 60, base: pd.Timestamp = T0) -> Signal:
    eq = (high + low) / 2.0
    zone = classify_zone(close, eq)
    return Signal(bar_ts=base + pd.Timedelta(minutes=close_minute - 60), close_ts=base + pd.Timedelta(minutes=close_minute),
                  direction=direction, sweep_high=high, sweep_low=low, close=close, eq=eq, zone=zone,
                  entry_type=entry_type_for(direction, zone), level_price=high if direction == SHORT else low, n_levels=1)


def sim(sessions: Optional[List[Session]] = None, **cfg_overrides) -> Simulator:
    import dataclasses
    cfg = BacktestConfig()
    if cfg_overrides:
        cfg = dataclasses.replace(cfg, **cfg_overrides)
    return Simulator(cfg, sessions or long_session())

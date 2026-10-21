"""CME equity-index trading sessions for MNQ with documented overrides.

A *session* is one exchange trading day: it opens at 18:00 New York the previous
calendar day and closes at 17:00 New York (16:00 Chicago), with a 16:15 to 16:30
New York halt, except on holidays. Sessions come from pandas_market_calendars
``CME_Equity`` and are then patched with ``CALENDAR_OVERRIDES`` from config.

Flatten cutoffs are derived here:
* ``closure_flatten``: the gap to the next session's open exceeds
  ``extended_closure_hours`` (weekends, Christmas, New Year), cutoff is
  ``flatten_minutes_before_close`` before the close.
* ``roll_flatten``: the session is a roll boundary (see data.py), same cutoff.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal

from .config import CALENDAR_OVERRIDES, StrategyConfig

NY = "America/New_York"


@dataclass
class Session:
    date: pd.Timestamp          # exchange trading date (naive date of the close)
    open: pd.Timestamp          # UTC
    close: pd.Timestamp         # UTC (exclusive: last tradable minute starts 1 min before)
    break_start: pd.Timestamp   # UTC
    break_end: pd.Timestamp     # UTC
    override_note: Optional[str] = None
    extended_closure_after: bool = False
    roll_boundary: bool = False
    flatten_at: Optional[pd.Timestamp] = None   # UTC, None if no flatten this session

    @property
    def requires_flatten(self) -> bool:
        return self.flatten_at is not None


def build_sessions(start: str, end: str, cfg: StrategyConfig,
                   roll_dates: Optional[List[pd.Timestamp]] = None) -> List[Session]:
    cal = mcal.get_calendar("CME_Equity")
    sched = cal.schedule(start_date=pd.Timestamp(start).date() - pd.Timedelta(days=3),
                         end_date=pd.Timestamp(end).date() + pd.Timedelta(days=5))
    roll_set = {pd.Timestamp(d).normalize() for d in (roll_dates or [])}
    sessions: List[Session] = []
    for date, row in sched.iterrows():
        s = Session(date=pd.Timestamp(date).normalize(), open=row.market_open, close=row.market_close,
                    break_start=row.break_start, break_end=row.break_end)
        key = s.date.strftime("%Y-%m-%d")
        if key in CALENDAR_OVERRIDES:
            hhmm, note = CALENDAR_OVERRIDES[key]
            s.close = pd.Timestamp(f"{key} {hhmm}", tz=NY).tz_convert("UTC")
            s.override_note = note
        if s.date in roll_set:
            s.roll_boundary = True
        sessions.append(s)
    # closures and flatten cutoffs
    thresh = pd.Timedelta(hours=cfg.extended_closure_hours)
    cut = pd.Timedelta(minutes=cfg.flatten_minutes_before_close)
    for i, s in enumerate(sessions):
        if i + 1 < len(sessions):
            s.extended_closure_after = (sessions[i + 1].open - s.close) > thresh
        if s.extended_closure_after or s.roll_boundary:
            s.flatten_at = s.close - cut
    return sessions


class SessionIndex:
    """Vectorised lookup of the session containing a UTC timestamp."""

    def __init__(self, sessions: List[Session]):
        self.sessions = sessions
        self.opens = np.array([s.open.value for s in sessions], dtype="int64")
        self.closes = np.array([s.close.value for s in sessions], dtype="int64")

    def locate(self, ts_ns: np.ndarray) -> np.ndarray:
        """Session index for each timestamp, or -1 when outside every session."""
        idx = np.searchsorted(self.opens, ts_ns, side="right") - 1
        ok = (idx >= 0)
        res = np.where(ok, idx, -1)
        inside = ok & (ts_ns < self.closes[np.clip(idx, 0, len(self.closes) - 1)])
        res[~inside] = -1
        return res

    def in_break(self, ts_ns: np.ndarray, sess_idx: np.ndarray) -> np.ndarray:
        bs = np.array([s.break_start.value for s in self.sessions]); be = np.array([s.break_end.value for s in self.sessions])
        i = np.clip(sess_idx, 0, len(self.sessions) - 1)
        return (sess_idx >= 0) & (ts_ns >= bs[i]) & (ts_ns < be[i])

    def as_frame(self) -> pd.DataFrame:
        rows = []
        for s in self.sessions:
            rows.append(dict(date=s.date.date(), open_et=s.open.tz_convert(NY), close_et=s.close.tz_convert(NY),
                             extended_closure_after=s.extended_closure_after, roll_boundary=s.roll_boundary,
                             flatten_at_et=s.flatten_at.tz_convert(NY) if s.flatten_at is not None else None,
                             override=s.override_note is not None))
        return pd.DataFrame(rows)

"""Databento MNQ 1-minute data: loading, contract expiries, fixed-Friday roll
schedule, forward-adjusted continuous series and 1H aggregation.

Roll rule (approved 2026-10-21): the roll boundary is the close of the last
session of the week preceding the expiry week ("the Friday before expiry
week"). The new contract is used from the next session on. Positions are flat
across the boundary (sessions.py marks it as a flatten session).

Adjustment: forward, additive. At each boundary the offset is
``new_close - old_close`` using each contract's last 1-minute bar at or before
the session close, both observable at that moment. Bars of later contracts carry
raw price plus the cumulative offset of all earlier rolls. Earlier bars are
untouched. The engine only compares prices and takes midpoints, so it is
translation-invariant; forward adjustment makes lookahead impossible by
construction and keeps every executable price recoverable as
``adjusted - cum_offset``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal

from .config import DataConfig, StrategyConfig
from .sessions import Session, SessionIndex, build_sessions, NY

MONTH_CODES = {"H": 3, "M": 6, "U": 9, "Z": 12}


# ----------------------------------------------------------------------------- loading
def load_contract(path: Path) -> pd.DataFrame:
    import databento as db
    df = db.DBNStore.from_file(path).to_df()[["open", "high", "low", "close", "volume"]].copy()
    df.index = df.index.tz_convert("UTC")
    df.index.name = "ts"
    return df


def load_all_contracts(cfg: DataConfig) -> Dict[str, pd.DataFrame]:
    out = {}
    for sym in cfg.front_contracts:
        files = sorted(cfg.databento_dir.rglob(f"*.ohlcv-1m.{sym}.dbn.zst"))
        if not files:
            raise FileNotFoundError(f"no file for {sym} in {cfg.databento_dir}")
        frames = [load_contract(f) for f in files]
        df = pd.concat(frames).sort_index()
        df = df[~df.index.duplicated(keep="first")]   # the same contract may appear in two batches
        out[sym] = df
    return out


# ---------------------------------------------------------------------------- expiries
def contract_year_month(sym: str) -> Tuple[int, int]:
    code, yy = sym[-2], int(sym[-1])
    # single-digit year code: 5 -> 2025, 6 -> 2026, 7 -> 2027 (valid for this decade's data)
    return 2020 + yy, MONTH_CODES[code]


def third_friday(year: int, month: int) -> pd.Timestamp:
    d = pd.Timestamp(year=year, month=month, day=1)
    first_friday = d + pd.Timedelta(days=(4 - d.weekday()) % 7)
    return first_friday + pd.Timedelta(days=14)


def expiry_date(sym: str, nyse_days: pd.DatetimeIndex) -> pd.Timestamp:
    """Third Friday of the contract month, moved to the preceding NYSE trading day
    when that Friday is an NYSE holiday (e.g. MNQM6 expired Thu 2026-06-18)."""
    y, m = contract_year_month(sym)
    e = third_friday(y, m)
    while e not in nyse_days:
        e -= pd.Timedelta(days=1)
    return e


@dataclass
class Roll:
    old: str
    new: str
    roll_session_date: pd.Timestamp     # last session using `old`
    boundary_utc: pd.Timestamp          # that session's close
    expiry: pd.Timestamp
    old_close: float = np.nan
    new_close: float = np.nan
    offset: float = np.nan              # new_close - old_close
    old_volume_roll_day: int = 0
    new_volume_roll_day: int = 0
    old_close_ts: Optional[pd.Timestamp] = None
    new_close_ts: Optional[pd.Timestamp] = None


def roll_schedule(front_contracts: List[str], sessions: List[Session]) -> List[Roll]:
    nyse = mcal.get_calendar("NYSE").valid_days("2015-01-01", "2030-12-31").tz_localize(None)
    sess_dates = pd.DatetimeIndex([s.date for s in sessions])
    rolls = []
    for old, new in zip(front_contracts[:-1], front_contracts[1:]):
        e = expiry_date(old, nyse)
        monday_of_expiry_week = e - pd.Timedelta(days=e.weekday())
        prior = sess_dates[sess_dates < monday_of_expiry_week]
        roll_date = prior[-1]
        s = sessions[list(sess_dates).index(roll_date)]
        rolls.append(Roll(old=old, new=new, roll_session_date=roll_date, boundary_utc=s.close, expiry=e))
    return rolls


# ------------------------------------------------------------------ continuous series
@dataclass
class MarketData:
    """Continuous forward-adjusted 1-minute series plus 1H aggregation."""
    m1: pd.DataFrame                 # index ts (UTC); open/high/low/close adjusted; raw_*; volume; contract; cum_offset; session
    h1: pd.DataFrame                 # index hour start (UTC); open/high/low/close adjusted; n_m1; first_m1; last_m1; contract; session
    sessions: List[Session]
    rolls: List[Roll]
    validation: Dict[str, object] = field(default_factory=dict)

    @property
    def session_index(self) -> SessionIndex:
        return SessionIndex(self.sessions)


def build_market_data(cfg: DataConfig, scfg: StrategyConfig,
                      front_contracts: Optional[Tuple[str, ...]] = None,
                      contracts: Optional[Dict[str, pd.DataFrame]] = None) -> MarketData:
    front_contracts = front_contracts or cfg.front_contracts
    contracts = contracts or {s: d for s, d in load_all_contracts(cfg).items() if s in front_contracts}
    base_sessions = build_sessions(cfg.start_utc, cfg.end_utc, scfg)
    rolls = roll_schedule(list(front_contracts), base_sessions)
    sessions = build_sessions(cfg.start_utc, cfg.end_utc, scfg, roll_dates=[r.roll_session_date for r in rolls])
    sidx = SessionIndex(sessions)
    start = pd.Timestamp(cfg.start_utc); end = pd.Timestamp(cfg.end_utc)

    # front contract per session
    sess_dates = [s.date for s in sessions]
    front_by_session = {}
    k = 0
    for d in sess_dates:
        while k < len(rolls) and d > rolls[k].roll_session_date:
            k += 1
        front_by_session[d] = front_contracts[k]

    # offsets at each boundary
    for r in rolls:
        s = sessions[sess_dates.index(r.roll_session_date)]
        for attr, sym in (("old", r.old), ("new", r.new)):
            d = contracts[sym]
            win = d[(d.index >= s.open) & (d.index < s.close)]
            if win.empty:
                raise ValueError(f"no bars for {sym} on roll session {s.date.date()}")
            last = win.iloc[-1]
            setattr(r, f"{attr}_close", float(last.close))
            setattr(r, f"{attr}_close_ts", win.index[-1])
            setattr(r, f"{attr}_volume_roll_day", int(win.volume.sum()))
        r.offset = r.new_close - r.old_close

    # Forward adjustment: the new contract is shifted so that its close at the
    # boundary equals the old contract's close, i.e. adjusted = raw - (new - old).
    # ``cum_offset`` therefore accumulates the negative calendar spreads.
    cum = {front_contracts[0]: 0.0}
    acc = 0.0
    for r in rolls:
        acc -= r.offset
        cum[r.new] = acc

    # assemble continuous 1m
    parts = []
    dropped_outside_session = 0
    for sym, d in contracts.items():
        d = d[(d.index >= start) & (d.index < end)]
        ts_ns = d.index.as_unit("ns").asi8
        si = sidx.locate(ts_ns)
        keep = si >= 0
        dropped_outside_session += int((~keep).sum())
        d = d[keep].copy(); si = si[keep]
        sess_d = np.array([sessions[i].date for i in si], dtype="datetime64[ns]")
        is_front = np.array([front_by_session[pd.Timestamp(x)] == sym for x in sess_d], dtype=bool)
        d = d[is_front].copy(); si = si[is_front]
        if d.empty:
            continue
        d["contract"] = sym
        d["cum_offset"] = cum[sym]
        d["session"] = si
        parts.append(d)
    m1 = pd.concat(parts).sort_index()
    assert m1.index.is_unique, "duplicate minute stamps in continuous series"
    for c in ("open", "high", "low", "close"):
        m1[f"raw_{c}"] = m1[c]
        m1[c] = m1[c] + m1["cum_offset"]
    m1["hour"] = m1.index.floor("h")

    # 1H aggregation
    g = m1.groupby("hour", sort=True)
    h1 = g.agg(open=("open", "first"), high=("high", "max"), low=("low", "min"), close=("close", "last"),
               volume=("volume", "sum"), n_m1=("close", "size"), contract=("contract", "first"), session=("session", "first"))
    pos = np.arange(len(m1))
    h1["first_m1"] = pd.Series(pos, index=m1.index).groupby(m1["hour"].values).min().values
    h1["last_m1"] = pd.Series(pos, index=m1.index).groupby(m1["hour"].values).max().values
    h1["close_ts"] = h1.index + pd.Timedelta(minutes=scfg.timeframe_minutes)
    assert (h1.contract.values == m1.contract.values[h1.first_m1.values]).all()
    assert (m1.contract.values[h1.first_m1.values] == m1.contract.values[h1.last_m1.values]).all(), "1H bar spans a roll"

    validation = dict(
        m1_bars=int(len(m1)), h1_bars=int(len(h1)), dropped_outside_session=dropped_outside_session,
        first_ts=str(m1.index[0]), last_ts=str(m1.index[-1]),
        tick_valid=bool(all(((m1[c] * 4).round() == m1[c] * 4).all() for c in ("open", "high", "low", "close"))),
        hl_ok=bool((m1.high >= m1.low).all()),
        rolls=[dict(old=r.old, new=r.new, roll_session=str(r.roll_session_date.date()), expiry=str(r.expiry.date()),
                    old_close=r.old_close, new_close=r.new_close, offset=r.offset,
                    old_volume=r.old_volume_roll_day, new_volume=r.new_volume_roll_day,
                    old_close_ts_et=str(r.old_close_ts.tz_convert(NY)), new_close_ts_et=str(r.new_close_ts.tz_convert(NY))) for r in rolls],
    )
    return MarketData(m1=m1, h1=h1, sessions=sessions, rolls=rolls, validation=validation)

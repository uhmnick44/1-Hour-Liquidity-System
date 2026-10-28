"""1H liquidity sweep -> first qualifying 1-minute FVG -> market entry with a
doubled reversal-extreme stop. Specification V1 (2026-10-28).

The 1H liquidity engine is used as-is. This module only consumes its levels
and events; it never alters them.

Sweep event timestamp. The engine evaluates closed 1H candles, so its own
event timestamp is the 1H close. The Pine original in Wick mode fires its
alert intrabar on the first tick through the level. ``SweepTimestampMode``
exposes both readings:

* ``intrabar_1m``: the sweep timestamp is the close of the first 1-minute
  bar whose high (low) strictly exceeds an active buy-side (sell-side) level.
  Levels active during an hour are those the engine holds after the previous
  1H close, so the detection is causal and reproduces the engine's own 1H
  sweep set exactly, one minute-level timestamp per (level, hour).
* ``h1_close``: the sweep timestamp is the engine's 1H close event.

FVG on three consecutive completed 1-minute candles A, B, C:
bullish when ``C.low > A.high``, bearish when ``C.high < A.low``. Equality is
not a gap. The FVG is confirmed at C's close. A and B may precede the sweep;
C must close strictly after the sweep timestamp and no later than
``sweep_timestamp + window_minutes`` (equality valid). The first qualifying FVG
in the sweep's direction is taken; opposite-direction FVGs are ignored.

Reversal extreme: the lowest low (long) or highest high (short) over the
1-minute candles from the sweep-containing candle through candle C inclusive.
Entry is at the open of the first 1-minute bar after C; the stop is
``fill -/+ 2 * |fill - extreme|``, which the existing execution module computes
from the modeled fill. If ``fill - extreme`` is not strictly positive in the
trade's favour the entry is rejected.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Deque, Dict, List, Optional, Tuple

import pandas as pd

from .liquidity_engine import Level, LiquidityEngine
from .signals import LONG, SHORT


class SweepTimestampMode(str, Enum):
    INTRABAR_1M = "intrabar_1m"
    H1_CLOSE = "h1_close"


class SetupStatus(str, Enum):
    WAITING_FOR_FVG = "WAITING_FOR_FVG"
    FVG_CONFIRMED = "FVG_CONFIRMED"
    ENTRY_TRIGGERED = "ENTRY_TRIGGERED"
    ENTRY_REJECTED = "ENTRY_REJECTED"
    EXPIRED = "EXPIRED"


@dataclass
class Candle:
    ts: pd.Timestamp          # bar open (UTC)
    open: float
    high: float
    low: float
    close: float

    @property
    def close_ts(self) -> pd.Timestamp:
        return self.ts + pd.Timedelta(minutes=1)


def fvg_direction(a: Candle, c: Candle) -> Optional[int]:
    """LONG for a bullish gap (C.low > A.high), SHORT for a bearish gap
    (C.high < A.low), None otherwise. Equal boundaries are not a gap."""
    if c.low > a.high:
        return LONG
    if c.high < a.low:
        return SHORT
    return None


@dataclass
class SweepSetup:
    sweep_id: int
    sweep_timestamp: pd.Timestamp        # UTC; the moment the sweep is known
    sweep_direction: int                 # SHORT after a high is swept, LONG after a low
    level_price: float
    level_id: str                        # "<side>:<created_bar>:<price>"
    expiration_timestamp: pd.Timestamp
    setup_status: SetupStatus = SetupStatus.WAITING_FOR_FVG
    fvg_confirmation_timestamp: Optional[pd.Timestamp] = None
    fvg_direction: Optional[int] = None
    fvg_candle_a_ts: Optional[pd.Timestamp] = None
    fvg_candle_c_ts: Optional[pd.Timestamp] = None
    entry_timestamp: Optional[pd.Timestamp] = None
    entry_fill_price: Optional[float] = None
    reversal_extreme: Optional[float] = None
    reversal_extreme_ts: Optional[pd.Timestamp] = None
    original_stop_distance: Optional[float] = None
    doubled_stop_distance: Optional[float] = None
    final_stop_price: Optional[float] = None
    reject_reason: Optional[str] = None
    window_candles: int = 0

    def row(self) -> dict:
        d = asdict(self)
        d["setup_status"] = self.setup_status.value
        d["sweep_direction"] = "short" if self.sweep_direction == SHORT else "long"
        d["fvg_direction"] = None if self.fvg_direction is None else ("short" if self.fvg_direction == SHORT else "long")
        return d


@dataclass(frozen=True)
class FvgSignal:
    """Entry request handed to the execution module. ``extreme`` is the
    reversal extreme, so the existing doubled-stop formula applies unchanged.
    ``zone_test`` is False: there is no EQ premium/discount rule here."""
    bar_ts: pd.Timestamp
    close_ts: pd.Timestamp
    direction: int
    extreme: float
    sweep_high: float
    sweep_low: float
    close: float
    eq: float
    zone: str
    entry_type: str
    level_price: float
    n_levels: int
    setup_id: int
    zone_test: bool = False


class SetupManager:
    """Tracks at most one active sweep setup at a time (the existing one-active
    rule, applied to setups as well as orders and positions, pending user
    confirmation: see FvgConfig.ignore_sweeps_while_occupied)."""

    def __init__(self, engine: LiquidityEngine, window_minutes: int, mode: SweepTimestampMode,
                 ignore_sweeps_while_occupied: bool = True):
        self.engine = engine
        self.window = pd.Timedelta(minutes=window_minutes)
        self.mode = mode
        self.ignore_while_occupied = ignore_sweeps_while_occupied
        self.active: Optional[SweepSetup] = None
        self.setups: List[SweepSetup] = []
        self.ignored: List[dict] = []
        self._recent: Deque[Candle] = deque(maxlen=3)
        self._window: List[Candle] = []
        self._seq = 0
        self._swept_keys: set = set()   # (level_id) already treated as swept intrabar this hour

    # ------------------------------------------------------------- helpers
    @staticmethod
    def level_id(side: str, lvl: Level) -> str:
        return f"{side}:{lvl.created_bar}:{lvl.price}"

    def _new_setup(self, ts: pd.Timestamp, direction: int, lvl_price: float, lvl_id: str) -> SweepSetup:
        self._seq += 1
        s = SweepSetup(sweep_id=self._seq, sweep_timestamp=ts, sweep_direction=direction, level_price=lvl_price,
                       level_id=lvl_id, expiration_timestamp=ts + self.window)
        self.setups.append(s)
        return s

    # ---------------------------------------------------------- sweep input
    def detect_intrabar_sweeps(self, c: Candle, occupied: bool) -> None:
        """Called after a 1-minute candle closes (intrabar mode). Checks the
        engine's currently active levels, which were fixed at the last 1H close."""
        hits: List[Tuple[int, float, str]] = []
        for lvl in self.engine.active_levels("bsl"):
            key = self.level_id("bsl", lvl)
            if key not in self._swept_keys and c.high > lvl.price:
                self._swept_keys.add(key); hits.append((SHORT, lvl.price, key))
        for lvl in self.engine.active_levels("ssl"):
            key = self.level_id("ssl", lvl)
            if key not in self._swept_keys and c.low < lvl.price:
                self._swept_keys.add(key); hits.append((LONG, lvl.price, key))
        self._register_sweeps(c.close_ts, hits, occupied)

    def register_h1_sweeps(self, close_ts: pd.Timestamp, bsl: List[Level], ssl: List[Level], occupied: bool) -> None:
        """h1_close mode: the engine's own events at the 1H close."""
        hits = [(SHORT, l.price, self.level_id("bsl", l)) for l in bsl] + [(LONG, l.price, self.level_id("ssl", l)) for l in ssl]
        self._register_sweeps(close_ts, hits, occupied)

    def on_h1_close(self) -> None:
        self._swept_keys.clear()   # the engine now carries the swept flags itself

    def _register_sweeps(self, ts: pd.Timestamp, hits: List[Tuple[int, float, str]], occupied: bool) -> None:
        if not hits:
            return
        dirs = {h[0] for h in hits}
        if len(dirs) > 1:
            for d, px, key in hits:
                self.ignored.append(dict(ts=ts, level_id=key, level_price=px, direction="short" if d == SHORT else "long",
                                         reason="both_sides_swept_same_minute"))
            return
        if self.active is not None or (occupied and self.ignore_while_occupied):
            for d, px, key in hits:
                self.ignored.append(dict(ts=ts, level_id=key, level_price=px, direction="short" if d == SHORT else "long",
                                         reason="setup_active" if self.active is not None else "position_or_order_active"))
            return
        # several levels of one side swept in the same minute: one setup, keyed to the most significant level
        d = hits[0][0]
        px = max(h[1] for h in hits) if d == SHORT else min(h[1] for h in hits)
        key = [h[2] for h in hits if h[1] == px][0]
        if len(hits) > 1:
            for dd, p2, k2 in hits:
                if k2 != key:
                    self.ignored.append(dict(ts=ts, level_id=k2, level_price=p2, direction="short" if dd == SHORT else "long",
                                             reason="merged_into_setup_same_minute"))
        self.active = self._new_setup(ts, d, px, key)
        self._window = [self._recent[-1]] if self._recent and self._recent[-1].close_ts == ts else []

    # ---------------------------------------------------------- minute step
    def on_candle_close(self, c: Candle, occupied: bool) -> Optional[FvgSignal]:
        """Feed every completed 1-minute candle in order. Returns an entry
        request when the active setup's first qualifying FVG confirms."""
        self._recent.append(c)
        if self.mode == SweepTimestampMode.INTRABAR_1M:
            self.detect_intrabar_sweeps(c, occupied)
        s = self.active
        if s is None or s.setup_status != SetupStatus.WAITING_FOR_FVG:
            return None
        if c.close_ts <= s.sweep_timestamp:
            return None
        if c.close_ts > s.expiration_timestamp:
            s.setup_status = SetupStatus.EXPIRED
            s.reject_reason = "no_fvg_within_window"
            self.active = None
            return None
        self._window.append(c)
        if len(self._recent) < 3:
            return None
        a, b, cc = self._recent
        d = fvg_direction(a, cc)
        if d != s.sweep_direction:
            return None
        s.setup_status = SetupStatus.FVG_CONFIRMED
        s.fvg_confirmation_timestamp = cc.close_ts
        s.fvg_direction = d
        s.fvg_candle_a_ts = a.ts; s.fvg_candle_c_ts = cc.ts
        s.window_candles = len(self._window)
        if d == LONG:
            ext = min(self._window, key=lambda x: x.low); s.reversal_extreme = ext.low
        else:
            ext = max(self._window, key=lambda x: x.high); s.reversal_extreme = ext.high
        s.reversal_extreme_ts = ext.ts
        return FvgSignal(bar_ts=cc.ts, close_ts=cc.close_ts, direction=d, extreme=s.reversal_extreme,
                         sweep_high=max(x.high for x in self._window), sweep_low=min(x.low for x in self._window),
                         close=cc.close, eq=float("nan"), zone="n/a", entry_type="market", level_price=s.level_price,
                         n_levels=1, setup_id=s.sweep_id)

    # ----------------------------------------------------------- outcomes
    def on_entry(self, ts: pd.Timestamp, fill: float, stop: float, dist: float) -> None:
        s = self.active
        s.setup_status = SetupStatus.ENTRY_TRIGGERED
        s.entry_timestamp = ts; s.entry_fill_price = fill
        s.original_stop_distance = dist / 2.0; s.doubled_stop_distance = dist; s.final_stop_price = stop
        self.active = None

    def on_entry_rejected(self, ts: pd.Timestamp, reason: str, fill: Optional[float] = None) -> None:
        s = self.active
        s.setup_status = SetupStatus.ENTRY_REJECTED
        s.reject_reason = reason; s.entry_timestamp = ts; s.entry_fill_price = fill
        self.active = None

    def setups_frame(self) -> pd.DataFrame:
        return pd.DataFrame([s.row() for s in self.setups])

    def ignored_frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.ignored)

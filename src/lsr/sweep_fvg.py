"""Window state machine for the 10-MNQ liquidity sweep -> first 1-minute FVG strategy.

Per entry window, per completed 1-minute candle, in this order:
1. publish levels whose reference period ended at this candle's open (so they are
   eligible from this candle on), purge expired levels;
2. penetration scan against eligible levels; consume what was penetrated; open or
   extend a sweep event, or reject a dual-sided one;
3. confirmation check for a pending event: close strictly back on the original side
   of the most extreme included level, within ``close_back_candles`` candles counting
   the penetration candle as the first;
4. for an active setup: 15-minute invalidation if this candle completes a 15-minute
   bar (strict close beyond any included level), then the first FVG in the reversal
   direction (candle 3 may be the confirmation candle); an FVG schedules a market
   entry at the next candle's open, with the stop beyond the three FVG candles'
   extreme by the tested offset;
5. the entry must open before the window ends; a scheduled entry whose timestamp
   coincides with a 15-minute invalidation is cancelled.

One executed trade per window. While a position is open, or after the window's trade,
penetrations still consume levels but create no events. Nothing here imports the
retired 1H engine.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Tuple

import pandas as pd

from .fvg import Candle, fvg_direction
from .liquidity_levels import BUY, SELL, Level, LevelBook
from .signals import LONG, SHORT

NY = "America/New_York"


class EventStatus(str, Enum):
    PENDING = "PENDING"                   # penetrated, awaiting close-back
    REJECTED_DUAL = "REJECTED_DUAL"
    FAILED_NO_CLOSE_BACK = "FAILED_NO_CLOSE_BACK"
    CONFIRMED = "CONFIRMED"               # setup active, awaiting FVG
    INVALIDATED_15M = "INVALIDATED_15M"
    ENTRY_SCHEDULED = "ENTRY_SCHEDULED"
    ENTERED = "ENTERED"
    ENTRY_CANCELLED = "ENTRY_CANCELLED"   # window end, invalidation at entry time, or stop not beyond fill
    WINDOW_ENDED = "WINDOW_ENDED"         # setup still waiting when the window closed


@dataclass
class SweepEvent:
    event_id: int
    window: str
    session_date: str
    direction: int                        # LONG after sell-side swept, SHORT after buy-side
    first_penetration_ts: pd.Timestamp    # open of the penetrating candle
    levels: List[Level] = field(default_factory=list)
    candles_seen: int = 0
    status: EventStatus = EventStatus.PENDING
    confirmed_at: Optional[pd.Timestamp] = None
    fvg_confirmed_at: Optional[pd.Timestamp] = None
    fvg_candles: Optional[Tuple[Candle, Candle, Candle]] = None
    stop_reference: Optional[float] = None
    stop_price: Optional[float] = None
    scheduled_entry_ts: Optional[pd.Timestamp] = None
    entry_ts: Optional[pd.Timestamp] = None
    entry_fill: Optional[float] = None
    reason: str = ""

    @property
    def extreme_level(self) -> float:
        """Most extreme included level: highest swept low (bullish) or lowest swept high (bearish)."""
        return max(l.price for l in self.levels) if self.direction == LONG else min(l.price for l in self.levels)

    def row(self) -> dict:
        return dict(event_id=self.event_id, window=self.window, session_date=self.session_date,
                    direction="long" if self.direction == LONG else "short",
                    first_penetration_ts=self.first_penetration_ts, status=self.status.value, reason=self.reason,
                    levels=";".join(f"{l.price}:{l.label()}" for l in self.levels), n_levels=len(self.levels),
                    extreme_level=self.extreme_level if self.levels else None, confirmed_at=self.confirmed_at,
                    fvg_confirmed_at=self.fvg_confirmed_at,
                    fvg_candle1_ts=self.fvg_candles[0].ts if self.fvg_candles else None,
                    stop_reference=self.stop_reference, stop_price=self.stop_price,
                    scheduled_entry_ts=self.scheduled_entry_ts, entry_ts=self.entry_ts, entry_fill=self.entry_fill)


@dataclass(frozen=True)
class SweepFvgSignal:
    """Entry request for the execution module: explicit stop, fixed contracts, no zone test."""
    bar_ts: pd.Timestamp
    close_ts: pd.Timestamp
    direction: int
    stop_price: float
    extreme: float
    sweep_high: float
    sweep_low: float
    close: float
    eq: float
    zone: str
    entry_type: str
    level_price: float
    n_levels: int
    event_id: int
    zone_test: bool = False


class WindowStateMachine:
    def __init__(self, book: LevelBook, tick: float, close_back_candles: int, stop_offset_ticks: int):
        self.book = book
        self.tick = tick
        self.close_back_candles = close_back_candles
        self.stop_offset = stop_offset_ticks * tick
        self.events: List[SweepEvent] = []
        self.current: Optional[SweepEvent] = None
        self.window_traded: set = set()           # (session_date, window) with an executed trade
        self.window_closed_for_entries: set = set()  # a setup that could not be entered: no second attempt
        self._seq = 0
        self._recent: List[Candle] = []
        self.ignored: List[dict] = []

    # ------------------------------------------------------------- helpers
    def _new_event(self, window: str, session_date: str, direction: int, ts: pd.Timestamp, levels: List[Level]) -> SweepEvent:
        self._seq += 1
        ev = SweepEvent(self._seq, window, session_date, direction, ts, list(levels))
        self.events.append(ev)
        return ev

    def _close_event(self, status: EventStatus, reason: str = "") -> None:
        if self.current is not None:
            self.current.status = status; self.current.reason = reason
            self.current = None

    def window_can_trade(self, session_date: str, window: str) -> bool:
        return (session_date, window) not in self.window_traded and (session_date, window) not in self.window_closed_for_entries

    # ------------------------------------------------------------ per candle
    def on_candle(self, c: Candle, window: Optional[str], session_date: str, window_end: Optional[pd.Timestamp],
                  occupied: bool, fifteen_closes: bool) -> Optional[SweepFvgSignal]:
        """Process one completed 1-minute candle. ``window`` is None outside entry windows.
        ``fifteen_closes`` is True when this candle completes a 15-minute bar."""
        self._recent.append(c)
        if len(self._recent) > 3:
            del self._recent[0]
        self.book.purge_expired(c.ts)

        # 1. penetration scan (always: consumption applies everywhere)
        pen_buy = self.book.penetrated(BUY, c.ts, c.high, c.low, self.tick)
        pen_sell = self.book.penetrated(SELL, c.ts, c.high, c.low, self.tick)
        for l in pen_buy + pen_sell:
            self.book.consume(l, c.close_ts, "penetrated")

        ev = self.current
        in_window = window is not None
        can_trade = in_window and not occupied and self.window_can_trade(session_date, window)

        # 2. event handling
        if ev is not None and ev.status == EventStatus.PENDING:
            ev.candles_seen += 1
            same = pen_sell if ev.direction == LONG else pen_buy
            opp = pen_buy if ev.direction == LONG else pen_sell
            if opp:
                self._close_event(EventStatus.REJECTED_DUAL, "opposite side penetrated before confirmation")
                for l in opp + same:
                    self.ignored.append(dict(ts=c.ts, level=l.price, side=l.side, reason="dual_sided_event"))
                ev = None
            else:
                ev.levels.extend(same)
                X = ev.extreme_level
                confirmed = (c.close > X) if ev.direction == LONG else (c.close < X)
                if confirmed:
                    ev.status = EventStatus.CONFIRMED; ev.confirmed_at = c.close_ts
                elif ev.candles_seen >= self.close_back_candles:
                    self._close_event(EventStatus.FAILED_NO_CLOSE_BACK, f"no close back within {self.close_back_candles} candles")
                    ev = None
        elif ev is None and can_trade and (pen_buy or pen_sell):
            if pen_buy and pen_sell:
                for l in pen_buy + pen_sell:
                    self.ignored.append(dict(ts=c.ts, level=l.price, side=l.side, reason="dual_sided_event"))
                rej = self._new_event(window, session_date, LONG, c.ts, pen_buy + pen_sell)
                rej.status = EventStatus.REJECTED_DUAL; rej.reason = "both sides penetrated on one candle"; rej.candles_seen = 1
            else:
                direction = LONG if pen_sell else SHORT
                ev = self._new_event(window, session_date, direction, c.ts, pen_sell or pen_buy)
                ev.candles_seen = 1
                self.current = ev
                X = ev.extreme_level
                if (c.close > X) if direction == LONG else (c.close < X):
                    ev.status = EventStatus.CONFIRMED; ev.confirmed_at = c.close_ts
        elif (pen_buy or pen_sell) and (ev is not None or not can_trade):
            reason = "setup_active" if ev is not None else ("position_open" if occupied else ("outside_window" if not in_window else "window_done"))
            for l in pen_buy + pen_sell:
                self.ignored.append(dict(ts=c.ts, level=l.price, side=l.side, reason=reason))

        ev = self.current
        if ev is None or ev.status != EventStatus.CONFIRMED:
            return None

        # 3. window end: a setup still waiting dies with the window
        if window_end is None or c.close_ts >= window_end:
            self._close_event(EventStatus.WINDOW_ENDED, "window closed before entry")
            return None

        # 4. 15-minute invalidation (priority over an FVG on the same candle)
        if fifteen_closes:
            X = ev.extreme_level
            if (c.close < X) if ev.direction == LONG else (c.close > X):
                self._close_event(EventStatus.INVALIDATED_15M, f"15m close beyond {X}")
                return None

        # 5. first FVG in the reversal direction, confirmed at or after sweep confirmation
        if len(self._recent) < 3:
            return None
        a, b, cc = self._recent
        if fvg_direction(a, cc) != ev.direction:
            return None
        ev.fvg_confirmed_at = cc.close_ts
        ev.fvg_candles = (a, b, cc)
        if ev.direction == LONG:
            ev.stop_reference = min(a.low, b.low, cc.low); ev.stop_price = ev.stop_reference - self.stop_offset
        else:
            ev.stop_reference = max(a.high, b.high, cc.high); ev.stop_price = ev.stop_reference + self.stop_offset
        ev.scheduled_entry_ts = cc.close_ts
        ev.status = EventStatus.ENTRY_SCHEDULED
        return SweepFvgSignal(bar_ts=cc.ts, close_ts=cc.close_ts, direction=ev.direction, stop_price=ev.stop_price,
                              extreme=ev.stop_reference, sweep_high=max(a.high, b.high, cc.high), sweep_low=min(a.low, b.low, cc.low),
                              close=cc.close, eq=float("nan"), zone="n/a", entry_type="market",
                              level_price=ev.extreme_level, n_levels=len(ev.levels), event_id=ev.event_id)

    # ------------------------------------------------------ entry outcomes
    def on_entered(self, ts: pd.Timestamp, fill: float) -> None:
        ev = self.current
        ev.status = EventStatus.ENTERED; ev.entry_ts = ts; ev.entry_fill = fill
        self.window_traded.add((ev.session_date, ev.window))
        self.current = None

    def on_entry_cancelled(self, ts: pd.Timestamp, reason: str, allow_new_setup: bool) -> None:
        ev = self.current
        ev.status = EventStatus.ENTRY_CANCELLED; ev.reason = reason; ev.entry_ts = ts
        if not allow_new_setup:
            self.window_closed_for_entries.add((ev.session_date, ev.window))
        self.current = None

    def events_frame(self) -> pd.DataFrame:
        return pd.DataFrame([e.row() for e in self.events])

"""Liquidity level book for the 10-MNQ sweep -> first 1-minute FVG strategy.

Five sources, all active together (user definitions of 2026-10-30):

1. 1-minute swing highs/lows: 2-left/2-right pivots (ties allowed, >=), eligible for
   60 minutes from the pivot bar's timestamp, tradeable only from the close of the
   second right-hand bar.
2. 15-minute swing highs/lows: 2-left/2-right pivots on clock-aligned 15-minute bars,
   eligible through the pivot's trading session plus the next five sessions.
3. Previous completed CME session (18:00 to 17:00 New York, or the actual close on
   early-close days) high and low, available from that close until the next session
   completes.
4. Previous completed regular-hours range (09:30 to 16:00 New York, or to the close
   when earlier) high and low, available from that end until the next RTH completes.
5. Pre-window range high and low for each entry window, available from the window
   start. ASSUMPTION: eligible only during that window.

Identical prices on the same side are one level carrying every source label. A level
is consumed by any one-tick penetration (default 1 of 2026-10-30) and does not return
until a source republishes it. Nothing here imports the retired 1H engine.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

BUY, SELL = "buy", "sell"      # buy-side liquidity sits above price (highs); sell-side below (lows)


@dataclass
class Level:
    level_id: int
    side: str
    price: float
    sources: Set[str]
    available_from: pd.Timestamp          # first bar open at which it may be swept
    expires_at: Optional[pd.Timestamp]    # exclusive; None = until republished
    created_at: pd.Timestamp
    consumed_at: Optional[pd.Timestamp] = None
    consumed_by: str = ""

    def label(self) -> str:
        return "|".join(sorted(self.sources))


class LevelBook:
    def __init__(self) -> None:
        self._active: Dict[Tuple[str, float], Level] = {}
        self.history: List[Level] = []
        self._seq = 0
        self._dirty = True
        self._arr: Dict[str, Tuple[np.ndarray, List[Level]]] = {}

    # ------------------------------------------------------------------ edits
    def add(self, side: str, price: float, source: str, available_from: pd.Timestamp,
            expires_at: Optional[pd.Timestamp], created_at: pd.Timestamp) -> Level:
        key = (side, float(price))
        lvl = self._active.get(key)
        if lvl is not None:
            lvl.sources.add(source)
            if lvl.expires_at is not None and (expires_at is None or expires_at > lvl.expires_at):
                lvl.expires_at = expires_at
            lvl.available_from = min(lvl.available_from, available_from)
            self._dirty = True
            return lvl
        self._seq += 1
        lvl = Level(self._seq, side, float(price), {source}, available_from, expires_at, created_at)
        self._active[key] = lvl
        self.history.append(lvl)
        self._dirty = True
        return lvl

    def retire_source(self, side: str, source: str, ts: pd.Timestamp) -> None:
        """A republishing source withdraws its previous level (e.g. previous-session high)."""
        for key, lvl in list(self._active.items()):
            if lvl.side == side and source in lvl.sources:
                lvl.sources.discard(source)
                if not lvl.sources:
                    lvl.consumed_at = ts; lvl.consumed_by = "retired"
                    del self._active[key]
        self._dirty = True

    def purge_expired(self, ts: pd.Timestamp) -> None:
        for key, lvl in list(self._active.items()):
            if lvl.expires_at is not None and ts >= lvl.expires_at:
                lvl.consumed_at = ts; lvl.consumed_by = "expired"
                del self._active[key]
                self._dirty = True

    def consume(self, lvl: Level, ts: pd.Timestamp, by: str) -> None:
        key = (lvl.side, lvl.price)
        if key in self._active and self._active[key] is lvl:
            lvl.consumed_at = ts; lvl.consumed_by = by
            del self._active[key]
            self._dirty = True

    # ----------------------------------------------------------------- queries
    def _rebuild(self) -> None:
        for side in (BUY, SELL):
            lv = [l for l in self._active.values() if l.side == side]
            self._arr[side] = (np.array([l.price for l in lv], dtype=float), lv)
        self._dirty = False

    def eligible(self, side: str, bar_open: pd.Timestamp) -> List[Level]:
        """Levels that may be swept by a candle opening at ``bar_open``."""
        if self._dirty:
            self._rebuild()
        _, lv = self._arr[side]
        return [l for l in lv if l.available_from <= bar_open and (l.expires_at is None or bar_open < l.expires_at)]

    def penetrated(self, side: str, bar_open: pd.Timestamp, high: float, low: float, tick: float) -> List[Level]:
        """Eligible levels penetrated by at least one tick on this candle."""
        cands = self.eligible(side, bar_open)
        if side == BUY:
            return [l for l in cands if high >= l.price + tick]
        return [l for l in cands if low <= l.price - tick]

    def active_count(self) -> int:
        return len(self._active)


# ------------------------------------------------------------------ pivot detection
class PivotDetector:
    """Streaming 2-left/2-right (configurable) pivot detector with ties allowed (>=).
    ``feed`` returns (pivot_high_price, pivot_low_price, pivot_bar_ts) for the candidate
    bar ``right`` bars back, or None values when that bar is not a pivot."""

    def __init__(self, left: int, right: int):
        self.left, self.right = left, right
        self.hi: List[float] = []; self.lo: List[float] = []; self.ts: List[pd.Timestamp] = []

    def feed(self, ts: pd.Timestamp, high: float, low: float) -> Tuple[Optional[float], Optional[float], Optional[pd.Timestamp]]:
        self.hi.append(high); self.lo.append(low); self.ts.append(ts)
        n = self.left + self.right + 1
        if len(self.hi) > n:
            del self.hi[0]; del self.lo[0]; del self.ts[0]
        if len(self.hi) < n:
            return None, None, None
        c = self.left
        ph = self.hi[c] if all(self.hi[c] >= x for i, x in enumerate(self.hi) if i != c) else None
        pl = self.lo[c] if all(self.lo[c] <= x for i, x in enumerate(self.lo) if i != c) else None
        return ph, pl, self.ts[c]

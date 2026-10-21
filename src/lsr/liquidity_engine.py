"""Faithful Python port of the Pine Script v6 indicator ``engine/bsl_ssl.pine``
(Buy/Sell-Side Liquidity).

This module reproduces the indicator's *state* bar by bar: the parallel arrays of
levels per side, their swept / equal / reclaim flags, the FIFO eviction cap, and
the per-bar events (new level, sweep, reclaim). Drawing objects (lines, labels,
table) are not reproduced because they never feed back into state.

The order of operations inside one bar follows the Pine source exactly:

1. pivot detection for the candidate bar ``swing_len`` bars back
2. push a new buy-side level (and equal-high marking, then eviction)
3. push a new sell-side level (and equal-low marking, then eviction)
4. buy-side loop, newest to oldest: sweep test, or reclaim test if already swept
5. sell-side loop, newest to oldest: same

Only closed bars are ever fed in, so the port is causal by construction.

One detail of ``ta.pivothigh`` / ``ta.pivotlow`` is not documented by
TradingView: how a candidate pivot is treated when a neighbouring bar has an
*equal* high (or low). ``PivotTieRule`` makes that choice explicit. The parity
test against a TradingView export (``tests/test_engine_parity.py``) established
empirically that TradingView accepts an equal bar on the LEFT of the candidate
and rejects an equal bar on the RIGHT (``LEFT_GE_RIGHT_STRICT``): of two equal
highs, the later one becomes the pivot. That is the default.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class PivotTieRule(str, Enum):
    """How ``ta.pivothigh(len, len)`` treats neighbours equal to the candidate.

    ``STRICT_BOTH``: candidate must be strictly greater than every bar on both
    sides. ``LEFT_STRICT_RIGHT_GE``: strictly greater than the left bars,
    greater-or-equal to the right bars. ``LEFT_GE_RIGHT_STRICT`` is the mirror.
    ``GE_BOTH``: greater-or-equal on both sides.
    """

    STRICT_BOTH = "strict_both"
    LEFT_STRICT_RIGHT_GE = "left_strict_right_ge"
    LEFT_GE_RIGHT_STRICT = "left_ge_right_strict"
    GE_BOTH = "ge_both"

    @property
    def left_strict(self) -> bool:
        return self in (PivotTieRule.STRICT_BOTH, PivotTieRule.LEFT_STRICT_RIGHT_GE)

    @property
    def right_strict(self) -> bool:
        return self in (PivotTieRule.STRICT_BOTH, PivotTieRule.LEFT_GE_RIGHT_STRICT)


@dataclass
class EngineParams:
    """Mirror of the indicator inputs that affect state."""

    swing_len: int = 5            # "Swing Strength"
    max_levels: int = 8           # "Max Levels per Side"
    sweep_mode: str = "Wick"      # "Sweep Trigger": "Wick" | "Close"
    on_sweep: str = "Keep & recolor"  # "On Sweep": "Keep & recolor" | "Delete"
    reclaim_on: bool = True       # "Flag Sweep + Reclaim"
    eq_on: bool = True            # "Detect Equal Highs/Lows"
    eq_ticks: int = 4             # "Equal Tolerance (ticks)"
    show_bsl: bool = True
    show_ssl: bool = True
    tick_size: float = 0.25       # syminfo.mintick for MNQ
    tie_rule: PivotTieRule = PivotTieRule.LEFT_GE_RIGHT_STRICT

    def __post_init__(self) -> None:
        if self.sweep_mode not in ("Wick", "Close"):
            raise ValueError(f"sweep_mode must be 'Wick' or 'Close', got {self.sweep_mode!r}")
        if self.on_sweep not in ("Keep & recolor", "Delete"):
            raise ValueError(f"on_sweep must be 'Keep & recolor' or 'Delete', got {self.on_sweep!r}")
        if self.swing_len < 1 or self.max_levels < 1:
            raise ValueError("swing_len and max_levels must be >= 1")
        self.tie_rule = PivotTieRule(self.tie_rule)

    @property
    def eq_tol(self) -> float:
        return self.eq_ticks * self.tick_size


@dataclass
class Level:
    """One tracked liquidity level (one slot of the Pine parallel arrays)."""

    price: float
    created_bar: int          # bar index on which the level was pushed (confirmation bar)
    pivot_bar: int            # bar index of the actual swing high/low
    swept: bool = False
    eq: bool = False
    reclaimed: bool = False
    swept_bar: Optional[int] = None
    reclaimed_bar: Optional[int] = None


@dataclass
class BarEvents:
    """What happened on one bar, mirroring the harness export columns."""

    bar: int
    new_bsl_px: Optional[float] = None
    new_ssl_px: Optional[float] = None
    bsl_swept_now: bool = False
    ssl_swept_now: bool = False
    bsl_reclaim_now: bool = False
    ssl_reclaim_now: bool = False
    # Levels swept on this bar (references into the engine state at end of bar).
    bsl_swept_levels: List[Level] = field(default_factory=list)
    ssl_swept_levels: List[Level] = field(default_factory=list)


class LiquidityEngine:
    """Stateful, bar-by-bar port of the indicator. Feed closed bars in order."""

    def __init__(self, params: Optional[EngineParams] = None) -> None:
        self.p = params or EngineParams()
        self.bsl: List[Level] = []
        self.ssl: List[Level] = []
        self._highs: List[float] = []
        self._lows: List[float] = []
        self.bar_index: int = -1

    # ------------------------------------------------------------------ pivots
    def _pivot(self, series: List[float], is_high: bool) -> Optional[float]:
        """Equivalent of ``ta.pivothigh(len, len)`` / ``ta.pivotlow(len, len)``
        evaluated on the current bar. Returns the pivot price or None."""
        n = self.p.swing_len
        t = len(series) - 1
        c = t - n
        if c - n < 0:
            return None
        cand = series[c]
        left = series[c - n:c]
        right = series[c + 1:t + 1]
        ls, rs = self.p.tie_rule.left_strict, self.p.tie_rule.right_strict
        if is_high:
            ok_left = all(cand > x for x in left) if ls else all(cand >= x for x in left)
            ok_right = all(cand > x for x in right) if rs else all(cand >= x for x in right)
        else:
            ok_left = all(cand < x for x in left) if ls else all(cand <= x for x in left)
            ok_right = all(cand < x for x in right) if rs else all(cand <= x for x in right)
        return cand if (ok_left and ok_right) else None

    # ------------------------------------------------------------------- push
    def _push(self, side: List[Level], price: float) -> None:
        is_eq = False
        if self.p.eq_on and side:
            last = side[-1]
            if not last.swept and abs(price - last.price) <= self.p.eq_tol:
                is_eq = True
                last.eq = True
        side.append(Level(price=price, created_bar=self.bar_index,
                          pivot_bar=self.bar_index - self.p.swing_len, eq=is_eq))
        if len(side) > self.p.max_levels:
            side.pop(0)  # array.shift: evict the oldest regardless of swept state

    # --------------------------------------------------------------- sweep loop
    def _sweep_loop(self, side: List[Level], high: float, low: float, close: float,
                    is_bsl: bool) -> tuple[bool, bool, List[Level]]:
        taken_now = False
        recl_now = False
        swept_levels: List[Level] = []
        wick = self.p.sweep_mode == "Wick"
        delete = self.p.on_sweep == "Delete"
        # Pine: for i = size-1 to 0 (newest to oldest), with in-loop removal in Delete mode.
        for i in range(len(side) - 1, -1, -1):
            lvl = side[i]
            px = lvl.price
            if not lvl.swept:
                if is_bsl:
                    taken = (high > px) if wick else (close > px)
                else:
                    taken = (low < px) if wick else (close < px)
                if taken:
                    lvl.swept = True
                    lvl.swept_bar = self.bar_index
                    taken_now = True
                    swept_levels.append(lvl)
                    if delete:
                        side.pop(i)
            elif self.p.reclaim_on and not delete and not lvl.reclaimed:
                reclaimed = (close < px) if is_bsl else (close > px)
                if reclaimed:
                    lvl.reclaimed = True
                    lvl.reclaimed_bar = self.bar_index
                    recl_now = True
        return taken_now, recl_now, swept_levels

    # ------------------------------------------------------------------ on_bar
    def on_bar(self, high: float, low: float, close: float) -> BarEvents:
        """Process one *closed* bar. Returns the events for that bar."""
        self.bar_index += 1
        self._highs.append(high)
        self._lows.append(low)
        # Only the trailing 2*len+1 values are ever needed; trim to bound memory.
        keep = 2 * self.p.swing_len + 1
        if len(self._highs) > keep:
            del self._highs[:-keep]
            del self._lows[:-keep]

        ev = BarEvents(bar=self.bar_index)
        ph = self._pivot(self._highs, is_high=True)
        pl = self._pivot(self._lows, is_high=False)

        if self.p.show_bsl and ph is not None:
            self._push(self.bsl, ph)
            ev.new_bsl_px = ph
        if self.p.show_ssl and pl is not None:
            self._push(self.ssl, pl)
            ev.new_ssl_px = pl

        if self.bsl:
            ev.bsl_swept_now, ev.bsl_reclaim_now, ev.bsl_swept_levels = \
                self._sweep_loop(self.bsl, high, low, close, is_bsl=True)
        if self.ssl:
            ev.ssl_swept_now, ev.ssl_reclaim_now, ev.ssl_swept_levels = \
                self._sweep_loop(self.ssl, high, low, close, is_bsl=False)
        return ev

    # --------------------------------------------------------------- snapshots
    def slots(self, side: str) -> List[Level]:
        return list(self.bsl if side == "bsl" else self.ssl)

    def active_levels(self, side: str) -> List[Level]:
        """Un-swept levels on a side, oldest first. These are the 'valid' levels
        the strategy may use on the *next* bar."""
        return [l for l in self.slots(side) if not l.swept]

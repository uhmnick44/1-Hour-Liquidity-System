"""Liquidity-sweep confirmation on a completed 1H candle.

Uses the engine's own sweep events for the candle. In Wick mode the engine
marks a buy-side level swept when ``high > level`` (strict) and a sell-side
level swept when ``low < level`` (strict); only levels that already existed
before the candle can be swept on it. The confirmation adds the same-candle
strict close-back:

* bearish: some swept buy-side level with ``close < level``
* bullish: some swept sell-side level with ``close > level``

A close exactly at the level is not a rejection. If the candle swept levels on
both sides it is skipped entirely, whatever the close did.

EQ is the midpoint of the full candle including wicks and is kept unrounded for
classification; it is rounded only when it becomes a limit price.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import pandas as pd

from .liquidity_engine import BarEvents

SHORT, LONG = -1, 1


@dataclass(frozen=True)
class Signal:
    bar_ts: pd.Timestamp          # 1H bar open time (UTC)
    close_ts: pd.Timestamp        # 1H bar close time (UTC), the earliest moment the setup is eligible
    direction: int                # SHORT (-1) or LONG (+1)
    sweep_high: float
    sweep_low: float
    close: float
    eq: float
    zone: str                     # 'premium' | 'discount' | 'equilibrium'
    entry_type: str               # 'market' | 'limit'
    level_price: float            # most significant qualifying level (highest for bearish, lowest for bullish)
    n_levels: int                 # number of qualifying levels on this candle

    @property
    def extreme(self) -> float:
        """The wick extreme that defines invalidation and the stop."""
        return self.sweep_high if self.direction == SHORT else self.sweep_low


def classify_zone(close: float, eq: float) -> str:
    if close > eq:
        return "premium"
    if close < eq:
        return "discount"
    return "equilibrium"


def entry_type_for(direction: int, zone: str) -> str:
    """Bearish: premium or equilibrium -> market, discount -> limit at EQ.
    Bullish: discount or equilibrium -> market, premium -> limit at EQ."""
    if zone == "equilibrium":
        return "market"
    if direction == SHORT:
        return "market" if zone == "premium" else "limit"
    return "market" if zone == "discount" else "limit"


def evaluate_candle(ev: BarEvents, bar_ts: pd.Timestamp, close_ts: pd.Timestamp,
                    high: float, low: float, close: float) -> Tuple[Optional[Signal], Optional[str]]:
    """Returns (signal, None), (None, skip_reason) or (None, None)."""
    if ev.bsl_swept_now and ev.ssl_swept_now:
        return None, "dual_side_sweep"
    bear = [l.price for l in ev.bsl_swept_levels if close < l.price]
    bull = [l.price for l in ev.ssl_swept_levels if close > l.price]
    if bear and bull:  # cannot happen when the dual-side check above holds; kept as a guard
        return None, "dual_side_sweep"
    if not bear and not bull:
        if ev.bsl_swept_now or ev.ssl_swept_now:
            return None, "sweep_without_close_back"
        return None, None
    direction = SHORT if bear else LONG
    levels = bear if bear else bull
    eq = (high + low) / 2.0
    zone = classify_zone(close, eq)
    return Signal(bar_ts=bar_ts, close_ts=close_ts, direction=direction, sweep_high=high, sweep_low=low,
                  close=close, eq=eq, zone=zone, entry_type=entry_type_for(direction, zone),
                  level_price=max(levels) if direction == SHORT else min(levels), n_levels=len(levels)), None

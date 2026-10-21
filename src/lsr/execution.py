"""Order and position simulation over 1-minute bars.

Conventions. ``direction`` is -1 for short, +1 for long, so one formula serves
both sides: a quantity ``direction * (price - reference)`` is positive when
``price`` is on the favourable side of ``reference`` for the position.

Execution model (all approved 2026-10-21):
* Market entry: raw open of the first 1-minute bar after the signal's 1H close.
  The raw open is tested against the zone (short needs open >= EQ, long needs
  open <= EQ, equality allowed). Fill = open moved ``slippage_ticks`` against us.
  Stop and target are computed from the slipped fill.
* Limit entry at EQ, rounded up for a sell limit and down for a buy limit. It
  fills when a 1-minute bar trades through it by at least one tick (sell: high
  >= limit + tick; buy: low <= limit - tick) at the limit price with no
  slippage, or at the bar's open when the open is already through the limit
  (price improvement). It is cancelled when price breaches the sweep candle's
  wick extreme strictly, or when the third completed 1H candle after the sweep
  candle closes without a fill, or at a flatten cutoff.
* Within one 1-minute bar the open is the first trade, so an event decided by
  the open is never ambiguous. Anything else that needs an intrabar order is
  resolved adverse-first: invalidation before fill, stop before target. Such
  bars are flagged.
* Stop: stop-market, triggers when price trades at or through it, fills with
  ``slippage_ticks`` against us, or at the open when the open gaps through it.
* Target: limit, trade-through by one tick at the target price, or at the open
  when the open gaps through it. No slippage.
* Flatten: market at the open of the first bar at or after the cutoff, with
  slippage. If the session ends without such a bar, the last bar's close is
  used and flagged.
* Sizing: contracts = floor(risk_budget / (stop_distance * point_value +
  round-trip fees + stop-exit slippage cost)), capped. The entry slippage is
  already inside the fill price from which the stop distance is measured, so it
  is not added a second time. Risk budget = risk_fraction * realized equity.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

import pandas as pd

from .config import BacktestConfig
from .sessions import Session
from .signals import Signal, SHORT, LONG


@dataclass
class MinuteBar:
    ts: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    session: int
    contract: str
    cum_offset: float


@dataclass
class PendingOrder:
    signal: Signal
    kind: str                     # 'market' | 'limit'
    created_ts: pd.Timestamp
    limit_price: Optional[float]  # adjusted price, tick-valid (limit only)
    planned_contracts: int        # limit only (sized at placement)
    planned_stop_distance: float  # limit only
    planned_risk_usd: float       # limit only
    equity_at_creation: float
    candles_elapsed: int = 0


@dataclass
class Position:
    signal: Signal
    entry_type: str
    direction: int
    entry_ts: pd.Timestamp
    entry_price: float            # adjusted, slipped where applicable
    raw_reference: float          # raw open (market) or limit price before slippage
    entry_slippage_ticks: int
    stop: float
    target: float
    stop_distance: float
    contracts: int
    planned_risk_usd: float
    planned_risk_per_contract: float
    equity_at_entry: float
    contract: str
    cum_offset: float
    flags: List[str] = field(default_factory=list)
    order_created_ts: Optional[pd.Timestamp] = None
    gap_fill: bool = False


@dataclass
class TradeRecord:
    trade_id: int
    signal_bar_ts: pd.Timestamp
    signal_close_ts: pd.Timestamp
    direction: str
    entry_type: str
    zone: str
    level_price: float
    n_levels: int
    sweep_high: float
    sweep_low: float
    signal_close: float
    eq: float
    order_created_ts: pd.Timestamp
    limit_price: Optional[float]
    entry_ts: pd.Timestamp
    entry_price: float
    entry_price_raw: float
    contract: str
    entry_slippage_ticks: int
    gap_fill: bool
    stop: float
    target: float
    stop_distance: float
    contracts: int
    planned_risk_per_contract: float
    planned_risk_usd: float
    equity_at_entry: float
    exit_ts: pd.Timestamp
    exit_price: float
    exit_price_raw: float
    exit_reason: str
    exit_slippage_ticks: int
    pnl_points: float
    gross_pnl_usd: float
    fees_usd: float
    net_pnl_usd: float
    r_net: float
    r_price: float
    equity_after: float
    minutes_held: float
    trade_flags: str


@dataclass
class OrderEvent:
    """Non-trade outcomes: cancelled pending orders and skipped setups."""
    ts: pd.Timestamp
    signal_bar_ts: Optional[pd.Timestamp]
    direction: Optional[str]
    entry_type: Optional[str]
    outcome: str                  # 'expired' | 'invalidated' | 'flatten_cancel' | 'skipped' | ...
    reason: str
    detail: str = ""


class Simulator:
    def __init__(self, cfg: BacktestConfig, sessions: List[Session]):
        self.cfg = cfg
        self.sessions = sessions
        self.equity = cfg.risk.starting_equity
        self.pending: Optional[PendingOrder] = None
        self.position: Optional[Position] = None
        self.trades: List[TradeRecord] = []
        self.events: List[OrderEvent] = []
        self.ambiguity: Dict[str, int] = {"fill_vs_invalidation": 0, "stop_vs_target": 0, "entry_and_exit_same_minute": 0}
        self._last_bar: Optional[MinuteBar] = None
        self._trade_seq = 0
        self.equity_curve: List[tuple] = [(None, cfg.risk.starting_equity)]

    # ------------------------------------------------------------ helpers
    @property
    def tick(self) -> float:
        return self.cfg.instrument.tick_size

    @property
    def slip(self) -> float:
        return self.cfg.costs.slippage_ticks * self.tick

    @property
    def occupied(self) -> bool:
        return self.pending is not None or self.position is not None

    def _dir_name(self, d: int) -> str:
        return "short" if d == SHORT else "long"

    def risk_per_contract(self, stop_distance: float) -> float:
        c = self.cfg
        return stop_distance * c.instrument.point_value + c.costs.fees_round_trip + c.costs.slippage_ticks * c.instrument.tick_value

    def size(self, stop_distance: float, equity: float) -> tuple[int, float, float]:
        rpc = self.risk_per_contract(stop_distance)
        budget = equity * self.cfg.risk.risk_fraction
        n = math.floor(budget / rpc + 1e-12)
        n = min(n, self.cfg.risk.max_contracts, self.cfg.instrument.max_contracts)
        return n, rpc, budget

    def stop_and_target(self, direction: int, fill: float, extreme: float) -> tuple[float, float, float]:
        """Returns (stop, target, stop_distance). stop_distance <= 0 means invalid."""
        d = direction * (fill - extreme)
        dist = 2.0 * d
        stop = fill - direction * dist
        target = fill + direction * dist
        return stop, target, dist

    def _record_event(self, ts, sig: Optional[Signal], outcome: str, reason: str, detail: str = ""):
        self.events.append(OrderEvent(ts=ts, signal_bar_ts=sig.bar_ts if sig else None,
                                      direction=self._dir_name(sig.direction) if sig else None,
                                      entry_type=sig.entry_type if sig else None, outcome=outcome, reason=reason, detail=detail))

    # ----------------------------------------------------- signal handling
    def on_signal(self, sig: Signal, session: Session) -> None:
        """Called at the 1H close that confirmed the setup."""
        if self.occupied:
            self._record_event(sig.close_ts, sig, "skipped", "occupied")
            return
        if session.flatten_at is not None and sig.close_ts >= session.flatten_at:
            self._record_event(sig.close_ts, sig, "skipped", "pre_closure_window")
            return
        if sig.entry_type == "market":
            self.pending = PendingOrder(signal=sig, kind="market", created_ts=sig.close_ts, limit_price=None,
                                        planned_contracts=0, planned_stop_distance=0.0, planned_risk_usd=0.0,
                                        equity_at_creation=self.equity)
            return
        # limit at EQ: sell limit rounds up, buy limit rounds down
        lp = self.cfg.instrument.round_to_tick(sig.eq, "up" if sig.direction == SHORT else "down")
        stop, target, dist = self.stop_and_target(sig.direction, lp, sig.extreme)
        if dist <= 0:
            self._record_event(sig.close_ts, sig, "skipped", "invalid_stop", f"limit {lp} extreme {sig.extreme}")
            return
        if dist < self.cfg.risk.min_stop_points:
            self._record_event(sig.close_ts, sig, "skipped", "min_stop", f"dist {dist}")
            return
        n, rpc, budget = self.size(dist, self.equity)
        if n < 1:
            self._record_event(sig.close_ts, sig, "skipped", "size_below_min", f"rpc {rpc:.2f} budget {budget:.2f}")
            return
        self.pending = PendingOrder(signal=sig, kind="limit", created_ts=sig.close_ts, limit_price=lp,
                                    planned_contracts=n, planned_stop_distance=dist, planned_risk_usd=n * rpc,
                                    equity_at_creation=self.equity)

    def on_hour_close(self, close_ts: pd.Timestamp) -> None:
        """Called at every 1H close before the new candle is evaluated."""
        p = self.pending
        if p is None or p.kind != "limit" or close_ts <= p.created_ts:
            return
        p.candles_elapsed += 1
        if p.candles_elapsed >= self.cfg.strategy.limit_window_candles:
            self._record_event(close_ts, p.signal, "expired", "limit_window_elapsed")
            self.pending = None

    # ------------------------------------------------------- minute bars
    def on_minute(self, bar: MinuteBar) -> None:
        prev = self._last_bar
        # session rollover: enforce a missed flatten using the previous session's last bar
        if prev is not None and bar.session != prev.session:
            ps = self.sessions[prev.session]
            if ps.flatten_at is not None:
                if self.position is not None:
                    self.position.flags.append("flatten_forced_last_bar")
                    self._close(prev, prev.close - self.position.direction * self.slip, "flatten", self.cfg.costs.slippage_ticks,
                                ts=prev.ts + pd.Timedelta(minutes=1))
                if self.pending is not None:
                    self._record_event(prev.ts + pd.Timedelta(minutes=1), self.pending.signal, "flatten_cancel", "flatten_forced_last_bar")
                    self.pending = None
        self._last_bar = bar
        sess = self.sessions[bar.session]
        flatten_due = sess.flatten_at is not None and bar.ts >= sess.flatten_at

        if self.position is not None:
            self._manage_position(bar, flatten_due, from_open=True)
        elif self.pending is not None:
            if flatten_due:
                self._record_event(bar.ts, self.pending.signal, "flatten_cancel", "flatten_cutoff")
                self.pending = None
            elif self.pending.kind == "market":
                self._execute_market(bar)
            else:
                self._try_limit(bar)

    # ---------------------------------------------------------- entries
    def _execute_market(self, bar: MinuteBar) -> None:
        p = self.pending; sig = p.signal; d = sig.direction
        self.pending = None
        if d * (bar.open - sig.eq) > 0:
            # short: open below EQ; long: open above EQ -> outside the permitted zone
            self._record_event(bar.ts, sig, "skipped", "market_open_outside_zone", f"open {bar.open} eq {sig.eq}")
            return
        fill = bar.open + d * self.slip
        stop, target, dist = self.stop_and_target(d, fill, sig.extreme)
        if dist <= 0:
            self._record_event(bar.ts, sig, "skipped", "invalid_stop", f"fill {fill} extreme {sig.extreme}")
            return
        if dist < self.cfg.risk.min_stop_points:
            self._record_event(bar.ts, sig, "skipped", "min_stop", f"dist {dist}")
            return
        n, rpc, budget = self.size(dist, self.equity)
        if n < 1:
            self._record_event(bar.ts, sig, "skipped", "size_below_min", f"rpc {rpc:.2f} budget {budget:.2f}")
            return
        self.position = Position(signal=sig, entry_type="market", direction=d, entry_ts=bar.ts, entry_price=fill,
                                 raw_reference=bar.open, entry_slippage_ticks=self.cfg.costs.slippage_ticks, stop=stop,
                                 target=target, stop_distance=dist, contracts=n, planned_risk_usd=n * rpc,
                                 planned_risk_per_contract=rpc, equity_at_entry=self.equity, contract=bar.contract,
                                 cum_offset=bar.cum_offset, order_created_ts=p.created_ts)
        self._manage_position(bar, False, from_open=False)

    def _try_limit(self, bar: MinuteBar) -> None:
        p = self.pending; sig = p.signal; d = sig.direction; L = p.limit_price; X = sig.extreme
        adv = bar.high if d == SHORT else bar.low      # price moving against the pending thesis
        fav = bar.high if d == SHORT else bar.low      # for a sell limit the favourable extreme is the high
        # 1. open decides
        if d * (bar.open - X) < 0:
            self._record_event(bar.ts, sig, "invalidated", "open_beyond_extreme", f"open {bar.open} extreme {X}")
            self.pending = None
            return
        if d * (bar.open - L) < 0:
            fill = bar.open
            if fill == X:
                self._record_event(bar.ts, sig, "invalidated", "gap_fill_at_extreme", f"open {bar.open}")
                self.pending = None
                return
            self._open_from_limit(bar, fill, gap=True)
            return
        # 2. intrabar
        invalid = d * (adv - X) < 0
        filled = d * (fav - L) <= -self.tick
        if invalid and filled:
            self.ambiguity["fill_vs_invalidation"] += 1
            self._record_event(bar.ts, sig, "invalidated", "ambiguous_fill_vs_invalidation", f"high/low beyond both limit and extreme")
            self.pending = None
            return
        if invalid:
            self._record_event(bar.ts, sig, "invalidated", "wick_extreme_breached", f"adv {adv} extreme {X}")
            self.pending = None
            return
        if filled:
            self._open_from_limit(bar, L, gap=False)

    def _open_from_limit(self, bar: MinuteBar, fill: float, gap: bool) -> None:
        p = self.pending; sig = p.signal; d = sig.direction
        self.pending = None
        stop, target, dist = self.stop_and_target(d, fill, sig.extreme)
        flags = []
        if gap:
            flags.append("gap_fill")
            if dist < self.cfg.risk.min_stop_points:
                flags.append("stop_below_min_after_gap_fill")
        n = p.planned_contracts
        rpc = self.risk_per_contract(dist)
        self.position = Position(signal=sig, entry_type="limit", direction=d, entry_ts=bar.ts, entry_price=fill,
                                 raw_reference=p.limit_price, entry_slippage_ticks=0, stop=stop, target=target,
                                 stop_distance=dist, contracts=n, planned_risk_usd=p.planned_risk_usd,
                                 planned_risk_per_contract=p.planned_risk_usd / n, equity_at_entry=p.equity_at_creation,
                                 contract=bar.contract, cum_offset=bar.cum_offset, flags=flags,
                                 order_created_ts=p.created_ts, gap_fill=gap)
        self._manage_position(bar, False, from_open=False)

    # ----------------------------------------------------------- exits
    def _manage_position(self, bar: MinuteBar, flatten_due: bool, from_open: bool) -> None:
        pos = self.position; d = pos.direction; S = pos.stop; T = pos.target
        slip_ticks = self.cfg.costs.slippage_ticks
        if from_open:
            if flatten_due:
                self._close(bar, bar.open - d * self.slip, "flatten", slip_ticks)
                return
            if d * (bar.open - S) <= 0:
                pos.flags.append("gap_stop")
                self._close(bar, bar.open - d * self.slip, "stop", slip_ticks)
                return
            if d * (bar.open - T) >= self.tick:
                pos.flags.append("gap_target")
                self._close(bar, bar.open, "target", 0)
                return
        adv = bar.high if d == SHORT else bar.low
        fav = bar.low if d == SHORT else bar.high
        stop_hit = d * (adv - S) <= 0
        tp_hit = d * (fav - T) >= self.tick
        if stop_hit and tp_hit:
            self.ambiguity["stop_vs_target"] += 1
            pos.flags.append("ambiguous_stop_vs_target")
        if stop_hit:
            if not from_open:
                self.ambiguity["entry_and_exit_same_minute"] += 1; pos.flags.append("entry_and_exit_same_minute")
            self._close(bar, S - d * self.slip, "stop", slip_ticks)
        elif tp_hit:
            if not from_open:
                self.ambiguity["entry_and_exit_same_minute"] += 1; pos.flags.append("entry_and_exit_same_minute")
            self._close(bar, T, "target", 0)

    def _close(self, bar: MinuteBar, exit_price: float, reason: str, exit_slip_ticks: int, ts: Optional[pd.Timestamp] = None) -> None:
        pos = self.position; c = self.cfg
        ts = ts or bar.ts
        pnl_pts = pos.direction * (exit_price - pos.entry_price)
        gross = pnl_pts * c.instrument.point_value * pos.contracts
        fees = c.costs.fees_round_trip * pos.contracts
        net = gross - fees
        self.equity += net
        self._trade_seq += 1
        self.trades.append(TradeRecord(
            trade_id=self._trade_seq, signal_bar_ts=pos.signal.bar_ts, signal_close_ts=pos.signal.close_ts,
            direction=self._dir_name(pos.direction), entry_type=pos.entry_type, zone=pos.signal.zone,
            level_price=pos.signal.level_price, n_levels=pos.signal.n_levels, sweep_high=pos.signal.sweep_high,
            sweep_low=pos.signal.sweep_low, signal_close=pos.signal.close, eq=pos.signal.eq,
            order_created_ts=pos.order_created_ts, limit_price=pos.raw_reference if pos.entry_type == "limit" else None,
            entry_ts=pos.entry_ts, entry_price=pos.entry_price, entry_price_raw=pos.entry_price - pos.cum_offset,
            contract=pos.contract, entry_slippage_ticks=pos.entry_slippage_ticks, gap_fill=pos.gap_fill,
            stop=pos.stop, target=pos.target, stop_distance=pos.stop_distance, contracts=pos.contracts,
            planned_risk_per_contract=pos.planned_risk_per_contract, planned_risk_usd=pos.planned_risk_usd,
            equity_at_entry=pos.equity_at_entry, exit_ts=ts, exit_price=exit_price, exit_price_raw=exit_price - bar.cum_offset,
            exit_reason=reason, exit_slippage_ticks=exit_slip_ticks, pnl_points=pnl_pts, gross_pnl_usd=gross,
            fees_usd=fees, net_pnl_usd=net, r_net=net / pos.planned_risk_usd if pos.planned_risk_usd else float("nan"),
            r_price=pnl_pts / pos.stop_distance if pos.stop_distance else float("nan"), equity_after=self.equity,
            minutes_held=(ts - pos.entry_ts).total_seconds() / 60.0, trade_flags=",".join(pos.flags)))
        self.equity_curve.append((ts, self.equity))
        self.position = None

    def finish(self) -> None:
        bar = self._last_bar
        if bar is None:
            return
        if self.position is not None:
            self.position.flags.append("end_of_data")
            self._close(bar, bar.close - self.position.direction * self.slip, "end_of_data", self.cfg.costs.slippage_ticks,
                        ts=bar.ts + pd.Timedelta(minutes=1))
        if self.pending is not None:
            self._record_event(bar.ts + pd.Timedelta(minutes=1), self.pending.signal, "flatten_cancel", "end_of_data")
            self.pending = None

    # --------------------------------------------------------- outputs
    def trades_frame(self) -> pd.DataFrame:
        return pd.DataFrame([asdict(t) for t in self.trades])

    def events_frame(self) -> pd.DataFrame:
        return pd.DataFrame([asdict(e) for e in self.events])

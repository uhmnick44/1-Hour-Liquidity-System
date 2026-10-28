"""Configuration for the MNQ 1H Liquidity Sweep Reversal strategy, V1.

Every number here is an approved V1 input. Nothing in this file is tuned by the
backtest. Costs and slippage are required inputs: the defaults are the values
approved on 2026-10-21 (NinjaTrader Free plan) and must be reconciled with
brokerage statements.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class InstrumentSpec:
    symbol: str = "MNQ"
    exchange: str = "CME"
    tick_size: float = 0.25          # index points
    point_value: float = 2.0         # USD per index point per contract
    min_contracts: int = 1
    max_contracts: int = 10

    @property
    def tick_value(self) -> float:
        return self.tick_size * self.point_value

    def round_to_tick(self, px: float, mode: str) -> float:
        """mode: 'up' | 'down' | 'nearest'. Uses integer tick arithmetic to avoid
        floating-point drift."""
        import math
        t = px / self.tick_size
        if mode == "up":
            n = math.ceil(round(t, 9))
        elif mode == "down":
            n = math.floor(round(t, 9))
        elif mode == "nearest":
            n = math.floor(round(t, 9) + 0.5)
        else:
            raise ValueError(mode)
        return n * self.tick_size

    def is_tick_valid(self, px: float) -> bool:
        return abs(round(px / self.tick_size) * self.tick_size - px) < 1e-9


@dataclass(frozen=True)
class CostConfig:
    """Per contract, per side, USD. Slippage in ticks per eligible fill."""
    commission_per_side: float = 0.39
    exchange_nfa_per_side: float = 0.36
    clearing_per_side: float = 0.19
    slippage_ticks: int = 2

    @property
    def fees_per_side(self) -> float:
        return self.commission_per_side + self.exchange_nfa_per_side + self.clearing_per_side

    @property
    def fees_round_trip(self) -> float:
        return 2.0 * self.fees_per_side


@dataclass(frozen=True)
class RiskConfig:
    starting_equity: float = 50_000.0
    risk_fraction: float = 0.01          # of current realized equity
    min_stop_points: float = 10.0        # minimum doubled stop distance
    max_contracts: int = 10


@dataclass(frozen=True)
class StrategyConfig:
    timeframe_minutes: int = 60
    limit_window_candles: int = 3        # completed 1H candles after the sweep candle
    flatten_minutes_before_close: int = 15
    extended_closure_hours: float = 24.0  # closure longer than this triggers a flatten
    roll_business_days_before_expiry: int = 5
    # Engine inputs (verified against the live chart on 2026-10-21)
    swing_len: int = 5
    max_levels: int = 8
    sweep_mode: str = "Wick"
    on_sweep: str = "Keep & recolor"
    # Entry mode. V1 (immutable baseline): "market_and_limit". V2 experiment
    # (approved 2026-10-21): "market_only", which skips every setup that would
    # have produced an EQ limit order and leaves the system available for the
    # next signal. Nothing else differs between V1 and V2.
    entry_mode: str = "market_and_limit"
    # Exit mode. V1/V2: "fixed_1r" (1:1 target, no stop changes). V3 experiment
    # (requested 2026-10-21): "be_at_1r_tp_2r": when price touches +1R the stop
    # moves to the entry fill; the target is a limit at +2R.
    exit_mode: str = "fixed_1r"
    # Stop distance as a multiple of the entry-to-extreme distance. V1/V2/V3 and
    # the first FVG specification use 2.0. The 2026-10-28 FVG update specifies
    # (distance * 2) * 0.5, i.e. 1.0: the stop sits at the reversal wick.
    stop_multiple: float = 2.0

    def __post_init__(self) -> None:
        if self.stop_multiple <= 0:
            raise ValueError("stop_multiple must be positive")
        if self.entry_mode not in ("market_and_limit", "market_only"):
            raise ValueError(f"unknown entry_mode {self.entry_mode!r}")
        if self.exit_mode not in ("fixed_1r", "be_at_1r_tp_2r"):
            raise ValueError(f"unknown exit_mode {self.exit_mode!r}")


@dataclass(frozen=True)
class FvgConfig:
    """1H sweep -> 1M FVG strategy (specification 2026-10-28).

    The four Section 16 decisions were approved by the user on 2026-10-28:
    intrabar sweep timestamp, 1:1 target from the fill, keep the 10-point
    minimum doubled stop, one active setup / order / position at a time.
    """
    window_minutes: int = 15
    # APPROVED: the sweep timestamp is the close of the first 1-minute bar
    # through the level (how the Pine alert fires live). "h1_close" is kept
    # for comparison only.
    sweep_timestamp_mode: str = "intrabar_1m"
    # APPROVED: existing exit rule, 1:1 target from the actual fill.
    take_profit: str = "existing_fixed_1r"
    # APPROVED: existing 10-point minimum doubled stop applies.
    apply_existing_min_stop: bool = True
    # APPROVED: one active setup, order or position; new sweeps are ignored while occupied.
    ignore_sweeps_while_occupied: bool = True
    # Optional entry session, New York wall-clock "HH:MM". When set, a sweep outside
    # [start, end] creates no setup and an FVG confirming outside it is rejected, so
    # the entry open is never later than `end`. Open positions are not time-exited.
    session_start: Optional[str] = None
    session_end: Optional[str] = None


@dataclass(frozen=True)
class DataConfig:
    """One Databento batch. ``front_contracts`` is the liquid front-month chain in
    expiry order; back months in the batch that never become front are ignored."""
    name: str = "2025_2026"
    databento_dir: Path = REPO_ROOT / "data" / "databento"
    front_contracts: Tuple[str, ...] = ("MNQZ5", "MNQH6", "MNQM6", "MNQU6", "MNQZ6")
    start_utc: str = "2025-10-01T00:00:00Z"
    end_utc: str = "2026-10-21T00:00:00Z"


DATASETS = {
    # The year V1 was specified on and V2/V3 were selected from. Development + out-of-sample split.
    "2025_2026": DataConfig(),
    # Clean history for testing the frozen V2 rule. Ends before 2025-10-01 so nothing overlaps.
    "2022_2025": DataConfig(name="2022_2025", databento_dir=REPO_ROOT / "data" / "databento_2022_2025",
                            front_contracts=("MNQZ2", "MNQH3", "MNQM3", "MNQU3", "MNQZ3", "MNQH4", "MNQM4", "MNQU4",
                                             "MNQZ4", "MNQH5", "MNQM5", "MNQU5", "MNQZ5"),
                            start_utc="2022-10-02T00:00:00Z", end_utc="2025-10-01T00:00:00Z"),
}


@dataclass(frozen=True)
class SplitConfig:
    """Chronological split fixed before the first run: first two-thirds of the
    calendar span is development, the final third is out-of-sample."""
    dev_fraction: float = 2.0 / 3.0


# Explicit calendar overrides. Each entry: session date (YYYY-MM-DD, exchange
# local date of the close) -> (close time 'HH:MM' America/New_York, source note).
_VERIFIED = ("User-verified CME Equity Index Globex close 1:15 PM ET (2026-10-21). Databento and TradingView "
             "both show the last traded minute at 13:14 ET. pandas_market_calendars CME_Equity 5.5.0 says 13:00 ET.")
_PRE_HOLIDAY = ("Day-before-holiday early close. Databento shows the last traded minute at 13:14 ET; the calendar "
                "library says 13:00 ET. Same convention as the two user-verified 2025 dates. PENDING user verification "
                "against CME's holiday schedule for that year.")
CALENDAR_OVERRIDES: Dict[str, Tuple[str, str]] = {
    "2025-11-28": ("13:15", _VERIFIED),
    "2025-12-24": ("13:15", _VERIFIED),
    "2022-11-25": ("13:15", _PRE_HOLIDAY),   # day after Thanksgiving
    "2023-07-03": ("13:15", _PRE_HOLIDAY),   # day before Independence Day
    "2023-11-24": ("13:15", _PRE_HOLIDAY),
    "2024-07-03": ("13:15", _PRE_HOLIDAY),
    "2024-11-29": ("13:15", _PRE_HOLIDAY),
    "2024-12-24": ("13:15", _PRE_HOLIDAY),   # Christmas Eve
    "2025-07-03": ("13:15", _PRE_HOLIDAY),
}

# Sessions the calendar library omits entirely. date -> (open, close, note), times America/New_York.
ADDED_SESSIONS: Dict[str, Tuple[str, str, str]] = {
    "2025-01-09": ("2025-01-08 18:00", "2025-01-09 09:30",
                   "National Day of Mourning (Carter). NYSE closed; the library marks CME closed. Databento shows "
                   "CME equity index futures trading from 18:00 ET on 01-08 to 09:29 ET on 01-09, then reopening "
                   "18:00 ET for the 01-10 session. PENDING user verification against CME's notice."),
}


@dataclass(frozen=True)
class BacktestConfig:
    instrument: InstrumentSpec = field(default_factory=InstrumentSpec)
    costs: CostConfig = field(default_factory=CostConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    data: DataConfig = field(default_factory=DataConfig)
    split: SplitConfig = field(default_factory=SplitConfig)
    fvg: FvgConfig = field(default_factory=FvgConfig)

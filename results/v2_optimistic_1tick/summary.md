# v2_optimistic_1tick
Slippage 1 ticks per eligible fill, fees $0.94 per side, starting equity $50,000, risk 1%, max 10 contracts.
Data: 6228 1H bars from 2025-10-01 00:00:00+00:00 to 2026-10-21 00:00:00+00:00. Split boundary 2026-06-14 12:00:00-04:00.

## Development period

| Metric | Value |
|---|---|
| Trades | 83 |
| Wins / losses | 48 / 35 |
| Win rate | 57.8% (95% CI 47.1% to 67.9%) |
| Avg win R / avg loss R | 0.939 / -0.973 |
| Expectancy R | +0.133 (95% CI -0.084 to +0.333) |
| Profit factor | 1.31 |
| Net profit after costs | $4,486.88 |
| Fees / price slippage | $750.12 / $292.00 |
| Ending equity | $54,486.88 |
| Max drawdown | $-3,308.36 (-6.4%) |
| Longest losing streak | 5 |
| Avg contracts / avg planned risk | 4.81 / 0.82% of equity |
| Exits | target 47, stop 34, flatten 2 |
| Signals | 186 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'limit_entries_disabled': 95, 'size_below_min': 4, 'min_stop': 2, 'occupied': 2, 'dual_side_sweep': 1} |

## Out-of-sample period

| Metric | Value |
|---|---|
| Trades | 37 |
| Wins / losses | 20 / 17 |
| Win rate | 54.1% (95% CI 38.4% to 69.0%) |
| Avg win R / avg loss R | 0.959 / -1.000 |
| Expectancy R | +0.059 (95% CI -0.259 to +0.377) |
| Profit factor | 1.24 |
| Net profit after costs | $1,693.38 |
| Fees / price slippage | $233.12 / $78.50 |
| Ending equity | $56,180.26 |
| Max drawdown | $-3,088.24 (-5.6%) |
| Longest losing streak | 6 |
| Avg contracts / avg planned risk | 3.35 / 0.82% of equity |
| Exits | target 20, stop 17 |
| Signals | 82 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'limit_entries_disabled': 39, 'size_below_min': 3, 'occupied': 1, 'pre_closure_window': 1, 'market_open_outside_zone': 1} |

## Full sample

| Metric | Value |
|---|---|
| Trades | 120 |
| Wins / losses | 68 / 52 |
| Win rate | 56.7% (95% CI 47.7% to 65.2%) |
| Avg win R / avg loss R | 0.945 / -0.982 |
| Expectancy R | +0.110 (95% CI -0.066 to +0.278) |
| Profit factor | 1.29 |
| Net profit after costs | $6,180.26 |
| Fees / price slippage | $983.24 / $370.50 |
| Ending equity | $56,180.26 |
| Max drawdown | $-3,308.36 (-6.4%) |
| Longest losing streak | 6 |
| Avg contracts / avg planned risk | 4.36 / 0.82% of equity |
| Exits | target 67, stop 51, flatten 2 |
| Signals | 268 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'limit_entries_disabled': 134, 'size_below_min': 7, 'occupied': 3, 'min_stop': 2, 'dual_side_sweep': 1, 'pre_closure_window': 1, 'market_open_outside_zone': 1} |

Ambiguous 1-minute sequences: {'fill_vs_invalidation': 0, 'stop_vs_target': 0, 'entry_and_exit_same_minute': 2}. Flagged trades: {'entry_and_exit_same_minute': 2}.

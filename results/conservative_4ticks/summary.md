# conservative_4ticks
Slippage 4 ticks per eligible fill, fees $0.94 per side, starting equity $50,000, risk 1%, max 10 contracts.
Data: 6228 1H bars from 2025-10-01 00:00:00+00:00 to 2026-10-21 00:00:00+00:00. Split boundary 2026-06-14 12:00:00-04:00.

## Development period

| Metric | Value |
|---|---|
| Trades | 147 |
| Wins / losses | 68 / 79 |
| Win rate | 46.3% (95% CI 38.4% to 54.3%) |
| Avg win R / avg loss R | 0.937 / -0.967 |
| Expectancy R | -0.086 (95% CI -0.237 to +0.068) |
| Profit factor | 0.86 |
| Net profit after costs | $-4,164.62 |
| Fees / price slippage | $985.12 / $1,238.00 |
| Ending equity | $45,835.38 |
| Max drawdown | $-5,949.88 (-11.6%) |
| Longest losing streak | 7 |
| Avg contracts / avg planned risk | 3.56 / 0.81% of equity |
| Exits | stop 76, target 67, flatten 4 |
| Signals | 186 |
| Limit orders placed / filled | 87 / 72 (82.8%) |
| Expired / invalidated / cancelled at flatten | 14 / 1 / 0 |
| Skipped setups | {'size_below_min': 12, 'occupied': 11, 'min_stop': 1, 'dual_side_sweep': 1} |

## Out-of-sample period

| Metric | Value |
|---|---|
| Trades | 60 |
| Wins / losses | 30 / 30 |
| Win rate | 50.0% (95% CI 37.7% to 62.3%) |
| Avg win R / avg loss R | 0.954 / -1.000 |
| Expectancy R | -0.023 (95% CI -0.281 to +0.237) |
| Profit factor | 1.05 |
| Net profit after costs | $547.04 |
| Fees / price slippage | $266.96 / $284.00 |
| Ending equity | $46,382.42 |
| Max drawdown | $-3,267.60 (-7.0%) |
| Longest losing streak | 6 |
| Avg contracts / avg planned risk | 2.37 / 0.80% of equity |
| Exits | target 30, stop 30 |
| Signals | 82 |
| Limit orders placed / filled | 31 / 27 (87.1%) |
| Expired / invalidated / cancelled at flatten | 4 / 0 / 0 |
| Skipped setups | {'size_below_min': 10, 'occupied': 5, 'min_stop': 1, 'pre_closure_window': 1, 'market_open_outside_zone': 1} |

## Full sample

| Metric | Value |
|---|---|
| Trades | 207 |
| Wins / losses | 98 / 109 |
| Win rate | 47.3% (95% CI 40.7% to 54.1%) |
| Avg win R / avg loss R | 0.943 / -0.976 |
| Expectancy R | -0.068 (95% CI -0.199 to +0.060) |
| Profit factor | 0.91 |
| Net profit after costs | $-3,617.58 |
| Fees / price slippage | $1,252.08 / $1,522.00 |
| Ending equity | $46,382.42 |
| Max drawdown | $-7,827.18 (-15.3%) |
| Longest losing streak | 7 |
| Avg contracts / avg planned risk | 3.22 / 0.81% of equity |
| Exits | stop 106, target 97, flatten 4 |
| Signals | 268 |
| Limit orders placed / filled | 118 / 99 (83.9%) |
| Expired / invalidated / cancelled at flatten | 18 / 1 / 0 |
| Skipped setups | {'size_below_min': 22, 'occupied': 16, 'min_stop': 2, 'dual_side_sweep': 1, 'pre_closure_window': 1, 'market_open_outside_zone': 1} |

Ambiguous 1-minute sequences: {'fill_vs_invalidation': 0, 'stop_vs_target': 0, 'entry_and_exit_same_minute': 2}. Flagged trades: {'entry_and_exit_same_minute': 2, 'gap_fill': 1, 'gap_target': 1}.

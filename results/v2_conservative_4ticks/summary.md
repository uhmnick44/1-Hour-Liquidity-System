# v2_conservative_4ticks
Slippage 4 ticks per eligible fill, fees $0.94 per side, starting equity $50,000, risk 1%, max 10 contracts.
Data: 6228 1H bars from 2025-10-01 00:00:00+00:00 to 2026-10-21 00:00:00+00:00. Split boundary 2026-06-14 12:00:00-04:00.

## Development period

| Metric | Value |
|---|---|
| Trades | 84 |
| Wins / losses | 45 / 39 |
| Win rate | 53.6% (95% CI 43.0% to 63.8%) |
| Avg win R / avg loss R | 0.927 / -0.976 |
| Expectancy R | +0.043 (95% CI -0.171 to +0.250) |
| Profit factor | 1.07 |
| Net profit after costs | $1,054.32 |
| Fees / price slippage | $725.68 / $1,172.00 |
| Ending equity | $51,054.32 |
| Max drawdown | $-3,576.60 (-6.9%) |
| Longest losing streak | 5 |
| Avg contracts / avg planned risk | 4.60 / 0.83% of equity |
| Exits | target 44, stop 38, flatten 2 |
| Signals | 186 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'limit_entries_disabled': 95, 'size_below_min': 5, 'min_stop': 1, 'dual_side_sweep': 1, 'occupied': 1} |

## Out-of-sample period

| Metric | Value |
|---|---|
| Trades | 37 |
| Wins / losses | 21 / 16 |
| Win rate | 56.8% (95% CI 40.9% to 71.3%) |
| Avg win R / avg loss R | 0.949 / -1.000 |
| Expectancy R | +0.106 (95% CI -0.210 to +0.421) |
| Profit factor | 1.30 |
| Net profit after costs | $1,888.08 |
| Fees / price slippage | $204.92 / $276.00 |
| Ending equity | $52,942.40 |
| Max drawdown | $-3,233.96 (-6.3%) |
| Longest losing streak | 6 |
| Avg contracts / avg planned risk | 2.95 / 0.81% of equity |
| Exits | target 21, stop 16 |
| Signals | 82 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'limit_entries_disabled': 37, 'size_below_min': 3, 'occupied': 3, 'pre_closure_window': 1, 'market_open_outside_zone': 1} |

## Full sample

| Metric | Value |
|---|---|
| Trades | 121 |
| Wins / losses | 66 / 55 |
| Win rate | 54.5% (95% CI 45.7% to 63.1%) |
| Avg win R / avg loss R | 0.934 / -0.983 |
| Expectancy R | +0.063 (95% CI -0.114 to +0.234) |
| Profit factor | 1.13 |
| Net profit after costs | $2,942.40 |
| Fees / price slippage | $930.60 / $1,448.00 |
| Ending equity | $52,942.40 |
| Max drawdown | $-3,576.60 (-6.9%) |
| Longest losing streak | 6 |
| Avg contracts / avg planned risk | 4.09 / 0.82% of equity |
| Exits | target 65, stop 54, flatten 2 |
| Signals | 268 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'limit_entries_disabled': 132, 'size_below_min': 8, 'occupied': 4, 'min_stop': 1, 'dual_side_sweep': 1, 'pre_closure_window': 1, 'market_open_outside_zone': 1} |

Ambiguous 1-minute sequences: {'fill_vs_invalidation': 0, 'stop_vs_target': 0, 'entry_and_exit_same_minute': 2}. Flagged trades: {'entry_and_exit_same_minute': 2, 'gap_target': 1}.

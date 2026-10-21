# optimistic_1tick
Slippage 1 ticks per eligible fill, fees $0.94 per side, starting equity $50,000, risk 1%, max 10 contracts.
Data: 6228 1H bars from 2025-10-01 00:00:00+00:00 to 2026-10-21 00:00:00+00:00. Split boundary 2026-06-14 12:00:00-04:00.

## Development period

| Metric | Value |
|---|---|
| Trades | 146 |
| Wins / losses | 70 / 76 |
| Win rate | 47.9% (95% CI 40.0% to 56.0%) |
| Avg win R / avg loss R | 0.948 / -0.966 |
| Expectancy R | -0.048 (95% CI -0.201 to +0.106) |
| Profit factor | 0.91 |
| Net profit after costs | $-2,569.06 |
| Fees / price slippage | $1,009.56 / $309.50 |
| Ending equity | $47,430.94 |
| Max drawdown | $-4,547.12 (-8.9%) |
| Longest losing streak | 7 |
| Avg contracts / avg planned risk | 3.68 / 0.80% of equity |
| Exits | stop 73, target 69, flatten 4 |
| Signals | 186 |
| Limit orders placed / filled | 88 / 72 (81.8%) |
| Expired / invalidated / cancelled at flatten | 15 / 1 / 0 |
| Skipped setups | {'occupied': 11, 'size_below_min': 11, 'min_stop': 2, 'dual_side_sweep': 1} |

## Out-of-sample period

| Metric | Value |
|---|---|
| Trades | 63 |
| Wins / losses | 29 / 34 |
| Win rate | 46.0% (95% CI 34.3% to 58.2%) |
| Avg win R / avg loss R | 0.964 / -1.000 |
| Expectancy R | -0.096 (95% CI -0.316 to +0.154) |
| Profit factor | 0.86 |
| Net profit after costs | $-1,734.88 |
| Fees / price slippage | $283.88 / $77.50 |
| Ending equity | $45,696.06 |
| Max drawdown | $-4,545.26 (-9.4%) |
| Longest losing streak | 6 |
| Avg contracts / avg planned risk | 2.40 / 0.80% of equity |
| Exits | stop 34, target 29 |
| Signals | 82 |
| Limit orders placed / filled | 33 / 29 (87.9%) |
| Expired / invalidated / cancelled at flatten | 4 / 0 / 0 |
| Skipped setups | {'size_below_min': 8, 'occupied': 4, 'min_stop': 1, 'pre_closure_window': 1, 'market_open_outside_zone': 1} |

## Full sample

| Metric | Value |
|---|---|
| Trades | 209 |
| Wins / losses | 99 / 110 |
| Win rate | 47.4% (95% CI 40.7% to 54.1%) |
| Avg win R / avg loss R | 0.953 / -0.976 |
| Expectancy R | -0.063 (95% CI -0.195 to +0.068) |
| Profit factor | 0.89 |
| Net profit after costs | $-4,303.94 |
| Fees / price slippage | $1,293.44 / $387.00 |
| Ending equity | $45,696.06 |
| Max drawdown | $-7,531.28 (-14.7%) |
| Longest losing streak | 7 |
| Avg contracts / avg planned risk | 3.29 / 0.80% of equity |
| Exits | stop 107, target 98, flatten 4 |
| Signals | 268 |
| Limit orders placed / filled | 121 / 101 (83.5%) |
| Expired / invalidated / cancelled at flatten | 19 / 1 / 0 |
| Skipped setups | {'size_below_min': 19, 'occupied': 15, 'min_stop': 3, 'dual_side_sweep': 1, 'pre_closure_window': 1, 'market_open_outside_zone': 1} |

Ambiguous 1-minute sequences: {'fill_vs_invalidation': 0, 'stop_vs_target': 0, 'entry_and_exit_same_minute': 2}. Flagged trades: {'entry_and_exit_same_minute': 2, 'gap_fill': 1}.

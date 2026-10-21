# baseline_2ticks
Slippage 2 ticks per eligible fill, fees $0.94 per side, starting equity $50,000, risk 1%, max 10 contracts.
Data: 6228 1H bars from 2025-10-01 00:00:00+00:00 to 2026-10-21 00:00:00+00:00. Split boundary 2026-06-14 12:00:00-04:00.

## Development period

| Metric | Value |
|---|---|
| Trades | 147 |
| Wins / losses | 70 / 77 |
| Win rate | 47.6% (95% CI 39.7% to 55.7%) |
| Avg win R / avg loss R | 0.944 / -0.966 |
| Expectancy R | -0.057 (95% CI -0.208 to +0.098) |
| Profit factor | 0.90 |
| Net profit after costs | $-2,865.08 |
| Fees / price slippage | $1,017.08 / $631.00 |
| Ending equity | $47,134.92 |
| Max drawdown | $-4,577.62 (-8.9%) |
| Longest losing streak | 7 |
| Avg contracts / avg planned risk | 3.68 / 0.80% of equity |
| Exits | stop 74, target 69, flatten 4 |
| Signals | 186 |
| Limit orders placed / filled | 88 / 72 (81.8%) |
| Expired / invalidated / cancelled at flatten | 15 / 1 / 0 |
| Skipped setups | {'occupied': 11, 'size_below_min': 11, 'min_stop': 1, 'dual_side_sweep': 1} |

## Out-of-sample period

| Metric | Value |
|---|---|
| Trades | 62 |
| Wins / losses | 29 / 33 |
| Win rate | 46.8% (95% CI 34.9% to 59.0%) |
| Avg win R / avg loss R | 0.961 / -1.000 |
| Expectancy R | -0.083 (95% CI -0.335 to +0.168) |
| Profit factor | 0.89 |
| Net profit after costs | $-1,341.12 |
| Fees / price slippage | $280.12 / $153.00 |
| Ending equity | $45,793.80 |
| Max drawdown | $-4,180.00 (-8.7%) |
| Longest losing streak | 6 |
| Avg contracts / avg planned risk | 2.40 / 0.81% of equity |
| Exits | stop 33, target 29 |
| Signals | 82 |
| Limit orders placed / filled | 32 / 28 (87.5%) |
| Expired / invalidated / cancelled at flatten | 4 / 0 / 0 |
| Skipped setups | {'size_below_min': 9, 'occupied': 4, 'min_stop': 1, 'pre_closure_window': 1, 'market_open_outside_zone': 1} |

## Full sample

| Metric | Value |
|---|---|
| Trades | 209 |
| Wins / losses | 99 / 110 |
| Win rate | 47.4% (95% CI 40.7% to 54.1%) |
| Avg win R / avg loss R | 0.949 / -0.976 |
| Expectancy R | -0.064 (95% CI -0.200 to +0.066) |
| Profit factor | 0.90 |
| Net profit after costs | $-4,206.20 |
| Fees / price slippage | $1,297.20 / $784.00 |
| Ending equity | $45,793.80 |
| Max drawdown | $-7,460.04 (-14.6%) |
| Longest losing streak | 7 |
| Avg contracts / avg planned risk | 3.30 / 0.80% of equity |
| Exits | stop 107, target 98, flatten 4 |
| Signals | 268 |
| Limit orders placed / filled | 120 / 100 (83.3%) |
| Expired / invalidated / cancelled at flatten | 19 / 1 / 0 |
| Skipped setups | {'size_below_min': 20, 'occupied': 15, 'min_stop': 2, 'dual_side_sweep': 1, 'pre_closure_window': 1, 'market_open_outside_zone': 1} |

Ambiguous 1-minute sequences: {'fill_vs_invalidation': 0, 'stop_vs_target': 0, 'entry_and_exit_same_minute': 2}. Flagged trades: {'entry_and_exit_same_minute': 2, 'gap_fill': 1}.

# v3_market_only_baseline_2ticks
Slippage 2 ticks per eligible fill, fees $0.94 per side, starting equity $50,000, risk 1%, max 10 contracts.
Data: 6228 1H bars from 2025-10-01 00:00:00+00:00 to 2026-10-21 00:00:00+00:00. Split boundary 2026-06-14 12:00:00-04:00.

## Development period

| Metric | Value |
|---|---|
| Trades | 84 |
| Wins / losses | 20 / 64 |
| Win rate | 23.8% (95% CI 16.0% to 33.9%) |
| Avg win R / avg loss R | 1.832 / -0.576 |
| Expectancy R | -0.003 (95% CI -0.243 to +0.240) |
| Profit factor | 0.96 |
| Net profit after costs | $-639.50 |
| Fees / price slippage | $752.00 / $714.00 |
| Ending equity | $49,360.50 |
| Max drawdown | $-4,465.32 (-8.5%) |
| Longest losing streak | 13 |
| Avg contracts / avg planned risk | 4.76 / 0.81% of equity |
| Exits | stop 36, breakeven 27, target 19, flatten 2 |
| Signals | 186 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'limit_entries_disabled': 94, 'size_below_min': 5, 'occupied': 2, 'min_stop': 1, 'dual_side_sweep': 1} |

## Out-of-sample period

| Metric | Value |
|---|---|
| Trades | 36 |
| Wins / losses | 9 / 27 |
| Win rate | 25.0% (95% CI 13.8% to 41.1%) |
| Avg win R / avg loss R | 1.939 / -0.605 |
| Expectancy R | +0.031 (95% CI -0.347 to +0.435) |
| Profit factor | 1.15 |
| Net profit after costs | $933.08 |
| Fees / price slippage | $204.92 / $188.00 |
| Ending equity | $50,293.58 |
| Max drawdown | $-3,034.68 (-6.1%) |
| Longest losing streak | 10 |
| Avg contracts / avg planned risk | 3.03 / 0.82% of equity |
| Exits | stop 16, breakeven 11, target 9 |
| Signals | 82 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'limit_entries_disabled': 39, 'size_below_min': 4, 'min_stop': 1, 'pre_closure_window': 1, 'market_open_outside_zone': 1} |

## Full sample

| Metric | Value |
|---|---|
| Trades | 120 |
| Wins / losses | 29 / 91 |
| Win rate | 24.2% (95% CI 17.4% to 32.6%) |
| Avg win R / avg loss R | 1.865 / -0.585 |
| Expectancy R | +0.007 (95% CI -0.204 to +0.211) |
| Profit factor | 1.01 |
| Net profit after costs | $293.58 |
| Fees / price slippage | $956.92 / $902.00 |
| Ending equity | $50,293.58 |
| Max drawdown | $-6,179.06 (-11.8%) |
| Longest losing streak | 17 |
| Avg contracts / avg planned risk | 4.24 / 0.82% of equity |
| Exits | stop 52, breakeven 38, target 28, flatten 2 |
| Signals | 268 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'limit_entries_disabled': 133, 'size_below_min': 9, 'min_stop': 2, 'occupied': 2, 'dual_side_sweep': 1, 'pre_closure_window': 1, 'market_open_outside_zone': 1} |

Ambiguous 1-minute sequences: {'fill_vs_invalidation': 0, 'stop_vs_target': 3, 'entry_and_exit_same_minute': 1}. Flagged trades: {'be_armed': 62, 'be_armed,ambiguous_be_arm_and_hit_same_minute': 2, 'be_armed,gap_target': 1, 'be_armed,ambiguous_stop_vs_target': 1, 'entry_and_exit_same_minute': 1}.

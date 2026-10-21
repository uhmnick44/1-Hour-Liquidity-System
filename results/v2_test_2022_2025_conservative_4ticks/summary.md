# v2_test_2022_2025_conservative_4ticks
Slippage 4 ticks per eligible fill, fees $0.94 per side, starting equity $50,000, risk 1%, max 10 contracts.
Data: 17685 1H bars from 2022-10-02 22:00:00+00:00 to 2025-10-01 00:00:00+00:00. Split boundary 2022-10-02 18:00:00-04:00.

## Development period

| Metric | Value |
|---|---|
| trades | 0 |
| Signals | 0 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {} |

## Out-of-sample period

| Metric | Value |
|---|---|
| Trades | 363 |
| Wins / losses | 156 / 207 |
| Win rate | 43.0% (95% CI 38.0% to 48.1%) |
| Avg win R / avg loss R | 0.883 / -0.993 |
| Expectancy R | -0.187 (95% CI -0.281 to -0.089) |
| Profit factor | 0.66 |
| Net profit after costs | $-22,558.80 |
| Fees / price slippage | $2,885.80 / $4,900.00 |
| Ending equity | $27,441.20 |
| Max drawdown | $-25,301.90 (-49.0%) |
| Longest losing streak | 11 |
| Avg contracts / avg planned risk | 4.23 / 0.85% of equity |
| Exits | stop 205, target 147, flatten 10, end_of_data 1 |
| Signals | 740 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'limit_entries_disabled': 326, 'occupied': 19, 'size_below_min': 16, 'dual_side_sweep': 11, 'min_stop': 9, 'market_open_outside_zone': 4, 'pre_closure_window': 2, 'invalid_stop': 1} |

## Full sample

| Metric | Value |
|---|---|
| Trades | 363 |
| Wins / losses | 156 / 207 |
| Win rate | 43.0% (95% CI 38.0% to 48.1%) |
| Avg win R / avg loss R | 0.883 / -0.993 |
| Expectancy R | -0.187 (95% CI -0.281 to -0.089) |
| Profit factor | 0.66 |
| Net profit after costs | $-22,558.80 |
| Fees / price slippage | $2,885.80 / $4,900.00 |
| Ending equity | $27,441.20 |
| Max drawdown | $-25,301.90 (-49.0%) |
| Longest losing streak | 11 |
| Avg contracts / avg planned risk | 4.23 / 0.85% of equity |
| Exits | stop 205, target 147, flatten 10, end_of_data 1 |
| Signals | 740 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'limit_entries_disabled': 326, 'occupied': 19, 'size_below_min': 16, 'dual_side_sweep': 11, 'min_stop': 9, 'market_open_outside_zone': 4, 'pre_closure_window': 2, 'invalid_stop': 1} |

Ambiguous 1-minute sequences: {'fill_vs_invalidation': 0, 'stop_vs_target': 3, 'entry_and_exit_same_minute': 6}. Flagged trades: {'entry_and_exit_same_minute': 6, 'ambiguous_stop_vs_target': 3, 'end_of_data': 1}.

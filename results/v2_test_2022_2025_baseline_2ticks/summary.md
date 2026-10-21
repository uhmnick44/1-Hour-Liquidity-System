# v2_test_2022_2025_baseline_2ticks
Slippage 2 ticks per eligible fill, fees $0.94 per side, starting equity $50,000, risk 1%, max 10 contracts.
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
| Trades | 364 |
| Wins / losses | 157 / 207 |
| Win rate | 43.1% (95% CI 38.1% to 48.3%) |
| Avg win R / avg loss R | 0.895 / -0.993 |
| Expectancy R | -0.179 (95% CI -0.276 to -0.080) |
| Profit factor | 0.68 |
| Net profit after costs | $-21,526.24 |
| Fees / price slippage | $3,098.24 / $2,607.00 |
| Ending equity | $28,473.76 |
| Max drawdown | $-24,162.94 (-46.9%) |
| Longest losing streak | 11 |
| Avg contracts / avg planned risk | 4.53 / 0.85% of equity |
| Exits | stop 205, target 149, flatten 9, end_of_data 1 |
| Signals | 740 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'limit_entries_disabled': 327, 'occupied': 18, 'size_below_min': 15, 'dual_side_sweep': 11, 'min_stop': 9, 'market_open_outside_zone': 4, 'pre_closure_window': 2, 'invalid_stop': 1} |

## Full sample

| Metric | Value |
|---|---|
| Trades | 364 |
| Wins / losses | 157 / 207 |
| Win rate | 43.1% (95% CI 38.1% to 48.3%) |
| Avg win R / avg loss R | 0.895 / -0.993 |
| Expectancy R | -0.179 (95% CI -0.276 to -0.080) |
| Profit factor | 0.68 |
| Net profit after costs | $-21,526.24 |
| Fees / price slippage | $3,098.24 / $2,607.00 |
| Ending equity | $28,473.76 |
| Max drawdown | $-24,162.94 (-46.9%) |
| Longest losing streak | 11 |
| Avg contracts / avg planned risk | 4.53 / 0.85% of equity |
| Exits | stop 205, target 149, flatten 9, end_of_data 1 |
| Signals | 740 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'limit_entries_disabled': 327, 'occupied': 18, 'size_below_min': 15, 'dual_side_sweep': 11, 'min_stop': 9, 'market_open_outside_zone': 4, 'pre_closure_window': 2, 'invalid_stop': 1} |

Ambiguous 1-minute sequences: {'fill_vs_invalidation': 0, 'stop_vs_target': 3, 'entry_and_exit_same_minute': 6}. Flagged trades: {'entry_and_exit_same_minute': 6, 'ambiguous_stop_vs_target': 3, 'end_of_data': 1}.

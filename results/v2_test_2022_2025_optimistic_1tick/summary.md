# v2_test_2022_2025_optimistic_1tick
Slippage 1 ticks per eligible fill, fees $0.94 per side, starting equity $50,000, risk 1%, max 10 contracts.
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
| Trades | 365 |
| Wins / losses | 160 / 205 |
| Win rate | 43.8% (95% CI 38.8% to 49.0%) |
| Avg win R / avg loss R | 0.901 / -0.993 |
| Expectancy R | -0.163 (95% CI -0.263 to -0.063) |
| Profit factor | 0.71 |
| Net profit after costs | $-19,808.86 |
| Fees / price slippage | $3,190.36 / $1,332.50 |
| Ending equity | $30,191.14 |
| Max drawdown | $-22,340.94 (-43.6%) |
| Longest losing streak | 11 |
| Avg contracts / avg planned risk | 4.65 / 0.85% of equity |
| Exits | stop 203, target 152, flatten 9, end_of_data 1 |
| Signals | 740 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'limit_entries_disabled': 326, 'occupied': 20, 'size_below_min': 12, 'dual_side_sweep': 11, 'min_stop': 10, 'market_open_outside_zone': 4, 'pre_closure_window': 2, 'invalid_stop': 1} |

## Full sample

| Metric | Value |
|---|---|
| Trades | 365 |
| Wins / losses | 160 / 205 |
| Win rate | 43.8% (95% CI 38.8% to 49.0%) |
| Avg win R / avg loss R | 0.901 / -0.993 |
| Expectancy R | -0.163 (95% CI -0.263 to -0.063) |
| Profit factor | 0.71 |
| Net profit after costs | $-19,808.86 |
| Fees / price slippage | $3,190.36 / $1,332.50 |
| Ending equity | $30,191.14 |
| Max drawdown | $-22,340.94 (-43.6%) |
| Longest losing streak | 11 |
| Avg contracts / avg planned risk | 4.65 / 0.85% of equity |
| Exits | stop 203, target 152, flatten 9, end_of_data 1 |
| Signals | 740 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'limit_entries_disabled': 326, 'occupied': 20, 'size_below_min': 12, 'dual_side_sweep': 11, 'min_stop': 10, 'market_open_outside_zone': 4, 'pre_closure_window': 2, 'invalid_stop': 1} |

Ambiguous 1-minute sequences: {'fill_vs_invalidation': 0, 'stop_vs_target': 2, 'entry_and_exit_same_minute': 6}. Flagged trades: {'entry_and_exit_same_minute': 6, 'ambiguous_stop_vs_target': 2, 'end_of_data': 1}.

# v1_ref_2022_2025_baseline_2ticks
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
| Trades | 554 |
| Wins / losses | 254 / 300 |
| Win rate | 45.8% (95% CI 41.7% to 50.0%) |
| Avg win R / avg loss R | 0.909 / -0.984 |
| Expectancy R | -0.116 (95% CI -0.193 to -0.036) |
| Profit factor | 0.77 |
| Net profit after costs | $-22,335.88 |
| Fees / price slippage | $4,184.88 / $2,863.00 |
| Ending equity | $27,664.12 |
| Max drawdown | $-27,538.00 (-50.8%) |
| Longest losing streak | 13 |
| Avg contracts / avg planned risk | 4.02 / 0.83% of equity |
| Exits | stop 293, target 242, flatten 18, end_of_data 1 |
| Signals | 740 |
| Limit orders placed / filled | 282 / 205 (72.7%) |
| Expired / invalidated / cancelled at flatten | 75 / 0 / 2 |
| Skipped setups | {'size_below_min': 47, 'occupied': 46, 'dual_side_sweep': 11, 'min_stop': 9, 'market_open_outside_zone': 4, 'pre_closure_window': 2, 'invalid_stop': 1} |

## Full sample

| Metric | Value |
|---|---|
| Trades | 554 |
| Wins / losses | 254 / 300 |
| Win rate | 45.8% (95% CI 41.7% to 50.0%) |
| Avg win R / avg loss R | 0.909 / -0.984 |
| Expectancy R | -0.116 (95% CI -0.193 to -0.036) |
| Profit factor | 0.77 |
| Net profit after costs | $-22,335.88 |
| Fees / price slippage | $4,184.88 / $2,863.00 |
| Ending equity | $27,664.12 |
| Max drawdown | $-27,538.00 (-50.8%) |
| Longest losing streak | 13 |
| Avg contracts / avg planned risk | 4.02 / 0.83% of equity |
| Exits | stop 293, target 242, flatten 18, end_of_data 1 |
| Signals | 740 |
| Limit orders placed / filled | 282 / 205 (72.7%) |
| Expired / invalidated / cancelled at flatten | 75 / 0 / 2 |
| Skipped setups | {'size_below_min': 47, 'occupied': 46, 'dual_side_sweep': 11, 'min_stop': 9, 'market_open_outside_zone': 4, 'pre_closure_window': 2, 'invalid_stop': 1} |

Ambiguous 1-minute sequences: {'fill_vs_invalidation': 0, 'stop_vs_target': 4, 'entry_and_exit_same_minute': 6}. Flagged trades: {'entry_and_exit_same_minute': 6, 'ambiguous_stop_vs_target': 4, 'gap_fill': 3, 'end_of_data': 1}.

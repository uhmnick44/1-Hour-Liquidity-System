# v3_with_limits_baseline_2ticks
Slippage 2 ticks per eligible fill, fees $0.94 per side, starting equity $50,000, risk 1%, max 10 contracts.
Data: 6228 1H bars from 2025-10-01 00:00:00+00:00 to 2026-10-21 00:00:00+00:00. Split boundary 2026-06-14 12:00:00-04:00.

## Development period

| Metric | Value |
|---|---|
| Trades | 137 |
| Wins / losses | 27 / 110 |
| Win rate | 19.7% (95% CI 13.9% to 27.2%) |
| Avg win R / avg loss R | 1.812 / -0.667 |
| Expectancy R | -0.179 (95% CI -0.361 to +0.008) |
| Profit factor | 0.67 |
| Net profit after costs | $-8,927.34 |
| Fees / price slippage | $926.84 / $718.00 |
| Ending equity | $41,072.66 |
| Max drawdown | $-10,684.86 (-20.6%) |
| Longest losing streak | 14 |
| Avg contracts / avg planned risk | 3.60 / 0.81% of equity |
| Exits | stop 72, breakeven 35, target 25, flatten 5 |
| Signals | 186 |
| Limit orders placed / filled | 80 / 67 (83.8%) |
| Expired / invalidated / cancelled at flatten | 12 / 1 / 0 |
| Skipped setups | {'occupied': 18, 'size_below_min': 17, 'min_stop': 1, 'dual_side_sweep': 1} |

## Out-of-sample period

| Metric | Value |
|---|---|
| Trades | 59 |
| Wins / losses | 12 / 47 |
| Win rate | 20.3% (95% CI 12.0% to 32.3%) |
| Avg win R / avg loss R | 1.940 / -0.627 |
| Expectancy R | -0.105 (95% CI -0.386 to +0.195) |
| Profit factor | 0.80 |
| Net profit after costs | $-1,764.88 |
| Fees / price slippage | $236.88 / $178.00 |
| Ending equity | $39,307.78 |
| Max drawdown | $-3,720.52 (-9.1%) |
| Longest losing streak | 16 |
| Avg contracts / avg planned risk | 2.14 / 0.79% of equity |
| Exits | stop 29, breakeven 18, target 12 |
| Signals | 82 |
| Limit orders placed / filled | 30 / 26 (86.7%) |
| Expired / invalidated / cancelled at flatten | 4 / 0 / 0 |
| Skipped setups | {'size_below_min': 13, 'occupied': 3, 'min_stop': 1, 'pre_closure_window': 1, 'market_open_outside_zone': 1} |

## Full sample

| Metric | Value |
|---|---|
| Trades | 196 |
| Wins / losses | 39 / 157 |
| Win rate | 19.9% (95% CI 14.9% to 26.0%) |
| Avg win R / avg loss R | 1.851 / -0.655 |
| Expectancy R | -0.156 (95% CI -0.308 to +0.002) |
| Profit factor | 0.70 |
| Net profit after costs | $-10,692.22 |
| Fees / price slippage | $1,163.72 / $896.00 |
| Ending equity | $39,307.78 |
| Max drawdown | $-14,405.38 (-27.8%) |
| Longest losing streak | 24 |
| Avg contracts / avg planned risk | 3.16 / 0.80% of equity |
| Exits | stop 101, breakeven 53, target 37, flatten 5 |
| Signals | 268 |
| Limit orders placed / filled | 110 / 93 (84.5%) |
| Expired / invalidated / cancelled at flatten | 16 / 1 / 0 |
| Skipped setups | {'size_below_min': 30, 'occupied': 21, 'min_stop': 2, 'dual_side_sweep': 1, 'pre_closure_window': 1, 'market_open_outside_zone': 1} |

Ambiguous 1-minute sequences: {'fill_vs_invalidation': 0, 'stop_vs_target': 3, 'entry_and_exit_same_minute': 1}. Flagged trades: {'be_armed': 87, 'be_armed,ambiguous_be_arm_and_hit_same_minute': 2, 'be_armed,gap_target': 1, 'be_armed,ambiguous_stop_vs_target': 1, 'entry_and_exit_same_minute': 1, 'gap_fill': 1}.

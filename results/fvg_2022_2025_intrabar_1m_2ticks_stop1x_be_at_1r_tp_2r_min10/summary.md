# fvg_2022_2025_intrabar_1m_2ticks_stop1x_be_at_1r_tp_2r_min10
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
| Trades | 896 |
| Wins / losses | 224 / 672 |
| Win rate | 25.0% (95% CI 22.3% to 27.9%) |
| Avg win R / avg loss R | 1.824 / -0.688 |
| Expectancy R | -0.060 (95% CI -0.135 to +0.017) |
| Profit factor | 0.89 |
| Net profit after costs | $-17,362.54 |
| Fees / price slippage | $11,859.04 / $11,094.00 |
| Ending equity | $32,637.46 |
| Max drawdown | $-21,962.22 (-41.3%) |
| Longest losing streak | 23 |
| Avg contracts / avg planned risk | 7.04 / 0.85% of equity |
| Exits | stop 447, breakeven 223, target 221, flatten 5 |
| Signals | 1015 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'min_stop': 115, 'size_below_min': 3, 'pre_closure_window': 1} |

## Full sample

| Metric | Value |
|---|---|
| Trades | 896 |
| Wins / losses | 224 / 672 |
| Win rate | 25.0% (95% CI 22.3% to 27.9%) |
| Avg win R / avg loss R | 1.824 / -0.688 |
| Expectancy R | -0.060 (95% CI -0.135 to +0.017) |
| Profit factor | 0.89 |
| Net profit after costs | $-17,362.54 |
| Fees / price slippage | $11,859.04 / $11,094.00 |
| Ending equity | $32,637.46 |
| Max drawdown | $-21,962.22 (-41.3%) |
| Longest losing streak | 23 |
| Avg contracts / avg planned risk | 7.04 / 0.85% of equity |
| Exits | stop 447, breakeven 223, target 221, flatten 5 |
| Signals | 1015 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'min_stop': 115, 'size_below_min': 3, 'pre_closure_window': 1} |

Ambiguous 1-minute sequences: {'fill_vs_invalidation': 0, 'stop_vs_target': 35, 'entry_and_exit_same_minute': 6}. Flagged trades: {'be_armed': 413, 'be_armed,ambiguous_be_arm_and_hit_same_minute': 31, 'entry_and_exit_same_minute': 6, 'ambiguous_stop_vs_target': 4, 'gap_stop': 3, 'be_armed,gap_stop': 1}.

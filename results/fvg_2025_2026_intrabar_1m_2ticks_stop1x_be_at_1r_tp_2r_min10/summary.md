# fvg_2025_2026_intrabar_1m_2ticks_stop1x_be_at_1r_tp_2r_min10
Slippage 2 ticks per eligible fill, fees $0.94 per side, starting equity $50,000, risk 1%, max 10 contracts.
Data: 6228 1H bars from 2025-10-01 00:00:00+00:00 to 2026-10-21 00:00:00+00:00. Split boundary 2026-06-14 12:00:00-04:00.

## Development period

| Metric | Value |
|---|---|
| Trades | 221 |
| Wins / losses | 35 / 186 |
| Win rate | 15.8% (95% CI 11.6% to 21.2%) |
| Avg win R / avg loss R | 1.853 / -0.671 |
| Expectancy R | -0.271 (95% CI -0.398 to -0.136) |
| Profit factor | 0.49 |
| Net profit after costs | $-21,030.24 |
| Fees / price slippage | $2,017.24 / $1,998.00 |
| Ending equity | $28,969.76 |
| Max drawdown | $-22,413.68 (-43.9%) |
| Longest losing streak | 20 |
| Avg contracts / avg planned risk | 4.86 / 0.85% of equity |
| Exits | stop 121, breakeven 64, target 34, flatten 2 |
| Signals | 236 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'min_stop': 13, 'size_below_min': 2} |

## Out-of-sample period

| Metric | Value |
|---|---|
| Trades | 109 |
| Wins / losses | 28 / 81 |
| Win rate | 25.7% (95% CI 18.4% to 34.6%) |
| Avg win R / avg loss R | 1.874 / -0.636 |
| Expectancy R | +0.009 (95% CI -0.213 to +0.235) |
| Profit factor | 1.05 |
| Net profit after costs | $655.36 |
| Fees / price slippage | $851.64 / $784.00 |
| Ending equity | $29,625.12 |
| Max drawdown | $-2,411.60 (-7.9%) |
| Longest losing streak | 10 |
| Avg contracts / avg planned risk | 4.16 / 0.86% of equity |
| Exits | stop 50, breakeven 31, target 28 |
| Signals | 112 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'min_stop': 2, 'size_below_min': 1} |

## Full sample

| Metric | Value |
|---|---|
| Trades | 330 |
| Wins / losses | 63 / 267 |
| Win rate | 19.1% (95% CI 15.2% to 23.7%) |
| Avg win R / avg loss R | 1.862 / -0.660 |
| Expectancy R | -0.179 (95% CI -0.293 to -0.058) |
| Profit factor | 0.62 |
| Net profit after costs | $-20,374.88 |
| Fees / price slippage | $2,868.88 / $2,782.00 |
| Ending equity | $29,625.12 |
| Max drawdown | $-23,074.24 (-45.2%) |
| Longest losing streak | 20 |
| Avg contracts / avg planned risk | 4.62 / 0.85% of equity |
| Exits | stop 171, breakeven 95, target 62, flatten 2 |
| Signals | 348 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'min_stop': 15, 'size_below_min': 3} |

Ambiguous 1-minute sequences: {'fill_vs_invalidation': 0, 'stop_vs_target': 18, 'entry_and_exit_same_minute': 2}. Flagged trades: {'be_armed': 140, 'be_armed,ambiguous_be_arm_and_hit_same_minute': 18, 'entry_and_exit_same_minute': 2, 'gap_stop': 2}.

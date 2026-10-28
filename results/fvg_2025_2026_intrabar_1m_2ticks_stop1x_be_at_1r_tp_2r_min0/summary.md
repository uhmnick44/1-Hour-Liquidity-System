# fvg_2025_2026_intrabar_1m_2ticks_stop1x_be_at_1r_tp_2r_min0
Slippage 2 ticks per eligible fill, fees $0.94 per side, starting equity $50,000, risk 1%, max 10 contracts.
Data: 6228 1H bars from 2025-10-01 00:00:00+00:00 to 2026-10-21 00:00:00+00:00. Split boundary 2026-06-14 12:00:00-04:00.

## Development period

| Metric | Value |
|---|---|
| Trades | 234 |
| Wins / losses | 37 / 197 |
| Win rate | 15.8% (95% CI 11.7% to 21.0%) |
| Avg win R / avg loss R | 1.841 / -0.668 |
| Expectancy R | -0.271 (95% CI -0.400 to -0.137) |
| Profit factor | 0.50 |
| Net profit after costs | $-21,264.20 |
| Fees / price slippage | $2,237.20 / $2,214.00 |
| Ending equity | $28,735.80 |
| Max drawdown | $-22,618.84 (-44.4%) |
| Longest losing streak | 20 |
| Avg contracts / avg planned risk | 5.09 / 0.83% of equity |
| Exits | stop 127, breakeven 69, target 36, flatten 2 |
| Signals | 236 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'size_below_min': 2} |

## Out-of-sample period

| Metric | Value |
|---|---|
| Trades | 111 |
| Wins / losses | 28 / 83 |
| Win rate | 25.2% (95% CI 18.1% to 34.0%) |
| Avg win R / avg loss R | 1.874 / -0.636 |
| Expectancy R | -0.003 (95% CI -0.218 to +0.213) |
| Profit factor | 1.02 |
| Net profit after costs | $258.04 |
| Fees / price slippage | $877.96 / $815.00 |
| Ending equity | $28,993.84 |
| Max drawdown | $-2,411.60 (-8.0%) |
| Longest losing streak | 10 |
| Avg contracts / avg planned risk | 4.21 / 0.85% of equity |
| Exits | stop 51, breakeven 32, target 28 |
| Signals | 112 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'size_below_min': 1} |

## Full sample

| Metric | Value |
|---|---|
| Trades | 345 |
| Wins / losses | 65 / 280 |
| Win rate | 18.8% (95% CI 15.1% to 23.3%) |
| Avg win R / avg loss R | 1.855 / -0.658 |
| Expectancy R | -0.185 (95% CI -0.297 to -0.069) |
| Profit factor | 0.62 |
| Net profit after costs | $-21,006.16 |
| Fees / price slippage | $3,115.16 / $3,029.00 |
| Ending equity | $28,993.84 |
| Max drawdown | $-23,279.40 (-45.7%) |
| Longest losing streak | 20 |
| Avg contracts / avg planned risk | 4.80 / 0.84% of equity |
| Exits | stop 178, breakeven 101, target 64, flatten 2 |
| Signals | 348 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'size_below_min': 3} |

Ambiguous 1-minute sequences: {'fill_vs_invalidation': 0, 'stop_vs_target': 20, 'entry_and_exit_same_minute': 4}. Flagged trades: {'be_armed': 146, 'be_armed,ambiguous_be_arm_and_hit_same_minute': 20, 'entry_and_exit_same_minute': 4, 'gap_stop': 2}.

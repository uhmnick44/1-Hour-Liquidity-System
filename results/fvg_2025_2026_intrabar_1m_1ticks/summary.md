# fvg_2025_2026_intrabar_1m_1ticks
Slippage 1 ticks per eligible fill, fees $0.94 per side, starting equity $50,000, risk 1%, max 10 contracts.
Data: 6228 1H bars from 2025-10-01 00:00:00+00:00 to 2026-10-21 00:00:00+00:00. Split boundary 2026-06-14 12:00:00-04:00.

## Development period

| Metric | Value |
|---|---|
| Trades | 210 |
| Wins / losses | 102 / 108 |
| Win rate | 48.6% (95% CI 41.9% to 55.3%) |
| Avg win R / avg loss R | 0.955 / -0.985 |
| Expectancy R | -0.042 (95% CI -0.172 to +0.094) |
| Profit factor | 0.92 |
| Net profit after costs | $-3,141.30 |
| Fees / price slippage | $1,381.80 / $558.00 |
| Ending equity | $46,858.70 |
| Max drawdown | $-5,841.24 (-11.5%) |
| Longest losing streak | 5 |
| Avg contracts / avg planned risk | 3.50 / 0.81% of equity |
| Exits | stop 106, target 101, flatten 3 |
| Signals | 218 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'size_below_min': 7, 'min_stop': 1} |

## Out-of-sample period

| Metric | Value |
|---|---|
| Trades | 102 |
| Wins / losses | 55 / 47 |
| Win rate | 53.9% (95% CI 44.3% to 63.3%) |
| Avg win R / avg loss R | 0.950 / -1.000 |
| Expectancy R | +0.051 (95% CI -0.134 to +0.245) |
| Profit factor | 1.16 |
| Net profit after costs | $2,964.64 |
| Fees / price slippage | $699.36 / $268.00 |
| Ending equity | $49,823.34 |
| Max drawdown | $-2,747.52 (-5.4%) |
| Longest losing streak | 3 |
| Avg contracts / avg planned risk | 3.65 / 0.84% of equity |
| Exits | target 54, stop 47, flatten 1 |
| Signals | 105 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'size_below_min': 2, 'min_stop': 1} |

## Full sample

| Metric | Value |
|---|---|
| Trades | 312 |
| Wins / losses | 157 / 155 |
| Win rate | 50.3% (95% CI 44.8% to 55.8%) |
| Avg win R / avg loss R | 0.953 / -0.989 |
| Expectancy R | -0.012 (95% CI -0.118 to +0.097) |
| Profit factor | 1.00 |
| Net profit after costs | $-176.66 |
| Fees / price slippage | $2,081.16 / $826.00 |
| Ending equity | $49,823.34 |
| Max drawdown | $-5,841.24 (-11.5%) |
| Longest losing streak | 5 |
| Avg contracts / avg planned risk | 3.55 / 0.82% of equity |
| Exits | target 155, stop 153, flatten 4 |
| Signals | 323 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'size_below_min': 9, 'min_stop': 2} |

Ambiguous 1-minute sequences: {'fill_vs_invalidation': 0, 'stop_vs_target': 0, 'entry_and_exit_same_minute': 0}. Flagged trades: {}.

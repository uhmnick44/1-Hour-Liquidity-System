# fvg_2025_2026_intrabar_1m_4ticks
Slippage 4 ticks per eligible fill, fees $0.94 per side, starting equity $50,000, risk 1%, max 10 contracts.
Data: 6228 1H bars from 2025-10-01 00:00:00+00:00 to 2026-10-21 00:00:00+00:00. Split boundary 2026-06-14 12:00:00-04:00.

## Development period

| Metric | Value |
|---|---|
| Trades | 210 |
| Wins / losses | 100 / 110 |
| Win rate | 47.6% (95% CI 41.0% to 54.4%) |
| Avg win R / avg loss R | 0.946 / -0.985 |
| Expectancy R | -0.066 (95% CI -0.197 to +0.070) |
| Profit factor | 0.88 |
| Net profit after costs | $-5,117.24 |
| Fees / price slippage | $1,312.24 / $2,146.00 |
| Ending equity | $44,882.76 |
| Max drawdown | $-6,806.20 (-13.4%) |
| Longest losing streak | 7 |
| Avg contracts / avg planned risk | 3.32 / 0.82% of equity |
| Exits | stop 108, target 99, flatten 3 |
| Signals | 218 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'size_below_min': 7, 'min_stop': 1} |

## Out-of-sample period

| Metric | Value |
|---|---|
| Trades | 100 |
| Wins / losses | 53 / 47 |
| Win rate | 53.0% (95% CI 43.3% to 62.5%) |
| Avg win R / avg loss R | 0.946 / -1.000 |
| Expectancy R | +0.032 (95% CI -0.163 to +0.225) |
| Profit factor | 1.10 |
| Net profit after costs | $1,748.92 |
| Fees / price slippage | $641.08 / $986.00 |
| Ending equity | $46,631.68 |
| Max drawdown | $-3,230.96 (-6.7%) |
| Longest losing streak | 3 |
| Avg contracts / avg planned risk | 3.41 / 0.84% of equity |
| Exits | target 53, stop 47 |
| Signals | 105 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'size_below_min': 5} |

## Full sample

| Metric | Value |
|---|---|
| Trades | 310 |
| Wins / losses | 153 / 157 |
| Win rate | 49.4% (95% CI 43.8% to 54.9%) |
| Avg win R / avg loss R | 0.946 / -0.990 |
| Expectancy R | -0.034 (95% CI -0.142 to +0.075) |
| Profit factor | 0.94 |
| Net profit after costs | $-3,368.32 |
| Fees / price slippage | $1,953.32 / $3,132.00 |
| Ending equity | $46,631.68 |
| Max drawdown | $-7,678.60 (-15.1%) |
| Longest losing streak | 7 |
| Avg contracts / avg planned risk | 3.35 / 0.83% of equity |
| Exits | stop 155, target 152, flatten 3 |
| Signals | 323 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'size_below_min': 12, 'min_stop': 1} |

Ambiguous 1-minute sequences: {'fill_vs_invalidation': 0, 'stop_vs_target': 0, 'entry_and_exit_same_minute': 0}. Flagged trades: {}.

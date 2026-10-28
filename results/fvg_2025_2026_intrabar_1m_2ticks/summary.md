# fvg_2025_2026_intrabar_1m_2ticks
Slippage 2 ticks per eligible fill, fees $0.94 per side, starting equity $50,000, risk 1%, max 10 contracts.
Data: 6228 1H bars from 2025-10-01 00:00:00+00:00 to 2026-10-21 00:00:00+00:00. Split boundary 2026-06-14 12:00:00-04:00.

## Development period

| Metric | Value |
|---|---|
| Trades | 210 |
| Wins / losses | 101 / 109 |
| Win rate | 48.1% (95% CI 41.4% to 54.8%) |
| Avg win R / avg loss R | 0.952 / -0.985 |
| Expectancy R | -0.053 (95% CI -0.183 to +0.081) |
| Profit factor | 0.90 |
| Net profit after costs | $-4,190.36 |
| Fees / price slippage | $1,357.36 / $1,101.00 |
| Ending equity | $45,809.64 |
| Max drawdown | $-6,914.04 (-13.6%) |
| Longest losing streak | 5 |
| Avg contracts / avg planned risk | 3.44 / 0.82% of equity |
| Exits | stop 107, target 100, flatten 3 |
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
| Avg win R / avg loss R | 0.946 / -1.000 |
| Expectancy R | +0.049 (95% CI -0.136 to +0.242) |
| Profit factor | 1.16 |
| Net profit after costs | $2,924.46 |
| Fees / price slippage | $673.04 / $515.00 |
| Ending equity | $48,734.10 |
| Max drawdown | $-2,632.88 (-5.3%) |
| Longest losing streak | 3 |
| Avg contracts / avg planned risk | 3.51 / 0.84% of equity |
| Exits | target 54, stop 47, flatten 1 |
| Signals | 105 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'size_below_min': 2, 'min_stop': 1} |

## Full sample

| Metric | Value |
|---|---|
| Trades | 312 |
| Wins / losses | 156 / 156 |
| Win rate | 50.0% (95% CI 44.5% to 55.5%) |
| Avg win R / avg loss R | 0.950 / -0.990 |
| Expectancy R | -0.020 (95% CI -0.126 to +0.088) |
| Profit factor | 0.98 |
| Net profit after costs | $-1,265.90 |
| Fees / price slippage | $2,030.40 / $1,616.00 |
| Ending equity | $48,734.10 |
| Max drawdown | $-6,914.04 (-13.6%) |
| Longest losing streak | 5 |
| Avg contracts / avg planned risk | 3.46 / 0.83% of equity |
| Exits | stop 154, target 154, flatten 4 |
| Signals | 323 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'size_below_min': 9, 'min_stop': 2} |

Ambiguous 1-minute sequences: {'fill_vs_invalidation': 0, 'stop_vs_target': 0, 'entry_and_exit_same_minute': 0}. Flagged trades: {}.

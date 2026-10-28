# fvg_2022_2025_intrabar_1m_2ticks
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
| Trades | 903 |
| Wins / losses | 436 / 467 |
| Win rate | 48.3% (95% CI 45.0% to 51.5%) |
| Avg win R / avg loss R | 0.931 / -0.989 |
| Expectancy R | -0.062 (95% CI -0.124 to +0.002) |
| Profit factor | 0.85 |
| Net profit after costs | $-20,019.54 |
| Fees / price slippage | $6,877.04 / $5,593.00 |
| Ending equity | $29,980.46 |
| Max drawdown | $-23,689.56 (-46.4%) |
| Longest losing streak | 9 |
| Avg contracts / avg planned risk | 4.05 / 0.85% of equity |
| Exits | stop 459, target 433, flatten 11 |
| Signals | 952 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'size_below_min': 39, 'min_stop': 9, 'pre_closure_window': 1} |

## Full sample

| Metric | Value |
|---|---|
| Trades | 903 |
| Wins / losses | 436 / 467 |
| Win rate | 48.3% (95% CI 45.0% to 51.5%) |
| Avg win R / avg loss R | 0.931 / -0.989 |
| Expectancy R | -0.062 (95% CI -0.124 to +0.002) |
| Profit factor | 0.85 |
| Net profit after costs | $-20,019.54 |
| Fees / price slippage | $6,877.04 / $5,593.00 |
| Ending equity | $29,980.46 |
| Max drawdown | $-23,689.56 (-46.4%) |
| Longest losing streak | 9 |
| Avg contracts / avg planned risk | 4.05 / 0.85% of equity |
| Exits | stop 459, target 433, flatten 11 |
| Signals | 952 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'size_below_min': 39, 'min_stop': 9, 'pre_closure_window': 1} |

Ambiguous 1-minute sequences: {'fill_vs_invalidation': 0, 'stop_vs_target': 1, 'entry_and_exit_same_minute': 1}. Flagged trades: {'ambiguous_stop_vs_target': 1, 'gap_stop': 1, 'entry_and_exit_same_minute': 1}.

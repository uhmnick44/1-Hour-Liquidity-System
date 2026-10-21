# v2_baseline_2ticks
Slippage 2 ticks per eligible fill, fees $0.94 per side, starting equity $50,000, risk 1%, max 10 contracts.
Data: 6228 1H bars from 2025-10-01 00:00:00+00:00 to 2026-10-21 00:00:00+00:00. Split boundary 2026-06-14 12:00:00-04:00.

## Development period

| Metric | Value |
|---|---|
| Trades | 84 |
| Wins / losses | 48 / 36 |
| Win rate | 57.1% (95% CI 46.5% to 67.2%) |
| Avg win R / avg loss R | 0.935 / -0.974 |
| Expectancy R | +0.117 (95% CI -0.095 to +0.324) |
| Profit factor | 1.26 |
| Net profit after costs | $3,803.98 |
| Fees / price slippage | $759.52 / $598.00 |
| Ending equity | $53,803.98 |
| Max drawdown | $-3,366.36 (-6.5%) |
| Longest losing streak | 5 |
| Avg contracts / avg planned risk | 4.81 / 0.82% of equity |
| Exits | target 47, stop 35, flatten 2 |
| Signals | 186 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'limit_entries_disabled': 95, 'size_below_min': 4, 'occupied': 2, 'min_stop': 1, 'dual_side_sweep': 1} |

## Out-of-sample period

| Metric | Value |
|---|---|
| Trades | 37 |
| Wins / losses | 20 / 17 |
| Win rate | 54.1% (95% CI 38.4% to 69.0%) |
| Avg win R / avg loss R | 0.955 / -1.000 |
| Expectancy R | +0.057 (95% CI -0.261 to +0.374) |
| Profit factor | 1.21 |
| Net profit after costs | $1,491.52 |
| Fees / price slippage | $227.48 / $154.00 |
| Ending equity | $55,295.50 |
| Max drawdown | $-3,300.48 (-6.1%) |
| Longest losing streak | 6 |
| Avg contracts / avg planned risk | 3.27 / 0.83% of equity |
| Exits | target 20, stop 17 |
| Signals | 82 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'limit_entries_disabled': 39, 'size_below_min': 3, 'occupied': 1, 'pre_closure_window': 1, 'market_open_outside_zone': 1} |

## Full sample

| Metric | Value |
|---|---|
| Trades | 121 |
| Wins / losses | 68 / 53 |
| Win rate | 56.2% (95% CI 47.3% to 64.7%) |
| Avg win R / avg loss R | 0.941 / -0.982 |
| Expectancy R | +0.098 (95% CI -0.079 to +0.269) |
| Profit factor | 1.24 |
| Net profit after costs | $5,295.50 |
| Fees / price slippage | $987.00 / $752.00 |
| Ending equity | $55,295.50 |
| Max drawdown | $-3,366.36 (-6.5%) |
| Longest losing streak | 6 |
| Avg contracts / avg planned risk | 4.34 / 0.82% of equity |
| Exits | target 67, stop 52, flatten 2 |
| Signals | 268 |
| Limit orders placed / filled | 0 / 0 (nan%) |
| Expired / invalidated / cancelled at flatten | 0 / 0 / 0 |
| Skipped setups | {'limit_entries_disabled': 134, 'size_below_min': 7, 'occupied': 3, 'min_stop': 1, 'dual_side_sweep': 1, 'pre_closure_window': 1, 'market_open_outside_zone': 1} |

Ambiguous 1-minute sequences: {'fill_vs_invalidation': 0, 'stop_vs_target': 0, 'entry_and_exit_same_minute': 2}. Flagged trades: {'entry_and_exit_same_minute': 2}.

# 10-MNQ Liquidity Sweep -> First 1-Minute FVG: Development Results

Run date 2026-10-30. Development period 2022-10-02 to 2024-10-20, four chronological half-year folds.
Holdout 2024-10-21 to 2026-10-21 NOT run. Nine scenarios: stop offset 1, 2, 4 ticks x slippage 1, 2, 3 ticks.
Fixed 10 contracts, costs $0.94 per side, break-even at +1R by touch, limit target at +2R, 16:00 hard exit.
Level definitions and ambiguity resolutions of 2026-10-30 as agreed; see the implementation audit below.

## Nine scenarios, development period

Expectancy is net R per trade after fees and slippage, R = stop distance x $2 x 10 contracts. CI is a 95%
bootstrap interval. Folds are the four half-year expectancies in order.

| Stop offset | Slippage | Trades | Win rate | Avg win / loss R | Expectancy R | 95% CI | Profit factor | Net P&L | Max DD | Folds |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1467 | 20.9% | +1.91 / -0.74 | -0.183 | -0.24 to -0.13 | 0.69 | $-94,405 | $-99,281 | -0.12 / -0.17 / -0.18 / -0.26 |
| 1 | 2 | 1467 | 20.3% | +1.91 / -0.77 | -0.223 | -0.28 to -0.17 | 0.64 | $-115,995 | $-120,181 | -0.16 / -0.21 / -0.23 / -0.30 |
| 1 | 3 | 1467 | 19.6% | +1.91 / -0.79 | -0.259 | -0.32 to -0.20 | 0.60 | $-133,600 | $-137,370 | -0.19 / -0.23 / -0.29 / -0.32 |
| 2 | 1 | 1467 | 20.7% | +1.91 / -0.74 | -0.190 | -0.25 to -0.13 | 0.67 | $-103,050 | $-107,341 | -0.11 / -0.18 / -0.19 / -0.28 |
| 2 | 2 | 1467 | 19.9% | +1.91 / -0.76 | -0.228 | -0.29 to -0.17 | 0.63 | $-121,060 | $-125,276 | -0.17 / -0.20 / -0.26 / -0.29 |
| 2 | 3 | 1467 | 19.7% | +1.91 / -0.79 | -0.258 | -0.32 to -0.20 | 0.60 | $-134,190 | $-138,035 | -0.18 / -0.22 / -0.29 / -0.34 |
| 4 | 1 | 1467 | 20.4% | +1.91 / -0.73 | -0.195 | -0.25 to -0.14 | 0.65 | $-111,605 | $-115,956 | -0.14 / -0.16 / -0.22 / -0.27 |
| 4 | 2 | 1467 | 20.3% | +1.91 / -0.77 | -0.221 | -0.28 to -0.16 | 0.64 | $-120,410 | $-124,516 | -0.14 / -0.18 / -0.26 / -0.30 |
| 4 | 3 | 1467 | 20.2% | +1.92 / -0.79 | -0.243 | -0.30 to -0.18 | 0.62 | $-132,435 | $-136,350 | -0.17 / -0.21 / -0.27 / -0.32 |

The trade count is identical across scenarios because entries do not depend on the offset or slippage; only
fills and stops do.

## Walk-forward consistency

Every fold of every scenario is negative. The worst fold is the most recent (2024-04 to 2024-10) in all nine.
The pre-stated selection rule (best worst-fold expectancy at 2-tick slippage) picks a 2-tick stop offset with
a worst fold of -0.294 R; the alternatives are -0.296 R (1 tick) and -0.295 R (4 ticks). The three offsets
are indistinguishable.

## By session, stop 2 ticks, slippage 2 ticks

| Window | Trades | Win rate | Expectancy R | 95% CI | Profit factor | Net P&L |
|---|---|---|---|---|---|---|
| london | 503 | 22.1% | -0.217 | -0.32 to -0.11 | 0.71 | $-21,276 |
| ny_am | 488 | 18.0% | -0.232 | -0.33 to -0.13 | 0.61 | $-58,104 |
| ny_pm | 476 | 19.5% | -0.237 | -0.34 to -0.14 | 0.59 | $-41,679 |

## What happened inside the trades, stop 2 / slippage 2

* 1,467 entries from 3,201 sweep events: 953 failed to close back within three candles, 631 were invalidated by
  a 15-minute close, 81 died at the window end, 69 were dual-sided.
* Exits: 770 stopped (52%), 404 scratched at break-even (28%), 288 reached 2R (20%), 5 forced at 16:00.
  Of the 692 trades that reached +1R, 41.6% went on to +2R and 58.4% came back to entry.
* Median stop 15.5 points, median hold 10 minutes. Gross expectancy before any costs: -0.16 R. Fees $27,580
  and slippage $26,460 over two years account for the rest.
* Longs -0.18 R over 726, shorts -0.28 R over 741. 2022 Q4 -0.19 R, 2023 -0.20 R, 2024 -0.28 R.
* 80 trades had stop and target inside one minute and were resolved stop-first; 20 entered and exited in
  the same minute. Both are flagged in the trade files.
* Level sources behind the entered events: 1-minute swings 1,715, 15-minute swings 135, pre-window ranges
  191, previous session 6, previous RTH 7. The strategy as defined is, in practice, a fade of 1-minute swing
  points; the session reference levels almost never produce the entry.

## Conclusion

The strategy has a negative net expectancy on the development period in all nine scenarios, with every 95%
interval entirely below zero, every fold negative, every session negative, and both directions negative. The
gross result before costs is also negative, so this is not a cost problem. Under the pre-registered
standard, a positive expectancy with an interval above zero and fold consistency, the evidence points the
other way with 1,467 trades per scenario.

Running the holdout would be a formality: a result this far below zero on two years does not reverse on the
next two. The configuration the selection rule freezes is stop offset 2 ticks. It is presented for the record
and I do not recommend spending the holdout on it.

## Implementation audit

* 89 tests pass, including: 2/2 pivot confirmation with ties, 60-minute eligibility from the pivot bar with
  tradeability from confirmation, dedup with label merging, consumption on any penetration, multi-candle
  same-side grouping confirmed on the most extreme level, three-candle limit counting the penetration candle,
  dual-sided rejection on one candle and across candles with search continuing, 15-minute invalidation
  strict and with priority over an FVG on the same candle, first FVG in direction including on the
  confirmation candle, opposite FVGs ignored, setups dying at the window end, early-close force exit and
  absent PM window, 16:00 hard exit, break-even scratch arithmetic, one trade per window, and a real-data
  truncation test proving no lookahead plus a per-trade recomputation from raw minutes.
* Data: 1,434,204 continuous minutes 2022-10-02 to 2026-10-21, 0 bars outside sessions, forward-adjusted
  with 16 roll offsets; signals in adjusted space, fills recorded in contract prices.
* Assumption not in the specification: pre-window levels are eligible only during their own window.
* The holdout period overlaps data used by earlier, different strategies in this project, as disclosed.
* 1-minute bars only; no tick sequencing available.

## Files

results/sweep_fvg/dev/: summary.json, trades_<scenario>.csv (timestamps in UTC and New York, direction,
liquidity sources, FVG candle, entry, stop, target, exit reason, fees, slippage, net R, flags),
events_<scenario>.csv (every sweep event and its outcome), equity_<scenario>.csv, levels_stop2_slip2.csv.

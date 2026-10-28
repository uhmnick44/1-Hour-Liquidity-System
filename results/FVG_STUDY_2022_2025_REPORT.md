# FVG Strategy on 2022-10-02 to 2025-09-30: Out-of-Sample Study

Run date 2026-10-28. Single block, no development split, baseline costs (2 ticks). Three rule sets, each fully
specified on the 2025-2026 development year before this block was touched, run once each with nothing changed
afterwards. Engine, sizing, costs, calendar and rolls as in V1. The 2025-10-01 overlap day is excluded.

| Variant | Trades | Win rate | Avg win R / loss R | Expectancy R | 95% CI | Profit factor | Net after costs | Max DD | Longest losing streak |
|---|---|---|---|---|---|---|---|---|---|
| A: 09:30-11:30 NY, stop at reversal wick, 1:1 (latest rule set) | 285 | 46.7% | +0.91 / -1.00 | -0.108 | -0.22 to +0.00 | 0.79 | -$12,262 | -27.0% | 7 |
| B: all hours, doubled stop, 1:1 (original FVG spec) | 903 | 48.3% | +0.93 / -0.99 | -0.062 | -0.12 to +0.00 | 0.85 | -$20,020 | -46.4% | 9 |
| C: all hours, stop at wick, break-even at 1R, target 2R | 896 | 25.0% | +1.82 / -0.69 | -0.060 | -0.14 to +0.02 | 0.89 | -$17,363 | -41.3% | 23 |

By year:

| Variant | 2022 (Q4) | 2023 | 2024 | 2025 (to Sep) |
|---|---|---|---|---|
| A expectancy R (trades) | -0.23 (20) | -0.12 (102) | -0.10 (92) | -0.06 (71) |
| B expectancy R (trades) | -0.14 (74) | -0.11 (307) | -0.03 (307) | -0.02 (215) |
| C expectancy R (trades) | -0.14 (73) | -0.10 (292) | -0.00 (300) | -0.06 (231) |

Both directions lose in every variant. Variant A: longs -0.10 R over 145, shorts -0.11 R over 140.
Variant B: 1,349 setups, 903 entered, 397 expired with no FVG in 15 minutes. Variant A: 1,171 sweeps fell
outside the session window.

## Conclusion

None of the three rule sets has a positive expectancy on three years it had no part in shaping. All three
intervals have their upper end at or just below zero. Every calendar year is negative for every variant, with
2024 the closest to flat. The development-year results (-0.02 R, -0.18 R, -0.05 R for B, C, A) were not
better than this; they were simply one year's noise around the same slightly negative mean.

The win rate at 1:1 sits between 46.7% and 48.3% on 285 to 903 trades. That is the signature of an entry
with no directional information at the horizon of its own stop: a random entry with a symmetric stop and
target wins about half the time and loses the costs. The exit variants only change how the costs are paid.

Taken together with V1 and V2, five rule sets built on this engine's levels have now been tested on this
block, and all five lose. The common element is the premise that a swept 1H swing high or low produces a
tradeable reversal within the next hours, whether confirmed by a 1H close-back or a 1-minute FVG. On MNQ
over 2022 to 2026, under these definitions and costs, it does not.

## What is and is not established

* Established: these specific mechanical definitions have no edge. The sample sizes are large enough that
  this is not a power problem.
* Not established: anything about discretionary versions of the idea, other level definitions (session
  highs and lows, prior-day extremes, equal highs only), other instruments or other timeframes. None of those
  was tested, and this block has now been used, so testing them here would be exploration, not a test.

## Reproduction

```
python scripts/run_fvg_backtest.py --dataset 2022_2025 --single-block --sweep-mode intrabar_1m --slippage-ticks 2 --stop-multiple 1.0 --exit-mode fixed_1r --min-stop-points 10 --session 09:30-11:30
python scripts/run_fvg_backtest.py --dataset 2022_2025 --single-block --sweep-mode intrabar_1m --slippage-ticks 2
python scripts/run_fvg_backtest.py --dataset 2022_2025 --single-block --sweep-mode intrabar_1m --slippage-ticks 2 --stop-multiple 1.0 --exit-mode be_at_1r_tp_2r --min-stop-points 10
```

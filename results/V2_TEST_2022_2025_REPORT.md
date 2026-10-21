# V2 on Unseen Data: 2022-10-02 to 2025-09-30

Run date 2026-10-21. This is the pre-registered test of the frozen V2 rule (market entries only,
all other V1 rules unchanged) on three years of MNQ history that played no part in specifying V1
or selecting V2. One run per cost scenario, no development split, nothing changed after seeing it.

Data: Databento GLBX.MDP3 ohlcv-1m, 13 front contracts Z2 through Z5, 1,060,704 continuous minutes,
17,685 hourly bars, 12 fixed-Friday rolls with tick-valid offsets, 0 bars outside sessions after
the documented calendar overrides (seven 13:15 ET day-before-holiday closes and the omitted
2025-01-09 session, all pending user verification against CME). The test ends 2025-10-01 00:00 UTC,
so the one overlapping day in the download is excluded.

## Result

| Scenario | Trades | Win rate (95% CI) | Avg win R / loss R | Expectancy R (95% CI) | Profit factor | Net after costs | Ending equity | Max drawdown | Longest losing streak |
|---|---|---|---|---|---|---|---|---|---|
| Optimistic, 1 tick | 365 | 43.8% (38.8 to 49.0) | +0.90 / -0.99 | -0.163 (-0.263 to -0.063) | 0.71 | -$19,809 | $30,191 | -43.6% | 11 |
| Baseline, 2 ticks | 364 | 43.1% (38.1 to 48.3) | +0.90 / -0.99 | -0.179 (-0.276 to -0.080) | 0.68 | -$21,526 | $28,474 | -46.9% | 11 |
| Conservative, 4 ticks | 363 | 43.0% (38.0 to 48.1) | +0.88 / -0.99 | -0.187 (-0.281 to -0.089) | 0.66 | -$22,559 | $27,441 | -49.0% | 11 |

Baseline by year (exit year) and by direction:

| Year | Trades | Win rate | Expectancy R | Profit factor | Net |
|---|---|---|---|---|---|
| 2022 (Oct to Dec) | 28 | 53.6% | +0.030 | 1.05 | +$260 |
| 2023 | 138 | 40.6% | -0.227 | 0.60 | -$12,232 |
| 2024 | 112 | 50.0% | -0.061 | 0.86 | -$2,401 |
| 2025 (Jan to Sep) | 86 | 34.9% | -0.323 | 0.48 | -$7,153 |

| Direction | Trades | Win rate | Expectancy R (95% CI) | Net |
|---|---|---|---|---|
| Long | 175 | 37.7% | -0.276 (-0.41 to -0.14) | -$15,908 |
| Short | 189 | 48.1% | -0.088 (-0.23 to +0.04) | -$5,618 |

Reference, the V1 parent rule with limit entries on the same period, 2 ticks: 554 trades,
expectancy -0.116 R (95% CI -0.193 to -0.036), profit factor 0.77, net -$22,336, max drawdown -50.8%.

Order statistics, baseline: 740 signals, 327 skipped as limit-type, 18 occupied, 15 size below
minimum, 11 dual-side, 9 minimum stop, 4 open outside zone, 2 pre-closure, 1 invalid stop.
Ambiguous minutes: 3 stop-versus-target, 6 entry-and-exit in the same minute, resolved adverse-first.
Trade rate 121 per year, matching the 2025 to 2026 year.

## Conclusion

**V2 has a negative expectancy on data it did not influence, and the interval excludes zero.**
At -0.18 R per trade with a 95% interval of -0.28 to -0.08 R, this is not a case of insufficient
evidence. The rule loses money in every cost scenario, in three of four calendar years, on both
sides, with the long side worse. The V1 parent rule loses on the same period too.

The +0.10 R seen on 2025 to 2026 is now best explained as that year's noise plus selection: the
market-only split was the better-looking half of one year's trades, and the next three years did
not repeat it.

Trading implication: neither V1 nor V2 should be traded. The liquidity-sweep-and-close-back setup,
with a stop at twice the distance to the wick extreme and a 1:1 target, does not have an edge on
MNQ 1H over 2022 to 2026 under these execution assumptions.

## What this does not say

* It does not say the engine's levels are useless. It says this particular entry, stop and target
  built on them lose. The same levels with a different thesis are a different strategy.
* It does not cover other instruments or timeframes.
* The calendar overrides for 2022 to 2024 are inferred from data and still await verification;
  they affect only the flatten minute on seven afternoons and cannot move a 364-trade result.

## Reproduction

```
python scripts/run_backtest.py --dataset 2022_2025 --single-block --entry-mode market_only --prefix v2_test_2022_2025_ --sensitivity
python scripts/run_backtest.py --dataset 2022_2025 --single-block --entry-mode market_and_limit --prefix v1_ref_2022_2025_ --slippage-ticks 2 --label baseline_2ticks
```

# MNQ V2 Candidate Experiment: Market Entries Only

Run date 2026-10-21. Exploratory. The hypothesis (drop EQ limit entries) was selected after
reviewing V1's development and out-of-sample splits, so these periods cannot validate it. V1
remains the immutable baseline (`entry_mode="market_and_limit"`, the config default). V2 is
`entry_mode="market_only"`: a setup that would have produced an EQ limit order is skipped and the
system stays available. Every other rule, cost, calendar and roll setting is identical. V2 was run
independently through the full chronological dataset, not filtered from V1's log.

## V1 versus V2, baseline 2 ticks, same periods

| Period | Version | Trades | Win rate | Expectancy R | 95% CI | Profit factor | Net P&L | Max DD |
|---|---|---|---|---|---|---|---|---|
| Development | V1 | 147 | 47.6% | -0.057 | -0.21 to +0.10 | 0.90 | -$2,865 | -8.9% |
| Development | V2 | 84 | 57.1% | +0.117 | -0.10 to +0.32 | 1.26 | +$3,804 | -6.5% |
| Out-of-sample | V1 | 62 | 46.8% | -0.083 | -0.33 to +0.17 | 0.89 | -$1,341 | -8.7% |
| Out-of-sample | V2 | 37 | 54.1% | +0.057 | -0.26 to +0.37 | 1.21 | +$1,492 | -6.1% |
| Full sample | V1 | 209 | 47.4% | -0.064 | -0.20 to +0.07 | 0.90 | -$4,206 | -14.6% |
| Full sample | V2 | 121 | 56.2% | +0.098 | -0.08 to +0.27 | 1.24 | +$5,296 | -6.5% |

Slippage sensitivity, V2 full sample: 1 tick +0.110 R, 2 ticks +0.098 R, 4 ticks +0.063 R.
V2 out-of-sample: 1 tick +0.059 R, 2 ticks +0.057 R, 4 ticks +0.106 R (path dependence, as in V1).

## V2 market longs and shorts

| Direction | Period | Trades | Win rate (Wilson 95%) | Expectancy R | 95% CI | Profit factor | Net P&L |
|---|---|---|---|---|---|---|---|
| Long | Development | 38 | 52.6% (37 to 68) | +0.062 | -0.25 to +0.38 | 1.14 | +$1,014 |
| Long | Out-of-sample | 22 | 45.5% (27 to 65) | -0.105 | -0.47 to +0.34 | 0.80 | -$986 |
| Short | Development | 46 | 60.9% (46 to 74) | +0.162 | -0.12 to +0.43 | 1.36 | +$2,790 |
| Short | Out-of-sample | 15 | 66.7% (42 to 85) | +0.294 | -0.22 to +0.69 | 2.17 | +$2,478 |
| Long | Full | 60 | 50.0% | +0.001 | -0.26 to +0.25 | 1.00 | +$27 |
| Short | Full | 61 | 62.3% | +0.194 | -0.05 to +0.42 | 1.53 | +$5,268 |

## Eligibility verification

* Signals are engine-driven and identical in both runs: 268.
* All 135 limit-type signals in V2 were skipped (134 `limit_entries_disabled`, 1 pre-closure).
  None created an order and none occupied the slot.
* `occupied` skips fell from 15 in V1 to 3 in V2.
* 108 trades are common to both runs with identical entries and exits; 28 of them differ only in
  contract count because the realized-equity path differs.
* 13 trades exist only in V2. They are signals that V1 skipped as occupied while a limit order was
  pending or filled. Net -$382, expectancy -0.09 R. 1 V1 trade is absent in V2 because a freed-slot
  trade was open when its signal arrived.
* Unit test: a limit-type signal under V2 leaves the system free and the next signal is taken,
  while V1 marks it occupied.

## Reading

V2's improvement over V1 is the arithmetic consequence of removing the 100 limit trades that the
hypothesis was chosen on. The only information in this run that V1's splits did not already
contain is the 13 freed-slot trades, and they were slightly negative. The out-of-sample
expectancy of +0.057 R with an interval of -0.26 to +0.37 R on 37 trades is consistent with zero.
The short-side numbers are the strongest in the table and still include zero in every interval.

Nothing here is evidence of an edge. It is a well-defined, pre-stated V2 rule ready to be tested
on data it has not seen: MNQ history before 2025-10-01 from the same Databento dataset, or forward
data from now. At roughly 115 V2 trades a year, two to three years of prior history would give a
sample large enough to resolve a +0.1 R effect.

## Reproduction

```
python scripts/run_backtest.py --entry-mode market_only --prefix v2_ --sensitivity
```
Outputs under `results/v2_<label>/`.

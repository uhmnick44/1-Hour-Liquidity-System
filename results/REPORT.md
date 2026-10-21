# MNQ 1H Liquidity Sweep Reversal, V1: Backtest Results and Limitations

Run date 2026-10-21. Branch `claude/1h-liquidity-sweep-strategy-unn2bw`, commit after `c78ab13`.
All figures are **simulated** results on historical Databento 1-minute data. Nothing here is a live or forward-test result.

## 1. What was tested

The approved V1 rules, unchanged: engine levels from the verified port of `engine/bsl_ssl.pine`
(swing 5, max 8 per side, Wick, Keep & recolor); same-candle strict sweep and close-back on 1H;
EQ of the sweep candle; market entry at the next 1-minute open when the close is in premium
(short) or discount (long) or exactly at EQ, otherwise a limit at EQ for three completed candles with
strict wick invalidation; stop = 2x the distance from the actual fill to the sweep extreme,
minimum 10 points; 1:1 target; 1% of realized equity with costs in the risk per contract,
whole contracts, cap 10; one setup at a time; flatten 15 minutes before any closure longer
than 24 hours and before the fixed-Friday roll; fees $0.94 per side; adverse slippage on
market, stop and flatten fills only.

Data: 373,500 continuous minutes, 6,228 hourly bars, 2025-10-01 00:00 UTC to 2026-10-21 00:00 UTC,
front contracts Z5, H6, M6, U6, Z6 rolled on 2025-12-12, 2026-03-13, 2026-06-12, 2026-09-11 with
forward offsets of 253.25, 214.25, 293.25 and 299.75 points.

Split, fixed before the first run: development 2025-10-01 to 2026-06-14 12:00 ET, out-of-sample
2026-06-14 12:00 ET to 2026-10-21. The out-of-sample period was run once per scenario and nothing
was changed after seeing it.

## 2. Results

Baseline, 2 ticks adverse slippage. Development / out-of-sample / full.

| Metric | Development | Out-of-sample | Full sample |
|---|---|---|---|
| Trades | 147 | 62 | 209 |
| Win rate | 47.6% (CI 39.7 to 55.7) | 46.8% (CI 34.9 to 59.0) | 47.4% (CI 40.7 to 54.1) |
| Avg win R / avg loss R | +0.94 / -0.97 | +0.96 / -1.00 | +0.95 / -0.98 |
| Expectancy, R | -0.057 (CI -0.21 to +0.10) | -0.083 (CI -0.34 to +0.17) | -0.064 (CI -0.20 to +0.07) |
| Profit factor | 0.90 | 0.89 | 0.90 |
| Gross P&L before costs | -$1,848 | -$1,061 | -$2,909 |
| Fees / price slippage | $1,017 / $631 | $280 / $153 | $1,297 / $784 |
| Net profit after costs | -$2,865 | -$1,341 | -$4,206 |
| Ending equity | $47,135 | $45,794 | $45,794 |
| Max drawdown | -$4,578 (-8.9%) | -$4,180 (-8.7%) | -$7,460 (-14.6%) |
| Longest losing streak | 7 | 6 | 7 |
| EQ limit orders placed / filled | 88 / 72 (81.8%) | 32 / 28 (87.5%) | 120 / 100 (83.3%) |
| Expired / invalidated | 15 / 1 | 4 / 0 | 19 / 1 |
| Skipped setups | occupied 11, size below min 11, min stop 1, dual-side 1 | size below min 9, occupied 4, min stop 1, pre-closure 1, open outside zone 1 | 20 / 15 / 2 / 1 / 1 / 1 |

CI is a 95% interval: Wilson for win rate, bootstrap (5,000 resamples) for expectancy.
R is net P&L divided by planned dollar risk, so a stop exit is exactly -1 R and a target exit is
slightly below +1 R because the planned risk includes fees and stop slippage that a target exit
does not pay.

Sensitivity to slippage (full sample / out-of-sample):

| Scenario | Trades | Expectancy R | Profit factor | Net after costs | OOS net | OOS expectancy R |
|---|---|---|---|---|---|---|
| Optimistic, 1 tick | 209 | -0.063 | 0.89 | -$4,304 | -$1,735 | -0.096 |
| Baseline, 2 ticks | 209 | -0.064 | 0.90 | -$4,206 | -$1,341 | -0.083 |
| Conservative, 4 ticks | 207 | -0.068 | 0.91 | -$3,618 | +$547 | -0.023 |

The conservative scenario is not monotonically worse. Slippage moves the fill, the fill moves the
stop and target, and a different stop changes which trades win; with 60 out-of-sample trades that
path dependence is larger than the cost difference. Treat the three scenarios as one answer:
expectancy near zero to slightly negative under every cost assumption.

Other facts from the baseline log: median hold 83 minutes, 90th percentile 9.2 hours, longest
23.6 hours; 17 of 209 trades hit the 10-contract cap; mean planned risk 0.80% of equity, below
the 1% budget because of whole-contract rounding and the cap; 4 flatten exits; 2 trades entered
and exited in the same minute; 1 limit filled on a gap-through open; 0 ambiguous fill-versus-
invalidation minutes and 0 ambiguous stop-versus-target minutes; no trade spanned the
2025-11-27/28 data gap.

Monthly and hourly tables are in `results/baseline_2ticks/monthly.csv` and `hourly_et.csv`.
Monthly net ranges from -$2,842 (June 2026) to +$1,618 (February 2026). Per-hour samples are
2 to 24 trades and should not be read as evidence of anything.

## 3. Conclusion on edge

**There is no evidence that V1 has a positive edge.** The point estimate is negative in
development, out-of-sample and full sample, and the full-sample 95% interval for expectancy
(-0.20 R to +0.07 R) excludes anything better than a small positive edge. Gross expectancy
before any costs is -0.049 R, so this is not a cost problem. The out-of-sample result agrees
with development, so it is not an overfitting artefact either; there were no tunable
parameters to overfit.

With 209 trades the test cannot distinguish a true expectancy of -0.06 R from 0 R. It can rule
out an edge of +0.1 R or better with reasonable confidence.

One sub-sample observation, recorded as a hypothesis and not a rule: market entries (109
trades, +0.11 R) and limit entries (100 trades, -0.26 R) differ, and longs (98, -0.17 R) and
shorts (111, +0.03 R) differ. These are post-hoc splits of a sample that was not designed to
test them and the differences are within what random variation produces across several
comparisons. If either is worth pursuing it must be defined as a new variation and tested on
new data, not on this sample.

## 4. Interpretations made during implementation

Each of these was a gap in the written rules. The choice is documented in code and here; none
is hidden. Say if any should change, and the backtest will be rerun.

1. A signal whose confirming candle closes at or after the session's flatten cutoff is skipped
   (`pre_closure_window`), because the order it would create could only execute after the
   closure. One occurrence.
2. At a 1H close, a pending limit's expiry is processed before that candle's signal is
   evaluated, so the slot is free for a signal on the third candle.
3. A limit filled by a gap-through open at exactly the sweep extreme is cancelled, since the
   stop distance would be zero. Zero occurrences.
4. A limit filled by a gap-through open closer to the extreme than the limit keeps its planned
   contracts and gets a tighter stop from the actual fill; if that stop is under 10 points the
   trade is kept and flagged. Zero occurrences with a sub-minimum stop.
5. Risk per contract = stop distance x $2 + $1.88 fees + stop-exit slippage. Entry slippage is
   already inside the fill from which the stop is measured and is not added twice.
6. Stops trigger on a touch (stop-market); targets and entry limits need a one-tick trade-
   through. The asymmetry is deliberate and conservative.
7. The dual-side rule uses the engine's sweep events, so a candle that swept both sides is
   skipped even if it closed back through only one.
8. The engine starts empty on 2025-10-01; its level set is incomplete for roughly the first six
   trading days. The first trade is on 2025-10-03.
9. Partial hourly bars at early closes count as candles, as they do on TradingView.
10. The 2025-11-27 21:45 to 2025-11-28 08:30 ET gap, present in both data sources, is treated as
    a closure shorter than 24 hours: no flatten, orders resume at the first bar after it.

## 5. Verification performed

* Engine parity: the Python port matches the TradingView indicator's level state on 7,024 of
  7,024 hourly bars after warm-up, and its events on Databento-built bars match TradingView's
  on 719 levels and 496 sweeps with zero mismatches.
* 40 tests: every Section 16 item on synthetic bars, determinism (identical logs on rerun),
  no-lookahead (results before three random cuts are identical when later data is removed),
  and an independent recomputation of every trade from raw minute data (signal candle,
  level breach, entry price, zone test, limit fill minute, no missed invalidation or earlier
  fill, stop and target arithmetic, sizing, no missed exit, P&L).
* A sign error in the roll adjustment was caught by the synthetic rollover test before any
  result was reported.

## 6. Simulated versus live execution

* Limit fills assume a one-tick trade-through guarantees a fill. Live, queue position can leave
  a resting order unfilled at the limit even after a trade-through. The 83% fill rate is an
  upper bound.
* Slippage is a fixed 2 ticks. Live slippage on stops during fast moves, at the Sunday open,
  and in the roll week's thinner contract can be larger. The 4-tick scenario bounds this.
* Market entries execute at the first trade of the next minute. Live, alert-to-order latency
  adds a few seconds and the fill can be any trade in that window.
* Intrabar order of events inside one minute is unknown; adverse-first was used. Zero ambiguous
  minutes occurred in this sample, so this assumption did not change any result.
* The TradingView indicator and the backtest agree on levels, but TradingView's bars differed
  from Databento's on 4 of 6,228 hours by up to 0.75 points. Live signals from the chart can
  occasionally differ from the backtest's.
* Live hourly bars must be built on the same clock-hour boundaries and the same session
  template as TradingView's. A platform using a different session template, for example a
  regular-hours-only template on NinjaTrader, will produce different candles and different
  levels.
* Rollover live depends on the platform's continuous-contract settings. The backtest rolled on
  a fixed Friday and never held a position across a roll.
* The engine's level set depends on how much history the chart loaded; after eight new pivots
  per side it converges, so a freshly loaded chart agrees with the backtest only after warm-up.
* Fees were taken from the broker's published plan and must be reconciled with statements.

## 7. Limitations

* One instrument, 12.7 months, one market regime. 209 trades is too few to estimate
  expectancy to better than about +/-0.13 R.
* Holiday closing times for 2025-11-28 and 2025-12-24 are user-verified overrides, not read
  from CME directly.
* The exchange calendar comes from a third-party library with two documented corrections;
  other dates were checked only against the data's first and last traded minute.
* The engine's pivot tie rule was established empirically from five cases in the export, all
  consistent; it is not documented by TradingView.
* No volume or liquidity filter was modelled; position size is capped at 10 contracts, which
  is small relative to MNQ volume, so market impact was ignored.

## 8. Reproduction

```
pip install -r requirements.txt
python -m pytest -q
python scripts/run_backtest.py --sensitivity
```
Outputs per scenario under `results/<label>/`: `summary.json`, `summary.md`, `trades.csv`,
`order_events.csv`, `signals.csv`, `equity_curve.csv`, `monthly.csv`, `hourly_et.csv`, `rolls.csv`.

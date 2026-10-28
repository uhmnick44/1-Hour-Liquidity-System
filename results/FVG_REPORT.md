# 1H Sweep -> 1M FVG -> Doubled Reversal-Extreme Stop: Development Run

Run date 2026-10-28. Rules as specified on 2026-10-28 with the four Section 16 decisions approved the
same day: intrabar sweep timestamp, 1:1 target from the fill, 10-point minimum doubled stop kept, one
active setup / order / position. Engine, sizing, costs, calendar and rolls as in V1.

This is the development run on 2025-10-01 to 2026-10-21. It is in-sample in the sense that any change
made after reading it contaminates this year. The 2022-10-02 to 2025-09-30 block has not been run
with this strategy and remains the sealed test.

## Results

| Slippage | Period | Trades | Win rate | Expectancy R | 95% CI | Profit factor | Net after costs | Max DD |
|---|---|---|---|---|---|---|---|---|
| 1 tick | Development | 210 | 48.6% | -0.042 | -0.17 to +0.09 | 0.92 | -$3,141 | -11.5% |
| 1 tick | Out-of-sample | 102 | 53.9% | +0.051 | -0.13 to +0.24 | 1.16 | +$2,965 | -5.4% |
| 1 tick | Full | 312 | 50.3% | -0.012 | -0.12 to +0.10 | 1.00 | -$177 | -11.5% |
| 2 ticks | Development | 210 | 48.1% | -0.053 | -0.18 to +0.08 | 0.90 | -$4,190 | -13.6% |
| 2 ticks | Out-of-sample | 102 | 53.9% | +0.049 | -0.14 to +0.24 | 1.16 | +$2,924 | -5.3% |
| 2 ticks | Full | 312 | 50.0% | -0.020 | -0.13 to +0.09 | 0.98 | -$1,266 | -13.6% |
| 4 ticks | Development | 210 | 47.6% | -0.066 | -0.20 to +0.07 | 0.88 | -$5,117 | -13.4% |
| 4 ticks | Out-of-sample | 100 | 53.0% | +0.032 | -0.16 to +0.23 | 1.10 | +$1,749 | -6.7% |
| 4 ticks | Full | 310 | 49.4% | -0.034 | -0.14 to +0.08 | 0.94 | -$3,368 | -15.1% |

Baseline, 2 ticks, full year: 467 setups from 467 sweeps that were not ignored; 312 entered, 144 expired
with no FVG inside 15 minutes, 9 rejected for size, 2 for the minimum stop. 123 further sweeps were
ignored while a setup, order or position was active. Median sweep-to-confirmation 7 minutes, median
doubled stop 71 points, median hold 44 minutes. Longs 152 trades at +0.05 R, shorts 160 at -0.09 R.
Gross P&L before costs +$764, so costs turn a flat result slightly negative.

## Reading

Expectancy is indistinguishable from zero in every scenario and both halves of the year. The full-year
interval of -0.13 R to +0.09 R rules out a meaningful edge in either direction on this sample. The
strategy trades about 2.6 times as often as V2, so the same year gives 312 trades instead of 121, which
is why the interval is tighter.

No claim of an edge is made. The sealed 2022-2025 block is the test, and it is only a test if nothing
in the rule set changes after this report.

## Reproduction

```
python scripts/run_fvg_backtest.py --dataset 2025_2026 --sweep-mode intrabar_1m --slippage-ticks 2
```

# 10-MNQ Sweep -> First 1-Minute FVG, Variant Without 1-Minute Swings: Development Results

Run date 2026-10-30. Second variant on the development period 2022-10-02 to 2024-10-20, requested after the first
development result; exploratory by construction. Only change: the 1-minute swing source is removed. The other
four sources (15-minute swings, previous session, previous RTH, pre-window ranges) and every other rule are as
before. Holdout 2024-10-21 to 2026-10-21 NOT run.

| Stop offset | Slippage | Trades | Win rate | Avg win / loss R | Expectancy R | 95% CI | Profit factor | Net P&L | Max DD | Folds |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 651 | 22.9% | +1.89 / -0.71 | -0.116 | -0.20 to -0.03 | 0.74 | $-33,409 | $-36,385 | -0.13 / -0.06 / -0.04 / -0.23 |
| 1 | 2 | 651 | 23.3% | +1.89 / -0.75 | -0.131 | -0.22 to -0.04 | 0.75 | $-34,619 | $-37,475 | -0.15 / -0.10 / -0.03 / -0.24 |
| 1 | 3 | 651 | 22.7% | +1.89 / -0.76 | -0.161 | -0.25 to -0.07 | 0.70 | $-41,909 | $-44,645 | -0.20 / -0.12 / -0.05 / -0.27 |
| 2 | 1 | 651 | 23.7% | +1.89 / -0.72 | -0.101 | -0.19 to -0.01 | 0.76 | $-31,869 | $-34,855 | -0.13 / -0.07 / +0.03 / -0.24 |
| 2 | 2 | 651 | 23.3% | +1.89 / -0.74 | -0.127 | -0.22 to -0.04 | 0.75 | $-34,879 | $-37,745 | -0.17 / -0.09 / -0.00 / -0.24 |
| 2 | 3 | 651 | 22.9% | +1.89 / -0.76 | -0.156 | -0.25 to -0.06 | 0.71 | $-41,234 | $-44,408 | -0.18 / -0.11 / -0.05 / -0.29 |
| 4 | 1 | 651 | 23.3% | +1.89 / -0.71 | -0.104 | -0.19 to -0.01 | 0.76 | $-32,849 | $-36,040 | -0.16 / -0.07 / +0.04 / -0.23 |
| 4 | 2 | 651 | 23.2% | +1.89 / -0.74 | -0.126 | -0.21 to -0.04 | 0.75 | $-35,084 | $-38,598 | -0.16 / -0.07 / -0.03 / -0.25 |
| 4 | 3 | 651 | 22.4% | +1.89 / -0.76 | -0.164 | -0.25 to -0.07 | 0.70 | $-43,704 | $-47,093 | -0.21 / -0.11 / -0.06 / -0.28 |

Selection rule (best worst-fold expectancy at 2-tick slippage) picks a 1-tick offset at -0.241 R versus -0.245 R
and -0.247 R; the offsets are indistinguishable.

## By session, stop 2 / slippage 2

| Window | Trades | Win rate | Expectancy R | 95% CI | Profit factor | Net P&L |
|---|---|---|---|---|---|---|
| london | 244 | 24.6% | -0.136 | -0.29 to +0.03 | 0.77 | $-8,027 |
| ny_am | 207 | 22.2% | -0.114 | -0.27 to +0.05 | 0.74 | $-16,312 |
| ny_pm | 200 | 23.0% | -0.129 | -0.28 to +0.04 | 0.74 | $-10,540 |

## Inside the trades, stop 2 / slippage 2

* 651 entries from 1,541 events: 511 no close-back, 288 invalidated at 15 minutes, 91 died at window end.
* Exits: 318 stopped (49%), 178 break-even (27%), 148 reached 2R (23%), 7 forced at 16:00. Of trades that
  reached +1R, 45% continued to 2R.
* Gross expectancy before costs -0.06 R. Median stop 15.5 points, median hold 11 minutes.
* Longs -0.11 R over 319, shorts -0.14 R over 332. Fold 3 (2023-10 to 2024-04) was flat at 0.00 R; the other
  three folds were -0.17, -0.09 and -0.24 R.
* Level sources behind entries: 15-minute swings 493, pre-window ranges 390, previous session 14, previous
  RTH 13. The session reference levels are still rarely the trigger, because the consumption rule retires
  them when price runs through them before the window opens.

## Reading

Removing the 1-minute swings cut the trade count by more than half and improved expectancy from about -0.23 R
to about -0.13 R at the baseline, but every scenario's 95% interval still lies entirely below zero, three of
four folds are negative in every scenario, and the gross result before costs is negative. Under the
pre-registered standard this is not an edge; it is a smaller loss.

Compared with the first run, the entries now come mostly from 15-minute swings and pre-window extremes. The
structural pattern is unchanged: after reaching +1R, price returns to entry more often than it extends.

The holdout should not be spent on this configuration.

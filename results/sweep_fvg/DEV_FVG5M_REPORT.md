# 10-MNQ Sweep -> First FVG on 5-Minute Candles: Development Results

Run date 2026-10-30. Fourth variant on the development period 2022-10-02 to 2024-10-20; exploratory. Change
from the previous variant: the FVG is formed by three clock-aligned 5-minute candles, confirmed when the third
completes, with the stop beyond their extreme. Sweep confirmation (three 1-minute candles), 15-minute
invalidation, next-1-minute-open entry, windows, no 1-minute swings, \$1,000 risk per trade, \$100,000 account:
unchanged. Holdout NOT run.

| Stop offset | Slippage | Trades | Win rate | Expectancy R | 95% CI | Profit factor | Net P&L | Max DD % | Contracts min / med / max | Folds |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 247 | 25.5% | -0.153 | -0.28 to -0.02 | 0.71 | $-36,339 | -47.6% | 3 / 14 / 72 | -0.09 / +0.11 / -0.37 / -0.27 |
| 1 | 2 | 247 | 24.3% | -0.184 | -0.31 to -0.05 | 0.65 | $-44,253 | -53.4% | 3 / 14 / 67 | -0.10 / +0.07 / -0.41 / -0.31 |
| 1 | 3 | 247 | 24.3% | -0.193 | -0.32 to -0.06 | 0.64 | $-45,992 | -54.9% | 3 / 14 / 62 | -0.10 / +0.06 / -0.43 / -0.32 |
| 2 | 1 | 247 | 24.7% | -0.169 | -0.30 to -0.03 | 0.68 | $-39,712 | -51.0% | 3 / 14 / 69 | -0.09 / +0.07 / -0.40 / -0.27 |
| 2 | 2 | 247 | 24.3% | -0.184 | -0.31 to -0.05 | 0.65 | $-43,925 | -53.1% | 3 / 14 / 65 | -0.10 / +0.07 / -0.41 / -0.31 |
| 2 | 3 | 247 | 24.7% | -0.189 | -0.32 to -0.06 | 0.65 | $-44,515 | -53.5% | 3 / 13 / 61 | -0.10 / +0.09 / -0.43 / -0.33 |
| 4 | 1 | 247 | 24.3% | -0.174 | -0.30 to -0.04 | 0.67 | $-41,616 | -51.9% | 3 / 14 / 65 | -0.08 / +0.08 / -0.40 / -0.31 |
| 4 | 2 | 247 | 24.7% | -0.175 | -0.30 to -0.04 | 0.67 | $-41,372 | -51.4% | 3 / 13 / 61 | -0.08 / +0.10 / -0.42 / -0.31 |
| 4 | 3 | 247 | 24.7% | -0.184 | -0.31 to -0.05 | 0.65 | $-44,152 | -53.8% | 3 / 13 / 57 | -0.09 / +0.08 / -0.43 / -0.32 |

Selection rule picks a 2-tick offset at a worst fold of -0.406 R (1 tick -0.407, 4 ticks -0.421).

## By session, stop 2 / slippage 2

| Window | Trades | Win rate | Expectancy R | 95% CI | Profit factor | Net P&L |
|---|---|---|---|---|---|---|
| London | 93 | 19.4% | -0.229 | -0.44 to -0.00 | 0.61 | -\$21,019 |
| New York AM | 93 | 26.9% | -0.199 | -0.39 to +0.00 | 0.61 | -\$17,551 |
| New York PM | 61 | 27.9% | -0.091 | -0.34 to +0.18 | 0.81 | -\$5,355 |

## Inside the trades, stop 2 / slippage 2

* 1,592 events: 532 no close-back, 486 invalidated at 15 minutes, 327 died at the window end, 247 entered. The
  slower FVG means far more setups run out of window: 327 versus 91 in the 1-minute version.
* Exits: 125 stopped (51%), 52 break-even (21%), 40 reached 2R (16%), 30 forced at 16:00 (12%). Of trades
  that reached +1R, 43.5% went on to 2R.
* Median stop 34 points (1-minute version 15.5), median hold 56 minutes, median entry 18 minutes after sweep
  confirmation. Median 14 contracts, max 65.
* Gross expectancy before costs -0.15 R. Longs -0.12 R over 127, shorts -0.25 R over 120.
* Folds: -0.10, +0.07, -0.41, -0.31 R. The one positive fold has 66 trades; the two following it are the
  worst of any variant so far.

## Reading

Wider stops, later entries, fewer trades, same answer. Expectancy is -0.15 to -0.19 R with every interval below
zero and the gross result negative before costs. The 1R-to-2R continuation rate is 43.5%, matching the 42 to
46% seen in every prior variant at every timeframe tried. The reversal after a swept level does not extend to
twice its first leg often enough to pay for the stop-outs, and changing the candle size of the entry does not
change that.

Not an edge. The holdout should not be spent on this configuration.

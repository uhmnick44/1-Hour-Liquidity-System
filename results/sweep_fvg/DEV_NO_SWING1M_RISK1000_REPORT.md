# 10-MNQ Sweep -> First 1-Minute FVG, No 1-Minute Swings, $1,000 Risk per Trade: Development Results

Run date 2026-10-30. Same entries and exits as the no-1-minute-swing variant; only the sizing differs.
Account $100,000 (used for return and drawdown percentages only). Each trade risks $1,000:
contracts = floor($1,000 / (stop points x $2 + $1.88 fees + stop-exit slippage)), no cap, no compounding.
R is net P&L divided by that planned risk, so a stop exit is -1.0 R. Development period 2022-10-02 to
2024-10-20. Holdout NOT run.

| Stop offset | Slippage | Trades | Expectancy R | 95% CI | Profit factor | Net P&L | Return on $100k | Max DD | Max DD % | Contracts min / median / max |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 651 | -0.106 | -0.19 to -0.02 | 0.79 | -$67,361 | -67.4% | -$71,930 | 71.9% | 4 / 30 / 112 |
| 1 | 2 | 651 | -0.116 | -0.20 to -0.03 | 0.78 | -$74,039 | -74.0% | -$78,551 | 78.6% | 4 / 29 / 101 |
| 1 | 3 | 651 | -0.141 | -0.22 to -0.06 | 0.73 | -$89,184 | -89.2% | -$93,465 | 93.5% | 4 / 29 / 91 |
| 2 | 1 | 651 | -0.093 | -0.17 to -0.01 | 0.81 | -$59,921 | -59.9% | -$64,490 | 64.5% | 4 / 30 / 106 |
| 2 | 2 | 651 | -0.114 | -0.20 to -0.03 | 0.78 | -$71,610 | -71.6% | -$76,030 | 76.0% | 4 / 29 / 96 |
| 2 | 3 | 651 | -0.138 | -0.22 to -0.05 | 0.74 | -$87,296 | -87.3% | -$90,793 | 90.8% | 4 / 28 / 87 |
| 4 | 1 | 651 | -0.096 | -0.18 to -0.01 | 0.81 | -$60,018 | -60.0% | -$64,603 | 64.6% | 4 / 29 / 96 |
| 4 | 2 | 651 | -0.114 | -0.19 to -0.03 | 0.78 | -$72,203 | -72.2% | -$75,845 | 75.8% | 4 / 28 / 87 |
| 4 | 3 | 651 | -0.146 | -0.22 to -0.06 | 0.72 | -$92,477 | -92.5% | -$95,984 | 96.0% | 4 / 27 / 80 |

Folds (stop 2, slippage 2): -0.16, -0.08, -0.01, -0.22 R. By session: London -$27,893, New York AM -$20,870,
New York PM -$22,848. No trade was skipped for size: every stop fit at least four contracts in $1,000.

## Reading

Sizing does not change which trades are taken or how they exit, so the picture is the one from the previous
report: every interval below zero, three of four folds negative, gross before costs negative. The small change
in R (about -0.13 to about -0.11) is a definitional one: R now includes fees and slippage in the denominator.

What the dollar sizing adds is scale. Risking a fixed $1,000 on a median 15-point stop means a median of 29
MNQ contracts and up to 112, with 63 trades above 50 contracts. At that size the 1-, 2- and 3-tick slippage
assumptions are optimistic, so the real result would be worse than the table. A negative expectancy sized to
$1,000 a trade over 651 trades loses $60,000 to $92,000 of a $100,000 account, with drawdowns of 65% to 96%.

Not an edge. The holdout should not be spent on this configuration.

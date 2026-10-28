# FVG Strategy, Stop Update of 2026-10-28: Stop at (doubled distance x 0.5), Break-even at 1R, Target 2R

Run date 2026-10-28, development year 2025-10-01 to 2026-10-21, baseline costs (2 ticks). Entry, 15-minute
window, sweep timestamp, one-active rule, sizing, costs, calendar and rolls unchanged from the FVG run.
Stop distance = (entry-to-wick distance x 2) x 0.5 = the entry-to-wick distance: the stop is placed exactly at
the reversal wick. Exit: stop moves to the entry fill when +1R is touched; target is a limit at +2R, where R is
the new stop distance. Run twice: with the existing 10-point minimum stop and with it disabled, pending the
user's confirmation of that rule.

| Min stop | Period | Trades | Win rate | Avg win R / loss R | Expectancy R | 95% CI | Profit factor | Net after costs | Max DD |
|---|---|---|---|---|---|---|---|---|---|
| 10 pts | Development | 221 | 15.8% | +1.85 / -0.67 | -0.271 | -0.40 to -0.14 | 0.49 | -$21,030 | -43.9% |
| 10 pts | Out-of-sample | 109 | 25.7% | +1.87 / -0.64 | +0.009 | -0.21 to +0.23 | 1.05 | +$655 | -7.9% |
| 10 pts | Full | 330 | 19.1% | +1.86 / -0.66 | -0.179 | -0.29 to -0.06 | 0.62 | -$20,375 | -45.2% |
| none | Development | 234 | 15.8% | +1.84 / -0.67 | -0.271 | -0.40 to -0.14 | 0.50 | -$21,264 | -44.4% |
| none | Out-of-sample | 111 | 25.2% | +1.87 / -0.64 | -0.003 | -0.22 to +0.21 | 1.02 | +$258 | -8.0% |
| none | Full | 345 | 18.8% | +1.86 / -0.66 | -0.185 | -0.30 to -0.07 | 0.62 | -$21,006 | -45.7% |

Exits, full year with the 10-point minimum: stopped 171 (52%), scratched at break-even 95 (29%), target 62
(19%), flattened 2. Median placed stop 37.6 points, median hold 17 minutes. The 10-point minimum rejected 15
setups and changed nothing material.

## Reading

Placing the stop at the reversal wick halves the stop, which doubles the position size for the same 1% risk and
puts the stop where price returned 52% of the time within a median of 17 minutes. Of the trades that survived
to +1R, 61% came back to entry and 39% reached +2R. Scratches are not free: 95 of them paid slippage and fees.
The result is -0.18 R over 330 trades with the interval entirely below zero, and a 45% drawdown.

The last third of the year is flat, the first two thirds are strongly negative. Both are consistent with the
same negative or zero expectancy; neither supports an edge.

Compared with the two earlier exits on the same entries: doubled stop with 1:1 was -0.02 R; this is -0.18 R.
The entry has no directional information at these horizons, so the exit rule only changes how the costs are
paid, and this one pays them through frequent stop-outs and scratches.

No edge is claimed. The 2022-2025 block remains sealed.

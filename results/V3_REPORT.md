# MNQ V3 Candidate Experiment: Break-even at 1R, Target at 2R

Run date 2026-10-21. Exploratory: third rule chosen after reviewing results on the same year of data.
`exit_mode="be_at_1r_tp_2r"`: when price touches entry plus one stop distance in the trade's
favour, the stop moves to the entry fill (stop-market, 2 ticks slippage when hit). The target is a
limit at entry plus two stop distances, one-tick trade-through, no slippage. Adverse-first within a
minute: original stop, then break-even stop, then target. Everything else as V1/V2. Sizing unchanged.
Baseline costs, 2 ticks.

| Period | Version | Trades | Win rate | Avg win R / loss R | Expectancy R | 95% CI | Profit factor | Net P&L | Max DD |
|---|---|---|---|---|---|---|---|---|---|
| Development | V2 (1:1) | 84 | 57.1% | +0.94 / -0.97 | +0.117 | -0.10 to +0.32 | 1.26 | +$3,804 | -6.5% |
| Development | V3 market-only | 84 | 23.8% | +1.83 / -0.58 | -0.003 | -0.24 to +0.24 | 0.96 | -$640 | -8.5% |
| Out-of-sample | V2 (1:1) | 37 | 54.1% | +0.96 / -1.00 | +0.057 | -0.26 to +0.37 | 1.21 | +$1,492 | -6.1% |
| Out-of-sample | V3 market-only | 36 | 25.0% | +1.94 / -0.61 | +0.031 | -0.35 to +0.44 | 1.15 | +$933 | -6.1% |
| Full | V2 (1:1) | 121 | 56.2% | +0.95 / -0.98 | +0.098 | -0.08 to +0.27 | 1.24 | +$5,296 | -6.5% |
| Full | V3 market-only | 120 | 24.2% | +1.87 / -0.59 | +0.007 | -0.20 to +0.21 | 1.01 | +$294 | -11.8% |
| Full | V3 with limits (V1 base) | 196 | 19.9% | +1.85 / -0.66 | -0.156 | -0.31 to +0.00 | 0.70 | -$10,692 | -27.8% |

V3 market-only exits, full sample: 52 stopped before reaching 1R, 38 reached 1R and came back to
entry (scratch, about -0.03 R each after slippage and fees), 28 reached 2R, 2 flattened.

## Reading

The same 120 entries that won 68 times at 1R under V2 won 28 times at 2R under V3. Of the trades
that reached 1R, 42% went on to 2R and 58% returned to entry. That continuation rate is what the
exit change hinges on, and at 42% the extra R on the winners is cancelled by the 1R wins given back.
The result is an expectancy of zero with a deeper drawdown.

This is one year, 120 trades, and a rule picked after seeing V2. It is not evidence that 1:1 is the
right target. It is evidence that, on this sample, price returned to entry after a 1R move more often
than it extended to 2R, which is consistent with the mean-reverting character of the setup itself.

## Reproduction

```
python scripts/run_backtest.py --entry-mode market_only --exit-mode be_at_1r_tp_2r --prefix v3_market_only_ --slippage-ticks 2 --label baseline_2ticks
python scripts/run_backtest.py --entry-mode market_and_limit --exit-mode be_at_1r_tp_2r --prefix v3_with_limits_ --slippage-ticks 2 --label baseline_2ticks
```

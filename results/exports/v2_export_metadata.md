# V2 Trade Export: Configuration and Validation Notes

Exported 2026-10-22 from existing result files. No backtest was rerun and no logic, data or
assumption was changed. Source files: `results/v2_baseline_2ticks/trades.csv` and
`results/v2_test_2022_2025_baseline_2ticks/trades.csv`, produced by commits `67d6635` and `ab15181`.

## Runs included

`v2_trade_export.csv` holds one row per completed trade from the two V2 baseline runs, distinguished
by the `backtest_run` column. `trade_id` restarts at 1 in each run.

| backtest_run | Period | Role | Trades | Net P&L | Ending equity |
|---|---|---|---|---|---|
| v2_2025_2026_in_sample | 2025-10-01 to 2026-10-21 | The year V1 was specified on and V2 was selected from. In-sample. | 121 | +$5,295.50 | $55,295.50 |
| v2_2022_2025_unseen_test | 2022-10-02 to 2025-10-01 | Pre-registered test on data that did not influence V2. | 364 | -$21,526.24 | $28,473.76 |

Each run starts from $50,000. The two equity paths are independent.

## Reconciliation

| Check | v2_2025_2026_in_sample | v2_2022_2025_unseen_test |
|---|---|---|
| Trades in CSV vs summary.json | 121 vs 121 | 364 vs 364 |
| Net P&L in CSV vs summary.json | $5,295.50 vs $5,295.50 | -$21,526.24 vs -$21,526.24 |
| Ending equity in CSV vs summary.json | $55,295.50 vs $55,295.50 | $28,473.76 vs $28,473.76 |
| net_pnl = gross_pnl - commissions on every row | true | true |
| Exit reasons | target 67, stop 52, flatten 2 | stop 205, target 149, flatten 9, end_of_data 1 |

No discrepancies. All losses and all flattened trades are included. There are no breakeven exits in
V2 because V2 uses the fixed 1:1 exit; the break-even exit only exists in the separate V3 experiment.

## V2 configuration (identical in both runs)

* Engine: `engine/bsl_ssl.pine` port, swing strength 5, max 8 levels per side, Wick sweep trigger,
  Keep & recolor, pivot tie rule left-inclusive right-strict (verified against TradingView).
* Signal: 1H candle, strict high above a buy-side level and strict close below it (short), mirror for
  long. Candle skipped if it swept both sides. EQ = (high + low) / 2 of the sweep candle.
* Entry mode `market_only`: short when close > EQ or close = EQ, long when close < EQ or close = EQ.
  Setups that would have placed an EQ limit order are skipped and do not occupy the system.
* Market entry: raw open of the first 1-minute bar after the confirming 1H close; skipped if that open
  is on the wrong side of EQ; fill = open moved 2 ticks against the trade.
* Stop = fill + 2 x (sweep extreme - fill) in the adverse direction; minimum doubled distance 10
  points; target = 1:1 from the fill. Stop is a stop-market (touch triggers, 2 ticks slippage);
  target is a limit (one-tick trade-through, no slippage). Adverse-first inside a minute.
* Sizing: floor(1% of realized equity / (stop points x $2 + $1.88 fees + $1.00 stop slippage)),
  1 to 10 contracts, else skip. One position or order at a time.
* Costs: $0.39 commission + $0.36 exchange/NFA + $0.19 clearing per contract per side = $0.94;
  2 ticks ($1.00) adverse slippage on market, stop and flatten fills; none on target fills.
* Calendar: CME equity sessions with documented overrides; flatten 15 minutes before any closure
  longer than 24 hours and before each fixed-Friday roll (Friday before expiry week).
* Data: Databento GLBX.MDP3 ohlcv-1m, individual MNQ contracts, forward-adjusted continuous series;
  1H bars built on New York clock hours. Prices in `*_price` columns are in the adjusted series the
  strategy traded; `*_price_contract` columns are the actual contract prices (adjusted minus the
  cumulative roll offset).

## Column notes

* `commissions`: total fees per trade (commission + exchange/NFA + clearing, both sides, all contracts).
* `slippage_cost`: dollar value of the slippage ticks applied to the entry and exit fills. It is
  already inside `entry_price`, `exit_price` and therefore `gross_pnl`. Do not subtract it again.
  `net_pnl = gross_pnl - commissions`.
* `realized_R_after_costs`: net_pnl / planned_risk_usd. A stop exit is exactly -1.0 by construction.
  `price_R`: points gained / stop distance, before costs.
* `entry_session`: a labelling convention only, by entry hour New York: asia_18_02, london_03_08,
  new_york_09_16, evening_17_23. The strategy has no session logic. `entry_hour_et` is provided so
  the buckets can be redefined.
* `liquidity_level_type`: buy_side_liquidity for shorts (a swept swing high), sell_side_liquidity
  for longs (a swept swing low). `level_price` is the most significant qualifying level; `levels_swept_and_closed_back` counts them.
* `sweep_datetime`: open of the 1H sweep candle. `sweep_candle_close_datetime` and
  `setup_confirmation_datetime` are the same instant: the setup is confirmed at that close.
* `flags`: `entry_and_exit_same_minute`, `ambiguous_stop_vs_target`, `gap_stop`, `gap_target`,
  `flatten_forced_last_bar`, `end_of_data` where they occurred, else blank.

## Fields not available

* Whether the swept level was an equal-highs/equal-lows level (EQH/EQL). The engine tracks it but the
  trade log did not record it. It can be reconstructed from the engine, which would be a rerun.
* Maximum favourable and adverse excursion per trade. Not in the log; reconstructable from the
  minute data without changing any result, on request.
* Intrabar fill timestamps finer than one minute. The data is 1-minute bars.

## Caution for conditional expectancy research

The 2025-2026 run is the data V2 was selected on, and the 2022-2025 run is the only clean test, which
V2 failed (expectancy -0.179 R, 95% CI -0.276 to -0.080). Any condition found by searching these
485 trades is a hypothesis that must be tested on data that was not searched. Searching the 2022-2025
rows converts them from a test into a training set.

# Databento MNQ 1-minute OHLCV

Batch job `GLBX-20261021-5QBR9J5GST`: dataset GLBX.MDP3, schema ohlcv-1m, parent
symbol MNQ.FUT, 2025-10-01 00:00 UTC to 2026-10-21 00:00 UTC, split per symbol,
DBN + zstd. Only the eight outright contracts are kept here; the sixteen
calendar-spread files from the same job are not used and were not committed.
`metadata.json`, `condition.json` and `manifest.json` are the job's own files.

Decode with the `databento` package: `db.DBNStore.from_file(path).to_df()`.
`ts_event` is the UTC open time of the minute bar. Minutes with no trades have no row.

## Validation summary (2026-10-21)

| Check | Result |
|---|---|
| Outright contracts | Z5, H6, M6, U6, Z6 (liquid front months), H7, M7, U7 (back months, thin) |
| Outright 1-minute bars | 625,502; no duplicate stamps, monotonic, minute aligned, high >= low, open/close inside range, all on 0.25 tick, no zero-volume rows |
| Expiry | Last bar of each expiring contract is 09:29 ET on the third Friday (Z5 2025-12-19, H6 2026-03-20, M6 2026-06-18 Thursday because 06-19 is a holiday, U6 2026-09-18) |
| Front-by-volume switches | 2025-12-16 Z5>H6, 2026-03-17 H6>M6, 2026-06-15 M6>U6, 2026-09-15 U6>Z6 (session dates) |
| Session coverage, front contract vs CME_Equity calendar | 373,350 of 374,115 expected minutes (99.80%). No missing regular-hours minute on any session |
| Known gaps | 2025-10-01 session: first 120 minutes absent (job starts 00:00 UTC). 2025-11-28 session: 645 minutes absent, 2025-11-27 21:45 to 2025-11-28 08:29 ET; the TradingView export has the same gap, so it is treated as a closure |
| Calendar library deviations | Day-after-Thanksgiving and Christmas Eve closes observed at 13:15 ET, the library says 13:00 ET; all other early closes and Good Friday (09:15 ET) agree with the library |
| 1H bars built from this data vs TradingView MNQ1! export | 6,228 overlapping hours, 0 hours present in only one source; 4 bars differ, max 0.75 points |
| Liquidity engine events on these 1H bars vs TradingView | 719 new levels and 496 sweeps after warm-up, 0 mismatches |

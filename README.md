# 1H Liquidity Sweep Reversal (MNQ) — V1

Deterministic, backtestable 1H liquidity-sweep reversal strategy for MNQ built on the
existing Buy/Sell-Side Liquidity engine (`engine/bsl_ssl.pine`).

## Layout

| Path | Purpose |
|---|---|
| `engine/bsl_ssl.pine` | The original Pine Script v6 liquidity engine, unchanged. Reference implementation. |
| `tools/tradingview/bsl_ssl_parity_export.pine` | Engine + export plots. Run on TradingView, export chart data, to produce parity evidence. |
| `data/tradingview/` | TradingView exports used as parity evidence. |
| `src/lsr/liquidity_engine.py` | Faithful Python port of the engine's state machine. |
| `scripts/run_parity.py` | Replays an export through the port and reports convergence / mismatches. |
| `tests/` | pytest suite. |

## Backtest

```
pip install -r requirements.txt
python -m pytest -q                      # 40 tests: rules, parity, determinism, no-lookahead, trade audit
python scripts/run_backtest.py --sensitivity   # 1, 2 and 4 ticks slippage -> results/<label>/
```

Results and the limitations report: `results/REPORT.md`.

Modules under `src/lsr/`: `config.py` (approved inputs and calendar overrides), `sessions.py`
(CME sessions, flatten cutoffs), `data.py` (Databento loading, expiries, fixed-Friday roll,
forward adjustment, 1H aggregation), `liquidity_engine.py` (verified engine port), `signals.py`
(same-candle sweep confirmation, EQ zones), `execution.py` (orders, fills, exits, sizing),
`backtest.py` (chronological loop), `report.py` (metrics, split, tables).

## Engine parity

```
python scripts/run_parity.py --all-rules
python -m pytest -q
```

Verified 2026-10-21 on CME_MINI:MNQ1! 1H, default inputs, 7,165 completed bars
(2025-08-05 to 2026-10-21): exact match of every level slot, swept flag, and per-bar
event from bar 141 (end of warm-up) to the end. The undocumented `ta.pivothigh`
tie behaviour was established empirically: an equal neighbour on the left is allowed,
on the right it is not.

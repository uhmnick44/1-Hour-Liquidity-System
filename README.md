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

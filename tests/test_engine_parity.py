"""Parity of the Python liquidity engine port against the original Pine indicator.

Evidence file: data/tradingview/CME_MINI_MNQ1_60_parity_export.csv, produced by
tools/tradingview/bsl_ssl_parity_export.pine on CME_MINI:MNQ1!, 1H, default inputs,
exported 2026-10-21. It carries the indicator's full level state on every bar.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from lsr.liquidity_engine import EngineParams, PivotTieRule  # noqa: E402
from run_parity import DEFAULT_CSV, compare, load_export, replay  # noqa: E402

# Warm-up: the port starts empty while the export carries pre-export state. With
# swing_len=5 and max_levels=8 both sides are fully refreshed once 8 new pivots
# have formed per side; in this export that happens by bar 141.
EXPECTED_CONVERGENCE_BAR = 141


@pytest.fixture(scope="module")
def export():
    return load_export(DEFAULT_CSV)


def test_port_matches_tradingview_after_warmup(export):
    res = compare(export, replay(export, EngineParams()))
    assert res["convergence_bar"] == EXPECTED_CONVERGENCE_BAR
    assert res["event_mismatches_after_convergence"] == {}


def test_default_tie_rule_is_the_verified_one():
    assert EngineParams().tie_rule == PivotTieRule.LEFT_GE_RIGHT_STRICT


@pytest.mark.parametrize("rule", [r for r in PivotTieRule if r != PivotTieRule.LEFT_GE_RIGHT_STRICT])
def test_other_tie_rules_diverge_from_tradingview(export, rule):
    """Documents the evidence: every other tie rule mis-classifies at least one
    of the tie-dependent pivots in the export and so cannot converge by bar 141."""
    res = compare(export, replay(export, EngineParams(tie_rule=rule)))
    assert res["convergence_bar"] != EXPECTED_CONVERGENCE_BAR

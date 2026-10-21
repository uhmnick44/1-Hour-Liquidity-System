"""End-to-end properties on the real dataset: determinism, no lookahead, and
an independent recomputation of every trade from the raw minute bars."""
import numpy as np
import pandas as pd
import pytest

from lsr.backtest import run_backtest
from lsr.config import BacktestConfig
from lsr.data import build_market_data


@pytest.fixture(scope="module")
def md():
    pytest.importorskip("databento")
    cfg = BacktestConfig()
    return build_market_data(cfg.data, cfg.strategy)


@pytest.fixture(scope="module")
def result(md):
    return run_backtest(md, BacktestConfig())


def test_determinism(md, result):
    again = run_backtest(md, BacktestConfig())
    pd.testing.assert_frame_equal(result.trades, again.trades)
    pd.testing.assert_frame_equal(result.events, again.events)
    pd.testing.assert_frame_equal(result.signals, again.signals)


def test_no_lookahead_truncation(md, result):
    """Everything decided before a cut must be identical when the data after the cut is removed."""
    h1 = md.h1
    for frac in (0.3, 0.55, 0.8):
        cut = h1.close_ts.iloc[int(len(h1) * frac)]
        part = run_backtest(md, BacktestConfig(), end_ts=cut)
        full_sig = result.signals[result.signals.close_ts <= cut].reset_index(drop=True)
        pd.testing.assert_frame_equal(part.signals.reset_index(drop=True), full_sig)
        # trades fully closed before the cut are identical; the final partial trade may differ only by an end_of_data exit
        full_tr = result.trades[result.trades.exit_ts <= cut].reset_index(drop=True)
        part_tr = part.trades[part.trades.exit_reason != "end_of_data"].reset_index(drop=True)
        part_tr = part_tr[part_tr.exit_ts <= cut].reset_index(drop=True)
        pd.testing.assert_frame_equal(part_tr, full_tr)


def test_every_trade_recomputes_from_raw_minutes(md, result):
    tr = result.trades; m1 = md.m1; cfg = BacktestConfig(); slip = cfg.costs.slippage_ticks * cfg.instrument.tick_size
    assert len(tr) > 0
    for t in tr.itertuples():
        d = -1 if t.direction == "short" else 1
        hb = md.h1.loc[t.signal_bar_ts]
        assert hb.high == t.sweep_high and hb.low == t.sweep_low and hb.close == t.signal_close
        assert t.eq == (hb.high + hb.low) / 2
        # the level was swept strictly and closed back through on that candle
        assert (hb.high > t.level_price and hb.close < t.level_price) if d < 0 else (hb.low < t.level_price and hb.close > t.level_price)
        after = m1[m1.index >= t.signal_close_ts]
        if t.entry_type == "market":
            b = after.iloc[0]
            assert t.entry_ts == after.index[0] and t.entry_price == b.open + d * slip
            assert d * (b.open - t.eq) <= 0
        else:
            win = after[after.index <= t.entry_ts]
            prior = win.iloc[:-1]; fb = win.iloc[-1]
            adv = prior.high if d < 0 else prior.low
            assert not (d * (adv - (t.sweep_high if d < 0 else t.sweep_low)) < 0).any(), "invalidation missed before fill"
            if t.gap_fill:
                assert t.entry_price == fb.open and d * (fb.open - t.limit_price) < 0
            else:
                fav = fb.high if d < 0 else fb.low
                assert t.entry_price == t.limit_price and d * (fav - t.limit_price) <= -0.25
                assert not (d * ((prior.high if d < 0 else prior.low) - t.limit_price) <= -0.25).any(), "earlier fill missed"
        ext = t.sweep_high if d < 0 else t.sweep_low
        dist = 2 * d * (t.entry_price - ext)
        assert np.isclose(t.stop_distance, dist) and np.isclose(t.stop, t.entry_price - d * dist) and np.isclose(t.target, t.entry_price + d * dist)
        assert dist >= cfg.risk.min_stop_points or "stop_below_min_after_gap_fill" in str(t.trade_flags)
        rpc = dist * 2 + cfg.costs.fees_round_trip + cfg.costs.slippage_ticks * 0.5
        if t.entry_type == "market" or not t.gap_fill:
            assert t.contracts == min(10, int(np.floor(t.equity_at_entry * 0.01 / rpc + 1e-12)))
        # exit: no earlier minute could have exited
        held = m1[(m1.index > t.entry_ts) & (m1.index < t.exit_ts)]
        adv_h = held.high if d < 0 else held.low; fav_h = held.low if d < 0 else held.high
        assert not (d * (adv_h - t.stop) <= 0).any(), "stop missed"
        assert not (d * (fav_h - t.target) >= 0.25).any(), "target missed"
        assert np.isclose(t.net_pnl_usd, d * (t.exit_price - t.entry_price) * 2 * t.contracts - 1.88 * t.contracts)

"""
Tests for the backtesting engine, portfolio, and metrics.
"""
import pytest
import pandas as pd
import numpy as np

from src.backtesting.engine import run_backtest
from src.backtesting.portfolio import Portfolio, Trade
from src.backtesting.metrics import calculate_metrics
from src.strategies.moving_average import MovingAverageCrossover


class TestPortfolio:
    """Tests for the Portfolio class."""

    def test_initial_state(self):
        p = Portfolio(initial_capital=100_000)
        assert p.cash == 100_000
        assert not p.is_in_position
        assert len(p.trades) == 0

    def test_open_position(self):
        p = Portfolio(initial_capital=100_000, commission_pct=0.0, slippage_pct=0.0)
        p.open_position(pd.Timestamp("2023-01-02"), 100.0)
        assert p.is_in_position
        assert p.shares == 1000.0
        assert p.cash == 0.0

    def test_close_position(self):
        p = Portfolio(initial_capital=100_000, commission_pct=0.0, slippage_pct=0.0)
        p.open_position(pd.Timestamp("2023-01-02"), 100.0)
        p.close_position(pd.Timestamp("2023-01-03"), 110.0, 1)
        assert not p.is_in_position
        assert p.cash == 110_000.0
        assert len(p.trades) == 1
        assert p.trades[0].pnl == 10_000.0

    def test_commission_deduction(self):
        p = Portfolio(initial_capital=100_000, commission_pct=1.0, slippage_pct=0.0)
        p.open_position(pd.Timestamp("2023-01-02"), 100.0)
        assert p.shares == pytest.approx(990.0, rel=1e-4)

    def test_equity_recording(self):
        p = Portfolio(initial_capital=100_000, commission_pct=0.0, slippage_pct=0.0)
        p.record_equity(pd.Timestamp("2023-01-02"), 100.0)
        eq_df = p.get_equity_series()
        assert len(eq_df) == 1
        assert eq_df["equity"].iloc[0] == 100_000.0

    def test_no_double_entry(self):
        p = Portfolio(initial_capital=100_000, commission_pct=0.0, slippage_pct=0.0)
        p.open_position(pd.Timestamp("2023-01-02"), 100.0)
        p.open_position(pd.Timestamp("2023-01-03"), 105.0)  # Should be ignored
        assert p.entry_price == 100.0


class TestBacktestEngine:
    """Tests for the backtest execution engine."""

    def test_backtest_with_signals(self, sample_ohlc_df):
        s = MovingAverageCrossover(fast_period=5, slow_period=20)
        df = s.generate_signals(sample_ohlc_df)
        portfolio = run_backtest(df, initial_capital=100_000)
        eq = portfolio.get_equity_series()
        assert len(eq) == len(df)

    def test_no_signal_means_no_trade(self, sample_ohlc_df):
        df = sample_ohlc_df.copy()
        df["signal"] = 0  # No signals
        portfolio = run_backtest(df, initial_capital=100_000)
        assert len(portfolio.trades) == 0
        eq = portfolio.get_equity_series()
        assert eq["equity"].iloc[-1] == 100_000.0

    def test_execution_on_next_bar(self, tiny_ohlc_df):
        """Signal on bar t executes on bar t+1's open."""
        df = tiny_ohlc_df.copy()
        df["signal"] = [1, 0, -1, 0, 0]  # Enter on bar 0, exit on bar 2
        portfolio = run_backtest(df, initial_capital=100_000, commission_pct=0, slippage_pct=0)
        if len(portfolio.trades) > 0:
            trade = portfolio.trades[0]
            assert trade.entry_price == 101.0
            assert trade.exit_price == 101.5

    def test_needs_signal_column(self, sample_ohlc_df):
        with pytest.raises(ValueError, match="signal"):
            run_backtest(sample_ohlc_df)

    def test_needs_minimum_bars(self):
        df = pd.DataFrame({
            "date": [pd.Timestamp("2023-01-02")],
            "open": [100], "high": [101], "low": [99], "close": [100.5],
            "signal": [0],
        })
        with pytest.raises(ValueError, match="at least 2"):
            run_backtest(df)

    def test_force_close_at_end(self, sample_ohlc_df):
        """Open position should be closed at the end of data."""
        df = sample_ohlc_df.copy()
        df["signal"] = 0
        df.loc[20, "signal"] = 1  # Enter on bar 20, never exit
        portfolio = run_backtest(df, initial_capital=100_000)
        assert len(portfolio.trades) == 1


class TestMetrics:
    """Tests for financial metrics calculation."""

    def test_zero_trade_metrics(self, sample_ohlc_df):
        df = sample_ohlc_df.copy()
        df["signal"] = 0
        portfolio = run_backtest(df, initial_capital=100_000)
        metrics = calculate_metrics(portfolio)
        assert metrics["num_trades"] == 0
        assert metrics["total_return"] == 0.0
        assert metrics["win_rate"] == 0.0

    def test_metrics_with_trades(self, sample_ohlc_df):
        s = MovingAverageCrossover(fast_period=5, slow_period=20)
        df = s.generate_signals(sample_ohlc_df)
        portfolio = run_backtest(df, initial_capital=100_000)
        metrics = calculate_metrics(portfolio)
        assert "total_return" in metrics
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics
        assert "win_rate" in metrics
        assert "num_trades" in metrics
        assert "profit_factor" in metrics
        assert isinstance(metrics["num_trades"], int)

    def test_max_drawdown_is_non_positive(self, sample_ohlc_df):
        s = MovingAverageCrossover(fast_period=5, slow_period=20)
        df = s.generate_signals(sample_ohlc_df)
        portfolio = run_backtest(df, initial_capital=100_000)
        metrics = calculate_metrics(portfolio)
        assert metrics["max_drawdown"] <= 0.0

    def test_total_return_consistent_with_equity(self, sample_ohlc_df):
        s = MovingAverageCrossover(fast_period=5, slow_period=20)
        df = s.generate_signals(sample_ohlc_df)
        portfolio = run_backtest(df, initial_capital=100_000)
        metrics = calculate_metrics(portfolio)
        eq = portfolio.get_equity_series()
        expected = (eq["equity"].iloc[-1] / 100_000 - 1) * 100
        assert abs(metrics["total_return"] - expected) < 0.01

    def test_sharpe_zero_volatility(self):
        """Sharpe should be 0 when returns have no volatility."""
        p = Portfolio(initial_capital=100_000)
        for i in range(10):
            p.record_equity(pd.Timestamp(f"2023-01-{i+2:02d}"), 100.0)
        metrics = calculate_metrics(p)
        assert metrics["sharpe_ratio"] == 0.0

    def test_known_total_return(self):
        """Test with a known scenario: buy at 100, sell at 110, no costs."""
        df = pd.DataFrame({
            "date": pd.bdate_range("2023-01-02", periods=5),
            "open": [100, 100, 105, 110, 110],
            "high": [101, 106, 106, 111, 111],
            "low": [99, 99, 104, 109, 109],
            "close": [100, 105, 105, 110, 110],
            "signal": [1, 0, 0, -1, 0],
        })
        portfolio = run_backtest(df, initial_capital=10_000, commission_pct=0, slippage_pct=0)
        metrics = calculate_metrics(portfolio)
        assert abs(metrics["total_return"] - 10.0) < 0.1

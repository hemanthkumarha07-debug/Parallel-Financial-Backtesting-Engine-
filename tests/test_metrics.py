"""
Tests for financial performance metrics edge cases.
"""
import pytest
import pandas as pd
import numpy as np

from src.backtesting.portfolio import Portfolio
from src.backtesting.metrics import calculate_metrics


class TestMetricsEdgeCases:
    """Test edge cases in metric calculations."""

    def test_empty_portfolio(self):
        p = Portfolio(initial_capital=100_000)
        metrics = calculate_metrics(p)
        assert metrics["total_return"] == 0.0
        assert metrics["num_trades"] == 0
        assert metrics["sharpe_ratio"] == 0.0
        assert metrics["max_drawdown"] == 0.0

    def test_single_equity_point(self):
        p = Portfolio(initial_capital=100_000)
        p.record_equity(pd.Timestamp("2023-01-02"), 100.0)
        metrics = calculate_metrics(p)
        assert metrics["total_return"] == 0.0
        assert metrics["sharpe_ratio"] == 0.0

    def test_all_winning_trades(self):
        p = Portfolio(initial_capital=100_000, commission_pct=0, slippage_pct=0)
        p.open_position(pd.Timestamp("2023-01-02"), 100.0)
        p.close_position(pd.Timestamp("2023-01-03"), 110.0, 1)
        p.open_position(pd.Timestamp("2023-01-04"), 110.0)
        p.close_position(pd.Timestamp("2023-01-05"), 120.0, 1)
        for i in range(5):
            p.record_equity(pd.Timestamp(f"2023-01-{i+2:02d}"), 100 + i * 5)
        metrics = calculate_metrics(p)
        assert metrics["win_rate"] == 100.0
        assert metrics["profit_factor"] == float("inf")

    def test_all_losing_trades(self):
        p = Portfolio(initial_capital=100_000, commission_pct=0, slippage_pct=0)
        p.open_position(pd.Timestamp("2023-01-02"), 100.0)
        p.close_position(pd.Timestamp("2023-01-03"), 90.0, 1)
        for i in range(3):
            p.record_equity(pd.Timestamp(f"2023-01-{i+2:02d}"), 100_000 - i * 5000)
        metrics = calculate_metrics(p)
        assert metrics["win_rate"] == 0.0
        assert metrics["profit_factor"] == 0.0

    def test_risk_free_rate_effect(self):
        p = Portfolio(initial_capital=100_000, commission_pct=0, slippage_pct=0)
        for i in range(30):
            p.equity_curve.append((pd.Timestamp("2023-01-02") + pd.Timedelta(days=i), 100_000 + i * 100))
        m1 = calculate_metrics(p, risk_free_rate=0.0)
        m2 = calculate_metrics(p, risk_free_rate=0.05)
        assert m2["sharpe_ratio"] <= m1["sharpe_ratio"]

    def test_annualized_return_calculation(self):
        p = Portfolio(initial_capital=100_000, commission_pct=0, slippage_pct=0)
        for i in range(252):
            equity = 100_000 * (1 + 0.10 * i / 251)
            p.equity_curve.append((pd.Timestamp("2023-01-02") + pd.Timedelta(days=i), equity))
        metrics = calculate_metrics(p)
        assert abs(metrics["annualized_return"] - 10.0) < 1.0

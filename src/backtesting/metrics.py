"""
Financial performance and risk metrics.

All metric functions operate on either a Portfolio object or its
equity/trade DataFrames.
"""
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from src.backtesting.portfolio import Portfolio


def calculate_metrics(
    portfolio: Portfolio,
    risk_free_rate: float = 0.0,
    trading_days_per_year: int = 252,
) -> Dict[str, Any]:
    """
    Calculate a comprehensive set of financial metrics.

    Parameters
    ----------
    portfolio : Portfolio
        Completed portfolio with equity curve and trades.
    risk_free_rate : float
        Annualized risk-free rate (e.g. 0.04 for 4 %).
    trading_days_per_year : int
        Trading days per year for annualization.

    Returns
    -------
    dict
        Metric name → value.  Values may be float, int, or str.

    Metric definitions
    ------------------
    total_return        : (final_equity / initial_capital − 1) × 100
    annualized_return   : ((1 + total_return/100)^(252/n_bars) − 1) × 100
    max_drawdown        : largest peak-to-trough decline in equity (%)
    sharpe_ratio        : (mean_daily_excess_return / std_daily_return) × √252
    win_rate            : winning_trades / total_trades × 100
    num_trades          : total completed trades
    avg_trade_return    : mean return_pct across trades
    profit_factor       : gross_profit / gross_loss (or ∞ if no losses)
    avg_holding_period  : mean holding_bars across trades
    total_costs         : total commissions + slippage
    """
    equity_df = portfolio.get_equity_series()
    trades_df = portfolio.get_trades_df()

    metrics: Dict[str, Any] = {}

    # ── Total return ───────────────────────────────────────────────────
    if equity_df.empty or len(equity_df) < 1:
        metrics["total_return"] = 0.0
    else:
        final_eq = equity_df["equity"].iloc[-1]
        metrics["total_return"] = round(
            (final_eq / portfolio.initial_capital - 1.0) * 100.0, 4
        )

    # ── Annualized return ──────────────────────────────────────────────
    n_bars = len(equity_df)
    if n_bars > 1 and metrics["total_return"] != 0.0:
        total_r = metrics["total_return"] / 100.0
        years = n_bars / trading_days_per_year
        if years > 0 and (1 + total_r) > 0:
            ann = ((1 + total_r) ** (1.0 / years) - 1.0) * 100.0
            metrics["annualized_return"] = round(ann, 4)
        else:
            metrics["annualized_return"] = 0.0
    else:
        metrics["annualized_return"] = 0.0

    # ── Maximum drawdown ───────────────────────────────────────────────
    if equity_df.empty or len(equity_df) < 2:
        metrics["max_drawdown"] = 0.0
    else:
        eq = equity_df["equity"].values
        peak = np.maximum.accumulate(eq)
        drawdown = (eq - peak) / np.where(peak > 0, peak, 1.0) * 100.0
        metrics["max_drawdown"] = round(float(np.min(drawdown)), 4)

    # ── Sharpe ratio ───────────────────────────────────────────────────
    if equity_df.empty or len(equity_df) < 3:
        metrics["sharpe_ratio"] = 0.0
    else:
        eq = equity_df["equity"].values.astype(np.float64)
        daily_returns = np.diff(eq) / eq[:-1]
        daily_rf = (1 + risk_free_rate) ** (1.0 / trading_days_per_year) - 1.0
        excess = daily_returns - daily_rf
        std = np.std(excess, ddof=1)
        if std > 1e-12:
            metrics["sharpe_ratio"] = round(
                float(np.mean(excess) / std * np.sqrt(trading_days_per_year)), 4
            )
        else:
            metrics["sharpe_ratio"] = 0.0

    # ── Trade-level metrics ────────────────────────────────────────────
    num_trades = len(trades_df)
    metrics["num_trades"] = num_trades

    if num_trades == 0:
        metrics["win_rate"] = 0.0
        metrics["avg_trade_return"] = 0.0
        metrics["profit_factor"] = 0.0
        metrics["avg_holding_period"] = 0.0
    else:
        wins = trades_df[trades_df["pnl"] > 0]
        losses = trades_df[trades_df["pnl"] < 0]

        metrics["win_rate"] = round(len(wins) / num_trades * 100.0, 2)
        metrics["avg_trade_return"] = round(trades_df["return_pct"].mean(), 4)

        gross_profit = wins["pnl"].sum() if len(wins) > 0 else 0.0
        gross_loss = abs(losses["pnl"].sum()) if len(losses) > 0 else 0.0
        if gross_loss > 1e-12:
            metrics["profit_factor"] = round(gross_profit / gross_loss, 4)
        else:
            metrics["profit_factor"] = float("inf") if gross_profit > 0 else 0.0

        metrics["avg_holding_period"] = round(trades_df["holding_bars"].mean(), 2)

    # ── Transaction costs ──────────────────────────────────────────────
    metrics["total_costs"] = round(
        portfolio.total_commissions + portfolio.total_slippage, 2
    )

    # ── Final equity ───────────────────────────────────────────────────
    if not equity_df.empty:
        metrics["final_equity"] = round(equity_df["equity"].iloc[-1], 2)
    else:
        metrics["final_equity"] = portfolio.initial_capital

    return metrics

"""
Backtesting execution engine.

Walks through a signal-annotated OHLC DataFrame bar-by-bar, executing
trades on the NEXT bar's open price to avoid look-ahead bias.

Execution model
---------------
- Signal on bar t (using close[t]) → execute on bar t+1 at open[t+1].
- Commission and slippage are applied at execution time.
- Long-only mode (no short selling in the base implementation).
"""
from typing import Dict, Any

import pandas as pd
import numpy as np

from src.backtesting.portfolio import Portfolio
from src.utils.logging_config import logger


def run_backtest(
    df: pd.DataFrame,
    initial_capital: float = 100_000.0,
    commission_pct: float = 0.1,
    slippage_pct: float = 0.05,
    position_size_pct: float = 100.0,
) -> Portfolio:
    """
    Execute a backtest on a signal-annotated DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns: date, open, high, low, close, signal.
        signal: +1 = enter long, -1 = exit, 0 = hold.
    initial_capital : float
        Starting portfolio value.
    commission_pct : float
        Commission per trade (% of trade value).
    slippage_pct : float
        Slippage per trade (% of trade value).
    position_size_pct : float
        Percentage of available capital to invest per trade.

    Returns
    -------
    Portfolio
        Portfolio object with equity curve, trades, and cost tracking.
    """
    if "signal" not in df.columns:
        raise ValueError("DataFrame must contain a 'signal' column.")
    if len(df) < 2:
        raise ValueError("Need at least 2 bars for backtesting.")

    portfolio = Portfolio(
        initial_capital=initial_capital,
        commission_pct=commission_pct,
        slippage_pct=slippage_pct,
        position_size_pct=position_size_pct,
    )

    # Track entry bar index for holding-period calculation
    entry_bar_idx = None

    for i in range(len(df)):
        date = df["date"].iloc[i]
        open_price = df["open"].iloc[i]
        close_price = df["close"].iloc[i]

        # ── Execute pending signals from the PREVIOUS bar ──────────────
        if i > 0:
            prev_signal = df["signal"].iloc[i - 1]

            if prev_signal == 1 and not portfolio.is_in_position:
                # Enter long at this bar's open
                portfolio.open_position(date, open_price)
                entry_bar_idx = i

            elif prev_signal == -1 and portfolio.is_in_position:
                # Exit at this bar's open
                holding = i - entry_bar_idx if entry_bar_idx is not None else 0
                portfolio.close_position(date, open_price, holding)
                entry_bar_idx = None

        # ── Record equity (mark-to-market using close) ─────────────────
        portfolio.record_equity(date, close_price)

    # ── Close any open position at the last bar's close ────────────────
    if portfolio.is_in_position and len(df) > 0:
        last_date = df["date"].iloc[-1]
        last_close = df["close"].iloc[-1]
        holding = (len(df) - 1) - entry_bar_idx if entry_bar_idx is not None else 0
        portfolio.close_position(last_date, last_close, holding)
        # Re-record final equity after closing
        if portfolio.equity_curve:
            portfolio.equity_curve[-1] = (last_date, portfolio.cash)

    return portfolio

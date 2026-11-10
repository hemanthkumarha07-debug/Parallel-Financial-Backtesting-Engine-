"""
Portfolio tracking — cash, positions, equity, and trade records.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


@dataclass
class Trade:
    """Record of a completed (round-trip) trade."""
    entry_date: pd.Timestamp
    entry_price: float
    exit_date: pd.Timestamp
    exit_price: float
    shares: float
    pnl: float
    return_pct: float
    commission: float
    slippage_cost: float
    holding_bars: int


@dataclass
class Portfolio:
    """
    Tracks the portfolio state through a backtest.

    Attributes
    ----------
    initial_capital : float
        Starting cash.
    cash : float
        Current cash balance.
    shares : float
        Current position size (number of shares held).
    entry_price : float
        Average entry price of the current position (0 if flat).
    entry_date : pd.Timestamp or None
        Date of the current position's entry.
    equity_curve : list
        (date, equity_value) tuples for each bar.
    trades : list
        Completed Trade objects.
    commission_pct : float
        Commission per trade as a percentage of trade value (e.g. 0.1 = 0.1 %).
    slippage_pct : float
        Slippage per trade as a percentage of trade value (e.g. 0.05 = 0.05 %).
    position_size_pct : float
        Fraction of available capital to deploy (100 = 100 %).
    """

    initial_capital: float = 100_000.0
    commission_pct: float = 0.1
    slippage_pct: float = 0.05
    position_size_pct: float = 100.0

    cash: float = field(init=False)
    shares: float = field(init=False, default=0.0)
    entry_price: float = field(init=False, default=0.0)
    entry_date: Optional[pd.Timestamp] = field(init=False, default=None)
    equity_curve: List[tuple] = field(init=False, default_factory=list)
    trades: List[Trade] = field(init=False, default_factory=list)
    total_commissions: float = field(init=False, default=0.0)
    total_slippage: float = field(init=False, default=0.0)

    def __post_init__(self):
        self.cash = self.initial_capital

    @property
    def is_in_position(self) -> bool:
        return self.shares > 0

    def _apply_costs(self, trade_value: float) -> tuple:
        """Calculate commission and slippage for a trade."""
        commission = trade_value * (self.commission_pct / 100.0)
        slippage = trade_value * (self.slippage_pct / 100.0)
        return commission, slippage

    def open_position(self, date: pd.Timestamp, price: float) -> None:
        """
        Open a long position using next bar's open price.

        Parameters
        ----------
        date : pd.Timestamp
            Execution date (the bar AFTER the signal bar).
        price : float
            Execution price (open of the execution bar).
        """
        if self.is_in_position:
            return  # Already in position

        available = self.cash * (self.position_size_pct / 100.0)
        commission, slippage = self._apply_costs(available)
        investable = available - commission - slippage

        if investable <= 0 or price <= 0:
            return

        self.shares = investable / price
        self.entry_price = price
        self.entry_date = date
        self.cash -= available
        self.total_commissions += commission
        self.total_slippage += slippage

    def close_position(self, date: pd.Timestamp, price: float, bar_idx: int) -> None:
        """
        Close the current long position.

        Parameters
        ----------
        date : pd.Timestamp
            Execution date.
        price : float
            Execution price (open of the execution bar).
        bar_idx : int
            Index of the execution bar (for holding-period calculation).
        """
        if not self.is_in_position:
            return

        gross_proceeds = self.shares * price
        commission, slippage = self._apply_costs(gross_proceeds)
        net_proceeds = gross_proceeds - commission - slippage

        pnl = net_proceeds - (self.shares * self.entry_price)
        return_pct = (price / self.entry_price - 1.0) * 100.0 if self.entry_price > 0 else 0.0

        # Holding bars: difference from entry to exit
        holding = bar_idx  # Caller passes the count

        trade = Trade(
            entry_date=self.entry_date,
            entry_price=self.entry_price,
            exit_date=date,
            exit_price=price,
            shares=self.shares,
            pnl=pnl,
            return_pct=return_pct,
            commission=commission,
            slippage_cost=slippage,
            holding_bars=holding,
        )
        self.trades.append(trade)

        self.cash += net_proceeds
        self.total_commissions += commission
        self.total_slippage += slippage
        self.shares = 0.0
        self.entry_price = 0.0
        self.entry_date = None

    def record_equity(self, date: pd.Timestamp, current_price: float) -> None:
        """Record mark-to-market equity at this bar."""
        unrealized = self.shares * current_price if self.is_in_position else 0.0
        equity = self.cash + unrealized
        self.equity_curve.append((date, equity))

    def get_equity_series(self) -> pd.DataFrame:
        """Return equity curve as a DataFrame."""
        if not self.equity_curve:
            return pd.DataFrame(columns=["date", "equity"])
        df = pd.DataFrame(self.equity_curve, columns=["date", "equity"])
        return df

    def get_trades_df(self) -> pd.DataFrame:
        """Return trade history as a DataFrame."""
        if not self.trades:
            return pd.DataFrame(columns=[
                "entry_date", "entry_price", "exit_date", "exit_price",
                "shares", "pnl", "return_pct", "commission", "slippage_cost",
                "holding_bars",
            ])
        records = []
        for t in self.trades:
            records.append({
                "entry_date": t.entry_date,
                "entry_price": round(t.entry_price, 4),
                "exit_date": t.exit_date,
                "exit_price": round(t.exit_price, 4),
                "shares": round(t.shares, 4),
                "pnl": round(t.pnl, 2),
                "return_pct": round(t.return_pct, 2),
                "commission": round(t.commission, 2),
                "slippage_cost": round(t.slippage_cost, 2),
                "holding_bars": t.holding_bars,
            })
        return pd.DataFrame(records)

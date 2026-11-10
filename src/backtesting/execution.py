"""
Execution helpers — strategy instantiation and single-task runner.

This module provides the top-level function `run_single_backtest` which
is called by both the sequential and parallel runners.  Because
multiprocessing on Windows uses 'spawn', all worker functions must be
importable at module scope.
"""
from typing import Any, Dict, Optional, Tuple
import time
import traceback

import pandas as pd

from src.strategies.base import BaseStrategy
from src.strategies.moving_average import MovingAverageCrossover
from src.strategies.rsi_mean_reversion import RSIMeanReversion
from src.strategies.donchian_breakout import DonchianBreakout
from src.backtesting.engine import run_backtest
from src.backtesting.metrics import calculate_metrics
from src.utils.logging_config import logger


# ── Strategy registry ──────────────────────────────────────────────────────
STRATEGY_REGISTRY = {
    "MovingAverageCrossover": MovingAverageCrossover,
    "RSIMeanReversion": RSIMeanReversion,
    "DonchianBreakout": DonchianBreakout,
}


def create_strategy(strategy_name: str, params: Dict[str, Any]) -> BaseStrategy:
    """Instantiate a strategy from the registry."""
    if strategy_name not in STRATEGY_REGISTRY:
        raise ValueError(
            f"Unknown strategy '{strategy_name}'. "
            f"Available: {list(STRATEGY_REGISTRY.keys())}"
        )
    return STRATEGY_REGISTRY[strategy_name](**params)


# ── Task definition ────────────────────────────────────────────────────────

def make_task(
    task_id: str,
    strategy_name: str,
    params: Dict[str, Any],
    backtest_settings: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Create a deterministic task descriptor.

    Parameters
    ----------
    task_id : str
        Unique identifier for this task.
    strategy_name : str
        Key in STRATEGY_REGISTRY.
    params : dict
        Strategy parameter dict.
    backtest_settings : dict
        Keys: initial_capital, commission_pct, slippage_pct, position_size_pct,
              risk_free_rate, trading_days_per_year.

    Returns
    -------
    dict
        Serializable task descriptor.
    """
    return {
        "task_id": task_id,
        "strategy_name": strategy_name,
        "params": params,
        "backtest_settings": backtest_settings,
    }


# ── Worker function (module-scope for multiprocessing) ─────────────────────

def run_single_backtest(
    task: Dict[str, Any],
    df_records: list,
    df_columns: list,
) -> Dict[str, Any]:
    """
    Execute one backtest task.  This function is called by both the
    sequential runner and the parallel worker processes.

    Parameters
    ----------
    task : dict
        Task descriptor from make_task().
    df_records : list
        DataFrame rows as list of dicts (for safe serialization).
    df_columns : list
        Column names.

    Returns
    -------
    dict
        Result containing metrics, equity curve, trades, timing, and status.
    """
    t0 = time.perf_counter()
    result = {
        "task_id": task["task_id"],
        "strategy_name": task["strategy_name"],
        "params": task["params"],
        "status": "error",
        "metrics": {},
        "equity_curve": [],
        "trades": [],
        "execution_time": 0.0,
        "error": None,
    }

    try:
        # Reconstruct DataFrame from records
        df = pd.DataFrame(df_records, columns=df_columns)
        df["date"] = pd.to_datetime(df["date"])
        for col in ["open", "high", "low", "close"]:
            df[col] = df[col].astype(float)

        # Create strategy and generate signals
        strategy = create_strategy(task["strategy_name"], task["params"])
        df_signals = strategy.generate_signals(df)

        # Run backtest
        settings = task["backtest_settings"]
        portfolio = run_backtest(
            df_signals,
            initial_capital=settings.get("initial_capital", 100_000.0),
            commission_pct=settings.get("commission_pct", 0.1),
            slippage_pct=settings.get("slippage_pct", 0.05),
            position_size_pct=settings.get("position_size_pct", 100.0),
        )

        # Calculate metrics
        metrics = calculate_metrics(
            portfolio,
            risk_free_rate=settings.get("risk_free_rate", 0.0),
            trading_days_per_year=settings.get("trading_days_per_year", 252),
        )

        # Serialize equity curve & trades
        eq_df = portfolio.get_equity_series()
        trades_df = portfolio.get_trades_df()

        result["metrics"] = metrics
        result["equity_curve"] = eq_df.to_dict("records") if not eq_df.empty else []
        result["trades"] = trades_df.to_dict("records") if not trades_df.empty else []
        result["status"] = "success"

    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["status"] = "error"

    result["execution_time"] = time.perf_counter() - t0
    return result

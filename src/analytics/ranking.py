"""
Strategy ranking — compare and rank backtest results by user-selected criteria.
"""
from typing import Any, Dict, List, Optional

import pandas as pd


def rank_results(
    results: List[Dict[str, Any]],
    sort_by: str = "sharpe_ratio",
    ascending: bool = False,
    min_trades: int = 1,
) -> pd.DataFrame:
    """
    Build a ranked comparison table from backtest results.

    Parameters
    ----------
    results : list of dict
        Result dicts from run_single_backtest.
    sort_by : str
        Metric to sort by.
    ascending : bool
        Sort direction (False = highest first for return/sharpe,
        True = lowest first for drawdown).
    min_trades : int
        Minimum trades required to be ranked.

    Returns
    -------
    pd.DataFrame
        Ranked table with one row per configuration.
    """
    rows = []
    for r in results:
        if r["status"] != "success":
            continue
        m = r["metrics"]
        if m.get("num_trades", 0) < min_trades:
            continue
        rows.append({
            "strategy": r["strategy_name"],
            "params": str(r["params"]),
            "total_return": m.get("total_return", 0.0),
            "max_drawdown": m.get("max_drawdown", 0.0),
            "sharpe_ratio": m.get("sharpe_ratio", 0.0),
            "win_rate": m.get("win_rate", 0.0),
            "num_trades": m.get("num_trades", 0),
            "profit_factor": m.get("profit_factor", 0.0),
            "avg_holding_period": m.get("avg_holding_period", 0.0),
            "total_costs": m.get("total_costs", 0.0),
            "final_equity": m.get("final_equity", 0.0),
            "execution_time": round(r.get("execution_time", 0.0), 4),
        })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    if sort_by in df.columns:
        df = df.sort_values(sort_by, ascending=ascending).reset_index(drop=True)

    df.index = df.index + 1
    df.index.name = "rank"
    return df


def weighted_score(
    row: pd.Series,
    weights: Dict[str, float] = None,
) -> float:
    """
    Calculate a user-defined weighted score for a strategy.

    Default weights emphasize risk-adjusted return:
        sharpe_ratio: 0.4, total_return: 0.3, max_drawdown: 0.3

    Note: max_drawdown is negative, so we negate it for the score.
    """
    if weights is None:
        weights = {
            "sharpe_ratio": 0.4,
            "total_return": 0.3,
            "max_drawdown": 0.3,  # We'll negate it
        }
    score = 0.0
    for metric, weight in weights.items():
        val = row.get(metric, 0.0)
        if metric == "max_drawdown":
            val = -val  # Smaller drawdown is better
        score += val * weight
    return round(score, 4)

"""
Report generation — create downloadable CSV and summary reports.
"""
import io
import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from src.utils.logging_config import logger


def export_backtest_results_csv(
    results: List[Dict[str, Any]],
) -> str:
    """Export all backtest results as a CSV string."""
    rows = []
    for r in results:
        if r["status"] != "success":
            continue
        m = r["metrics"]
        rows.append({
            "task_id": r["task_id"],
            "strategy": r["strategy_name"],
            "params": str(r["params"]),
            "total_return_pct": m.get("total_return", 0.0),
            "annualized_return_pct": m.get("annualized_return", 0.0),
            "max_drawdown_pct": m.get("max_drawdown", 0.0),
            "sharpe_ratio": m.get("sharpe_ratio", 0.0),
            "win_rate_pct": m.get("win_rate", 0.0),
            "num_trades": m.get("num_trades", 0),
            "avg_trade_return_pct": m.get("avg_trade_return", 0.0),
            "profit_factor": m.get("profit_factor", 0.0),
            "avg_holding_period": m.get("avg_holding_period", 0.0),
            "total_costs": m.get("total_costs", 0.0),
            "final_equity": m.get("final_equity", 0.0),
            "execution_time_s": round(r.get("execution_time", 0.0), 6),
        })
    if not rows:
        return ""
    return pd.DataFrame(rows).to_csv(index=False)


def export_trades_csv(results: List[Dict[str, Any]]) -> str:
    """Export all trades from all results as a CSV string."""
    all_trades = []
    for r in results:
        if r["status"] != "success":
            continue
        for t in r.get("trades", []):
            trade = dict(t)
            trade["strategy"] = r["strategy_name"]
            trade["params"] = str(r["params"])
            all_trades.append(trade)
    if not all_trades:
        return ""
    return pd.DataFrame(all_trades).to_csv(index=False)


def export_benchmark_csv(benchmark: Dict[str, Any]) -> str:
    """Export benchmark results as a CSV string."""
    rows = []
    # Sequential
    seq = benchmark.get("sequential", {})
    rows.append({
        "mode": "sequential",
        "num_workers": 1,
        "median_time_s": seq.get("median_time", 0.0),
        "speedup": 1.0,
        "efficiency_pct": 100.0,
        "completed": seq.get("completed", 0),
        "failed": seq.get("failed", 0),
    })
    # Parallel
    for nw, data in sorted(benchmark.get("parallel", {}).items()):
        rows.append({
            "mode": "parallel",
            "num_workers": nw,
            "median_time_s": data.get("median_time", 0.0),
            "speedup": data.get("speedup", 0.0),
            "efficiency_pct": data.get("efficiency_pct", 0.0),
            "completed": data.get("completed", 0),
            "failed": data.get("failed", 0),
        })
    return pd.DataFrame(rows).to_csv(index=False)


def generate_experiment_report(
    benchmark: Dict[str, Any],
    ranked_df: pd.DataFrame,
    dataset_info: Dict[str, Any] = None,
    backtest_settings: Dict[str, Any] = None,
) -> str:
    """
    Generate a concise text-based experiment report.

    Returns
    -------
    str
        Markdown-formatted report text.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Parallel Financial Strategy Backtesting Engine — Experiment Report",
        f"\nGenerated: {now}\n",
        "---",
        "\n## 1. Dataset Information\n",
    ]

    if dataset_info:
        for k, v in dataset_info.items():
            lines.append(f"- **{k}**: {v}")
    else:
        lines.append("- No dataset information available.")

    lines.append("\n## 2. Backtest Settings\n")
    if backtest_settings:
        for k, v in backtest_settings.items():
            lines.append(f"- **{k}**: {v}")
    else:
        lines.append("- Default settings.")

    lines.append(f"\n## 3. Benchmark Results\n")
    lines.append(f"- **Total tasks**: {benchmark.get('num_tasks', 'N/A')}")
    lines.append(f"- **Repeat runs**: {benchmark.get('repeat', 'N/A')}")

    seq = benchmark.get("sequential", {})
    lines.append(f"\n### Sequential Execution")
    lines.append(f"- Median wall time: {seq.get('median_time', 0):.4f} s")
    lines.append(f"- Completed: {seq.get('completed', 0)}")
    lines.append(f"- Failed: {seq.get('failed', 0)}")

    lines.append(f"\n### Parallel Execution")
    for nw, data in sorted(benchmark.get("parallel", {}).items()):
        lines.append(f"\n**{nw} workers:**")
        lines.append(f"- Median wall time: {data.get('median_time', 0):.4f} s")
        lines.append(f"- Speedup: {data.get('speedup', 0):.2f}x")
        lines.append(f"- Efficiency: {data.get('efficiency_pct', 0):.1f}%")

    lines.append("\n## 4. Top Strategy Configurations\n")
    if ranked_df is not None and not ranked_df.empty:
        top = ranked_df.head(10)
        lines.append(top.to_markdown())
    else:
        lines.append("No ranked results available.")

    lines.append("\n## 5. Disclaimer\n")
    lines.append(
        "> **WARNING**: Past performance does not guarantee future results. "
        "This project is for educational purposes only. The strategies tested "
        "here are not investment advice and should not be used for live trading."
    )

    return "\n".join(lines)

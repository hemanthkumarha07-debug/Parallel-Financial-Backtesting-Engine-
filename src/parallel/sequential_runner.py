"""
Sequential runner — evaluate a list of backtest tasks one at a time.
"""
import time
from typing import Any, Dict, List

from src.backtesting.execution import run_single_backtest
from src.utils.logging_config import logger


def run_sequential(
    tasks: List[Dict[str, Any]],
    df_records: list,
    df_columns: list,
) -> Dict[str, Any]:
    """
    Execute all backtest tasks sequentially.

    Parameters
    ----------
    tasks : list of dict
        Task descriptors from build_task_list().
    df_records : list
        DataFrame rows as list of dicts.
    df_columns : list
        Column names.

    Returns
    -------
    dict
        {
            "results": [result_dict, ...],
            "wall_time": float,
            "completed": int,
            "failed": int,
        }
    """
    logger.info("Starting SEQUENTIAL execution of %d tasks.", len(tasks))
    results = []
    completed = 0
    failed = 0

    t_start = time.perf_counter()

    for task in tasks:
        result = run_single_backtest(task, df_records, df_columns)
        results.append(result)
        if result["status"] == "success":
            completed += 1
        else:
            failed += 1
            logger.warning(
                "Task %s failed: %s", task["task_id"], result.get("error", "unknown")
            )

    wall_time = time.perf_counter() - t_start

    logger.info(
        "Sequential execution complete: %d/%d succeeded in %.4f s.",
        completed, len(tasks), wall_time,
    )
    return {
        "results": results,
        "wall_time": wall_time,
        "completed": completed,
        "failed": failed,
        "mode": "sequential",
        "num_workers": 1,
    }

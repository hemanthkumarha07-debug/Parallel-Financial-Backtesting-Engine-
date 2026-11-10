"""
Parallel runner — distribute backtest tasks across multiple processes
using concurrent.futures.ProcessPoolExecutor.

IMPORTANT: On Windows, multiprocessing uses 'spawn' which requires the
worker function to be importable at module scope.  The worker function
`run_single_backtest` lives in src.backtesting.execution for this reason.
"""
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Dict, List

from src.backtesting.execution import run_single_backtest
from src.utils.logging_config import logger


def run_parallel(
    tasks: List[Dict[str, Any]],
    df_records: list,
    df_columns: list,
    num_workers: int = None,
) -> Dict[str, Any]:
    """
    Execute all backtest tasks in parallel using ProcessPoolExecutor.

    Parameters
    ----------
    tasks : list of dict
        Task descriptors from build_task_list().
    df_records : list
        DataFrame rows as list of dicts.
    df_columns : list
        Column names.
    num_workers : int, optional
        Number of worker processes.  Defaults to (cpu_count - 1, min 1).

    Returns
    -------
    dict
        Same structure as sequential_runner.run_sequential().
    """
    max_cpus = multiprocessing.cpu_count()
    if num_workers is None:
        num_workers = max(1, max_cpus - 1)
    num_workers = max(1, min(num_workers, max_cpus))

    logger.info(
        "Starting PARALLEL execution of %d tasks with %d workers.",
        len(tasks), num_workers,
    )

    results = []
    completed = 0
    failed = 0

    t_start = time.perf_counter()

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        # Submit all tasks
        future_to_task = {}
        for task in tasks:
            future = executor.submit(
                run_single_backtest,
                task,
                df_records,
                df_columns,
            )
            future_to_task[future] = task["task_id"]

        # Collect results as they complete
        for future in as_completed(future_to_task):
            task_id = future_to_task[future]
            try:
                result = future.result()
                results.append(result)
                if result["status"] == "success":
                    completed += 1
                else:
                    failed += 1
                    logger.warning(
                        "Task %s failed: %s", task_id, result.get("error", "unknown")
                    )
            except Exception as exc:
                failed += 1
                results.append({
                    "task_id": task_id,
                    "status": "error",
                    "error": f"Process error: {type(exc).__name__}: {exc}",
                    "metrics": {},
                    "equity_curve": [],
                    "trades": [],
                    "execution_time": 0.0,
                    "strategy_name": "",
                    "params": {},
                })
                logger.error("Task %s raised exception: %s", task_id, exc)

    wall_time = time.perf_counter() - t_start

    # Sort results by task_id for deterministic output order
    results.sort(key=lambda r: r.get("task_id", ""))

    logger.info(
        "Parallel execution complete: %d/%d succeeded in %.4f s with %d workers.",
        completed, len(tasks), wall_time, num_workers,
    )
    return {
        "results": results,
        "wall_time": wall_time,
        "completed": completed,
        "failed": failed,
        "mode": "parallel",
        "num_workers": num_workers,
    }

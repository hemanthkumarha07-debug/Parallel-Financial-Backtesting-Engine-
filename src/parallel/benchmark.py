"""
Performance benchmarking — measure sequential vs. parallel execution
and compute speedup, efficiency, and scalability metrics.
"""
import time
from typing import Any, Dict, List, Optional

from src.parallel.sequential_runner import run_sequential
from src.parallel.parallel_runner import run_parallel
from src.utils.logging_config import logger


def run_benchmark(
    tasks: List[Dict[str, Any]],
    df_records: list,
    df_columns: list,
    worker_counts: List[int] = None,
    repeat: int = 1,
    warmup: int = 0,
) -> Dict[str, Any]:
    """
    Run a reproducible benchmark comparing sequential and parallel execution.

    Parameters
    ----------
    tasks : list of dict
        Task descriptors (same list used for all runs).
    df_records : list
        Serialized DataFrame rows.
    df_columns : list
        Column names.
    worker_counts : list of int, optional
        Worker counts to test for parallel runs.
        Defaults to [2, 4, 8] (capped at CPU count).
    repeat : int
        Number of repeated runs per configuration (median is reported).
    warmup : int
        Number of warmup runs (results discarded).

    Returns
    -------
    dict
        {
            "sequential": {wall_times, median_time, completed, failed},
            "parallel": {
                <num_workers>: {wall_times, median_time, speedup, efficiency, ...},
                ...
            },
            "num_tasks": int,
            "repeat": int,
        }
    """
    import multiprocessing
    max_cpus = multiprocessing.cpu_count()

    if worker_counts is None:
        worker_counts = [w for w in [2, 4, 8] if w <= max_cpus]
        if not worker_counts:
            worker_counts = [1]

    logger.info(
        "Starting benchmark: %d tasks, %d repeat(s), %d warmup(s), "
        "worker counts = %s.",
        len(tasks), repeat, warmup, worker_counts,
    )

    # ── Warmup ─────────────────────────────────────────────────────────
    for w in range(warmup):
        logger.info("Warmup run %d/%d (sequential)...", w + 1, warmup)
        run_sequential(tasks, df_records, df_columns)

    # ── Sequential benchmark ───────────────────────────────────────────
    seq_times = []
    seq_last_result = None
    for r in range(repeat):
        logger.info("Sequential run %d/%d...", r + 1, repeat)
        result = run_sequential(tasks, df_records, df_columns)
        seq_times.append(result["wall_time"])
        seq_last_result = result

    seq_times.sort()
    seq_median = seq_times[len(seq_times) // 2]

    benchmark = {
        "sequential": {
            "wall_times": seq_times,
            "median_time": seq_median,
            "completed": seq_last_result["completed"],
            "failed": seq_last_result["failed"],
        },
        "parallel": {},
        "num_tasks": len(tasks),
        "repeat": repeat,
    }

    # ── Parallel benchmarks ────────────────────────────────────────────
    for nw in worker_counts:
        par_times = []
        par_last_result = None

        for r in range(repeat):
            logger.info(
                "Parallel run %d/%d with %d workers...", r + 1, repeat, nw
            )
            result = run_parallel(tasks, df_records, df_columns, num_workers=nw)
            par_times.append(result["wall_time"])
            par_last_result = result

        par_times.sort()
        par_median = par_times[len(par_times) // 2]

        speedup = seq_median / par_median if par_median > 0 else 0.0
        efficiency = speedup / nw if nw > 0 else 0.0

        benchmark["parallel"][nw] = {
            "wall_times": par_times,
            "median_time": par_median,
            "speedup": round(speedup, 4),
            "efficiency": round(efficiency, 4),
            "efficiency_pct": round(efficiency * 100, 2),
            "completed": par_last_result["completed"],
            "failed": par_last_result["failed"],
            "num_workers": nw,
        }

        logger.info(
            "Workers=%d: median=%.4fs, speedup=%.2fx, efficiency=%.1f%%",
            nw, par_median, speedup, efficiency * 100,
        )

    return benchmark

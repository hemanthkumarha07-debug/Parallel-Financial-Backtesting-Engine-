"""
Task manager — parameter-grid generation and task list construction.
"""
from itertools import product
from typing import Any, Dict, List, Tuple

from src.backtesting.execution import make_task, STRATEGY_REGISTRY
from src.utils.logging_config import logger


def generate_parameter_grid(
    strategy_name: str,
    param_ranges: Dict[str, List[Any]],
) -> List[Dict[str, Any]]:
    """
    Generate all valid parameter combinations for a strategy.

    Parameters
    ----------
    strategy_name : str
        Strategy key in STRATEGY_REGISTRY.
    param_ranges : dict
        Mapping of parameter name → list of values.
        Example: {"fast_period": [5,10,15], "slow_period": [30,40,50]}

    Returns
    -------
    list of dict
        Each dict is a valid parameter combination.
    """
    if not param_ranges:
        return [{}]

    keys = list(param_ranges.keys())
    values = [param_ranges[k] for k in keys]
    combos = []

    for vals in product(*values):
        params = dict(zip(keys, vals))
        # Validate by trying to instantiate the strategy
        try:
            cls = STRATEGY_REGISTRY[strategy_name]
            cls(**params)  # Will raise ValueError for invalid combos
            combos.append(params)
        except (ValueError, TypeError):
            pass  # Skip invalid combinations

    logger.info(
        "Generated %d valid parameter combinations for %s "
        "(from %d total combinations).",
        len(combos),
        strategy_name,
        len(list(product(*values))),
    )
    return combos


def build_task_list(
    strategy_configs: List[Tuple[str, Dict[str, List[Any]]]],
    backtest_settings: Dict[str, Any],
    max_tasks: int = 5000,
) -> List[Dict[str, Any]]:
    """
    Build a complete task list from multiple strategy grid configurations.

    Parameters
    ----------
    strategy_configs : list of (strategy_name, param_ranges) tuples
    backtest_settings : dict
        Shared backtest settings for all tasks.
    max_tasks : int
        Maximum number of tasks to generate.

    Returns
    -------
    list of dict
        Task descriptors ready for execution.
    """
    tasks = []
    task_counter = 0

    for strategy_name, param_ranges in strategy_configs:
        combos = generate_parameter_grid(strategy_name, param_ranges)
        for params in combos:
            if task_counter >= max_tasks:
                logger.warning(
                    "Task limit (%d) reached. Truncating task list.", max_tasks
                )
                return tasks
            task_id = f"task_{task_counter:05d}_{strategy_name}"
            tasks.append(make_task(task_id, strategy_name, params, backtest_settings))
            task_counter += 1

    logger.info("Built task list with %d tasks.", len(tasks))
    return tasks

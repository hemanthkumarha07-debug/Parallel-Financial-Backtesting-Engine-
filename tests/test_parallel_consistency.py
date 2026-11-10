"""
Tests for sequential vs. parallel result consistency.
"""
import sys
import os
import pytest
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data.loader import generate_synthetic_ohlc
from src.data.preprocessing import preprocess_ohlc
from src.parallel.task_manager import build_task_list, generate_parameter_grid
from src.parallel.sequential_runner import run_sequential
from src.parallel.parallel_runner import run_parallel
from src.backtesting.execution import run_single_backtest, make_task


class TestParameterGrid:
    """Tests for parameter grid generation."""

    def test_grid_discards_invalid_ma(self):
        combos = generate_parameter_grid(
            "MovingAverageCrossover",
            {"fast_period": [10, 20, 50], "slow_period": [30], "ma_type": ["SMA"]},
        )
        assert len(combos) == 2

    def test_grid_all_valid(self):
        combos = generate_parameter_grid(
            "DonchianBreakout",
            {"entry_period": [10, 20], "exit_period": [5, 10]},
        )
        assert len(combos) == 4

    def test_grid_rsi_discards_invalid(self):
        combos = generate_parameter_grid(
            "RSIMeanReversion",
            {"rsi_period": [14], "oversold": [30, 60], "exit_threshold": [50]},
        )
        assert len(combos) == 1

    def test_build_task_list_limit(self):
        configs = [
            ("MovingAverageCrossover", {
                "fast_period": [5, 10, 15, 20],
                "slow_period": [30, 40, 50, 60],
                "ma_type": ["SMA"],
            }),
        ]
        tasks = build_task_list(configs, {"initial_capital": 100000}, max_tasks=5)
        assert len(tasks) <= 5

    def test_task_ids_unique(self):
        configs = [
            ("DonchianBreakout", {"entry_period": [10, 20], "exit_period": [5, 10]}),
        ]
        tasks = build_task_list(configs, {"initial_capital": 100000})
        ids = [t["task_id"] for t in tasks]
        assert len(ids) == len(set(ids))


class TestSequentialParallelConsistency:
    """Ensure sequential and parallel produce identical financial results."""

    @pytest.fixture
    def prepared_data(self):
        df = preprocess_ohlc(generate_synthetic_ohlc(num_days=200, seed=42))
        return df.to_dict("records"), list(df.columns)

    @pytest.fixture
    def task_list(self):
        configs = [
            ("MovingAverageCrossover", {
                "fast_period": [5, 10],
                "slow_period": [30, 50],
                "ma_type": ["SMA"],
            }),
            ("RSIMeanReversion", {
                "rsi_period": [14],
                "oversold": [30],
                "exit_threshold": [50],
            }),
            ("DonchianBreakout", {
                "entry_period": [20],
                "exit_period": [10],
            }),
        ]
        settings = {
            "initial_capital": 100_000,
            "commission_pct": 0.1,
            "slippage_pct": 0.05,
            "position_size_pct": 100.0,
            "risk_free_rate": 0.0,
            "trading_days_per_year": 252,
        }
        return build_task_list(configs, settings)

    def test_result_counts_match(self, task_list, prepared_data):
        records, cols = prepared_data
        seq = run_sequential(task_list, records, cols)
        par = run_parallel(task_list, records, cols, num_workers=2)
        assert seq["completed"] == par["completed"]
        assert seq["failed"] == par["failed"]

    def test_metrics_match(self, task_list, prepared_data):
        records, cols = prepared_data
        seq = run_sequential(task_list, records, cols)
        par = run_parallel(task_list, records, cols, num_workers=2)

        seq_metrics = {r["task_id"]: r["metrics"] for r in seq["results"] if r["status"] == "success"}
        par_metrics = {r["task_id"]: r["metrics"] for r in par["results"] if r["status"] == "success"}

        assert set(seq_metrics.keys()) == set(par_metrics.keys())

        for task_id in seq_metrics:
            for key in seq_metrics[task_id]:
                sv = seq_metrics[task_id][key]
                pv = par_metrics[task_id][key]
                if isinstance(sv, (int, float)):
                    assert abs(sv - pv) < 1e-6, (
                        f"Mismatch in {task_id}.{key}: seq={sv}, par={pv}"
                    )


class TestWorkerFailureHandling:
    """Tests for graceful handling of worker errors."""

    def test_invalid_strategy_returns_error(self):
        task = make_task("test_err", "NonExistentStrategy", {}, {"initial_capital": 100000})
        df = preprocess_ohlc(generate_synthetic_ohlc(num_days=50, seed=1))
        result = run_single_backtest(task, df.to_dict("records"), list(df.columns))
        assert result["status"] == "error"
        assert result["error"] is not None

    def test_invalid_params_returns_error(self):
        task = make_task("test_err2", "MovingAverageCrossover",
                         {"fast_period": 100, "slow_period": 10},
                         {"initial_capital": 100000})
        df = preprocess_ohlc(generate_synthetic_ohlc(num_days=50, seed=1))
        result = run_single_backtest(task, df.to_dict("records"), list(df.columns))
        assert result["status"] == "error"

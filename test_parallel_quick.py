"""
Quick integration test for sequential vs parallel consistency.
Run from the project root:  python test_parallel_quick.py
"""
import sys
sys.path.insert(0, ".")

from src.data.loader import load_csv
from src.data.preprocessing import preprocess_ohlc
from src.parallel.task_manager import build_task_list
from src.parallel.sequential_runner import run_sequential
from src.parallel.parallel_runner import run_parallel


def main():
    # Load data
    df = preprocess_ohlc(load_csv("data/sample_ohlc.csv"))
    df_records = df.to_dict("records")
    df_columns = list(df.columns)

    # Build a small parameter grid
    strategy_configs = [
        ("MovingAverageCrossover", {"fast_period": [5, 10, 15], "slow_period": [30, 50]}),
        ("RSIMeanReversion", {"rsi_period": [10, 14], "oversold": [25, 30], "exit_threshold": [50]}),
        ("DonchianBreakout", {"entry_period": [15, 20, 25], "exit_period": [10]}),
    ]
    backtest_settings = {
        "initial_capital": 100000,
        "commission_pct": 0.1,
        "slippage_pct": 0.05,
        "position_size_pct": 100.0,
        "risk_free_rate": 0.0,
        "trading_days_per_year": 252,
    }

    tasks = build_task_list(strategy_configs, backtest_settings)
    print(f"Generated {len(tasks)} tasks")

    # Sequential
    seq_result = run_sequential(tasks, df_records, df_columns)
    print(f"Sequential: {seq_result['completed']} completed, {seq_result['failed']} failed, {seq_result['wall_time']:.4f}s")

    # Parallel
    par_result = run_parallel(tasks, df_records, df_columns, num_workers=4)
    print(f"Parallel:   {par_result['completed']} completed, {par_result['failed']} failed, {par_result['wall_time']:.4f}s")

    # Compare results
    seq_metrics = {r["task_id"]: r["metrics"] for r in seq_result["results"] if r["status"] == "success"}
    par_metrics = {r["task_id"]: r["metrics"] for r in par_result["results"] if r["status"] == "success"}

    print(f"\nComparing {len(seq_metrics)} sequential vs {len(par_metrics)} parallel results...")
    mismatches = 0
    for task_id in seq_metrics:
        if task_id not in par_metrics:
            print(f"  MISSING in parallel: {task_id}")
            mismatches += 1
            continue
        for key in seq_metrics[task_id]:
            sv = seq_metrics[task_id][key]
            pv = par_metrics[task_id][key]
            if isinstance(sv, (int, float)):
                if abs(sv - pv) > 1e-6:
                    print(f"  MISMATCH {task_id}.{key}: seq={sv}, par={pv}")
                    mismatches += 1

    if mismatches == 0:
        print("PASS: All results match between sequential and parallel execution.")
    else:
        print(f"FAIL: {mismatches} mismatches found!")

    speedup = seq_result["wall_time"] / par_result["wall_time"] if par_result["wall_time"] > 0 else 0
    print(f"\nSpeedup: {speedup:.2f}x")


if __name__ == "__main__":
    main()

# System Architecture: Parallel Financial Strategy Backtesting Engine (PFSBE)

## 1. High-Level Architecture Overview

The Parallel Financial Strategy Backtesting Engine (PFSBE) is engineered with a strict decoupled design separating user interaction, data validation, trading signal generation, trade execution, and parallel process scheduling.

```
+-------------------------------------------------------------+
|                      Streamlit Web UI                       |
|   (Data Explorer | Strategy Config | Results | Benchmark)   |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                     Analytics & Reports                     |
|  (Strategy Ranking | Experiment Reporting | CSV Exporters)  |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                  Parallel Task Management                   |
|   (Grid Generator | Task Serializer | Result Aggregator)    |
+--------------+-------------------------------+--------------+
               |                               |
               v                               v
    +--------------------+           +--------------------+
    | Sequential Runner  |           |  Parallel Runner   |
    | (1 single process) |           | (ProcessPoolExec)  |
    +----------+---------+           +---------+----------+
               \                               /
                \                             /
                 v                           v
+-------------------------------------------------------------+
|               Unified Backtest Execution Engine             |
|   (Bar-by-Bar Event Simulation | Zero Lookahead Execution)   |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                     Portfolio & Metrics                     |
| (Position Tracking | Cash | Drawdown | Sharpe | Win Rate)   |
+-------------------------------------------------------------+
```

## 2. Component Breakdown

### 2.1 Data Processing Layer (`src/data/`)
- **`loader.py`**: Ingests raw CSV data from file or uploaded bytes, maps non-standard column names to normalized aliases (`open`, `high`, `low`, `close`, `volume`, `date`), and synthesizes geometric Brownian motion OHLC candles for deterministic testing.
- **`validator.py`**: Implements 7 data integrity checks:
  1. Required OHLC columns existence.
  2. DateTime parseability and formatting.
  3. Duplicate timestamp detection.
  4. Null / NaN detection.
  5. Strict positivity of prices ($P > 0$).
  6. OHLC relationship integrity ($Low \le Open, Close \le High$).
  7. Time series interval discontinuity checks (warning on anomalous gaps without synthetic candle fabrication).
- **`preprocessing.py`**: Chronological sorting, deduplication, float64 precision casting, and optional sub-interval date slicing.

### 2.2 Strategy Layer (`src/strategies/`)
- **`base.py`**: Abstract base class (`BaseStrategy`) enforcing `validate_params()`, `generate_signals()`, `warmup_period`, and serializable `param_dict()`.
- **`moving_average.py`**: Fast/Slow SMA and EMA crossovers. Generates long entries on golden crosses and exits on death crosses. Enforces $Fast < Slow$.
- **`rsi_mean_reversion.py`**: Wilder-smoothed Relative Strength Index. Generates long entries when oversold threshold is reached and exits when mean recovery threshold is met.
- **`donchian_breakout.py`**: Upper/Lower channel breakouts. Uses shifted rolling windows ($t-1$) to guarantee zero look-ahead bias.

### 2.3 Backtesting Core (`src/backtesting/`)
- **`portfolio.py`**: Position ledger tracking cash balance, share quantity, cost-basis, commissions, slippage, and mark-to-market equity.
- **`engine.py`**: Strict bar-by-bar execution simulator:
  - Signal computed at candle $t$ close $\rightarrow$ executed at candle $t+1$ open.
  - Realistic commission deductions and slippage haircuts on each fill.
- **`metrics.py`**: Calculates total return, annualized compound return, peak-to-trough maximum drawdown, annualized Sharpe ratio ($R_f$ aware), win rate, profit factor, trade count, and transaction friction totals.
- **`execution.py`**: Top-level entry point `run_single_backtest` designed at module scope for cross-platform multiprocessing pickling.

### 2.4 Parallel Computing Layer (`src/parallel/`)
- **`task_manager.py`**: Generates Cartesian parameter grids, filters invalid combinations, and builds deterministic tasks.
- **`sequential_runner.py`**: Single-threaded baseline runner.
- **`parallel_runner.py`**: Multi-process worker pool using `concurrent.futures.ProcessPoolExecutor`.
- **`benchmark.py`**: Multi-run benchmarking module recording median wall-clock runtimes, speedup, and parallel efficiency.

### 2.5 Analytics Layer (`src/analytics/`)
- **`ranking.py`**: Multi-criteria ranking and custom multi-objective scoring.
- **`report_generator.py`**: Generates CSV downloads and markdown audit summaries.

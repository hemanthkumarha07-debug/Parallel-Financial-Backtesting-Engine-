# Parallel Financial Strategy Backtesting Engine (PFSBE)

![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)
![Tests](https://img.shields.io/badge/Tests-72%20Passed-emerald.svg)
![Multiprocessing](https://img.shields.io/badge/Parallel-ProcessPoolExecutor-cyan.svg)
![UI](https://img.shields.io/badge/UI-Streamlit-red.svg)

An educational and academic parallel computing application demonstrating how multi-core process parallelism accelerates algorithmic trading strategy evaluations and parameter grid searches over historical OHLC financial data.

---

## Key Features

1. **Robust OHLC Data Ingestion**:
   - Automatic column normalization (e.g. `Date`, `Timestamp`, `Open`, `High`, `Low`, `Close`, `Volume`).
   - 7-point data integrity validation (duplicate timestamps, missing values, impossible OHLC geometry, negative prices, and gap warnings).
   - Built-in deterministic synthetic OHLC generator (Geometric Brownian Motion) for demonstration and testing.

2. **Modular Trading Strategies**:
   - **Moving Average Crossover**: Fast/Slow SMA and EMA crossovers.
   - **RSI Mean Reversion**: Wilder-smoothed RSI with oversold entry and mean-reversion exit.
   - **Donchian Breakout**: Multi-period channel breakouts with shifted rolling windows to eliminate look-ahead bias.

3. **Custom Zero Look-Ahead Backtesting Engine**:
   - Signal computed at candle $t$ close $\rightarrow$ executed at candle $t+1$ open.
   - Realistic commission and slippage transaction friction modeling.
   - Full mark-to-market portfolio accounting, cash tracking, and equity curve generation.

4. **True Parallel Computing Engine**:
   - Built using Python's `concurrent.futures.ProcessPoolExecutor` to bypass the Global Interpreter Lock (GIL).
   - Cross-platform support (seamless Windows `spawn` and Linux `fork` process creation).
   - Benchmarking module with real measured Speedup ($S_p$), Parallel Efficiency ($E_p$), and scalability charts.

5. **Financial Analytics & Ranking**:
   - Total return, annualized return, max drawdown, Sharpe ratio ($R_f$ aware), win rate, profit factor, average trade duration, and total transaction costs.
   - Interactive ranking by Sharpe ratio, return, drawdown, or multi-objective weighted scores.

6. **Interactive Streamlit Dashboard**:
   - Professional dark-navy quantitative research UI.
   - 6 functional pages: Overview, Data Explorer, Strategy Configuration, Backtest Results, Parallel Performance Lab, and Reports & Exports.
   - One-click export for Backtest Results CSV, Trade History CSV, Benchmark CSV, and Markdown audit reports.

---

## Directory Structure

```text
parallel_financial_backtester/
│   app.py                        # Streamlit web dashboard entry point
│   requirements.txt              # Pinned project dependencies
│   README.md                     # Complete project documentation
│   test_parallel_quick.py        # Fast verification script for sequential vs parallel
│   .gitignore                    # Clean git ignores
│
├── config/
│       settings.py               # Global parameters, limits, and defaults
│
├── data/
│       sample_ohlc.csv           # 504-bar deterministic synthetic OHLC dataset
│       README.md                 # Dataset specifications and instructions
│
├── src/
│   ├── data/
│   │       loader.py             # CSV reader & synthetic data generator
│   │       validator.py          # 7-point OHLC quality validation
│   │       preprocessing.py      # Sorting, deduplication & datetime slicing
│   ├── strategies/
│   │       base.py               # Abstract BaseStrategy interface
│   │       moving_average.py     # SMA/EMA Crossover strategy
│   │       rsi_mean_reversion.py # RSI Mean Reversion strategy
│   │       donchian_breakout.py  # Donchian Channel Breakout strategy
│   ├── backtesting/
│   │       portfolio.py          # Cash, position, trades, & equity ledger
│   │       engine.py             # Bar-by-bar execution simulator
│   │       metrics.py            # Financial and risk metrics calculator
│   │       execution.py          # Top-level picklable task runner
│   ├── parallel/
│   │       task_manager.py       # Parameter grid generator & task builder
│   │       sequential_runner.py  # Single-process baseline runner
│   │       parallel_runner.py    # ProcessPoolExecutor multi-core runner
│   │       benchmark.py          # Multi-run runtime, speedup & efficiency benchmark
│   ├── analytics/
│   │       ranking.py            # Strategy comparison & multi-criteria ranking
│   │       report_generator.py   # CSV and markdown report exporters
│   └── utils/
│           logging_config.py     # Structured console and file logging
│           validation.py         # Numerical range and parameter validators
│
├── tests/
│       conftest.py               # Shared pytest fixtures
│       test_data_validation.py   # Loader, validation & preprocessing tests
│       test_strategies.py        # Strategy signals & indicators tests
│       test_backtesting.py       # Portfolio, engine & timing tests
│       test_parallel_consistency.py # Sequential vs parallel verification tests
│       test_metrics.py           # Financial metrics edge-case tests
│
└── docs/
        architecture.md           # System architecture document
        parallel_computing.md     # Parallel methodology, speedup & Amdahl's law
        methodology.md            # Trading rules & financial math formulas
        limitations.md            # Assumptions, boundaries & future work
        viva_questions.md         # Comprehensive viva voce Q&A guide
```

---

## Installation & Setup

### 1. Prerequisites
- Python 3.11 (or 3.10+)
- Windows, Linux, or macOS

### 2. Install Dependencies
```bash
cd parallel_financial_backtester
pip install -r requirements.txt
```

### 3. Run Automated Tests
Execute the full test suite (72 automated tests):
```bash
pytest tests -v
```

### 4. Verify Sequential vs. Parallel Consistency
Run the quick verification script:
```bash
python test_parallel_quick.py
```

### 5. Launch the Streamlit Dashboard
```bash
streamlit run app.py
```
Then open your browser at `http://localhost:8501`.

---

## How to Use the Application

1. **Data Explorer**:
   - Click **"Load Sample Dataset"** to load the pre-generated 504-candle dataset, or generate custom synthetic data, or upload your own CSV file.
   - Inspect the interactive candlestick chart and data quality report.
2. **Strategy Configuration**:
   - Choose parameter ranges for Moving Average, RSI, and Donchian Breakout.
   - Select **"Both (Benchmark)"** mode and pick your desired worker count.
   - Click **"Run Backtests"**.
3. **Backtest Results**:
   - Compare all strategy configurations in the ranking table.
   - Select any individual configuration to view its equity curve, drawdown chart, and round-trip trade history.
4. **Parallel Performance Lab**:
   - Execute benchmark tests across different worker counts (e.g. 2, 4, 8 cores).
   - Visualize real measured Speedup ($S_p$), Parallel Efficiency ($E_p$), and runtime curves.
5. **Reports & Exports**:
   - Download the Backtest Results CSV, Trades CSV, Benchmark Results CSV, or Markdown summary report.

---

## Parallel Computing Formulas

- **Speedup**:
  $$S_p = \frac{T_1}{T_p}$$
- **Parallel Efficiency**:
  $$E_p = \frac{S_p}{p} \times 100\%$$
- **Amdahl's Law**:
  $$S_{\text{max}} = \frac{1}{(1 - f) + \frac{f}{p}}$$

---

## Academic Disclaimer
This project is developed solely for academic research, education, and parallel computing benchmarking. It is not financial or investment advice.

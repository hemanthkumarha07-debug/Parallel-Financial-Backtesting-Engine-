"""
Global configuration settings for the Parallel Financial Strategy Backtesting Engine.
"""
import multiprocessing

# ── Data Ingestion ──────────────────────────────────────────────────────────
MAX_UPLOAD_SIZE_MB = 50
REQUIRED_OHLC_COLUMNS = ["open", "high", "low", "close"]
OPTIONAL_COLUMNS = ["volume"]
SUPPORTED_DATE_FORMATS = [
    "%Y-%m-%d",
    "%Y-%m-%d %H:%M:%S",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%Y/%m/%d",
    "%Y-%m-%dT%H:%M:%S",
]

# ── Backtesting Defaults ───────────────────────────────────────────────────
DEFAULT_INITIAL_CAPITAL = 100_000.0
DEFAULT_COMMISSION_PCT = 0.1       # 0.1 % per trade
DEFAULT_SLIPPAGE_PCT = 0.05        # 0.05 % slippage
DEFAULT_POSITION_SIZE_PCT = 100.0  # Invest 100 % of available capital
RISK_FREE_RATE = 0.0               # Annualized risk-free rate for Sharpe
TRADING_DAYS_PER_YEAR = 252

# ── Parallel Computing ─────────────────────────────────────────────────────
MAX_CPU_COUNT = multiprocessing.cpu_count()
DEFAULT_WORKER_COUNT = max(1, MAX_CPU_COUNT - 1)
MAX_PARAMETER_GRID_SIZE = 5_000
BENCHMARK_WARMUP_RUNS = 1
BENCHMARK_REPEAT_RUNS = 3

# ── UI ─────────────────────────────────────────────────────────────────────
APP_TITLE = "Parallel Financial Strategy Backtesting Engine"
APP_SUBTITLE = "PFSBE — Academic Parallel Computing Project"
PAGE_ICON = "📊"

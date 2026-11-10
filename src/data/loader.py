"""
OHLC data loading from CSV files and synthetic data generation.
"""
import io
from typing import Optional, Tuple

import numpy as np
import pandas as pd

from src.utils.logging_config import logger


# ---------------------------------------------------------------------------
# Column name normalization
# ---------------------------------------------------------------------------
_COLUMN_MAP = {
    # date / timestamp variants
    "date": "date", "timestamp": "date", "datetime": "date", "time": "date",
    "date/time": "date",
    # OHLCV variants
    "open": "open", "o": "open", "open_price": "open",
    "high": "high", "h": "high", "high_price": "high",
    "low": "low", "l": "low", "low_price": "low",
    "close": "close", "c": "close", "close_price": "close", "adj close": "close",
    "volume": "volume", "vol": "volume", "v": "volume",
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to lowercase standard names."""
    rename_map = {}
    for col in df.columns:
        key = col.strip().lower().replace("_", " ").replace("-", " ")
        # Collapse multiple spaces
        key = " ".join(key.split())
        # Replace space back to underscore for lookup where needed
        for pattern, target in _COLUMN_MAP.items():
            if key == pattern or key.replace(" ", "_") == pattern:
                rename_map[col] = target
                break
    df = df.rename(columns=rename_map)
    return df


def load_csv(file_or_path, max_size_mb: float = 50.0) -> pd.DataFrame:
    """
    Load an OHLC CSV file and normalize its columns.

    Parameters
    ----------
    file_or_path : str, pathlib.Path, or file-like
        Path to CSV or an uploaded file buffer.
    max_size_mb : float
        Maximum allowed file size in megabytes.

    Returns
    -------
    pd.DataFrame
        Raw dataframe with normalized column names.
    """
    # Size check for file-like objects
    if hasattr(file_or_path, "seek") and hasattr(file_or_path, "read"):
        file_or_path.seek(0, 2)
        size_mb = file_or_path.tell() / (1024 * 1024)
        file_or_path.seek(0)
        if size_mb > max_size_mb:
            raise ValueError(
                f"File size ({size_mb:.1f} MB) exceeds limit ({max_size_mb} MB)."
            )

    df = pd.read_csv(file_or_path)
    if df.empty:
        raise ValueError("CSV file is empty.")

    df = _normalize_columns(df)
    logger.info("Loaded CSV with %d rows and columns: %s", len(df), list(df.columns))
    return df


# ---------------------------------------------------------------------------
# Synthetic data generation
# ---------------------------------------------------------------------------

def generate_synthetic_ohlc(
    num_days: int = 504,
    start_date: str = "2022-01-03",
    start_price: float = 100.0,
    volatility: float = 0.02,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate a deterministic synthetic OHLC dataset using geometric Brownian motion.

    This data is for testing and demonstration only.
    It does NOT represent real market prices.

    Parameters
    ----------
    num_days : int
        Number of trading days to generate.
    start_date : str
        ISO start date string.
    start_price : float
        Starting close price.
    volatility : float
        Daily log-return standard deviation.
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        Columns: date, open, high, low, close, volume
    """
    rng = np.random.default_rng(seed)

    dates = pd.bdate_range(start=start_date, periods=num_days)

    # Generate log returns
    log_returns = rng.normal(loc=0.0003, scale=volatility, size=num_days)
    # Cumulative price path from close prices
    close_prices = start_price * np.exp(np.cumsum(log_returns))

    # Generate intraday ranges
    intraday_range = np.abs(rng.normal(0, volatility * start_price * 0.5, num_days))

    open_prices = close_prices * (1 + rng.normal(0, 0.003, num_days))
    high_prices = np.maximum(open_prices, close_prices) + np.abs(intraday_range * 0.5)
    low_prices = np.minimum(open_prices, close_prices) - np.abs(intraday_range * 0.5)

    # Ensure OHLC validity: low <= open,close <= high
    low_prices = np.minimum(low_prices, np.minimum(open_prices, close_prices))
    high_prices = np.maximum(high_prices, np.maximum(open_prices, close_prices))

    # Ensure all prices are positive
    low_prices = np.maximum(low_prices, 0.01)
    open_prices = np.maximum(open_prices, low_prices)
    close_prices = np.maximum(close_prices, low_prices)
    high_prices = np.maximum(high_prices, np.maximum(open_prices, close_prices))

    volume = rng.integers(100_000, 5_000_000, size=num_days)

    df = pd.DataFrame({
        "date": dates,
        "open": np.round(open_prices, 4),
        "high": np.round(high_prices, 4),
        "low": np.round(low_prices, 4),
        "close": np.round(close_prices, 4),
        "volume": volume,
    })

    logger.info(
        "Generated synthetic OHLC: %d rows, %s to %s",
        len(df), df["date"].iloc[0].date(), df["date"].iloc[-1].date()
    )
    return df

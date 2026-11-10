"""
Shared test fixtures for the PFSBE test suite.
"""
import sys
import os
import pytest
import pandas as pd
import numpy as np

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def sample_ohlc_df():
    """Deterministic 100-bar OHLC DataFrame."""
    rng = np.random.default_rng(42)
    n = 100
    dates = pd.bdate_range("2023-01-02", periods=n)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    open_ = close * (1 + rng.normal(0, 0.002, n))
    high = np.maximum(open_, close) + np.abs(rng.normal(0, 0.5, n))
    low = np.minimum(open_, close) - np.abs(rng.normal(0, 0.5, n))
    low = np.maximum(low, 0.01)
    high = np.maximum(high, np.maximum(open_, close))
    vol = rng.integers(100_000, 1_000_000, n)
    return pd.DataFrame({
        "date": dates,
        "open": np.round(open_, 4),
        "high": np.round(high, 4),
        "low": np.round(low, 4),
        "close": np.round(close, 4),
        "volume": vol,
    })


@pytest.fixture
def tiny_ohlc_df():
    """Minimal 5-bar OHLC DataFrame."""
    return pd.DataFrame({
        "date": pd.bdate_range("2023-01-02", periods=5),
        "open": [100.0, 101.0, 102.0, 101.5, 103.0],
        "high": [101.0, 102.5, 103.0, 102.0, 104.0],
        "low": [99.0, 100.5, 101.0, 100.0, 102.0],
        "close": [100.5, 102.0, 101.5, 101.0, 103.5],
        "volume": [1000, 1200, 1100, 900, 1300],
    })


@pytest.fixture
def large_ohlc_df():
    """504-bar OHLC DataFrame for performance testing."""
    from src.data.loader import generate_synthetic_ohlc
    return generate_synthetic_ohlc(num_days=504, seed=42)

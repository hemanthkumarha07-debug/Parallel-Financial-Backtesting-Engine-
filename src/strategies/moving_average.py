"""
Strategy A — Moving Average Crossover.

Entry: Fast MA crosses above Slow MA  → signal = +1
Exit:  Fast MA crosses below Slow MA  → signal = −1
"""
from typing import Any, Dict

import pandas as pd
import numpy as np

from src.strategies.base import BaseStrategy
from src.utils.validation import validate_integer_positive, validate_less_than


class MovingAverageCrossover(BaseStrategy):
    """
    Two-moving-average crossover strategy (long-only).

    Parameters
    ----------
    fast_period : int
        Lookback for the fast moving average (must be < slow_period).
    slow_period : int
        Lookback for the slow moving average.
    ma_type : str
        'SMA' for Simple Moving Average, 'EMA' for Exponential Moving Average.
    """

    def __init__(
        self,
        fast_period: int = 10,
        slow_period: int = 50,
        ma_type: str = "SMA",
    ):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.ma_type = ma_type.upper()
        self.validate_params()

    @property
    def name(self) -> str:
        return "Moving Average Crossover"

    @property
    def warmup_period(self) -> int:
        return self.slow_period

    def validate_params(self) -> None:
        validate_integer_positive(self.fast_period, "fast_period")
        validate_integer_positive(self.slow_period, "slow_period")
        validate_less_than(self.fast_period, self.slow_period, "fast_period", "slow_period")
        if self.ma_type not in ("SMA", "EMA"):
            raise ValueError(f"ma_type must be 'SMA' or 'EMA', got '{self.ma_type}'")

    def param_dict(self) -> Dict[str, Any]:
        return {
            "fast_period": self.fast_period,
            "slow_period": self.slow_period,
            "ma_type": self.ma_type,
        }

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        close = df["close"]

        if self.ma_type == "SMA":
            fast_ma = close.rolling(window=self.fast_period, min_periods=self.fast_period).mean()
            slow_ma = close.rolling(window=self.slow_period, min_periods=self.slow_period).mean()
        else:  # EMA
            fast_ma = close.ewm(span=self.fast_period, min_periods=self.fast_period, adjust=False).mean()
            slow_ma = close.ewm(span=self.slow_period, min_periods=self.slow_period, adjust=False).mean()

        df["fast_ma"] = fast_ma
        df["slow_ma"] = slow_ma

        # Crossover detection
        # Position indicator: 1 when fast > slow, 0 otherwise
        above = (fast_ma > slow_ma).astype(int)
        cross = above.diff()

        signal = pd.Series(0, index=df.index, dtype=int)
        signal[cross == 1] = 1    # Fast crosses above slow → enter long
        signal[cross == -1] = -1  # Fast crosses below slow → exit

        df["signal"] = signal
        return df

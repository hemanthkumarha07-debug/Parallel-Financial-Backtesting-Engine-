"""
Strategy B — RSI Mean Reversion.

Entry: RSI drops to or below the oversold threshold  → signal = +1
Exit:  RSI recovers to or above the exit threshold    → signal = −1
"""
from typing import Any, Dict

import pandas as pd
import numpy as np

from src.strategies.base import BaseStrategy
from src.utils.validation import validate_integer_positive, validate_less_than


def compute_rsi(close: pd.Series, period: int) -> pd.Series:
    """
    Compute the Relative Strength Index (RSI).

    RSI = 100 − 100 / (1 + RS)
    RS  = average gain / average loss  (Wilder smoothing)

    Parameters
    ----------
    close : pd.Series
        Closing prices.
    period : int
        RSI lookback period.

    Returns
    -------
    pd.Series
        RSI values (0–100), with NaN for the warm-up period.
    """
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    # Wilder smoothing (equivalent to EMA with alpha = 1/period)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


class RSIMeanReversion(BaseStrategy):
    """
    RSI-based mean-reversion strategy (long-only).

    Parameters
    ----------
    rsi_period : int
        RSI lookback period (default 14).
    oversold : float
        Entry threshold — enter when RSI ≤ this value (default 30).
    exit_threshold : float
        Exit threshold — exit when RSI ≥ this value (default 50).
    """

    def __init__(
        self,
        rsi_period: int = 14,
        oversold: float = 30.0,
        exit_threshold: float = 50.0,
    ):
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.exit_threshold = exit_threshold
        self.validate_params()

    @property
    def name(self) -> str:
        return "RSI Mean Reversion"

    @property
    def warmup_period(self) -> int:
        return self.rsi_period + 1

    def validate_params(self) -> None:
        validate_integer_positive(self.rsi_period, "rsi_period")
        if not (0 < self.oversold < 100):
            raise ValueError(f"oversold must be between 0 and 100, got {self.oversold}")
        if not (0 < self.exit_threshold < 100):
            raise ValueError(
                f"exit_threshold must be between 0 and 100, got {self.exit_threshold}"
            )
        validate_less_than(
            self.oversold, self.exit_threshold, "oversold", "exit_threshold"
        )

    def param_dict(self) -> Dict[str, Any]:
        return {
            "rsi_period": self.rsi_period,
            "oversold": self.oversold,
            "exit_threshold": self.exit_threshold,
        }

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        rsi = compute_rsi(df["close"], self.rsi_period)
        df["rsi"] = rsi

        signal = pd.Series(0, index=df.index, dtype=int)
        in_position = False

        for i in range(len(df)):
            if pd.isna(rsi.iloc[i]):
                continue
            if not in_position and rsi.iloc[i] <= self.oversold:
                signal.iloc[i] = 1   # Enter long
                in_position = True
            elif in_position and rsi.iloc[i] >= self.exit_threshold:
                signal.iloc[i] = -1  # Exit
                in_position = False

        df["signal"] = signal
        return df

"""
Strategy C — Donchian Channel Breakout.

Entry: Close breaks above the previous period's rolling high  → signal = +1
Exit:  Close breaks below the previous period's rolling low   → signal = −1

Uses shifted rolling windows so the current bar is excluded from the
channel calculation — no look-ahead bias.
"""
from typing import Any, Dict

import pandas as pd
import numpy as np

from src.strategies.base import BaseStrategy
from src.utils.validation import validate_integer_positive


class DonchianBreakout(BaseStrategy):
    """
    Donchian channel breakout strategy (long-only).

    Parameters
    ----------
    entry_period : int
        Lookback period for the entry (upper) channel.
    exit_period : int
        Lookback period for the exit (lower) channel.
    """

    def __init__(self, entry_period: int = 20, exit_period: int = 10):
        self.entry_period = entry_period
        self.exit_period = exit_period
        self.validate_params()

    @property
    def name(self) -> str:
        return "Donchian Breakout"

    @property
    def warmup_period(self) -> int:
        return max(self.entry_period, self.exit_period) + 1

    def validate_params(self) -> None:
        validate_integer_positive(self.entry_period, "entry_period")
        validate_integer_positive(self.exit_period, "exit_period")

    def param_dict(self) -> Dict[str, Any]:
        return {
            "entry_period": self.entry_period,
            "exit_period": self.exit_period,
        }

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Shifted channels — exclude current bar
        upper_channel = (
            df["high"]
            .rolling(window=self.entry_period, min_periods=self.entry_period)
            .max()
            .shift(1)
        )
        lower_channel = (
            df["low"]
            .rolling(window=self.exit_period, min_periods=self.exit_period)
            .min()
            .shift(1)
        )

        df["upper_channel"] = upper_channel
        df["lower_channel"] = lower_channel

        signal = pd.Series(0, index=df.index, dtype=int)
        in_position = False

        for i in range(len(df)):
            if pd.isna(upper_channel.iloc[i]) or pd.isna(lower_channel.iloc[i]):
                continue
            if not in_position and df["close"].iloc[i] > upper_channel.iloc[i]:
                signal.iloc[i] = 1   # Breakout entry
                in_position = True
            elif in_position and df["close"].iloc[i] < lower_channel.iloc[i]:
                signal.iloc[i] = -1  # Breakdown exit
                in_position = False

        df["signal"] = signal
        return df

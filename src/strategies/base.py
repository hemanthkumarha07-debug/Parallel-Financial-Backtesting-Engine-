"""
Abstract base class for all trading strategies.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List

import pandas as pd
import numpy as np


@dataclass
class Signal:
    """Represents a trading signal on a single bar."""
    date: pd.Timestamp
    signal: int           # +1 = long entry, -1 = exit, 0 = hold
    price: float          # Reference price (close of signal bar)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseStrategy(ABC):
    """
    Abstract base class that every strategy must inherit.

    Subclasses implement:
        - `name`           (property) — human-readable strategy name
        - `validate_params` — raise on invalid parameters
        - `generate_signals`— compute entry/exit signals
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable strategy name."""

    @abstractmethod
    def validate_params(self) -> None:
        """Raise ValueError for invalid parameter combinations."""

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add a 'signal' column to df.

        Parameters
        ----------
        df : pd.DataFrame
            Must contain at least: date, open, high, low, close.

        Returns
        -------
        pd.DataFrame
            Copy of df with an added 'signal' column:
                +1 = long entry
                -1 = exit / close position
                 0 = hold / no action
        """

    @property
    @abstractmethod
    def warmup_period(self) -> int:
        """Number of initial bars consumed by the indicator before valid signals."""

    @abstractmethod
    def param_dict(self) -> Dict[str, Any]:
        """Return a serializable dict of the strategy's current parameters."""

    def __repr__(self) -> str:
        return f"{self.name}({self.param_dict()})"

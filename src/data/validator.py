"""
OHLC data validation — detect and report quality issues before backtesting.
"""
from dataclasses import dataclass, field
from typing import List, Optional

import pandas as pd
import numpy as np

from src.utils.logging_config import logger


@dataclass
class ValidationReport:
    """Container for data-quality findings."""
    is_valid: bool = True
    row_count: int = 0
    date_range: str = ""
    missing_columns: List[str] = field(default_factory=list)
    missing_values: dict = field(default_factory=dict)
    duplicate_timestamps: int = 0
    invalid_ohlc_rows: int = 0
    negative_price_rows: int = 0
    time_gaps: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)
        logger.warning("Validation warning: %s", msg)

    def add_error(self, msg: str) -> None:
        self.is_valid = False
        self.errors.append(msg)
        logger.error("Validation error: %s", msg)


def validate_ohlc(df: pd.DataFrame) -> ValidationReport:
    """
    Validate an OHLC DataFrame and return a detailed report.

    Checks performed
    ----------------
    1. Required columns exist (date, open, high, low, close).
    2. Date column can be parsed as datetime.
    3. No duplicate timestamps.
    4. No missing values in OHLC columns.
    5. Prices are positive.
    6. OHLC relationship: low <= open,close <= high for every row.
    7. Warn about time-series gaps (but do NOT invent candles).
    """
    report = ValidationReport()

    # ── 1. Required columns ────────────────────────────────────────────────
    required = ["date", "open", "high", "low", "close"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        report.missing_columns = missing
        report.add_error(f"Missing required columns: {missing}")
        return report

    report.row_count = len(df)
    if report.row_count == 0:
        report.add_error("Dataset is empty.")
        return report

    # ── 2. Parse dates ─────────────────────────────────────────────────────
    try:
        df["date"] = pd.to_datetime(df["date"], utc=False)
    except Exception as exc:
        report.add_error(f"Cannot parse date column: {exc}")
        return report

    report.date_range = f"{df['date'].min().date()} to {df['date'].max().date()}"

    # ── 3. Duplicate timestamps ────────────────────────────────────────────
    dup_count = df["date"].duplicated().sum()
    report.duplicate_timestamps = int(dup_count)
    if dup_count > 0:
        report.add_error(f"{dup_count} duplicate timestamp(s) found.")

    # ── 4. Missing values ──────────────────────────────────────────────────
    ohlc_cols = ["open", "high", "low", "close"]
    for col in ohlc_cols:
        n_missing = int(df[col].isna().sum())
        if n_missing > 0:
            report.missing_values[col] = n_missing
            report.add_error(f"Column '{col}' has {n_missing} missing value(s).")

    if "volume" in df.columns:
        n_missing_vol = int(df["volume"].isna().sum())
        if n_missing_vol > 0:
            report.missing_values["volume"] = n_missing_vol
            report.add_warning(f"Column 'volume' has {n_missing_vol} missing value(s).")

    # ── 5. Positive prices ─────────────────────────────────────────────────
    numeric_mask = df[ohlc_cols].apply(pd.to_numeric, errors="coerce")
    neg_mask = (numeric_mask <= 0).any(axis=1)
    report.negative_price_rows = int(neg_mask.sum())
    if report.negative_price_rows > 0:
        report.add_error(
            f"{report.negative_price_rows} row(s) with non-positive prices."
        )

    # ── 6. OHLC relationship ──────────────────────────────────────────────
    if report.missing_values:
        pass  # Skip relationship check if values are missing
    else:
        o = df["open"].astype(float)
        h = df["high"].astype(float)
        l = df["low"].astype(float)
        c = df["close"].astype(float)

        invalid = (
            (l > o) | (l > c) | (h < o) | (h < c) | (l > h)
        )
        report.invalid_ohlc_rows = int(invalid.sum())
        if report.invalid_ohlc_rows > 0:
            report.add_error(
                f"{report.invalid_ohlc_rows} row(s) violate OHLC relationship "
                "(low ≤ open,close ≤ high)."
            )

    # ── 7. Time-series gaps ────────────────────────────────────────────────
    if report.row_count > 1 and report.duplicate_timestamps == 0:
        sorted_dates = df["date"].sort_values()
        diffs = sorted_dates.diff().dropna()
        median_gap = diffs.median()
        if median_gap > pd.Timedelta(0):
            large_gaps = diffs[diffs > median_gap * 3]
            report.time_gaps = len(large_gaps)
            if report.time_gaps > 0:
                report.add_warning(
                    f"{report.time_gaps} gap(s) larger than 3× the median "
                    f"interval ({median_gap}) detected. This may reflect "
                    "weekends, holidays, or missing data."
                )

    logger.info(
        "Validation complete: valid=%s, rows=%d, errors=%d, warnings=%d",
        report.is_valid, report.row_count, len(report.errors), len(report.warnings),
    )
    return report

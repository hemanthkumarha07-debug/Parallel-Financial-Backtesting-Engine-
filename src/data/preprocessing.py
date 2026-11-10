"""
OHLC data preprocessing — sort, clean, and prepare data for backtesting.
"""
import pandas as pd
import numpy as np

from src.utils.logging_config import logger


def preprocess_ohlc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare a validated OHLC DataFrame for backtesting.

    Steps
    -----
    1. Ensure date column is datetime.
    2. Sort chronologically.
    3. Remove duplicate timestamps (keep first).
    4. Cast OHLC columns to float64.
    5. Reset index.

    Parameters
    ----------
    df : pd.DataFrame
        Raw OHLC data with normalized column names.

    Returns
    -------
    pd.DataFrame
        Cleaned, sorted DataFrame ready for strategy computation.
    """
    df = df.copy()

    # 1. Ensure datetime
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"])

    # 2. Sort chronologically
    df = df.sort_values("date").reset_index(drop=True)

    # 3. Remove duplicate timestamps
    n_before = len(df)
    df = df.drop_duplicates(subset=["date"], keep="first").reset_index(drop=True)
    n_removed = n_before - len(df)
    if n_removed > 0:
        logger.info("Removed %d duplicate timestamp(s).", n_removed)

    # 4. Cast OHLC to float64
    for col in ["open", "high", "low", "close"]:
        df[col] = df[col].astype(np.float64)

    # 5. Cast volume if present
    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce").fillna(0).astype(np.int64)

    logger.info(
        "Preprocessing complete: %d rows, %s to %s",
        len(df), df["date"].iloc[0].date(), df["date"].iloc[-1].date(),
    )
    return df


def slice_date_range(
    df: pd.DataFrame,
    start_date: str = None,
    end_date: str = None,
) -> pd.DataFrame:
    """
    Slice DataFrame to a date range.

    Parameters
    ----------
    df : pd.DataFrame
        Preprocessed OHLC data.
    start_date, end_date : str, optional
        ISO date strings.

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame.
    """
    df = df.copy()
    if start_date:
        df = df[df["date"] >= pd.Timestamp(start_date)]
    if end_date:
        df = df[df["date"] <= pd.Timestamp(end_date)]
    return df.reset_index(drop=True)

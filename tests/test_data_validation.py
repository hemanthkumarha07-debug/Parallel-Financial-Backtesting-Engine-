"""
Tests for data loading, validation, and preprocessing.
"""
import pytest
import pandas as pd
import numpy as np

from src.data.loader import load_csv, generate_synthetic_ohlc, _normalize_columns
from src.data.validator import validate_ohlc, ValidationReport
from src.data.preprocessing import preprocess_ohlc, slice_date_range


class TestDataLoader:
    """Tests for CSV loading and column normalization."""

    def test_normalize_columns_standard(self):
        df = pd.DataFrame({"Date": [1], "Open": [2], "High": [3], "Low": [4], "Close": [5]})
        result = _normalize_columns(df)
        assert "date" in result.columns
        assert "open" in result.columns

    def test_normalize_columns_variants(self):
        df = pd.DataFrame({"Timestamp": [1], "O": [2], "H": [3], "L": [4], "C": [5], "Vol": [6]})
        result = _normalize_columns(df)
        assert "date" in result.columns
        assert "volume" in result.columns

    def test_generate_synthetic_deterministic(self):
        df1 = generate_synthetic_ohlc(num_days=50, seed=123)
        df2 = generate_synthetic_ohlc(num_days=50, seed=123)
        pd.testing.assert_frame_equal(df1, df2)

    def test_generate_synthetic_valid_ohlc(self):
        df = generate_synthetic_ohlc(num_days=100, seed=42)
        assert len(df) == 100
        assert (df["low"] <= df["open"]).all()
        assert (df["low"] <= df["close"]).all()
        assert (df["high"] >= df["open"]).all()
        assert (df["high"] >= df["close"]).all()
        assert (df["low"] > 0).all()

    def test_generate_synthetic_columns(self):
        df = generate_synthetic_ohlc(num_days=10)
        assert list(df.columns) == ["date", "open", "high", "low", "close", "volume"]


class TestDataValidation:
    """Tests for OHLC data validation."""

    def test_valid_data(self, sample_ohlc_df):
        report = validate_ohlc(sample_ohlc_df)
        assert report.is_valid
        assert report.row_count == 100

    def test_missing_column(self):
        df = pd.DataFrame({"date": [1], "open": [2], "high": [3]})
        report = validate_ohlc(df)
        assert not report.is_valid
        assert len(report.missing_columns) > 0

    def test_empty_dataframe(self):
        df = pd.DataFrame({"date": [], "open": [], "high": [], "low": [], "close": []})
        report = validate_ohlc(df)
        assert not report.is_valid

    def test_duplicate_timestamps(self, sample_ohlc_df):
        df = pd.concat([sample_ohlc_df, sample_ohlc_df.iloc[:2]], ignore_index=True)
        report = validate_ohlc(df)
        assert not report.is_valid
        assert report.duplicate_timestamps > 0

    def test_missing_values(self, sample_ohlc_df):
        df = sample_ohlc_df.copy()
        df.loc[5, "close"] = np.nan
        report = validate_ohlc(df)
        assert not report.is_valid
        assert "close" in report.missing_values

    def test_negative_prices(self, sample_ohlc_df):
        df = sample_ohlc_df.copy()
        df.loc[10, "low"] = -1.0
        report = validate_ohlc(df)
        assert not report.is_valid
        assert report.negative_price_rows > 0

    def test_invalid_ohlc_relationship(self):
        df = pd.DataFrame({
            "date": pd.bdate_range("2023-01-02", periods=3),
            "open": [100.0, 101.0, 102.0],
            "high": [99.0, 102.0, 103.0],  # high < open in first row
            "low": [98.0, 100.0, 101.0],
            "close": [99.5, 101.5, 102.5],
        })
        report = validate_ohlc(df)
        assert not report.is_valid
        assert report.invalid_ohlc_rows > 0


class TestDataPreprocessing:
    """Tests for data preprocessing."""

    def test_sort_chronologically(self, sample_ohlc_df):
        df = sample_ohlc_df.iloc[::-1].reset_index(drop=True)
        result = preprocess_ohlc(df)
        assert result["date"].is_monotonic_increasing

    def test_remove_duplicates(self, sample_ohlc_df):
        df = pd.concat([sample_ohlc_df, sample_ohlc_df.iloc[:3]], ignore_index=True)
        result = preprocess_ohlc(df)
        assert len(result) == len(sample_ohlc_df)

    def test_float_casting(self, sample_ohlc_df):
        result = preprocess_ohlc(sample_ohlc_df)
        assert result["close"].dtype == np.float64

    def test_slice_date_range(self, sample_ohlc_df):
        df = preprocess_ohlc(sample_ohlc_df)
        start = str(df["date"].iloc[10].date())
        end = str(df["date"].iloc[50].date())
        sliced = slice_date_range(df, start_date=start, end_date=end)
        assert sliced["date"].iloc[0] >= pd.Timestamp(start)
        assert sliced["date"].iloc[-1] <= pd.Timestamp(end)

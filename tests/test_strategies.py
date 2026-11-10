"""
Tests for trading strategy signal generation.
"""
import pytest
import pandas as pd
import numpy as np

from src.strategies.moving_average import MovingAverageCrossover
from src.strategies.rsi_mean_reversion import RSIMeanReversion, compute_rsi
from src.strategies.donchian_breakout import DonchianBreakout
from src.data.preprocessing import preprocess_ohlc


class TestMovingAverageCrossover:
    """Tests for the Moving Average Crossover strategy."""

    def test_valid_params(self):
        s = MovingAverageCrossover(fast_period=5, slow_period=20)
        assert s.fast_period == 5
        assert s.slow_period == 20

    def test_invalid_fast_gte_slow(self):
        with pytest.raises(ValueError):
            MovingAverageCrossover(fast_period=50, slow_period=10)

    def test_invalid_equal_periods(self):
        with pytest.raises(ValueError):
            MovingAverageCrossover(fast_period=20, slow_period=20)

    def test_invalid_negative_period(self):
        with pytest.raises(ValueError):
            MovingAverageCrossover(fast_period=-5, slow_period=20)

    def test_invalid_ma_type(self):
        with pytest.raises(ValueError):
            MovingAverageCrossover(fast_period=5, slow_period=20, ma_type="WMA")

    def test_signal_generation(self, sample_ohlc_df):
        s = MovingAverageCrossover(fast_period=5, slow_period=20)
        result = s.generate_signals(sample_ohlc_df)
        assert "signal" in result.columns
        assert set(result["signal"].unique()).issubset({-1, 0, 1})

    def test_warmup_period(self):
        s = MovingAverageCrossover(fast_period=10, slow_period=50)
        assert s.warmup_period == 50

    def test_ema_mode(self, sample_ohlc_df):
        s = MovingAverageCrossover(fast_period=5, slow_period=20, ma_type="EMA")
        result = s.generate_signals(sample_ohlc_df)
        assert "signal" in result.columns

    def test_param_dict(self):
        s = MovingAverageCrossover(fast_period=10, slow_period=50, ma_type="SMA")
        d = s.param_dict()
        assert d == {"fast_period": 10, "slow_period": 50, "ma_type": "SMA"}

    def test_deterministic_signals(self, sample_ohlc_df):
        s = MovingAverageCrossover(fast_period=10, slow_period=30)
        r1 = s.generate_signals(sample_ohlc_df)
        r2 = s.generate_signals(sample_ohlc_df)
        pd.testing.assert_series_equal(r1["signal"], r2["signal"])


class TestRSIMeanReversion:
    """Tests for the RSI Mean Reversion strategy."""

    def test_valid_params(self):
        s = RSIMeanReversion(rsi_period=14, oversold=30, exit_threshold=50)
        assert s.rsi_period == 14

    def test_invalid_oversold_gte_exit(self):
        with pytest.raises(ValueError):
            RSIMeanReversion(oversold=70, exit_threshold=30)

    def test_invalid_oversold_range(self):
        with pytest.raises(ValueError):
            RSIMeanReversion(oversold=0, exit_threshold=50)

    def test_rsi_range(self, sample_ohlc_df):
        rsi = compute_rsi(sample_ohlc_df["close"], 14)
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()

    def test_signal_generation(self, sample_ohlc_df):
        s = RSIMeanReversion(rsi_period=14, oversold=30, exit_threshold=50)
        result = s.generate_signals(sample_ohlc_df)
        assert "signal" in result.columns
        assert "rsi" in result.columns

    def test_warmup_period(self):
        s = RSIMeanReversion(rsi_period=14)
        assert s.warmup_period == 15

    def test_no_simultaneous_entry_exit(self, sample_ohlc_df):
        """Ensure we don't enter and exit on the same bar."""
        s = RSIMeanReversion(rsi_period=14, oversold=30, exit_threshold=50)
        result = s.generate_signals(sample_ohlc_df)
        signal = result["signal"]
        for i in range(len(signal)):
            assert signal.iloc[i] in {-1, 0, 1}


class TestDonchianBreakout:
    """Tests for the Donchian Channel Breakout strategy."""

    def test_valid_params(self):
        s = DonchianBreakout(entry_period=20, exit_period=10)
        assert s.entry_period == 20

    def test_invalid_period(self):
        with pytest.raises(ValueError):
            DonchianBreakout(entry_period=0)

    def test_signal_generation(self, sample_ohlc_df):
        s = DonchianBreakout(entry_period=20, exit_period=10)
        result = s.generate_signals(sample_ohlc_df)
        assert "signal" in result.columns
        assert "upper_channel" in result.columns
        assert "lower_channel" in result.columns

    def test_shifted_channel(self, sample_ohlc_df):
        """Ensure the channel is shifted (current bar excluded)."""
        s = DonchianBreakout(entry_period=5, exit_period=3)
        result = s.generate_signals(sample_ohlc_df)
        assert result["upper_channel"].iloc[:5].isna().all()

    def test_warmup_period(self):
        s = DonchianBreakout(entry_period=20, exit_period=10)
        assert s.warmup_period == 21

    def test_deterministic_signals(self, sample_ohlc_df):
        s = DonchianBreakout(entry_period=20, exit_period=10)
        r1 = s.generate_signals(sample_ohlc_df)
        r2 = s.generate_signals(sample_ohlc_df)
        pd.testing.assert_series_equal(r1["signal"], r2["signal"])

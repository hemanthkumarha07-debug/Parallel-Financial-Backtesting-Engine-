# Sample Data

## `sample_ohlc.csv`

This file contains **504 rows** of synthetic daily OHLC (Open, High, Low, Close, Volume)
data generated using geometric Brownian motion.

**Date range**: 2022-01-03 to 2023-12-07  
**Starting price**: ~100.00  
**Volatility**: ~2% daily  
**Seed**: 42 (deterministic)

> ⚠️ **This is simulated data.**  
> It does NOT represent real market prices for any instrument.  
> It is provided solely for testing and first-time demonstration of the application.

## Using Your Own Data

Upload a CSV file with these columns:
- `Date` or `Timestamp` — any standard date format
- `Open`, `High`, `Low`, `Close` — numeric prices
- `Volume` (optional) — integer or float

Column names are normalized automatically (case-insensitive).

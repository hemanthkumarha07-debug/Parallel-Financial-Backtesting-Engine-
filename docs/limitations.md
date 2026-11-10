# Project Limitations, Academic Assumptions & Future Enhancements

## 1. Academic & Research Scope

The Parallel Financial Strategy Backtesting Engine (PFSBE) is designed primarily for **academic research, education, and parallel computing benchmarking**. It serves to demonstrate how multi-core computing principles (speedup, efficiency, task scheduling, Amdahl's Law) apply directly to quantitative finance workloads.

> **CRITICAL DISCLAIMER**:
> This software is not intended for live market trading. Simulated historical performance does not guarantee future profitability. Backtest results do not account for market microstructure phenomena, order book liquidity, exchange latency, or regulatory restrictions.

## 2. Modeling Limitations & Assumptions

### 2.1 Market Liquidity & Fill Probability
- **Assumption**: The model assumes that limit or market orders placed at open $O_{t+1}$ are filled in full regardless of order volume.
- **Reality**: In live markets, large orders generate market impact, moving prices adversely (slippage beyond the static percentage model) or receiving partial fills if available volume at the inside quote is insufficient.

### 2.2 Constant Spread & Slippage Model
- **Assumption**: Commissions and slippage are modeled as static percentages (e.g., $0.1\%$ commission and $0.05\%$ slippage).
- **Reality**: Market spreads widen significantly during high-volatility regimes (earnings releases, macroeconomic announcements) and illiquid trading sessions (market open/close, overnight).

### 2.3 Long-Only Position Framework
- **Assumption**: The base backtester assumes long-only equity exposures without overnight margin borrowing costs.
- **Reality**: Short-selling requires borrowing stock from a prime broker, paying borrow rates (hard-to-borrow fees), maintaining margin maintenance equity, and facing short squeeze recall risks.

### 2.4 Overfitting & Data Snooping Bias
- Evaluating thousands of parameter combinations on a single historical sample introduces **selection bias (p-hacking)**. The strategy with the highest historical Sharpe ratio is frequently overfit to historical noise rather than persistent alpha.

## 3. High-Priority Future Enhancements

1. **Walk-Forward Analysis (WFA) & Out-of-Sample (OOS) Testing**:
   - Partition data into rolling train/test splits (e.g., 2 years in-sample optimization, 6 months out-of-sample forward testing).
2. **Distributed Computing via Celery / Ray**:
   - Scale beyond single-node multi-core processing to multi-node clusters using Ray or Dask for multi-million parameter explorations.
3. **Advanced Order Types**:
   - Stop-loss, trailing stops, and profit-target limit orders evaluated on high-resolution tick or 1-minute intrabar data.
4. **Monte Carlo Resampling**:
   - Bootstrap trade return distributions to generate confidence intervals for maximum drawdown and return expectations.

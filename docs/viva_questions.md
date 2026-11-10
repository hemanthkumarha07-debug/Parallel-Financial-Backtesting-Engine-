# Viva Voce Questions & Answers: Parallel Computing & Quantitative Backtesting

This document contains expected academic viva questions and rigorous answers designed for faculty examination, defense presentations, and lab evaluations.

---

### Q1: What type of parallelism does this project implement and why?
**Answer:**  
This project implements **Task Parallelism** (specifically an **Embarrassingly Parallel / Pleasantly Parallel** pattern). Each backtest evaluation consists of an independent strategy and parameter configuration running against an immutable time-series dataset. Because each configuration executes autonomously without needing to communicate with or synchronize against other configurations, the workload can be decomposed into discrete, stateless tasks distributed across CPU cores.

---

### Q2: Why did you use `ProcessPoolExecutor` instead of `ThreadPoolExecutor` in Python?
**Answer:**  
In CPython, the **Global Interpreter Lock (GIL)** allows only one thread to execute Python bytecode at a time within a single process. Because financial backtesting (indicator computation, loop simulation, metric statistics) is heavily **CPU-bound**, multithreading would be bottlenecked by the GIL and would run entirely sequentially on a single core. `ProcessPoolExecutor` bypasses the GIL by creating independent operating system processes, each with its own Python interpreter and memory space, allowing true concurrent execution on multiple physical CPU cores.

---

### Q3: What is the difference between process creation on Windows vs. Linux, and how did you handle it?
**Answer:**  
POSIX systems (Linux/macOS) use `fork()`, which clones the parent process state via copy-on-write memory. Windows lacks `fork()` and strictly uses `spawn`, which starts a fresh Python interpreter and imports the entry-point modules from scratch.  
To ensure robust Windows compatibility:
1. Worker functions (`run_single_backtest`) are declared at top-level module scope (not inside nested functions or classes).
2. The main script is protected by `if __name__ == '__main__':` guards to prevent infinite recursive fork-bombing.
3. Task descriptors and DataFrames are serialized into picklable standard primitives.

---

### Q4: Define Speedup and Parallel Efficiency. What are their mathematical formulas?
**Answer:**  
- **Speedup ($S_p$)** measures how many times faster parallel execution is compared to the sequential baseline:
  $$S_p = \frac{T_1}{T_p}$$
  where $T_1$ is the sequential execution time, and $T_p$ is parallel execution time with $p$ processes.
- **Parallel Efficiency ($E_p$)** measures how effectively the processing power of the cores is utilized:
  $$E_p = \frac{S_p}{p} = \frac{T_1}{p \cdot T_p}$$
  Multiplying $E_p \times 100\%$ gives efficiency percentage ($100\%$ being ideal linear speedup).

---

### Q5: Why is parallel execution sometimes slower than sequential for small task sets?
**Answer:**  
This occurs due to **parallel overhead**. Parallel execution incurs fixed setup costs:
1. Process pool initialization and child interpreter startup ($T_{\text{spawn}}$).
2. Inter-process communication (IPC) and data serialization via `pickle` ($T_{\text{serialize}}$).
3. Result collection and socket/pipe coordination ($T_{\text{coordination}}$).

When the computational duration of the tasks ($T_{\text{compute}}$) is very small (e.g. 10 fast tasks), $T_{\text{overhead}} > T_{\text{compute}}$, causing Speedup $S_p < 1.0$. Parallelism becomes beneficial only past the **crossover threshold**, where $T_{\text{compute}} \gg T_{\text{overhead}}$.

---

### Q6: How does Amdahl's Law apply to this backtesting engine?
**Answer:**  
Amdahl's Law states that maximum speedup is constrained by the sequential portion of the program:
$$S_{\text{max}} = \frac{1}{(1 - f) + \frac{f}{p}}$$
In our system:
- The **sequential fraction ($1 - f$)** includes CSV loading, data validation, task grid compilation, and final UI rendering.
- The **parallel fraction ($f$)** is the actual backtest execution across the parameter space.  
As the parameter grid scales up to hundreds or thousands of configurations, $f \to 1.0$, enabling near-linear speedup.

---

### Q7: What is Look-Ahead Bias and how did you prevent it in the backtesting engine?
**Answer:**  
Look-ahead bias occurs when historical trading decisions incorporate information that would not have been available at the time of execution. For instance, executing a buy signal on bar $t$ at bar $t$'s closing price is unrealistic because the closing price is only determined at the exact moment the bar closes.  
Our engine prevents look-ahead bias by:
1. Calculating signals strictly using data up to the close of bar $t$.
2. Executing entry and exit fills on the **Open of bar $t+1$**.
3. In Donchian breakout channels, applying a `.shift(1)` rolling window so the current bar cannot form its own breakout boundary.

---

### Q8: How is the Sharpe Ratio calculated and what does it represent?
**Answer:**  
The Sharpe Ratio measures the excess return per unit of total risk (volatility).
$$S = \frac{\overline{r_t - r_f}}{\sigma(r_t - r_f)} \times \sqrt{252}$$
where $\overline{r_t - r_f}$ is the mean daily excess return over the risk-free rate, $\sigma$ is the sample standard deviation of excess returns, and $\sqrt{252}$ annualizes the metric for daily frequency. Zero volatility or insufficient observations are explicitly handled to prevent division-by-zero errors.

---

### Q9: How do you verify that sequential and parallel execution produce identical results?
**Answer:**  
We built an automated test suite (`tests/test_parallel_consistency.py`) and an integration validation tool (`test_parallel_quick.py`). Both execution modes take identical deterministic task descriptors and OHLC data. The automated test checks that the resulting financial metrics (total return, maximum drawdown, Sharpe ratio, win rate, trade count) match between sequential and parallel runs within a floating-point tolerance of $10^{-6}$.

---

### Q10: How are transaction costs and slippage accounted for?
**Answer:**  
On each trade execution:
1. **Commission**: Deducted as a fixed percentage of total trade notional value (e.g. $0.1\%$).
2. **Slippage**: Deducted as an adverse price adjustment (e.g. $0.05\%$ penalty on entry and exit prices).
This prevents optimistic performance inflation and reflects realistic net profitability.

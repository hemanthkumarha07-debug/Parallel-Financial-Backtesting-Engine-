# Parallel Computing Methodology & Performance Analysis

## 1. Parallel Computing Paradigm: Task Parallelism

The evaluation of independent parameter combinations across algorithmic trading strategies constitutes an **Embarrassingly Parallel (Pleasantly Parallel)** computational workload. 

Each backtest task:
$$T_i = \{S_{\text{id}}, \Theta_i, \mathcal{D}, \mathcal{C}\}$$
where:
- $S_{\text{id}}$ is the strategy identifier.
- $\Theta_i$ is the parameter tuple.
- $\mathcal{D}$ is the immutable OHLC financial time series.
- $\mathcal{C}$ is the backtesting cost and portfolio configuration.

Because the calculation of $T_i$ is completely independent of $T_j$ ($i \ne j$), no inter-process communication (IPC) or barrier synchronization is required during execution.

## 2. Process-Level Parallelism vs. Threading

In standard CPython, the **Global Interpreter Lock (GIL)** restricts bytecode execution to a single operating system thread at any given instant. While I/O-bound tasks benefit from multithreading, numerical financial simulations (indicator calculation, looping over price bars, trade accounting) are strictly **CPU-bound**.

PFSBE utilizes `concurrent.futures.ProcessPoolExecutor` to spawn discrete Python OS processes:
- Each worker process possesses its own distinct Python interpreter, memory space, and GIL.
- True hardware multi-core execution is achieved across all physical and logical CPU cores.

## 3. Windows vs. Linux Process Spawning (`spawn` vs `fork`)

- On POSIX systems (Linux/macOS), multiprocessing can utilize `fork()`, which creates a copy-on-write duplicate of parent memory space quickly.
- On Windows, multiprocessing strictly utilizes `spawn`. A completely fresh Python interpreter is initialized, importing the entry module from scratch.

To guarantee seamless Windows and cross-platform compatibility:
1. All worker functions (`run_single_backtest`) are declared at top-level module scope.
2. Large DataFrames are serialized into lightweight primitive structures (`list` of row dicts and column headers) to ensure fast pickling.
3. The main application is safeguarded against recursion loops.

## 4. Benchmark Performance Metrics & Mathematical Formulations

To measure parallel speedup and efficiency rigorously, PFSBE captures wall-clock execution times using high-resolution monotonic clocks (`time.perf_counter()`):

### 4.1 Speedup ($S_p$)
Speedup measures the relative runtime improvement achieved by deploying $p$ parallel worker processes against the single-process sequential baseline:

$$S_p = \frac{T_1}{T_p}$$

where:
- $T_1$ = Median sequential execution wall-clock time.
- $T_p$ = Median parallel execution wall-clock time using $p$ processes.

### 4.2 Parallel Efficiency ($E_p$)
Efficiency quantifies how effectively the system's processing cores are utilized:

$$E_p = \frac{S_p}{p} = \frac{T_1}{p \cdot T_p}$$

$$\text{Efficiency Percentage} = E_p \times 100\%$$

- **Ideal Linear Scaling**: $S_p = p$, $E_p = 1.0$ ($100\%$).
- **Sub-linear Scaling**: $S_p < p$, $E_p < 1.0$ (typical due to overheads).
- **Super-linear Scaling**: $S_p > p$, rare, typically caused by CPU cache residency effects.

### 4.3 Amdahl's Law and Real-World Overhead

Amdahl's law defines the maximum theoretical speedup of a system:

$$S_{\text{max}} = \frac{1}{(1 - f) + \frac{f}{p}}$$

where $f$ is the parallel fraction of the workload. In PFSBE:
1. **Process Creation Overhead ($T_{\text{spawn}}$)**: On Windows, spinning up a pool of 8 processes incurs ~0.5–1.0s fixed overhead.
2. **IPC & Serialization Overhead ($T_{\text{pickle}}$)**: Serializing tasks and results between parent and child processes via OS pipes.
3. **Chunk Scheduling & Task Coordination ($T_{\text{sched}}$)**: Distributing work items across available workers.

### 4.4 The Crossover Point
For small workloads (e.g. $< 20$ tasks), $T_{\text{overhead}} > T_{\text{compute}}$, causing $S_p < 1.0$ (sequential is faster).
As workload scales (e.g. $\ge 100$ tasks or large multi-year candle datasets), $T_{\text{compute}} \gg T_{\text{overhead}}$, and parallel execution yields significant, measurable speedup (e.g., $3\times$ to $12\times$ on modern multi-core machines).

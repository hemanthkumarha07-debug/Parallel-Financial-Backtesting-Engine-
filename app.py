"""
Parallel Financial Strategy Backtesting Engine — Streamlit Dashboard

Launch:
    cd parallel_financial_backtester
    streamlit run app.py
"""
import sys
import os

# Ensure the project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import multiprocessing
import time
import io

from config.settings import (
    APP_TITLE, APP_SUBTITLE, PAGE_ICON, MAX_CPU_COUNT,
    DEFAULT_INITIAL_CAPITAL, DEFAULT_COMMISSION_PCT, DEFAULT_SLIPPAGE_PCT,
    DEFAULT_POSITION_SIZE_PCT, RISK_FREE_RATE, TRADING_DAYS_PER_YEAR,
    MAX_PARAMETER_GRID_SIZE, BENCHMARK_REPEAT_RUNS,
)
from src.data.loader import load_csv, generate_synthetic_ohlc
from src.data.validator import validate_ohlc
from src.data.preprocessing import preprocess_ohlc, slice_date_range
from src.strategies.moving_average import MovingAverageCrossover
from src.strategies.rsi_mean_reversion import RSIMeanReversion
from src.strategies.donchian_breakout import DonchianBreakout
from src.backtesting.engine import run_backtest
from src.backtesting.metrics import calculate_metrics
from src.backtesting.execution import run_single_backtest, STRATEGY_REGISTRY
from src.parallel.task_manager import build_task_list, generate_parameter_grid
from src.parallel.sequential_runner import run_sequential
from src.parallel.parallel_runner import run_parallel
from src.parallel.benchmark import run_benchmark
from src.analytics.ranking import rank_results, weighted_score
from src.analytics.report_generator import (
    export_backtest_results_csv, export_trades_csv,
    export_benchmark_csv, generate_experiment_report,
)

# ══════════════════════════════════════════════════════════════════════════════
# Page configuration
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom styling ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Dark navy theme adjustments */
    .main .block-container { max-width: 1200px; padding-top: 1rem; }
    .stMetric { background: rgba(17,25,40,0.75); border: 1px solid rgba(75,180,160,0.25);
                border-radius: 8px; padding: 12px; }
    .stMetric label { color: #78909C; font-size: 0.8rem; }
    .stMetric [data-testid="stMetricValue"] { color: #4DB6AC; font-weight: 600; }
    h1, h2, h3 { color: #E0E0E0; }
    div[data-testid="stSidebar"] { background: rgba(10,15,30,0.95); }
    .disclaimer { background: rgba(255,152,0,0.1); border-left: 3px solid #FF9800;
                  padding: 10px; border-radius: 4px; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# Sidebar navigation
# ══════════════════════════════════════════════════════════════════════════════
st.sidebar.title(f"{PAGE_ICON} PFSBE")
st.sidebar.caption(APP_SUBTITLE)
page = st.sidebar.radio(
    "Navigate",
    ["Overview", "Data Explorer", "Strategy Configuration",
     "Backtest Results", "Parallel Performance Lab", "Reports & Exports"],
    label_visibility="collapsed",
)

# ══════════════════════════════════════════════════════════════════════════════
# Session state initialization
# ══════════════════════════════════════════════════════════════════════════════
if "df_raw" not in st.session_state:
    st.session_state.df_raw = None
if "df_processed" not in st.session_state:
    st.session_state.df_processed = None
if "validation_report" not in st.session_state:
    st.session_state.validation_report = None
if "backtest_results" not in st.session_state:
    st.session_state.backtest_results = None
if "benchmark_data" not in st.session_state:
    st.session_state.benchmark_data = None
if "data_source" not in st.session_state:
    st.session_state.data_source = None
if "instrument_name" not in st.session_state:
    st.session_state.instrument_name = "Unknown"
if "timeframe" not in st.session_state:
    st.session_state.timeframe = "Daily"
if "last_backtest_settings" not in st.session_state:
    st.session_state.last_backtest_settings = None
if "execution_summary" not in st.session_state:
    st.session_state.execution_summary = None


# ══════════════════════════════════════════════════════════════════════════════
# Helper functions
# ══════════════════════════════════════════════════════════════════════════════

def create_candlestick_chart(df: pd.DataFrame, title: str = "OHLC Chart") -> go.Figure:
    """Create an interactive OHLC candlestick chart."""
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25],
        vertical_spacing=0.03,
    )
    fig.add_trace(go.Candlestick(
        x=df["date"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name="OHLC",
        increasing_line_color="#26A69A", decreasing_line_color="#EF5350",
    ), row=1, col=1)
    if "volume" in df.columns:
        colors = ["#26A69A" if c >= o else "#EF5350"
                  for c, o in zip(df["close"], df["open"])]
        fig.add_trace(go.Bar(
            x=df["date"], y=df["volume"], name="Volume",
            marker_color=colors, opacity=0.5,
        ), row=2, col=1)
    fig.update_layout(
        title=title, template="plotly_dark", height=550,
        xaxis_rangeslider_visible=False,
        paper_bgcolor="rgba(10,15,30,0.9)",
        plot_bgcolor="rgba(10,15,30,0.9)",
        font=dict(color="#B0BEC5"),
    )
    return fig


def create_equity_chart(equity_df: pd.DataFrame, initial_capital: float) -> go.Figure:
    """Create an equity curve chart with drawdown."""
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, row_heights=[0.65, 0.35],
        vertical_spacing=0.05,
        subplot_titles=("Equity Curve", "Drawdown"),
    )
    fig.add_trace(go.Scatter(
        x=equity_df["date"], y=equity_df["equity"],
        mode="lines", name="Equity",
        line=dict(color="#4DB6AC", width=2),
        fill="tozeroy", fillcolor="rgba(77,182,172,0.1)",
    ), row=1, col=1)
    fig.add_hline(y=initial_capital, line_dash="dash",
                  line_color="#78909C", row=1, col=1,
                  annotation_text="Initial Capital")

    # Calculate drawdown
    eq = equity_df["equity"].values
    peak = np.maximum.accumulate(eq)
    drawdown = (eq - peak) / np.where(peak > 0, peak, 1.0) * 100
    fig.add_trace(go.Scatter(
        x=equity_df["date"], y=drawdown,
        mode="lines", name="Drawdown %",
        line=dict(color="#EF5350", width=1.5),
        fill="tozeroy", fillcolor="rgba(239,83,80,0.15)",
    ), row=2, col=1)

    fig.update_layout(
        template="plotly_dark", height=500,
        paper_bgcolor="rgba(10,15,30,0.9)",
        plot_bgcolor="rgba(10,15,30,0.9)",
        font=dict(color="#B0BEC5"),
        showlegend=False,
    )
    return fig


def create_benchmark_charts(benchmark: dict) -> tuple:
    """Create benchmark visualization charts."""
    seq_time = benchmark["sequential"]["median_time"]
    workers = sorted(benchmark["parallel"].keys())
    par_times = [benchmark["parallel"][w]["median_time"] for w in workers]
    speedups = [benchmark["parallel"][w]["speedup"] for w in workers]
    efficiencies = [benchmark["parallel"][w]["efficiency_pct"] for w in workers]

    # Chart 1: Execution Time vs Workers
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=[1] + workers, y=[seq_time] + par_times,
        mode="lines+markers", name="Measured Time",
        line=dict(color="#4DB6AC", width=2),
        marker=dict(size=10),
    ))
    fig1.add_hline(y=seq_time, line_dash="dot", line_color="#78909C",
                   annotation_text="Sequential baseline")
    fig1.update_layout(
        title="Execution Time vs Worker Count",
        xaxis_title="Workers", yaxis_title="Time (seconds)",
        template="plotly_dark", height=350,
        paper_bgcolor="rgba(10,15,30,0.9)",
        plot_bgcolor="rgba(10,15,30,0.9)",
    )

    # Chart 2: Speedup
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=[str(w) for w in workers], y=speedups,
        marker_color="#4DB6AC", name="Measured Speedup",
    ))
    fig2.add_trace(go.Scatter(
        x=[str(w) for w in workers], y=workers,
        mode="lines+markers", name="Ideal (linear)",
        line=dict(color="#FF9800", dash="dash"),
    ))
    fig2.update_layout(
        title="Speedup vs Worker Count",
        xaxis_title="Workers", yaxis_title="Speedup (x)",
        template="plotly_dark", height=350,
        paper_bgcolor="rgba(10,15,30,0.9)",
        plot_bgcolor="rgba(10,15,30,0.9)",
    )

    # Chart 3: Efficiency
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=[str(w) for w in workers], y=efficiencies,
        marker_color="#26A69A", name="Efficiency",
    ))
    fig3.add_hline(y=100, line_dash="dash", line_color="#FF9800",
                   annotation_text="100% (ideal)")
    fig3.update_layout(
        title="Parallel Efficiency vs Worker Count",
        xaxis_title="Workers", yaxis_title="Efficiency (%)",
        template="plotly_dark", height=350,
        paper_bgcolor="rgba(10,15,30,0.9)",
        plot_bgcolor="rgba(10,15,30,0.9)",
    )

    return fig1, fig2, fig3


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1: Overview
# ══════════════════════════════════════════════════════════════════════════════
if page == "Overview":
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)

    st.markdown("""
    This application demonstrates how **parallel computing** accelerates the evaluation
    of algorithmic trading strategies on historical financial data.

    **Core capabilities:**
    - Import & validate OHLC (Open, High, Low, Close) candle data
    - Configure and backtest **3 independent trading strategies**
    - Compare **sequential vs. parallel** (multiprocessing) execution
    - Measure real **speedup, efficiency, and scalability**
    - Rank strategy configurations by financial metrics
    - Export results and reports
    """)

    st.markdown('<div class="disclaimer">&#9888; <b>Disclaimer:</b> This is an educational project. '
                'Past performance does not guarantee future results. '
                'Not suitable for live trading.</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        dataset_status = "Loaded" if st.session_state.df_processed is not None else "Not loaded"
        row_count = len(st.session_state.df_processed) if st.session_state.df_processed is not None else 0
        st.metric("Dataset", dataset_status, f"{row_count} rows" if row_count else None)
    with col2:
        st.metric("Strategies", "3", "MA, RSI, Donchian")
    with col3:
        n_exp = len(st.session_state.backtest_results["results"]) if st.session_state.backtest_results else 0
        st.metric("Backtests Run", n_exp)
    with col4:
        st.metric("CPU Cores", MAX_CPU_COUNT)

    if st.session_state.benchmark_data:
        bm = st.session_state.benchmark_data
        st.subheader("Latest Benchmark Summary")
        bcol1, bcol2, bcol3 = st.columns(3)
        with bcol1:
            st.metric("Sequential Time", f"{bm['sequential']['median_time']:.3f}s")
        best_par = min(bm["parallel"].values(), key=lambda x: x["median_time"]) if bm["parallel"] else None
        if best_par:
            with bcol2:
                st.metric("Best Parallel Time",
                          f"{best_par['median_time']:.3f}s",
                          f"{best_par['num_workers']} workers")
            with bcol3:
                st.metric("Best Speedup",
                          f"{best_par['speedup']:.2f}x",
                          f"{best_par['efficiency_pct']:.0f}% efficiency")

    st.info("Use the sidebar to navigate between pages.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2: Data Explorer
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Data Explorer":
    st.title("Data Explorer")

    tab1, tab2 = st.tabs(["Upload CSV", "Use Synthetic Data"])

    with tab1:
        uploaded_file = st.file_uploader(
            "Upload OHLC CSV file", type=["csv"],
            help="Columns: Date/Timestamp, Open, High, Low, Close, Volume (optional)"
        )
        if uploaded_file is not None:
            try:
                df_raw = load_csv(uploaded_file)
                report = validate_ohlc(df_raw)
                st.session_state.df_raw = df_raw
                st.session_state.validation_report = report
                st.session_state.data_source = f"Uploaded: {uploaded_file.name}"
                if report.is_valid:
                    st.session_state.df_processed = preprocess_ohlc(df_raw)
                    st.success(f"Loaded {report.row_count} rows ({report.date_range})")
                else:
                    st.error("Validation failed. See report below.")
            except Exception as e:
                st.error(f"Error loading file: {e}")

    with tab2:
        st.markdown("Generate a **synthetic** OHLC dataset for testing. "
                     "This data is simulated and does not represent real market prices.")
        scol1, scol2, scol3 = st.columns(3)
        with scol1:
            syn_days = st.number_input("Trading days", 100, 2000, 504, step=100)
        with scol2:
            syn_vol = st.number_input("Volatility", 0.005, 0.10, 0.02, step=0.005, format="%.3f")
        with scol3:
            syn_seed = st.number_input("Random seed", 0, 9999, 42)

        if st.button("Generate Synthetic Data", type="primary"):
            df_syn = generate_synthetic_ohlc(
                num_days=syn_days, volatility=syn_vol, seed=syn_seed
            )
            report = validate_ohlc(df_syn)
            st.session_state.df_raw = df_syn
            st.session_state.validation_report = report
            st.session_state.df_processed = preprocess_ohlc(df_syn)
            st.session_state.data_source = f"Synthetic (days={syn_days}, vol={syn_vol}, seed={syn_seed})"
            st.success(f"Generated {len(df_syn)} synthetic rows.")
        elif st.session_state.df_processed is None:
            # Load default sample
            sample_path = os.path.join(PROJECT_ROOT, "data", "sample_ohlc.csv")
            if os.path.exists(sample_path):
                if st.button("Load Sample Dataset"):
                    df_sample = load_csv(sample_path)
                    report = validate_ohlc(df_sample)
                    st.session_state.df_raw = df_sample
                    st.session_state.validation_report = report
                    st.session_state.df_processed = preprocess_ohlc(df_sample)
                    st.session_state.data_source = "Sample: data/sample_ohlc.csv (SYNTHETIC)"
                    st.success(f"Loaded sample data: {len(df_sample)} rows.")

    # ── Metadata ───────────────────────────────────────────────────────
    mcol1, mcol2 = st.columns(2)
    with mcol1:
        st.session_state.instrument_name = st.text_input(
            "Instrument name", value=st.session_state.instrument_name
        )
    with mcol2:
        st.session_state.timeframe = st.selectbox(
            "Timeframe", ["1m", "5m", "15m", "1h", "4h", "Daily", "Weekly"],
            index=5,
        )

    # ── Display loaded data ────────────────────────────────────────────
    if st.session_state.df_processed is not None:
        df = st.session_state.df_processed
        st.subheader("Dataset Preview")
        st.caption(f"Source: {st.session_state.data_source}")

        pcol1, pcol2, pcol3, pcol4 = st.columns(4)
        with pcol1:
            st.metric("Rows", len(df))
        with pcol2:
            st.metric("Date Range", f"{df['date'].iloc[0].date()} to {df['date'].iloc[-1].date()}")
        with pcol3:
            st.metric("Price Range", f"{df['close'].min():.2f} - {df['close'].max():.2f}")
        with pcol4:
            missing = df[["open","high","low","close"]].isna().sum().sum()
            st.metric("Missing OHLC", missing)

        st.dataframe(df.head(20), use_container_width=True)
        st.plotly_chart(create_candlestick_chart(df, f"{st.session_state.instrument_name} — {st.session_state.timeframe}"),
                        use_container_width=True)

        # Validation report
        report = st.session_state.validation_report
        if report:
            with st.expander("Data Quality Report"):
                st.write(f"**Status:** {'VALID' if report.is_valid else 'INVALID'}")
                st.write(f"**Rows:** {report.row_count}")
                st.write(f"**Date range:** {report.date_range}")
                st.write(f"**Duplicate timestamps:** {report.duplicate_timestamps}")
                st.write(f"**Invalid OHLC rows:** {report.invalid_ohlc_rows}")
                st.write(f"**Time gaps:** {report.time_gaps}")
                if report.errors:
                    st.error("Errors: " + "; ".join(report.errors))
                if report.warnings:
                    st.warning("Warnings: " + "; ".join(report.warnings))


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3: Strategy Configuration
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Strategy Configuration":
    st.title("Strategy Configuration & Execution")

    if st.session_state.df_processed is None:
        st.warning("Please load data first in the Data Explorer page.")
        st.stop()

    df = st.session_state.df_processed

    # ── Backtest settings ──────────────────────────────────────────────
    st.subheader("Backtest Settings")
    scol1, scol2, scol3, scol4 = st.columns(4)
    with scol1:
        initial_capital = st.number_input(
            "Initial Capital ($)", 1000.0, 10_000_000.0, DEFAULT_INITIAL_CAPITAL, step=10000.0
        )
    with scol2:
        commission_pct = st.number_input(
            "Commission (%)", 0.0, 5.0, DEFAULT_COMMISSION_PCT, step=0.01, format="%.2f"
        )
    with scol3:
        slippage_pct = st.number_input(
            "Slippage (%)", 0.0, 5.0, DEFAULT_SLIPPAGE_PCT, step=0.01, format="%.2f"
        )
    with scol4:
        position_size_pct = st.number_input(
            "Position Size (%)", 10.0, 100.0, DEFAULT_POSITION_SIZE_PCT, step=10.0
        )

    backtest_settings = {
        "initial_capital": initial_capital,
        "commission_pct": commission_pct,
        "slippage_pct": slippage_pct,
        "position_size_pct": position_size_pct,
        "risk_free_rate": RISK_FREE_RATE,
        "trading_days_per_year": TRADING_DAYS_PER_YEAR,
    }

    st.divider()

    # ── Strategy parameter grids ───────────────────────────────────────
    st.subheader("Strategy Parameter Grids")
    st.caption("Configure parameter ranges for each strategy. Invalid combinations are automatically discarded.")

    strategy_configs = []

    # Moving Average Crossover
    with st.expander("Strategy A: Moving Average Crossover", expanded=True):
        ma_enabled = st.checkbox("Enable", value=True, key="ma_enabled")
        if ma_enabled:
            mac1, mac2, mac3 = st.columns(3)
            with mac1:
                ma_fast = st.text_input("Fast periods (comma-sep)", "5,10,15,20", key="ma_fast")
            with mac2:
                ma_slow = st.text_input("Slow periods (comma-sep)", "30,40,50,60", key="ma_slow")
            with mac3:
                ma_type = st.selectbox("MA type", ["SMA", "EMA"], key="ma_type")
            try:
                fast_vals = [int(x.strip()) for x in ma_fast.split(",")]
                slow_vals = [int(x.strip()) for x in ma_slow.split(",")]
                param_ranges = {"fast_period": fast_vals, "slow_period": slow_vals, "ma_type": [ma_type]}
                n_valid = len(generate_parameter_grid("MovingAverageCrossover", param_ranges))
                st.info(f"{n_valid} valid combinations")
                strategy_configs.append(("MovingAverageCrossover", param_ranges))
            except Exception as e:
                st.error(f"Invalid parameters: {e}")

    # RSI Mean Reversion
    with st.expander("Strategy B: RSI Mean Reversion", expanded=True):
        rsi_enabled = st.checkbox("Enable", value=True, key="rsi_enabled")
        if rsi_enabled:
            rc1, rc2, rc3 = st.columns(3)
            with rc1:
                rsi_periods = st.text_input("RSI periods (comma-sep)", "10,14,20", key="rsi_per")
            with rc2:
                rsi_os = st.text_input("Oversold thresholds", "25,30", key="rsi_os")
            with rc3:
                rsi_exit = st.text_input("Exit thresholds", "50,60", key="rsi_exit")
            try:
                rsi_p = [int(x.strip()) for x in rsi_periods.split(",")]
                os_v = [float(x.strip()) for x in rsi_os.split(",")]
                ex_v = [float(x.strip()) for x in rsi_exit.split(",")]
                param_ranges = {"rsi_period": rsi_p, "oversold": os_v, "exit_threshold": ex_v}
                n_valid = len(generate_parameter_grid("RSIMeanReversion", param_ranges))
                st.info(f"{n_valid} valid combinations")
                strategy_configs.append(("RSIMeanReversion", param_ranges))
            except Exception as e:
                st.error(f"Invalid parameters: {e}")

    # Donchian Breakout
    with st.expander("Strategy C: Donchian Channel Breakout", expanded=True):
        don_enabled = st.checkbox("Enable", value=True, key="don_enabled")
        if don_enabled:
            dc1, dc2 = st.columns(2)
            with dc1:
                don_entry = st.text_input("Entry periods (comma-sep)", "15,20,25,30", key="don_entry")
            with dc2:
                don_exit = st.text_input("Exit periods (comma-sep)", "5,10,15", key="don_exit")
            try:
                ep = [int(x.strip()) for x in don_entry.split(",")]
                xp = [int(x.strip()) for x in don_exit.split(",")]
                param_ranges = {"entry_period": ep, "exit_period": xp}
                n_valid = len(generate_parameter_grid("DonchianBreakout", param_ranges))
                st.info(f"{n_valid} valid combinations")
                strategy_configs.append(("DonchianBreakout", param_ranges))
            except Exception as e:
                st.error(f"Invalid parameters: {e}")

    st.divider()

    # ── Execution controls ─────────────────────────────────────────────
    st.subheader("Execution")
    ecol1, ecol2, ecol3 = st.columns(3)
    with ecol1:
        exec_mode = st.radio("Execution mode", ["Sequential", "Parallel", "Both (Benchmark)"])
    with ecol2:
        num_workers = st.slider("Worker processes", 1, MAX_CPU_COUNT, min(4, MAX_CPU_COUNT))
    with ecol3:
        max_tasks = st.number_input("Max tasks", 10, MAX_PARAMETER_GRID_SIZE, 500, step=50)

    # Preview
    if strategy_configs:
        preview_tasks = build_task_list(strategy_configs, backtest_settings, max_tasks=max_tasks)
        st.info(f"**{len(preview_tasks)}** backtest tasks will be generated.")
    else:
        st.warning("Enable at least one strategy.")
        preview_tasks = []

    # Run button
    if st.button("Run Backtests", type="primary", disabled=len(preview_tasks) == 0):
        tasks = preview_tasks
        df_records = df.to_dict("records")
        df_columns = list(df.columns)

        progress_bar = st.progress(0, text="Preparing...")

        if exec_mode == "Sequential":
            progress_bar.progress(10, text="Running sequential backtests...")
            result = run_sequential(tasks, df_records, df_columns)
            st.session_state.backtest_results = result
            st.session_state.execution_summary = {
                "mode": "sequential", "tasks": len(tasks),
                "time": result["wall_time"], "workers": 1,
            }

        elif exec_mode == "Parallel":
            progress_bar.progress(10, text=f"Running parallel backtests ({num_workers} workers)...")
            result = run_parallel(tasks, df_records, df_columns, num_workers=num_workers)
            st.session_state.backtest_results = result
            st.session_state.execution_summary = {
                "mode": "parallel", "tasks": len(tasks),
                "time": result["wall_time"], "workers": num_workers,
            }

        else:  # Both (Benchmark)
            progress_bar.progress(5, text="Running sequential baseline...")
            seq_result = run_sequential(tasks, df_records, df_columns)
            progress_bar.progress(40, text=f"Running parallel ({num_workers} workers)...")
            par_result = run_parallel(tasks, df_records, df_columns, num_workers=num_workers)

            # Build benchmark data
            speedup = seq_result["wall_time"] / par_result["wall_time"] if par_result["wall_time"] > 0 else 0
            efficiency = speedup / num_workers if num_workers > 0 else 0
            st.session_state.benchmark_data = {
                "sequential": {
                    "wall_times": [seq_result["wall_time"]],
                    "median_time": seq_result["wall_time"],
                    "completed": seq_result["completed"],
                    "failed": seq_result["failed"],
                },
                "parallel": {
                    num_workers: {
                        "wall_times": [par_result["wall_time"]],
                        "median_time": par_result["wall_time"],
                        "speedup": round(speedup, 4),
                        "efficiency": round(efficiency, 4),
                        "efficiency_pct": round(efficiency * 100, 2),
                        "completed": par_result["completed"],
                        "failed": par_result["failed"],
                        "num_workers": num_workers,
                    }
                },
                "num_tasks": len(tasks),
                "repeat": 1,
            }
            st.session_state.backtest_results = par_result
            st.session_state.execution_summary = {
                "mode": "benchmark", "tasks": len(tasks),
                "seq_time": seq_result["wall_time"],
                "par_time": par_result["wall_time"],
                "speedup": speedup, "workers": num_workers,
            }

        st.session_state.last_backtest_settings = backtest_settings
        progress_bar.progress(100, text="Complete!")
        st.success("Backtests complete! Go to **Backtest Results** to view.")
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4: Backtest Results
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Backtest Results":
    st.title("Backtest Results")

    if st.session_state.backtest_results is None:
        st.info("No backtest results yet. Run backtests from the Strategy Configuration page.")
        st.stop()

    results = st.session_state.backtest_results["results"]
    successful = [r for r in results if r["status"] == "success"]

    if not successful:
        st.error("No successful backtests to display.")
        st.stop()

    # ── Summary ────────────────────────────────────────────────────────
    summary = st.session_state.execution_summary
    if summary:
        st.caption(f"Mode: {summary['mode']} | Tasks: {summary['tasks']}")

    # ── Ranking table ──────────────────────────────────────────────────
    st.subheader("Strategy Rankings")
    sort_col = st.selectbox(
        "Rank by",
        ["sharpe_ratio", "total_return", "max_drawdown", "win_rate", "profit_factor"],
    )
    ascending = sort_col == "max_drawdown"

    ranked_df = rank_results(successful, sort_by=sort_col, ascending=not ascending if sort_col == "max_drawdown" else ascending)
    if not ranked_df.empty:
        st.dataframe(
            ranked_df.style.format({
                "total_return": "{:.2f}%",
                "max_drawdown": "{:.2f}%",
                "sharpe_ratio": "{:.3f}",
                "win_rate": "{:.1f}%",
                "profit_factor": "{:.2f}",
                "execution_time": "{:.4f}s",
                "final_equity": "${:,.0f}",
                "total_costs": "${:,.2f}",
            }),
            use_container_width=True,
        )

    st.markdown('<div class="disclaimer">&#9888; Highest historical return does not imply '
                'best future performance. These results are from backtesting only.</div>',
                unsafe_allow_html=True)

    st.divider()

    # ── Detailed view for selected strategy ────────────────────────────
    st.subheader("Detailed Strategy View")
    strategy_labels = [
        f"{r['strategy_name']} {r['params']}" for r in successful
    ]
    if strategy_labels:
        selected_idx = st.selectbox("Select configuration", range(len(strategy_labels)),
                                     format_func=lambda i: strategy_labels[i])
        r = successful[selected_idx]
        metrics = r["metrics"]

        # Metric cards
        mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
        with mcol1:
            st.metric("Total Return", f"{metrics.get('total_return', 0):.2f}%")
        with mcol2:
            st.metric("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.3f}")
        with mcol3:
            st.metric("Max Drawdown", f"{metrics.get('max_drawdown', 0):.2f}%")
        with mcol4:
            st.metric("Trades", metrics.get("num_trades", 0))
        with mcol5:
            st.metric("Win Rate", f"{metrics.get('win_rate', 0):.1f}%")

        mcol6, mcol7, mcol8, mcol9 = st.columns(4)
        with mcol6:
            st.metric("Profit Factor", f"{metrics.get('profit_factor', 0):.2f}")
        with mcol7:
            st.metric("Avg Hold Period", f"{metrics.get('avg_holding_period', 0):.1f} bars")
        with mcol8:
            st.metric("Total Costs", f"${metrics.get('total_costs', 0):,.2f}")
        with mcol9:
            st.metric("Final Equity", f"${metrics.get('final_equity', 0):,.0f}")

        # Equity curve
        if r.get("equity_curve"):
            eq_df = pd.DataFrame(r["equity_curve"])
            eq_df["date"] = pd.to_datetime(eq_df["date"])
            ic = st.session_state.last_backtest_settings.get("initial_capital", 100000) if st.session_state.last_backtest_settings else 100000
            st.plotly_chart(create_equity_chart(eq_df, ic), use_container_width=True)

        # Trade history
        if r.get("trades"):
            with st.expander("Trade History"):
                trades_df = pd.DataFrame(r["trades"])
                st.dataframe(trades_df, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5: Parallel Performance Lab
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Parallel Performance Lab":
    st.title("Parallel Performance Lab")
    st.caption("Measure and visualize sequential vs. parallel execution performance.")

    if st.session_state.df_processed is None:
        st.warning("Please load data first in the Data Explorer page.")
        st.stop()

    df = st.session_state.df_processed

    st.subheader("Benchmark Configuration")
    st.markdown("""
    This lab runs the **same workload** sequentially and in parallel with different
    worker counts, measuring actual wall-clock time. Speedup and efficiency are
    calculated from these real measurements.

    > **Note:** For small workloads, parallel execution may be slower than sequential
    > due to process startup, data serialization, and coordination overhead.
    > Use larger parameter grids (50+ tasks) to observe meaningful speedup.
    """)

    bcol1, bcol2, bcol3 = st.columns(3)
    with bcol1:
        worker_list_str = st.text_input(
            "Worker counts (comma-sep)",
            ",".join(str(w) for w in [2, 4, 8] if w <= MAX_CPU_COUNT),
        )
    with bcol2:
        bench_repeat = st.number_input("Repeat runs", 1, 5, 1)
    with bcol3:
        bench_warmup = st.number_input("Warmup runs", 0, 3, 0)

    # Task configuration for benchmark
    st.subheader("Workload Configuration")
    st.caption("Configure a parameter grid specifically for benchmarking. Larger grids show clearer speedup.")

    grid_cols = st.columns(3)
    with grid_cols[0]:
        bench_ma_fast = st.text_input("MA fast periods", "5,10,15,20", key="b_fast")
        bench_ma_slow = st.text_input("MA slow periods", "30,40,50,60", key="b_slow")
    with grid_cols[1]:
        bench_rsi_per = st.text_input("RSI periods", "10,14,20", key="b_rsi")
        bench_rsi_os = st.text_input("RSI oversold", "20,25,30,35", key="b_os")
    with grid_cols[2]:
        bench_don_entry = st.text_input("Donchian entry", "10,15,20,25,30", key="b_de")
        bench_don_exit = st.text_input("Donchian exit", "5,10,15", key="b_dx")

    backtest_settings = {
        "initial_capital": DEFAULT_INITIAL_CAPITAL,
        "commission_pct": DEFAULT_COMMISSION_PCT,
        "slippage_pct": DEFAULT_SLIPPAGE_PCT,
        "position_size_pct": DEFAULT_POSITION_SIZE_PCT,
        "risk_free_rate": RISK_FREE_RATE,
        "trading_days_per_year": TRADING_DAYS_PER_YEAR,
    }

    try:
        strategy_configs = [
            ("MovingAverageCrossover", {
                "fast_period": [int(x.strip()) for x in bench_ma_fast.split(",")],
                "slow_period": [int(x.strip()) for x in bench_ma_slow.split(",")],
                "ma_type": ["SMA"],
            }),
            ("RSIMeanReversion", {
                "rsi_period": [int(x.strip()) for x in bench_rsi_per.split(",")],
                "oversold": [float(x.strip()) for x in bench_rsi_os.split(",")],
                "exit_threshold": [50.0],
            }),
            ("DonchianBreakout", {
                "entry_period": [int(x.strip()) for x in bench_don_entry.split(",")],
                "exit_period": [int(x.strip()) for x in bench_don_exit.split(",")],
            }),
        ]
        bench_tasks = build_task_list(strategy_configs, backtest_settings, max_tasks=MAX_PARAMETER_GRID_SIZE)
        st.info(f"**{len(bench_tasks)}** benchmark tasks generated.")
    except Exception as e:
        st.error(f"Error building task list: {e}")
        bench_tasks = []

    if st.button("Run Benchmark", type="primary", disabled=len(bench_tasks) == 0):
        try:
            worker_counts = [int(x.strip()) for x in worker_list_str.split(",")]
            worker_counts = [w for w in worker_counts if 1 < w <= MAX_CPU_COUNT]
        except:
            worker_counts = [2, 4]

        df_records = df.to_dict("records")
        df_columns = list(df.columns)

        with st.spinner(f"Running benchmark: {len(bench_tasks)} tasks, "
                        f"workers={worker_counts}, repeat={bench_repeat}..."):
            bm = run_benchmark(
                bench_tasks, df_records, df_columns,
                worker_counts=worker_counts,
                repeat=bench_repeat,
                warmup=bench_warmup,
            )
            st.session_state.benchmark_data = bm

        st.success("Benchmark complete!")
        st.rerun()

    # ── Display benchmark results ──────────────────────────────────────
    if st.session_state.benchmark_data:
        bm = st.session_state.benchmark_data

        st.divider()
        st.subheader("Benchmark Results")
        st.caption(f"Tasks: {bm['num_tasks']} | Repeats: {bm['repeat']}")

        # Summary metrics
        rcol1, rcol2, rcol3 = st.columns(3)
        with rcol1:
            st.metric("Sequential (median)", f"{bm['sequential']['median_time']:.4f} s")

        best_par = min(bm["parallel"].values(), key=lambda x: x["median_time"]) if bm["parallel"] else None
        if best_par:
            with rcol2:
                st.metric(f"Parallel ({best_par['num_workers']}w)", f"{best_par['median_time']:.4f} s")
            with rcol3:
                st.metric("Best Speedup", f"{best_par['speedup']:.2f}x",
                          f"Efficiency: {best_par['efficiency_pct']:.1f}%")

        # Detailed table
        rows = [{"Workers": 1, "Median Time (s)": bm["sequential"]["median_time"],
                 "Speedup": 1.0, "Efficiency (%)": 100.0,
                 "Completed": bm["sequential"]["completed"],
                 "Failed": bm["sequential"]["failed"]}]
        for nw in sorted(bm["parallel"].keys()):
            d = bm["parallel"][nw]
            rows.append({"Workers": nw, "Median Time (s)": d["median_time"],
                         "Speedup": d["speedup"], "Efficiency (%)": d["efficiency_pct"],
                         "Completed": d["completed"], "Failed": d["failed"]})
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        # Charts
        fig1, fig2, fig3 = create_benchmark_charts(bm)
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.plotly_chart(fig1, use_container_width=True)
            st.plotly_chart(fig3, use_container_width=True)
        with chart_col2:
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Interpreting the Results")
        st.markdown("""
        **Speedup** = Sequential Time / Parallel Time

        **Efficiency** = Speedup / Number of Workers x 100%

        **Why parallel might be slower for small workloads:**
        - Process startup overhead (especially on Windows using 'spawn')
        - Data serialization (pickling DataFrames for each worker)
        - Task scheduling and result collection overhead
        - These fixed costs dominate when individual tasks are very fast

        **When parallel shines:**
        - Many independent tasks (50+)
        - Each task takes significant time (complex strategies, large datasets)
        - The dataset is large enough that computation dominates overhead
        """)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6: Reports & Exports
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Reports & Exports":
    st.title("Reports & Exports")

    if st.session_state.backtest_results is None and st.session_state.benchmark_data is None:
        st.info("No results to export. Run backtests or benchmarks first.")
        st.stop()

    results = st.session_state.backtest_results
    benchmark = st.session_state.benchmark_data

    st.subheader("Download Results")

    dcol1, dcol2 = st.columns(2)

    with dcol1:
        # Backtest results CSV
        if results and results.get("results"):
            csv_data = export_backtest_results_csv(results["results"])
            if csv_data:
                st.download_button(
                    "Download Backtest Results (CSV)",
                    data=csv_data,
                    file_name="backtest_results.csv",
                    mime="text/csv",
                )

            # Trade history CSV
            trades_csv = export_trades_csv(results["results"])
            if trades_csv:
                st.download_button(
                    "Download Trade History (CSV)",
                    data=trades_csv,
                    file_name="trade_history.csv",
                    mime="text/csv",
                )

    with dcol2:
        # Benchmark CSV
        if benchmark:
            bm_csv = export_benchmark_csv(benchmark)
            if bm_csv:
                st.download_button(
                    "Download Benchmark Results (CSV)",
                    data=bm_csv,
                    file_name="benchmark_results.csv",
                    mime="text/csv",
                )

    st.divider()

    # Experiment report
    st.subheader("Experiment Report")
    if results and benchmark:
        successful = [r for r in results["results"] if r["status"] == "success"]
        ranked = rank_results(successful, sort_by="sharpe_ratio")
        dataset_info = {
            "Source": st.session_state.data_source or "N/A",
            "Instrument": st.session_state.instrument_name,
            "Timeframe": st.session_state.timeframe,
            "Rows": len(st.session_state.df_processed) if st.session_state.df_processed is not None else "N/A",
        }
        report_text = generate_experiment_report(
            benchmark, ranked, dataset_info,
            st.session_state.last_backtest_settings,
        )
        st.markdown(report_text)
        st.download_button(
            "Download Report (Markdown)",
            data=report_text,
            file_name="experiment_report.md",
            mime="text/markdown",
        )
    elif results:
        st.info("Run a benchmark (Both mode) to generate a complete report.")
    else:
        st.info("Run backtests first to generate reports.")

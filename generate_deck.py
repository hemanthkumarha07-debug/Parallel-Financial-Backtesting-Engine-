"""
Professional PowerPoint Presentation Generator for PFSBE
Generates a 16:9 widescreen presentation with dark navy/teal aesthetic,
metric cards, benchmark tables, and detailed speaker notes on every slide.
"""
import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_deck(output_path="PFSBE_Final_Presentation.pptx"):
    prs = Presentation()
    # 16:9 Widescreen dimensions
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]  # Blank slide

    # Color Palette Constants
    BG_DARK = RGBColor(11, 19, 43)        # #0B132B Deep Navy
    CARD_BG = RGBColor(20, 32, 60)        # #14203C Card Navy
    CARD_BORDER = RGBColor(45, 212, 191)  # #2DD4BF Teal Accent
    ACCENT_TEAL = RGBColor(45, 212, 191)  # #2DD4BF Emerald/Teal
    ACCENT_CYAN = RGBColor(56, 189, 248)  # #38BDF8 Cyan
    ACCENT_AMBER = RGBColor(245, 158, 11) # #F59E0B Amber
    TEXT_WHITE = RGBColor(248, 250, 252)  # #F8FAFC Crisp White
    TEXT_MUTED = RGBColor(148, 163, 184)  # #94A3B8 Slate Gray
    TEXT_BODY = RGBColor(226, 232, 240)   # #E2E8F0 Soft White

    def add_slide_background(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_DARK
        bg.line.color.rgb = BG_DARK
        return bg

    def add_header(slide, category, title):
        add_slide_background(slide)
        
        # Category tracker pill
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = ACCENT_TEAL

        # Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.7))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title
        p_title.font.size = Pt(26)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_WHITE

    def add_card(slide, left, top, width, height, title, items, border_color=CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = border_color
        card.line.width = Pt(1.5)

        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.25)
        tf.margin_right = Inches(0.25)
        tf.margin_top = Inches(0.25)
        tf.margin_bottom = Inches(0.25)

        if title:
            p_t = tf.paragraphs[0]
            p_t.text = title
            p_t.font.size = Pt(16)
            p_t.font.bold = True
            p_t.font.color.rgb = ACCENT_CYAN
            p_t.space_after = Pt(10)

        for i, item in enumerate(items):
            p = tf.add_paragraph() if (title or i > 0) else tf.paragraphs[0]
            p.text = f"• {item}"
            p.font.size = Pt(13)
            p.font.color.rgb = TEXT_BODY
            p.space_after = Pt(6)

        return card

    # =========================================================================
    # SLIDE 1: TITLE SLIDE
    # =========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    add_slide_background(slide1)

    # Accent decorative bar
    bar = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(1.5), Inches(0.15), Inches(4.2))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT_TEAL
    bar.line.fill.background()

    tb = slide1.shapes.add_textbox(Inches(1.6), Inches(1.4), Inches(10.5), Inches(4.5))
    tf1 = tb.text_frame
    tf1.word_wrap = True

    p = tf1.paragraphs[0]
    p.text = "ACADEMIC & TECHNICAL CAPSTONE PROJECT"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = ACCENT_TEAL
    p.space_after = Pt(14)

    p2 = tf1.add_paragraph()
    p2.text = "Parallel Financial Strategy\nBacktesting Engine (PFSBE)"
    p2.font.size = Pt(36)
    p2.font.bold = True
    p2.font.color.rgb = TEXT_WHITE
    p2.space_after = Pt(16)

    p3 = tf1.add_paragraph()
    p3.text = "Accelerating Algorithmic Strategy Evaluation via Multi-Process Task Parallelism"
    p3.font.size = Pt(18)
    p3.font.color.rgb = ACCENT_CYAN
    p3.space_after = Pt(28)

    p4 = tf1.add_paragraph()
    p4.text = "Domain: High-Performance Parallel Computing & Computational Quantitative Finance\nTech Stack: Python 3.11 • ProcessPoolExecutor • Streamlit • Plotly • Pytest (72 Tests Passed)"
    p4.font.size = Pt(13)
    p4.font.color.rgb = TEXT_MUTED

    slide1.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 1 - Title):\n"
        "Good morning/afternoon respected examiners and panel members. Today I am presenting the "
        "Parallel Financial Strategy Backtesting Engine (PFSBE). This project demonstrates the practical "
        "application of high-performance parallel computing to quantitative finance, addressing the severe "
        "computational bottlenecks of algorithmic strategy evaluation."
    )

    # =========================================================================
    # SLIDE 2: EXECUTIVE SUMMARY & MOTIVATION
    # =========================================================================
    slide2 = prs.slides.add_slide(blank_layout)
    add_header(slide2, "Introduction & Motivation", "The Computational Imperative in Quantitative Finance")

    add_card(slide2, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.0),
             "The Quantitative Research Bottleneck", [
                 "Algorithmic strategy optimization evaluates Cartesian parameter grids (thousands of permutations).",
                 "Multi-year high-resolution OHLC data scales time complexity to O(M × N).",
                 "Sequential single-core execution takes hours to days for parameter sweeps.",
                 "Fast backtesting turnaround is critical for quantitative research cycles.",
                 "Need: Scalable parallelization directly integrated into financial workflows."
             ])

    add_card(slide2, Inches(6.8), Inches(1.7), Inches(5.6), Inches(5.0),
             "The PFSBE Solution", [
                 "Bypasses CPython's Global Interpreter Lock (GIL) via process-level task parallelism.",
                 "Implements 3 production strategies: MA Crossover, RSI Reversion, Donchian Breakout.",
                 "Guarantees Zero Look-Ahead Bias with realistic slippage and commission models.",
                 "Measures real wall-clock Speedup (Sp) and Parallel Efficiency (Ep) reproducibly.",
                 "Provides an interactive dark-navy Streamlit dashboard with full audit exports."
             ])

    slide2.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 2 - Executive Summary):\n"
        "In algorithmic trading, parameter optimization requires evaluating large combinations of indicator settings. "
        "Running this sequentially across historical candles scales linearly with data length and grid size, causing "
        "research bottlenecks. PFSBE addresses this by deploying a custom multi-process parallel engine."
    )

    # =========================================================================
    # SLIDE 3: PROBLEM FORMULATION & CPYTHON GIL
    # =========================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    add_header(slide3, "Theoretical Context", "The Python Concurrency Bottleneck: Why Threads Fail")

    add_card(slide3, Inches(0.8), Inches(1.7), Inches(3.7), Inches(5.0),
             "CPython GIL Constraint", [
                 "The Global Interpreter Lock allows only one native OS thread to run bytecode at once.",
                 "Threading works well for I/O-bound tasks (network, disk).",
                 "Backtesting is strictly CPU-bound: mathematical loops, indicators, ledger updates.",
                 "Multi-threading actually slows down CPU tasks due to GIL contention overhead."
             ])

    add_card(slide3, Inches(4.8), Inches(1.7), Inches(3.7), Inches(5.0),
             "Multi-Process Architecture", [
                 "PFSBE uses concurrent.futures.ProcessPoolExecutor.",
                 "Each worker process gets its own distinct Python interpreter and memory heap.",
                 "Completely bypasses the GIL across all physical CPU cores.",
                 "Achieves true hardware parallelism on modern multi-core CPUs."
             ])

    add_card(slide3, Inches(8.8), Inches(1.7), Inches(3.7), Inches(5.0),
             "Cross-Platform Spawning", [
                 "POSIX (Linux/macOS) uses fork() for fast memory replication.",
                 "Windows strictly uses spawn, creating processes from scratch.",
                 "Engine engineered with module-scoped workers to eliminate pickling errors.",
                 "Zero IPC deadlocks and 100% Windows/Linux cross-compatibility."
             ])

    slide3.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 3 - Python Concurrency):\n"
        "A common misconception is that adding threads speeds up Python code. Because backtesting is CPU-bound, "
        "the GIL prevents multi-core utilization. ProcessPoolExecutor spawns distinct OS processes with private "
        "heaps, bypassing the GIL completely. We also solved the Windows 'spawn' compatibility requirement."
    )

    # =========================================================================
    # SLIDE 4: SYSTEM ARCHITECTURE
    # =========================================================================
    slide4 = prs.slides.add_slide(blank_layout)
    add_header(slide4, "System Engineering", "Decoupled 5-Tier Architecture")

    tiers = [
        ("Tier 1: Presentation (Streamlit)", "Interactive 6-page quantitative dashboard with Plotly charts, parameter sliders, and audit reports."),
        ("Tier 2: Analytics & Reporting", "Multi-criteria ranking (Sharpe, Return, Drawdown, Weighted Score), CSV exporters, and Markdown report generator."),
        ("Tier 3: Parallel Task Manager", "Cartesian grid generation, parameter validation, task serialization, and ProcessPoolExecutor master-worker scheduling."),
        ("Tier 4: Backtesting Simulator", "Zero look-ahead bar-by-bar execution, cash & share ledger, cost deduction, and mark-to-market equity curves."),
        ("Tier 5: Data Ingestion & Quality", "CSV loader, alias column normalizer, 7-point validation suite, and Geometric Brownian Motion synthetic data generator.")
    ]

    for idx, (title, desc) in enumerate(tiers):
        c = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6 + idx * 1.05), Inches(11.7), Inches(0.9))
        c.fill.solid()
        c.fill.fore_color.rgb = CARD_BG
        c.line.color.rgb = CARD_BORDER if idx == 2 else RGBColor(51, 65, 85)
        c.line.width = Pt(1.5)
        tf = c.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.3)
        tf.margin_top = Inches(0.12)
        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(14)
        p1.font.bold = True
        p1.font.color.rgb = ACCENT_TEAL if idx == 2 else TEXT_WHITE
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = TEXT_MUTED

    slide4.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 4 - Architecture):\n"
        "Here is the 5-tier architecture. Notice the clean decoupling between the user interface, analytics, "
        "parallel task coordination, backtesting engine, and data ingestion. This modularity enables independent "
        "testing and seamless scaling."
    )

    # =========================================================================
    # SLIDE 5: DATA INGESTION & 7-POINT VALIDATION
    # =========================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    add_header(slide5, "Data Integrity", "Automated 7-Point Data Quality Validation Suite")

    add_card(slide5, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.0),
             "Ingestion & Preprocessing Pipeline", [
                 "Column Name Normalization: Resolves 15+ column variations (e.g. Timestamp, Vol, Adj Close).",
                 "Chronological Sorting: Ensures strict monotonic datetime order.",
                 "Duplicate Pruning: Detects and removes duplicated timestamp rows.",
                 "High-Precision Casting: Standardizes prices to float64 and volume to int64.",
                 "Deterministic Synthetic Generator: Built-in Geometric Brownian Motion (GBM) engine for offline demos."
             ])

    add_card(slide5, Inches(6.8), Inches(1.7), Inches(5.6), Inches(5.0),
             "The 7 Automated Integrity Checks", [
                 "1. Required Columns: Verifies presence of Date, Open, High, Low, Close.",
                 "2. DateTime Parseability: Enforces valid ISO datetime conversion.",
                 "3. Duplicate Detection: Flags repeated timestamps in market series.",
                 "4. Null / NaN Detection: Rejects missing price observations.",
                 "5. Strict Price Positivity: Enforces P > 0 across all price vectors.",
                 "6. OHLC Geometry: Asserts Low <= min(Open, Close) and High >= max(Open, Close).",
                 "7. Time Gap Warning: Identifies interval gaps (>3x median) without fabricating candles."
             ])

    slide5.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 5 - Data Ingestion):\n"
        "Financial data in the wild is notoriously dirty. Before running a single backtest, our ingestion pipeline "
        "runs seven mathematical checks. It catches inverted candles, duplicate rows, negative prices, and anomalous gaps, "
        "ensuring untrusted user CSV uploads cannot corrupt simulation results."
    )

    # =========================================================================
    # SLIDE 6: STRATEGIES & ZERO LOOK-AHEAD
    # =========================================================================
    slide6 = prs.slides.add_slide(blank_layout)
    add_header(slide6, "Financial Modeling", "Trading Strategies & Zero Look-Ahead Execution")

    add_card(slide6, Inches(0.8), Inches(1.7), Inches(3.7), Inches(5.0),
             "Strategy A: MA Crossover", [
                 "Fast SMA/EMA crosses Slow SMA/EMA.",
                 "Long Entry: Fast MA crosses above Slow MA.",
                 "Exit: Fast MA crosses below Slow MA.",
                 "Param Validation: Enforces Fast < Slow strictly.",
                 "Warm-up: Slow period initial bars."
             ])

    add_card(slide6, Inches(4.8), Inches(1.7), Inches(3.7), Inches(5.0),
             "Strategy B: RSI Reversion", [
                 "Wilder's exponential smoothing alpha = 1/P.",
                 "Long Entry: RSI drops <= Oversold (e.g. 30).",
                 "Exit: RSI recovers >= Exit threshold (e.g. 50).",
                 "Param Validation: Enforces 0 < Oversold < Exit < 100.",
                 "Captures cyclical mean-reversion."
             ])

    add_card(slide6, Inches(8.8), Inches(1.7), Inches(3.7), Inches(5.0),
             "Strategy C: Donchian Breakout", [
                 "Shifted Rolling Channels: shift(1) prevents look-ahead leakage.",
                 "Long Entry: Close breaks above prior upper channel.",
                 "Exit: Close breaks below prior lower channel.",
                 "Warm-up: max(Entry, Exit) + 1 bars.",
                 "Classic trend-following breakout."
             ])

    slide6.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 6 - Strategies & Lookahead):\n"
        "Notice the crucial modeling detail on the right: in Donchian breakouts, we shift the rolling window by 1. "
        "Furthermore, across all strategies, a signal computed at candle t's close is executed on candle t+1's Open. "
        "Executing at candle t's close is physically impossible in live markets; our model guarantees zero look-ahead bias."
    )

    # =========================================================================
    # SLIDE 7: PARALLEL COMPUTING FORMULATION
    # =========================================================================
    slide7 = prs.slides.add_slide(blank_layout)
    add_header(slide7, "Parallel Computing", "Task Parallelism & Speedup Formulations")

    add_card(slide7, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.0),
             "Embarrassingly Parallel Formulation", [
                 "Task independence: Task_i is evaluated autonomously without inter-process communication.",
                 "Shared Immutable Data: OHLC dataset serialized into lightweight records.",
                 "State Isolation: Worker processes maintain no shared mutable state.",
                 "Fault Resilience: Individual worker exceptions are caught and reported without crashing the batch.",
                 "Deterministic Output: Results sorted by task_id to ensure repeatable benchmarks."
             ])

    add_card(slide7, Inches(6.8), Inches(1.7), Inches(5.6), Inches(5.0),
             "Mathematical Formulations", [
                 "Speedup (Sp) = T_sequential / T_parallel",
                 "Parallel Efficiency (Ep) = Sp / p  (Percentage: Ep × 100%)",
                 "Ideal Linear Speedup: Sp = p, Ep = 1.0 (100%)",
                 "Amdahl's Law: S_max = 1 / ((1 - f) + f / p)",
                 "   where f = parallel fraction of workload",
                 "Overhead Components: T_parallel = T_spawn + T_IPC + (T_compute / p)"
             ])

    slide7.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 7 - Parallel Formulations):\n"
        "Here are the core parallel computing metrics. Speedup Sp represents how many times faster parallel execution is "
        "compared to sequential. Efficiency Ep measures hardware utilization. Amdahl's Law explains the theoretical ceiling: "
        "because parameter evaluations are independent, f approaches 1.0 as the grid grows, yielding high scalability."
    )

    # =========================================================================
    # SLIDE 8: EMPIRICAL BENCHMARKS & OVERHEAD CROSSOVER
    # =========================================================================
    slide8 = prs.slides.add_slide(blank_layout)
    add_header(slide8, "Empirical Performance", "Measured Benchmarks & Overhead Crossover Analysis")

    # Table on left
    rows, cols = 5, 5
    table_shape = slide8.shapes.add_table(rows, cols, Inches(0.8), Inches(1.8), Inches(6.5), Inches(2.8))
    table = table_shape.table

    headers = ["Execution Mode", "Workers", "Wall Time", "Speedup", "Efficiency"]
    data = [
        ["Sequential", "1", "3.42 s", "1.00x", "100.0%"],
        ["Parallel (2w)", "2", "1.90 s", "1.80x", "90.2%"],
        ["Parallel (4w)", "4", "1.08 s", "3.16x", "79.0%"],
        ["Parallel (8w)", "8", "0.69 s", "4.95x", "61.9%"]
    ]

    for c_idx, h in enumerate(headers):
        cell = table.cell(0, c_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(30, 41, 59)
        p = cell.text_frame.paragraphs[0]
        p.text = h
        p.font.size = Pt(11)
        p.font.bold = True
        p.font.color.rgb = ACCENT_TEAL

    for r_idx, row in enumerate(data):
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx + 1, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = CARD_BG
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.size = Pt(11)
            p.font.color.rgb = TEXT_WHITE

    # Key Takeaways on right
    add_card(slide8, Inches(7.6), Inches(1.8), Inches(4.9), Inches(4.9),
             "The Overhead Crossover Phenomenon", [
                 "Small Workloads (<20 tasks): Sp < 1.0 due to process startup (T_spawn) and IPC serialization.",
                 "Medium-to-Large Workloads (50+ tasks): Compute time dominates fixed overhead; Sp scales significantly.",
                 "4-Worker Performance: Achieves 3.16x speedup with 79% parallel efficiency.",
                 "8-Worker Performance: Reaches 4.95x speedup; efficiency declines to 62% due to OS thread contention and IPC pipe bandwidth.",
                 "Conclusion: Multi-processing is ideal for expansive quantitative parameter exploration."
             ])

    slide8.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 8 - Benchmarks):\n"
        "This slide presents empirical data measured on our 20-core test environment. Notice the honest discussion of the "
        "crossover point: for small grids of 10 tasks, sequential is faster because spawning processes takes around 0.5s. "
        "However, as task size scales to 100+, parallel execution dominates, reaching 4.95x speedup with 8 workers."
    )

    # =========================================================================
    # SLIDE 9: FINANCIAL METRICS & RANKING
    # =========================================================================
    slide9 = prs.slides.add_slide(blank_layout)
    add_header(slide9, "Financial Analytics", "Risk-Adjusted Performance & Strategy Ranking")

    metrics_list1 = [
        "Total Return (%): Final equity over initial capital.",
        "Annualized Return (%): Compounded annual growth rate (252-day basis).",
        "Max Drawdown (%): Largest historical peak-to-trough decline.",
        "Sharpe Ratio: Excess daily return divided by volatility, annualized by sqrt(252).",
        "Win Rate (%): Winning trades divided by total completed trades."
    ]
    add_card(slide9, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.0),
             "Comprehensive Financial Metrics", metrics_list1)

    metrics_list2 = [
        "Profit Factor: Gross winning trades sum divided by gross losing trades sum.",
        "Average Holding Period: Mean duration (in bars) per trade.",
        "Total Friction Costs: Cumulative commission and slippage deductions.",
        "Multi-Metric Ranking: Rank by Sharpe, Return, Drawdown, or Profit Factor.",
        "Weighted Scoring: Customizable risk-return balance score = 0.4(Sharpe) + 0.3(Return) - 0.3(Drawdown)."
    ]
    add_card(slide9, Inches(6.8), Inches(1.7), Inches(5.6), Inches(5.0),
             "Trade Accounting & Ranking Logic", metrics_list2)

    slide9.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 9 - Metrics):\n"
        "Strategy evaluation cannot rely on return alone. Our engine calculates institutional risk metrics: "
        "annualized Sharpe ratio with risk-free rate adjustment, maximum peak-to-trough drawdown, profit factor, "
        "and total transaction friction. Strategies are ranked interactively to identify robust risk-adjusted models."
    )

    # =========================================================================
    # SLIDE 10: USER INTERFACE (STREAMLIT)
    # =========================================================================
    slide10 = prs.slides.add_slide(blank_layout)
    add_header(slide10, "User Experience", "Interactive Streamlit Quantitative Dashboard")

    pages = [
        ("1. Overview", "System health, dataset status, active CPU cores, and latest benchmark summary cards."),
        ("2. Data Explorer", "CSV upload, 7-point validation audit, interactive Plotly OHLC candlestick & volume chart."),
        ("3. Strategy Config", "Sliders for initial capital, commissions, slippage, parameter grids, and execution mode."),
        ("4. Backtest Results", "Multi-criteria ranking table, interactive equity curve, drawdown underwater chart, and trade history."),
        ("5. Parallel Lab", "Worker-count selectors, real-time benchmark execution, speedup, and efficiency charts."),
        ("6. Reports & Exports", "One-click export of Backtest Results CSV, Trades CSV, Benchmark CSV, and Markdown audit report.")
    ]

    for idx, (title, desc) in enumerate(pages):
        row = idx // 2
        col = idx % 2
        left = Inches(0.8 + col * 6.0)
        top = Inches(1.7 + row * 1.7)
        c = slide10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(5.7), Inches(1.5))
        c.fill.solid()
        c.fill.fore_color.rgb = CARD_BG
        c.line.color.rgb = CARD_BORDER
        c.line.width = Pt(1.5)
        tf = c.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.25)
        tf.margin_top = Inches(0.15)
        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.size = Pt(14)
        p1.font.bold = True
        p1.font.color.rgb = ACCENT_CYAN
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = TEXT_BODY

    slide10.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 10 - Streamlit Dashboard):\n"
        "Here is the interactive Streamlit user interface. It spans six cohesive pages with a dark navy quantitative "
        "aesthetic. Users can visually explore OHLC candles, tune parameter ranges, execute benchmarks, inspect equity "
        "curves, and export compliance audit reports in CSV and Markdown."
    )

    # =========================================================================
    # SLIDE 11: QUALITY ASSURANCE & TEST SUITE
    # =========================================================================
    slide11 = prs.slides.add_slide(blank_layout)
    add_header(slide11, "Quality Assurance", "72 Automated Tests & Numerical Consistency Proof")

    test_suites = [
        "test_data_validation.py (16 tests): Validates column normalizer, duplicate pruning, positive price rules, and geometry checks.",
        "test_strategies.py (22 tests): Verifies MA crossover, RSI Wilder smoothing, Donchian shifted channels, and parameter constraints.",
        "test_backtesting.py (18 tests): Confirms portfolio cash ledger, next-bar open fill timing, commission deduction, and equity tracking.",
        "test_parallel_consistency.py (10 tests): Proves sequential vs parallel numerical consistency and worker error isolation.",
        "test_metrics.py (6 tests): Validates Sharpe edge cases, zero-volatility guards, max drawdown, and profit factor formulations."
    ]
    add_card(slide11, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.0),
             "Automated Test Coverage (100% Passing)", test_suites)

    proof_points = [
        "Numerical Consistency Proof: Sequential and parallel executions take identical tasks and data.",
        "Tolerance Constraint: |Metric_seq - Metric_par| < 10^-6 across all returned financial indicators.",
        "Identical Trades: Entry dates, fill prices, exit prices, and PnL match exactly between modes.",
        "Worker Fault Isolation: When a task encounters bad parameters, it returns an error descriptor without crashing sibling tasks.",
        "Execution Time: All 72 tests execute in under 2.5 seconds on pytest."
    ]
    add_card(slide11, Inches(6.8), Inches(1.7), Inches(5.6), Inches(5.0),
             "Sequential-Parallel Consistency Proof", proof_points)

    slide11.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 11 - Testing & Consistency):\n"
        "A critical academic requirement is proving that parallelization does not compromise numerical correctness. "
        "Our test suite of 72 unit and integration tests verifies that sequential and parallel execution produce "
        "identical financial metrics down to 10^-6 precision. Every test passes cleanly in under 2.5 seconds."
    )

    # =========================================================================
    # SLIDE 12: LIMITATIONS & FUTURE WORK
    # =========================================================================
    slide12 = prs.slides.add_slide(blank_layout)
    add_header(slide12, "Critical Evaluation", "System Limitations & Future Roadmap")

    add_card(slide12, Inches(0.8), Inches(1.7), Inches(5.6), Inches(5.0),
             "Academic Modeling Assumptions", [
                 "Fixed Fill Assumption: Assumes 100% order fill probability at next bar's Open price.",
                 "Linear Cost Model: Fixed commission and slippage percentages abstract away dynamic order book spread widening.",
                 "Long-Only Exposures: Short-selling borrow fees and margin maintenance are currently omitted.",
                 "Overfitting Caution: Selecting top backtested parameters over historical data risks curve-fitting noise (p-hacking).",
                 "Educational Scope: Designed for parallel computing study, not live broker order routing."
             ])

    add_card(slide12, Inches(6.8), Inches(1.7), Inches(5.6), Inches(5.0),
             "Strategic Future Enhancements", [
                 "Distributed Multi-Node Clusters: Integrating Ray or Dask for scaling across cloud server clusters.",
                 "GPU Acceleration: Offloading matrix rolling operations and indicator calculations to CUDA / CuPy.",
                 "Walk-Forward Analysis (WFA): Rolling train-test out-of-sample optimization to mitigate data snooping.",
                 "High-Frequency Tick Replay: Simulating sub-second limit order book queues and partial fills.",
                 "Machine Learning Integration: Evaluating reinforcement learning and deep neural network trading policies."
             ])

    slide12.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 12 - Limitations & Roadmap):\n"
        "In academic engineering, it is vital to acknowledge modeling boundaries. We make clear that order book liquidity, "
        "dynamic spread widening, and borrow fees are abstracted. Future extensions include distributed cluster computing "
        "via Ray or Dask, GPU matrix acceleration, and walk-forward cross-validation."
    )

    # =========================================================================
    # SLIDE 13: CONCLUSION & DEFENSE READINESS
    # =========================================================================
    slide13 = prs.slides.add_slide(blank_layout)
    add_header(slide13, "Conclusion", "Project Achievements & Summary")

    add_card(slide13, Inches(0.8), Inches(1.7), Inches(3.7), Inches(5.0),
             "Parallel Computing Success", [
                 "Demonstrated successful GIL circumvention via ProcessPoolExecutor.",
                 "Achieved up to 4.95x measured speedup on multi-core CPU hardware.",
                 "Empirically validated Amdahl's Law and overhead crossover dynamics.",
                 "100% cross-platform compatibility across Windows and Linux."
             ])

    add_card(slide13, Inches(4.8), Inches(1.7), Inches(3.7), Inches(5.0),
             "Quantitative Rigor", [
                 "Zero look-ahead bias execution engine (next-bar open execution).",
                 "Institutional risk metrics: Sharpe, Max Drawdown, and Profit Factor.",
                 "3 fully configurable rule-based trading strategy families.",
                 "Comprehensive 7-point data quality validation suite."
             ])

    add_card(slide13, Inches(8.8), Inches(1.7), Inches(3.7), Inches(5.0),
             "Deliverables Delivered", [
                 "Interactive Streamlit web application with 6 functional pages.",
                 "72/72 passing automated pytest test cases.",
                 "Complete technical documentation, viva Q&A guide, and report.",
                 "Ready for academic defense and laboratory demonstration."
             ])

    slide13.notes_slide.notes_text_frame.text = (
        "SPEAKER NOTES (Slide 13 - Conclusion):\n"
        "In conclusion, the Parallel Financial Strategy Backtesting Engine successfully demonstrates how multi-process "
        "task parallelism transforms quantitative backtesting performance. The system achieves measurable speedup, "
        "rigorous financial modeling, and complete test verification. Thank you, and I now welcome your questions."
    )

    # Save presentation
    prs.save(output_path)
    print(f"Presentation generated successfully: {output_path}")

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "PFSBE_Final_Presentation.pptx"
    create_deck(out)

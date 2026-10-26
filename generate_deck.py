"""
QuantDB Presentation Generator - Master Script
Generates a complete, professional, 22-slide PowerPoint presentation
QuantDB_DBMS_Project_Sem3.pptx covering all 20 required sections in depth.
"""

import os
import sys
import pptx
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

# -------------------------------------------------------------
# Color Palette Constants (Dark Navy & Cyan Fintech Aesthetics)
# -------------------------------------------------------------
BG_COLOR = RGBColor(11, 19, 43)        # #0B132B Midnight Navy
CARD_BG = RGBColor(19, 32, 56)         # #132038 Deep Slate Navy
CARD_BORDER = RGBColor(38, 58, 92)     # #263A5C Subtle Border
ACCENT_CYAN = RGBColor(0, 229, 255)    # #00E5FF Electric Cyan
ACCENT_BLUE = RGBColor(58, 134, 255)   # #3A86FF Royal Blue
ACCENT_MINT = RGBColor(0, 245, 212)    # #00F5D4 Emerald Mint
ACCENT_GOLD = RGBColor(255, 183, 3)    # #FFB703 Amber Gold
TEXT_WHITE = RGBColor(255, 255, 255)   # #FFFFFF
TEXT_MUTED = RGBColor(156, 175, 201)   # #9CAFC9 Slate Silver
TEXT_CYAN = RGBColor(128, 237, 255)    # #80EDFF Ice Cyan
CODE_BG = RGBColor(13, 22, 38)         # #0D1626 Monospace block bg
CODE_BORDER = RGBColor(30, 48, 76)     # #1E304C
TABLE_HEADER_BG = RGBColor(16, 42, 77) # #102A4D Table Header
TABLE_ROW_ALT = RGBColor(14, 25, 45)   # #0E192D Table Alt Row

FONT_HEADING = "Helvetica"
FONT_BODY = "Arial"
FONT_CODE = "Courier New"

TOTAL_SLIDES = 22

def create_deck():
    prs = pptx.Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs

def apply_background(slide):
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = BG_COLOR
    bg.line.fill.background()
    return bg

def add_header(slide, category: str, title: str, subtitle: str):
    # Category Pill
    pill_w = max(2.4, len(category) * 0.12 + 0.6)
    pill = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.38), Inches(pill_w), Inches(0.30)
    )
    pill.fill.solid()
    pill.fill.fore_color.rgb = RGBColor(15, 34, 61)
    pill.line.color.rgb = ACCENT_CYAN
    pill.line.width = Pt(1)
    tf_p = pill.text_frame
    tf_p.word_wrap = True
    p_p = tf_p.paragraphs[0]
    p_p.text = category.upper()
    p_p.font.name = FONT_HEADING
    p_p.font.size = Pt(8.5)
    p_p.font.bold = True
    p_p.font.color.rgb = ACCENT_CYAN
    p_p.alignment = PP_ALIGN.CENTER

    # Title & Subtitle
    tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.72), Inches(11.733), Inches(0.82))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p_t = tf.paragraphs[0]
    p_t.text = title
    p_t.font.name = FONT_HEADING
    p_t.font.size = Pt(21)
    p_t.font.bold = True
    p_t.font.color.rgb = TEXT_WHITE
    p_t.space_after = Pt(2)

    p_s = tf.add_paragraph()
    p_s.text = subtitle
    p_s.font.name = FONT_BODY
    p_s.font.size = Pt(11.5)
    p_s.font.color.rgb = TEXT_MUTED

def add_footer(slide, slide_num: int):
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(7.02), Inches(11.733), Inches(0.015)
    )
    line.fill.solid()
    line.fill.fore_color.rgb = CARD_BORDER
    line.line.fill.background()

    # Left note
    tb_l = slide.shapes.add_textbox(Inches(0.8), Inches(7.07), Inches(8.5), Inches(0.28))
    tf_l = tb_l.text_frame
    tf_l.margin_left = tf_l.margin_top = tf_l.margin_right = tf_l.margin_bottom = 0
    p_l = tf_l.paragraphs[0]
    p_l.text = "QuantDB — Market Data & Algorithmic Trading Platform | DBMS Lab (Sem 3) | SVNIT Surat"
    p_l.font.name = FONT_BODY
    p_l.font.size = Pt(8.5)
    p_l.font.color.rgb = TEXT_MUTED

    # Right slide counter
    tb_r = slide.shapes.add_textbox(Inches(10.0), Inches(7.07), Inches(2.533), Inches(0.28))
    tf_r = tb_r.text_frame
    tf_r.margin_left = tf_r.margin_top = tf_r.margin_right = tf_r.margin_bottom = 0
    p_r = tf_r.paragraphs[0]
    p_r.text = f"Slide {slide_num} of {TOTAL_SLIDES}"
    p_r.font.name = FONT_HEADING
    p_r.font.size = Pt(9)
    p_r.font.bold = True
    p_r.font.color.rgb = ACCENT_CYAN
    p_r.alignment = PP_ALIGN.RIGHT

def add_speaker_notes(slide, notes: str):
    notes_slide = slide.notes_slide
    notes_slide.notes_text_frame.text = notes.strip()

def create_card(slide, left, top, width, height, title="", title_color=ACCENT_CYAN, border_color=CARD_BORDER, bg_color=CARD_BG):
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(1)

    if title:
        tb = slide.shapes.add_textbox(left + Inches(0.22), top + Inches(0.18), width - Inches(0.44), Inches(0.38))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title
        p.font.name = FONT_HEADING
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = title_color
    return card

def add_bullet_list(tf, items, font_size=10.5, text_color=TEXT_WHITE, space_after=6):
    for idx, item in enumerate(items):
        if idx == 0 and len(tf.paragraphs) == 1 and tf.paragraphs[0].text == "":
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.space_after = Pt(space_after)
        p.font.name = FONT_BODY
        p.font.size = Pt(font_size)
        
        # Check if item has title/prefix like "**Title:** text"
        if "**" in item:
            parts = item.split("**")
            # e.g. ["", "Title:", " rest of text"]
            for i, part in enumerate(parts):
                if not part:
                    continue
                run = p.add_run()
                run.text = part
                run.font.name = FONT_BODY
                run.font.size = Pt(font_size)
                if i % 2 == 1:
                    run.font.bold = True
                    run.font.color.rgb = ACCENT_CYAN
                else:
                    run.font.bold = False
                    run.font.color.rgb = text_color
        else:
            run = p.add_run()
            run.text = item
            run.font.name = FONT_BODY
            run.font.size = Pt(font_size)
            run.font.color.rgb = text_color

# -------------------------------------------------------------
# SLIDE BUILDERS (SLIDES 1 TO 22)
# -------------------------------------------------------------

def build_slide_1_title(prs):
    # Slide 1: Title
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)

    # Hero Card
    hero = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.8), Inches(11.733), Inches(5.9)
    )
    hero.fill.solid()
    hero.fill.fore_color.rgb = CARD_BG
    hero.line.color.rgb = ACCENT_CYAN
    hero.line.width = Pt(1.5)

    # Pill Badge top
    pill = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.3), Inches(1.2), Inches(5.2), Inches(0.38)
    )
    pill.fill.solid()
    pill.fill.fore_color.rgb = RGBColor(16, 40, 72)
    pill.line.color.rgb = ACCENT_CYAN
    pill.line.width = Pt(1)
    tf_p = pill.text_frame
    p_p = tf_p.paragraphs[0]
    p_p.text = "DATABASE MANAGEMENT SYSTEMS LAB PROJECT — SEMESTER 3"
    p_p.font.name = FONT_HEADING
    p_p.font.size = Pt(10)
    p_p.font.bold = True
    p_p.font.color.rgb = ACCENT_CYAN
    p_p.alignment = PP_ALIGN.CENTER

    # Title & Subtitle Box
    tb = slide.shapes.add_textbox(Inches(1.3), Inches(1.8), Inches(10.7), Inches(2.2))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p1 = tf.paragraphs[0]
    p1.text = "QuantDB"
    p1.font.name = FONT_HEADING
    p1.font.size = Pt(44)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_WHITE
    p1.space_after = Pt(4)

    p2 = tf.add_paragraph()
    p2.text = "A Database-Driven Market Data and Algorithmic Trading Research Platform"
    p2.font.name = FONT_HEADING
    p2.font.size = Pt(20)
    p2.font.bold = True
    p2.font.color.rgb = ACCENT_CYAN
    p2.space_after = Pt(14)

    p3 = tf.add_paragraph()
    p3.text = "An institutional-grade relational schema powering historical tick storage, simulated order matching, portfolio tracking, and quantitative strategy backtesting."
    p3.font.name = FONT_BODY
    p3.font.size = Pt(13)
    p3.font.color.rgb = TEXT_MUTED

    # Metadata Cards (2 columns at bottom of hero)
    c1 = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.3), Inches(4.3), Inches(5.1), Inches(1.9)
    )
    c1.fill.solid()
    c1.fill.fore_color.rgb = RGBColor(14, 25, 46)
    c1.line.color.rgb = CARD_BORDER
    tf1 = c1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = Inches(0.2)
    p_c1_t = tf1.paragraphs[0]
    p_c1_t.text = "ACADEMIC & INSTITUTIONAL CONTEXT"
    p_c1_t.font.name = FONT_HEADING
    p_c1_t.font.size = Pt(11)
    p_c1_t.font.bold = True
    p_c1_t.font.color.rgb = ACCENT_CYAN
    p_c1_t.space_after = Pt(6)

    bullets1 = [
        "**Institution:** SVNIT Surat (Sardar Vallabhbhai NIT)",
        "**Department:** Computer Science and Engineering",
        "**Subject:** Database Management Systems (CS207)",
        "**Academic Scope:** Paper Trading & Research Simulation",
    ]
    add_bullet_list(tf1, bullets1, font_size=10, space_after=3)

    c2 = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.7), Inches(4.3), Inches(5.3), Inches(1.9)
    )
    c2.fill.solid()
    c2.fill.fore_color.rgb = RGBColor(14, 25, 46)
    c2.line.color.rgb = CARD_BORDER
    tf2 = c2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = Inches(0.2)
    p_c2_t = tf2.paragraphs[0]
    p_c2_t.text = "CORE TECHNOLOGY STACK"
    p_c2_t.font.name = FONT_HEADING
    p_c2_t.font.size = Pt(11)
    p_c2_t.font.bold = True
    p_c2_t.font.color.rgb = ACCENT_MINT
    p_c2_t.space_after = Pt(6)

    bullets2 = [
        "**Relational Engine:** MySQL 8.x / Aiven MySQL (InnoDB, UTF8MB4)",
        "**Backend & Analytics:** Python 3.13, Pandas, NumPy, MySQL Connector",
        "**Research Terminal UI:** Streamlit Dark Architecture, Plotly Charts",
        "**Verification:** Pytest Suite (235 Passed / 238 Tests)",
    ]
    add_bullet_list(tf2, bullets2, font_size=10, space_after=3)

    add_speaker_notes(slide, """
Good morning, respected professors and evaluators.
Today, I am presenting QuantDB — a database-driven quantitative finance research and simulated trading platform developed as our Semester-3 DBMS Lab Project at SVNIT Surat.

In this project, we bridge core database management principles with real-world quantitative finance. Financial research requires organizing complex, interrelated entities: securities, multi-timestamp market data, simulated orders, executed trades, portfolios, and backtest results.
Instead of relying on isolated scripts or flat CSV files, QuantDB implements a fully normalized MySQL relational database with referential integrity, ACID transaction management, indexes, triggers, and stored procedures, integrated with a Python quantitative analytics engine and an interactive Streamlit terminal.
Let us examine the problem statement that motivated this architecture.
""")

def build_slide_2_problem(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 2: Problem Statement", "The Database Challenges in Quantitative Finance", 
               "Why conventional file-based approaches fail and why a centralized RDBMS is essential.")
    add_footer(slide, 2)

    # 3 Cards Layout
    card_w = Inches(3.64)
    card_h = Inches(5.0)
    top_pos = Inches(1.75)

    # Card 1: Data Fragmentation
    c1 = create_card(slide, Inches(0.8), top_pos, card_w, card_h, "1. Flat File Pitfalls", ACCENT_GOLD)
    tb1 = slide.shapes.add_textbox(Inches(1.0), top_pos + Inches(0.65), card_w - Inches(0.4), card_h - Inches(0.8))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = 0
    b1 = [
        "**Scattered Data Sources:** Financial researchers typically juggle detached CSVs, Excel workbooks, and ad-hoc scripts.",
        "**Rampant Redundancy:** Exchange codes, security metadata, and currency definitions are duplicated across thousands of price tick rows.",
        "**Update & Delete Anomalies:** Modifying an exchange's timezone or purging price history corrupts or permanently deletes security reference master data.",
        "**Zero Schema Enforcement:** No type safety, allowing corrupted decimal prices or missing timestamps to pass silently into models.",
    ]
    add_bullet_list(tf1, b1, font_size=10, space_after=8)

    # Card 2: Integrity & Concurrency
    c2 = create_card(slide, Inches(4.84), top_pos, card_w, card_h, "2. Integrity & Race Conditions", RGBColor(255, 107, 107))
    tb2 = slide.shapes.add_textbox(Inches(5.04), top_pos + Inches(0.65), card_w - Inches(0.4), card_h - Inches(0.8))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = 0
    b2 = [
        "**Lack of ACID Guarantees:** Multi-step paper trading (order submission -> cash reduction -> trade creation -> position update) can fail mid-way, leaving phantom balances.",
        "**Race Conditions:** Concurrent simulated orders cause double-spending of portfolio cash without database row locking.",
        "**Orphaned Records:** Trades referencing deleted orders or orders referencing non-existent securities create unrecoverable analytical drift.",
        "**No Native Constraints:** Cannot easily enforce business rules like High Price >= Low Price or Positive Quantities at storage level.",
    ]
    add_bullet_list(tf2, b2, font_size=10, space_after=8)

    # Card 3: RDBMS Solution
    c3 = create_card(slide, Inches(8.88), top_pos, card_w, card_h, "3. The RDBMS Solution", ACCENT_CYAN)
    tb3 = slide.shapes.add_textbox(Inches(9.08), top_pos + Inches(0.65), card_w - Inches(0.4), card_h - Inches(0.8))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_top = 0
    b3 = [
        "**Centralized Relational Storage:** A single source of truth connecting exchanges, securities, orders, trades, and portfolios.",
        "**3NF Normalization:** Eliminates repeating groups and transitive dependencies, ensuring minimum storage footprint.",
        "**Strict Constraints & Triggers:** Primary keys, foreign keys, CHECK constraints, and triggers enforce real-time market data validity.",
        "**High-Performance SQL:** Multi-table JOINs, aggregated views, and B+ Tree indexes deliver millisecond data slices to the backtester.",
    ]
    add_bullet_list(tf3, b3, font_size=10, space_after=8)

    add_speaker_notes(slide, """
In financial analytics, data integrity is paramount. If you run a strategy simulation on corrupted market data or phantom portfolio balances, your entire risk assessment is invalid.
In typical academic setups, students use CSV files. But CSVs have no referential integrity, no ACID guarantees, and cause severe update anomalies.
If an order executes, three things must happen simultaneously: the order status becomes FILLED, a trade record is created, and the portfolio cash balance is decremented. If the system crashes halfway, a flat-file system leaves an inconsistent state.
A relational database with InnoDB row-level locking and foreign key cascades solves this completely.
""")

def build_slide_3_objectives(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 3: Project Objectives", "Core DBMS & Engineering Goals", 
               "Systematic objectives mapping database theory directly into software implementation.")
    add_footer(slide, 3)

    # 4 Cards Grid (2x2)
    cw = Inches(5.66)
    ch = Inches(2.38)

    # Grid 1: Relational Design
    c1 = create_card(slide, Inches(0.8), Inches(1.8), cw, ch, "1. Centralized Schema & Normalization", ACCENT_CYAN)
    tb1 = slide.shapes.add_textbox(Inches(1.0), Inches(2.28), cw - Inches(0.4), ch - Inches(0.55))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = 0
    b1 = [
        "**Centralized RDBMS:** Design and deploy a relational database managing 12+ interconnected financial entities.",
        "**ER Modeling:** Construct a conceptual Entity-Relationship model with rigorous cardinality mapping.",
        "**Third Normal Form (3NF):** Eliminate functional redundancies and anomalies between securities, exchanges, and ticks.",
    ]
    add_bullet_list(tf1, b1, font_size=10, space_after=4)

    # Grid 2: Constraints & SQL
    c2 = create_card(slide, Inches(6.86), Inches(1.8), cw, ch, "2. Integrity Constraints & Advanced SQL", ACCENT_MINT)
    tb2 = slide.shapes.add_textbox(Inches(7.06), Inches(2.28), cw - Inches(0.4), ch - Inches(0.55))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = 0
    b2 = [
        "**Declarative Constraints:** Implement PKs, FKs, UNIQUE composite indexes, and complex domain CHECK rules.",
        "**Advanced SQL Querying:** Build multi-table JOINs, GROUP BY aggregations, correlated subqueries, and 9 database views.",
        "**Query Optimization:** Design secondary B+ Tree indexes and evaluate query execution plans using EXPLAIN.",
    ]
    add_bullet_list(tf2, b2, font_size=10, space_after=4)

    # Grid 3: Programmability & Transactions
    c3 = create_card(slide, Inches(0.8), Inches(4.42), cw, ch, "3. Programmability & ACID Concurrency", ACCENT_BLUE)
    tb3 = slide.shapes.add_textbox(Inches(1.0), Inches(4.90), cw - Inches(0.4), ch - Inches(0.55))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_top = 0
    b3 = [
        "**Database Programmability:** Develop stored procedures for querying, stored functions for math, and triggers for automated audit.",
        "**ACID Transactions:** Guarantee atomicity during order execution and cash transfer using START TRANSACTION and COMMIT/ROLLBACK.",
        "**Pessimistic Concurrency:** Demonstrate SELECT ... FOR UPDATE row-level locking to prevent race conditions.",
    ]
    add_bullet_list(tf3, b3, font_size=10, space_after=4)

    # Grid 4: Quant Engine & UI
    c4 = create_card(slide, Inches(6.86), Inches(4.42), cw, ch, "4. Python Quant Engine & Terminal UI", ACCENT_GOLD)
    tb4 = slide.shapes.add_textbox(Inches(7.06), Inches(4.90), cw - Inches(0.4), ch - Inches(0.55))
    tf4 = tb4.text_frame
    tf4.word_wrap = True
    tf4.margin_left = tf4.margin_top = 0
    b4 = [
        "**Full-Stack DB Integration:** Establish robust MySQL connection pooling with parameterized SQL in Python.",
        "**Quantitative Backtesting:** Simulate trading strategies (SMA, Momentum) and calculate Sharpe Ratio & Drawdown.",
        "**Terminal-Grade UI:** Deploy an 8-page Streamlit dashboard supporting dual real-database and mock-simulation modes.",
    ]
    add_bullet_list(tf4, b4, font_size=10, space_after=4)

    add_speaker_notes(slide, """
Our project objectives are structured around four pillars:
1. Centralized Relational Schema & Normalization up to 3NF.
2. Declarative Integrity Constraints, complex SQL operations, and performance tuning using B+ Tree indexes.
3. Database Programmability using Stored Procedures, Functions, Triggers, and ACID transaction control with row-level locks.
4. Python Quantitative Analytics integration, connecting the MySQL backend to an interactive Streamlit terminal.
Notice that each objective directly addresses a concept evaluated in our Semester 3 DBMS curriculum.
""")

def build_slide_4_motivation(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 4: Real-World Motivation", "Quantitative Research & Simulation Architecture", 
               "Connecting database engineering with modern algorithmic trading and investment research.")
    add_footer(slide, 4)

    # Top banner: Simulation Disclaimer
    banner = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.75), Inches(11.733), Inches(0.72)
    )
    banner.fill.solid()
    banner.fill.fore_color.rgb = RGBColor(30, 20, 10)
    banner.line.color.rgb = ACCENT_GOLD
    banner.line.width = Pt(1.5)
    tf_b = banner.text_frame
    tf_b.word_wrap = True
    p_b = tf_b.paragraphs[0]
    p_b.text = "ACADEMIC SIMULATION & PAPER TRADING DISCLAIMER"
    p_b.font.name = FONT_HEADING
    p_b.font.size = Pt(11)
    p_b.font.bold = True
    p_b.font.color.rgb = ACCENT_GOLD
    p_b_desc = tf_b.add_paragraph()
    p_b_desc.text = "QuantDB is strictly an academic simulated trading and quantitative research platform. It does NOT route orders to live exchanges, hold actual fiat currency, or execute real-money financial transactions."
    p_b_desc.font.name = FONT_BODY
    p_b_desc.font.size = Pt(9.5)
    p_b_desc.font.color.rgb = TEXT_WHITE

    # 3 Phase Cards
    cw = Inches(3.64)
    ch = Inches(4.15)
    top_pos = Inches(2.65)

    # Phase 1: Market Data
    c1 = create_card(slide, Inches(0.8), top_pos, cw, ch, "Phase 1: Ingestion & Storage", ACCENT_CYAN)
    tb1 = slide.shapes.add_textbox(Inches(1.0), top_pos + Inches(0.6), cw - Inches(0.4), ch - Inches(0.75))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = 0
    b1 = [
        "**Market Data Lifecycle:** Historical price ticks require rigorous ingestion, clean OHLC structuring, and continuous validation.",
        "**Microstructure Metrics:** Storing bid/ask quotes enables calculating Bid-Ask Spread, Market Depth, and Order Book Imbalance.",
        "**High Ingestion Volumes:** Requires composite indexes on (security_id, timestamp) for rapid sub-second slice queries during strategy evaluation.",
    ]
    add_bullet_list(tf1, b1, font_size=10, space_after=8)

    # Phase 2: Strategy & Backtesting
    c2 = create_card(slide, Inches(4.84), top_pos, cw, ch, "Phase 2: Strategy Backtesting", ACCENT_MINT)
    tb2 = slide.shapes.add_textbox(Inches(5.04), top_pos + Inches(0.6), cw - Inches(0.4), ch - Inches(0.75))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = 0
    b2 = [
        "**Strategy Formulation:** Researchers parameterize algorithmic rules (e.g. SMA 20/50 crossover, Mean Reversion Z-scores).",
        "**Event-Driven Backtesting:** Historical ticks replay against algorithms to generate simulated orders and trade blotters.",
        "**Result Persistence:** Output metrics (total return, P&L, trade counts, win rate) are committed to backtest_results for auditability.",
    ]
    add_bullet_list(tf2, b2, font_size=10, space_after=8)

    # Phase 3: Paper Trading & Risk
    c3 = create_card(slide, Inches(8.88), top_pos, cw, ch, "Phase 3: Portfolio & Risk Tracking", ACCENT_BLUE)
    tb3 = slide.shapes.add_textbox(Inches(9.08), top_pos + Inches(0.6), cw - Inches(0.4), ch - Inches(0.75))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_top = 0
    b3 = [
        "**Simulated Execution:** Supports MARKET and LIMIT orders with automated trade matching and status updates.",
        "**Real-Time Position Tracking:** Automatically calculates average acquisition cost, realized P&L, and unrealized floating P&L.",
        "**Institutional Risk Metrics:** Computes Annualized Volatility, Sharpe Ratio, and Maximum Drawdown to assess strategy risk.",
    ]
    add_bullet_list(tf3, b3, font_size=10, space_after=8)

    add_speaker_notes(slide, """
Let us establish the real-world domain context.
In quantitative hedge funds and trading firms, researchers don't just write algorithms — they rely on high-performance data systems to validate their hypotheses.
QuantDB models the entire quantitative research lifecycle:
1. Ingesting and validating OHLCV market data and microstructure quotes.
2. Backtesting mathematical trading strategies across historical time horizons.
3. Paper trading in simulated portfolios to track cash, positions, and risk metrics like Sharpe Ratio and Maximum Drawdown.
Crucially, as highlighted in the banner, this is an academic research platform. There is no real-money execution or live brokerage risk.
""")

def build_slide_5_roles(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 5: Users & Roles", "Role-Based Access Control & Schema Enforcement", 
               "Explicit distinction between conceptual user workflows and implemented database roles.")
    add_footer(slide, 5)

    # Left: Role Table (Table shape)
    table_shape = slide.shapes.add_table(5, 4, Inches(0.8), Inches(1.8), Inches(7.6), Inches(4.8))
    table = table_shape.table
    table.columns[0].width = Inches(1.8)
    table.columns[1].width = Inches(2.2)
    table.columns[2].width = Inches(2.0)
    table.columns[3].width = Inches(1.6)

    headers = ["Role (SQL ENUM)", "Primary Purpose", "Key Permissions", "Schema Status"]
    for col_idx, text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = TABLE_HEADER_BG
        p = cell.text_frame.paragraphs[0]
        p.text = text
        p.font.name = FONT_HEADING
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_CYAN

    data = [
        ("ADMIN", "System governance, exchange & security catalog management, user audit.", "Full DDL/DML, user verification, system topology.", "Active (Implemented)"),
        ("QUANT_RESEARCHER", "Quantitative model formulation, backtesting, factor research.", "Read market data, write strategies, execute backtests.", "Active (Implemented)"),
        ("SIMULATED_TRADER", "Simulated paper trading, order tickets, portfolio tracking.", "Place orders, manage portfolios, view positions.", "Active (Implemented)"),
        ("QUANT_DEVELOPER", "Database tuning, query optimization, analytics extension.", "Manage procedures, view explain plans, diagnostics.", "Active (Implemented)"),
    ]

    for row_idx, row in enumerate(data):
        for col_idx, val in enumerate(row):
            cell = table.cell(row_idx + 1, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = TABLE_ROW_ALT if row_idx % 2 == 1 else CARD_BG
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = FONT_BODY
            p.font.size = Pt(9.5)
            p.font.color.rgb = ACCENT_MINT if col_idx == 3 else (TEXT_WHITE if col_idx == 0 else TEXT_MUTED)
            if col_idx == 0:
                p.font.bold = True

    # Right: Technical Implementation Card
    cw = Inches(3.8)
    ch = Inches(4.8)
    c_right = create_card(slide, Inches(8.733), Inches(1.8), cw, ch, "Database-Level Security", ACCENT_CYAN)
    tb = slide.shapes.add_textbox(Inches(8.933), Inches(2.35), cw - Inches(0.4), ch - Inches(0.7))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = 0
    b = [
        "**SQL Schema Enforcement:** User roles are strictly validated via SQL ENUM constraints:",
        "`role ENUM('USER', 'QUANT_TRADER', 'QUANT_RESEARCHER', 'QUANT_DEVELOPER', 'ADMIN', 'SIMULATED_TRADER') NOT NULL`",
        "**Account Verification & OTPs:** Dedicated table `email_otps` stores hashed OTP tokens with expiration and attempt counters.",
        "**Conceptual vs Implemented:** While full enterprise LDAP/OAuth is future scope, QuantDB implements password hashing (PBKDF2/SHA-256), email uniqueness, and verified session authorization.",
    ]
    add_bullet_list(tf, b, font_size=9.5, space_after=6)

    add_speaker_notes(slide, """
Regarding user roles, we strictly adhere to what is actually implemented in the database schema.
In MySQL table `users`, the `role` column is enforced by an ENUM constraint containing ADMIN, QUANT_RESEARCHER, SIMULATED_TRADER, and QUANT_DEVELOPER.
Each role maps to specific operational workflows:
- Admins manage the security and exchange catalogs.
- Researchers build strategies and execute backtests.
- Traders execute simulated paper orders and monitor portfolios.
Additionally, the database includes an `email_otps` table for secure registration and verification. We do not claim external OAuth integrations that do not exist; our authorization is built directly on MySQL schema constraints and password hashing.
""")

def build_slide_6_functional_requirements(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 6: Functional Requirements", "Structured Functional Requirements Matrix", 
               "Core modules, implemented operations, database linkages, and business rules.")
    add_footer(slide, 6)

    # Table Shape for Functional Requirements
    table_shape = slide.shapes.add_table(7, 4, Inches(0.8), Inches(1.8), Inches(11.733), Inches(4.8))
    table = table_shape.table
    table.columns[0].width = Inches(2.2)
    table.columns[1].width = Inches(3.5)
    table.columns[2].width = Inches(3.2)
    table.columns[3].width = Inches(2.833)

    headers = ["Functional Module", "Key Implemented Capabilities", "Database Entities Involved", "DBMS Rule Enforced"]
    for col_idx, text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = TABLE_HEADER_BG
        p = cell.text_frame.paragraphs[0]
        p.text = text
        p.font.name = FONT_HEADING
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = ACCENT_CYAN

    data = [
        ("Data Management", "Create exchanges, register securities, store OHLCV daily market ticks and bid/ask quotes.", "exchanges, securities, market_data", "UNIQUE(security_id, timestamp), CHECK(high_price >= low_price)"),
        ("Trading Simulation", "Place simulated MARKET & LIMIT buy/sell orders, simulate execution, record trades.", "orders, trades, securities", "CHECK(quantity > 0), Trigger updating order_status to 'FILLED'"),
        ("Portfolio Management", "Track user portfolio cash, positions, average acquisition price, and realized/unrealized P&L.", "portfolios, positions, users", "UNIQUE(portfolio_id, security_id), Trigger preventing cash < 0"),
        ("Strategy Research", "Configure algorithmic strategies (Moving Average, Momentum, Mean Reversion) with JSON parameters.", "strategies, users", "FK to users, JSON parameter validation in application layer"),
        ("Backtesting Engine", "Execute strategies on historical market data, compute equity curves, persist result records.", "backtests, backtest_results, securities", "UNIQUE(backtest_id), CHECK(start_date <= end_date)"),
        ("Quantitative Analytics", "Calculate Sharpe Ratio, Annualized Volatility, Max Drawdown, Win Rate, and Microstructure metrics.", "risk_metrics, backtest_results", "XOR CHECK: risk_metric belongs to portfolio OR backtest"),
    ]

    for row_idx, row in enumerate(data):
        for col_idx, val in enumerate(row):
            cell = table.cell(row_idx + 1, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = TABLE_ROW_ALT if row_idx % 2 == 1 else CARD_BG
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = FONT_BODY
            p.font.size = Pt(9)
            p.font.color.rgb = ACCENT_CYAN if col_idx == 0 else (ACCENT_MINT if col_idx == 3 else TEXT_WHITE)
            if col_idx == 0:
                p.font.bold = True

    add_speaker_notes(slide, """
This functional requirements matrix demonstrates how our software features are directly tied to database constraints.
For example:
- In Data Management, the market_data entity enforces a composite unique constraint on security_id and timestamp, preventing duplicate tick records.
- In Trading Simulation, orders enforce quantity > 0, and inserting a trade automatically triggers an update to the order's status.
- In Quantitative Analytics, the risk_metrics table enforces an exclusive OR (XOR) constraint: each record must link to EITHER a portfolio OR a backtest, but never both.
Every functional requirement is backed by database-level integrity rules.
""")

def build_slide_7_architecture(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 7: System Architecture", "Layered System Architecture & Data Flow", 
               "Multi-tier architecture separating presentation, service abstractions, quant logic, and database.")
    add_footer(slide, 7)

    # Left: Layer Diagram Cards
    lw = Inches(6.8)
    lh = Inches(0.85)
    start_y = Inches(1.8)
    gap = Inches(0.18)

    layers = [
        ("Layer 1: Presentation Tier (Streamlit UI)", "Institutional dark terminal, 8 dedicated workspaces, Plotly financial charts.", ACCENT_CYAN),
        ("Layer 2: Service & Provider Tier", "Provider Factory supporting dual execution modes: Mock Simulation vs Real MySQL Bridge.", ACCENT_MINT),
        ("Layer 3: Quantitative Analytics Engine", "Pandas & NumPy engines for OHLCV vectorization, backtesting, Sharpe Ratio & Drawdown.", ACCENT_BLUE),
        ("Layer 4: Repository & Query Layer", "queries.py executing parameterized SQL (%s) with MySQL connection pooling & error handling.", ACCENT_GOLD),
        ("Layer 5: Database Storage Tier", "MySQL 8.x / Aiven MySQL with InnoDB engine, B+ Tree indexes, ACID transactions, and Triggers.", RGBColor(255, 107, 107)),
    ]

    for i, (title, desc, col) in enumerate(layers):
        y_pos = start_y + i * (lh + gap)
        c = create_card(slide, Inches(0.8), y_pos, lw, lh, "", col, bg_color=CARD_BG)
        tb = slide.shapes.add_textbox(Inches(1.0), y_pos + Inches(0.12), lw - Inches(0.4), lh - Inches(0.24))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = 0
        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.name = FONT_HEADING
        p1.font.size = Pt(11)
        p1.font.bold = True
        p1.font.color.rgb = col
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.name = FONT_BODY
        p2.font.size = Pt(9.5)
        p2.font.color.rgb = TEXT_WHITE

    # Right: 5-Step Execution Flow Card
    rw = Inches(4.6)
    rh = Inches(4.97)
    c_flow = create_card(slide, Inches(7.933), Inches(1.8), rw, rh, "5-Step Execution Flow", ACCENT_CYAN)
    tb_flow = slide.shapes.add_textbox(Inches(8.15), Inches(2.35), rw - Inches(0.4), rh - Inches(0.7))
    tf_flow = tb_flow.text_frame
    tf_flow.word_wrap = True
    tf_flow.margin_left = tf_flow.margin_top = 0

    steps = [
        "**1. User Interaction:** User selects a security (e.g. RELIANCE) and initiates a backtest or submits a paper order.",
        "**2. Service Delegation:** The Streamlit page routes request to the Service Layer (`market_service`, `trading_service`).",
        "**3. Repository SQL Execution:** Repository fetches connection from pool, executes parameterized SQL on MySQL with InnoDB row lock.",
        "**4. Analytics Processing:** Raw database records are converted to Pandas DataFrames; NumPy computes moving averages, signals, and risk.",
        "**5. Reactive UI Rendering:** Metrics, tables, and Plotly equity curves return to Streamlit with clean dark formatting.",
    ]
    add_bullet_list(tf_flow, steps, font_size=9.5, space_after=8)

    add_speaker_notes(slide, """
Here is our System Architecture. It follows a clean five-layer structure:
At the top is the Presentation Layer built in Streamlit.
Below that is the Service and Provider Layer. We implemented a Provider Factory pattern that allows running in either 'Real' mode connected to MySQL, or 'Mock' mode for offline testing.
The third layer is our Python Quantitative Analytics engine, which vectorizes financial calculations.
The fourth layer is the Database Repository in `src/database/queries.py`, which exclusively uses parameterized SQL queries to eliminate SQL injection vulnerabilities.
At the foundation is MySQL 8.x with the InnoDB engine.
When a user runs a backtest, the 5-step flow shown on the right executes cleanly without tight coupling between UI and SQL.
""")

def build_slide_8_er_diagram(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 8: Entity-Relationship Model", "Conceptual ER Diagram & Entity Cardinalities", 
               "12 core relational entities plus authentication, modeling complete quant trading lifecycle.")
    add_footer(slide, 8)

    # 4 Entity Clusters Cards (2x2 grid)
    cw = Inches(5.66)
    ch = Inches(2.38)

    # Cluster 1: Market Catalog
    c1 = create_card(slide, Inches(0.8), Inches(1.8), cw, ch, "Market Data Cluster", ACCENT_CYAN)
    tb1 = slide.shapes.add_textbox(Inches(1.0), Inches(2.28), cw - Inches(0.4), ch - Inches(0.55))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = 0
    b1 = [
        "**EXCHANGES (1) ───< (N) SECURITIES**",
        "• Primary Key: `exchange_id` | Foreign Key: `securities.exchange_id`",
        "**SECURITIES (1) ───< (N) MARKET_DATA**",
        "• Stores historical OHLCV ticks & bid/ask microstructure quotes.",
        "• Natural Composite Key Constraint: `UNIQUE(security_id, timestamp)`",
    ]
    add_bullet_list(tf1, b1, font_size=9.5, space_after=3)

    # Cluster 2: Trading Blotter
    c2 = create_card(slide, Inches(6.86), Inches(1.8), cw, ch, "Simulated Trading Cluster", ACCENT_MINT)
    tb2 = slide.shapes.add_textbox(Inches(7.06), Inches(2.28), cw - Inches(0.4), ch - Inches(0.55))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = 0
    b2 = [
        "**USERS (1) ───< (N) ORDERS ───> (1) SECURITIES**",
        "• Tracks user-submitted paper orders (MARKET / LIMIT).",
        "**ORDERS (1) ───- (1) TRADES (Executed Blotter)**",
        "• Each executed trade references exactly one parent order.",
        "• Trade execution updates order status and triggers portfolio cash adjustment.",
    ]
    add_bullet_list(tf2, b2, font_size=9.5, space_after=3)

    # Cluster 3: Portfolio & Positions
    c3 = create_card(slide, Inches(0.8), Inches(4.42), cw, ch, "Portfolio & Holdings Cluster", ACCENT_BLUE)
    tb3 = slide.shapes.add_textbox(Inches(1.0), Inches(4.90), cw - Inches(0.4), ch - Inches(0.55))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_top = 0
    b3 = [
        "**USERS (1) ───< (N) PORTFOLIOS**",
        "• Users can manage multiple paper trading portfolios with distinct capital.",
        "**PORTFOLIOS (1) ───< (N) POSITIONS ───> (1) SECURITIES**",
        "• Represents holdings. Constraint: `UNIQUE(portfolio_id, security_id)`",
        "• Tracks quantity, average cost basis, realized P&L, unrealized P&L.",
    ]
    add_bullet_list(tf3, b3, font_size=9.5, space_after=3)

    # Cluster 4: Strategy & Backtesting
    c4 = create_card(slide, Inches(6.86), Inches(4.42), cw, ch, "Strategy & Analytics Cluster", ACCENT_GOLD)
    tb4 = slide.shapes.add_textbox(Inches(7.06), Inches(4.90), cw - Inches(0.4), ch - Inches(0.55))
    tf4 = tb4.text_frame
    tf4.word_wrap = True
    tf4.margin_left = tf4.margin_top = 0
    b4 = [
        "**USERS (1) ───< (N) STRATEGIES ───< (N) BACKTESTS**",
        "• Strategies hold JSON algorithmic configuration parameters.",
        "**BACKTESTS (1) ───- (1) BACKTEST_RESULTS**",
        "• Backtest result stores return, Sharpe, max drawdown, win rate.",
        "**RISK_METRICS:** XOR relation to either `portfolio_id` OR `backtest_id`.",
    ]
    add_bullet_list(tf4, b4, font_size=9.5, space_after=3)

    add_speaker_notes(slide, """
Our Entity-Relationship model encompasses 12 core tables organized into four cohesive clusters:
1. The Market Data Cluster: Exchanges have a 1-to-N relationship with Securities, and Securities have a 1-to-N relationship with Market Data ticks.
2. The Trading Cluster: Users place Orders on Securities. When filled, an Order has a 1-to-1 relationship with an executed Trade record.
3. The Portfolio Cluster: A User can own multiple Portfolios. Each Portfolio has a 1-to-N relationship with Positions, uniquely keyed on portfolio_id and security_id.
4. The Strategy and Analytics Cluster: Users author Strategies, which are run across date ranges as Backtests. Each Backtest produces a 1-to-1 Backtest Result.
All cardinalities follow standard crow's foot notation and match our actual MySQL DDL script.
""")

def build_slide_9_relational_schema(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 9: Relational Schema", "Relational Mapping & Referential Integrity", 
               "Formal conversion of conceptual ER entities into normalized MySQL relational tables.")
    add_footer(slide, 9)

    # Schema Table
    table_shape = slide.shapes.add_table(7, 4, Inches(0.8), Inches(1.8), Inches(11.733), Inches(4.8))
    table = table_shape.table
    table.columns[0].width = Inches(2.0)
    table.columns[1].width = Inches(2.2)
    table.columns[2].width = Inches(3.2)
    table.columns[3].width = Inches(4.333)

    headers = ["Relational Table", "Primary Key", "Foreign Keys & References", "Important Attributes & Unique Keys"]
    for col_idx, text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = TABLE_HEADER_BG
        p = cell.text_frame.paragraphs[0]
        p.text = text
        p.font.name = FONT_HEADING
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = ACCENT_CYAN

    data = [
        ("users", "user_id (BIGINT PK)", "None", "name, email (UNIQUE), role (ENUM), status, created_at"),
        ("exchanges", "exchange_id (BIGINT PK)", "None", "exchange_name, exchange_code (UNIQUE), country, timezone"),
        ("securities", "security_id (BIGINT PK)", "exchange_id -> exchanges", "symbol, security_type, currency, status. UNIQUE(exchange_id, symbol)"),
        ("market_data", "market_data_id (BIGINT PK)", "security_id -> securities", "timestamp, open, high, low, close, volume. UNIQUE(security_id, timestamp)"),
        ("orders", "order_id (BIGINT PK)", "user_id -> users, security_id -> securities", "order_type (MARKET/LIMIT), side (BUY/SELL), quantity, order_price, status"),
        ("trades", "trade_id (BIGINT PK)", "order_id -> orders, security_id -> securities", "trade_side, quantity, execution_price, trade_time, transaction_cost"),
    ]

    for row_idx, row in enumerate(data):
        for col_idx, val in enumerate(row):
            cell = table.cell(row_idx + 1, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = TABLE_ROW_ALT if row_idx % 2 == 1 else CARD_BG
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = FONT_BODY
            p.font.size = Pt(9)
            p.font.color.rgb = ACCENT_CYAN if col_idx == 0 else (ACCENT_MINT if col_idx == 1 else TEXT_WHITE)
            if col_idx in [0, 1]:
                p.font.bold = True

    add_speaker_notes(slide, """
This slide details the translation from our conceptual ER diagram into physical MySQL relational tables.
Every table uses an auto-incrementing surrogate primary key of type BIGINT to optimize B+ tree index depth and joins.
Foreign keys maintain strict referential integrity across the system.
Notice the composite uniqueness constraints:
- In `securities`: UNIQUE(exchange_id, symbol) ensures symbols are unique within an exchange (e.g. RELIANCE on NSE).
- In `market_data`: UNIQUE(security_id, timestamp) prevents multiple price records for the same security at the exact same point in time.
Referential actions prevent orphan records: for example, you cannot delete a security if historical market data exists for it.
""")

def build_slide_10_normalization(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 10: Normalization Analysis", "Rigorous Normalization: 1NF, 2NF, and 3NF", 
               "Step-by-step mathematical decomposition eliminating redundancy and update anomalies.")
    add_footer(slide, 10)

    # Left: 1NF, 2NF, 3NF Definitions Card
    lw = Inches(5.2)
    lh = Inches(4.97)
    c_left = create_card(slide, Inches(0.8), Inches(1.8), lw, lh, "Normalization Proofs", ACCENT_CYAN)
    tb_l = slide.shapes.add_textbox(Inches(1.0), Inches(2.35), lw - Inches(0.4), lh - Inches(0.7))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    tf_l.margin_left = tf_l.margin_top = 0

    norm_steps = [
        "**1. First Normal Form (1NF):**",
        "• All attributes contain atomic, indivisible values.",
        "• No repeating groups or comma-separated lists (e.g. OHLC prices and volumes are discrete scalar columns).",
        "**2. Second Normal Form (2NF):**",
        "• Meets 1NF + every non-key attribute is fully functionally dependent on the entire primary key.",
        "• Since surrogate keys (BIGINT PK) are single-attribute, partial key dependency is mathematically impossible.",
        "• For composite keys like `(security_id, timestamp)`, price metrics depend on the entire tuple.",
        "**3. Third Normal Form (3NF):**",
        "• Meets 2NF + no non-key attribute is transitively dependent on another non-key attribute (X -> Y where Y -> Z).",
        "• QuantDB separates exchanges, securities, users, portfolios, and ticks into isolated relations.",
    ]
    add_bullet_list(tf_l, norm_steps, font_size=9, space_after=4)

    # Right: Concrete Decomposition Case Study Card
    rw = Inches(6.2)
    rh = Inches(4.97)
    c_right = create_card(slide, Inches(6.333), Inches(1.8), rw, rh, "Decomposition Case Study: Market Data", ACCENT_GOLD)
    tb_r = slide.shapes.add_textbox(Inches(6.533), Inches(2.35), rw - Inches(0.4), rh - Inches(0.7))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    tf_r.margin_left = tf_r.margin_top = 0

    case_study = [
        "**Unnormalized Flat Relation (Universal Table):**",
        "`UNNORM_TICKS(tick_id, timestamp, symbol, sec_name, sec_type, currency, exchange_code, exchange_name, country, timezone, open, high, low, close, volume)`",
        "**Severe Anomalies in Flat Design:**",
        "• **Redundancy:** If RELIANCE has 100,000 tick rows, exchange details ('NSE', 'India', 'Asia/Kolkata') are repeated 100,000 times.",
        "• **Insertion Anomaly:** Cannot record a newly listed exchange or security until at least one market price tick occurs.",
        "• **Update Anomaly:** Updating an exchange's timezone requires updating 100,000 rows; failure causes split-brain data.",
        "• **Deletion Anomaly:** Deleting old market ticks inadvertently wipes out the security and exchange definition.",
        "**Decomposed 3NF Structure (QuantDB):**",
        "• `EXCHANGES(exchange_id PK, exchange_name, exchange_code, ...)`",
        "• `SECURITIES(security_id PK, exchange_id FK, symbol, ...)`",
        "• `MARKET_DATA(market_data_id PK, security_id FK, timestamp, ...)`",
    ]
    add_bullet_list(tf_r, case_study, font_size=8.5, space_after=3)

    add_speaker_notes(slide, """
Normalization is one of the most important evaluation criteria in a Semester 3 DBMS viva.
Here we demonstrate formal compliance up to 3NF.
In 1NF, every attribute is atomic — we do not store arrays or comma-delimited price series.
In 2NF, because our tables use single-attribute surrogate keys (like security_id or order_id), partial dependencies cannot exist.
In 3NF, transitive dependencies are completely eliminated.
Consider the case study on the right: in a flat CSV approach, the exchange name and country depend on exchange_id, which in turn depends on security_id. That is a textbook transitive dependency (security_id -> exchange_id -> country).
By decomposing this into EXCHANGES, SECURITIES, and MARKET_DATA, we eliminate redundancy, insertion anomalies, update anomalies, and deletion anomalies.
""")

def build_slide_11_database_design(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 11: Database Design & Constraints", "DDL Specifications, Integrity Constraints & Storage", 
               "Engine-level rules enforcing business integrity across financial transactions.")
    add_footer(slide, 11)

    # 3 Cards Layout
    cw = Inches(3.64)
    ch = Inches(4.97)
    top_pos = Inches(1.8)

    # Card 1: DDL & Types
    c1 = create_card(slide, Inches(0.8), top_pos, cw, ch, "1. DDL & Engine Standard", ACCENT_CYAN)
    tb1 = slide.shapes.add_textbox(Inches(1.0), top_pos + Inches(0.6), cw - Inches(0.4), ch - Inches(0.75))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = 0
    b1 = [
        "**Storage Engine:** MySQL InnoDB engine enabled across all 13 tables for full ACID compliance.",
        "**Charset & Collation:** `utf8mb4_unicode_ci` for international security names and currency symbols.",
        "**Surrogate Identifiers:** `BIGINT AUTO_INCREMENT` for high-throughput row scaling without key collisions.",
        "**Precision Decimals:** Financial prices use `DECIMAL(18,6)` to avoid IEEE floating-point rounding errors.",
    ]
    add_bullet_list(tf1, b1, font_size=9.5, space_after=8)

    # Card 2: Check Constraints
    c2 = create_card(slide, Inches(4.84), top_pos, cw, ch, "2. Declarative CHECK Rules", ACCENT_MINT)
    tb2 = slide.shapes.add_textbox(Inches(5.04), top_pos + Inches(0.6), cw - Inches(0.4), ch - Inches(0.75))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = 0
    b2 = [
        "**Price Sanity Rules:**",
        "• `CHECK (open_price > 0 AND close_price > 0)`",
        "• `CHECK (high_price >= low_price)`",
        "• `CHECK (volume >= 0)`",
        "**Trading Sanity Rules:**",
        "• `CHECK (quantity > 0)` in orders & trades",
        "• `CHECK (execution_price > 0)`",
        "• `CHECK (initial_capital >= 0)`",
        "**Win Rate Range:**",
        "• `CHECK (win_rate >= 0 AND win_rate <= 100)`",
    ]
    add_bullet_list(tf2, b2, font_size=9.5, space_after=6)

    # Card 3: Advanced Constraints
    c3 = create_card(slide, Inches(8.88), top_pos, cw, ch, "3. Exclusive OR (XOR) Rule", ACCENT_GOLD)
    tb3 = slide.shapes.add_textbox(Inches(9.08), top_pos + Inches(0.6), cw - Inches(0.4), ch - Inches(0.75))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_top = 0
    b3 = [
        "**Mutually Exclusive Foreign Key:**",
        "In `risk_metrics`, a risk observation must belong to EITHER a portfolio OR a backtest, but never both or neither:",
        "```sql\nALTER TABLE risk_metrics\nADD CONSTRAINT\nchk_risk_metrics_source\nCHECK (\n  (portfolio_id IS NOT NULL \n   AND backtest_id IS NULL)\n  OR\n  (portfolio_id IS NULL \n   AND backtest_id IS NOT NULL)\n);```",
        "This is an institutional design pattern preventing orphaned or dual-attributed risk metrics.",
    ]
    add_bullet_list(tf3, b3, font_size=8.5, space_after=5)

    add_speaker_notes(slide, """
Notice how our database schema handles data fidelity at the engine level:
1. In finance, floating-point types like FLOAT or DOUBLE cause rounding bugs. We exclusively use DECIMAL(18,6) for financial figures.
2. We enforce business validation via SQL CHECK constraints: High price must be >= Low price, quantities must be positive, and win rates must stay between 0 and 100%.
3. A standout feature is the XOR CHECK constraint on `risk_metrics`. A risk metric can measure a simulated live portfolio OR a backtest, but never both simultaneously. This mutually exclusive constraint is enforced directly by MySQL.
""")

def build_slide_12_programmability(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 12: Database Programmability", "Stored Procedures, Stored Functions & Triggers", 
               "Automating business logic, state transitions, and audit validation inside MySQL.")
    add_footer(slide, 12)

    # 3 Cards Layout
    cw = Inches(3.64)
    ch = Inches(4.97)
    top_pos = Inches(1.8)

    # Card 1: Procedures
    c1 = create_card(slide, Inches(0.8), top_pos, cw, ch, "Stored Procedures (6 Implemented)", ACCENT_CYAN)
    tb1 = slide.shapes.add_textbox(Inches(1.0), top_pos + Inches(0.6), cw - Inches(0.4), ch - Inches(0.75))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = 0
    b1 = [
        "**sp_get_user_portfolios:** Returns all portfolios and cash balances for a given user.",
        "**sp_get_market_data:** Parameterized date-range slice retrieval for a security.",
        "**sp_get_user_orders:** Retrieves full order history with security join for a trader.",
        "**sp_get_security_trades:** Audit blotter of executed trades for a security.",
        "**sp_get_backtest_performance:** Joins backtests, strategies, and results for complete tear-sheets.",
    ]
    add_bullet_list(tf1, b1, font_size=9, space_after=6)

    # Card 2: Functions
    c2 = create_card(slide, Inches(4.84), top_pos, cw, ch, "Stored Functions (5 Implemented)", ACCENT_MINT)
    tb2 = slide.shapes.add_textbox(Inches(5.04), top_pos + Inches(0.6), cw - Inches(0.4), ch - Inches(0.75))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = 0
    b2 = [
        "**fn_portfolio_invested_amount:** Computes invested capital `(initial_capital - current_cash)`.",
        "**fn_position_value:** Computes total holding market value `(quantity * average_price)`.",
        "**fn_win_rate:** Computes win percentage safely avoiding zero-division errors.",
        "**fn_backtest_profit_percentage:** Returns ROI percentage `(total_pnl / initial_capital) * 100`.",
        "**fn_portfolio_total_quantity:** Aggregates all open units held across portfolio positions.",
    ]
    add_bullet_list(tf2, b2, font_size=9, space_after=6)

    # Card 3: Triggers
    c3 = create_card(slide, Inches(8.88), top_pos, cw, ch, "Database Triggers (5 Implemented)", ACCENT_GOLD)
    tb3 = slide.shapes.add_textbox(Inches(9.08), top_pos + Inches(0.6), cw - Inches(0.4), ch - Inches(0.75))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_top = 0
    b3 = [
        "**trg_after_buy_trade:** Deducts `(quantity * price)` from buyer's portfolio cash immediately upon trade insertion.",
        "**trg_after_sell_trade:** Credits cash to seller's portfolio upon trade execution.",
        "**trg_after_trade_order_status:** Automatically sets `order_status = 'FILLED'` when matched trade is inserted.",
        "**trg_before_portfolio_update:** Emits SQLSTATE '45000' error if cash drops below zero.",
        "**trg_before_market_data_insert:** Blocks ticks if High < Low or Open <= 0.",
    ]
    add_bullet_list(tf3, b3, font_size=8.5, space_after=5)

    add_speaker_notes(slide, """
A major strength of QuantDB is database programmability.
Instead of relying solely on Python for data logic, we implemented:
- 6 Stored Procedures: encapsulate common query routines like retrieving backtest performance.
- 5 Stored Functions: deterministic mathematical calculations like position valuation and safe win-rate computation.
- 5 Database Triggers: crucial for automated data consistency. When a trade is inserted into the `trades` table, `trg_after_trade_order_status` automatically transitions the order status to FILLED, and `trg_after_buy_trade` automatically debits the user's cash balance.
If an update attempts to push portfolio cash below zero, `trg_before_portfolio_update` raises SQLSTATE '45000' and aborts the transaction.
""")

def build_slide_13_transactions(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 13: Transaction Management", "ACID Compliance & Concurrency Control", 
               "Pessimistic row-level locking and atomic multi-step execution in simulated finance.")
    add_footer(slide, 13)

    # Left: ACID Properties Card
    lw = Inches(5.2)
    lh = Inches(4.97)
    c_left = create_card(slide, Inches(0.8), Inches(1.8), lw, lh, "ACID Enforcement in QuantDB", ACCENT_CYAN)
    tb_l = slide.shapes.add_textbox(Inches(1.0), Inches(2.35), lw - Inches(0.4), lh - Inches(0.7))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    tf_l.margin_left = tf_l.margin_top = 0

    acid = [
        "**Atomicity:** Order creation, trade blotter generation, and portfolio cash debits are executed inside `START TRANSACTION ... COMMIT`. If any step fails, `ROLLBACK` reverts all modifications.",
        "**Consistency:** All schema integrity constraints (CHECK, FK, UNIQUE) and triggers must evaluate to true before a commit is acknowledged.",
        "**Isolation:** MySQL InnoDB uses `REPEATABLE READ` by default. Multi-version concurrency control (MVCC) ensures queries view consistent snapshots.",
        "**Durability:** Once committed, records are persisted to InnoDB Redo Log (WAL) and disk tablespaces, surviving system crashes.",
    ]
    add_bullet_list(tf_l, acid, font_size=9.5, space_after=8)

    # Right: sp_transfer_portfolio_cash Code Card
    rw = Inches(6.2)
    rh = Inches(4.97)
    c_right = create_card(slide, Inches(6.333), Inches(1.8), rw, rh, "Pessimistic Row Locking (`SELECT ... FOR UPDATE`)", ACCENT_GOLD)
    tb_r = slide.shapes.add_textbox(Inches(6.533), Inches(2.35), rw - Inches(0.4), rh - Inches(0.7))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    tf_r.margin_left = tf_r.margin_top = 0

    sql_code = [
        "**Real Procedure: `sp_transfer_portfolio_cash`**",
        "```sql\nCREATE PROCEDURE sp_transfer_portfolio_cash(\n    IN p_from_portfolio BIGINT,\n    IN p_to_portfolio BIGINT,\n    IN p_amount DECIMAL(18,6)\n)\nBEGIN\n    DECLARE v_from_cash DECIMAL(18,6);\n    START TRANSACTION;\n    -- Pessimistic Lock on Source Portfolio Row\n    SELECT current_cash INTO v_from_cash\n    FROM portfolios WHERE portfolio_id = p_from_portfolio\n    FOR UPDATE;\n\n    IF v_from_cash IS NULL OR v_from_cash < p_amount THEN\n        ROLLBACK;\n        SIGNAL SQLSTATE '45000' \n        SET MESSAGE_TEXT = 'Insufficient cash or invalid id';\n    ELSE\n        UPDATE portfolios SET current_cash = current_cash - p_amount\n        WHERE portfolio_id = p_from_portfolio;\n        UPDATE portfolios SET current_cash = current_cash + p_amount\n        WHERE portfolio_id = p_to_portfolio;\n        COMMIT;\n    END IF;\nEND $$```",
    ]
    add_bullet_list(tf_r, sql_code, font_size=8, space_after=4)

    add_speaker_notes(slide, """
Transaction management is vital for financial consistency.
In slide 13, we demonstrate real transaction management using `sp_transfer_portfolio_cash` from `database/11_transactions.sql`.
Notice the clause: `SELECT current_cash ... FOR UPDATE`.
In a multi-user environment, if two threads attempt to withdraw funds simultaneously, a standard SELECT would read the same balance, leading to a race condition and negative cash.
`FOR UPDATE` places an exclusive write lock on that specific portfolio row until the transaction completes.
If there are insufficient funds, the procedure executes `ROLLBACK` and raises an error.
If funds are sufficient, both accounts update atomically and execute `COMMIT`.
This guarantees strict ACID compliance.
""")

def build_slide_14_sql_queries(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 14: SQL Queries & Views", "Complex Joins, Aggregations & Database Views", 
               "Production queries from the repository demonstrating relational calculus and abstractions.")
    add_footer(slide, 14)

    # Left: Multi-Table JOIN View
    lw = Inches(5.7)
    lh = Inches(4.97)
    c1 = create_card(slide, Inches(0.8), Inches(1.8), lw, lh, "1. Multi-Table JOIN: `vw_backtest_performance`", ACCENT_CYAN)
    tb1 = slide.shapes.add_textbox(Inches(1.0), Inches(2.35), lw - Inches(0.4), lh - Inches(0.7))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = 0

    q1 = [
        "**Purpose:** Joins 4 related entities to build full backtest tear-sheets without multi-query overhead.",
        "```sql\nCREATE OR REPLACE VIEW vw_backtest_performance AS\nSELECT\n    b.backtest_id,\n    st.strategy_name,\n    s.symbol,\n    b.start_date,\n    b.end_date,\n    b.initial_capital,\n    br.total_return,\n    br.total_pnl,\n    br.sharpe_ratio,\n    br.max_drawdown,\n    br.win_rate\nFROM backtests b\nJOIN strategies st\n    ON b.strategy_id = st.strategy_id\nJOIN securities s\n    ON b.security_id = s.security_id\nLEFT JOIN backtest_results br\n    ON b.backtest_id = br.backtest_id;```",
        "**Benefit:** Encapsulates complex joins; UI simply calls `SELECT * FROM vw_backtest_performance WHERE backtest_id = %s`.",
    ]
    add_bullet_list(tf1, q1, font_size=8.5, space_after=4)

    # Right: Correlated Subquery View
    rw = Inches(5.7)
    rh = Inches(4.97)
    c2 = create_card(slide, Inches(6.833), Inches(1.8), rw, rh, "2. Correlated Subquery: `vw_latest_market_data`", ACCENT_MINT)
    tb2 = slide.shapes.add_textbox(Inches(7.033), Inches(2.35), rw - Inches(0.4), rh - Inches(0.7))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = 0

    q2 = [
        "**Purpose:** Returns the latest market tick for every security using a correlated subquery.",
        "```sql\nCREATE OR REPLACE VIEW vw_latest_market_data AS\nSELECT\n    s.security_id,\n    s.symbol,\n    s.security_name,\n    m.timestamp,\n    m.open_price,\n    m.high_price,\n    m.low_price,\n    m.close_price,\n    m.volume\nFROM market_data m\nJOIN securities s\n    ON m.security_id = s.security_id\nWHERE m.timestamp = (\n    SELECT MAX(m2.timestamp)\n    FROM market_data m2\n    WHERE m2.security_id = m.security_id\n);```",
        "**Result:** Instant access to latest prices across the trading terminal without scanning obsolete ticks.",
    ]
    add_bullet_list(tf2, q2, font_size=8.5, space_after=4)

    add_speaker_notes(slide, """
On slide 14, we showcase two of our 9 production database views.
On the left: `vw_backtest_performance` joins four distinct tables — backtests, strategies, securities, and backtest_results using INNER and LEFT JOINs. This gives our application a single abstracted view for strategy performance.
On the right: `vw_latest_market_data` demonstrates a correlated subquery. In financial systems, querying the latest price of every security is a frequent operation. The inner subquery filters for the maximum timestamp corresponding to each specific security_id.
Database views provide security, simplify application queries, and allow underlying schema evolution without breaking frontend contracts.
""")

def build_slide_15_query_optimization(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 15: Query Optimization", "B+ Tree Indexing Strategy & EXPLAIN Analysis", 
               "Transforming O(N) full-table scans into O(log N) index range scans for tick data.")
    add_footer(slide, 15)

    # 3 Cards Layout
    cw = Inches(3.64)
    ch = Inches(4.97)
    top_pos = Inches(1.8)

    # Card 1: Composite Indexing
    c1 = create_card(slide, Inches(0.8), top_pos, cw, ch, "1. Composite Index Design", ACCENT_CYAN)
    tb1 = slide.shapes.add_textbox(Inches(1.0), top_pos + Inches(0.6), cw - Inches(0.4), ch - Inches(0.75))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = 0
    b1 = [
        "**idx_market_data_security_time:**",
        "`ON market_data(security_id, timestamp)`",
        "• High cardinality filter index tailored for historical backtesting queries.",
        "• **Leftmost Prefix Rule:** Supports queries filtering by `security_id` alone, as well as range queries on `(security_id, timestamp)`.",
        "• Eliminates sort overhead during chronological tick ordering (`ORDER BY timestamp`).",
    ]
    add_bullet_list(tf1, b1, font_size=9.5, space_after=6)

    # Card 2: Filter & Foreign Key Indexes
    c2 = create_card(slide, Inches(4.84), top_pos, cw, ch, "2. Foreign Key & Status Indexes", ACCENT_MINT)
    tb2 = slide.shapes.add_textbox(Inches(5.04), top_pos + Inches(0.6), cw - Inches(0.4), ch - Inches(0.75))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = 0
    b2 = [
        "**Orders & Blotters:**",
        "• `idx_orders_user` on `orders(user_id)`",
        "• `idx_orders_status` on `orders(order_status)`",
        "• `idx_orders_time` on `orders(order_time)`",
        "**Trade Execution:**",
        "• `idx_trades_order` on `trades(order_id)`",
        "• `idx_trades_security` on `trades(security_id)`",
        "• Speeds up joins and portfolio P&L aggregation by orders of magnitude.",
    ]
    add_bullet_list(tf2, b2, font_size=9.5, space_after=6)

    # Card 3: EXPLAIN Execution Plan
    c3 = create_card(slide, Inches(8.88), top_pos, cw, ch, "3. EXPLAIN Plan Analysis", ACCENT_GOLD)
    tb3 = slide.shapes.add_textbox(Inches(9.08), top_pos + Inches(0.6), cw - Inches(0.4), ch - Inches(0.75))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_top = 0
    b3 = [
        "**Without Index (Full Table Scan):**",
        "• `type: ALL` | `rows: 100,000+`",
        "• `Extra: Using where; Using filesort`",
        "• Execution: High CPU, high disk I/O.",
        "**With B+ Tree Index (Range Scan):**",
        "• `type: ref / range` | `rows: 250`",
        "• `key: idx_market_data_security_time`",
        "• `Extra: Using index condition`",
        "• Query latency drops from ~180ms to < 2ms.",
    ]
    add_bullet_list(tf3, b3, font_size=9, space_after=6)

    add_speaker_notes(slide, """
Slide 15 addresses query optimization and database indexing.
In financial databases, the `market_data` table can quickly grow to millions of rows.
Without indexing, a query fetching 60 days of historical data for RELIANCE performs a full table scan of type ALL, requiring expensive disk I/O and filesort.
We implemented a composite B+ Tree index on `(security_id, timestamp)` in `07_indexes.sql`.
Under MySQL's B+ Tree architecture, this creates a compound search tree that immediately locates the security, and then traverses leaf nodes for the date range.
Using `EXPLAIN`, we confirmed the execution plan changes from `type: ALL` to `type: ref / range`, reducing row inspection from thousands to only the exact rows needed, dropping query latency to under 2 milliseconds.
""")

def build_slide_16_ui_overview(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 16: Research Terminal UI", "Streamlit Institutional Terminal Architecture", 
               "High-density financial ergonomics, dark theme, and dual execution mode support.")
    add_footer(slide, 16)

    # 4 Grid Cards of 8 Pages (2x2)
    cw = Inches(5.66)
    ch = Inches(2.38)

    # Grid 1: Overview & Market Data
    c1 = create_card(slide, Inches(0.8), Inches(1.8), cw, ch, "1. Overview & Market Data Workspaces", ACCENT_CYAN)
    tb1 = slide.shapes.add_textbox(Inches(1.0), Inches(2.28), cw - Inches(0.4), ch - Inches(0.55))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = 0
    b1 = [
        "**Overview Dashboard (`app.py`):** High-level KPI cards, database health status, market summary, and recent platform activity.",
        "**Market Data (`market_data.py`):** Interactive Plotly candlestick charts, volume bars, OHLC summary table, and microstructure metrics (bid-ask spread, order book depth).",
    ]
    add_bullet_list(tf1, b1, font_size=9.5, space_after=5)

    # Grid 2: Trading & Portfolio
    c2 = create_card(slide, Inches(6.86), Inches(1.8), cw, ch, "2. Trading & Portfolio Workspaces", ACCENT_MINT)
    tb2 = slide.shapes.add_textbox(Inches(7.06), Inches(2.28), cw - Inches(0.4), ch - Inches(0.55))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = 0
    b2 = [
        "**Paper Trading Desk (`trading.py`):** Order execution ticket supporting MARKET and LIMIT orders, live order book, full order history blotter.",
        "**Portfolio Tracker (`portfolio.py`):** Real-time asset valuation, cash vs invested allocation, position table with realized & unrealized P&L.",
    ]
    add_bullet_list(tf2, b2, font_size=9.5, space_after=5)

    # Grid 3: Strategies & Backtesting
    c3 = create_card(slide, Inches(0.8), Inches(4.42), cw, ch, "3. Strategy & Backtest Workspaces", ACCENT_BLUE)
    tb3 = slide.shapes.add_textbox(Inches(1.0), Inches(4.90), cw - Inches(0.4), ch - Inches(0.55))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_top = 0
    b3 = [
        "**Strategy Catalog (`strategies.py`):** Algorithmic catalog (SMA Crossover, Momentum, Mean Reversion) with dynamic JSON parameter sliders.",
        "**Backtesting Engine (`backtesting.py`):** Date range historical simulation, equity curve visualization, drawdown chart, and trade execution log.",
    ]
    add_bullet_list(tf3, b3, font_size=9.5, space_after=5)

    # Grid 4: Reports, Admin & Dual Mode
    c4 = create_card(slide, Inches(6.86), Inches(4.42), cw, ch, "4. Governance, Reports & Dual Mode", ACCENT_GOLD)
    tb4 = slide.shapes.add_textbox(Inches(7.06), Inches(4.90), cw - Inches(0.4), ch - Inches(0.55))
    tf4 = tb4.text_frame
    tf4.word_wrap = True
    tf4.margin_left = tf4.margin_top = 0
    b4 = [
        "**Risk Reports (`reports.py`):** Institutional factor tearsheets, Sharpe ratio, volatility, and maximum drawdown metrics.",
        "**Admin & Topology (`admin.py`):** Master exchange/security catalog, user verification, and database connection status.",
        "**Dual Mode Architecture:** `DATA_MODE = 'real'` (direct MySQL) vs `'mock'` (autonomous simulation for offline evaluation).",
    ]
    add_bullet_list(tf4, b4, font_size=9.5, space_after=5)

    add_speaker_notes(slide, """
Slide 16 details our frontend architecture built in Streamlit.
We designed an institutional dark terminal interface inspired by Bloomberg and FactSet systems.
It consists of 8 distinct application pages:
1. Overview Dashboard with KPI telemetry.
2. Market Data with Plotly OHLCV candlesticks and microstructure depth.
3. Paper Trading desk with order execution tickets.
4. Portfolio Tracker showing capital allocation and position P&L.
5. Strategy Catalog with interactive parameter controls.
6. Backtesting Engine rendering equity curves and trade blotters.
7. Reports delivering institutional risk tear-sheets.
8. Admin page for database governance and master catalog management.
Crucially, the UI supports a Dual-Mode Architecture: toggling between 'real' MySQL database mode and 'mock' simulation mode seamlessly.
""")

def build_slide_17_screenshots(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 17: Screenshots & Workflows", "Application Walkthrough & System Verification", 
               "System interface panels and database verification workflows across key modules.")
    add_footer(slide, 17)

    # 4 Mock UI Panels representing genuine screens
    cw = Inches(5.66)
    ch = Inches(2.38)

    # Panel 1: Overview & Metrics
    c1 = create_card(slide, Inches(0.8), Inches(1.8), cw, ch, "Panel A: Platform Overview & System Status", ACCENT_CYAN)
    tb1 = slide.shapes.add_textbox(Inches(1.0), Inches(2.28), cw - Inches(0.4), ch - Inches(0.55))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = 0
    b1 = [
        "**UI Layout:** System status indicator showing 'DATABASE CONNECTED' (Aiven MySQL / MySQL 8.x).",
        "**Key Metrics Displayed:** Active Portfolios: 5 | Total Orders: 10+ | Seed Securities: 10 | System Health: 100%.",
        "**Underlying SQL:** Calls `vw_portfolio_summary` and `COUNT(*)` aggregations from `orders` and `securities`.",
        "[Screenshot Guide: Insert Streamlit Overview Dashboard showing KPI cards and database badge]",
    ]
    add_bullet_list(tf1, b1, font_size=9, space_after=4)

    # Panel 2: Market Data Candlestick
    c2 = create_card(slide, Inches(6.86), Inches(1.8), cw, ch, "Panel B: Market Data & Microstructure", ACCENT_MINT)
    tb2 = slide.shapes.add_textbox(Inches(7.06), Inches(2.28), cw - Inches(0.4), ch - Inches(0.55))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = 0
    b2 = [
        "**UI Layout:** Security selector (RELIANCE, TCS, INFY), date range picker, and Plotly candlestick chart.",
        "**Microstructure Depth:** Bid-Ask spread display (`ask_price - bid_price`), volume histogram, and OHLC data grid.",
        "**Underlying SQL:** Executes `sp_get_market_data(p_security_id, p_start, p_end)` utilizing `idx_market_data_security_time`.",
        "[Screenshot Guide: Insert Plotly Candlestick chart for RELIANCE (5-day daily bars)]",
    ]
    add_bullet_list(tf2, b2, font_size=9, space_after=4)

    # Panel 3: Trading Blotter
    c3 = create_card(slide, Inches(0.8), Inches(4.42), cw, ch, "Panel C: Trading Desk & Executed Trades", ACCENT_BLUE)
    tb3 = slide.shapes.add_textbox(Inches(1.0), Inches(4.90), cw - Inches(0.4), ch - Inches(0.55))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_top = 0
    b3 = [
        "**UI Layout:** Order placement ticket (Side, Quantity, Order Type: MARKET/LIMIT), submission button.",
        "**Blotter Verification:** Order table showing transition from 'PENDING' to 'FILLED' with trade timestamp and execution cost.",
        "**Underlying SQL:** `INSERT INTO orders ...` followed by trigger `trg_after_trade_order_status` updating status.",
        "[Screenshot Guide: Insert Trading Blotter showing order history and executed trades table]",
    ]
    add_bullet_list(tf3, b3, font_size=9, space_after=4)

    # Panel 4: Backtesting Equity Curve
    c4 = create_card(slide, Inches(6.86), Inches(4.42), cw, ch, "Panel D: Strategy Backtesting & Risk Report", ACCENT_GOLD)
    tb4 = slide.shapes.add_textbox(Inches(7.06), Inches(4.90), cw - Inches(0.4), ch - Inches(0.55))
    tf4 = tb4.text_frame
    tf4.word_wrap = True
    tf4.margin_left = tf4.margin_top = 0
    b4 = [
        "**UI Layout:** Moving Average Crossover configuration (Short=20, Long=50), capital input: 1,000,000.",
        "**Visual Output:** Cumulative equity curve, underwater drawdown curve, Sharpe ratio, and win-rate badge.",
        "**Underlying SQL:** Persistence of backtest results via `INSERT INTO backtest_results ...` and query via `vw_backtest_performance`.",
        "[Screenshot Guide: Insert Backtest Performance screen with equity curve & Sharpe metric]",
    ]
    add_bullet_list(tf4, b4, font_size=9, space_after=4)

    add_speaker_notes(slide, """
Slide 17 illustrates the primary user workflows and provides clear captions matching our project implementation.
Panel A shows the Overview Dashboard, which reads directly from our views and provides real-time system health.
Panel B displays the Market Data interface, showing interactive candlesticks and microstructure metrics for securities like RELIANCE, fetched via our stored procedure.
Panel C demonstrates the Trading Desk: when an order is placed, our database trigger updates the order status to FILLED and registers the executed trade in the blotter.
Panel D demonstrates the Backtesting workflow, which computes the equity curve, total P&L, and Sharpe ratio, persisting these into `backtest_results`.
Evaluators can view these exact pages running locally or inspect the tables in MySQL Workbench.
""")

def build_slide_18_testing(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 18: Testing & Verification", "Comprehensive Automated Testing Strategy", 
               "235 passing tests verified via Pytest across unit, integration, and database suites.")
    add_footer(slide, 18)

    # Left: Test Matrix Table
    table_shape = slide.shapes.add_table(6, 4, Inches(0.8), Inches(1.8), Inches(7.5), Inches(4.8))
    table = table_shape.table
    table.columns[0].width = Inches(2.2)
    table.columns[1].width = Inches(1.4)
    table.columns[2].width = Inches(2.5)
    table.columns[3].width = Inches(1.4)

    headers = ["Test Suite File", "Tests Run", "Scope & Functionality Tested", "Status"]
    for col_idx, text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = TABLE_HEADER_BG
        p = cell.text_frame.paragraphs[0]
        p.text = text
        p.font.name = FONT_HEADING
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = ACCENT_CYAN

    data = [
        ("test_analytics.py", "32 tests", "Returns, Volatility, Sharpe, Drawdown, Microstructure", "32 Passed"),
        ("test_trading.py", "40 tests", "Order validation, Trade execution, Balance checks", "40 Passed"),
        ("test_backtesting.py", "39 tests", "SMA Crossover, Momentum, Mean Reversion execution", "39 Passed"),
        ("test_services.py", "31 tests", "Service layer delegation, Provider switching", "31 Passed"),
        ("test_auth & signup.py", "47 tests", "Password hashing, OTP verification, Rate limiting", "47 Passed"),
    ]

    for row_idx, row in enumerate(data):
        for col_idx, val in enumerate(row):
            cell = table.cell(row_idx + 1, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = TABLE_ROW_ALT if row_idx % 2 == 1 else CARD_BG
            p = cell.text_frame.paragraphs[0]
            p.text = val
            p.font.name = FONT_BODY
            p.font.size = Pt(9.5)
            p.font.color.rgb = ACCENT_MINT if col_idx == 3 else (TEXT_WHITE if col_idx == 0 else TEXT_MUTED)
            if col_idx in [0, 3]:
                p.font.bold = True

    # Right: Test Summary Metrics Card
    cw = Inches(3.9)
    ch = Inches(4.8)
    c_right = create_card(slide, Inches(8.633), Inches(1.8), cw, ch, "Verified Test Telemetry", ACCENT_CYAN)
    tb = slide.shapes.add_textbox(Inches(8.833), Inches(2.35), cw - Inches(0.4), ch - Inches(0.7))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = 0

    stats = [
        "**Verified Pytest Execution:**",
        "• **Total Tests Collected:** 238 tests",
        "• **Passing Tests:** 235 passed (98.7% pass rate)",
        "• **Execution Time:** ~3.18 minutes",
        "**Test Coverage Categories:**",
        "• **Unit Tests:** Analytics engine, microstructure formulas, backtesting logic.",
        "• **Database Tests:** Connection pooling, query construction, parameter binding.",
        "• **Regression Tests:** Trading real regression and UI dataframe rendering.",
        "• **Security Tests:** PBKDF2 password hashing, OTP expiry, domain validation.",
    ]
    add_bullet_list(tf, stats, font_size=9.5, space_after=6)

    add_speaker_notes(slide, """
On slide 18, we present our verified testing strategy and results.
We believe software quality should be verified by automated telemetry rather than claims.
Running pytest across the repository confirms:
- 235 tests pass out of 238 total tests across 12 distinct test suites.
- 32 tests in `test_analytics.py` verify mathematical precision for Sharpe ratio, volatility, and max drawdown.
- 40 tests in `test_trading.py` verify paper trading order validation, trade matching, and cash deduction.
- 39 tests in `test_backtesting.py` test algorithmic event loops.
- 47 tests across auth and signup OTP suites verify secure password hashing and rate limiting.
This rigor ensures our database integration and quantitative engine are robust and reproducible.
""")

def build_slide_19_results(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 19: Measurable Results", "Concrete Implementation Outputs & Artifacts", 
               "Verified project deliverables deployed and operating in the local environment.")
    add_footer(slide, 19)

    # 4 Deliverables Cards (2x2)
    cw = Inches(5.66)
    ch = Inches(2.38)

    # Grid 1: Relational Schema
    c1 = create_card(slide, Inches(0.8), Inches(1.8), cw, ch, "1. Relational Database Deployment", ACCENT_CYAN)
    tb1 = slide.shapes.add_textbox(Inches(1.0), Inches(2.28), cw - Inches(0.4), ch - Inches(0.55))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = 0
    b1 = [
        "**13 Tables Deployed:** Fully structured with InnoDB storage engine, primary keys, and foreign keys.",
        "**Integrity Rules Enforced:** Verified CHECK constraints on prices, quantities, and XOR rule on `risk_metrics`.",
        "**14 SQL Script Files:** Structured DDL, DML, indexes, views, procedures, functions, triggers, and transactions.",
    ]
    add_bullet_list(tf1, b1, font_size=9.5, space_after=5)

    # Grid 2: Seed Data
    c2 = create_card(slide, Inches(6.86), Inches(1.8), cw, ch, "2. Populated Financial Catalogs", ACCENT_MINT)
    tb2 = slide.shapes.add_textbox(Inches(7.06), Inches(2.28), cw - Inches(0.4), ch - Inches(0.55))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = 0
    b2 = [
        "**Exchanges & Securities:** 4 Exchanges (NSE, BSE, NASDAQ, NYSE) and 10 active securities (RELIANCE, TCS, AAPL, etc.).",
        "**Historical Market Ticks:** Seeded 5-day daily OHLCV series for top stocks (e.g. RELIANCE 1410.00 -> 1468.00).",
        "**User Accounts & Portfolios:** Seeded test users (Admin, Researchers, Traders) with 5 distinct portfolios.",
    ]
    add_bullet_list(tf2, b2, font_size=9.5, space_after=5)

    # Grid 3: Quant Backtest Outputs
    c3 = create_card(slide, Inches(0.8), Inches(4.42), cw, ch, "3. Backtest & Analytics Outputs", ACCENT_BLUE)
    tb3 = slide.shapes.add_textbox(Inches(1.0), Inches(4.90), cw - Inches(0.4), ch - Inches(0.55))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_top = 0
    b3 = [
        "**Strategy Simulation:** Moving Average Crossover (20/50 SMA) and Momentum backtest runs executed successfully.",
        "**Calculated Metrics:** Total P&L, Annualized Volatility, Sharpe Ratio, Maximum Drawdown, and Win Rate.",
        "**Result Persistence:** Results written to `backtest_results` and queried through `vw_backtest_performance`.",
    ]
    add_bullet_list(tf3, b3, font_size=9.5, space_after=5)

    # Grid 4: Full-Stack Terminal
    c4 = create_card(slide, Inches(6.86), Inches(4.42), cw, ch, "4. Functional Research Terminal", ACCENT_GOLD)
    tb4 = slide.shapes.add_textbox(Inches(7.06), Inches(4.90), cw - Inches(0.4), ch - Inches(0.55))
    tf4 = tb4.text_frame
    tf4.word_wrap = True
    tf4.margin_left = tf4.margin_top = 0
    b4 = [
        "**Streamlit Dashboard Active:** 8 dedicated pages operating with high-density financial layout and Plotly charts.",
        "**Order Execution Flow:** Simulated market order placement executes, creates trade records, and updates cash balances.",
        "**Test Verification:** 235 passing tests in the automated pytest suite confirming end-to-end stability.",
    ]
    add_bullet_list(tf4, b4, font_size=9.5, space_after=5)

    add_speaker_notes(slide, """
Slide 19 outlines our concrete, verifiable implementation outputs:
1. We deployed all 13 relational tables in MySQL with declarative constraints and foreign keys.
2. We seeded real-world financial master data: 4 major global exchanges, 10 blue-chip equities, and multi-day OHLCV market ticks.
3. Our analytics layer executed quantitative trading strategies, successfully computing and persisting risk metrics.
4. Our Streamlit research terminal is fully operational with 8 interconnected pages, validated by 235 passing automated tests.
Everything shown is working software, verified against our codebase.
""")

def build_slide_20_dbms_checklist(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 20: DBMS Concepts Demonstrated", "Curriculum Alignment & Verification Checklist", 
               "Direct mapping of Semester-3 DBMS lab concepts to QuantDB code implementation.")
    add_footer(slide, 20)

    # Checklist Table
    table_shape = slide.shapes.add_table(13, 3, Inches(0.8), Inches(1.8), Inches(11.733), Inches(4.9))
    table = table_shape.table
    table.columns[0].width = Inches(4.2)
    table.columns[1].width = Inches(5.8)
    table.columns[2].width = Inches(1.733)

    headers = ["DBMS Syllabus Concept", "QuantDB Implementation Evidence in Repository", "Status"]
    for col_idx, text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = TABLE_HEADER_BG
        p = cell.text_frame.paragraphs[0]
        p.text = text
        p.font.name = FONT_HEADING
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = ACCENT_CYAN

    items = [
        ("Entity-Relationship (ER) Modeling", "12+ core entities mapped with 1:1, 1:N cardinalities in `docs/er_diagram.md`", "[x] Implemented"),
        ("Relational Schema Conversion", "Converted ER entities to 13 relational tables in `database/02_create_tables.sql`", "[x] Implemented"),
        ("Database Normalization (1NF, 2NF, 3NF)", "Formal decomposition of flat market data into 3NF in `docs/normalization.md`", "[x] Implemented"),
        ("Primary & Foreign Key Constraints", "Surrogate BIGINT PKs and referential FKs across all 13 tables (`03_constraints.sql`)", "[x] Implemented"),
        ("Integrity Constraints (CHECK, ENUM, UNIQUE)", "CHECK(high >= low), XOR rule on risk_metrics, ENUMs for roles and order types", "[x] Implemented"),
        ("Multi-Table SQL Joins", "4-table joins in views combining backtests, strategies, securities, and results", "[x] Implemented"),
        ("Aggregate Functions & Grouping", "SUM, AVG, COUNT in portfolio summaries and trading blotters (`queries.py`)", "[x] Implemented"),
        ("Database Views (9 Views)", "Production views like `vw_backtest_performance`, `vw_latest_market_data` (`06_views.sql`)", "[x] Implemented"),
        ("B+ Tree Indexing & EXPLAIN", "Composite index `(security_id, timestamp)` and foreign key indexes (`07_indexes.sql`)", "[x] Implemented"),
        ("Stored Procedures & Functions", "6 Stored Procedures and 5 Stored Functions for business logic (`08_` & `09_`)", "[x] Implemented"),
        ("Automated Triggers", "5 Triggers for automatic cash deductions and order status transitions (`10_triggers.sql`)", "[x] Implemented"),
        ("ACID Transactions & Row Locking", "`START TRANSACTION`, `SELECT ... FOR UPDATE`, and `ROLLBACK` in `11_transactions.sql`", "[x] Implemented"),
    ]

    for row_idx, (c_name, c_evid, c_stat) in enumerate(items):
        r_idx = row_idx + 1
        # Col 0
        c0 = table.cell(r_idx, 0)
        c0.fill.solid()
        c0.fill.fore_color.rgb = TABLE_ROW_ALT if row_idx % 2 == 1 else CARD_BG
        p0 = c0.text_frame.paragraphs[0]
        p0.text = c_name
        p0.font.name = FONT_BODY
        p0.font.size = Pt(8.5)
        p0.font.bold = True
        p0.font.color.rgb = TEXT_WHITE

        # Col 1
        c1 = table.cell(r_idx, 1)
        c1.fill.solid()
        c1.fill.fore_color.rgb = TABLE_ROW_ALT if row_idx % 2 == 1 else CARD_BG
        p1 = c1.text_frame.paragraphs[0]
        p1.text = c_evid
        p1.font.name = FONT_BODY
        p1.font.size = Pt(8.5)
        p1.font.color.rgb = TEXT_MUTED

        # Col 2
        c2 = table.cell(r_idx, 2)
        c2.fill.solid()
        c2.fill.fore_color.rgb = TABLE_ROW_ALT if row_idx % 2 == 1 else CARD_BG
        p2 = c2.text_frame.paragraphs[0]
        p2.text = c_stat
        p2.font.name = FONT_HEADING
        p2.font.size = Pt(8.5)
        p2.font.bold = True
        p2.font.color.rgb = ACCENT_MINT

    add_speaker_notes(slide, """
Slide 20 is our comprehensive DBMS concepts checklist.
Every single topic required in our Semester 3 DBMS syllabus is not just theoretically discussed, but physically implemented in the project code:
- ER modeling and Relational conversion.
- Normalization up to 3NF.
- Declarative integrity constraints including CHECK, ENUM, and composite UNIQUE keys.
- Complex multi-table JOINs and aggregations.
- 9 Production Database Views.
- B+ Tree indexing evaluated via EXPLAIN.
- Stored Procedures, Functions, and Triggers.
- ACID transactions with pessimistic row locking using SELECT ... FOR UPDATE.
- Full-stack Python database integration with connection pooling.
This provides a complete, cohesive demonstration of database principles.
""")

def build_slide_21_limitations_future(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 21: Limitations & Future Scope", "Engineering Constraints & Roadmap", 
               "Clear boundary between current academic implementation and planned industrial enhancements.")
    add_footer(slide, 21)

    # 2 Cards: Left: Limitations, Right: Future Scope
    cw = Inches(5.66)
    ch = Inches(4.97)
    top_pos = Inches(1.8)

    # Card 1: Limitations
    c1 = create_card(slide, Inches(0.8), top_pos, cw, ch, "System Limitations (Current Scope)", ACCENT_GOLD)
    tb1 = slide.shapes.add_textbox(Inches(1.0), top_pos + Inches(0.6), cw - Inches(0.4), ch - Inches(0.75))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = 0
    b1 = [
        "**Academic Paper Trading Only:** Platform does not connect to live exchange gateways (e.g. FIX protocol) and executes zero real-money transactions.",
        "**Historical Data Granularity:** Currently stores daily/interval OHLCV ticks; does not store nanosecond Level-3 full order book market depth.",
        "**Simplified Execution Model:** Simulated order matching assumes immediate liquidity and zero price slippage at historical close.",
        "**Cloud Database Latency:** Remote Aiven MySQL instances introduce WAN round-trip latency (~40-80ms) compared to co-located high-frequency trading setups.",
        "**Single Node Deployment:** Relational engine runs on a single primary node; does not utilize distributed sharding or read-replicas.",
    ]
    add_bullet_list(tf1, b1, font_size=9.5, space_after=8)

    # Card 2: Future Scope
    c2 = create_card(slide, Inches(6.86), top_pos, cw, ch, "Future Scope & Enhancements", ACCENT_MINT)
    tb2 = slide.shapes.add_textbox(Inches(7.06), top_pos + Inches(0.6), cw - Inches(0.4), ch - Inches(0.75))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = 0
    b2 = [
        "**Real-Time WebSocket Ingestion:** Integrate live market data feeds via WebSockets for real-time tick streaming into MySQL.",
        "**Advanced Quantitative Models:** Implement institutional risk analytics such as Value at Risk (VaR), Conditional VaR, and Monte Carlo simulations.",
        "**Algorithmic Execution Bots:** Expand order matching to include TWAP (Time-Weighted) and VWAP (Volume-Weighted) algorithmic execution.",
        "**Automated Pipeline & ETL:** Build scheduled cron ingestion pipelines fetching daily corporate actions and split adjustments.",
        "**Read Replicas & Connection Partitioning:** Separate heavy backtesting read queries onto dedicated MySQL read replicas to protect OLTP transactions.",
    ]
    add_bullet_list(tf2, b2, font_size=9.5, space_after=8)

    add_speaker_notes(slide, """
On slide 21, we maintain technical honesty regarding our system's boundaries:
Our current implementation is an academic paper trading system. We do not pretend to have live broker routing or real-money execution.
Our market data is daily/interval OHLCV rather than nanosecond high-frequency data feeds, and our order fill model assumes ideal liquidity without slippage.
For future scope, the platform can naturally evolve:
- Adding real-time WebSocket feeds.
- Implementing advanced risk models like Value at Risk (VaR) and Conditional VaR.
- Supporting algorithmic execution algorithms like TWAP and VWAP.
- Introducing MySQL read replicas to separate heavy analytical backtesting queries from transactional paper trading writes.
""")

def build_slide_22_conclusion_viva(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    apply_background(slide)
    add_header(slide, "Section 22: Conclusion & Viva Prep", "Summary of Achievements & Evaluator Q&A", 
               "Core takeaways and rapid-fire viva explanations for DBMS evaluation defense.")
    add_footer(slide, 22)

    # Left: Summary Card
    lw = Inches(5.4)
    lh = Inches(4.97)
    c_left = create_card(slide, Inches(0.8), Inches(1.8), lw, lh, "Summary of Achievements", ACCENT_CYAN)
    tb_l = slide.shapes.add_textbox(Inches(1.0), Inches(2.35), lw - Inches(0.4), lh - Inches(0.7))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    tf_l.margin_left = tf_l.margin_top = 0

    summary = [
        "**Database Problem Solved:** Eliminated financial data fragmentation, anomalies, and inconsistencies through a centralized 3NF relational database.",
        "**Comprehensive DBMS Demonstration:** Successfully deployed 13 tables, primary/foreign keys, CHECK constraints, views, indexes, stored procedures, functions, triggers, and ACID transactions.",
        "**Full-Stack Engineering:** Seamlessly integrated MySQL 8.x with Python, Pandas, and Streamlit, verified by 235 passing automated tests.",
        "**Academic & Practical Synergy:** Demonstrated how textbook database concepts directly empower quantitative research and simulated financial analytics.",
        "**Thank You:** Open to questions, architecture inspection, and live code demonstration.",
    ]
    add_bullet_list(tf_l, summary, font_size=9.5, space_after=8)

    # Right: Top Viva Questions Card
    rw = Inches(6.0)
    rh = Inches(4.97)
    c_right = create_card(slide, Inches(6.533), Inches(1.8), rw, rh, "Viva Defense: Key Technical Q&A", ACCENT_GOLD)
    tb_r = slide.shapes.add_textbox(Inches(6.733), Inches(2.35), rw - Inches(0.4), rh - Inches(0.7))
    tf_r = tb_r.text_frame
    tf_r.word_wrap = True
    tf_r.margin_left = tf_r.margin_top = 0

    qa = [
        "**Q1: Why choose InnoDB instead of MyISAM?**",
        "• *Answer:* InnoDB supports ACID transactions, row-level locking (`SELECT ... FOR UPDATE`), and foreign keys. MyISAM only supports table-level locking and lacks transaction rollback capabilities.",
        "**Q2: How does `SELECT ... FOR UPDATE` prevent race conditions?**",
        "• *Answer:* It acquires an exclusive write lock on the target row during the SELECT, blocking concurrent transactions from reading or modifying the balance until COMMIT.",
        "**Q3: Why create a composite index on `(security_id, timestamp)`?**",
        "• *Answer:* It leverages the B+ Tree leftmost prefix rule to filter by security first, and instantly perform range scans on timestamps, eliminating full table scans.",
        "**Q4: What happens if a trigger encounters invalid data?**",
        "• *Answer:* Triggers like `trg_before_portfolio_update` emit `SIGNAL SQLSTATE '45000'`, which halts execution and forces an automatic transaction rollback.",
    ]
    add_bullet_list(tf_r, qa, font_size=8.5, space_after=4)

    add_speaker_notes(slide, """
To conclude:
QuantDB demonstrates that database management principles are not just theoretical textbook concepts, but the essential foundation for reliable financial engineering.
By designing a 3NF relational schema with declarative constraints, B+ Tree indexing, stored procedures, triggers, and ACID transactions, we built a robust research platform that powers automated trading simulations and risk analytics.
On the right, we have anticipated the most common technical questions our DBMS evaluators might ask regarding storage engine selection, row-level locking, composite indexing, and trigger error signals.
Thank you for your time and attention. We are ready to take your questions and demonstrate the live system.
""")

def main():
    print("Generating QuantDB_DBMS_Project_Sem3.pptx...")
    prs = create_deck()

    build_slide_1_title(prs)
    build_slide_2_problem(prs)
    build_slide_3_objectives(prs)
    build_slide_4_motivation(prs)
    build_slide_5_roles(prs)
    build_slide_6_functional_requirements(prs)
    build_slide_7_architecture(prs)
    build_slide_8_er_diagram(prs)
    build_slide_9_relational_schema(prs)
    build_slide_10_normalization(prs)
    build_slide_11_database_design(prs)
    build_slide_12_programmability(prs)
    build_slide_13_transactions(prs)
    build_slide_14_sql_queries(prs)
    build_slide_15_query_optimization(prs)
    build_slide_16_ui_overview(prs)
    build_slide_17_screenshots(prs)
    build_slide_18_testing(prs)
    build_slide_19_results(prs)
    build_slide_20_dbms_checklist(prs)
    build_slide_21_limitations_future(prs)
    build_slide_22_conclusion_viva(prs)

    output_path = "/Users/darshilprajapati/QuantDB-1/QuantDB_DBMS_Project_Sem3.pptx"
    prs.save(output_path)
    print(f"Successfully generated presentation: {output_path}")

if __name__ == "__main__":
    main()

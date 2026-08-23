# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

KazKaz AI is a Turkish-language financial analysis SaaS platform built with Streamlit. It provides SMEs with financial health scoring, AI-powered analysis, cash flow/debt management, investment tracking, budgeting, customer analytics, and PDF reporting. It includes a semi-autonomous CFO AI agent.

## Commands

```bash
# Run the app
streamlit run app.py

# Run tests
python -m pytest test_engines.py -v
# or
python test_engines.py

# Install dependencies
pip install -r requirements-2.txt
```

## Architecture

The codebase follows a strict **engine/UI separation pattern**:

- **Engine files** (`*_engine.py`) — Pure computation, no Streamlit imports. Each engine handles a specific domain:
  - `financial_engine.py` — Core: DataLoader, health score (0-100), revenue/expense/profit analysis
  - `gemini_engine.py` — AI provider abstraction (Groq default, Gemini fallback). Class is called `GeminiEngine` regardless of provider
  - `cfo_agent.py` — Semi-autonomous CFO agent with tool-based architecture (FinancialHealthTool, CashFlowAlertTool, etc.)
  - `cashflow_engine.py`, `debt_engine.py`, `budget_engine.py`, `customer_engine.py`, `sector_engine.py`, `investment_engine.py`, `forecast_engine.py`

- **UI files** (`*_ui.py`) — Streamlit rendering, each exposes a `show_*_tab()` function consumed by `app.py`

- **`app.py`** — Main entry point. Uses try/except imports with `*_OK` boolean flags for graceful degradation when optional modules are unavailable

- **`design_system.py`** — Design tokens (`DS` class) and global CSS injection (`inject_css()`). All UI files import: `from design_system import DS, kpi, sec, alert, fmt, PLOTLY_THEME`

- **`ui_components.py`** — Reusable UI primitives (KPI cards, section headers, alerts, health bars). Premium navy/corporate theme

## Key Conventions

- **Language**: All user-facing text, variable names, column headers, and comments are in Turkish
- **Data format**: Input DataFrames expect columns: `Tarih`, `Kategori`, `Gelir`, `Gider`
- **Auth/Billing**: Firebase Auth REST API + Firestore. Three tiers: Free, Pro, Uzman (defined in `firebase_engine.py`)
- **Secrets**: Managed via `st.secrets` — keys include `FIREBASE_WEB_API_KEY`, `FIREBASE_PROJECT_ID`, `GEMINI_API_KEY`, `GROQ_API_KEY`
- **AI providers**: Groq is primary (free, fast — llama-3.3-70b), Gemini is secondary. Both accessed via `GeminiEngine` class
- **Forecast fallback**: Prophet preferred, falls back to statsmodels ExponentialSmoothing if Prophet unavailable
- **Theme**: Light corporate navy theme defined in `.streamlit/config.toml` and `design_system.py`

## Landing Pages

`landing/` contains static HTML marketing pages (startup, corporate, investor variants).

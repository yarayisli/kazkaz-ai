# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KazKaz AI is a Turkish-language financial analysis SaaS platform for SMEs: financial health
scoring, AI-assisted commentary, cash flow/debt management, investment tracking, budgeting,
customer analytics and PDF reporting, plus a semi-autonomous CFO agent.

There are **two front ends over one set of Python engines**:

| Surface | Status | Where |
|---|---|---|
| **FastAPI + React** | **Active — all new work goes here** | `api/`, `web/` |
| **Streamlit** | **Frozen — maintenance only** | `app.py`, `*_ui.py` |

**Do not add features to the Streamlit app.** It predates the React product and still carries
19 pages of UI. It is kept because it works and is useful as an internal tool, but every user
facing change belongs in `web/`. Fixing a genuine bug in it is fine; porting a new capability
into it is not. Engines (`*_engine.py`) are shared by both and remain fully active.

## Commands

```bash
# --- Active product ---
# API (from repo root)
python -m uvicorn api.main:uygulama --host 127.0.0.1 --port 8000
# Web (from web/)
npm install && npm run dev          # dev server
npm run lint                        # tsc --noEmit — run before every commit
npm run test:e2e                    # Playwright

# --- Tests ---
python -m pytest api/tests/ -q                       # API + data quality + guardrails
python -m unittest test_engines test_usage_tracker    # shared engines

# --- Frozen surface ---
streamlit run app.py

# Dependencies
pip install -r requirements-2.txt
```

## Architecture

**Engines** (`*_engine.py`, repo root) — pure computation, no Streamlit or FastAPI imports.
Shared by both front ends:

- `financial_engine.py` — DataLoader, 5-dimension health score (0-100), revenue/expense/profit.
  The health score **needs a time series**; it cannot be derived from a single-period
  `FinansalGorunum`, and the API deliberately returns `None` rather than guessing.
- `gemini_engine.py` — AI provider abstraction (Groq primary, Gemini/NVIDIA fallback). The class
  is named `GeminiEngine` regardless of provider.
- `cfo_agent.py` — CFO agent with tool-based architecture (FinancialHealthTool, CashFlowAlertTool…)
- `expense_classification.py` — shared fixed/variable expense keyword matching (regex-escaped)
- `cashflow_engine.py`, `debt_engine.py`, `budget_engine.py`, `customer_engine.py`,
  `sector_engine.py`, `investment_engine.py`, `forecast_engine.py`

**API** (`api/`) — FastAPI app, instance named `uygulama`, ~45 endpoints under `/api/v1/`:

- `services.py` — `finansal_denetim` (metrics, risks, actions) and `cfo_yaniti` (chat)
- `ai_guardrails.py` — **source lock**: every number in an AI answer must match a value the
  engine produced or the user reported, otherwise the whole answer is withheld. Accepted numbers
  carry the source they matched (`kaynak_eslesmeleri`).
- `ai_orchestrator.py` — provider ordering, fallback, validation plumbing
- `data_quality.py` — 11 rules: 7 cross-field accounting identities + 4 anomaly scans
- `excel_import.py` — sheet detection, column mapping, quality report
- `models.py` — Pydantic models; `FinansalGorunum` is the single-period financial view

**Web** (`web/`) — Vite 6 + React 18 + TypeScript + Tailwind 4:

- `src/lib/navigation.ts` — **single source of truth for navigation**. Five screens (Durum, Para,
  Kâr, CFO'ya Sor, Veri & Rapor), each holding its tabs. Tab ids match `App.tsx` routing exactly;
  regrouping must never rename a tab id.
- `src/components/ScreenTabs.tsx` — screen heading + sub-tab strip
- `src/App.tsx` — tab routing, workspace state, Firestore persistence
- `src/lib/api.ts` — typed API client

**Frozen Streamlit surface** — `app.py` (19 pages, `_sayfa` routing), `*_ui.py` (`show_*_tab()`),
`design_system.py` (DS tokens, `inject_css()`), `ui_components.py`.

## Key Conventions

- **Language**: all user-facing text, identifiers and comments are Turkish
- **Turkish locale trap**: never CSS-`uppercase` an ASCII identifier — `toplam_varliklar` becomes
  `TOPLAM_VARLİKLAR` (dotted İ). Use readable labels instead.
- **Data format**: input DataFrames expect `Tarih`, `Kategori`, `Gelir`, `Gider`
- **Auth/Billing**: Firebase Auth REST + Firestore. Tiers: Free, Pro, Uzman (`firebase_engine.py`)
- **Secrets**: `st.secrets` for Streamlit, env vars for the API — `FIREBASE_WEB_API_KEY`,
  `FIREBASE_PROJECT_ID`, `GEMINI_API_KEY`, `GROQ_API_KEY`. Never commit `.env`.
- **AI providers**: Groq primary (llama-3.3-70b), Gemini/NVIDIA fallback, all via `GeminiEngine`
- **Forecast fallback**: Prophet preferred, statsmodels ExponentialSmoothing otherwise. Accuracy
  is reported as WAPE (zero-safe); MAPE only when every actual is non-zero.
- **`.gitignore` caution**: the Python template's generic entries are anchored to the repo root
  (`/lib/`, `/lib64/`) because an unanchored `lib/` silently swallowed `web/src/lib/`.

## Landing Pages

`landing/` contains static HTML marketing pages (startup, corporate, investor variants).
These are separate from the React app and also receive no new features.

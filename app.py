"""
KazKaz AI - Nihai Uygulama (Tam Entegre)
==========================================
Tüm modüller burada birleşir:
  - financial_engine.py  → Gelir/Gider/Karlılık/Sağlık Skoru
  - gemini_engine.py     → AI yorum + sohbet
  - forecast_engine.py   → Prophet tahmin
  - firebase_engine.py   → Auth + paket yönetimi
  - auth_ui.py           → Giriş/kayıt arayüzü
  - pdf_report.py        → PDF rapor motoru
  - pdf_ui.py            → PDF indirme butonu
  - investment_engine.py → Yatırım analiz motoru
  - investment_ui.py     → Yatırım arayüzü

Çalıştır: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# ── Core motor (zorunlu) ──
from financial_engine import FinancialEngine

# ── Opsiyonel modüller ──
try:
    from gemini_engine import GeminiEngine
    GEMINI_OK = True
except ImportError:
    GEMINI_OK = False

try:
    from forecast_engine import ForecastEngine
    FORECAST_OK = True
except ImportError:
    FORECAST_OK = False

try:
    from firebase_engine import SessionManager, Plan, PLAN_FEATURES
    from auth_ui import show_auth_page, show_plan_page, show_user_badge, plan_gate
    FIREBASE_OK = True
except ImportError:
    FIREBASE_OK = False

try:
    from pdf_report import PDFReportGenerator
    from pdf_ui import show_pdf_download_button
    PDF_OK = True
except ImportError:
    PDF_OK = False

try:
    from investment_engine import Investment, InvestmentEngine
    from investment_ui import show_investment_tab
    INVESTMENT_OK = True
except ImportError:
    INVESTMENT_OK = False

try:
    from sector_ui import show_sector_tab
    SECTOR_OK = True
except ImportError:
    SECTOR_OK = False

try:
    from cashflow_debt_ui import show_cashflow_tab, show_debt_tab
    CASHFLOW_OK = True
except ImportError:
    CASHFLOW_OK = False

try:
    from cfo_ui import show_cfo_tab
    CFO_OK = True
except ImportError:
    CFO_OK = False

try:
    from company_ui import show_company_tab
    COMPANY_OK = True
except ImportError:
    COMPANY_OK = False

try:
    from customer_ui import show_customer_tab
    CUSTOMER_OK = True
except ImportError:
    CUSTOMER_OK = False

try:
    from budget_ui import show_budget_tab
    BUDGET_OK = True
except ImportError:
    BUDGET_OK = False

try:
    from data_entry_ui import show_data_entry_tab
    DATA_ENTRY_OK = True
except ImportError:
    DATA_ENTRY_OK = False

# ─────────────────────────────────────────────
# SAYFA AYARLARI
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="KazKaz AI",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# SECRETS
# ─────────────────────────────────────────────

def get_secret(key, default=""):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default

FIREBASE_WEB_API_KEY = get_secret("FIREBASE_WEB_API_KEY")
FIREBASE_CRED_PATH   = get_secret("FIREBASE_CRED_PATH", "firebase_credentials.json")
FIREBASE_PROJECT_ID  = get_secret("FIREBASE_PROJECT_ID")
GEMINI_API_KEY_ENV   = get_secret("GEMINI_API_KEY")
GROQ_API_KEY_ENV     = get_secret("GROQ_API_KEY")

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────

# ═══════════════════════════════════════════════════════════════
# KazKaz AI — 10 Temel Tasarım İlkesi Design System
# 1. Tek vurgu rengi (#1D4ED8)
# 2. Açık tema varsayılan
# 3. Sol dikey aksan çizgisi (Bloomberg stili)
# 4. KPI sayıları baskın (22-26px, 600 weight)
# 5. Yönetici özeti bloku her ekranın tepesinde
# 6. Grafiklerde max 4 renk
# 7. Section arası 32px+ boşluk
# 8. Alert: açık zemin + ince sol çizgi
# 9. Menü 3 gruba bölünmüş
# 10. Hover: border-color değişimi, animasyon yok
# ═══════════════════════════════════════════════════════════════

DESIGN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,300..700;1,14..32,300..700&display=swap');

/* ── DESIGN TOKENS ── */
:root {
  --bg-page:       #F1F5F9;
  --bg-surface:    #FFFFFF;
  --bg-elevated:   #F8FAFC;
  --bg-input:      #F8FAFC;
  --bg-sidebar:    #0F172A;

  --border:        #E2E8F0;
  --border-strong: #CBD5E1;
  --border-focus:  #BFDBFE;

  --text-primary:  #0F172A;
  --text-secondary:#475569;
  --text-tertiary: #94A3B8;
  --text-disabled: #CBD5E1;

  /* İlke 1 — Tek vurgu */
  --accent:        #1D4ED8;
  --accent-hover:  #1E40AF;
  --accent-muted:  #EFF6FF;
  --accent-border: #BFDBFE;

  /* İlke 6 — 4 renk paleti */
  --chart-1: #1D4ED8;
  --chart-2: #0F766E;
  --chart-3: #374151;
  --chart-4: #6B7280;

  /* Durum renkleri — kurumsal */
  --green:      #059669;
  --green-bg:   #F0FDF4;
  --green-bdr:  #A7F3D0;
  --amber:      #D97706;
  --amber-bg:   #FFFBEB;
  --amber-bdr:  #FDE68A;
  --red:        #DC2626;
  --red-bg:     #FFF7F7;
  --red-bdr:    #FECACA;
  --blue:       #1D4ED8;
  --blue-bg:    #EFF6FF;
  --blue-bdr:   #BFDBFE;

  --radius-sm:  4px;
  --radius-md:  8px;
  --radius-lg:  10px;
  --shadow:     0 1px 3px rgba(15,23,42,.06), 0 2px 8px rgba(15,23,42,.04);
}

/* ── BASE ── */
html, body, [class*="css"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  -webkit-font-smoothing: antialiased;
}
.stApp { background: var(--bg-page); color: var(--text-primary); }

/* ── SIDEBAR (İlke 9: 3 grup) ── */
[data-testid="stSidebar"] {
  background: var(--bg-sidebar) !important;
  border-right: 1px solid #1E293B !important;
}
[data-testid="stSidebar"] * { color: #64748B !important; font-family: 'Inter', sans-serif !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
  color: #F1F5F9 !important;
}

/* ── LOGO ── */
.kazkaz-logo {
  font-family: 'Inter', sans-serif;
  font-size: 14px; font-weight: 600;
  letter-spacing: -0.01em; color: #F1F5F9;
}

/* ── KPI CARDS (İlke 3: sol çizgi, İlke 4: büyük sayı) ── */
.kpi-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 18px 20px 16px 22px;
  position: relative; overflow: hidden;
  margin-bottom: 8px;
  box-shadow: var(--shadow);
  transition: border-color 0.15s;  /* İlke 10 */
}
.kpi-card:hover { border-color: var(--border-strong); }  /* İlke 10 */

/* İlke 3: Sol dikey aksan çizgisi */
.kpi-card-accent {
  position: absolute; left: 0; top: 0; bottom: 0;
  width: 3px; border-radius: 4px 0 0 4px;
  background: var(--accent);
}
.kpi-card-accent.green { background: var(--green); }
.kpi-card-accent.red   { background: var(--red); }
.kpi-card-accent.amber { background: var(--amber); }

/* İlke 4: Sayılar baskın */
.kpi-label {
  font-size: 10px; font-weight: 600;
  letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--text-tertiary); margin-bottom: 8px;
}
.kpi-value {
  font-size: 24px; font-weight: 600;
  letter-spacing: -0.025em; color: var(--text-primary);
  line-height: 1.1;
}
.kpi-delta {
  display: inline-flex; align-items: center;
  font-size: 11px; font-weight: 500;
  padding: 2px 6px; border-radius: 3px;
  margin-top: 6px;
}
.kpi-delta.pos { background: var(--green-bg); color: var(--green); }
.kpi-delta.neg { background: var(--red-bg);   color: var(--red); }

/* İlke 5: Yönetici özeti bloku */
.exec-summary {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  border-radius: 0 var(--radius-lg) var(--radius-lg) 0;
  padding: 14px 18px; margin-bottom: 24px;
  box-shadow: var(--shadow);
}
.exec-summary-label {
  font-size: 9px; font-weight: 700;
  letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--accent); margin-bottom: 6px;
}
.exec-summary-text {
  font-size: 13px; color: var(--text-secondary);
  line-height: 1.6;
}

/* İlke 7: Section arası 32px+ */
.section-title {
  font-size: 11px; font-weight: 600;
  letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--text-tertiary);
  padding: 0 0 10px; margin: 28px 0 16px;
  border-bottom: 1px solid var(--border);
}

/* İlke 8: Alert blokları — açık zemin + sol çizgi */
.alert-row {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 12px 14px; border-radius: var(--radius-md);
  border-left: 3px solid; margin-bottom: 8px;
  transition: border-color 0.15s;
}
.alert-critical { background: var(--red-bg);   border-color: var(--red); }
.alert-warning  { background: var(--amber-bg); border-color: var(--amber); }
.alert-info     { background: var(--blue-bg);  border-color: var(--accent); }
.alert-success  { background: var(--green-bg); border-color: var(--green); }

.alert-title { font-size: 12px; font-weight: 600; color: var(--text-primary); }
.alert-body  { font-size: 11px; color: var(--text-secondary); line-height: 1.5; margin-top: 2px; }

/* ── BADGES ── */
.badge {
  display: inline-flex; align-items: center;
  padding: 2px 7px; border-radius: 3px;
  font-size: 10px; font-weight: 600;
  letter-spacing: 0.05em; text-transform: uppercase;
}
.badge-green  { background: var(--green-bg); color: var(--green); border: 1px solid var(--green-bdr); }
.badge-red    { background: var(--red-bg);   color: var(--red);   border: 1px solid var(--red-bdr); }
.badge-amber  { background: var(--amber-bg); color: var(--amber); border: 1px solid var(--amber-bdr); }
.badge-blue   { background: var(--blue-bg);  color: var(--blue);  border: 1px solid var(--blue-bdr); }
.badge-gray   { background: #F1F5F9; color: #475569; border: 1px solid #CBD5E1; }
.ai-badge     { background: var(--blue-bg);  color: #1E40AF; border: 1px solid var(--blue-bdr); font-size: 9px; }

/* ── TABLO (İlke 6 uyumlu) ── */
.dataframe {
  background: var(--bg-surface) !important;
  color: var(--text-primary) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  font-size: 12px !important; font-family: 'Inter', sans-serif !important;
}
.dataframe th {
  background: var(--bg-elevated) !important;
  color: var(--text-tertiary) !important;
  font-size: 10px !important; font-weight: 600 !important;
  letter-spacing: 0.08em !important; text-transform: uppercase !important;
  border-bottom: 1px solid var(--border) !important;
  padding: 10px 14px !important;
}
.dataframe td {
  border-bottom: 1px solid var(--bg-elevated) !important;
  padding: 9px 14px !important;
  color: var(--text-secondary) !important;
}
.dataframe tr:hover td {
  background: var(--bg-elevated) !important;
  color: var(--text-primary) !important;
}

/* ── BUTTONS (İlke 1: tek vurgu) ── */
.stButton > button {
  background: var(--accent) !important;
  color: #fff !important; border: none !important;
  border-radius: var(--radius-md) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 13px !important; font-weight: 500 !important;
  letter-spacing: -0.01em !important;
  padding: 8px 18px !important;
  transition: background 0.15s !important;
  box-shadow: 0 1px 3px rgba(29,78,216,.25) !important;
}
.stButton > button:hover {
  background: var(--accent-hover) !important;
}
.stDownloadButton > button {
  background: var(--bg-elevated) !important;
  color: var(--text-secondary) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  font-size: 12px !important; font-weight: 500 !important;
  transition: border-color 0.15s !important;
}
.stDownloadButton > button:hover {
  border-color: var(--accent-border) !important;
  color: var(--accent) !important;
}

/* ── INPUTS ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea textarea {
  background: var(--bg-input) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  color: var(--text-primary) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 13px !important;
  transition: border-color 0.15s !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px rgba(29,78,216,.1) !important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: 3px; gap: 2px;
}
.stTabs [data-baseweb="tab"] {
  color: var(--text-tertiary) !important;
  font-size: 12px !important; font-weight: 500 !important;
  border-radius: 6px !important; padding: 6px 14px !important;
  transition: all 0.15s !important; font-family: 'Inter', sans-serif !important;
}
.stTabs [data-baseweb="tab"]:hover {
  color: var(--text-secondary) !important;
  background: var(--bg-surface) !important;
}
.stTabs [aria-selected="true"] {
  color: var(--accent) !important;
  background: var(--bg-surface) !important;
  border: 1px solid var(--border) !important;
  font-weight: 600 !important;
}

/* ── METRICS ── */
[data-testid="stMetric"] {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg); padding: 16px 18px;
  transition: border-color 0.15s;
}
[data-testid="stMetric"]:hover { border-color: var(--border-strong); }
[data-testid="stMetricLabel"] {
  font-size: 10px !important; font-weight: 600 !important;
  letter-spacing: 0.1em !important; text-transform: uppercase !important;
  color: var(--text-tertiary) !important;
}
[data-testid="stMetricValue"] {
  font-size: 22px !important; font-weight: 600 !important;
  letter-spacing: -0.025em !important; color: var(--text-primary) !important;
}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {
  background: var(--bg-elevated) !important;
  border: 1.5px dashed var(--border-strong) !important;
  border-radius: var(--radius-lg) !important;
  transition: border-color 0.15s !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: var(--accent-border) !important;
}

/* ── EXPANDER ── */
.streamlit-expanderHeader {
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  color: var(--text-secondary) !important;
  font-size: 13px !important; font-weight: 500 !important;
  transition: border-color 0.15s !important;
}
.streamlit-expanderHeader:hover {
  border-color: var(--border-strong) !important;
}

/* ── CHAT ── */
.chat-user {
  background: var(--accent-muted);
  border: 1px solid var(--accent-border);
  border-radius: var(--radius-lg) var(--radius-lg) 4px var(--radius-lg);
  padding: 10px 14px; margin: 6px 0 6px 40px;
  font-size: 13px; color: var(--text-primary);
}
.chat-ai {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg) var(--radius-lg) var(--radius-lg) 4px;
  padding: 10px 14px; margin: 6px 40px 6px 0;
  font-size: 13px; color: var(--text-secondary);
}

/* ── MISC ── */
hr { border-color: var(--border) !important; margin: 24px 0 !important; }
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg-page); }
::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 3px; }
small, .stCaption { color: var(--text-tertiary) !important; font-size: 11px !important; }
.stRadio label, .stCheckbox label { color: var(--text-secondary) !important; font-size: 13px !important; }
.stSpinner > div { border-top-color: var(--accent) !important; }
.stProgress > div > div > div > div { background: var(--accent) !important; }
</style>
"""

st.markdown(DESIGN_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

DEFAULTS = {
    "engine": None, "rapor": None, "df": None,
    "ai_active": False, "gemini": None, "chat_history": [],
    "sirket_adi": "Şirketim", "page": "main",
    "ai_analiz": None, "ai_strateji": None,
    "senaryo_sonuc": None, "forecast": None,
    "inv_rapor": None, "mc_sonuc": None,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────

if FIREBASE_OK:
    if not SessionManager.is_authenticated():
        if FIREBASE_WEB_API_KEY:
            show_auth_page(FIREBASE_WEB_API_KEY, FIREBASE_CRED_PATH, FIREBASE_PROJECT_ID)
        else:
            _, col, _ = st.columns([1, 1.2, 1])
            with col:
                st.markdown("""
                <div style="text-align:center;padding:50px 0 20px;">
                    <div class="kazkaz-logo" style="font-size:3rem;">KazKaz AI</div>
                    <div style="color:#64748B;font-size:0.75rem;letter-spacing:2px;
                                text-transform:uppercase;margin:8px 0 28px;">Demo Modu</div>
                </div>""", unsafe_allow_html=True)
                if st.button("🚀 Demo Olarak Başla", use_container_width=True):
                    SessionManager.login(
                        {"localId": "demo", "email": "demo@kazkaz.ai"},
                        {"uid": "demo", "email": "demo@kazkaz.ai",
                         "plan": Plan.UZMAN, "ai_msg_count": 0},
                    )
                    st.rerun()
        st.stop()

    if st.session_state.get("page") == "plans":
        show_plan_page()
        if st.button("← Ana Sayfaya Dön"):
            st.session_state["page"] = "main"
            st.rerun()
        st.stop()

# ─────────────────────────────────────────────
# PAKET KONTROL YARDIMCILARI
# ─────────────────────────────────────────────

def can(feature):
    if not FIREBASE_OK:
        return True
    guard = SessionManager.get_guard()
    return guard.can(feature) if guard else True

def gate(feature, label=""):
    if not FIREBASE_OK:
        return True
    return plan_gate(feature, label)

# ─────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ─────────────────────────────────────────────

# ── PREMIUM PLOTLY THEME ──────────────────────────────────────
# Design system ile uyumlu: lacivert zemin, düşük kontrastlı grid
PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#7a90b5", family="Inter, -apple-system, sans-serif", size=11),
    xaxis=dict(gridcolor="#1a2640", showgrid=True, zeroline=False,
               tickfont=dict(size=10, color="#4a6080"),
               linecolor="#1a2640"),
    yaxis=dict(gridcolor="#1a2640", showgrid=True, zeroline=False,
               tickfont=dict(size=10, color="#4a6080"),
               linecolor="#1a2640"),
    margin=dict(l=8, r=8, t=36, b=8),
    legend=dict(
        bgcolor="rgba(13,20,36,0.8)",
        bordercolor="#1e3050",
        borderwidth=1,
        font=dict(size=11, color="#7a90b5"),
    ),
    hoverlabel=dict(
        bgcolor="#0d1424",
        bordercolor="#1e3050",
        font=dict(size=11, color="#dde4f0"),
    ),
)

# ── DESIGN SYSTEM RENK PALETİ ──────────────────────────────────
# Grafik renkleri — kontrollü, premium, kurumsal
C_BLUE   = "#2563eb"   # Primary accent
C_BLUE2  = "#3b82f6"   # Secondary blue
C_GREEN  = "#22c55e"   # Pozitif
C_RED    = "#ef4444"   # Negatif / Risk
C_AMBER  = "#f59e0b"   # Uyarı
C_SLATE  = "#475569"   # Nötr / Pasif
C_CYAN   = "#0ea5e9"   # Info / Vurgu
C_PURPLE = "#8b5cf6"   # Kategori 4
C_YELLOW = "#eab308"   # Uyarı 2

# Grafik renk sıralaması (kategorik)
CHART_COLORS = [C_BLUE, C_CYAN, C_GREEN, C_AMBER, C_PURPLE, C_SLATE, "#ec4899", "#14b8a6"]

def fmt(v):
    if abs(v) >= 1_000_000_000: return f"{v/1_000_000_000:.1f}Mn ₺"
    if abs(v) >= 1_000_000:     return f"{v/1_000_000:.1f}M ₺"
    if abs(v) >= 1_000:         return f"{v/1_000:.0f}K ₺"
    return f"{v:,.0f} ₺"

def score_color(k):
    return {
        "Mükemmel":  C_GREEN,
        "İyi":       C_BLUE2,
        "Orta":      C_AMBER,
        "Zayıf":     "#f97316",
        "Kritik":    C_RED,
    }.get(k, "#7a90b5")

def kpi(label, value, delta="", positive=True):
    try:
        _pos = bool(positive)
    except Exception:
        _pos = True
    dc = "pos" if _pos else "neg"
    di = "▲" if _pos else "▼"
    dh = f'<div class="kpi-delta {dc}">{di} {delta}</div>' if delta else ""
    st.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-card-accent {"green" if _pos else "red"}"></div>'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>{dh}</div>',
        unsafe_allow_html=True
    )

def sec(text):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    # ── LOGO ──
    st.markdown('''
    <div style="padding: 20px 4px 16px; border-bottom: 1px solid var(--border-subtle); margin-bottom: 16px;">
        <div style="display:flex; align-items:center; gap:10px;">
            <div style="width:32px;height:32px;background:var(--accent);
                        border-radius:8px;display:flex;align-items:center;
                        justify-content:center;font-size:16px;flex-shrink:0;">K</div>
            <div>
                <div style="font-family:Inter,sans-serif;font-size:1rem;
                            font-weight:600;letter-spacing:-0.01em;
                            color:var(--text-primary);">KazKaz <span style="color:var(--accent-light);">AI</span></div>
                <div style="font-size:0.58rem;letter-spacing:0.12em;
                            text-transform:uppercase;color:var(--text-tertiary);
                            margin-top:1px;">Finansal Karar Platformu</div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    if FIREBASE_OK:
        show_user_badge()
        guard = SessionManager.get_guard()
        if guard and guard.plan != Plan.UZMAN:
            if st.button("⚡ Paketi Yükselt", use_container_width=True):
                st.session_state["page"] = "plans"
                st.rerun()

    st.markdown("---")

    # Şirket adı
    st.session_state["sirket_adi"] = st.text_input(
        "Şirket / Proje Adı",
        value=st.session_state["sirket_adi"],
        placeholder="Örn: Acme A.Ş."
    )

    # Veri yükleme
    sec("📂 Veri Yükle")
    kaynak = st.radio("Kaynak:", ["CSV / Excel", "Google Sheets"], horizontal=True)

    max_rows = 50000
    if FIREBASE_OK:
        guard = SessionManager.get_guard()
        if guard:
            max_rows = guard.max_rows()

    if kaynak == "CSV / Excel":
        uploaded = st.file_uploader("Dosya seç", type=["csv", "xlsx", "xls"])
        if uploaded and st.button("▶ Analizi Başlat", use_container_width=True):
            with st.spinner("İşleniyor..."):
                try:
                    df = (pd.read_csv(uploaded)
                          if uploaded.name.endswith(".csv")
                          else pd.read_excel(uploaded))
                    if len(df) > max_rows:
                        st.warning(f"İlk {max_rows:,} satır işlendi.")
                        df = df.head(max_rows)
                    engine = FinancialEngine.from_dataframe(df)
                    st.session_state.update(
                        engine=engine, rapor=engine.full_report(), df=engine.df
                    )
                    st.success("✅ Analiz tamamlandı!")
                except Exception as e:
                    st.error(f"Hata: {e}")
    else:
        gs_url  = st.text_input("Google Sheets URL")
        gs_cred = st.text_input("Credentials JSON yolu")
        if st.button("🔗 Bağlan", use_container_width=True):
            with st.spinner("Bağlanıyor..."):
                try:
                    engine = FinancialEngine.from_google_sheets(gs_url, gs_cred)
                    st.session_state.update(
                        engine=engine, rapor=engine.full_report(), df=engine.df
                    )
                    st.success("✅ Bağlandı!")
                except Exception as e:
                    st.error(f"Hata: {e}")

    st.markdown("---")

    # AI aktivasyonu
    sec("🤖 Yapay Zeka")
    if not GEMINI_OK:
        st.caption("AI motoru yüklenemedi.")
    elif not can("ai_yorum"):
        st.caption("🔒 Pro veya Uzman paket gerekli.")
    else:
        # Provider seçimi
        provider = st.radio("AI Servisi", ["Groq (Ücretsiz)", "Gemini"],
                            horizontal=True, key="ai_provider")

        ai_toggle = st.toggle("AI Aktif Et", value=st.session_state.ai_active)
        if ai_toggle and not st.session_state.ai_active:
            if "Groq" in provider:
                st.markdown('<div class="ai-badge">Groq — Llama 3.3</div>',
                            unsafe_allow_html=True)
                api_key = GROQ_API_KEY_ENV or st.text_input(
                    "Groq API Key", type="password",
                    help="console.groq.com → API Keys → Create"
                )
                chosen_provider = "groq"
            else:
                st.markdown('<div class="ai-badge">Gemini 2.0 Flash</div>',
                            unsafe_allow_html=True)
                api_key = GEMINI_API_KEY_ENV or st.text_input(
                    "Gemini API Key", type="password",
                    help="aistudio.google.com/app/apikey"
                )
                chosen_provider = "gemini"

            if api_key and st.button("🔓 Etkinleştir", use_container_width=True):
                try:
                    st.session_state.gemini    = GeminiEngine(
                        api_key=api_key, provider=chosen_provider)
                    st.session_state.ai_active = True
                    st.success(f"🤖 {provider} aktif!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Hata: {e}")
        elif not ai_toggle:
            st.session_state.ai_active = False
        if st.session_state.ai_active:
            st.success("🟢 AI Aktif")

    st.markdown("---")

    # PDF indirme
    if PDF_OK and st.session_state.rapor:
        sec("📄 Rapor")
        if can("pdf_rapor"):
            show_pdf_download_button(
                rapor      = st.session_state.rapor,
                engine     = st.session_state.engine,
                sirket_adi = st.session_state.sirket_adi,
                ai_yorum   = st.session_state.ai_analiz,
                senaryo    = st.session_state.senaryo_sonuc,
                tahmin     = st.session_state.forecast,
                key        = "sidebar_pdf",
            )
        else:
            st.caption("🔒 PDF Uzman paket gerekli.")
        st.markdown("---")

    # Örnek veri
    with st.expander("📋 Örnek Veri"):
        sample = pd.DataFrame({
            "Tarih":    ["2024-01","2024-01","2024-02","2024-02",
                         "2024-03","2024-03","2024-04","2024-04",
                         "2024-05","2024-05","2024-06","2024-06"],
            "Kategori": ["Satış","Pazarlama","Satış","Kira",
                         "Satış","Personel","Satış","Pazarlama",
                         "Satış","Kira","Satış","Personel"],
            "Gelir":    [120000,0,140000,0,160000,0,180000,0,200000,0,220000,0],
            "Gider":    [0,15000,0,8000,0,45000,0,20000,0,8000,0,48000],
        })
        st.download_button(
            "⬇ CSV İndir", sample.to_csv(index=False).encode(),
            "ornek_veri.csv", "text/csv", use_container_width=True
        )

# ─────────────────────────────────────────────
# KARŞILAMA EKRANI
# ─────────────────────────────────────────────

if st.session_state.rapor is None:
    st.markdown("""
    <div style="text-align:center;padding:60px 20px 30px;">
        <div class="kazkaz-logo" style="font-size:3.4rem;">KazKaz AI</div>
        <div style="color:#64748B;font-size:0.82rem;letter-spacing:3px;
                    text-transform:uppercase;margin:10px 0 40px;">
            Yapay Zeka Destekli Finansal Analiz Platformu
        </div>
    </div>""", unsafe_allow_html=True)
    for col, (ico, title, desc) in zip(st.columns(4), [
        ("💰", "Gelir Analizi",   "Trend, büyüme, kategori dağılımı"),
        ("📉", "Gider Kontrolü",  "Sabit/değişken ayrım"),
        ("🔮", "Gelecek Tahmini", "Prophet ile 3-12 ay tahmin"),
        ("💼", "Yatırım Analizi", "ROI, NPV, IRR, Monte Carlo"),
    ]):
        with col:
            st.markdown(f"""
            <div class="kpi-card" style="text-align:center;padding:24px 12px;">
                <div style="font-size:2rem;margin-bottom:8px;">{ico}</div>
                <div style="font-family:'Syne',sans-serif;font-weight:700;
                            font-size:0.88rem;color:#0F172A;margin-bottom:5px;">{title}</div>
                <div style="color:#64748B;font-size:0.74rem;line-height:1.5;">{desc}</div>
            </div>""", unsafe_allow_html=True)
    st.markdown(
        "<div style='text-align:center;color:#2a3f6a;font-size:0.8rem;margin-top:20px;'>"
        "← Sol panelden veri yükleyerek başlayın</div>",
        unsafe_allow_html=True
    )
    st.stop()

# ─────────────────────────────────────────────
# SEKMEler
# ─────────────────────────────────────────────

rapor  = st.session_state.rapor
engine = st.session_state.engine
df     = st.session_state.df

(tab_genel, tab_gelir, tab_gider, tab_kar,
 tab_tahmin, tab_senaryo, tab_yatirim,
 tab_nakit, tab_borc, tab_sektor,
 tab_profil, tab_musteri, tab_butce,
 tab_veri, tab_cfo, tab_ai, tab_sohbet) = st.tabs([
    "📊 Genel", "💰 Gelir", "📉 Gider", "📈 Karlılık",
    "🔮 Tahmin", "🎯 Senaryo", "💼 Yatırım",
    "💧 Nakit Akışı", "🏦 Borç Analizi",
    "🏭 Sektör", "🏢 Şirket Profili", "👥 Müşteri & Ürün", "🎯 Bütçe",
    "📥 Veri Girişi", "🧠 CFO Agent", "🤖 AI Analiz", "💬 AI Sohbet",
])

# ══ GENEL DASHBOARD ══
with tab_genel:
    g, e, k, s = rapor["gelir"], rapor["gider"], rapor["karlilik"], rapor["saglik_skoru"]

    # ── PAGE HEADER ──
    buyume_val  = g.get("ortalama_buyume_orani", 0)
    kar_val     = k.get("toplam_net_kar", 0)
    skor_val    = s.get("skor", 0)
    skor_kat    = s.get("kategori", "")
    skor_renk   = score_color(skor_kat)

    st.markdown(f'''
    <div class="page-header">
        <div class="page-title">{st.session_state.get("sirket_adi","Şirket")} — Finansal Genel Bakış</div>
        <div class="page-subtitle">
            {g.get("ay_sayisi", 0)} aylık veri &nbsp;·&nbsp;
            Son güncelleme: {rapor.get("son_donem", "—")} &nbsp;·&nbsp;
            <span class="badge badge-{"green" if skor_val >= 65 else "amber" if skor_val >= 40 else "red"}">{skor_kat}</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # ── EXECUTIVE SUMMARY — 4 KPI ──
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("Toplam Gelir", fmt(g["toplam_gelir"]),
            f'Aylık ort. {fmt(g["ortalama_aylik_gelir"])}',
            True)
    with c2:
        kpi("Net Kar", fmt(kar_val),
            f'Marj %{k["kar_marji"]}',
            kar_val >= 0)
    with c3:
        kpi("Büyüme Oranı", f'%{buyume_val}',
            f'Aylık ortalama',
            buyume_val >= 0)
    with c4:
        st.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-card-accent" style="background:{skor_renk}"></div>'
            f'<div class="kpi-label">Finansal Sağlık</div>'
            f'<div class="kpi-value" style="color:{skor_renk};">{skor_val}'
            f'<span style="font-size:1rem;color:var(--text-tertiary);font-weight:400;"> /100</span></div>'
            f'<div style="color:{skor_renk};font-size:0.72rem;font-weight:500;'
            f'letter-spacing:0.04em;margin-top:6px;">{skor_kat.upper()}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # ── İKİNCİL KPI SATIRI ──
    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Toplam Gider",    fmt(e["toplam_gider"]),
                 f'Sabit %{e["sabit_gider_orani"]}',
                 e["sabit_gider_orani"] < 60)
    with c2: kpi("Kar Marjı",       f'%{k["kar_marji"]}',
                 positive=k["kar_marji"] >= 10)
    with c3: kpi("Gider / Gelir",
                 f'%{round(e["toplam_gider"]/g["toplam_gelir"]*100,1) if g["toplam_gelir"] else 0}',
                 "Hedef < %80",
                 (e["toplam_gider"]/g["toplam_gelir"] < 0.80) if g["toplam_gelir"] else False)
    with c4: kpi("Analiz Dönemi",
                 f'{g.get("ay_sayisi",0)} Ay',
                 f'{g.get("donem_baslangic","—")} – {g.get("donem_bitis","—")}',
                 True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── ANA GRAFİK — GELİR / GİDER / NET KAR ──
    col_main, col_side = st.columns([2, 1])

    with col_main:
        st.markdown('<div class="section-title">Aylık Finansal Performans</div>',
                    unsafe_allow_html=True)
        mp = engine.profit.monthly_profit()
        if not mp.empty:
            fig = go.Figure()
            fig.add_bar(x=mp["Dönem"], y=mp["Gelir"],
                        name="Gelir", marker_color=C_BLUE, opacity=0.85)
            fig.add_bar(x=mp["Dönem"], y=mp["Gider"],
                        name="Gider", marker_color=C_SLATE, opacity=0.75)
            fig.add_scatter(x=mp["Dönem"], y=mp["NetKar"],
                            name="Net Kar",
                            mode="lines+markers",
                            line=dict(color=C_GREEN, width=2),
                            marker=dict(size=5, color=C_GREEN))
            fig.update_layout(
                barmode="group", height=310,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#7a90b5", family="Inter, sans-serif", size=11),
                xaxis=dict(gridcolor="#1a2640", showgrid=True, zeroline=False),
                yaxis=dict(gridcolor="#1a2640", showgrid=True, zeroline=False),
                margin=dict(l=8, r=8, t=36, b=8),
                legend=dict(orientation="h", y=1.06, x=0, font=dict(size=10)))
            st.plotly_chart(fig, use_container_width=True)

    with col_side:
        st.markdown('<div class="section-title">Finansal Sağlık Alt Skorları</div>',
                    unsafe_allow_html=True)
        alt = s["alt_skorlar"]
        for key, lbl in [
            ("karlilik","Karlılık"),
            ("buyume","Büyüme"),
            ("gider_kontrolu","Gider Kontrolü"),
            ("nakit","Nakit"),
        ]:
            val    = alt.get(key, 0)
            renk   = C_GREEN if val >= 70 else C_AMBER if val >= 40 else C_RED
            pct    = min(val, 100)
            st.markdown(f'''
            <div style="margin-bottom:14px;">
                <div style="display:flex;justify-content:space-between;
                            margin-bottom:5px;">
                    <span style="font-size:0.72rem;font-weight:500;
                                 color:var(--text-secondary);
                                 letter-spacing:0.04em;">{lbl.upper()}</span>
                    <span style="font-size:0.78rem;font-weight:600;
                                 color:{renk};">{val}</span>
                </div>
                <div style="background:var(--border-subtle);border-radius:3px;
                            height:5px;overflow:hidden;">
                    <div style="background:{renk};width:{pct}%;height:100%;
                                border-radius:3px;transition:width 0.4s;"></div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

        st.markdown(
            f'<div class="alert-row alert-info" style="margin-top:8px;">'
            f'<div><div class="alert-title" style="font-size:0.72rem;">Sistem Değerlendirmesi</div>'
            f'<div class="alert-body">{s.get("aciklama","")}</div></div></div>',
            unsafe_allow_html=True
        )

# ══ GELİR ══
with tab_gelir:
    g = rapor["gelir"]
    sec("💰 Gelir Analizi")
    c1, c2, c3 = st.columns(3)
    with c1: kpi("Toplam Gelir",   fmt(g["toplam_gelir"]))
    with c2: kpi("Aylık Ortalama", fmt(g["ortalama_aylik_gelir"]))
    with c3: kpi("Ort. Büyüme",    f'%{g["ortalama_buyume_orani"]}',
                 positive=g["ortalama_buyume_orani"] >= 0)
    col1, col2 = st.columns(2)
    with col1:
        mr  = engine.revenue.monthly_revenue()
        fig = px.bar(mr, x="Dönem", y="Toplam Gelir",
                     color_discrete_sequence=["#1D4ED8"])
        fig.update_layout(title="Aylık Gelir Trendi", height=280, **PLOTLY_THEME)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        cr = engine.revenue.revenue_by_category()
        cr = cr[cr["Toplam Gelir"] > 0]
        if not cr.empty:
            fig = px.pie(cr, values="Toplam Gelir", names="Kategori",
                         color_discrete_sequence=px.colors.sequential.Blues_r, hole=0.5)
            fig.update_layout(title="Gelir Dağılımı", height=280, **PLOTLY_THEME)
            st.plotly_chart(fig, use_container_width=True)
    gr = engine.revenue.revenue_growth_rate().dropna()
    if not gr.empty:
        fig = go.Figure(go.Scatter(x=gr["Dönem"], y=gr["Büyüme Oranı (%)"],
                        fill="tozeroy", mode="lines+markers",
                        line=dict(color="#0EA5E9", width=2),
                        fillcolor="rgba(0,212,255,0.07)"))
        fig.add_hline(y=0, line_dash="dash", line_color="#DC2626", opacity=0.5)
        fig.update_layout(title="Büyüme Oranı (%)", height=230, **PLOTLY_THEME)
        st.plotly_chart(fig, use_container_width=True)

# ══ GİDER ══
with tab_gider:
    e = rapor["gider"]
    sec("📉 Gider Analizi")
    c1, c2, c3 = st.columns(3)
    with c1: kpi("Toplam Gider",   fmt(e["toplam_gider"]))
    with c2: kpi("Sabit Gider",    fmt(e["sabit_gider"]))
    with c3: kpi("Değişken Gider", fmt(e["degisken_gider"]))
    col1, col2 = st.columns(2)
    with col1:
        ce = engine.expense.expense_by_category()
        ce = ce[ce["Toplam Gider"] > 0]
        if not ce.empty:
            fig = px.bar(ce, x="Toplam Gider", y="Kategori", orientation="h",
                         color_discrete_sequence=["#DC2626"])
            fig.update_layout(title="Kategoriye Göre Gider", height=280,
                              yaxis=dict(autorange="reversed", gridcolor="#1e2d4a", showgrid=True, zeroline=False),
                              paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font=dict(color="#8899bb", family="DM Sans"),
                              xaxis=dict(gridcolor="#1e2d4a", showgrid=True, zeroline=False),
                              margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        fv  = engine.expense.fixed_vs_variable()
        fig = go.Figure(go.Pie(
            labels=["Sabit", "Değişken"],
            values=[fv["sabit_gider"], fv["degisken_gider"]],
            marker_colors=["#DC2626", "#f97316"], hole=0.5
        ))
        fig.update_layout(title="Sabit / Değişken", height=280, **PLOTLY_THEME)
        st.plotly_chart(fig, use_container_width=True)

# ══ KARLILIK ══
with tab_kar:
    k = rapor["karlilik"]
    sec("📈 Karlılık Analizi")
    c1, c2, c3 = st.columns(3)
    with c1: kpi("Net Kar",   fmt(k["toplam_net_kar"]), positive=k["toplam_net_kar"] >= 0)
    with c2: kpi("Kar Marjı", f'%{k["kar_marji"]}',    positive=k["kar_marji"] >= 0)
    with c3: kpi("Trend",     k["kar_trendi"])
    mp = engine.profit.monthly_profit()
    if not mp.empty:
        renkler = ["#059669" if v >= 0 else "#DC2626" for v in mp["NetKar"]]
        fig = go.Figure()
        fig.add_bar(x=mp["Dönem"], y=mp["NetKar"], marker_color=renkler, name="Net Kar")
        fig.add_scatter(x=mp["Dönem"], y=mp["KarMarji"], name="Kar Marjı (%)",
                        yaxis="y2", mode="lines+markers",
                        line=dict(color="#D97706", width=2, dash="dot"),
                        marker=dict(size=5))
        fig.update_layout(title="Aylık Net Kar & Kar Marjı", height=300,
                          yaxis2=dict(overlaying="y", side="right", gridcolor="#1e2d4a",
                                      tickformat=".0f", ticksuffix="%"), **PLOTLY_THEME)
        st.plotly_chart(fig, use_container_width=True)

# ══ TAHMİN ══
with tab_tahmin:
    sec("🔮 Gelecek Gelir Tahmini")
    if not gate("tahmin", "Gelecek Tahmini"):
        st.stop()
    if not FORECAST_OK:
        st.error("`prophet` kurulu değil → `pip install prophet`")
    else:
        col1, col2 = st.columns([1, 3])
        with col1:
            ay = st.slider("Tahmin (Ay)", 1, 12, 3, key="fc_ay")
            if st.button("📈 Tahmin Üret", use_container_width=True):
                with st.spinner("Prophet eğitiliyor..."):
                    try:
                        sonuc = ForecastEngine(df).summary_report(ay=ay)
                        st.session_state["forecast"] = sonuc
                        st.success("✅ Hazır!")
                    except Exception as ex:
                        st.error(f"Hata: {ex}")
        if st.session_state.forecast:
            sonuc = st.session_state.forecast
            with col2:
                c1, c2, c3 = st.columns(3)
                with c1: kpi("Toplam Tahmin", fmt(sonuc["toplam_tahmin"]))
                with c2: kpi("Aylık Ort.",    fmt(sonuc["ortalama_tahmin"]))
                with c3: kpi("Büyüme Bkl.",   f'%{sonuc["buyume_beklentisi"]}',
                             positive=sonuc["buyume_beklentisi"] >= 0)
            t_df = sonuc["tahmin_tablosu"]
            mr   = engine.revenue.monthly_revenue()
            fig  = go.Figure()
            fig.add_scatter(x=mr["Dönem"], y=mr["Toplam Gelir"], name="Gerçek",
                            mode="lines+markers", line=dict(color="#3B82F6", width=2))
            fig.add_scatter(x=t_df["Dönem"], y=t_df["Tahmin"], name="Tahmin",
                            mode="lines+markers",
                            line=dict(color="#059669", width=2.5, dash="dot"),
                            marker=dict(size=7, symbol="diamond"))
            fig.add_scatter(
                x=list(t_df["Dönem"]) + list(reversed(t_df["Dönem"])),
                y=list(t_df["Üst Sınır"]) + list(reversed(t_df["Alt Sınır"])),
                fill="toself", fillcolor="rgba(16,217,148,0.09)",
                line=dict(color="rgba(0,0,0,0)"), name="Güven Aralığı"
            )
            fig.update_layout(title="Gelir Tahmini", height=330,
                              legend=dict(orientation="h", y=1.1, x=0), **PLOTLY_THEME)
            st.plotly_chart(fig, use_container_width=True)
            sec("📋 Tahmin Tablosu")
            st.dataframe(t_df.style.format({
                "Tahmin":    "{:,.0f} ₺",
                "Alt Sınır": "{:,.0f} ₺",
                "Üst Sınır": "{:,.0f} ₺",
            }), use_container_width=True, hide_index=True)

# ══ SENARYO ══
with tab_senaryo:
    sec("🎯 Senaryo Analizi")
    if not gate("senaryo_analiz", "Senaryo Analizi"):
        st.stop()
    c1, c2 = st.columns(2)
    with c1: gelir_artis  = st.slider("📈 Gelir Artışı (%)",  0, 100, 10, 5)
    with c2: gider_azalis = st.slider("📉 Gider Azalışı (%)", 0,  50,  5, 5)
    sen = engine.scenario_analysis(gelir_artis / 100, gider_azalis / 100)
    st.session_state["senaryo_sonuc"] = sen
    mevcut, yeni, degisim = sen["mevcut"], sen["senaryo"], sen["degisim"]
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Mevcut Gelir",   fmt(mevcut["gelir"]))
    with c2: kpi("Yeni Gelir",     fmt(yeni["gelir"]),
                 f'+{fmt(degisim["gelir_farki"])}', True)
    with c3: kpi("Mevcut Net Kar", fmt(mevcut["net_kar"]))
    with c4: kpi("Yeni Net Kar",   fmt(yeni["net_kar"]),
                 f'+{fmt(degisim["kar_farki"])}', degisim["kar_farki"] >= 0)
    fig = go.Figure()
    for name, vals, color in [
        ("Mevcut",  [mevcut["gelir"], mevcut["gider"], mevcut["net_kar"]], "#4a6fa5"),
        ("Senaryo", [yeni["gelir"],   yeni["gider"],   yeni["net_kar"]],   "#0EA5E9"),
    ]:
        fig.add_bar(name=name, x=["Gelir", "Gider", "Net Kar"],
                    y=vals, marker_color=color, opacity=0.88)
    fig.update_layout(barmode="group", title="Mevcut vs Senaryo",
                      height=300, **PLOTLY_THEME)
    st.plotly_chart(fig, use_container_width=True)
    if st.session_state.ai_active and GEMINI_OK:
        if st.button("🤖 Senaryoyu AI ile Yorumla"):
            with st.spinner("Yorumlanıyor..."):
                yorum = st.session_state.gemini.scenario_comment(mevcut, yeni)
            st.markdown(
                f'<div style="background:#F8FAFC;border:1px solid #BFDBFE;'
                f'border-radius:12px;padding:14px 18px;color:#475569;'
                f'font-size:0.88rem;line-height:1.7;">'
                f'<div class="ai-badge">AI Yorumu</div><br>'
                f'{yorum.replace(chr(10), "<br>")}</div>',
                unsafe_allow_html=True
            )

# ══ YATIRIM ══
with tab_yatirim:
    if not INVESTMENT_OK:
        st.error("`investment_engine.py` bulunamadı. Tüm dosyaların aynı klasörde olduğundan emin olun.")
    else:
        show_investment_tab()

# ══ NAKİT AKIŞI ══
with tab_nakit:
    if not CASHFLOW_OK:
        st.error("`cashflow_engine.py` ve `cashflow_debt_ui.py` klasörde olmalı.")
    else:
        show_cashflow_tab(fin_engine=engine, fin_rapor=rapor)

# ══ BORÇ ANALİZİ ══
with tab_borc:
    if not CASHFLOW_OK:
        st.error("`debt_engine.py` ve `cashflow_debt_ui.py` klasörde olmalı.")
    else:
        show_debt_tab(fin_rapor=rapor)

# ══ SEKTÖR KARŞILAŞTIRMASI ══
with tab_sektor:
    if not SECTOR_OK:
        st.error("`sector_engine.py` ve `sector_ui.py` dosyaları klasörde olmalı.")
    else:
        gemini_inst = st.session_state.gemini if st.session_state.ai_active else None
        show_sector_tab(
            df         = df,
            rapor      = rapor,
            sirket_adi = st.session_state.get("sirket_adi", "Şirketim"),
            gemini     = gemini_inst,
        )

# ══ ŞİRKET PROFİLİ ══
with tab_profil:
    if not COMPANY_OK:
        st.error("`company_profile.py` ve `company_ui.py` dosyaları klasörde olmalı.")
    else:
        show_company_tab(fin_rapor=rapor)

# ══ MÜŞTERİ & ÜRÜN ANALİZİ ══
with tab_musteri:
    if not CUSTOMER_OK:
        st.error("`customer_engine.py` ve `customer_ui.py` dosyaları klasörde olmalı.")
    else:
        show_customer_tab(df=df)

# ══ BÜTÇE VS GERÇEKLEŞen ══
with tab_butce:
    if not BUDGET_OK:
        st.error("`budget_engine.py` ve `budget_ui.py` dosyaları klasörde olmalı.")
    else:
        show_budget_tab(df=df, fin_rapor=rapor)

# ══ VERİ GİRİŞ MERKEZİ ══
with tab_veri:
    if not DATA_ENTRY_OK:
        st.error("`data_importer.py` ve `data_entry_ui.py` dosyaları klasörde olmalı.")
    else:
        show_data_entry_tab()

# ══ CFO AGENT ══
with tab_cfo:
    if not CFO_OK:
        st.error("`cfo_agent.py` ve `cfo_ui.py` dosyaları klasörde olmalı.")
    else:
        ai_inst = st.session_state.gemini if st.session_state.ai_active else None
        show_cfo_tab(
            fin_rapor  = rapor,
            sirket_adi = st.session_state.get("sirket_adi", "Şirketim"),
            ai_engine  = ai_inst,
            cf_rapor   = st.session_state.get("cf_rapor"),
            debt_rapor = st.session_state.get("debt_rapor"),
        )

# ══ AI ANALİZ ══
with tab_ai:
    sec("🤖 AI Finansal Analiz")
    if not gate("ai_yorum", "AI Yorumları"):
        st.stop()
    if not GEMINI_OK:
        st.error("`google-generativeai` kurulu değil → `pip install google-generativeai`")
    elif not st.session_state.ai_active:
        st.info("Sol panelden Gemini API anahtarını girerek AI'ı aktif edin.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📊 Tam Analiz Üret", use_container_width=True):
                with st.spinner("Analiz yapılıyor..."):
                    # Şirket profilini rapor'a ekle
                    rapor_with_profil = dict(rapor)
                    if "cp_profile" in st.session_state:
                        rapor_with_profil["sirket_profili"] = \
                            st.session_state["cp_profile"].to_dict()
                    st.session_state["ai_analiz"] = \
                        st.session_state.gemini.analyze(rapor_with_profil)
        with c2:
            if st.button("🎯 Stratejik Öneriler", use_container_width=True):
                with st.spinner("Öneriler üretiliyor..."):
                    rapor_with_profil = dict(rapor)
                    if "cp_profile" in st.session_state:
                        rapor_with_profil["sirket_profili"] = \
                            st.session_state["cp_profile"].to_dict()
                    st.session_state["ai_strateji"] = \
                        st.session_state.gemini.strategic_recommendations(
                            rapor_with_profil)
        for key, title in [("ai_analiz","📋 Analiz Raporu"),
                            ("ai_strateji","🎯 Stratejik Öneriler")]:
            if st.session_state.get(key):
                sec(title)
                st.markdown(
                    f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
                    f'border-radius:14px;padding:18px 22px;color:#334155;'
                    f'font-size:0.88rem;line-height:1.8;">'
                    f'<div class="ai-badge">Gemini AI</div><br>'
                    f'{st.session_state[key].replace(chr(10), "<br>")}</div>',
                    unsafe_allow_html=True
                )

# ══ AI SOHBET ══
with tab_sohbet:
    sec("💬 AI Finansal Asistan")
    if not gate("ai_sohbet", "AI Sohbet"):
        st.stop()
    if not GEMINI_OK:
        st.error("`google-generativeai` kurulu değil.")
    elif not st.session_state.ai_active:
        st.info("Sol panelden Gemini'yi aktif edin.")
    else:
        for col, soru in zip(st.columns(4), [
            "Şirketim karlı mı?", "En büyük giderim?",
            "Geliri nasıl artırırım?", "Nakit akışım sağlıklı mı?"
        ]):
            with col:
                if st.button(soru, key=f"qs_{soru}", use_container_width=True):
                    st.session_state.chat_history.append({"role":"user","content":soru})
                    with st.spinner("..."):
                        cevap = st.session_state.gemini.chat(soru, rapor)
                    st.session_state.chat_history.append({"role":"ai","content":cevap})
                    st.rerun()
        st.markdown("---")
        for msg in st.session_state.chat_history:
            cls  = "chat-user" if msg["role"] == "user" else "chat-ai"
            ikon = "👤" if msg["role"] == "user" else "🤖"
            st.markdown(f'<div class="{cls}">{ikon} {msg["content"]}</div>',
                        unsafe_allow_html=True)
        ci, cs = st.columns([5, 1])
        with ci:
            user_input = st.text_input("Sorunuzu yazın...", key="chat_input",
                                       label_visibility="collapsed",
                                       placeholder="Örn: Hangi kategoride büyüme var?")
        with cs:
            if st.button("➤", use_container_width=True) and user_input:
                st.session_state.chat_history.append({"role":"user","content":user_input})
                with st.spinner("..."):
                    cevap = st.session_state.gemini.chat(user_input, rapor)
                st.session_state.chat_history.append({"role":"ai","content":cevap})
                st.rerun()
        if st.session_state.chat_history:
            if st.button("🗑 Sohbeti Temizle"):
                st.session_state.chat_history = []
                if st.session_state.gemini:
                    st.session_state.gemini.reset_chat()
                st.rerun()

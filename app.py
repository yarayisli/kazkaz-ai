"""
KazKaz AI — Ana Uygulama v2.1
================================
Değişiklikler (v2.1):
  - Sidebar sadece navigasyon — tek, temiz menü sistemi
  - Veri yükleme sidebar'dan çıkarıldı → "Veri Girişi" sayfasına taşındı
  - CSS çakışmaları giderildi (yıldız selektör kaldırıldı)
  - YAPAY ZEKA / RAPORLAMA grupları sidebar'dan kaldırıldı
  - AI aktivasyonu → AI Analiz / AI Sohbet sayfalarına taşındı
  - Karşılama ekranında "Hızlı Başlat" butonu eklendi
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit.components.v1 as components

# ── Core motor ────────────────────────────────────────────────────────────────
from financial_engine import FinancialEngine
from design_system import *
from ui_components import (
    render_topbar, render_page_header, render_exec_summary,
    render_kpi_row, render_section, render_alerts,
    render_health_bars, render_stat_strip, render_insight_card,
    render_divider, badge_html, fmt as ufmt, T,
)

# ── Opsiyonel modüller ────────────────────────────────────────────────────────
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

# ── Sayfa ayarları ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="KazKaz AI",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Secrets ───────────────────────────────────────────────────────────────────
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

# ── CSS — temiz, çakışmasız ───────────────────────────────────────────────────
inject_css()

st.markdown("""
<style>
.stApp { background-color: #F7F8FA !important; }

/* Sidebar — beyaz, temiz */
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 0.5px solid #E2E5EB !important;
}

/* Sidebar nav butonları — sadece butonlar, yıldız yok */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: none !important;
    border-radius: 6px !important;
    color: #4B5563 !important;
    font-size: 12.5px !important;
    font-weight: 400 !important;
    padding: 6px 10px !important;
    text-align: left !important;
    box-shadow: none !important;
    width: 100% !important;
    justify-content: flex-start !important;
    transition: background 0.12s, color 0.12s !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #F3F4F6 !important;
    color: #1A1F36 !important;
}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: #EEF2FF !important;
    color: #1B3A6B !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] .stButton {
    margin-bottom: 1px !important;
}

/* Ana içerik butonları */
.main .stButton > button {
    background: #1B3A6B !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}
.main .stButton > button:hover { background: #2B4F8C !important; }
.main .stButton > button:disabled {
    background: #E5E7EB !important;
    color: #9CA3AF !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #F3F4F6 !important;
    border: 0.5px solid #E2E5EB !important;
    border-radius: 8px !important;
    padding: 3px !important;
}
.stTabs [data-baseweb="tab"] {
    color: #9CA3AF !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
}
.stTabs [aria-selected="true"] {
    color: #1B3A6B !important;
    background: #FFFFFF !important;
    font-weight: 600 !important;
}

/* Metrik kartları */
[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: 0.5px solid #E2E5EB !important;
    border-radius: 8px !important;
    padding: 12px !important;
}
[data-testid="stMetricLabel"] {
    font-size: 9px !important;
    font-weight: 600 !important;
    letter-spacing: .1em !important;
    text-transform: uppercase !important;
    color: #9CA3AF !important;
}
[data-testid="stMetricValue"] {
    font-size: 22px !important;
    font-weight: 600 !important;
    color: #1A1A2E !important;
}

/* Tablo */
.dataframe th {
    background: #F3F4F6 !important;
    color: #9CA3AF !important;
    font-size: 9px !important;
    font-weight: 600 !important;
    letter-spacing: .08em !important;
    text-transform: uppercase !important;
}
.dataframe td { border-bottom: 0.5px solid #F3F4F6 !important; }

/* Download butonu */
.stDownloadButton > button {
    background: #F3F4F6 !important;
    color: #4B5563 !important;
    border: 0.5px solid #E2E5EB !important;
    border-radius: 8px !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: #D1D5DB; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
DEFAULTS = {
    "engine": None, "rapor": None, "df": None,
    "ai_active": False, "gemini": None, "chat_history": [],
    "sirket_adi": "Şirketim", "page": "main",
    "ai_analiz": None, "ai_strateji": None,
    "senaryo_sonuc": None, "forecast": None,
    "inv_rapor": None, "mc_sonuc": None,
    "nav_sayfa": "genel",
    "rol": "cfo",
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Auth ──────────────────────────────────────────────────────────────────────
if FIREBASE_OK:
    if not SessionManager.is_authenticated():
        if FIREBASE_WEB_API_KEY:
            show_auth_page(FIREBASE_WEB_API_KEY, FIREBASE_CRED_PATH, FIREBASE_PROJECT_ID)
        else:
            _, col, _ = st.columns([1, 1.2, 1])
            with col:
                st.markdown("""
                <div style="text-align:center;padding:50px 0 20px;">
                    <div style="font-size:2.4rem;font-weight:700;color:#0F2252;">KazKaz AI</div>
                    <div style="color:#9CA3AF;font-size:0.75rem;letter-spacing:2px;
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
        st.stop()

# ── Yardımcı: paket kontrolü ──────────────────────────────────────────────────
def can(feature):
    if not FIREBASE_OK:
        return True
    guard = SessionManager.get_guard()
    return guard.can(feature) if guard else True

def gate(feature, label=""):
    if not FIREBASE_OK:
        return True
    return plan_gate(feature, label)

# ── Yardımcı: format & renk ───────────────────────────────────────────────────
def fmt(v):
    try:
        v = float(v)
    except Exception:
        return str(v)
    if abs(v) >= 1_000_000_000: return f"{v/1_000_000_000:.1f}Mn ₺"
    if abs(v) >= 1_000_000:     return f"{v/1_000_000:.1f}M ₺"
    if abs(v) >= 1_000:         return f"{v/1_000:.0f}K ₺"
    return f"{v:,.0f} ₺"

def score_color(k):
    return {
        "Mükemmel": "#059669", "İyi": "#2563EB",
        "Orta": "#D97706",    "Zayıf": "#f97316", "Kritik": "#DC2626",
    }.get(k, "#6B7280")

PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#FAFBFC",
    font=dict(color="#9CA3AF", family="-apple-system,Segoe UI,Arial,sans-serif", size=11),
    xaxis=dict(gridcolor="#F3F4F6", showgrid=True, zeroline=False,
               tickfont=dict(size=10, color="#9CA3AF")),
    yaxis=dict(gridcolor="#F3F4F6", showgrid=True, zeroline=False,
               tickfont=dict(size=10, color="#9CA3AF")),
    margin=dict(l=8, r=8, t=36, b=8),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#E5E7EB",
                borderwidth=1, font=dict(size=11, color="#475569")),
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#E5E7EB",
                    font=dict(size=11, color="#0F172A")),
)

def kpi(label, value, delta="", color="#0F172A", positive=True):
    try:
        _p = bool(positive)
    except Exception:
        _p = True
    accent = "#059669" if _p else "#DC2626"
    dh = (
        f'<div style="display:inline-flex;align-items:center;gap:3px;font-size:11px;'
        f'font-weight:500;padding:2px 6px;border-radius:3px;margin-top:6px;'
        f'background:{"#F0FDF4" if _p else "#FFF7F7"};color:{accent};">'
        f'{"+" if _p else "−"} {delta}</div>'
    ) if delta else ""
    st.markdown(
        f'<div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:10px;'
        f'padding:18px 20px 16px 22px;position:relative;overflow:hidden;margin-bottom:8px;">'
        f'<div style="position:absolute;left:0;top:0;bottom:0;width:3px;'
        f'border-radius:4px 0 0 4px;background:{accent};"></div>'
        f'<div style="font-size:10px;font-weight:600;letter-spacing:0.1em;'
        f'text-transform:uppercase;color:#94A3B8;margin-bottom:8px;">{label}</div>'
        f'<div style="font-size:24px;font-weight:600;letter-spacing:-0.025em;'
        f'line-height:1.1;color:{color};">{value}</div>{dh}</div>',
        unsafe_allow_html=True
    )

def sec(text, small=False):
    fs = "0.78rem" if small else "0.8rem"
    st.markdown(
        f'<div style="font-size:{fs};font-weight:600;letter-spacing:0.08em;'
        f'text-transform:uppercase;color:#94A3B8;padding:0 0 10px;'
        f'border-bottom:1px solid #E2E8F0;margin:28px 0 16px;">{text}</div>',
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — Sadece navigasyon
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:

    # Logo
    st.markdown(
        '<div style="padding:16px 16px 12px;border-bottom:0.5px solid #E2E5EB;">'
        '<div style="display:flex;align-items:center;gap:10px;">'
        '<div style="width:30px;height:30px;background:#1B3A6B;border-radius:7px;'
        'display:flex;align-items:center;justify-content:center;'
        'font-size:13px;font-weight:700;color:#fff;flex-shrink:0;">K</div>'
        '<div>'
        '<div style="font-size:13px;font-weight:600;color:#1A1A2E;">KazKaz <span style="color:#2563EB;">AI</span></div>'
        '<div style="font-size:9px;text-transform:uppercase;letter-spacing:.1em;color:#9CA3AF;">Finansal Platform</div>'
        '</div></div></div>',
        unsafe_allow_html=True
    )

    # Kullanıcı badge + paket yükselt
    if FIREBASE_OK:
        show_user_badge()
        guard = SessionManager.get_guard()
        if guard and guard.plan != Plan.UZMAN:
            if st.button("⚡ Paketi Yükselt", use_container_width=True, key="btn_upgrade"):
                st.session_state["page"] = "plans"
                st.rerun()

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # Şirket adı
    st.session_state["sirket_adi"] = st.text_input(
        "Şirket adı",
        value=st.session_state["sirket_adi"],
        placeholder="Örn: Acme A.Ş.",
        label_visibility="collapsed",
        key="input_sirket_adi"
    )

    # Rol seçici
    _rol = st.session_state.get("rol", "cfo")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✓ CFO" if _rol == "cfo" else "CFO", use_container_width=True,
                     type="primary" if _rol == "cfo" else "secondary", key="btn_cfo"):
            st.session_state["rol"] = "cfo"; st.rerun()
    with c2:
        if st.button("✓ CEO" if _rol == "ceo" else "CEO", use_container_width=True,
                     type="primary" if _rol == "ceo" else "secondary", key="btn_ceo"):
            st.session_state["rol"] = "ceo"; st.rerun()

    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

    # ── Navigasyon ────────────────────────────────────────────────────────────
    def nav_group(label):
        st.markdown(
            f'<div style="font-size:9px;font-weight:700;letter-spacing:.1em;'
            f'text-transform:uppercase;color:#9CA3AF;'
            f'padding:12px 4px 4px;margin-top:2px;">{label}</div>',
            unsafe_allow_html=True
        )

    def nav_item(label, key, icon="·"):
        aktif = st.session_state.get("nav_sayfa") == key
        clicked = st.button(
            f"{icon} {label}" if aktif else f"  {label}",
            key=f"nav_{key}",
            use_container_width=True,
            type="primary" if aktif else "secondary",
        )
        if clicked:
            st.session_state["nav_sayfa"] = key
            st.rerun()

    nav_group("Genel Bakış")
    nav_item("Dashboard",        "genel",   "◉")
    nav_item("Şirket & Sektör",  "profil",  "○")
    nav_item("Risk & Alarm",     "risk",    "○")

    nav_group("Finansal Analiz")
    nav_item("Gelir Analizi",    "gelir",   "○")
    nav_item("Gider Analizi",    "gider",   "○")
    nav_item("Karlılık",         "kar",     "○")
    nav_item("Nakit Akışı",      "nakit",   "○")
    nav_item("Borç & Finansman", "borc",    "○")
    nav_item("Bütçe & Gerçek",   "butce",   "○")
    nav_item("Müşteri & Ürün",   "musteri", "○")

    nav_group("Stratejik Karar")
    nav_item("Tahmin & Senaryo", "tahmin",  "○")
    nav_item("Yatırım Merkezi",  "yatirim", "○")
    nav_item("Sektör Benchmark", "sektor",  "○")

    nav_group("AI & CFO Agent")
    nav_item("CFO Agent",        "cfo",     "◈")
    nav_item("AI Analiz",        "ai",      "◈")
    nav_item("AI Sohbet",        "sohbet",  "◈")

    nav_group("Veri & Rapor")
    nav_item("Veri Girişi",      "veri",    "○")
    nav_item("PDF Rapor",        "pdf",     "○")

    # Örnek veri indirme
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    with st.expander("📋 Örnek Veri İndir"):
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

# ─────────────────────────────────────────────────────────────────────────────
# KARŞILAMA EKRANI (veri yüklenmemişse)
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.rapor is None and st.session_state.get("nav_sayfa") not in ("veri", "pdf"):

    st.markdown(
        '<div style="padding:32px 0 20px;">'
        '<div style="font-size:26px;font-weight:700;color:#0F2252;margin-bottom:6px;">'
        'KazKaz AI</div>'
        '<div style="font-size:13px;color:#9CA3AF;">Yapay Zeka Destekli Finansal Karar Platformu</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # ── Hızlı Başlat ─────────────────────────────────────────────────────────
    st.markdown(
        '<div style="background:#EEF2FF;border:1px solid #C7D2FE;border-radius:10px;'
        'padding:16px 20px;margin-bottom:20px;">'
        '<div style="font-size:13px;font-weight:600;color:#1B3A6B;margin-bottom:4px;">'
        '🚀 Hızlı Başlat</div>'
        '<div style="font-size:12px;color:#4B5563;">Demo veriyle sistemi hemen keşfedin '
        'veya kendi dosyanızı "Veri Girişi" sayfasından yükleyin.</div>'
        '</div>',
        unsafe_allow_html=True
    )

    col_demo, col_yukle = st.columns(2)
    with col_demo:
        if st.button("▶  Demo Veriyle Başlat", use_container_width=True, key="btn_demo"):
            demo_df = pd.DataFrame({
                "Tarih":    ["2023-01","2023-01","2023-02","2023-02","2023-03","2023-03",
                             "2023-04","2023-04","2023-05","2023-05","2023-06","2023-06",
                             "2023-07","2023-07","2023-08","2023-08","2023-09","2023-09",
                             "2023-10","2023-10","2023-11","2023-11","2023-12","2023-12",
                             "2024-01","2024-01","2024-02","2024-02","2024-03","2024-03"],
                "Kategori": ["Yazılım Satışı","Personel","Yazılım Satışı","Kira",
                             "Yazılım Satışı","Pazarlama","Danışmanlık","Personel",
                             "Yazılım Satışı","Kira","Danışmanlık","Pazarlama",
                             "Yazılım Satışı","Personel","Yazılım Satışı","Kira",
                             "Danışmanlık","Pazarlama","Yazılım Satışı","Personel",
                             "Yazılım Satışı","Kira","Danışmanlık","Pazarlama",
                             "Yazılım Satışı","Personel","Yazılım Satışı","Kira",
                             "Danışmanlık","Pazarlama"],
                "Gelir":    [180000,0,195000,0,210000,0,185000,0,225000,0,240000,0,
                             260000,0,275000,0,255000,0,290000,0,310000,0,330000,0,
                             345000,0,360000,0,380000,0],
                "Gider":    [0,85000,0,12000,0,25000,0,88000,0,12000,0,28000,
                             0,90000,0,12000,0,32000,0,92000,0,12000,0,35000,
                             0,95000,0,13000,0,38000],
            })
            with st.spinner("Demo verisi yükleniyor..."):
                try:
                    engine = FinancialEngine.from_dataframe(demo_df)
                    st.session_state.update(
                        engine=engine,
                        rapor=engine.full_report(),
                        df=engine.df,
                        sirket_adi="TechNova Demo",
                        nav_sayfa="genel",
                    )
                    st.success("✅ Demo verisi yüklendi!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Hata: {ex}")

    with col_yukle:
        if st.button("📂  Veri Girişi Sayfasına Git", use_container_width=True, key="btn_goto_veri"):
            st.session_state["nav_sayfa"] = "veri"
            st.rerun()

    # ── Modül tanıtım kartları ────────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:9px;font-weight:700;letter-spacing:.1em;'
        'text-transform:uppercase;color:#9CA3AF;'
        'padding:20px 0 10px;border-top:1px solid #E8EAEF;margin-top:8px;">'
        'Platform Özellikleri</div>',
        unsafe_allow_html=True
    )
    moduller = [
        ("Finansal Analiz",   "Gelir, gider, karlılık, nakit, borç — tam finansal görünürlük"),
        ("Bütçe & Gerçek",    "Sapma analizi, projeksiyon, kategori bazlı takip"),
        ("Tahmin & Senaryo",  "Prophet ile 12 aya kadar gelir tahmini, what-if analizi"),
        ("Müşteri & Ürün",    "RFM segmentasyonu, churn riski, ürün karlılığı"),
        ("Yatırım Merkezi",   "ROI, NPV, IRR, Monte Carlo simülasyonu"),
        ("AI & CFO Agent",    "Groq/Gemini destekli stratejik öneri ve finansal sohbet"),
    ]
    c1, c2 = st.columns(2)
    for i, (title, desc) in enumerate(moduller):
        col = c1 if i % 2 == 0 else c2
        with col:
            st.markdown(
                f'<div style="background:#FFFFFF;border:1px solid #E8EAEF;'
                f'border-left:3px solid #1B3A6B;border-radius:0 8px 8px 0;'
                f'padding:11px 14px;margin-bottom:8px;">'
                f'<div style="font-size:12px;font-weight:600;color:#0F2252;margin-bottom:3px;">{title}</div>'
                f'<div style="font-size:11px;color:#6B7280;line-height:1.5;">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# VERİ GİRİŞ SAYFASI — rapor olmasa da açılır
# ─────────────────────────────────────────────────────────────────────────────
_sayfa = st.session_state.get("nav_sayfa", "genel")

if _sayfa == "veri":
    render_page_header(
        "Veri Girişi",
        "CSV, Excel veya Google Sheets bağlantısı ile analizi başlatın",
        badge_text="Veri Yükleme", badge_level="brand"
    )

    tab_csv, tab_sheets, tab_manuel = st.tabs(["📂 CSV / Excel", "🔗 Google Sheets", "✏️ Manuel Giriş"])

    with tab_csv:
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        max_rows = 50000
        if FIREBASE_OK:
            guard = SessionManager.get_guard()
            if guard:
                max_rows = guard.max_rows()

        uploaded = st.file_uploader(
            "CSV veya Excel dosyanızı yükleyin",
            type=["csv", "xlsx", "xls"],
            help="Gerekli sütunlar: Tarih, Kategori, Gelir, Gider"
        )

        if uploaded:
            col_onizleme, col_basla = st.columns([3, 1])
            with col_onizleme:
                try:
                    _prev = (pd.read_csv(uploaded) if uploaded.name.endswith(".csv")
                             else pd.read_excel(uploaded))
                    uploaded.seek(0)  # pointer'ı sıfırla
                    st.markdown(f"**{len(_prev):,} satır** · {list(_prev.columns)}")
                    st.dataframe(_prev.head(5), use_container_width=True, hide_index=True)
                except Exception:
                    pass

            with col_basla:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if st.button("▶ Analizi Başlat", use_container_width=True, key="btn_analiz"):
                    with st.spinner("İşleniyor..."):
                        try:
                            uploaded.seek(0)
                            df = (pd.read_csv(uploaded)
                                  if uploaded.name.endswith(".csv")
                                  else pd.read_excel(uploaded))
                            if len(df) > max_rows:
                                st.warning(f"İlk {max_rows:,} satır işlendi.")
                                df = df.head(max_rows)
                            engine = FinancialEngine.from_dataframe(df)
                            rapor_ = engine.full_report()
                            st.session_state.update(
                                engine=engine,
                                rapor=rapor_,
                                df=engine.df,
                                nav_sayfa="genel",
                            )
                            if FIREBASE_OK:
                                SessionManager.save_snapshot(
                                    rapor_,
                                    st.session_state.get("sirket_adi", "Şirketim")
                                )
                            st.success("✅ Analiz tamamlandı! Dashboard'a yönlendiriliyor...")
                            st.rerun()
                        except Exception as ex:
                            st.error(f"Hata: {ex}")
        else:
            st.markdown(
                '<div style="background:#F9FAFB;border:1.5px dashed #D1D5DB;border-radius:10px;'
                'padding:32px;text-align:center;color:#9CA3AF;font-size:13px;">'
                '📁 Dosya seçin veya buraya sürükleyin<br>'
                '<span style="font-size:11px;">CSV · XLSX · XLS · Maks 50.000 satır</span>'
                '</div>',
                unsafe_allow_html=True
            )

    with tab_sheets:
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        gs_url  = st.text_input("Google Sheets URL", placeholder="https://docs.google.com/spreadsheets/d/...")
        gs_cred = st.text_input("Service Account JSON yolu", placeholder="firebase_credentials.json")
        if st.button("🔗 Bağlan ve Analiz Et", use_container_width=True, key="btn_sheets"):
            with st.spinner("Bağlanıyor..."):
                try:
                    engine = FinancialEngine.from_google_sheets(gs_url, gs_cred)
                    rapor_ = engine.full_report()
                    st.session_state.update(
                        engine=engine,
                        rapor=rapor_,
                        df=engine.df,
                        nav_sayfa="genel",
                    )
                    if FIREBASE_OK:
                        SessionManager.save_snapshot(
                            rapor_,
                            st.session_state.get("sirket_adi", "Şirketim")
                        )
                    st.success("✅ Bağlandı!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Hata: {ex}")

    with tab_manuel:
        if DATA_ENTRY_OK:
            show_data_entry_tab()
        else:
            st.info("`data_entry_ui.py` bulunamadı.")

    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# Buradan itibaren: rapor mevcut olmalı
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.rapor is None:
    st.info("Önce veri yükleyin — sol menüden **Veri Girişi**'ne gidin.")
    st.stop()

rapor  = st.session_state.rapor
engine = st.session_state.engine
df     = st.session_state.df

# ── Sayfa routing ─────────────────────────────────────────────────────────────
class _Page:
    def __init__(self, active): self.active = active
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def __bool__(self): return self.active

tab_genel   = _Page(_sayfa == "genel")
tab_gelir   = _Page(_sayfa == "gelir")
tab_gider   = _Page(_sayfa == "gider")
tab_kar     = _Page(_sayfa == "kar")
tab_tahmin  = _Page(_sayfa == "tahmin")
tab_yatirim = _Page(_sayfa == "yatirim")
tab_nakit   = _Page(_sayfa == "nakit")
tab_borc    = _Page(_sayfa == "borc")
tab_sektor  = _Page(_sayfa == "sektor")
tab_profil  = _Page(_sayfa == "profil")
tab_musteri = _Page(_sayfa == "musteri")
tab_butce   = _Page(_sayfa == "butce")
tab_cfo     = _Page(_sayfa == "cfo")
tab_ai      = _Page(_sayfa == "ai")
tab_sohbet  = _Page(_sayfa == "sohbet")
tab_risk    = _Page(_sayfa == "risk")
tab_pdf     = _Page(_sayfa == "pdf")

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if tab_genel.active:
    g   = rapor["gelir"]
    e   = rapor["gider"]
    k   = rapor["karlilik"]
    s   = rapor["saglik_skoru"]
    alt = s.get("alt_skorlar", {})

    _buyume  = float(g.get("ortalama_buyume_orani", 0) or 0)
    _kar     = float(k.get("toplam_net_kar", 0) or 0)
    _skor    = int(s.get("skor", 0) or 0)
    _skat    = s.get("kategori", "")
    _marj    = float(k.get("kar_marji", 0) or 0)
    _gider_o = round(e["toplam_gider"] / g["toplam_gelir"] * 100, 1) if g.get("toplam_gelir") else 0
    _sirket  = st.session_state.get("sirket_adi", "Şirket")
    _s_level = "success" if _skor >= 65 else "warning" if _skor >= 40 else "danger"
    _rol     = st.session_state.get("rol", "cfo")
    _s_acc   = "#059669" if _skor >= 65 else "#D97706" if _skor >= 40 else "#DC2626"
    _by      = "güçlü büyüme" if _buyume >= 10 else "ılımlı büyüme" if _buyume >= 0 else "gerileme"
    _mj      = "sağlıklı" if _marj >= 20 else "baskı altında" if _marj >= 10 else "kritik"

    # ── Topbar ──────────────────────────────────────────────────────────────
    render_topbar(
        sirket_adi=_sirket,
        donem=f'{g.get("donem_baslangic","—")} – {g.get("donem_bitis","—")}',
        saglik_badge=f"{_skat} · {_skor}/100",
        saglik_level=_s_level,
    )

    # ── Exec Summary ────────────────────────────────────────────────────────
    render_exec_summary(
        f"{_sirket} {g.get('ay_sayisi',0)} aylık dönemde <strong>{_by}</strong> kaydetti. "
        f"Toplam gelir <strong>{fmt(g['toplam_gelir'])}</strong>; "
        f"net kar marjı <strong>%{_marj}</strong> — {_mj}. "
        f"Finansal sağlık skoru: <strong>{_skor}/100 ({_skat})</strong>."
    )

    # ── KPI Satırı 1 ────────────────────────────────────────────────────────
    render_kpi_row([
        {"label": "Toplam Gelir",  "value": fmt(g["toplam_gelir"]),
         "delta": f'Ort. {fmt(g["ortalama_aylik_gelir"])}/ay', "positive": True},
        {"label": "Net Kar",       "value": fmt(_kar),
         "delta": f"Marj %{_marj}", "positive": _kar >= 0},
        {"label": "Gider / Gelir", "value": f"%{_gider_o}",
         "delta": "Hedef <%80", "positive": _gider_o < 80,
         "accent_color": "#D97706"},
        {"label": "Sağlık Skoru",  "value": f"{_skor}/100",
         "delta": _skat, "positive": _skor >= 60,
         "accent_color": _s_acc, "color": _s_acc},
    ], height=118)

    # ── Stat Strip ──────────────────────────────────────────────────────────
    render_stat_strip([
        {"label": "Aylık Ort. Gelir",  "value": fmt(g["ortalama_aylik_gelir"])},
        {"label": "Sabit Gider",       "value": f'%{e["sabit_gider_orani"]}'},
        {"label": "Brüt Kar Marjı",    "value": f'%{k.get("brut_kar_marji", 0)}'},
        {"label": "Net Kar Marjı",     "value": f"%{_marj}"},
    ])

    # ── 2 Sütun: Grafik + Sağlık ────────────────────────────────────────────
    col_main, col_side = st.columns([2, 1], gap="medium")

    with col_main:
        render_section("Aylık Finansal Performans")
        mp = engine.profit.monthly_profit()
        if not mp.empty:
            fig = go.Figure()
            fig.add_bar(
                x=mp["Dönem"], y=mp["Gelir"], name="Gelir",
                marker_color="#0F2252", opacity=0.88,
            )
            fig.add_bar(
                x=mp["Dönem"], y=mp["Gider"], name="Gider",
                marker_color="#E2E5EB", opacity=0.95,
            )
            fig.add_scatter(
                x=mp["Dönem"], y=mp["NetKar"], name="Net Kar",
                mode="lines+markers",
                line=dict(color="#059669", width=2.5),
                marker=dict(size=6, color="#059669", symbol="circle"),
            )
            fig.update_layout(
                barmode="group", height=290,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#F9FAFB",
                font=dict(color="#8B93A8", family="-apple-system,Segoe UI,Arial", size=11),
                margin=dict(l=8, r=8, t=8, b=8),
                xaxis=dict(gridcolor="#F0F2F5", showgrid=True, zeroline=False,
                           tickfont=dict(size=10, color="#8B93A8")),
                yaxis=dict(gridcolor="#F0F2F5", showgrid=True, zeroline=False,
                           tickfont=dict(size=10, color="#8B93A8")),
                legend=dict(bgcolor="rgba(255,255,255,.9)", bordercolor="#E2E5EB",
                            borderwidth=1, font=dict(size=11)),
                hoverlabel=dict(bgcolor="#fff", bordercolor="#E2E5EB",
                                font=dict(size=11, color="#0F1729")),
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_side:
        render_section("Finansal Sağlık")
        render_health_bars({
            "Karlılık":       alt.get("karlilik", 0),
            "Büyüme":         alt.get("buyume", 0),
            "Gider Kontrolü": alt.get("gider_kontrolu", 0),
            "Nakit":          alt.get("nakit", 0),
        })

    # ── 3 Sütun: Risk / CFO Önerileri / Kategori ────────────────────────────
    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        render_section("Aktif Riskler")
        _riskler = []
        if _gider_o > 80:
            _riskler.append({"title": "Gider/Gelir oranı kritik",
                             "body": f"Oran %{_gider_o} — %80 eşiğini aştı.", "level": "danger"})
        elif _gider_o > 70:
            _riskler.append({"title": "Gider oranı yükseliyor",
                             "body": f"Oran %{_gider_o} — trend izlenmeli.", "level": "warning"})
        if _marj < 10:
            _riskler.append({"title": "Kar marjı baskı altında",
                             "body": f"Marj %{_marj} — hedef %15.", "level": "warning"})
        if _buyume < 0:
            _riskler.append({"title": "Negatif büyüme",
                             "body": f"Aylık ort. %{_buyume}.", "level": "danger"})
        if not _riskler:
            _riskler.append({"title": "Risk yok",
                             "body": "Tüm göstergeler hedef bandında.", "level": "success"})
        render_alerts(_riskler)

    with c2:
        render_section("CFO Önerileri")
        _oner = []
        if _gider_o > 70:
            _oner.append({"title": "Sabit gideri optimize et",
                          "body": "Sabit gider oranı yüksek. %10 azaltma ile önemli kar artışı sağlanabilir.",
                          "level": "info"})
        if _marj < 15:
            _oner.append({"title": "Fiyatlandırma stratejisi gözden geçir",
                          "body": "Kar marjı hedefin altında. Fiyat artışı simülasyonu önerilir.",
                          "level": "info"})
        if _buyume >= 10:
            _oner.append({"title": "Büyüme momentumunu koru",
                          "body": "Güçlü büyüme var. Yatırım senaryosu değerlendirilebilir.",
                          "level": "success"})
        if not _oner:
            _oner.append({"title": "Finansal yapı dengeli",
                          "body": "Kritik aksiyon gerektiren alan yok. İzlemeye devam.",
                          "level": "success"})
        render_alerts(_oner)

    with c3:
        render_section("Gelir Dağılımı")
        cr = engine.revenue.revenue_by_category()
        cr = cr[cr["Toplam Gelir"] > 0].head(5)
        if not cr.empty:
            toplam = cr["Toplam Gelir"].sum()
            renkler = ["#0F2252", "#2563EB", "#059669", "#D97706", "#DC2626"]
            for i, (_, row) in enumerate(cr.iterrows()):
                pct = round(row["Toplam Gelir"] / toplam * 100, 1) if toplam else 0
                renk = renkler[i % len(renkler)]
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;'
                    f'margin-bottom:8px;">' 
                    f'<div style="width:8px;height:8px;border-radius:50%;'
                    f'background:{renk};flex-shrink:0;"></div>'
                    f'<span style="font-size:12px;color:#3D4663;flex:1;'
                    f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'
                    f'{row["Kategori"]}</span>'
                    f'<span style="font-size:12px;font-weight:700;color:#0F1729;">'
                    f'%{pct}</span></div>',
                    unsafe_allow_html=True
                )
            # Yatay renk şeridi
            serit = "".join(
                f'<div style="width:{round(row["Toplam Gelir"]/toplam*100,1)}%;'
                f'background:{renkler[i%5]};height:100%;"></div>'
                for i, (_, row) in enumerate(cr.iterrows())
            )
            st.markdown(
                f'<div style="height:6px;border-radius:3px;overflow:hidden;'
                f'display:flex;margin-top:4px;">{serit}</div>',
                unsafe_allow_html=True
            )

# ══════════════════════════════════════════════════════════════════════════════
# RİSK & ALARM
# ══════════════════════════════════════════════════════════════════════════════
if tab_risk.active:
    g    = rapor["gelir"]
    e    = rapor["gider"]
    k    = rapor["karlilik"]
    s    = rapor["saglik_skoru"]
    alt  = s.get("alt_skorlar", {})

    _skor    = int(s.get("skor", 0) or 0)
    _skat    = s.get("kategori", "")
    _marj    = float(k.get("kar_marji", 0) or 0)
    _buyume  = float(g.get("ortalama_buyume_orani", 0) or 0)
    _gider_o = round(e["toplam_gider"] / g["toplam_gelir"] * 100, 1) if g.get("toplam_gelir") else 0
    _s_level = "success" if _skor >= 65 else "warning" if _skor >= 40 else "danger"
    _s_acc   = "#059669" if _skor >= 65 else "#D97706" if _skor >= 40 else "#DC2626"
    _aktif_uyari = sum([_gider_o > 80, _marj < 10, _buyume < 0, _skor < 40])

    render_page_header(
        "Risk & Alarm Merkezi",
        "Otomatik risk tespiti · Oncelik siralaması · Aksiyon onerileri",
        badge_text="Canli Izleme", badge_level="brand",
    )

    # KPI satiri
    render_kpi_row([
        {"label": "Finansal Saglik", "value": f"{_skor}/100",
         "delta": _skat, "positive": _skor >= 60,
         "accent_color": _s_acc, "color": _s_acc},
        {"label": "Aktif Uyari",    "value": str(_aktif_uyari),
         "delta": "Izlenen risk",   "positive": _aktif_uyari == 0,
         "accent_color": "#DC2626" if _aktif_uyari > 0 else "#059669"},
        {"label": "Kar Marji",      "value": f"%{_marj}",
         "delta": "Hedef >%15",     "positive": _marj >= 15},
        {"label": "Gider Orani",    "value": f"%{_gider_o}",
         "delta": "Hedef <%80",     "positive": _gider_o < 80},
    ], height=118)

    # 3 kolon: Kritik / Orta / Firsatlar
    col_krit, col_orta, col_fir = st.columns(3, gap="medium")

    with col_krit:
        render_section("Kritik Riskler")
        _kritik = []
        if _skor < 40:
            _kritik.append({"title": "Finansal Saglik Kritik",
                "body": f"Skor {_skor}/100. Acil mudahale gerekiyor.", "level": "danger"})
        if _gider_o > 80:
            _kritik.append({"title": "Gider/Gelir Orani Kritik",
                "body": f"Oran %{_gider_o} — %80 esigini asti.", "level": "danger"})
        if _marj < 5:
            _kritik.append({"title": "Kar Marji Cok Dusuk",
                "body": f"Net kar marji %{_marj}.", "level": "danger"})
        render_alerts(_kritik if _kritik else [
            {"title": "Kritik risk yok",
             "body": "Tum ana gostergeler kabul edilebilir sinirlar icinde.",
             "level": "success"}
        ])

    with col_orta:
        render_section("Orta Seviye")
        _orta = []
        if 70 < _gider_o <= 80:
            _orta.append({"title": "Gider orani yukseliyor",
                "body": f"Oran %{_gider_o} — trend takip edilmeli.", "level": "warning"})
        if 5 <= _marj < 15:
            _orta.append({"title": "Kar marji baskida",
                "body": f"Marj %{_marj} — hedef %15'in altinda.", "level": "warning"})
        if _buyume < 0:
            _orta.append({"title": "Negatif buyume",
                "body": f"Aylik ort. %{abs(_buyume)} gerileme.", "level": "warning"})
        render_alerts(_orta if _orta else [
            {"title": "Orta seviye uyari yok",
             "body": "Dikkat gerektiren gosterge bulunmuyor.", "level": "info"}
        ])

    with col_fir:
        render_section("Firsatlar")
        _fir = []
        if _buyume >= 10:
            _fir.append({"title": "Guclu buyume",
                "body": f"Aylik %{_buyume} buyume — yatirim icin uygun.", "level": "success"})
        if _marj >= 20:
            _fir.append({"title": "Yuksek kar marji",
                "body": f"Marj %{_marj} — sektör ortalamasinin uzerinde.", "level": "success"})
        if _skor >= 65:
            _fir.append({"title": "Saglikli finansal yapi",
                "body": f"Skor {_skor}/100 ile guclu konumda.", "level": "success"})
        render_alerts(_fir if _fir else [
            {"title": "One cikan firsat yok",
             "body": "Mevcut verilerle guclu yon tespit edilemedi.", "level": "info"}
        ])

    # CFO Aksiyon Plani + Saglik Alt Skorlari + Genel Skor
    st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
    col_action, col_saglik = st.columns([2, 1], gap="medium")

    with col_action:
        render_section("CFO Aksiyon Plani")
        _aksiyonlar = []
        if _gider_o > 70:
            _aksiyonlar.append({
                "title": "Sabit gideri optimize et",
                "body":  f"Gider/gelir oran %{_gider_o}. %5 azaltma ile onemli kar artisi saglanabilir.",
                "level": "warning"
            })
        if _marj < 15:
            _aksiyonlar.append({
                "title": "Fiyatlandirma stratejisi gozden gecir",
                "body":  "Kar marji hedefin altinda. Q2 icin fiyat artisi simulasyonu onerilir.",
                "level": "info"
            })
        if _buyume >= 10:
            _aksiyonlar.append({
                "title": "Yatirim senaryosu degerlendir",
                "body":  "Guclu buyume momentum var. Nakit pozisyonu yatirim icin elverisli.",
                "level": "success"
            })
        if not _aksiyonlar:
            _aksiyonlar.append({
                "title": "Finansal yapi dengeli",
                "body":  "Kritik aksiyon gerektiren alan yok. Izlemeye devam.",
                "level": "success"
            })
        render_alerts(_aksiyonlar)

    with col_saglik:
        render_section("Finansal Saglik Alt Skorlari")
        render_health_bars({
            "Karlilik":       alt.get("karlilik", 0),
            "Buyume":         alt.get("buyume", 0),
            "Gider Kontrolu": alt.get("gider_kontrolu", 0),
            "Nakit":          alt.get("nakit", 0),
        })

        # Skor ring SVG
        hedef_pct = min(_skor, 100)
        circ = 2 * 3.14159 * 46
        offset = circ * (1 - hedef_pct / 100)
        st.markdown(
            f'<div style="text-align:center;padding:12px 0 6px;">' 
            f'<svg viewBox="0 0 120 120" width="100" height="100">' 
            f'<circle cx="60" cy="60" r="46" fill="none" stroke="#F3F5F9" stroke-width="10"/>' 
            f'<circle cx="60" cy="60" r="46" fill="none" stroke="{_s_acc}" stroke-width="10"' 
            f' stroke-dasharray="{circ:.1f}" stroke-dashoffset="{offset:.1f}"' 
            f' stroke-linecap="round" transform="rotate(-90 60 60)"/>' 
            f'<text x="60" y="54" text-anchor="middle" font-size="22" font-weight="700"' 
            f' fill="#0F1729">{_skor}</text>' 
            f'<text x="60" y="68" text-anchor="middle" font-size="9" fill="#8B93A8">/ 100</text>' 
            f'</svg>' 
            f'<div style="font-size:13px;font-weight:700;color:{_s_acc};' 
            f'background:{"#ECFDF5" if _skor>=65 else "#FFFBEB" if _skor>=40 else "#FEF2F2"};' 
            f'display:inline-block;padding:4px 14px;border-radius:20px;' 
            f'border:0.5px solid {"#6EE7B7" if _skor>=65 else "#FCD34D" if _skor>=40 else "#FCA5A5"};">' 
            f'{_skat}</div></div>',
            unsafe_allow_html=True
        )

if tab_gelir.active:
    g    = rapor["gelir"]
    k    = rapor["karlilik"]
    _bv  = float(g.get("ortalama_buyume_orani", 0) or 0)
    _max = float(g.get("max_aylik_gelir", 0) or 0)
    _min = float(g.get("min_aylik_gelir", 0) or 0)
    _en_karli = g.get("en_karli_kategori", {}).get("kategori", "—")

    render_page_header(
        "Gelir Analizi",
        f'{g.get("ay_sayisi", 0)} aylık dönem · {g.get("donem_baslangic","—")} – {g.get("donem_bitis","—")}',
        badge_text="Gelir", badge_level="brand",
    )
    render_exec_summary(
        f"Toplam gelir <strong>{fmt(g['toplam_gelir'])}</strong> — "
        f"aylık ortalama <strong>{fmt(g['ortalama_aylik_gelir'])}</strong>. "
        f"Büyüme oranı <strong>%{_bv}</strong> ile "
        f"{'güçlü seyirde' if _bv >= 10 else 'ılımlı seyirde' if _bv >= 0 else 'gerileme yaşıyor'}. "
        f"En karlı kategori <strong>{_en_karli}</strong>."
    )

    # KPI satırı
    render_kpi_row([
        {"label": "Toplam Gelir",     "value": fmt(g["toplam_gelir"]),
         "delta": f'{g.get("ay_sayisi",0)} aylık toplam', "positive": True},
        {"label": "Aylık Ortalama",   "value": fmt(g["ortalama_aylik_gelir"]),
         "delta": f"En yüksek: {fmt(_max)}", "positive": True,
         "accent_color": "#2563EB"},
        {"label": "Büyüme Oranı",     "value": f"%{_bv}",
         "delta": "Aylık ortalama", "positive": _bv >= 0},
        {"label": "En Karlı Kategori","value": _en_karli,
         "delta": "Kategori bazlı", "positive": True,
         "accent_color": "#D97706"},
    ], height=118)

    # 2 sütun: trend + kategori
    col_main, col_side = st.columns([3, 2], gap="medium")

    with col_main:
        render_section("Aylık Gelir Trendi")
        mr = engine.revenue.monthly_revenue()
        if not mr.empty:
            fig = go.Figure()
            fig.add_bar(
                x=mr["Dönem"], y=mr["Toplam Gelir"],
                marker_color="#0F2252", opacity=0.88, name="Gelir",
            )
            fig.update_layout(
                height=220,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#F9FAFB",
                font=dict(color="#8B93A8", size=11),
                margin=dict(l=8, r=8, t=8, b=8),
                xaxis=dict(gridcolor="#F0F2F5", showgrid=True, zeroline=False,
                           tickfont=dict(size=10, color="#8B93A8")),
                yaxis=dict(gridcolor="#F0F2F5", showgrid=True, zeroline=False,
                           tickfont=dict(size=10, color="#8B93A8")),
                showlegend=False,
                hoverlabel=dict(bgcolor="#fff", bordercolor="#E2E5EB",
                                font=dict(size=11, color="#0F1729")),
            )
            st.plotly_chart(fig, use_container_width=True)

        render_section("Büyüme Oranı Trendi", top_margin=8)
        gr = engine.revenue.revenue_growth_rate().dropna()
        if not gr.empty:
            renkler = ["#059669" if v >= 0 else "#DC2626"
                       for v in gr["Büyüme Oranı (%)"]]
            fig2 = go.Figure()
            fig2.add_scatter(
                x=gr["Dönem"], y=gr["Büyüme Oranı (%)"],
                fill="tozeroy", mode="lines+markers",
                line=dict(color="#0F2252", width=2.5),
                fillcolor="rgba(15,34,82,0.06)",
                marker=dict(size=6, color=renkler),
            )
            fig2.add_hline(y=0, line_dash="dash",
                           line_color="#DC2626", opacity=0.35)
            fig2.update_layout(
                height=160,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#F9FAFB",
                font=dict(color="#8B93A8", size=11),
                margin=dict(l=8, r=8, t=8, b=8),
                xaxis=dict(gridcolor="#F0F2F5", zeroline=False,
                           tickfont=dict(size=10, color="#8B93A8")),
                yaxis=dict(gridcolor="#F0F2F5", zeroline=False,
                           tickfont=dict(size=10, color="#8B93A8"),
                           ticksuffix="%"),
                showlegend=False,
                hoverlabel=dict(bgcolor="#fff", bordercolor="#E2E5EB",
                                font=dict(size=11, color="#0F1729")),
            )
            st.plotly_chart(fig2, use_container_width=True)

    with col_side:
        render_section("Kategori Dağılımı")
        cr = engine.revenue.revenue_by_category()
        cr = cr[cr["Toplam Gelir"] > 0]
        if not cr.empty:
            renkler_pie = ["#0F2252","#2563EB","#059669","#D97706","#DC2626","#7C3AED","#0891B2"]
            fig3 = go.Figure(go.Pie(
                values=cr["Toplam Gelir"],
                labels=cr["Kategori"],
                hole=0.58,
                marker=dict(colors=renkler_pie[:len(cr)],
                            line=dict(color="#fff", width=2)),
                textfont=dict(size=11),
            ))
            fig3.update_layout(
                height=200,
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=8, r=8, t=8, b=8),
                showlegend=False,
            )
            st.plotly_chart(fig3, use_container_width=True)

            toplam = cr["Toplam Gelir"].sum()
            for i, (_, row) in enumerate(cr.iterrows()):
                pct = round(row["Toplam Gelir"] / toplam * 100, 1) if toplam else 0
                renk = renkler_pie[i % len(renkler_pie)]
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">' 
                    f'<div style="width:8px;height:8px;border-radius:50%;background:{renk};flex-shrink:0;"></div>'
                    f'<span style="font-size:12px;color:#3D4663;flex:1;">{row["Kategori"]}</span>'
                    f'<span style="font-size:12px;font-weight:700;color:#0F1729;">%{pct}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    # Aylık tablo
    render_section("Aylık Gelir Tablosu")
    mr2 = engine.revenue.monthly_revenue()
    if not mr2.empty:
        mr2_display = mr2.copy()
        if "Büyüme (%)" not in mr2_display.columns:
            mr2_display["Büyüme (%)"] = mr2_display["Toplam Gelir"].pct_change() * 100
        mr2_display["Toplam Gelir"] = mr2_display["Toplam Gelir"].apply(fmt)
        st.dataframe(mr2_display, use_container_width=True, hide_index=True)

if tab_gider.active:
    e    = rapor["gider"]
    g    = rapor["gelir"]
    _sv  = float(e.get("sabit_gider_orani", 0) or 0)
    _dv  = round(100 - _sv, 1)
    _go  = round(e["toplam_gider"] / g["toplam_gelir"] * 100, 1) if g.get("toplam_gelir") else 0
    _dur = "kontrol altında" if _sv < 60 else "yüksek, optimizasyon önerilir"

    render_page_header(
        "Gider Analizi",
        f'{e.get("ay_sayisi", g.get("ay_sayisi", 0))} aylık dönem',
        badge_text="Gider", badge_level="danger",
    )
    render_exec_summary(
        f"Toplam gider <strong>{fmt(e['toplam_gider'])}</strong>. "
        f"Sabit gider oranı <strong>%{_sv}</strong> — {_dur}. "
        f"Değişken gider oranı <strong>%{_dv}</strong> ile esneklik korunuyor. "
        f"Gider/gelir oranı <strong>%{_go}</strong> — "
        f"{'hedef bandında' if _go < 80 else 'hedef üzerinde, dikkat'}."
    )

    render_kpi_row([
        {"label": "Toplam Gider",    "value": fmt(e["toplam_gider"]),
         "delta": "12 aylık toplam", "positive": False,
         "accent_color": "#DC2626"},
        {"label": "Sabit Gider",     "value": fmt(e["sabit_gider"]),
         "delta": f"%{_sv} oran", "positive": _sv < 60,
         "accent_color": "#D97706"},
        {"label": "Değişken Gider",  "value": fmt(e["degisken_gider"]),
         "delta": f"%{_dv} oran", "positive": True,
         "accent_color": "#059669"},
        {"label": "Gider / Gelir",   "value": f"%{_go}",
         "delta": "Hedef <%80", "positive": _go < 80},
    ], height=118)

    col1, col2, col3 = st.columns([2, 1, 1], gap="medium")

    with col1:
        render_section("Kategoriye Göre Gider")
        ce = engine.expense.expense_by_category()
        ce = ce[ce["Toplam Gider"] > 0]
        if not ce.empty:
            toplam_g = ce["Toplam Gider"].sum()
            renkler_g = ["#DC2626", "#D97706", "#2563EB", "#8B93A8", "#7C3AED"]
            fig = go.Figure()
            fig.add_bar(
                x=ce["Toplam Gider"], y=ce["Kategori"],
                orientation="h",
                marker_color=renkler_g[:len(ce)],
                opacity=0.88,
            )
            fig.update_layout(
                height=240,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#F9FAFB",
                font=dict(color="#8B93A8", size=11),
                margin=dict(l=8, r=8, t=8, b=8),
                xaxis=dict(gridcolor="#F0F2F5", zeroline=False,
                           tickfont=dict(size=10, color="#8B93A8")),
                yaxis=dict(gridcolor="rgba(0,0,0,0)", zeroline=False,
                           tickfont=dict(size=11, color="#3D4663")),
                showlegend=False,
                hoverlabel=dict(bgcolor="#fff", bordercolor="#E2E5EB",
                                font=dict(size=11, color="#0F1729")),
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        render_section("Sabit / Değişken")
        fv = engine.expense.fixed_vs_variable()
        fig2 = go.Figure(go.Pie(
            labels=["Sabit", "Değişken"],
            values=[fv["sabit_gider"], fv["degisken_gider"]],
            hole=0.58,
            marker=dict(
                colors=["#DC2626", "#059669"],
                line=dict(color="#fff", width=2),
            ),
            textfont=dict(size=11),
        ))
        fig2.update_layout(
            height=200,
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=8, r=8, t=8, b=8),
            legend=dict(font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown(
            f'<div style="font-size:11px;color:#3D4663;line-height:1.6;'
            f'background:#F9FAFB;border-radius:8px;padding:10px 12px;">'
            f'Sabit oran {"kontrol altında" if _sv < 60 else "yüksek"} — '
            f'%{_sv} ile {"esneklik korunuyor" if _sv < 60 else "optimizasyon önerilir"}.</div>',
            unsafe_allow_html=True
        )

    with col3:
        render_section("Risk Uyarıları")
        _uyarilar = []
        ce2 = engine.expense.expense_by_category() if not ce.empty else ce
        if not ce2.empty:
            toplam_g2 = ce2["Toplam Gider"].sum()
            en_buyuk = ce2.iloc[0]
            en_pct = round(en_buyuk["Toplam Gider"] / toplam_g2 * 100, 1) if toplam_g2 else 0
            if en_pct > 50:
                _uyarilar.append({
                    "title": f'{en_buyuk["Kategori"]} ağırlığı yüksek',
                    "body": f'Toplam giderin %{en_pct} orani - cesitlendirme onerilir.',
                    "level": "warning"
                })
        if _go > 80:
            _uyarilar.append({"title": "Gider/gelir kritik",
                              "body": f"Oran %{_go} — %80 hedefini aştı.", "level": "danger"})
        elif _go > 70:
            _uyarilar.append({"title": "Gider oranı izlenmeli",
                              "body": f"Oran %{_go} — trend takibi önerilir.", "level": "warning"})
        if _sv < 60:
            _uyarilar.append({"title": "Gider yapısı sağlıklı",
                              "body": f"Sabit oran %{_sv} — esneklik korunuyor.", "level": "success"})
        if not _uyarilar:
            _uyarilar.append({"title": "Risk yok",
                              "body": "Tüm gider göstergeleri normal.", "level": "success"})
        render_alerts(_uyarilar)

    render_section("Aylık Gider Tablosu")
    me = engine.expense.monthly_expense() if hasattr(engine.expense, "monthly_expense") else None
    if me is not None and not me.empty:
        st.dataframe(me, use_container_width=True, hide_index=True)

if tab_kar.active:
    k    = rapor["karlilik"]
    g    = rapor["gelir"]
    _km  = float(k.get("kar_marji", 0) or 0)
    _bkm = float(k.get("brut_kar_marji", 0) or 0)
    _nk  = float(k.get("toplam_net_kar", 0) or 0)
    _trd = k.get("kar_trendi", "Stabil")
    _durum = "guclu" if _km >= 20 else "orta" if _km >= 10 else "dusuk"
    _hedef_fark = round(20 - _km, 1)

    render_page_header(
        "Karlilik Analizi",
        f"Net kar marji %{_km} — {_durum}",
        badge_text="Karlilik", badge_level="success" if _km >= 15 else "warning",
    )
    render_exec_summary(
        f"Net kar <strong>{fmt(_nk)}</strong>, marj <strong>%{_km}</strong> — "
        f"{'guclu, hedefin uzerinde' if _km >= 20 else 'saglikli seviye' if _km >= 15 else 'baskida, iyilestirme gerekli'}. "
        f"Brut kar marji <strong>%{_bkm}</strong>. "
        f"Trend <strong>{_trd}</strong> yonunde."
    )

    render_kpi_row([
        {"label": "Net Kar",          "value": fmt(_nk),
         "delta": "12 aylik toplam",  "positive": _nk >= 0,
         "accent_color": "#059669" if _nk >= 0 else "#DC2626"},
        {"label": "Net Kar Marji",    "value": f"%{_km}",
         "delta": "Hedef >%15",       "positive": _km >= 15},
        {"label": "Brut Kar Marji",   "value": f"%{_bkm}",
         "delta": "Gelir - COGS",     "positive": _bkm >= 20,
         "accent_color": "#2563EB"},
        {"label": "Kar Trendi",       "value": _trd,
         "delta": "Son 3 ay",         "positive": "yuksel" in _trd.lower() or "Yuksel" in _trd,
         "accent_color": "#059669"},
    ], height=118)

    col_main, col_side = st.columns([2, 1], gap="medium")

    with col_main:
        render_section("Aylik Net Kar & Kar Marji")
        mp = engine.profit.monthly_profit()
        if not mp.empty:
            renkler_kar = ["#059669" if v >= 0 else "#DC2626" for v in mp["NetKar"]]
            fig = go.Figure()
            fig.add_bar(
                x=mp["Dönem"], y=mp["NetKar"],
                marker_color=renkler_kar,
                name="Net Kar",
                opacity=0.9,
            )
            if "KarMarji" in mp.columns:
                fig.add_scatter(
                    x=mp["Dönem"], y=mp["KarMarji"],
                    name="Kar Marji (%)",
                    yaxis="y2",
                    mode="lines+markers",
                    line=dict(color="#D97706", width=2, dash="dot"),
                    marker=dict(size=5, color="#D97706"),
                )
            fig.update_layout(
                barmode="relative", height=300,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#F9FAFB",
                font=dict(color="#8B93A8", size=11),
                margin=dict(l=8, r=8, t=8, b=8),
                xaxis=dict(gridcolor="#F0F2F5", zeroline=False,
                           tickfont=dict(size=10, color="#8B93A8")),
                yaxis=dict(gridcolor="#F0F2F5", zeroline=True,
                           zerolinecolor="#E2E5EB", zerolinewidth=1,
                           tickfont=dict(size=10, color="#8B93A8")),
                yaxis2=dict(overlaying="y", side="right",
                            tickformat=".0f", ticksuffix="%",
                            tickfont=dict(size=10, color="#D97706"),
                            showgrid=False),
                legend=dict(bgcolor="rgba(255,255,255,.9)", bordercolor="#E2E5EB",
                            borderwidth=1, font=dict(size=11)),
                hoverlabel=dict(bgcolor="#fff", bordercolor="#E2E5EB",
                                font=dict(size=11, color="#0F1729")),
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_side:
        render_section("Karlilik Ozeti")

        hedef_pct = min(int(_km / 20 * 100), 100)
        st.markdown(
            f'<div style="background:#F9FAFB;border-radius:10px;padding:14px 16px;margin-bottom:10px;">' 
            f'<div style="font-size:9px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;' 
            f'color:#8B93A8;margin-bottom:8px;">Hedefe Uzaklik</div>' 
            f'<div style="display:flex;justify-content:space-between;margin-bottom:6px;">' 
            f'<span style="font-size:12px;color:#3D4663;">Mevcut %{_km}</span>' 
            f'<span style="font-size:12px;font-weight:700;color:#0F2252;">Hedef %20</span>' 
            f'</div>' 
            f'<div style="background:#E2E5EB;border-radius:3px;height:7px;overflow:hidden;">' 
            f'<div style="background:{"#059669" if _km>=20 else "#D97706"};width:{hedef_pct}%;height:100%;border-radius:3px;"></div>' 
            f'</div>' 
            f'<div style="font-size:10px;color:#8B93A8;margin-top:5px;">Hedefe %{hedef_pct} ulasildi</div>' 
            f'</div>',
            unsafe_allow_html=True
        )

        _insights = []
        if _km < 20:
            _insights.append(
                {"title": "Strateji onerisi",
                 "body": f"Sabit gideri %5 azaltmak marji %{round(_km+2,1)} seviyesine tasiyabilir.",
                 "level": "info"}
            )
        if _km >= 15:
            _insights.append(
                {"title": "Guclu yon",
                 "body": "Kar marji hedef bandinda. Buyume momentumu korunmali.",
                 "level": "success"}
            )
        if _nk < 0:
            _insights.append(
                {"title": "Acil mudahale",
                 "body": "Net kar negatif. Gider yapisi acil gozden gecirilmeli.",
                 "level": "danger"}
            )
        render_alerts(_insights if _insights else [
            {"title": "Karlilik normal", "body": "Onemli aksiyon gerektiren durum yok.", "level": "success"}
        ])

    render_section("Aylik Karlilik Tablosu")
    mp2 = engine.profit.monthly_profit()
    if not mp2.empty:
        display_cols = [c for c in ["Dönem", "Gelir", "Gider", "NetKar", "KarMarji"] if c in mp2.columns]
        mp2_disp = mp2[display_cols].copy()
        for col in ["Gelir", "Gider", "NetKar"]:
            if col in mp2_disp.columns:
                mp2_disp[col] = mp2_disp[col].apply(fmt)
        if "KarMarji" in mp2_disp.columns:
            mp2_disp["KarMarji"] = mp2_disp["KarMarji"].apply(lambda x: f"%{round(x,1)}" if x == x else "—")
        st.dataframe(mp2_disp, use_container_width=True, hide_index=True)

if tab_tahmin.active:
    render_page_header(
        "Tahmin & Senaryo",
        "Prophet destekli gelir tahmini · What-if analizi",
        badge_text="Prophet Aktif", badge_level="brand",
    )
    if not gate("tahmin", "Gelecek Tahmini"):
        st.stop()

    tab_fc, tab_sen = st.tabs(["Gelir Tahmini", "Senaryo Analizi"])

    with tab_fc:
        if not FORECAST_OK:
            render_alerts([{"title": "Prophet veya statsmodels kurulu degil",
                "body": "requirements.txt dosyasini kontrol edin.", "level": "danger"}])
        else:
            from forecast_engine import get_backend_info
            bi = get_backend_info()
            col_ctrl, col_main = st.columns([1, 3], gap="medium")

            with col_ctrl:
                render_section("Ayarlar")
                ay = st.slider("Tahmin Suresi (Ay)", 1, 12, 3, key="fc_ay")
                if st.button("Tahmin Uret", use_container_width=True, key="btn_fc"):
                    with st.spinner("Model egitiliyor..."):
                        try:
                            sonuc = ForecastEngine(df).summary_report(ay=ay)
                            st.session_state["forecast"] = sonuc
                            st.success("Hazir!")
                        except Exception as ex:
                            st.error(f"Hata: {ex}")
                st.markdown(
                    f'<div style="background:#EEF2FF;border:0.5px solid #C7D2FE;'
                    f'border-radius:8px;padding:10px 12px;margin-top:8px;'
                    f'font-size:11px;color:#1E3A8A;line-height:1.6;">'
                    f'<strong>Motor:</strong> {bi["label"]}</div>',
                    unsafe_allow_html=True
                )

                if st.session_state.get("forecast"):
                    sonuc = st.session_state.forecast
                    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
                    render_section("Senaryo Ozeti", top_margin=8)
                    _bv = sonuc["buyume_beklentisi"]
                    for sen_label, gelir_mult, gider_mult, level, renk in [
                        ("Optimistik", 1.20, 0.95, "success", "#059669"),
                        ("Baz",        1.10, 1.00, "info",    "#0F2252"),
                        ("Pesimistik", 0.95, 1.10, "danger",  "#DC2626"),
                    ]:
                        st.markdown(
                            f'<div style="background:{"#ECFDF5" if level=="success" else "#EEF2FF" if level=="info" else "#FEF2F2"};'
                            f'border:0.5px solid {"#6EE7B7" if level=="success" else "#C7D2FE" if level=="info" else "#FCA5A5"};'
                            f'border-radius:8px;padding:10px 12px;margin-bottom:6px;">'
                            f'<div style="font-size:9px;font-weight:700;color:{renk};letter-spacing:.08em;text-transform:uppercase;margin-bottom:3px;">{sen_label}</div>'
                            f'<div style="font-size:16px;font-weight:700;color:{renk};">{"+%20" if level=="success" else "+%10" if level=="info" else "-%5"} gelir</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

            with col_main:
                if st.session_state.get("forecast"):
                    sonuc = st.session_state.forecast
                    render_kpi_row([
                        {"label": "Toplam Tahmin",     "value": fmt(sonuc["toplam_tahmin"]),
                         "delta": f'{sonuc["ay_sayisi"]} aylik', "positive": True},
                        {"label": "Aylik Ortalama",    "value": fmt(sonuc["ortalama_tahmin"]),
                         "delta": "Tahmin", "positive": True, "accent_color": "#2563EB"},
                        {"label": "Buyume Beklentisi", "value": f'%{sonuc["buyume_beklentisi"]}',
                         "delta": "Projeksiyon", "positive": sonuc["buyume_beklentisi"] >= 0},
                        {"label": "Guven Araligi",     "value": "%90",
                         "delta": "Prophet CI", "positive": True, "accent_color": "#7C3AED"},
                    ], height=118)

                    t_df = sonuc["tahmin_tablosu"]
                    mr   = engine.revenue.monthly_revenue()
                    fig  = go.Figure()
                    fig.add_scatter(
                        x=mr["Dönem"], y=mr["Toplam Gelir"], name="Gercek",
                        mode="lines+markers",
                        line=dict(color="#0F2252", width=2.5),
                        marker=dict(size=5, color="#0F2252"),
                    )
                    fig.add_scatter(
                        x=t_df["Dönem"], y=t_df["Tahmin"], name="Tahmin",
                        mode="lines+markers",
                        line=dict(color="#059669", width=2.5, dash="dot"),
                        marker=dict(size=7, symbol="diamond", color="#059669"),
                    )
                    if "Alt Sinir" in t_df.columns and "Ust Sinir" in t_df.columns:
                        fig.add_scatter(
                            x=list(t_df["Dönem"]) + list(reversed(t_df["Dönem"])),
                            y=list(t_df["Üst Sınır"]) + list(reversed(t_df["Alt Sınır"])),
                            fill="toself", fillcolor="rgba(5,150,105,0.08)",
                            line=dict(color="rgba(0,0,0,0)"), name="Guven Araligi",
                        )
                    fig.update_layout(
                        height=300,
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#F9FAFB",
                        font=dict(color="#8B93A8", size=11),
                        margin=dict(l=8, r=8, t=8, b=8),
                        xaxis=dict(gridcolor="#F0F2F5", zeroline=False,
                                   tickfont=dict(size=10, color="#8B93A8")),
                        yaxis=dict(gridcolor="#F0F2F5", zeroline=False,
                                   tickfont=dict(size=10, color="#8B93A8")),
                        legend=dict(bgcolor="rgba(255,255,255,.9)", bordercolor="#E2E5EB",
                                    borderwidth=1, font=dict(size=11)),
                        hoverlabel=dict(bgcolor="#fff", bordercolor="#E2E5EB",
                                        font=dict(size=11, color="#0F1729")),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    render_section("Tahmin Tablosu")
                    st.dataframe(t_df.style.format({
                        "Tahmin":    "{:,.0f} ₺",
                        "Alt Sinir": "{:,.0f} ₺",
                        "Ust Sinir": "{:,.0f} ₺",
                    }), use_container_width=True, hide_index=True)
                else:
                    st.markdown(
                        '<div style="background:#F9FAFB;border:1.5px dashed #D1D5DB;'
                        'border-radius:10px;padding:40px;text-align:center;'
                        'color:#8B93A8;font-size:13px;">'
                        'Sol taraftan tahmin suresini secip "Tahmin Uret" butonuna basin</div>',
                        unsafe_allow_html=True
                    )

    with tab_sen:
        if not gate("senaryo_analiz", "Senaryo Analizi"):
            st.stop()
        render_exec_summary(
            "Gelir artisi ve gider azalisi parametrelerini ayarlayarak "
            "farkli finansal senaryolarin sirketinize etkisini gozlemleyin."
        )
        col_s1, col_s2 = st.columns(2, gap="medium")
        with col_s1:
            gelir_artis  = st.slider("Gelir Artisi (%)", 0, 100, 10, 5, key="sen_gelir")
        with col_s2:
            gider_azalis = st.slider("Gider Azalisi (%)", 0, 50, 5, 5, key="sen_gider")

        sen = engine.scenario_analysis(gelir_artis/100, gider_azalis/100)
        st.session_state["senaryo_sonuc"] = sen
        mevcut, yeni, degisim = sen["mevcut"], sen["senaryo"], sen["degisim"]

        render_kpi_row([
            {"label": "Mevcut Gelir",   "value": fmt(mevcut["gelir"]),
             "delta": "Baz deger", "positive": True, "accent_color": "#0F2252"},
            {"label": "Yeni Gelir",     "value": fmt(yeni["gelir"]),
             "delta": f'+{fmt(degisim["gelir_farki"])}', "positive": True},
            {"label": "Mevcut Net Kar", "value": fmt(mevcut["net_kar"]),
             "delta": "Baz deger", "positive": mevcut["net_kar"] >= 0, "accent_color": "#0F2252"},
            {"label": "Yeni Net Kar",   "value": fmt(yeni["net_kar"]),
             "delta": f'+{fmt(degisim["kar_farki"])}', "positive": degisim["kar_farki"] >= 0},
        ], height=118)

        fig_sen = go.Figure()
        for name, vals, color in [
            ("Mevcut",  [mevcut["gelir"], mevcut["gider"], mevcut["net_kar"]], "#0F2252"),
            ("Senaryo", [yeni["gelir"],   yeni["gider"],   yeni["net_kar"]],   "#059669"),
        ]:
            fig_sen.add_bar(name=name, x=["Gelir","Gider","Net Kar"],
                            y=vals, marker_color=color, opacity=0.88)
        fig_sen.update_layout(
            barmode="group", height=280,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#F9FAFB",
            font=dict(color="#8B93A8", size=11),
            margin=dict(l=8, r=8, t=8, b=8),
            xaxis=dict(gridcolor="#F0F2F5", zeroline=False),
            yaxis=dict(gridcolor="#F0F2F5", zeroline=False),
            legend=dict(bgcolor="rgba(255,255,255,.9)", bordercolor="#E2E5EB",
                        borderwidth=1, font=dict(size=11)),
        )
        st.plotly_chart(fig_sen, use_container_width=True)

if tab_yatirim.active:
    render_page_header(
        "Yatirim Merkezi",
        "ROI · NPV · IRR · Monte Carlo simulasyonu",
        badge_text="Yatirim", badge_level="brand",
    )
    if not INVESTMENT_OK:
        render_alerts([{"title": "investment_engine.py bulunamadi",
            "body": "Modul yuklenemedi.", "level": "danger"}])
    else:
        show_investment_tab()

# ══════════════════════════════════════════════════════════════════════════════
# NAKİT AKIŞI
# ══════════════════════════════════════════════════════════════════════════════
if tab_nakit.active:
    render_page_header(
        "Nakit Akisi",
        "Operasyonel nakit · Burn rate · Likidite analizi",
        badge_text="Nakit", badge_level="brand",
    )
    if not CASHFLOW_OK:
        render_alerts([{"title": "cashflow_debt_ui.py bulunamadi",
            "body": "Modül yuklenemedi.", "level": "danger"}])
    else:
        show_cashflow_tab(fin_engine=engine, fin_rapor=rapor)

# ══════════════════════════════════════════════════════════════════════════════
# BORÇ
# ══════════════════════════════════════════════════════════════════════════════
if tab_borc.active:
    render_page_header(
        "Borc & Finansman",
        "Borc yapisi · Odeme takvimi · Faiz analizi",
        badge_text="Borc", badge_level="warning",
    )
    if not CASHFLOW_OK:
        render_alerts([{"title": "cashflow_debt_ui.py bulunamadi",
            "body": "Modul yuklenemedi.", "level": "danger"}])
    else:
        show_debt_tab(fin_rapor=rapor)

# ══════════════════════════════════════════════════════════════════════════════
# SEKTÖR
# ══════════════════════════════════════════════════════════════════════════════
if tab_sektor.active:
    render_page_header(
        "Sektor Benchmark",
        "Rakip karsilastirma · Sektör ortalamalari · Pozisyon analizi",
        badge_text="Benchmark", badge_level="brand",
    )
    if not SECTOR_OK:
        render_alerts([{"title": "sector_ui.py bulunamadi",
            "body": "Modul yuklenemedi.", "level": "danger"}])
    else:
        show_sector_tab(df=df, rapor=rapor,
                        sirket_adi=st.session_state.get("sirket_adi","Sirketim"),
                        gemini=st.session_state.gemini if st.session_state.ai_active else None)

# ══════════════════════════════════════════════════════════════════════════════
# ŞİRKET PROFİLİ
# ══════════════════════════════════════════════════════════════════════════════
if tab_profil.active:
    render_page_header(
        "Sirket Profili & Sektor",
        "Sirket bilgileri · Sektör konumu · Benchmark hedefleri",
        badge_text="Profil", badge_level="brand",
    )
    if not COMPANY_OK:
        render_alerts([{"title": "company_ui.py bulunamadi",
            "body": "Modul yuklenemedi.", "level": "danger"}])
    else:
        show_company_tab(fin_rapor=rapor)

# ══════════════════════════════════════════════════════════════════════════════
# MÜŞTERİ & ÜRÜN
# ══════════════════════════════════════════════════════════════════════════════
if tab_musteri.active:
    render_page_header(
        "Musteri & Urun Analizi",
        "RFM segmentasyonu · Churn riski · Urun karlilik",
        badge_text="Musteri", badge_level="brand",
    )
    if not CUSTOMER_OK:
        render_alerts([{"title": "customer_ui.py bulunamadi",
            "body": "Modul yuklenemedi.", "level": "danger"}])
    else:
        show_customer_tab(df=df)

# ══════════════════════════════════════════════════════════════════════════════
# BÜTÇE
# ══════════════════════════════════════════════════════════════════════════════
if tab_butce.active:
    render_page_header(
        "Butce & Gerceklesen",
        "Sapma analizi · Kategori bazli takip · Projeksiyon",
        badge_text="Butce", badge_level="brand",
    )
    if not BUDGET_OK:
        render_alerts([{"title": "budget_ui.py bulunamadi",
            "body": "Modul yuklenemedi.", "level": "danger"}])
    else:
        show_budget_tab(df=df, fin_rapor=rapor)

# ══════════════════════════════════════════════════════════════════════════════
# CFO AGENT
# ══════════════════════════════════════════════════════════════════════════════
if tab_cfo.active:
    if not CFO_OK:
        st.error("`cfo_ui.py` bulunamadı.")
    else:
        show_cfo_tab(
            fin_rapor=rapor,
            sirket_adi=st.session_state.get("sirket_adi","Şirketim"),
            ai_engine=st.session_state.gemini if st.session_state.ai_active else None,
            cf_rapor=st.session_state.get("cf_rapor"),
            debt_rapor=st.session_state.get("debt_rapor"),
        )

# ══════════════════════════════════════════════════════════════════════════════
# AI ANALİZ
# ══════════════════════════════════════════════════════════════════════════════
if tab_ai.active:
    render_page_header("AI Finansal Analiz", "Groq · Gemini · Otomatik yorum")
    if not gate("ai_yorum", "AI Yorumları"):
        st.stop()
    if not GEMINI_OK:
        st.error("`groq` veya `google-generativeai` kurulu değil.")
        st.stop()

    # AI aktivasyon
    if not st.session_state.ai_active:
        st.markdown("#### AI Motorunu Aktive Et")
        provider = st.radio("Servis", ["Groq (Ücretsiz, Hızlı)", "Gemini"], horizontal=True)
        if "Groq" in provider:
            api_key = GROQ_API_KEY_ENV or st.text_input("Groq API Key", type="password",
                        help="console.groq.com → API Keys")
            chosen  = "groq"
        else:
            api_key = GEMINI_API_KEY_ENV or st.text_input("Gemini API Key", type="password",
                        help="aistudio.google.com/app/apikey")
            chosen  = "gemini"
        if api_key and st.button("🔓 Aktive Et", key="btn_ai_aktif"):
            try:
                st.session_state.gemini    = GeminiEngine(api_key=api_key, provider=chosen)
                st.session_state.ai_active = True
                st.success(f"✅ {provider} aktif!")
                st.rerun()
            except Exception as ex:
                st.error(f"Hata: {ex}")
    else:
        st.success("🟢 AI Aktif")
        if st.button("Devre Dışı Bırak", key="btn_ai_off"):
            st.session_state.ai_active = False; st.rerun()
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📊 Tam Analiz Üret", use_container_width=True):
                rp = dict(rapor)
                if "cp_profile" in st.session_state:
                    rp["sirket_profili"] = st.session_state["cp_profile"].to_dict()
                render_section("Analiz Raporu")
                ph = st.empty()
                st.session_state["ai_analiz"] = \
                    st.session_state.gemini.analyze_stream(rp, ph)
        with c2:
            if st.button("🎯 Stratejik Öneriler", use_container_width=True):
                render_section("Stratejik Öneriler")
                ph2 = st.empty()
                st.session_state["ai_strateji"] = \
                    st.session_state.gemini.strategic_recommendations_stream(rapor, ph2)

        # Önceki oturumdan kalan sonuçları göster
        for key, title in [("ai_analiz","Analiz Raporu"), ("ai_strateji","Stratejik Öneriler")]:
            if st.session_state.get(key):
                render_section(title)
                st.markdown(
                    f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
                    f'border-radius:12px;padding:16px 20px;color:#334155;'
                    f'font-size:0.88rem;line-height:1.8;white-space:pre-wrap;">'
                    f'{st.session_state[key]}</div>',
                    unsafe_allow_html=True
                )

# ══════════════════════════════════════════════════════════════════════════════
# AI SOHBET
# ══════════════════════════════════════════════════════════════════════════════
if tab_sohbet.active:
    render_page_header("AI Finansal Asistan", "Sorularınızı doğal dilde sorun")
    if not gate("ai_sohbet", "AI Sohbet"):
        st.stop()
    if not GEMINI_OK:
        st.error("`groq` veya `google-generativeai` kurulu değil.")
        st.stop()

    if not st.session_state.ai_active:
        st.info("Önce **AI Analiz** sayfasından AI motorunu aktive edin.")
        if st.button("→ AI Analiz sayfasına git"):
            st.session_state["nav_sayfa"] = "ai"; st.rerun()
    else:
        # Hızlı sorular
        for col, soru in zip(st.columns(4), [
            "Şirketim karlı mı?", "En büyük giderim?",
            "Geliri nasıl artırırım?", "Nakit akışım sağlıklı mı?"
        ]):
            with col:
                if st.button(soru, key=f"qs_{soru}", use_container_width=True):
                    st.session_state.chat_history.append({"role":"user","content":soru})
                    ph = st.empty()
                    cevap = st.session_state.gemini.chat_stream(soru, rapor, ph)
                    st.session_state.chat_history.append({"role":"ai","content":cevap})
                    st.rerun()

        # Sohbet geçmişi
        for msg in st.session_state.chat_history:
            ikon = "👤" if msg["role"] == "user" else "🤖"
            align = "right" if msg["role"] == "user" else "left"
            bg    = "#EEF2FF" if msg["role"] == "user" else "#F8FAFC"
            border= "#C7D2FE" if msg["role"] == "user" else "#E2E8F0"
            st.markdown(
                f'<div style="text-align:{align};margin:6px 0;">'
                f'<div style="display:inline-block;max-width:80%;background:{bg};'
                f'border:1px solid {border};border-radius:12px;padding:10px 14px;'
                f'font-size:13px;color:#334155;line-height:1.6;">'
                f'{ikon} {msg["content"]}</div></div>',
                unsafe_allow_html=True
            )

        # Input
        ci, cs = st.columns([5, 1])
        with ci:
            user_input = st.text_input("Sorunuzu yazın...", key="chat_input",
                                       label_visibility="collapsed",
                                       placeholder="Örn: Hangi kategoride büyüme var?")
        with cs:
            if st.button("➤", use_container_width=True) and user_input:
                st.session_state.chat_history.append({"role":"user","content":user_input})
                ph = st.empty()
                cevap = st.session_state.gemini.chat_stream(user_input, rapor, ph)
                st.session_state.chat_history.append({"role":"ai","content":cevap})
                st.rerun()

        if st.session_state.chat_history:
            if st.button("🗑 Sohbeti Temizle", key="btn_clear_chat"):
                st.session_state.chat_history = []
                if st.session_state.gemini:
                    st.session_state.gemini.reset_chat()
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PDF RAPOR
# ══════════════════════════════════════════════════════════════════════════════
if tab_pdf.active:
    render_page_header("PDF Rapor", "Tek tıkla profesyonel rapor üretimi")
    if not gate("pdf_rapor", "PDF Rapor"):
        st.stop()
    if PDF_OK and st.session_state.rapor:
        show_pdf_download_button(
            rapor      = st.session_state.rapor,
            engine     = st.session_state.engine,
            sirket_adi = st.session_state.sirket_adi,
            ai_yorum   = st.session_state.ai_analiz,
            senaryo    = st.session_state.senaryo_sonuc,
            tahmin     = st.session_state.forecast,
            key        = "main_pdf",
        )
    elif not PDF_OK:
        st.error("`pdf_report.py` veya `reportlab` bulunamadı.")
    else:
        st.info("PDF oluşturmak için önce veri yükleyin.")

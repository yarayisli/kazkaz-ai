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
    from llm_guardrail import Guardrail
    GUARDRAIL_OK = True
except ImportError:
    GUARDRAIL_OK = False

try:
    from llm_cache import LLMCache, InMemoryCacheBackend
    LLM_CACHE_OK = True
except ImportError:
    LLM_CACHE_OK = False

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

try:
    from usage_tracker import UsageTracker
    from admin_ui import show_admin_tab, is_admin
    ADMIN_OK = True
except ImportError:
    ADMIN_OK = False
    def is_admin(): return False

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
SENTRY_DSN           = get_secret("SENTRY_DSN")
APP_ENV              = get_secret("APP_ENV", "production")


# ── Sentry — hata bildirim (opsiyonel; SENTRY_DSN yoksa devre dışı) ──────────

def _init_sentry():
    """
    Sentry-sdk'yi başlat. SENTRY_DSN secrets'ta yoksa hiçbir şey yapmaz
    (uygulama aynen çalışır).

    Kurulum:
      Streamlit → Manage app → Settings → Secrets:
        SENTRY_DSN = "https://xxxxx@sentry.io/yyyy"
        APP_ENV    = "production"   # veya "dev", "staging"

    Sentry.io'da ücretsiz plan 5000 event/ay verir; küçük-orta ölçekli
    KOBİ SaaS için fazlasıyla yeterli.
    """
    if not SENTRY_DSN:
        return False
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=APP_ENV,
            # Performans örneklemesi — tüm istekleri değil, %10'unu izle
            traces_sample_rate=0.10,
            # PII gizle: kullanıcı IP'si vs. varsayılan olarak gönderilmesin
            send_default_pii=False,
            # Streamlit rerun'ları çok event üretir — spam olmasın diye limit
            max_breadcrumbs=30,
            release="kazkaz-ai@v2.1",
        )
        return True
    except ImportError:
        return False
    except Exception:
        return False

SENTRY_ACTIVE = _init_sentry()


# ── Usage tracker — Firestore counter tabanlı ────────────────────────────────

import os as _os

def _get_firestore_client():
    """
    firebase_admin ile firestore client döndür. Cred yoksa None.
    admin_ui bu client'ı kullanarak usage_daily koleksiyonunu okur/yazar.
    """
    if not FIREBASE_CRED_PATH or not _os.path.exists(FIREBASE_CRED_PATH):
        return None
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        if not firebase_admin._apps:
            firebase_admin.initialize_app(
                credentials.Certificate(FIREBASE_CRED_PATH)
            )
        return firestore.client()
    except Exception:
        return None


def _get_usage_tracker():
    """Session-level tek UsageTracker. Firestore yoksa no-op."""
    if not ADMIN_OK:
        return None
    if "usage_tracker" not in st.session_state:
        fs_client = _get_firestore_client()
        st.session_state.usage_tracker = UsageTracker(fs_client)
    return st.session_state.usage_tracker


def _track(event: str, page: str = None):
    """Kısayol: mevcut kullanıcı bilgileri ile track."""
    tracker = _get_usage_tracker()
    if not tracker:
        return
    try:
        profile = st.session_state.get("user_profile") or {}
        tracker.track(
            event=event,
            user_id=_current_user_id(),
            page=page,
            plan=profile.get("plan", "free"),
        )
    except Exception:
        pass


# ── LLM guardrail + cache — oturum boyunca tek örnek ─────────────────────────

def _current_user_id() -> str:
    """Rate-limit ve cache anahtarı için kullanıcı kimliği."""
    try:
        user = st.session_state.get("user") or {}
        return user.get("localId") or "_anon"
    except Exception:
        return "_anon"


def init_ai_engine(api_key: str, provider: str) -> "GeminiEngine":
    """
    GeminiEngine kur — daima session-level guardrail + cache ile.
    Session state'de tek Guardrail ve tek LLMCache tutulur (paylaşımlı sayaç).
    """
    if GUARDRAIL_OK and "llm_guardrail" not in st.session_state:
        # Free plan için 30 çağrı/60 sn, Pro/Uzman için daha yüksek olabilir
        st.session_state.llm_guardrail = Guardrail(
            rate_limit_calls=30, rate_limit_window=60,
        )
    if LLM_CACHE_OK and "llm_cache" not in st.session_state:
        st.session_state.llm_cache = LLMCache(
            InMemoryCacheBackend(), ttl_hours=24,
        )
    kwargs = {"api_key": api_key, "provider": provider, "user_id": _current_user_id()}
    if GUARDRAIL_OK:
        kwargs["guardrail"] = st.session_state.llm_guardrail
    if LLM_CACHE_OK:
        kwargs["cache"] = st.session_state.llm_cache
    return GeminiEngine(**kwargs)

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

# ── Landing Sayfası ───────────────────────────────────────────────────────────
def show_landing_page():
    """
    Native Streamlit landing sayfası (segfault-safe).
    components.html kullanmaz — sadece st.markdown + st.columns + st.button.
    """

    # ── Global CSS ──
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700;800;900&display=swap');
    .kz *{font-family:'Hanken Grotesk',system-ui,sans-serif;box-sizing:border-box}

    /* Hero */
    .kz-hero{
        background:linear-gradient(135deg,#0A1628 0%,#0F2252 40%,#1B3A6B 100%);
        border-radius:20px;padding:64px 32px 48px;text-align:center;
        position:relative;overflow:hidden;margin-bottom:32px;
    }
    .kz-hero::before{
        content:'';position:absolute;top:-60%;right:-20%;width:600px;height:600px;
        background:radial-gradient(circle,rgba(124,58,237,.15) 0%,transparent 70%);
    }
    .kz-hero::after{
        content:'';position:absolute;bottom:-40%;left:-10%;width:500px;height:500px;
        background:radial-gradient(circle,rgba(5,150,105,.1) 0%,transparent 70%);
    }
    .kz-eyebrow{
        display:inline-flex;align-items:center;gap:6px;
        background:rgba(255,255,255,.1);backdrop-filter:blur(8px);
        color:#C7D2FE;font-size:11px;font-weight:800;letter-spacing:.1em;
        padding:6px 16px;border-radius:24px;text-transform:uppercase;margin-bottom:24px;
        border:1px solid rgba(255,255,255,.08);
    }
    .kz-h1{
        font:900 48px/1.08 'Hanken Grotesk',sans-serif;color:#fff;
        letter-spacing:-.03em;margin:0 auto 18px;max-width:760px;position:relative;z-index:1;
    }
    .kz-h1 .grad{
        background:linear-gradient(90deg,#818CF8,#A78BFA,#C084FC);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
    }
    .kz-sub{
        font:400 17px/1.7 'Hanken Grotesk',sans-serif;color:rgba(255,255,255,.65);
        max-width:580px;margin:0 auto 28px;position:relative;z-index:1;
    }
    .kz-trust{
        display:flex;justify-content:center;gap:24px;flex-wrap:wrap;
        margin-top:20px;position:relative;z-index:1;
    }
    .kz-trust span{
        font:600 11px 'Hanken Grotesk',sans-serif;color:rgba(255,255,255,.45);
        letter-spacing:.04em;display:flex;align-items:center;gap:5px;
    }
    .kz-trust span b{color:rgba(255,255,255,.7)}

    /* Dashboard preview */
    .kz-dash{
        background:#fff;border:1px solid #E2E5EB;border-radius:16px;
        padding:24px;margin-bottom:40px;box-shadow:0 4px 24px rgba(15,34,82,.06);
    }
    .kz-dash-title{
        font:800 10px 'Hanken Grotesk',sans-serif;letter-spacing:.12em;
        text-transform:uppercase;color:#8B93A8;margin-bottom:16px;
        display:flex;align-items:center;gap:8px;
    }
    .kz-dash-title::before{
        content:'';width:6px;height:6px;border-radius:50%;background:#059669;
        box-shadow:0 0 0 3px rgba(5,150,105,.2);
    }
    .kz-kpi{
        background:#F8FAFC;border:1px solid #E8ECF1;border-radius:12px;
        padding:16px 18px;position:relative;overflow:hidden;
    }
    .kz-kpi::before{
        content:'';position:absolute;left:0;top:0;bottom:0;width:3px;
        border-radius:3px 0 0 3px;
    }
    .kz-kpi.blue::before{background:#0F2252}
    .kz-kpi.green::before{background:#059669}
    .kz-kpi.amber::before{background:#D97706}
    .kz-kpi.purple::before{background:#7C3AED}
    .kz-kpi-label{font:600 9px 'Hanken Grotesk',sans-serif;letter-spacing:.1em;text-transform:uppercase;color:#8B93A8;margin-bottom:6px}
    .kz-kpi-val{font:700 22px 'Hanken Grotesk',sans-serif;color:#0F1729;letter-spacing:-.02em;margin-bottom:4px}
    .kz-kpi-delta{font:600 11px 'Hanken Grotesk',sans-serif;padding:2px 8px;border-radius:4px;display:inline-block}
    .kz-kpi-delta.up{background:#ECFDF5;color:#059669}
    .kz-kpi-delta.neutral{background:#EEF2FF;color:#3B5998}

    /* Section headers */
    .kz-sec-eyebrow{font:800 10px 'Hanken Grotesk',sans-serif;letter-spacing:.15em;color:#7C3AED;text-transform:uppercase;text-align:center;margin-bottom:8px}
    .kz-sec-title{font:900 28px 'Hanken Grotesk',sans-serif;color:#0A1628;text-align:center;letter-spacing:-.02em;margin-bottom:8px}
    .kz-sec-sub{font:400 14px/1.6 'Hanken Grotesk',sans-serif;color:#6B7280;text-align:center;margin-bottom:28px;max-width:520px;margin-left:auto;margin-right:auto}

    /* Segment & Feature cards */
    .kz-card{
        background:#fff;border:1px solid #E8ECF1;border-radius:14px;
        padding:24px;height:100%;transition:border-color .2s,box-shadow .2s;
    }
    .kz-card:hover{border-color:#C7D2FE;box-shadow:0 4px 16px rgba(15,34,82,.06)}
    .kz-card-ico{font-size:28px;margin-bottom:12px;display:block}
    .kz-card h3{font:800 15px 'Hanken Grotesk',sans-serif;color:#0F1729;margin:0 0 8px}
    .kz-card p{font:400 13px/1.65 'Hanken Grotesk',sans-serif;color:#4B5563;margin:0}
    .kz-badge{display:inline-block;font:800 9px 'Hanken Grotesk',sans-serif;padding:4px 12px;border-radius:20px;text-transform:uppercase;letter-spacing:.08em;margin-bottom:14px}
    .kz-badge.active{background:#ECFDF5;color:#059669;border:1px solid #A7F3D0}
    .kz-badge.soon{background:#FFFBEB;color:#D97706;border:1px solid #FDE68A}

    /* Feature cards with top accent */
    .kz-fcard{
        background:#fff;border:1px solid #E8ECF1;border-radius:14px;
        padding:24px;height:100%;border-top:3px solid #0F2252;
        transition:border-color .2s,box-shadow .2s;
    }
    .kz-fcard:hover{box-shadow:0 4px 16px rgba(15,34,82,.06)}
    .kz-fcard-ico{
        width:40px;height:40px;border-radius:10px;display:flex;align-items:center;
        justify-content:center;font-size:20px;margin-bottom:14px;
    }
    .kz-fcard-ico.navy{background:#EEF2FF}
    .kz-fcard-ico.green{background:#ECFDF5}
    .kz-fcard-ico.amber{background:#FFFBEB}
    .kz-fcard-ico.purple{background:#F5F3FF}
    .kz-fcard-ico.red{background:#FEF2F2}
    .kz-fcard-ico.cyan{background:#ECFEFF}
    .kz-fcard h3{font:800 14.5px 'Hanken Grotesk',sans-serif;color:#0F1729;margin:0 0 8px}
    .kz-fcard p{font:400 13px/1.65 'Hanken Grotesk',sans-serif;color:#4B5563;margin:0}

    /* Pricing */
    .kz-price{
        background:#fff;border:1px solid #E8ECF1;border-radius:16px;
        padding:28px 24px;height:100%;display:flex;flex-direction:column;
        transition:border-color .2s,box-shadow .2s;
    }
    .kz-price:hover{border-color:#C7D2FE;box-shadow:0 4px 16px rgba(15,34,82,.06)}
    .kz-price.featured{border:2px solid #0F2252;box-shadow:0 8px 32px rgba(15,34,82,.10);position:relative}
    .kz-price-pop{
        position:absolute;top:-12px;left:50%;transform:translateX(-50%);
        background:#0F2252;color:#fff;font:800 9px 'Hanken Grotesk',sans-serif;
        padding:4px 16px;border-radius:20px;letter-spacing:.08em;text-transform:uppercase;
    }
    .kz-price-name{font:800 18px 'Hanken Grotesk',sans-serif;color:#0F1729;margin-bottom:4px}
    .kz-price-desc{font:400 12px 'Hanken Grotesk',sans-serif;color:#6B7280;margin-bottom:16px}
    .kz-price-amount{font:900 36px 'Hanken Grotesk',sans-serif;color:#0F2252;letter-spacing:-.02em}
    .kz-price-period{font:500 13px 'Hanken Grotesk',sans-serif;color:#8B93A8}
    .kz-price-divider{border:none;border-top:1px solid #F0F2F5;margin:18px 0}
    .kz-price ul{list-style:none;padding:0;margin:0 0 20px;flex:1}
    .kz-price li{
        font:400 13px/2 'Hanken Grotesk',sans-serif;color:#3D4663;
        padding-left:22px;position:relative;
    }
    .kz-price li::before{content:'';position:absolute;left:0;top:9px;width:14px;height:14px;border-radius:50%;background:#ECFDF5;border:1.5px solid #059669}
    .kz-price li::after{content:'';position:absolute;left:4px;top:13px;width:6px;height:3px;border-left:1.5px solid #059669;border-bottom:1.5px solid #059669;transform:rotate(-45deg)}
    .kz-price li.disabled{color:#C4C9D4}
    .kz-price li.disabled::before{background:#F5F5F5;border-color:#D1D5DB}
    .kz-price li.disabled::after{border-color:#D1D5DB}

    /* CTA band */
    .kz-cta-band{
        background:linear-gradient(135deg,#0A1628,#0F2252,#1B3A6B);
        color:#fff;padding:48px 32px;border-radius:18px;text-align:center;
        margin-top:32px;position:relative;overflow:hidden;
    }
    .kz-cta-band::before{
        content:'';position:absolute;top:-50%;right:-15%;width:400px;height:400px;
        background:radial-gradient(circle,rgba(124,58,237,.12) 0%,transparent 70%);
    }
    .kz-cta-band h2{font:900 30px 'Hanken Grotesk',sans-serif;color:#fff;margin:0 0 10px;position:relative;z-index:1}
    .kz-cta-band p{font:400 15px 'Hanken Grotesk',sans-serif;color:rgba(255,255,255,.6);margin:0 0 20px;position:relative;z-index:1}
    </style>
    """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # 1. HERO
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div class="kz">
    <div class="kz-hero">
      <span class="kz-eyebrow">&#9889; Dijital CFO Platformu</span>
      <h1 class="kz-h1">Finansal kararlarinizi<br><span class="grad">yapay zeka CFO'nuz</span><br>30 saniyede hazirlasın</h1>
      <p class="kz-sub">KOBİ ve startup'lar icin tam kapsamlı finansal analiz motoru.
      Verinizi yukleyin &mdash; kar fırsatlarını, risk uyarılarını ve yatırımcıya hazır raporlarınızı anında alın.</p>
      <div class="kz-trust">
        <span>&#x1F512; <b>KVKK uyumlu</b></span>
        <span>&#9889; <b>30 saniyede sonuc</b></span>
        <span>&#x1F4CA; <b>14 analiz modulu</b></span>
        <span>&#x1F916; <b>AI destekli</b></span>
      </div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    # Hero CTA
    _, hc, _ = st.columns([1.2, 1.6, 1.2])
    with hc:
        if st.button("Ucretsiz Basla  \u2192", use_container_width=True,
                     type="primary", key="enter_top"):
            st.session_state["show_landing"] = False
            st.rerun()
        st.markdown(
            "<div style='text-align:center;font-size:11.5px;color:#8B93A8;margin-top:6px;'>"
            "Kredi karti gerekmez &middot; Hemen baslayın</div>",
            unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # 2. DASHBOARD ONIZLEME
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Mini bar chart SVG
    _bars_svg = (
        '<svg viewBox="0 0 200 60" style="width:100%;height:56px;margin-top:8px">'
        '<rect x="4" y="38" width="18" height="22" rx="3" fill="#C7D2FE"/>'
        '<rect x="28" y="28" width="18" height="32" rx="3" fill="#A5B4FC"/>'
        '<rect x="52" y="20" width="18" height="40" rx="3" fill="#818CF8"/>'
        '<rect x="76" y="24" width="18" height="36" rx="3" fill="#818CF8"/>'
        '<rect x="100" y="14" width="18" height="46" rx="3" fill="#6366F1"/>'
        '<rect x="124" y="8" width="18" height="52" rx="3" fill="#4F46E5"/>'
        '<rect x="148" y="4" width="18" height="56" rx="3" fill="#4338CA"/>'
        '<rect x="172" y="0" width="18" height="60" rx="3" fill="#3730A3"/>'
        '</svg>'
    )

    st.markdown(f"""
    <div class="kz"><div class="kz-dash">
      <div class="kz-dash-title">Canli Dashboard Onizlemesi</div>
    </div></div>
    """, unsafe_allow_html=True)

    # KPI row
    kc1, kc2, kc3, kc4 = st.columns(4, gap="small")
    with kc1:
        st.markdown("""<div class="kz"><div class="kz-kpi blue">
            <div class="kz-kpi-label">Toplam Gelir</div>
            <div class="kz-kpi-val">3.42M &#8378;</div>
            <span class="kz-kpi-delta up">&#9650; %18.4 buyume</span>
        </div></div>""", unsafe_allow_html=True)
    with kc2:
        st.markdown("""<div class="kz"><div class="kz-kpi green">
            <div class="kz-kpi-label">Net Kar Marji</div>
            <div class="kz-kpi-val">%22.8</div>
            <span class="kz-kpi-delta up">Hedef uzerinde</span>
        </div></div>""", unsafe_allow_html=True)
    with kc3:
        st.markdown("""<div class="kz"><div class="kz-kpi purple">
            <div class="kz-kpi-label">Saglik Skoru</div>
            <div class="kz-kpi-val">78/100</div>
            <span class="kz-kpi-delta neutral">Iyi seviye</span>
        </div></div>""", unsafe_allow_html=True)
    with kc4:
        st.markdown(f"""<div class="kz"><div class="kz-kpi amber">
            <div class="kz-kpi-label">Aylik Buyume</div>
            <div class="kz-kpi-val">%12.6</div>
            <span class="kz-kpi-delta up">&#9650; Guclu trend</span>
        </div></div>""", unsafe_allow_html=True)

    # Mini chart
    gc1, gc2 = st.columns([2, 1], gap="small")
    with gc1:
        st.markdown(f"""<div class="kz"><div style="background:#F8FAFC;border:1px solid #E8ECF1;border-radius:12px;padding:14px 18px">
            <div style="font:600 9px 'Hanken Grotesk',sans-serif;letter-spacing:.1em;text-transform:uppercase;color:#8B93A8;margin-bottom:4px">Aylik Gelir Trendi</div>
            {_bars_svg}
        </div></div>""", unsafe_allow_html=True)
    with gc2:
        _ring_svg = (
            '<svg viewBox="0 0 100 100" style="width:80px;height:80px;display:block;margin:0 auto">'
            '<circle cx="50" cy="50" r="40" fill="none" stroke="#F0F2F5" stroke-width="8"/>'
            '<circle cx="50" cy="50" r="40" fill="none" stroke="#059669" stroke-width="8"'
            ' stroke-dasharray="251.3" stroke-dashoffset="55.3" stroke-linecap="round"'
            ' transform="rotate(-90 50 50)"/>'
            '<text x="50" y="46" text-anchor="middle" font-size="20" font-weight="800" fill="#0F1729">78</text>'
            '<text x="50" y="60" text-anchor="middle" font-size="9" fill="#8B93A8">/100</text>'
            '</svg>'
        )
        st.markdown(f"""<div class="kz"><div style="background:#F8FAFC;border:1px solid #E8ECF1;border-radius:12px;padding:14px 18px;text-align:center">
            <div style="font:600 9px 'Hanken Grotesk',sans-serif;letter-spacing:.1em;text-transform:uppercase;color:#8B93A8;margin-bottom:4px">Saglik Skoru</div>
            {_ring_svg}
        </div></div>""", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # 3. SEGMENTLER
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="kz"><div class="kz-sec-eyebrow">Kimler icin</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="kz"><div class="kz-sec-title">4 segment, tek platform</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="kz"><div class="kz-sec-sub">Startup\'dan kurumsal\'a, her olcekte finansal karar destek sistemi</div></div>', unsafe_allow_html=True)

    sc1, sc2, sc3, sc4 = st.columns(4, gap="small")
    _segments = [
        ("active", "🏢", "KOBİ'ler",        "Kurumsallasma ve buyume yolculugu. 14 modullu tek panel."),
        ("active", "🚀", "Startup'lar",      "Yatırımcıya hazır olun. Burn rate, runway, pitch metrikleri."),
        ("soon",   "🏛️", "Kurumsal",         "ESG ve risk raporlama otomasyonu. GRI/SASB uyumlu."),
        ("soon",   "💼", "Yatırımcı / Fon",  "Portfolyonuzu tek panelden izleyin. Sirket karsilastirma."),
    ]
    for col, (status, ico, title, desc) in zip([sc1, sc2, sc3, sc4], _segments):
        badge_cls = "active" if status == "active" else "soon"
        badge_txt = "Su an aktif" if status == "active" else "Yakinda"
        with col:
            st.markdown(f"""<div class="kz"><div class="kz-card">
                <span class="kz-badge {badge_cls}">{badge_txt}</span>
                <span class="kz-card-ico">{ico}</span>
                <h3>{title}</h3><p>{desc}</p>
            </div></div>""", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # 4. OZELLIKLER
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="kz"><div class="kz-sec-eyebrow">Ozellikler</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="kz"><div class="kz-sec-title">Kurumsal analiz, KOBİ fiyatina</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="kz"><div class="kz-sec-sub">Buyuk sirketlerin kullandigi finansal araclar, simdi herkes icin erislebilir</div></div>', unsafe_allow_html=True)

    _features = [
        ("📊", "navy",   "14 Analiz Modulu",       "Gelir, gider, karlilik, nakit akisi, borc, butce, musteri, yatirim, sektor benchmark."),
        ("🤖", "purple", "AI CFO Agent",            "Turkce finansal yorum, 90 gunluk aksiyon plani, karar destek — Groq/Gemini destekli."),
        ("📈", "green",  "Gelir Tahmini",           "Holt-Winters ile 12 aya kadar mevsimsellik uyumlu projeksiyon ve senaryo analizi."),
        ("🇹🇷", "amber",  "Turkiye'ye Ozel",        "Logo, Mikro, Netsis entegrasyonu. BIST sektor benchmark. Turkce muhasebe formati."),
        ("⚡", "red",    "Risk & Alarm Merkezi",    "Otomatik risk tespiti, oncelik siralamasi, kritik durum uyarilari."),
        ("📄", "cyan",   "Yatırımcı Raporlari",     "Bankaya, yatirimciya, ortaga sunulabilir PDF raporlar. Tek tikla uret."),
    ]
    for row_start in (0, 3):
        cols = st.columns(3, gap="small")
        for i, col in enumerate(cols):
            idx = row_start + i
            ico, color, title, desc = _features[idx]
            with col:
                st.markdown(f"""<div class="kz"><div class="kz-fcard">
                    <div class="kz-fcard-ico {color}">{ico}</div>
                    <h3>{title}</h3><p>{desc}</p>
                </div></div>""", unsafe_allow_html=True)
        if row_start == 0:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # 5. FIYATLANDIRMA
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="kz"><div class="kz-sec-eyebrow">Fiyatlandirma</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="kz"><div class="kz-sec-title">Sirketinize uygun plan secin</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="kz"><div class="kz-sec-sub">Her plan ile temel analizlere erisim. AI ve ileri ozellikler icin yukseltme yapin.</div></div>', unsafe_allow_html=True)

    pc1, pc2, pc3 = st.columns(3, gap="small")

    # Free
    with pc1:
        st.markdown("""<div class="kz"><div class="kz-price">
            <div class="kz-price-name">Free</div>
            <div class="kz-price-desc">Kesfetmek icin ideal</div>
            <div><span class="kz-price-amount">&#8378;0</span> <span class="kz-price-period">/ sonsuza kadar</span></div>
            <hr class="kz-price-divider">
            <ul>
                <li>Temel finansal analiz</li>
                <li>Grafikler & gorsellestirme</li>
                <li>Saglik skoru</li>
                <li>Maks 500 satir veri</li>
                <li class="disabled">AI yorumlari</li>
                <li class="disabled">Senaryo analizi</li>
                <li class="disabled">Gelir tahmini</li>
                <li class="disabled">PDF rapor</li>
            </ul>
        </div></div>""", unsafe_allow_html=True)
        if st.button("Ucretsiz Basla", use_container_width=True, key="price_free"):
            st.session_state["show_landing"] = False
            st.rerun()

    # Pro (featured)
    with pc2:
        st.markdown("""<div class="kz"><div class="kz-price featured">
            <div class="kz-price-pop">En Populer</div>
            <div class="kz-price-name">Pro</div>
            <div class="kz-price-desc">Buyuyen isletmeler icin</div>
            <div><span class="kz-price-amount">&#8378;299</span> <span class="kz-price-period">/ ay</span></div>
            <hr class="kz-price-divider">
            <ul>
                <li>Tum temel ozellikler</li>
                <li>AI finansal yorumlar</li>
                <li>AI sohbet asistani</li>
                <li>Senaryo analizi</li>
                <li>Maks 5.000 satir veri</li>
                <li>100 AI mesaj / ay</li>
                <li class="disabled">Gelir tahmini</li>
                <li class="disabled">PDF rapor</li>
            </ul>
        </div></div>""", unsafe_allow_html=True)
        if st.button("Pro'ya Yukselt", use_container_width=True, type="primary", key="price_pro"):
            st.session_state["show_landing"] = False
            st.rerun()

    # Uzman
    with pc3:
        st.markdown("""<div class="kz"><div class="kz-price">
            <div class="kz-price-name">Uzman</div>
            <div class="kz-price-desc">Tam guclu CFO deneyimi</div>
            <div><span class="kz-price-amount">&#8378;799</span> <span class="kz-price-period">/ ay</span></div>
            <hr class="kz-price-divider">
            <ul>
                <li>Tum Pro ozellikleri</li>
                <li>Prophet gelir tahmini</li>
                <li>PDF yatirimci raporlari</li>
                <li>Gelismis analiz modulleri</li>
                <li>Maks 50.000 satir veri</li>
                <li>500 AI mesaj / ay</li>
                <li>CFO Agent erisimi</li>
                <li>Oncelikli destek</li>
            </ul>
        </div></div>""", unsafe_allow_html=True)
        if st.button("Uzman'a Yukselt", use_container_width=True, key="price_uzman"):
            st.session_state["show_landing"] = False
            st.rerun()

    # ═══════════════════════════════════════════════════════════════════════
    # 6. ALT CTA
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown("""
    <div class="kz"><div class="kz-cta-band">
      <h2>Sirketinizin dijital CFO'su bugun baslasin</h2>
      <p>Kredi karti gerekmez &middot; 30 saniyede ilk sonuc &middot; Istediginiz zaman iptal edin</p>
    </div></div>
    """, unsafe_allow_html=True)

    _, bc, _ = st.columns([1.2, 1.6, 1.2])
    with bc:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("Ucretsiz Basla  \u2192", use_container_width=True,
                     type="primary", key="enter_bottom"):
            st.session_state["show_landing"] = False
            st.rerun()

if "show_landing" not in st.session_state:
    st.session_state["show_landing"] = (st.query_params.get("app") != "1")

# HTML icindeki butonlar ?app=1 ekleyince de calissin
if st.query_params.get("app") == "1":
    st.session_state["show_landing"] = False

if st.session_state.get("show_landing", True):
    show_landing_page()
    st.stop()

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

# ── Yardımcı: Plotly layout şablonu ──────────────────────────────────────────
_AXIS = dict(gridcolor="#F0F2F5", showgrid=True, zeroline=False,
             tickfont=dict(size=10, color="#8B93A8"))
_PLOT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#F9FAFB",
    font=dict(color="#8B93A8", family="-apple-system,Segoe UI,Arial,sans-serif", size=11),
    xaxis=_AXIS,
    yaxis=_AXIS,
    margin=dict(l=8, r=8, t=8, b=8),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#E2E5EB",
                borderwidth=1, font=dict(size=11)),
    hoverlabel=dict(bgcolor="#fff", bordercolor="#E2E5EB",
                    font=dict(size=11, color="#0F1729")),
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
            _track("page_view", page=key)
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

    # Admin bölümü — sadece admin listesindeki kullanıcılara görünür
    if ADMIN_OK and is_admin():
        nav_group("Admin")
        nav_item("Admin Dashboard", "admin", "🛠")

    # AI kullanım göstergesi (guardrail + cache aktifse)
    if st.session_state.get("ai_active") and "llm_guardrail" in st.session_state:
        _g = st.session_state.llm_guardrail
        _u = _g.get_usage(_current_user_id())
        _cache_stats = (st.session_state.llm_cache.stats()
                        if "llm_cache" in st.session_state else None)
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        with st.expander("🤖 AI Kullanım"):
            st.markdown(
                f"<div style='font-size:11px;color:#3D4663;line-height:1.7'>"
                f"<b>Çağrı:</b> {_u.get('calls', 0)}<br>"
                f"<b>Prompt token (yaklaşık):</b> {_u.get('prompt', 0):,}<br>"
                f"<b>Cevap token (yaklaşık):</b> {_u.get('response', 0):,}"
                + (f"<br><b>Cache hit oranı:</b> %{_cache_stats['hit_rate_pct']:.1f} "
                   f"({_cache_stats['hits']}/{_cache_stats['total']})"
                   if _cache_stats and _cache_stats['total'] > 0 else "")
                + "</div>",
                unsafe_allow_html=True,
            )

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

# Admin sayfa — sadece admin listesindekiler; erken çık, alt sayfaları render etme
if _sayfa == "admin":
    if ADMIN_OK and is_admin():
        show_admin_tab(_get_usage_tracker())
    else:
        st.warning("🔒 Bu sayfa yalnızca admin kullanıcılar içindir.")
    st.stop()

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

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if _sayfa == "genel":
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
            fig.update_layout(**_PLOT, barmode="group", height=290)
            st.plotly_chart(fig, use_container_width=True)

    with col_side:
        render_section("Finansal Sağlık")
        _bars = {
            "Karlılık":       alt.get("karlilik", 0),
            "Büyüme":         alt.get("buyume", 0),
            "Gider Kontrolü": alt.get("gider_kontrolu", 0),
            "Nakit":          alt.get("nakit", 0),
        }
        if "konsantrasyon" in alt:
            _bars["Konsantrasyon"] = alt["konsantrasyon"]
        render_health_bars(_bars)

        # ── Metodoloji + Uyarılar (yeni) ────────────────────────────────────
        _uyarilar   = s.get("uyarilar", [])
        _metodoloji = s.get("metodoloji", {})
        if _uyarilar or _metodoloji:
            with st.expander("ℹ️ Skor nasıl hesaplandı?", expanded=False):
                if _metodoloji:
                    _labels = {
                        "karlilik_agirlik":      "Karlılık",
                        "buyume_agirlik":        "Büyüme",
                        "gider_kontrolu_agirlik": "Gider Kontrolü",
                        "nakit_agirlik":         "Nakit",
                        "konsantrasyon_agirlik": "Konsantrasyon Riski",
                        # Eski key adı için geri uyumluluk
                        "gider_agirlik":         "Gider Kontrolü",
                    }
                    _boyut_sayisi = _metodoloji.get("boyut_sayisi")
                    _rows = "".join(
                        f"• {_labels[k]}: <b>%{int(v*100)}</b><br>"
                        for k, v in _metodoloji.items()
                        if k in _labels
                    )
                    _bilgi = (
                        f"<b>Boyut sayısı:</b> {_boyut_sayisi}<br>"
                        if _boyut_sayisi else ""
                    )
                    st.markdown(
                        f"""
                        <div style='font-size:12.5px;color:#3D4663;line-height:1.7'>
                        <b>Ağırlıklı formül:</b> Σ (alt_skor × ağırlık)<br>
                        {_bilgi}{_rows}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                for u in _uyarilar:
                    st.markdown(
                        f"<div style='background:#FFFBEB;border-left:3px solid #D97706;"
                        f"padding:8px 12px;border-radius:6px;font-size:12px;color:#78350F;"
                        f"margin-bottom:6px'>⚠️ {u}</div>",
                        unsafe_allow_html=True,
                    )

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
if _sayfa == "risk":
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
        _bars2 = {
            "Karlilik":       alt.get("karlilik", 0),
            "Buyume":         alt.get("buyume", 0),
            "Gider Kontrolu": alt.get("gider_kontrolu", 0),
            "Nakit":          alt.get("nakit", 0),
        }
        if "konsantrasyon" in alt:
            _bars2["Konsantrasyon"] = alt["konsantrasyon"]
        render_health_bars(_bars2)

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

if _sayfa == "gelir":
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
            fig.update_layout(**_PLOT, height=220, showlegend=False)
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
            fig2.update_layout(**_PLOT, height=160, showlegend=False,
                               yaxis=dict(**_AXIS, ticksuffix="%"))
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
            fig3.update_layout(height=200, paper_bgcolor="rgba(0,0,0,0)",
                               margin=dict(l=8, r=8, t=8, b=8), showlegend=False)
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

if _sayfa == "gider":
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
            fig.update_layout(**_PLOT, height=240, showlegend=False,
                             yaxis=dict(gridcolor="rgba(0,0,0,0)", zeroline=False,
                                        tickfont=dict(size=11, color="#3D4663")))
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

if _sayfa == "kar":
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
            fig.update_layout(**_PLOT, barmode="relative", height=300,
                             yaxis=dict(**_AXIS, zeroline=True,
                                        zerolinecolor="#E2E5EB", zerolinewidth=1),
                             yaxis2=dict(overlaying="y", side="right",
                                         tickformat=".0f", ticksuffix="%",
                                         tickfont=dict(size=10, color="#D97706"),
                                         showgrid=False))
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

if _sayfa == "tahmin":
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

                # Reel tahmin toggle (P1.2 enflasyon deflatörü)
                reel_aktif = st.checkbox(
                    "🇹🇷 Reel tahmin (enflasyondan arındır)",
                    value=st.session_state.get("fc_reel_aktif", False),
                    key="fc_reel_aktif",
                    help="İşaretlerseniz nominal ₺ tahminine ek olarak bugünkü "
                         "satın alma gücüne göre reel sütunlar hesaplanır.",
                )
                infl = None
                if reel_aktif:
                    infl_pct = st.slider(
                        "Yıllık enflasyon varsayımı (%)",
                        min_value=5, max_value=100, value=35, step=1,
                        key="fc_infl_pct",
                        help="TÜİK/TCMB projeksiyonu veya kendi tahmininizi girin.",
                    )
                    infl = infl_pct / 100

                if st.button("Tahmin Uret", use_container_width=True, key="btn_fc"):
                    with st.spinner("Model egitiliyor..."):
                        try:
                            sonuc = ForecastEngine(df).summary_report(
                                ay=ay, enflasyon_yillik=infl,
                            )
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

                    # ── Veri kalitesi uyarıları (yeni) ──
                    _veri_uy = sonuc.get("veri_uyarilari", [])
                    _guven_notu = sonuc.get("guven_notu", "")
                    _metod_notu = sonuc.get("metodoloji_notu", "")
                    if _veri_uy or _guven_notu:
                        for u in _veri_uy:
                            # İçerikten renk seç
                            is_warn = u.startswith("⚠️") or "düşük" in u.lower() or "yakalanamaz" in u.lower()
                            bg = "#FEF2F2" if is_warn else "#EEF2FF"
                            bd = "#FCA5A5" if is_warn else "#C7D2FE"
                            fg = "#991B1B" if is_warn else "#1E3A8A"
                            st.markdown(
                                f'<div style="background:{bg};border:0.5px solid {bd};'
                                f'border-radius:8px;padding:10px 14px;margin-bottom:6px;'
                                f'font-size:12px;color:{fg};line-height:1.55;">{u}</div>',
                                unsafe_allow_html=True,
                            )
                        if _guven_notu:
                            st.markdown(
                                f'<div style="background:#F9FAFB;border:0.5px solid #E2E5EB;'
                                f'border-radius:8px;padding:8px 14px;margin-bottom:10px;'
                                f'font-size:11.5px;color:#6B7280;line-height:1.5;">'
                                f'ℹ️ <b>Güven notu:</b> {_guven_notu}'
                                f'{"<br>" + _metod_notu if _metod_notu else ""}</div>',
                                unsafe_allow_html=True,
                            )

                    # Güven aralığı KPI'da backend'e göre değişir
                    _backend = sonuc.get("backend", "prophet")
                    _ci_label = "%90" if _backend == "prophet" else "±%15" if _backend == "statsmodels" else "±%20"
                    _ci_delta = "Prophet CI" if _backend == "prophet" else "Holt-Winters" if _backend == "statsmodels" else "Lineer trend"

                    _kpi_row = [
                        {"label": "Toplam Tahmin (Nominal)", "value": fmt(sonuc["toplam_tahmin"]),
                         "delta": f'{sonuc["ay_sayisi"]} aylik', "positive": True},
                        {"label": "Aylik Ortalama",    "value": fmt(sonuc["ortalama_tahmin"]),
                         "delta": "Tahmin", "positive": True, "accent_color": "#2563EB"},
                        {"label": "Buyume Beklentisi", "value": f'%{sonuc["buyume_beklentisi"]}',
                         "delta": "Projeksiyon (nominal)", "positive": sonuc["buyume_beklentisi"] >= 0},
                        {"label": "Guven Araligi",     "value": _ci_label,
                         "delta": _ci_delta, "positive": True, "accent_color": "#7C3AED"},
                    ]
                    # Reel toplam varsa ek KPI
                    if "toplam_tahmin_reel" in sonuc:
                        _infl_pct = sonuc.get("enflasyon_uygulandi", 0) * 100
                        _kpi_row.insert(1, {
                            "label": "Toplam Tahmin (Reel)",
                            "value": fmt(sonuc["toplam_tahmin_reel"]),
                            "delta": f'Enflasyon %{_infl_pct:.1f}',
                            "positive": True, "accent_color": "#059669",
                        })
                    render_kpi_row(_kpi_row, height=118)

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
                    fig.update_layout(**_PLOT, height=300)
                    st.plotly_chart(fig, use_container_width=True)
                    render_section("Tahmin Tablosu")
                    _fmt_map = {
                        "Tahmin":              "{:,.0f} ₺",
                        "Alt Sınır":           "{:,.0f} ₺",
                        "Üst Sınır":           "{:,.0f} ₺",
                        "Tahmin (Reel ₺)":     "{:,.0f} ₺",
                        "Alt Sınır (Reel ₺)":  "{:,.0f} ₺",
                        "Üst Sınır (Reel ₺)":  "{:,.0f} ₺",
                    }
                    _active = {k: v for k, v in _fmt_map.items() if k in t_df.columns}
                    st.dataframe(t_df.style.format(_active),
                                 use_container_width=True, hide_index=True)
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
        fig_sen.update_layout(**_PLOT, barmode="group", height=280)
        st.plotly_chart(fig_sen, use_container_width=True)

if _sayfa == "yatirim":
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
if _sayfa == "nakit":
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
if _sayfa == "borc":
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
if _sayfa == "sektor":
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
if _sayfa == "profil":
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
if _sayfa == "musteri":
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
if _sayfa == "butce":
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
if _sayfa == "cfo":
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
if _sayfa == "ai":
    render_page_header("AI Finansal Analiz", "Groq · Gemini · Otomatik yorum")
    if not gate("ai_yorum", "AI Yorumları"):
        st.stop()
    if not GEMINI_OK:
        st.error("`groq` veya `google-generativeai` kurulu değil.")
        st.stop()

    # ── AI Otomatik Aktivasyon (Secrets'ta key varsa) ─────────────────────
    # Streamlit Secrets'a GROQ_API_KEY veya GEMINI_API_KEY eklenmişse
    # kullanıcı butona basmadan AI otomatik başlar.
    if not st.session_state.ai_active:
        _auto_key = GROQ_API_KEY_ENV or GEMINI_API_KEY_ENV
        _auto_provider = "groq" if GROQ_API_KEY_ENV else ("gemini" if GEMINI_API_KEY_ENV else None)
        if _auto_key and _auto_provider:
            try:
                st.session_state.gemini    = init_ai_engine(_auto_key, _auto_provider)
                st.session_state.ai_active = True
            except Exception as ex:
                st.warning(f"AI otomatik başlatılamadı: {ex}")

    # AI aktivasyon (kullanıcı manuel)
    if not st.session_state.ai_active:
        st.markdown("#### AI Motorunu Aktive Et")
        st.info(
            "ℹ️ Kalıcı otomatik aktivasyon için: "
            "Streamlit → Manage app → Settings → Secrets → "
            "`GROQ_API_KEY = \"gsk_...\"` ekleyin.",
        )
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
                st.session_state.gemini    = init_ai_engine(api_key, chosen)
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
if _sayfa == "sohbet":
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
if _sayfa == "pdf":
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

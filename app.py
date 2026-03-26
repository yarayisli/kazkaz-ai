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
from design_system import *
from ui_components import (
    render_topbar, render_page_header, render_exec_summary,
    render_kpi_row, render_section, render_alerts,
    render_health_bars, render_stat_strip, render_insight_card,
    render_divider, badge_html, fmt as ufmt, T,
)
from html_components import (
    render_page_header, render_exec_summary, render_kpi_row,
    render_alert, render_section, render_health_bars,
    badge_html, SIDEBAR_LOGO_HTML, NAV_GROUP_HTML,
)

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

# Streamlit'e açık temayı zorla
import streamlit.components.v1 as _components
_FORCE_LIGHT = """
<script>
(function() {
  var root = window.parent.document.querySelector(':root');
  if (root) {
    root.setAttribute('data-theme', 'light');
    root.style.colorScheme = 'light';
  }
  var app = window.parent.document.querySelector('.stApp');
  if (app) app.style.backgroundColor = '#F1F5F9';
})();
</script>
"""
_components.html(_FORCE_LIGHT, height=0, scrolling=False)

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

inject_css()

# Streamlit'in beyaz tema ile çakışmasını önle
st.markdown("""
<style>
.stApp { background-color: #F7F8FA !important; }
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 0.5px solid #E2E5EB !important;
}
[data-testid="stSidebar"] * { color: #4B5563 !important; }
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
    box-shadow: 0 0 0 0.5px #E2E5EB !important;
}
.stButton > button {
    background: #1B3A6B !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 8px 18px !important;
}
.stButton > button:hover { background: #2B4F8C !important; }
.stDownloadButton > button {
    background: #F3F4F6 !important;
    color: #4B5563 !important;
    border: 0.5px solid #E2E5EB !important;
    border-radius: 8px !important;
}
[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: 0.5px solid #E2E5EB !important;
    border-radius: 8px !important;
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
    letter-spacing: -.03em !important;
    color: #1A1A2E !important;
}
.dataframe { font-size: 12px !important; }
.dataframe th {
    background: #F3F4F6 !important;
    color: #9CA3AF !important;
    font-size: 9px !important;
    font-weight: 600 !important;
    letter-spacing: .08em !important;
    text-transform: uppercase !important;
    border-bottom: 0.5px solid #E2E5EB !important;
}
.dataframe td { border-bottom: 0.5px solid #F3F4F6 !important; }
hr { border-color: #E2E5EB !important; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: #D1D5DB; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

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

PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94A3B8", family="Inter, -apple-system, sans-serif", size=11),
    xaxis=dict(gridcolor="#E2E8F0", showgrid=True, zeroline=False,
               tickfont=dict(size=10, color="#94A3B8"), linecolor="#E2E8F0"),
    yaxis=dict(gridcolor="#E2E8F0", showgrid=True, zeroline=False,
               tickfont=dict(size=10, color="#94A3B8"), linecolor="#E2E8F0"),
    margin=dict(l=8, r=8, t=36, b=8),
    legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor="#E2E8F0",
                borderwidth=1, font=dict(size=11, color="#475569")),
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#E2E8F0",
                    font=dict(size=11, color="#0F172A")),
)

C_BLUE   = "#1D4ED8"
C_BLUE2  = "#3B82F6"
C_GREEN  = "#059669"
C_RED    = "#DC2626"
C_AMBER  = "#D97706"
C_SLATE  = "#374151"
C_CYAN   = "#0EA5E9"
C_PURPLE = "#4F46E5"
C_YELLOW = "#D97706"
CHART_COLORS = ["#1D4ED8", "#0F766E", "#374151", "#6B7280"]

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

def kpi(label, value, delta="", color="#0F172A", positive=True):
    try:
        _p = bool(positive)
    except Exception:
        _p = True
    accent_color = "#059669" if _p else "#DC2626"
    delta_bg     = "#F0FDF4" if _p else "#FFF7F7"
    delta_color  = "#059669" if _p else "#DC2626"
    sign         = "+" if _p else "−"
    dh = (
        f'<div style="display:inline-flex;align-items:center;gap:3px;'
        f'font-size:11px;font-weight:500;padding:2px 6px;border-radius:3px;'
        f'margin-top:6px;background:{delta_bg};color:{delta_color};">'
        f'{sign} {delta}</div>'
    ) if delta else ""
    st.markdown(
        f'<div style="'
        f'background:#FFFFFF;'
        f'border:1px solid #E2E8F0;'
        f'border-radius:10px;'
        f'padding:18px 20px 16px 22px;'
        f'position:relative;overflow:hidden;'
        f'margin-bottom:8px;'
        f'box-shadow:0 1px 3px rgba(15,23,42,.06),0 2px 8px rgba(15,23,42,.04);'
        f'transition:border-color 0.15s;">'
        f'<div style="'
        f'position:absolute;left:0;top:0;bottom:0;width:3px;'
        f'border-radius:4px 0 0 4px;'
        f'background:{accent_color};"></div>'
        f'<div style="'
        f'font-size:10px;font-weight:600;letter-spacing:0.1em;'
        f'text-transform:uppercase;color:#94A3B8;'
        f'margin-bottom:8px;">{label}</div>'
        f'<div style="'
        f'font-family:Inter,-apple-system,sans-serif;'
        f'font-size:24px;font-weight:600;'
        f'letter-spacing:-0.025em;line-height:1.1;'
        f'color:{color};">{value}</div>'
        f'{dh}</div>',
        unsafe_allow_html=True
    )

def sec(text, small=False):
    fs = "0.78rem" if small else "0.8rem"
    st.markdown(
        f'<div style="'
        f'font-size:{fs};font-weight:600;'
        f'letter-spacing:0.08em;text-transform:uppercase;'
        f'color:#94A3B8;'
        f'padding:0 0 10px;'
        f'border-bottom:1px solid #E2E8F0;'
        f'margin:28px 0 16px;">{text}</div>',
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:

    st.markdown(SIDEBAR_LOGO_HTML, unsafe_allow_html=True)

    if FIREBASE_OK:
        show_user_badge()
        guard = SessionManager.get_guard()
        if guard and guard.plan != Plan.UZMAN:
            if st.button("⚡ Paketi Yükselt", use_container_width=True):
                st.session_state["page"] = "plans"
                st.rerun()

    # ══ Grup 1: Şirket & Veri ══
    st.markdown(
        f'<div style="font-size:9px;font-weight:600;letter-spacing:.12em;'
        f'text-transform:uppercase;color:#3D5275;padding:16px 4px 8px;">'
        f'ŞİRKET &amp; VERİ</div>',
        unsafe_allow_html=True
    )
    st.session_state["sirket_adi"] = st.text_input(
        "Şirket Adı",
        value=st.session_state["sirket_adi"],
        placeholder="Örn: Acme A.Ş."
    )
    kaynak = st.radio("Veri kaynağı:", ["CSV / Excel", "Google Sheets"], horizontal=True)

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



    # ══ Grup 2: Yapay Zeka ══
    st.markdown(
        f'<div style="font-size:9px;font-weight:600;letter-spacing:.12em;'
        f'text-transform:uppercase;color:#3D5275;'
        f'padding:16px 4px 8px;border-top:1px solid #1A2E4A;">YAPAY ZEKA</div>',
        unsafe_allow_html=True
    )
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
                st.markdown('<div style="display:inline-flex;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;background:rgba(59,130,246,0.10);color:#3B82F6;border:1px solid rgba(59,130,246,0.25);">GROQ — LLAMA 3.3</div>',
                            unsafe_allow_html=True)
                api_key = GROQ_API_KEY_ENV or st.text_input(
                    "Groq API Key", type="password",
                    help="console.groq.com → API Keys → Create"
                )
                chosen_provider = "groq"
            else:
                st.markdown('<div style="display:inline-flex;padding:2px 8px;border-radius:4px;font-size:9px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;background:rgba(59,130,246,0.10);color:#3B82F6;border:1px solid rgba(59,130,246,0.25);">GEMINI 2.0 FLASH</div>',
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



    # ══ Grup 3: Raporlama ══
    st.markdown(
        f'<div style="font-size:9px;font-weight:600;letter-spacing:.12em;'
        f'text-transform:uppercase;color:#3D5275;'
        f'padding:16px 4px 8px;border-top:1px solid #1A2E4A;">RAPORLAMA</div>',
        unsafe_allow_html=True
    )
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
            <div style="background:#0D1424;border:1px solid #1A2E4A;border-radius:14px;padding:18px 20px 16px 22px;position:relative;overflow:hidden;margin-bottom:8px;" style="text-align:center;padding:24px 12px;">
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
    g  = rapor["gelir"]
    e  = rapor["gider"]
    k  = rapor["karlilik"]
    s  = rapor["saglik_skoru"]

    _buyume  = float(g.get("ortalama_buyume_orani", 0) or 0)
    _kar     = float(k.get("toplam_net_kar", 0) or 0)
    _skor    = int(s.get("skor", 0) or 0)
    _skat    = s.get("kategori", "")
    _marj    = float(k.get("kar_marji", 0) or 0)
    _gider_o = round(e["toplam_gider"]/g["toplam_gelir"]*100,1) if g.get("toplam_gelir") else 0
    _sirket  = st.session_state.get("sirket_adi", "Şirket")
    _s_level = "success" if _skor >= 65 else "warning" if _skor >= 40 else "danger"

    # ── Topbar ──
    render_topbar(
        sirket_adi    = _sirket,
        donem         = f'{g.get("donem_baslangic","—")} – {g.get("donem_bitis","—")}',
        saglik_badge  = f'{_skat} · {_skor}/100',
    )

    # ── Page Header ──
    render_page_header(
        title    = f"{_sirket} — Finansal Genel Bakış",
        subtitle = f'{g.get("ay_sayisi",0)} aylık dönem · {g.get("donem_baslangic","—")} – {g.get("donem_bitis","—")}',
        badge_text  = _skat,
        badge_level = _s_level,
    )

    # ── İlke 5: Exec Summary ──
    _by = "güçlü büyüme" if _buyume >= 10 else "ılımlı büyüme" if _buyume >= 0 else "gerileme"
    _mj = "sağlıklı" if _marj >= 20 else "baskı altında" if _marj >= 10 else "kritik"
    render_exec_summary(
        f"{_sirket} {g.get('ay_sayisi',0)} aylık dönemde <strong>{_by}</strong> kaydetti. "
        f"Toplam gelir <strong>{fmt(g['toplam_gelir'])}</strong>; "
        f"net kar marjı <strong>%{_marj}</strong> — {_mj}. "
        f"Gider/gelir oranı %{_gider_o}. "
        f"Finansal sağlık: <strong>{_skor}/100 ({_skat})</strong>."
    )

    # ── KPI Satırı 1 ──
    render_kpi_row([
        {"label":"Toplam Gelir",  "value":fmt(g["toplam_gelir"]),
         "delta":f'Ort. {fmt(g["ortalama_aylik_gelir"])}/ay', "positive":True},
        {"label":"Net Kar",       "value":fmt(_kar),
         "delta":f'Marj %{_marj}', "positive":_kar>=0},
        {"label":"Büyüme Oranı", "value":f'%{_buyume}',
         "delta":"Aylık ortalama", "positive":_buyume>=0},
        {"label":"Sağlık Skoru", "value":f'{_skor}/100',
         "delta":_skat, "positive":_skor>=60,
         "accent_color": "#059669" if _skor>=65 else "#D97706" if _skor>=40 else "#DC2626",
         "color": "#059669" if _skor>=65 else "#D97706" if _skor>=40 else "#DC2626"},
    ], height=105)

    # ── KPI Satırı 2 ──
    render_kpi_row([
        {"label":"Toplam Gider",  "value":fmt(e["toplam_gider"]),
         "delta":f'Sabit %{e["sabit_gider_orani"]}',
         "positive":e["sabit_gider_orani"]<60,
         "accent_color":"#D97706"},
        {"label":"Kar Marjı",     "value":f'%{_marj}',
         "delta":"Hedef >%15", "positive":_marj>=15},
        {"label":"Gider / Gelir", "value":f'%{_gider_o}',
         "delta":"Hedef <%80", "positive":_gider_o<80},
        {"label":"Dönem",         "value":f'{g.get("ay_sayisi",0)} Ay',
         "delta":f'{g.get("donem_baslangic","—")} – {g.get("donem_bitis","—")}',
         "positive":True, "accent_color":"#1B3A6B"},
    ], height=105)

    # ── Ana Grafik + Sağlık ──
    col_main, col_side = st.columns([2, 1], gap="medium")

    with col_main:
        render_section("Aylık Finansal Performans")
        mp = engine.profit.monthly_profit()
        if not mp.empty:
            fig = go.Figure()
            fig.add_bar(x=mp["Dönem"], y=mp["Gelir"],
                        name="Gelir", marker_color="#1B3A6B", opacity=0.85)
            fig.add_bar(x=mp["Dönem"], y=mp["Gider"],
                        name="Gider", marker_color="#E5E7EB", opacity=0.9)
            fig.add_scatter(
                x=mp["Dönem"], y=mp["NetKar"], name="Net Kar",
                mode="lines+markers",
                line=dict(color="#059669", width=2.5),
                marker=dict(size=6, color="#059669",
                            line=dict(color="#fff", width=1.5)),
            )
            fig.update_layout(**chart_layout(
                height=280,
                barmode="group",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#FAFBFC",
                font=dict(color="#9CA3AF", family="-apple-system,Arial,sans-serif", size=11),
                xaxis=dict(gridcolor="#F3F4F6", showgrid=True, zeroline=False,
                           tickfont=dict(size=10, color="#9CA3AF"), linecolor="#E2E5EB"),
                yaxis=dict(gridcolor="#F3F4F6", showgrid=True, zeroline=False,
                           tickfont=dict(size=10, color="#9CA3AF"), linecolor="#E2E5EB"),
                legend=dict(orientation="h", y=1.06, x=0,
                            bgcolor="rgba(0,0,0,0)",
                            font=dict(size=11, color="#4B5563")),
            ))
            st.plotly_chart(fig, use_container_width=True)

    with col_side:
        render_section("Finansal Sağlık Alt Skorları")
        alt = s.get("alt_skorlar", {})
        render_health_bars({
            "Karlılık":       alt.get("karlilik", 0),
            "Büyüme":         alt.get("buyume", 0),
            "Gider Kontrolü": alt.get("gider_kontrolu", 0),
            "Nakit":          alt.get("nakit", 0),
        })

        # Sistem değerlendirmesi
        render_alerts([{
            "title": "Sistem Değerlendirmesi",
            "body":  s.get("aciklama", ""),
            "level": _s_level if _s_level != "brand" else "info",
        }])

    # ── Risk & Fırsat Alertleri ──
    render_section("Önemli Tespitler & Aksiyonlar", top_margin=8)

    _alerts = []
    if _gider_o > 80:
        _alerts.append({"title":"Gider oranı kritik seviyede",
            "body":f"Gider/gelir oranı %{_gider_o} — hedef %80'in üzerinde. Acil inceleme önerilir.",
            "level":"danger"})
    elif _gider_o > 70:
        _alerts.append({"title":"Gider oranı yükseliyor",
            "body":f"Gider/gelir oranı %{_gider_o}. Personel ve sabit gider kalemleri gözden geçirilmeli.",
            "level":"warning"})
    if _buyume >= 10:
        _alerts.append({"title":"Güçlü büyüme momentumu",
            "body":f"Aylık ortalama %{_buyume} büyüme. Kapasite planlaması gündeme alınabilir.",
            "level":"success"})
    if _skor >= 65:
        _alerts.append({"title":"Finansal sağlık iyi seviyede",
            "body":f"Skor {_skor}/100 — tüm ana göstergeler pozitif bölgede.",
            "level":"success"})
    elif _skor < 40:
        _alerts.append({"title":"Finansal sağlık kritik",
            "body":f"Skor {_skor}/100 — acil aksiyonlar gerekiyor.",
            "level":"danger"})

    if not _alerts:
        _alerts.append({"title":"Sistem normal seyrediyor",
            "body":"Kritik uyarı bulunmuyor.", "level":"info"})

    render_alerts(_alerts)

# ══ GELİR ══
with tab_gelir:
    g = rapor["gelir"]
    _bv = float(g.get("ortalama_buyume_orani", 0) or 0)

    # Page header
    page_header("Gelir Analizi", f'{g.get("ay_sayisi",0)} aylık dönem')

    # KPI
    c1, c2, c3 = st.columns(3)
    with c1: kpi("Toplam Gelir",   fmt(g["toplam_gelir"]))
    with c2: kpi("Aylık Ortalama", fmt(g["ortalama_aylik_gelir"]))
    with c3: kpi("Ort. Büyüme",    f'%{_bv}', positive=bool(_bv >= 0))

    # Grafikler
    col1, col2 = st.columns(2)
    with col1:
        sec("Aylık Gelir Trendi")
        mr = engine.revenue.monthly_revenue()
        fig = go.Figure(go.Bar(
            x=mr["Dönem"], y=mr["Toplam Gelir"],
            marker_color=DS.C1, opacity=0.9,
            hovertemplate="%{x}<br>%{y:,.0f} ₺<extra></extra>",
        ))
        fig.update_layout(**chart_layout(
            height=260,
            xaxis=dict(gridcolor=DS.BORDER, showgrid=False, zeroline=False,
                       tickfont=dict(size=10, color=DS.TEXT_TER)),
            yaxis=dict(gridcolor=DS.BORDER, showgrid=True, zeroline=False,
                       tickfont=dict(size=10, color=DS.TEXT_TER)),
        ))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        sec("Kategori Dağılımı")
        cr = engine.revenue.revenue_by_category()
        cr = cr[cr["Toplam Gelir"] > 0]
        if not cr.empty:
            fig = go.Figure(go.Pie(
                values=cr["Toplam Gelir"], labels=cr["Kategori"],
                hole=0.55,
                marker=dict(colors=[DS.C1, DS.C2, DS.C3, DS.C4,
                                    "#6366F1","#0891B2","#059669"]),
                textfont=dict(size=11),
            ))
            fig.update_layout(**chart_layout(height=260, legend=dict(
                font=dict(size=11, color=DS.TEXT_SEC), bgcolor="rgba(0,0,0,0)")))
            st.plotly_chart(fig, use_container_width=True)

    sec("Büyüme Oranı Trendi")
    gr = engine.revenue.revenue_growth_rate().dropna()
    if not gr.empty:
        renkler = [DS.GREEN if v >= 0 else DS.RED for v in gr["Büyüme Oranı (%)"]]
        fig = go.Figure()
        fig.add_scatter(
            x=gr["Dönem"], y=gr["Büyüme Oranı (%)"],
            fill="tozeroy", mode="lines+markers",
            line=dict(color=DS.C1, width=2.5),
            fillcolor=f"rgba(37,99,235,0.08)",
            marker=dict(size=6, color=renkler,
                        line=dict(color=DS.BG_BASE, width=1.5)),
        )
        fig.add_hline(y=0, line_dash="dash", line_color=DS.RED, opacity=0.4)
        fig.update_layout(**chart_layout(
            height=220,
            xaxis=dict(gridcolor=DS.BORDER, showgrid=True, zeroline=False,
                       tickfont=dict(size=10, color=DS.TEXT_TER)),
            yaxis=dict(gridcolor=DS.BORDER, showgrid=True, zeroline=False,
                       tickfont=dict(size=10, color=DS.TEXT_TER),
                       ticksuffix="%"),
        ))
        st.plotly_chart(fig, use_container_width=True)

# ══ GİDER ══
with tab_gider:
    e = rapor["gider"]
    page_header("Gider Analizi",
        f'{e.get("ay_sayisi", g.get("ay_sayisi",0))} aylık dönem')
    _sv = float(e.get("sabit_gider_orani", 0) or 0)
    render_exec_summary(
        f"Toplam gider <strong>{fmt(e['toplam_gider'])}</strong>. "
        f"Sabit gider oranı <strong>%{_sv}</strong> — "
        f"{'kontrol altında' if _sv < 60 else 'yüksek, optimizasyon önerilir'}. "
        f"Değişken gider oranı %{round(100-_sv,1)}."
    )
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
                              font=dict(color="#8899bb", family="Inter"),
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
        fig.update_layout(title="Sabit / Değişken", height=280, **{k:v for k,v in PLOTLY_THEME.items() if k not in ("title")})
        st.plotly_chart(fig, use_container_width=True)

# ══ KARLILIK ══
with tab_kar:
    k = rapor["karlilik"]
    page_header("Karlılık Analizi",
        f'Net kar marjı %{k.get("kar_marji",0)}')
    _km = float(k.get("kar_marji", 0) or 0)
    render_exec_summary(
        f"Net kar <strong>{fmt(k['toplam_net_kar'])}</strong>, "
        f"marj <strong>%{_km}</strong> — "
        f"{'güçlü' if _km >= 20 else 'orta' if _km >= 10 else 'düşük, iyileştirme gerekli'}. "
        f"Brüt kar marjı %{k.get('brut_kar_marji', 0)}."
    )
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
        fig.update_layout(**chart_layout(
            height=300,
            title="Aylık Net Kar & Kar Marjı",
            yaxis2=dict(overlaying="y", side="right", gridcolor=DS.BORDER,
                        tickformat=".0f", ticksuffix="%"),
        ))
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
                with c2: kpi("Aylık Ort.", fmt(sonuc["ortalama_tahmin"]))
                with c3: kpi("Büyüme Bkl.", f'%{sonuc["buyume_beklentisi"]}', positive=bool(sonuc["buyume_beklentisi"] >= 0))
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
            fig.update_layout(**chart_layout(
                height=330,
                title="Gelir Tahmini",
                legend=dict(orientation="h", y=1.1, x=0, bgcolor="rgba(0,0,0,0)"),
            ))
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
                      height=300, **{k:v for k,v in PLOTLY_THEME.items() if k not in ("barmode", "title")})
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

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

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #0a0e1a; color: #e8eaf0; }
[data-testid="stSidebar"] { background: #0f1629 !important; border-right: 1px solid #1e2d4a; }
.kazkaz-logo {
    font-family: 'Syne', sans-serif; font-size: 1.9rem; font-weight: 800;
    background: linear-gradient(135deg, #00d4ff, #0066ff, #7c3aed);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.kpi-card {
    background: linear-gradient(135deg, #111827, #1a2540);
    border: 1px solid #1e3a5f; border-radius: 14px;
    padding: 18px 20px; position: relative; overflow: hidden; margin-bottom: 10px;
}
.kpi-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #00d4ff, #0066ff);
}
.kpi-label { font-size: 0.68rem; color: #4a6fa5; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 5px; }
.kpi-value { font-family: 'Syne', sans-serif; font-size: 1.6rem; font-weight: 700; color: #e8eaf0; }
.kpi-delta { font-size: 0.76rem; margin-top: 3px; }
.kpi-delta.pos { color: #10d994; } .kpi-delta.neg { color: #ff4757; }
.section-title {
    font-family: 'Syne', sans-serif; font-size: 1rem; font-weight: 700;
    color: #e8eaf0; padding: 5px 0 10px; border-bottom: 1px solid #1e2d4a; margin: 14px 0 12px;
}
.ai-badge {
    display: inline-block; background: linear-gradient(135deg, #0066ff22, #7c3aed22);
    border: 1px solid #0066ff44; color: #60a5fa; font-size: 0.68rem;
    letter-spacing: 1.5px; text-transform: uppercase; padding: 2px 8px; border-radius: 20px;
}
.chat-user {
    background: #1a2d50; border-radius: 12px 12px 4px 12px;
    padding: 10px 14px; margin: 8px 0 8px 40px; font-size: 0.88rem; color: #c8d8f0;
}
.chat-ai {
    background: #111827; border: 1px solid #1e3a5f; border-radius: 12px 12px 12px 4px;
    padding: 10px 14px; margin: 8px 40px 8px 0; font-size: 0.88rem; color: #a8c0e0;
}
.stButton > button {
    background: linear-gradient(135deg, #0066ff, #7c3aed) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 500 !important; transition: opacity 0.2s;
}
.stButton > button:hover { opacity: 0.85 !important; }
[data-testid="stFileUploader"] { background: #111827; border: 2px dashed #1e3a5f; border-radius: 12px; }
.stTabs [data-baseweb="tab-list"] { background: #0f1629; border-radius: 10px; }
.stTabs [data-baseweb="tab"] { color: #4a6fa5 !important; }
.stTabs [aria-selected="true"] { color: #60a5fa !important; }
hr { border-color: #1e2d4a; }
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
                    <div style="color:#4a6fa5;font-size:0.75rem;letter-spacing:2px;
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
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#8899bb", family="DM Sans"),
    xaxis=dict(gridcolor="#1e2d4a", showgrid=True, zeroline=False),
    yaxis=dict(gridcolor="#1e2d4a", showgrid=True, zeroline=False),
    margin=dict(l=10, r=10, t=32, b=10),
)

def fmt(v):
    if abs(v) >= 1_000_000: return f"{v/1_000_000:.1f}M ₺"
    if abs(v) >= 1_000:     return f"{v/1_000:.0f}K ₺"
    return f"{v:,.0f} ₺"

def score_color(k):
    return {"Mükemmel":"#10d994","İyi":"#60a5fa","Orta":"#fbbf24",
            "Zayıf":"#f97316","Kritik":"#ff4757"}.get(k, "#e8eaf0")

def kpi(label, value, delta="", positive=True):
    dc = "pos" if positive else "neg"
    di = "▲" if positive else "▼"
    dh = f'<div class="kpi-delta {dc}">{di} {delta}</div>' if delta else ""
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>{dh}</div>',
        unsafe_allow_html=True
    )

def sec(text):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown('<div class="kazkaz-logo">KazKaz AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="color:#4a6fa5;font-size:0.68rem;letter-spacing:2px;'
        'text-transform:uppercase;margin-bottom:10px;">Finansal Analiz Platformu</div>',
        unsafe_allow_html=True
    )

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
        st.caption("google-generativeai kurulu değil.")
    elif not can("ai_yorum"):
        st.caption("🔒 Pro veya Uzman paket gerekli.")
    else:
        st.markdown('<div class="ai-badge">Gemini Powered</div>', unsafe_allow_html=True)
        ai_toggle = st.toggle("AI Aktif Et", value=st.session_state.ai_active)
        if ai_toggle and not st.session_state.ai_active:
            api_key = GEMINI_API_KEY_ENV or st.text_input(
                "Gemini API Key", type="password",
                help="https://aistudio.google.com/app/apikey"
            )
            if api_key and st.button("🔓 Etkinleştir", use_container_width=True):
                try:
                    st.session_state.gemini    = GeminiEngine(api_key=api_key)
                    st.session_state.ai_active = True
                    st.success("🤖 AI aktif!")
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
        <div style="color:#4a6fa5;font-size:0.82rem;letter-spacing:3px;
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
                            font-size:0.88rem;color:#e8eaf0;margin-bottom:5px;">{title}</div>
                <div style="color:#4a6fa5;font-size:0.74rem;line-height:1.5;">{desc}</div>
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
 tab_ai, tab_sohbet) = st.tabs([
    "📊 Genel", "💰 Gelir", "📉 Gider", "📈 Karlılık",
    "🔮 Tahmin", "🎯 Senaryo", "💼 Yatırım",
    "💧 Nakit Akışı", "🏦 Borç Analizi",
    "🏭 Sektör", "🤖 AI Analiz", "💬 AI Sohbet",
])

# ══ GENEL ══
with tab_genel:
    g, e, k, s = rapor["gelir"], rapor["gider"], rapor["karlilik"], rapor["saglik_skoru"]
    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Toplam Gelir", fmt(g["toplam_gelir"]),
                 f'%{g["ortalama_buyume_orani"]} büyüme', g["ortalama_buyume_orani"] >= 0)
    with c2: kpi("Toplam Gider", fmt(e["toplam_gider"]),
                 f'Sabit: %{e["sabit_gider_orani"]}', e["sabit_gider_orani"] < 50)
    with c3: kpi("Net Kar",      fmt(k["toplam_net_kar"]),
                 f'Marj: %{k["kar_marji"]}', k["toplam_net_kar"] >= 0)
    with c4:
        renk = score_color(s["kategori"])
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-label">Sağlık Skoru</div>'
            f'<div class="kpi-value" style="color:{renk};">{s["skor"]}'
            f'<span style="font-size:0.95rem;color:#4a6fa5;"> /100</span></div>'
            f'<div style="color:{renk};font-size:0.8rem;margin-top:3px;">● {s["kategori"]}</div>'
            f'</div>', unsafe_allow_html=True
        )
    st.markdown("---")
    sec("🏥 Finansal Sağlık Detayı")
    alt = s["alt_skorlar"]
    for col, (key, lbl) in zip(st.columns(4), [
        ("karlilik","Karlılık"),("buyume","Büyüme"),
        ("gider_kontrolu","Gider Kontrolü"),("nakit","Nakit")
    ]):
        val  = alt[key]
        renk = "#10d994" if val >= 70 else "#fbbf24" if val >= 40 else "#ff4757"
        with col:
            fig = go.Figure(go.Indicator(
                mode="gauge+number", value=val,
                title={"text": lbl, "font": {"size": 12, "color": "#8899bb"}},
                number={"font": {"size": 20, "color": renk}},
                gauge={"axis": {"range": [0, 100]}, "bar": {"color": renk, "thickness": 0.25},
                       "bgcolor": "#111827", "bordercolor": "#1e2d4a",
                       "steps": [{"range": [0,40],"color":"#1a0a0a"},
                                 {"range": [40,70],"color":"#1a1500"},
                                 {"range": [70,100],"color":"#0a1a10"}]},
            ))
            fig.update_layout(height=170, **PLOTLY_THEME)
            st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        f'<div style="background:#111827;border:1px solid #1e3a5f;border-radius:10px;'
        f'padding:10px 14px;color:#8aabcc;font-size:0.84rem;">💡 {s["aciklama"]}</div>',
        unsafe_allow_html=True
    )
    sec("📅 Aylık Özet")
    mp = engine.profit.monthly_profit()
    if not mp.empty:
        fig = go.Figure()
        fig.add_bar(x=mp["Dönem"], y=mp["Gelir"], name="Gelir",
                    marker_color="#0066ff", opacity=0.85)
        fig.add_bar(x=mp["Dönem"], y=mp["Gider"], name="Gider",
                    marker_color="#ff4757", opacity=0.85)
        fig.add_scatter(x=mp["Dönem"], y=mp["NetKar"], name="Net Kar",
                        mode="lines+markers", line=dict(color="#10d994", width=2.5),
                        marker=dict(size=6))
        fig.update_layout(barmode="group", height=300, **PLOTLY_THEME,
                          legend=dict(orientation="h", y=1.08, x=0))
        st.plotly_chart(fig, use_container_width=True)

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
                     color_discrete_sequence=["#0066ff"])
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
                        line=dict(color="#00d4ff", width=2),
                        fillcolor="rgba(0,212,255,0.07)"))
        fig.add_hline(y=0, line_dash="dash", line_color="#ff4757", opacity=0.5)
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
                         color_discrete_sequence=["#ff4757"])
            fig.update_layout(title="Kategoriye Göre Gider", height=280,
                              yaxis=dict(autorange="reversed"), **PLOTLY_THEME)
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        fv  = engine.expense.fixed_vs_variable()
        fig = go.Figure(go.Pie(
            labels=["Sabit", "Değişken"],
            values=[fv["sabit_gider"], fv["degisken_gider"]],
            marker_colors=["#ff4757", "#f97316"], hole=0.5
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
        renkler = ["#10d994" if v >= 0 else "#ff4757" for v in mp["NetKar"]]
        fig = go.Figure()
        fig.add_bar(x=mp["Dönem"], y=mp["NetKar"], marker_color=renkler, name="Net Kar")
        fig.add_scatter(x=mp["Dönem"], y=mp["KarMarji"], name="Kar Marjı (%)",
                        yaxis="y2", mode="lines+markers",
                        line=dict(color="#fbbf24", width=2, dash="dot"),
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
                            mode="lines+markers", line=dict(color="#60a5fa", width=2))
            fig.add_scatter(x=t_df["Dönem"], y=t_df["Tahmin"], name="Tahmin",
                            mode="lines+markers",
                            line=dict(color="#10d994", width=2.5, dash="dot"),
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
        ("Senaryo", [yeni["gelir"],   yeni["gider"],   yeni["net_kar"]],   "#00d4ff"),
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
                f'<div style="background:#0d1520;border:1px solid #0066ff44;'
                f'border-radius:12px;padding:14px 18px;color:#a0c0e8;'
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
                    st.session_state["ai_analiz"] = \
                        st.session_state.gemini.analyze(rapor)
        with c2:
            if st.button("🎯 Stratejik Öneriler", use_container_width=True):
                with st.spinner("Öneriler üretiliyor..."):
                    st.session_state["ai_strateji"] = \
                        st.session_state.gemini.strategic_recommendations(rapor)
        for key, title in [("ai_analiz","📋 Analiz Raporu"),
                            ("ai_strateji","🎯 Stratejik Öneriler")]:
            if st.session_state.get(key):
                sec(title)
                st.markdown(
                    f'<div style="background:#0d1520;border:1px solid #1e3a5f;'
                    f'border-radius:14px;padding:18px 22px;color:#a8c8e8;'
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

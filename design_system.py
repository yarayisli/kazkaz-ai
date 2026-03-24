"""
KazKaz AI — Premium Koyu Tema Design System
============================================
10 Temel İlke:
1.  Tek vurgu rengi: #2563EB lacivert
2.  Koyu tema: #080D1A zemin, #0D1424 yüzey
3.  Sol dikey aksan çizgisi (Bloomberg stili)
4.  KPI sayıları baskın: 26px / 600 weight
5.  Yönetici özeti her ekranın tepesinde
6.  Grafiklerde max 4 renk
7.  Section arası 32px+ boşluk
8.  Alert: yarı saydam zemin + sol çizgi
9.  Menü 3 gruba bölünmüş
10. Hover: border-color değişimi, animasyon yok

Kullanım (her UI dosyasında):
    from design_system import DS, kpi, sec, alert, fmt, PLOTLY_THEME
"""

import streamlit as st

# ─────────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────────

class DS:
    # Backgrounds
    BG_BASE     = "#080D1A"   # Ana zemin
    BG_SURFACE  = "#0D1424"   # Kart yüzeyi
    BG_ELEVATED = "#111D30"   # Hover / seçili
    BG_OVERLAY  = "#162038"   # Modal / tooltip

    # Borders
    BORDER      = "#1A2E4A"   # Standart kenarlık
    BORDER_STR  = "#243D5E"   # Vurgulu kenarlık
    BORDER_FOCUS= "#2563EB"   # Fokus

    # Typography
    TEXT_PRI    = "#DDE4F0"   # Ana metin
    TEXT_SEC    = "#7A90B5"   # İkincil
    TEXT_TER    = "#3D5275"   # Üçüncül / label
    TEXT_DIS    = "#1E3050"   # Pasif

    # İlke 1: Tek vurgu
    ACCENT      = "#2563EB"
    ACCENT_HOV  = "#3B82F6"
    ACCENT_MUT  = "rgba(37,99,235,0.12)"
    ACCENT_BDR  = "rgba(37,99,235,0.30)"

    # İlke 6: 4 renk paleti
    C1 = "#2563EB"   # Primary mavi
    C2 = "#0D9488"   # Teal
    C3 = "#475569"   # Slate
    C4 = "#64748B"   # Muted slate

    # Semantik renkler — kurumsal, neon değil
    GREEN       = "#10B981"
    GREEN_BG    = "rgba(16,185,129,0.10)"
    GREEN_BDR   = "rgba(16,185,129,0.25)"

    RED         = "#EF4444"
    RED_BG      = "rgba(239,68,68,0.10)"
    RED_BDR     = "rgba(239,68,68,0.25)"

    AMBER       = "#F59E0B"
    AMBER_BG    = "rgba(245,158,11,0.10)"
    AMBER_BDR   = "rgba(245,158,11,0.25)"

    BLUE_INFO   = "#3B82F6"
    BLUE_BG     = "rgba(59,130,246,0.10)"
    BLUE_BDR    = "rgba(59,130,246,0.25)"

    # Radius
    R_SM = "6px"
    R_MD = "10px"
    R_LG = "14px"

    # Shadow
    SHADOW = "0 1px 3px rgba(0,0,0,0.4), 0 4px 16px rgba(0,0,0,0.25)"

    FONT = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"


# ─────────────────────────────────────────────
# PLOTLY TEMA — inline, CSS'e bağımlı değil
# ─────────────────────────────────────────────

PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=DS.TEXT_SEC, family=DS.FONT, size=11),
    xaxis=dict(
        gridcolor=DS.BORDER, showgrid=True, zeroline=False,
        tickfont=dict(size=10, color=DS.TEXT_TER),
        linecolor=DS.BORDER,
    ),
    yaxis=dict(
        gridcolor=DS.BORDER, showgrid=True, zeroline=False,
        tickfont=dict(size=10, color=DS.TEXT_TER),
        linecolor=DS.BORDER,
    ),
    margin=dict(l=8, r=8, t=36, b=8),
    legend=dict(
        bgcolor="rgba(13,20,36,0.9)",
        bordercolor=DS.BORDER,
        borderwidth=1,
        font=dict(size=11, color=DS.TEXT_SEC),
    ),
    hoverlabel=dict(
        bgcolor=DS.BG_ELEVATED,
        bordercolor=DS.BORDER_STR,
        font=dict(size=11, color=DS.TEXT_PRI),
    ),
)

# Renk kısayolları (eski kodlarla uyumluluk)
C_BLUE   = DS.C1
C_GREEN  = DS.GREEN
C_RED    = DS.RED
C_AMBER  = DS.AMBER
C_SLATE  = DS.C3
C_CYAN   = DS.C2
C_YELLOW = DS.AMBER
C_PURPLE = "#6366F1"
CHART_COLORS = [DS.C1, DS.C2, DS.C3, DS.C4]


# ─────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ─────────────────────────────────────────────

def fmt(v: float) -> str:
    """Para birimi formatlama"""
    try:
        v = float(v)
        if abs(v) >= 1_000_000_000: return f"{v/1_000_000_000:.1f}Mn ₺"
        if abs(v) >= 1_000_000:     return f"{v/1_000_000:.1f}M ₺"
        if abs(v) >= 1_000:         return f"{v/1_000:.0f}K ₺"
        return f"{v:,.0f} ₺"
    except Exception:
        return str(v)


def score_color(kategori: str) -> str:
    return {
        "Mükemmel": DS.GREEN,
        "İyi":      DS.ACCENT_HOV,
        "Orta":     DS.AMBER,
        "Zayıf":    "#F97316",
        "Kritik":   DS.RED,
    }.get(kategori, DS.TEXT_SEC)


# ─────────────────────────────────────────────
# İLKE 3+4: KPI KARTI
# Sol çizgi, büyük sayı, inline style
# ─────────────────────────────────────────────

def kpi(label: str, value: str, delta: str = "",
        color: str = DS.TEXT_PRI, positive: bool = True):
    """
    Premium KPI kartı.
    İlke 3: Sol dikey aksan çizgisi
    İlke 4: Sayı baskın (26px)
    İlke 10: Hover border (CSS transition)
    """
    try:
        _p = bool(positive)
    except Exception:
        _p = True

    accent = DS.GREEN if _p else DS.RED
    d_bg   = DS.GREEN_BG if _p else DS.RED_BG
    d_bdr  = DS.GREEN_BDR if _p else DS.RED_BDR
    d_clr  = DS.GREEN if _p else DS.RED
    sign   = "+" if _p else "−"

    delta_html = (
        f'<div style="display:inline-flex;align-items:center;gap:3px;'
        f'font-size:11px;font-weight:500;padding:2px 7px;border-radius:4px;'
        f'margin-top:7px;background:{d_bg};color:{d_clr};'
        f'border:1px solid {d_bdr};">'
        f'{sign} {delta}</div>'
    ) if delta else ""

    st.markdown(
        f'<div style="'
        f'background:{DS.BG_SURFACE};'
        f'border:1px solid {DS.BORDER};'
        f'border-radius:{DS.R_LG};'
        f'padding:18px 20px 16px 22px;'
        f'position:relative;overflow:hidden;'
        f'margin-bottom:8px;'
        f'box-shadow:{DS.SHADOW};">'
        # İlke 3: Sol çizgi
        f'<div style="position:absolute;left:0;top:0;bottom:0;'
        f'width:3px;border-radius:4px 0 0 4px;'
        f'background:{accent};"></div>'
        # Label
        f'<div style="font-size:10px;font-weight:600;'
        f'letter-spacing:0.1em;text-transform:uppercase;'
        f'color:{DS.TEXT_TER};margin-bottom:8px;'
        f'font-family:{DS.FONT};">{label}</div>'
        # İlke 4: Büyük sayı
        f'<div style="font-family:{DS.FONT};'
        f'font-size:26px;font-weight:600;'
        f'letter-spacing:-0.025em;line-height:1.1;'
        f'color:{color};">{value}</div>'
        f'{delta_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# İLKE 7: SECTION BAŞLIĞI (32px+ boşluk)
# ─────────────────────────────────────────────

def sec(text: str, small: bool = False):
    fs = "0.72rem" if small else "0.78rem"
    st.markdown(
        f'<div style="'
        f'font-size:{fs};font-weight:600;'
        f'letter-spacing:0.1em;text-transform:uppercase;'
        f'color:{DS.TEXT_TER};'
        f'padding:0 0 10px;'
        f'border-bottom:1px solid {DS.BORDER};'
        f'margin:28px 0 16px;'
        f'font-family:{DS.FONT};">{text}</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# İLKE 5: YÖNETİCİ ÖZETİ BLOKU
# ─────────────────────────────────────────────

def exec_summary(text: str, title: str = "Yönetici Değerlendirmesi"):
    st.markdown(
        f'<div style="'
        f'background:{DS.BG_SURFACE};'
        f'border:1px solid {DS.BORDER};'
        f'border-left:3px solid {DS.ACCENT};'
        f'border-radius:0 {DS.R_LG} {DS.R_LG} 0;'
        f'padding:14px 18px;margin-bottom:24px;'
        f'box-shadow:{DS.SHADOW};">'
        f'<div style="font-size:9px;font-weight:700;'
        f'letter-spacing:0.14em;text-transform:uppercase;'
        f'color:{DS.ACCENT};margin-bottom:7px;'
        f'font-family:{DS.FONT};">{title}</div>'
        f'<div style="font-size:13px;color:{DS.TEXT_SEC};'
        f'line-height:1.65;font-family:{DS.FONT};">{text}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# İLKE 8: ALERT SATIRI
# Yarı saydam zemin + sol çizgi
# ─────────────────────────────────────────────

def alert(title: str, body: str = "", level: str = "info"):
    """
    level: "critical" | "warning" | "info" | "success"
    """
    cfg = {
        "critical": (DS.RED,      DS.RED_BG,   DS.RED_BDR),
        "warning":  (DS.AMBER,    DS.AMBER_BG, DS.AMBER_BDR),
        "info":     (DS.BLUE_INFO,DS.BLUE_BG,  DS.BLUE_BDR),
        "success":  (DS.GREEN,    DS.GREEN_BG, DS.GREEN_BDR),
    }
    clr, bg, bdr = cfg.get(level, cfg["info"])
    body_html = (
        f'<div style="font-size:12px;color:{DS.TEXT_SEC};'
        f'line-height:1.5;margin-top:3px;">{body}</div>'
    ) if body else ""

    st.markdown(
        f'<div style="'
        f'background:{bg};'
        f'border:1px solid {bdr};'
        f'border-left:3px solid {clr};'
        f'border-radius:0 {DS.R_MD} {DS.R_MD} 0;'
        f'padding:12px 14px;margin-bottom:8px;">'
        f'<div style="font-size:12px;font-weight:600;'
        f'color:{DS.TEXT_PRI};">{title}</div>'
        f'{body_html}</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# BADGE
# ─────────────────────────────────────────────

def badge(text: str, level: str = "info") -> str:
    """HTML badge string döndürür (st.markdown içinde kullanılır)"""
    cfg = {
        "success": (DS.GREEN,      DS.GREEN_BG,  DS.GREEN_BDR),
        "warning": (DS.AMBER,      DS.AMBER_BG,  DS.AMBER_BDR),
        "critical":(DS.RED,        DS.RED_BG,    DS.RED_BDR),
        "info":    (DS.BLUE_INFO,  DS.BLUE_BG,   DS.BLUE_BDR),
        "neutral": (DS.TEXT_SEC,   DS.BG_ELEVATED, DS.BORDER),
    }
    clr, bg, bdr = cfg.get(level, cfg["info"])
    return (
        f'<span style="display:inline-flex;align-items:center;'
        f'padding:2px 8px;border-radius:4px;'
        f'font-size:10px;font-weight:600;letter-spacing:0.05em;'
        f'text-transform:uppercase;'
        f'background:{bg};color:{clr};border:1px solid {bdr};">'
        f'{text}</span>'
    )


# ─────────────────────────────────────────────
# PAGE HEADER (İlke 5 uyumlu)
# ─────────────────────────────────────────────

def page_header(title: str, subtitle: str = "", badges: list = None):
    """
    badges: [("İyi", "success"), ("3 Uyarı", "warning")]
    """
    badge_html = ""
    if badges:
        badge_html = " &nbsp;" + " &nbsp;".join(
            badge(t, l) for t, l in badges
        )

    st.markdown(
        f'<div style="'
        f'padding:4px 0 20px;'
        f'border-bottom:1px solid {DS.BORDER};'
        f'margin-bottom:24px;">'
        f'<div style="font-size:18px;font-weight:600;'
        f'letter-spacing:-0.01em;color:{DS.TEXT_PRI};'
        f'font-family:{DS.FONT};">{title}</div>'
        f'<div style="font-size:12px;color:{DS.TEXT_TER};'
        f'margin-top:5px;font-family:{DS.FONT};">'
        f'{subtitle}{badge_html}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# CSS INJECT (config.toml'u destekler)
# ─────────────────────────────────────────────

GLOBAL_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {{
    font-family: {DS.FONT} !important;
    -webkit-font-smoothing: antialiased;
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: {DS.BG_BASE} !important;
    border-right: 1px solid {DS.BORDER} !important;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    background: {DS.BG_SURFACE} !important;
    border: 1px solid {DS.BORDER} !important;
    border-radius: {DS.R_MD} !important;
    padding: 3px !important;
    gap: 2px !important;
}}
.stTabs [data-baseweb="tab"] {{
    color: {DS.TEXT_TER} !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    border-radius: 7px !important;
    padding: 6px 14px !important;
    font-family: {DS.FONT} !important;
}}
.stTabs [data-baseweb="tab"]:hover {{
    color: {DS.TEXT_SEC} !important;
    background: {DS.BG_ELEVATED} !important;
}}
.stTabs [aria-selected="true"] {{
    color: {DS.TEXT_PRI} !important;
    background: {DS.BG_ELEVATED} !important;
    border: 1px solid {DS.BORDER_STR} !important;
    font-weight: 600 !important;
}}

/* Buttons */
.stButton > button {{
    background: {DS.ACCENT} !important;
    color: #fff !important;
    border: none !important;
    border-radius: {DS.R_MD} !important;
    font-family: {DS.FONT} !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 8px 18px !important;
    transition: background 0.15s !important;
}}
.stButton > button:hover {{
    background: {DS.ACCENT_HOV} !important;
}}
.stDownloadButton > button {{
    background: {DS.BG_ELEVATED} !important;
    color: {DS.TEXT_SEC} !important;
    border: 1px solid {DS.BORDER} !important;
    border-radius: {DS.R_MD} !important;
    font-size: 12px !important;
    transition: border-color 0.15s !important;
}}
.stDownloadButton > button:hover {{
    border-color: {DS.ACCENT} !important;
    color: {DS.TEXT_PRI} !important;
}}

/* Inputs */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea textarea,
.stSelectbox > div > div {{
    background: {DS.BG_ELEVATED} !important;
    border: 1px solid {DS.BORDER} !important;
    border-radius: {DS.R_MD} !important;
    color: {DS.TEXT_PRI} !important;
    font-family: {DS.FONT} !important;
    font-size: 13px !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: {DS.ACCENT} !important;
    box-shadow: 0 0 0 3px {DS.ACCENT_MUT} !important;
}}

/* Metrics */
[data-testid="stMetric"] {{
    background: {DS.BG_SURFACE} !important;
    border: 1px solid {DS.BORDER} !important;
    border-radius: {DS.R_LG} !important;
    padding: 16px 18px !important;
}}
[data-testid="stMetricLabel"] {{
    font-size: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: {DS.TEXT_TER} !important;
}}
[data-testid="stMetricValue"] {{
    font-size: 22px !important;
    font-weight: 600 !important;
    letter-spacing: -0.025em !important;
    color: {DS.TEXT_PRI} !important;
}}

/* File uploader */
[data-testid="stFileUploader"] {{
    background: {DS.BG_ELEVATED} !important;
    border: 1.5px dashed {DS.BORDER_STR} !important;
    border-radius: {DS.R_LG} !important;
}}

/* Dataframe */
.dataframe {{
    background: {DS.BG_SURFACE} !important;
    color: {DS.TEXT_PRI} !important;
    border: 1px solid {DS.BORDER} !important;
    border-radius: {DS.R_MD} !important;
    font-size: 12px !important;
    font-family: {DS.FONT} !important;
}}
.dataframe th {{
    background: {DS.BG_ELEVATED} !important;
    color: {DS.TEXT_TER} !important;
    font-size: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    border-bottom: 1px solid {DS.BORDER} !important;
    padding: 10px 14px !important;
}}
.dataframe td {{
    border-bottom: 1px solid {DS.BG_ELEVATED} !important;
    padding: 8px 14px !important;
    color: {DS.TEXT_SEC} !important;
}}
.dataframe tr:hover td {{
    background: {DS.BG_ELEVATED} !important;
    color: {DS.TEXT_PRI} !important;
}}

/* Scrollbar */
::-webkit-scrollbar {{ width: 5px; height: 5px; }}
::-webkit-scrollbar-track {{ background: {DS.BG_BASE}; }}
::-webkit-scrollbar-thumb {{ background: {DS.BORDER_STR}; border-radius: 3px; }}

/* Misc */
hr {{ border-color: {DS.BORDER} !important; margin: 24px 0 !important; }}
.stSpinner > div {{ border-top-color: {DS.ACCENT} !important; }}
.stProgress > div > div > div > div {{ background: {DS.ACCENT} !important; }}
small, .stCaption {{ color: {DS.TEXT_TER} !important; font-size: 11px !important; }}
.stRadio label, .stCheckbox label {{ color: {DS.TEXT_SEC} !important; font-size: 13px !important; }}
</style>
"""


def inject_css():
    """app.py'de bir kez çağrılır"""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

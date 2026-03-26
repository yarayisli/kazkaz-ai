"""
KazKaz AI — Premium UI Components
===================================
Streamlit components.html ile tam CSS kontrolü.
Hiçbir Streamlit style override'ı etkileyemez.

Kullanım:
    from ui_components import (
        render_topbar, render_kpi_row, render_exec_summary,
        render_alerts, render_page_header, render_section,
        render_health_bars, render_badge, STYLE
    )
"""

import streamlit.components.v1 as components

# ─────────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────────

T = {
    # Backgrounds
    "bg_page":     "#F7F8FA",
    "bg_surface":  "#FFFFFF",
    "bg_elevated": "#F3F4F6",
    "bg_hover":    "#F9FAFB",

    # Borders
    "border":      "#E2E5EB",
    "border_str":  "#C9CDD6",
    "border_focus":"#1B3A6B",

    # Typography
    "text_pri":    "#1A1A2E",
    "text_sec":    "#4B5563",
    "text_ter":    "#9CA3AF",
    "text_dis":    "#D1D5DB",

    # Brand — koyu lacivert, tek vurgu
    "accent":      "#1B3A6B",
    "accent_lt":   "#2B4F8C",
    "accent_mut":  "#EEF2FF",
    "accent_bdr":  "#C7D2FE",

    # Semantik
    "green":       "#059669",
    "green_bg":    "#ECFDF5",
    "green_bdr":   "#A7F3D0",
    "amber":       "#D97706",
    "amber_bg":    "#FFFBEB",
    "amber_bdr":   "#FDE68A",
    "red":         "#DC2626",
    "red_bg":      "#FEF2F2",
    "red_bdr":     "#FECACA",
    "blue":        "#2563EB",
    "blue_bg":     "#EFF6FF",
    "blue_bdr":    "#BFDBFE",

    # Font
    "font":        "-apple-system,'Helvetica Neue',Arial,sans-serif",
}


# ─────────────────────────────────────────────
# BASE CSS — tüm component'lerde ortak
# ─────────────────────────────────────────────

BASE_CSS = f"""
<style>
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{
    font-family: {T['font']};
    background: transparent;
    color: {T['text_pri']};
    -webkit-font-smoothing: antialiased;
}}
.kz-label {{
    font-size: 9px;
    font-weight: 600;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: {T['text_ter']};
}}
.kz-title {{
    font-size: 13px;
    font-weight: 600;
    color: {T['text_pri']};
    letter-spacing: -.01em;
}}
.kz-body {{
    font-size: 12px;
    color: {T['text_sec']};
    line-height: 1.6;
}}
</style>
"""


# ─────────────────────────────────────────────
# TOPBAR
# ─────────────────────────────────────────────

def render_topbar(sirket_adi: str = "Şirket", donem: str = "2024",
                  aktif_period: str = "12A", saglik_badge: str = "İyi"):
    """
    Üst navigasyon çubuğu.
    Şirket adı, dönem seçici, sağlık badge.
    """
    periods = ["Q1", "Q2", "YTD", "12A"]
    period_html = ""
    for p in periods:
        sel = f'background:{T["bg_surface"]};color:{T["accent"]};font-weight:600;box-shadow:0 0 0 0.5px {T["border"]};' if p == aktif_period else f'color:{T["text_ter"]};'
        period_html += f'<div style="font-size:10px;padding:3px 9px;border-radius:4px;cursor:pointer;{sel}">{p}</div>'

    html = f"""
{BASE_CSS}
<div style="
    height:44px;background:{T['bg_surface']};
    border-bottom:0.5px solid {T['border']};
    display:flex;align-items:center;
    padding:0 20px;justify-content:space-between;
    font-family:{T['font']};
">
    <div style="display:flex;align-items:center;gap:6px;">
        <span style="font-size:11px;color:{T['text_ter']};">KazKaz AI</span>
        <span style="color:{T['border_str']};font-size:11px;">/</span>
        <span style="font-size:11px;font-weight:500;color:{T['text_sec']};">{sirket_adi}</span>
    </div>
    <div style="display:flex;align-items:center;gap:8px;">
        <div style="display:flex;gap:2px;background:{T['bg_elevated']};padding:3px;border-radius:6px;">
            {period_html}
        </div>
        <div style="font-size:9px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;
                    padding:3px 9px;border-radius:4px;
                    background:{T['green_bg']};color:{T['green']};
                    border:0.5px solid {T['green_bdr']};">
            {saglik_badge}
        </div>
        <div style="font-size:10px;color:{T['text_ter']};">{donem}</div>
    </div>
</div>
"""
    components.html(html, height=45, scrolling=False)


# ─────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────

def render_page_header(title: str, subtitle: str = "",
                       badge_text: str = "", badge_level: str = "info"):
    """Sayfa başlığı — büyük isim, alt açıklama, opsiyonel badge."""
    badge_colors = {
        "success": (T["green_bg"],  T["green"],  T["green_bdr"]),
        "warning": (T["amber_bg"],  T["amber"],  T["amber_bdr"]),
        "danger":  (T["red_bg"],    T["red"],    T["red_bdr"]),
        "info":    (T["blue_bg"],   T["blue"],   T["blue_bdr"]),
        "brand":   (T["accent_mut"],T["accent"], T["accent_bdr"]),
    }
    bg, clr, bdr = badge_colors.get(badge_level, badge_colors["info"])
    badge_html = f"""
        <span style="font-size:9px;font-weight:600;letter-spacing:.05em;
                     text-transform:uppercase;padding:2px 8px;border-radius:4px;
                     background:{bg};color:{clr};border:0.5px solid {bdr};">
            {badge_text}
        </span>""" if badge_text else ""

    html = f"""
{BASE_CSS}
<div style="
    padding:4px 0 18px;
    border-bottom:0.5px solid {T['border']};
    margin-bottom:20px;
    font-family:{T['font']};
">
    <div style="font-size:18px;font-weight:600;color:{T['text_pri']};
                letter-spacing:-.02em;margin-bottom:5px;">
        {title}
    </div>
    <div style="display:flex;align-items:center;gap:8px;">
        <span style="font-size:11px;color:{T['text_ter']};">{subtitle}</span>
        {badge_html}
    </div>
</div>
"""
    components.html(html, height=70, scrolling=False)


# ─────────────────────────────────────────────
# EXECUTIVE SUMMARY
# ─────────────────────────────────────────────

def render_exec_summary(text: str, title: str = "Yönetici Değerlendirmesi"):
    """
    İlke 5: Her ekranın tepesinde yönetici özeti.
    Sol lacivert aksan çizgisi.
    """
    html = f"""
{BASE_CSS}
<div style="
    background:{T['bg_surface']};
    border:0.5px solid {T['border']};
    border-left:3px solid {T['accent']};
    border-radius:0 8px 8px 0;
    padding:12px 16px;
    margin-bottom:16px;
    font-family:{T['font']};
">
    <div style="font-size:8px;font-weight:700;letter-spacing:.14em;
                text-transform:uppercase;color:{T['accent']};margin-bottom:6px;">
        {title}
    </div>
    <div style="font-size:12px;color:{T['text_sec']};line-height:1.65;">
        {text}
    </div>
</div>
"""
    components.html(html, height=80, scrolling=False)


# ─────────────────────────────────────────────
# KPI ROW
# ─────────────────────────────────────────────

def render_kpi_row(kpis: list, height: int = 110):
    """
    İlke 3: Sol çizgi  |  İlke 4: Büyük sayı

    kpis: [
        {"label": "Toplam Gelir", "value": "9.4M ₺",
         "delta": "+%65", "positive": True},
        ...
    ]
    """
    cols = len(kpis)
    cards_html = ""

    for kpi in kpis:
        label    = kpi.get("label", "")
        value    = kpi.get("value", "—")
        delta    = kpi.get("delta", "")
        positive = kpi.get("positive", True)
        color    = kpi.get("color", T["text_pri"])

        # Accent çizgisi rengi
        acc_clr = T["green"] if positive else T["red"]
        if kpi.get("accent_color"):
            acc_clr = kpi["accent_color"]

        # Delta badge
        if delta:
            d_bg  = T["green_bg"] if positive else T["red_bg"]
            d_clr = T["green"]    if positive else T["red"]
            d_bdr = T["green_bdr"]if positive else T["red_bdr"]
            sign  = "+" if positive else "−"
            delta_html = f"""
            <div style="display:inline-flex;align-items:center;
                        font-size:10px;font-weight:500;
                        padding:2px 6px;border-radius:3px;
                        margin-top:6px;
                        background:{d_bg};color:{d_clr};
                        border:0.5px solid {d_bdr};">
                {sign} {delta}
            </div>"""
        else:
            delta_html = ""

        cards_html += f"""
        <div style="
            background:{T['bg_surface']};
            border:0.5px solid {T['border']};
            border-radius:8px;
            padding:14px 16px 12px 18px;
            position:relative;overflow:hidden;
            flex:1;min-width:0;
        ">
            <div style="position:absolute;left:0;top:0;bottom:0;
                        width:3px;background:{acc_clr};
                        border-radius:0;"></div>
            <div style="font-size:9px;font-weight:600;letter-spacing:.1em;
                        text-transform:uppercase;color:{T['text_ter']};
                        margin-bottom:7px;">{label}</div>
            <div style="font-size:22px;font-weight:600;
                        letter-spacing:-.03em;line-height:1;
                        color:{color};">{value}</div>
            {delta_html}
        </div>"""

    html = f"""
{BASE_CSS}
<div style="
    display:flex;gap:10px;
    font-family:{T['font']};
    margin-bottom:2px;
">
    {cards_html}
</div>
"""
    components.html(html, height=height, scrolling=False)


# ─────────────────────────────────────────────
# SECTION HEADER
# ─────────────────────────────────────────────

def render_section(title: str, top_margin: int = 24):
    """İlke 7: 32px+ boşluk, section başlığı."""
    html = f"""
{BASE_CSS}
<div style="
    font-size:9px;font-weight:600;
    letter-spacing:.1em;text-transform:uppercase;
    color:{T['text_ter']};
    padding:0 0 8px;
    border-bottom:0.5px solid {T['border']};
    margin-top:{top_margin}px;
    margin-bottom:4px;
    font-family:{T['font']};
">{title}</div>
"""
    components.html(html, height=30 + top_margin, scrolling=False)


# ─────────────────────────────────────────────
# ALERTS
# ─────────────────────────────────────────────

def render_alerts(alerts: list):
    """
    İlke 8: Açık zemin + sol çizgi.

    alerts: [
        {"title": "...", "body": "...", "level": "warning"},
        ...
    ]
    level: "warning" | "info" | "success" | "danger"
    """
    level_cfg = {
        "warning": (T["amber_bg"], T["amber"], T["amber_bdr"]),
        "info":    (T["blue_bg"],  T["blue"],  T["blue_bdr"]),
        "success": (T["green_bg"], T["green"], T["green_bdr"]),
        "danger":  (T["red_bg"],   T["red"],   T["red_bdr"]),
    }

    rows_html = ""
    for a in alerts:
        bg, clr, bdr = level_cfg.get(a.get("level","info"), level_cfg["info"])
        rows_html += f"""
        <div style="
            background:{bg};
            border:0.5px solid {bdr};
            border-left:3px solid {clr};
            border-radius:0 6px 6px 0;
            padding:10px 14px;
            margin-bottom:6px;
        ">
            <div style="font-size:11px;font-weight:600;
                        color:{T['text_pri']};margin-bottom:2px;">
                {a.get('title','')}
            </div>
            <div style="font-size:11px;color:{T['text_sec']};line-height:1.5;">
                {a.get('body','')}
            </div>
        </div>"""

    html = f"""
{BASE_CSS}
<div style="font-family:{T['font']};">
    {rows_html}
</div>
"""
    h = len(alerts) * 68 + 10
    components.html(html, height=h, scrolling=False)


# ─────────────────────────────────────────────
# HEALTH BARS
# ─────────────────────────────────────────────

def render_health_bars(scores: dict):
    """
    Sağlık alt skorları — progress bar.

    scores: {"Karlılık": 82, "Büyüme": 75, ...}
    """
    rows_html = ""
    for label, val in scores.items():
        val   = min(int(val or 0), 100)
        clr   = T["green"] if val >= 70 else T["amber"] if val >= 40 else T["red"]
        rows_html += f"""
        <div style="margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;
                        margin-bottom:5px;">
                <span style="font-size:11px;font-weight:500;
                             color:{T['text_sec']};">{label}</span>
                <span style="font-size:11px;font-weight:600;
                             color:{clr};">{val}</span>
            </div>
            <div style="background:{T['bg_elevated']};border-radius:2px;
                        height:5px;overflow:hidden;">
                <div style="background:{clr};width:{val}%;
                            height:100%;border-radius:2px;"></div>
            </div>
        </div>"""

    html = f"""
{BASE_CSS}
<div style="font-family:{T['font']};padding:4px 0;">
    {rows_html}
</div>
"""
    h = len(scores) * 42 + 16
    components.html(html, height=h, scrolling=False)


# ─────────────────────────────────────────────
# STAT STRIP — yatay özet şeridi
# ─────────────────────────────────────────────

def render_stat_strip(stats: list):
    """
    Küçük yatay istatistik şeridi.
    stats: [{"label":"Müşteri","value":"15"},...]
    """
    items_html = ""
    for i, s in enumerate(stats):
        sep = f'<div style="width:0.5px;background:{T["border"]};height:28px;"></div>' if i > 0 else ""
        items_html += f"""
        {sep}
        <div style="padding:0 16px;text-align:center;">
            <div style="font-size:9px;font-weight:600;letter-spacing:.08em;
                        text-transform:uppercase;color:{T['text_ter']};
                        margin-bottom:3px;">{s['label']}</div>
            <div style="font-size:15px;font-weight:600;color:{T['text_pri']};
                        letter-spacing:-.02em;">{s['value']}</div>
        </div>"""

    html = f"""
{BASE_CSS}
<div style="
    background:{T['bg_surface']};
    border:0.5px solid {T['border']};
    border-radius:8px;
    display:flex;align-items:center;
    padding:10px 0;
    font-family:{T['font']};
    margin-bottom:2px;
">
    {items_html}
</div>
"""
    components.html(html, height=62, scrolling=False)


# ─────────────────────────────────────────────
# INSIGHT CARD
# ─────────────────────────────────────────────

def render_insight_card(title: str, items: list, icon: str = "◈"):
    """
    AI veya sistem insight kartı.
    items: ["...", "...", ...]
    """
    items_html = "".join(
        f'<div style="display:flex;gap:8px;margin-bottom:6px;">'
        f'<span style="color:{T["accent"]};font-size:11px;flex-shrink:0;margin-top:1px;">›</span>'
        f'<span style="font-size:12px;color:{T["text_sec"]};line-height:1.5;">{item}</span>'
        f'</div>'
        for item in items
    )

    html = f"""
{BASE_CSS}
<div style="
    background:{T['bg_surface']};
    border:0.5px solid {T['border']};
    border-radius:8px;
    padding:14px 16px;
    font-family:{T['font']};
">
    <div style="display:flex;align-items:center;gap:6px;margin-bottom:10px;">
        <span style="font-size:14px;color:{T['accent']};">{icon}</span>
        <span style="font-size:11px;font-weight:600;color:{T['text_pri']};">{title}</span>
    </div>
    {items_html}
</div>
"""
    h = len(items) * 30 + 56
    components.html(html, height=h, scrolling=False)


# ─────────────────────────────────────────────
# BADGE (inline kullanım için HTML string)
# ─────────────────────────────────────────────

def badge_html(text: str, level: str = "info") -> str:
    """st.markdown() içinde kullanılacak badge HTML'i döndürür."""
    cfg = {
        "success": (T["green_bg"],  T["green"],  T["green_bdr"]),
        "warning": (T["amber_bg"],  T["amber"],  T["amber_bdr"]),
        "danger":  (T["red_bg"],    T["red"],    T["red_bdr"]),
        "info":    (T["blue_bg"],   T["blue"],   T["blue_bdr"]),
        "brand":   (T["accent_mut"],T["accent"], T["accent_bdr"]),
        "neutral": (T["bg_elevated"],T["text_sec"],T["border"]),
    }
    bg, clr, bdr = cfg.get(level, cfg["info"])
    return (
        f'<span style="display:inline-flex;align-items:center;'
        f'padding:2px 8px;border-radius:4px;'
        f'font-size:9px;font-weight:600;letter-spacing:.05em;'
        f'text-transform:uppercase;'
        f'background:{bg};color:{clr};'
        f'border:0.5px solid {bdr};">'
        f'{text}</span>'
    )


# ─────────────────────────────────────────────
# DIVIDER
# ─────────────────────────────────────────────

def render_divider():
    html = f'<hr style="border:none;border-top:0.5px solid {T["border"]};margin:4px 0;">'
    components.html(html, height=2, scrolling=False)


# ─────────────────────────────────────────────
# YARDIMCI
# ─────────────────────────────────────────────

def fmt(v: float) -> str:
    try:
        v = float(v)
        if abs(v) >= 1_000_000_000: return f"{v/1_000_000_000:.1f}Mn ₺"
        if abs(v) >= 1_000_000:     return f"{v/1_000_000:.1f}M ₺"
        if abs(v) >= 1_000:         return f"{v/1_000:.0f}K ₺"
        return f"{v:,.0f} ₺"
    except Exception:
        return str(v)


# Renk yardımcıları
def score_color(kategori: str) -> str:
    return {
        "Mükemmel": T["green"],
        "İyi":      T["accent_lt"],
        "Orta":     T["amber"],
        "Zayıf":    "#F97316",
        "Kritik":   T["red"],
    }.get(kategori, T["text_sec"])

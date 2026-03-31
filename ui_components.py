"""
KazKaz AI — Premium UI Components v2
======================================
Basarsoft.com.tr ilhamıyla özgün tasarım sistemi.
Streamlit components.html ile tam CSS kontrolü.

Renk sistemi:
  Navy Prime  #0F2252 — ana marka rengi
  Navy Mid    #1B3A6B — ikincil lacivert
  Action Blue #2563EB — interaktif elementler
  Page BG     #F7F8FC — sayfa zemini
  Surface     #FFFFFF — kart yüzeyi
  Border      #E8EAEF — kenarlıklar
"""

import streamlit.components.v1 as components

# ─────────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────────
T = {
    "bg_page":    "#F7F8FC",
    "bg_surface": "#FFFFFF",
    "bg_elevated":"#F3F5F9",
    "bg_hover":   "#F9FAFB",

    "border":     "#E8EAEF",
    "border_str": "#D1D5DB",

    "text_pri":   "#1A1F36",
    "text_sec":   "#4B5563",
    "text_ter":   "#9CA3AF",

    "navy":       "#0F2252",
    "navy_mid":   "#1B3A6B",
    "navy_lt":    "#EEF2FF",
    "navy_bdr":   "#C7D2FE",

    "action":     "#2563EB",
    "action_lt":  "#DBEAFE",

    "green":      "#059669",
    "green_bg":   "#ECFDF5",
    "green_bdr":  "#A7F3D0",

    "amber":      "#D97706",
    "amber_bg":   "#FFFBEB",
    "amber_bdr":  "#FDE68A",

    "red":        "#DC2626",
    "red_bg":     "#FEF2F2",
    "red_bdr":    "#FECACA",

    "font": "-apple-system,'Segoe UI','Helvetica Neue',Arial,sans-serif",
}

BASE = f"""<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:{T['font']};background:transparent;
     color:{T['text_pri']};-webkit-font-smoothing:antialiased}}
</style>"""


# ─────────────────────────────────────────────
# TOPBAR
# ─────────────────────────────────────────────
def render_topbar(sirket_adi="Şirket", donem="2024",
                  aktif_period="12A", saglik_badge="İyi",
                  saglik_level="success"):
    periods = ["Q1","Q2","YTD","12A","Tümü"]
    p_html = ""
    for p in periods:
        if p == aktif_period:
            s = f"background:{T['bg_surface']};color:{T['navy']};font-weight:600;box-shadow:0 0 0 0.5px {T['border']};"
        else:
            s = f"color:{T['text_ter']};"
        p_html += f'<div style="font-size:10px;padding:3px 8px;border-radius:5px;cursor:pointer;{s}">{p}</div>'

    lvl = {
        "success": (T["green_bg"],  T["green"],  T["green_bdr"]),
        "warning": (T["amber_bg"],  T["amber"],  T["amber_bdr"]),
        "danger":  (T["red_bg"],    T["red"],    T["red_bdr"]),
    }.get(saglik_level, (T["navy_lt"], T["navy"], T["navy_bdr"]))

    html = f"""{BASE}
<div style="height:44px;background:{T['bg_surface']};
     border-bottom:1px solid {T['border']};
     display:flex;align-items:center;
     padding:0 20px;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:6px;">
    <span style="font-size:11px;color:{T['text_ter']};">KazKaz AI</span>
    <span style="color:{T['border_str']};font-size:11px;">/</span>
    <span style="font-size:11px;font-weight:500;color:{T['text_sec']};">{sirket_adi}</span>
  </div>
  <div style="display:flex;align-items:center;gap:8px;">
    <div style="display:flex;gap:2px;background:{T['bg_elevated']};
               padding:3px;border-radius:7px;">{p_html}</div>
    <div style="font-size:9px;font-weight:600;letter-spacing:.05em;
                text-transform:uppercase;padding:3px 9px;border-radius:5px;
                background:{lvl[0]};color:{lvl[1]};border:1px solid {lvl[2]};">
      {saglik_badge}
    </div>
    <span style="font-size:10px;color:{T['text_ter']};">{donem}</span>
  </div>
</div>"""
    components.html(html, height=45, scrolling=False)


# ─────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────
def render_page_header(title, subtitle="", badge_text="", badge_level="info"):
    lvl = {
        "success": (T["green_bg"],  T["green"],  T["green_bdr"]),
        "warning": (T["amber_bg"],  T["amber"],  T["amber_bdr"]),
        "danger":  (T["red_bg"],    T["red"],    T["red_bdr"]),
        "info":    (T["action_lt"], T["action"], "#BFDBFE"),
        "brand":   (T["navy_lt"],   T["navy"],   T["navy_bdr"]),
    }.get(badge_level, (T["navy_lt"], T["navy"], T["navy_bdr"]))

    badge = f"""<span style="font-size:9px;font-weight:600;letter-spacing:.05em;
        text-transform:uppercase;padding:2px 8px;border-radius:4px;
        background:{lvl[0]};color:{lvl[1]};border:1px solid {lvl[2]};">
        {badge_text}</span>""" if badge_text else ""

    html = f"""{BASE}
<div style="padding:4px 0 18px;border-bottom:1px solid {T['border']};margin-bottom:20px;">
  <div style="font-size:18px;font-weight:700;color:{T['navy']};
              letter-spacing:-.02em;margin-bottom:5px;">{title}</div>
  <div style="display:flex;align-items:center;gap:8px;">
    <span style="font-size:11px;color:{T['text_ter']};">{subtitle}</span>
    {badge}
  </div>
</div>"""
    components.html(html, height=72, scrolling=False)


# ─────────────────────────────────────────────
# EXECUTIVE SUMMARY
# ─────────────────────────────────────────────
def render_exec_summary(text, title="Yönetici Değerlendirmesi"):
    html = f"""{BASE}
<div style="background:{T['bg_surface']};border:1px solid {T['border']};
     border-left:3px solid {T['navy']};border-radius:0 8px 8px 0;
     padding:12px 16px;margin-bottom:16px;">
  <div style="font-size:8px;font-weight:700;letter-spacing:.14em;
              text-transform:uppercase;color:{T['navy']};margin-bottom:6px;">
    {title}
  </div>
  <div style="font-size:12px;color:{T['text_sec']};line-height:1.65;">{text}</div>
</div>"""
    components.html(html, height=82, scrolling=False)


# ─────────────────────────────────────────────
# KPI ROW
# ─────────────────────────────────────────────
def render_kpi_row(kpis, height=108):
    cards = ""
    for k in kpis:
        label    = k.get("label","")
        value    = k.get("value","—")
        delta    = k.get("delta","")
        positive = k.get("positive", True)
        color    = k.get("color", T["text_pri"])
        acc      = k.get("accent_color",
                         T["green"] if positive else T["red"])

        if delta:
            d_bg  = T["green_bg"]  if positive else T["red_bg"]
            d_clr = T["green"]     if positive else T["red"]
            d_bdr = T["green_bdr"] if positive else T["red_bdr"]
            sign  = "+" if positive else "−"
            dh = f"""<div style="display:inline-flex;align-items:center;
                font-size:10px;font-weight:500;padding:2px 6px;
                border-radius:3px;margin-top:6px;
                background:{d_bg};color:{d_clr};border:1px solid {d_bdr};">
                {sign} {delta}</div>"""
        else:
            dh = ""

        cards += f"""
<div style="background:{T['bg_surface']};border:1px solid {T['border']};
     border-radius:8px;padding:14px 16px 12px 18px;
     position:relative;overflow:hidden;flex:1;min-width:0;">
  <div style="position:absolute;left:0;top:0;bottom:0;width:3px;
              background:{acc};border-radius:0;"></div>
  <div style="font-size:9px;font-weight:700;letter-spacing:.1em;
              text-transform:uppercase;color:{T['text_ter']};margin-bottom:7px;">
    {label}</div>
  <div style="font-size:22px;font-weight:600;letter-spacing:-.03em;
              line-height:1;color:{color};">{value}</div>
  {dh}
</div>"""

    html = f"""{BASE}
<div style="display:flex;gap:10px;margin-bottom:2px;">{cards}</div>"""
    components.html(html, height=height, scrolling=False)


# ─────────────────────────────────────────────
# SECTION HEADER
# ─────────────────────────────────────────────
def render_section(title, top_margin=24):
    html = f"""{BASE}
<div style="font-size:9px;font-weight:700;letter-spacing:.1em;
     text-transform:uppercase;color:{T['text_ter']};
     padding:0 0 8px;border-bottom:1px solid {T['border']};
     margin-top:{top_margin}px;margin-bottom:4px;">{title}</div>"""
    components.html(html, height=28+top_margin, scrolling=False)


# ─────────────────────────────────────────────
# ALERTS
# ─────────────────────────────────────────────
def render_alerts(alerts):
    lvl_cfg = {
        "warning": (T["amber_bg"], T["amber"], T["amber_bdr"]),
        "info":    (T["navy_lt"],  T["navy"],  T["navy_bdr"]),
        "success": (T["green_bg"], T["green"], T["green_bdr"]),
        "danger":  (T["red_bg"],   T["red"],   T["red_bdr"]),
    }
    rows = ""
    for a in alerts:
        bg, clr, bdr = lvl_cfg.get(a.get("level","info"), lvl_cfg["info"])
        rows += f"""
<div style="background:{bg};border:1px solid {bdr};border-left:3px solid {clr};
     border-radius:0 7px 7px 0;padding:10px 14px;margin-bottom:6px;">
  <div style="font-size:11px;font-weight:600;color:{T['text_pri']};margin-bottom:2px;">
    {a.get('title','')}</div>
  <div style="font-size:11px;color:{T['text_sec']};line-height:1.5;">
    {a.get('body','')}</div>
</div>"""
    html = f"""{BASE}<div>{rows}</div>"""
    components.html(html, height=len(alerts)*70+8, scrolling=False)


# ─────────────────────────────────────────────
# HEALTH BARS
# ─────────────────────────────────────────────
def render_health_bars(scores):
    rows = ""
    for label, val in scores.items():
        val  = min(int(val or 0), 100)
        clr  = T["green"] if val >= 70 else T["amber"] if val >= 40 else T["red"]
        rows += f"""
<div style="margin-bottom:13px;">
  <div style="display:flex;justify-content:space-between;margin-bottom:5px;">
    <span style="font-size:11px;font-weight:500;color:{T['text_sec']};">{label}</span>
    <span style="font-size:11px;font-weight:600;color:{clr};">{val}</span>
  </div>
  <div style="background:{T['bg_elevated']};border-radius:2px;height:5px;overflow:hidden;">
    <div style="background:{clr};width:{val}%;height:100%;border-radius:2px;"></div>
  </div>
</div>"""
    html = f"""{BASE}<div style="padding:4px 0;">{rows}</div>"""
    components.html(html, height=len(scores)*42+16, scrolling=False)


# ─────────────────────────────────────────────
# STAT STRIP
# ─────────────────────────────────────────────
def render_stat_strip(stats):
    items = ""
    for i, s in enumerate(stats):
        sep = f'<div style="width:1px;background:{T["border"]};height:28px;"></div>' if i else ""
        items += f"""{sep}
<div style="padding:0 16px;text-align:center;">
  <div style="font-size:9px;font-weight:700;letter-spacing:.08em;
              text-transform:uppercase;color:{T['text_ter']};margin-bottom:3px;">
    {s['label']}</div>
  <div style="font-size:15px;font-weight:600;color:{T['navy']};
              letter-spacing:-.02em;">{s['value']}</div>
</div>"""
    html = f"""{BASE}
<div style="background:{T['bg_surface']};border:1px solid {T['border']};
     border-radius:8px;display:flex;align-items:center;
     padding:10px 0;margin-bottom:2px;">{items}</div>"""
    components.html(html, height=62, scrolling=False)


# ─────────────────────────────────────────────
# INSIGHT CARD
# ─────────────────────────────────────────────
def render_insight_card(title, items, icon="◈"):
    rows = "".join(
        f'<div style="display:flex;gap:8px;margin-bottom:6px;">'
        f'<span style="color:{T["action"]};font-size:11px;flex-shrink:0;margin-top:1px;">›</span>'
        f'<span style="font-size:12px;color:{T["text_sec"]};line-height:1.5;">{item}</span>'
        f'</div>' for item in items
    )
    html = f"""{BASE}
<div style="background:{T['bg_surface']};border:1px solid {T['border']};
     border-radius:8px;padding:14px 16px;">
  <div style="display:flex;align-items:center;gap:6px;margin-bottom:10px;">
    <span style="font-size:14px;color:{T['navy']};">{icon}</span>
    <span style="font-size:11px;font-weight:600;color:{T['text_pri']};">{title}</span>
  </div>
  {rows}
</div>"""
    components.html(html, height=len(items)*30+56, scrolling=False)


# ─────────────────────────────────────────────
# DIVIDER
# ─────────────────────────────────────────────
def render_divider():
    components.html(
        f'<hr style="border:none;border-top:1px solid {T["border"]};margin:4px 0;">',
        height=2, scrolling=False
    )


# ─────────────────────────────────────────────
# BADGE HTML (inline)
# ─────────────────────────────────────────────
def badge_html(text, level="info"):
    cfg = {
        "success": (T["green_bg"],  T["green"],  T["green_bdr"]),
        "warning": (T["amber_bg"],  T["amber"],  T["amber_bdr"]),
        "danger":  (T["red_bg"],    T["red"],    T["red_bdr"]),
        "info":    (T["action_lt"], T["action"], "#BFDBFE"),
        "brand":   (T["navy_lt"],   T["navy"],   T["navy_bdr"]),
        "neutral": (T["bg_elevated"],T["text_sec"],T["border"]),
    }
    bg, clr, bdr = cfg.get(level, cfg["info"])
    return (f'<span style="display:inline-flex;align-items:center;'
            f'padding:2px 8px;border-radius:4px;'
            f'font-size:9px;font-weight:600;letter-spacing:.05em;'
            f'text-transform:uppercase;'
            f'background:{bg};color:{clr};border:1px solid {bdr};">'
            f'{text}</span>')


# ─────────────────────────────────────────────
# YARDIMCI
# ─────────────────────────────────────────────
def fmt(v):
    try:
        v = float(v)
        if abs(v) >= 1_000_000_000: return f"{v/1_000_000_000:.1f}Mn ₺"
        if abs(v) >= 1_000_000:     return f"{v/1_000_000:.1f}M ₺"
        if abs(v) >= 1_000:         return f"{v/1_000:.0f}K ₺"
        return f"{v:,.0f} ₺"
    except:
        return str(v)

def score_color(kategori):
    return {
        "Mükemmel": T["green"],
        "İyi":      T["action"],
        "Orta":     T["amber"],
        "Zayıf":    "#F97316",
        "Kritik":   T["red"],
    }.get(kategori, T["text_sec"])

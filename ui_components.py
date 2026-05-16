"""
KazKaz AI — Premium UI Components v3
======================================
Bloomberg Terminal + Notion + Linear ilhamıyla.

Prensipler:
  1. Koyu lacivert sidebar — güven ve otorite
  2. 30 saniyede durum okunabilir olmalı
  3. Renk anlam taşır — dekoratif kullanım yok
  4. Sayılar baskın (26px+), etiketler minimal (9px uppercase)
  5. Her sayfada Yönetici Özeti bloğu
  6. Sol aksan çizgisi her KPI kartında
  7. Grafiklerde max 3 renk

Kullanım:
  from ui_components import (
      render_topbar, render_page_header, render_exec_summary,
      render_kpi_row, render_section, render_alerts,
      render_health_bars, render_stat_strip, render_insight_card,
      render_metric_delta, render_divider, badge_html, fmt, T,
  )
"""

import streamlit.components.v1 as components

# ─────────────────────────────────────────────
# DESIGN TOKENS v3 — Premium Navy/Corporate
# ─────────────────────────────────────────────
T = {
    # Arka planlar
    "bg_page":     "#F4F6FB",
    "bg_surface":  "#FFFFFF",
    "bg_elevated": "#F3F5F9",
    "bg_hover":    "#F8F9FC",

    # Kenarlıklar
    "border":      "#E2E5EB",
    "border_str":  "#CDD0D8",
    "border_focus":"#0F2252",

    # Metinler
    "text_pri":    "#0F1729",
    "text_sec":    "#3D4663",
    "text_ter":    "#8B93A8",
    "text_dis":    "#C8CCDA",

    # Marka — lacivert
    "navy":        "#0F2252",
    "navy_mid":    "#1B3A6B",
    "navy_lt":     "#EEF2FF",
    "navy_bdr":    "#C7D2FE",
    "navy_deep":   "#080F2E",

    # Aksiyon mavi
    "action":      "#2563EB",
    "action_lt":   "#DBEAFE",
    "action_bdr":  "#93C5FD",

    # Durum renkleri
    "green":       "#059669",
    "green_bg":    "#ECFDF5",
    "green_bdr":   "#6EE7B7",

    "amber":       "#D97706",
    "amber_bg":    "#FFFBEB",
    "amber_bdr":   "#FCD34D",

    "red":         "#DC2626",
    "red_bg":      "#FEF2F2",
    "red_bdr":     "#FCA5A5",

    "purple":      "#7C3AED",
    "purple_bg":   "#F5F3FF",
    "purple_bdr":  "#C4B5FD",

    # Font
    "font": "-apple-system,'Segoe UI','Helvetica Neue',Arial,sans-serif",
}

BASE = f"""<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:{T['font']};background:transparent;
     color:{T['text_pri']};-webkit-font-smoothing:antialiased;
     -moz-osx-font-smoothing:grayscale}}
</style>"""


# ─────────────────────────────────────────────
# 1. TOPBAR — Premium üst bar
# ─────────────────────────────────────────────
def render_topbar(
    sirket_adi="Şirket",
    donem="2024",
    aktif_period="12A",
    saglik_badge="İyi",
    saglik_level="success",
):
    periods = ["Q1", "Q2", "YTD", "12A", "Tümü"]
    p_html = ""
    for p in periods:
        if p == aktif_period:
            s = (f"background:{T['bg_surface']};color:{T['navy']};"
                 f"font-weight:600;box-shadow:0 0 0 0.5px {T['border']};")
        else:
            s = f"color:{T['text_ter']};"
        p_html += (
            f'<div style="font-size:10px;padding:3px 9px;'
            f'border-radius:5px;cursor:pointer;{s}">{p}</div>'
        )

    lvl = {
        "success": (T["green_bg"],  T["green"],  T["green_bdr"]),
        "warning": (T["amber_bg"],  T["amber"],  T["amber_bdr"]),
        "danger":  (T["red_bg"],    T["red"],    T["red_bdr"]),
    }.get(saglik_level, (T["navy_lt"], T["navy"], T["navy_bdr"]))

    html = f"""{BASE}
<div style="height:48px;background:{T['bg_surface']};
     border-bottom:1px solid {T['border']};
     display:flex;align-items:center;
     padding:0 24px;justify-content:space-between;
     box-shadow:0 1px 3px rgba(15,34,82,.04);">

  <div style="display:flex;align-items:center;gap:6px;">
    <div style="width:22px;height:22px;background:{T['navy']};border-radius:5px;
                display:flex;align-items:center;justify-content:center;
                font-size:10px;font-weight:700;color:#fff;flex-shrink:0;">K</div>
    <span style="font-size:11px;color:{T['text_ter']};">KazKaz AI</span>
    <span style="color:{T['border_str']};font-size:13px;">›</span>
    <span style="font-size:12px;font-weight:600;color:{T['text_pri']};">{sirket_adi}</span>
  </div>

  <div style="display:flex;align-items:center;gap:10px;">
    <div style="display:flex;gap:2px;background:{T['bg_elevated']};
               padding:3px;border-radius:7px;">{p_html}</div>
    <div style="width:1px;height:20px;background:{T['border']};"></div>
    <div style="font-size:9px;font-weight:700;letter-spacing:.06em;
                text-transform:uppercase;padding:4px 10px;border-radius:5px;
                background:{lvl[0]};color:{lvl[1]};border:1px solid {lvl[2]};">
      {saglik_badge}
    </div>
    <span style="font-size:11px;color:{T['text_ter']};">{donem}</span>
  </div>
</div>"""
    components.html(html, height=49, scrolling=False)


# ─────────────────────────────────────────────
# 2. PAGE HEADER — Sayfa başlığı
# ─────────────────────────────────────────────
def render_page_header(title, subtitle="", badge_text="", badge_level="brand"):
    lvl = {
        "success": (T["green_bg"],  T["green"],  T["green_bdr"]),
        "warning": (T["amber_bg"],  T["amber"],  T["amber_bdr"]),
        "danger":  (T["red_bg"],    T["red"],    T["red_bdr"]),
        "info":    (T["action_lt"], T["action"], T["action_bdr"]),
        "brand":   (T["navy_lt"],   T["navy"],   T["navy_bdr"]),
        "purple":  (T["purple_bg"], T["purple"], T["purple_bdr"]),
    }.get(badge_level, (T["navy_lt"], T["navy"], T["navy_bdr"]))

    badge = (
        f'<span style="font-size:9px;font-weight:700;letter-spacing:.06em;'
        f'text-transform:uppercase;padding:3px 9px;border-radius:4px;'
        f'background:{lvl[0]};color:{lvl[1]};border:1px solid {lvl[2]};">'
        f'{badge_text}</span>'
    ) if badge_text else ""

    html = f"""{BASE}
<div style="padding:6px 0 20px;border-bottom:1px solid {T['border']};margin-bottom:20px;">
  <div style="font-size:20px;font-weight:700;color:{T['navy']};
              letter-spacing:-.025em;margin-bottom:6px;
              font-family:{T['font']};">{title}</div>
  <div style="display:flex;align-items:center;gap:8px;">
    <span style="font-size:12px;color:{T['text_ter']};">{subtitle}</span>
    {badge}
  </div>
</div>"""
    components.html(html, height=78, scrolling=False)


# ─────────────────────────────────────────────
# 3. EXECUTIVE SUMMARY — Yönetici özeti bloğu
# Her sayfanın tepesinde olmalı
# ─────────────────────────────────────────────
def render_exec_summary(text, title="Yönetici Değerlendirmesi"):
    html = f"""{BASE}
<div style="background:{T['bg_surface']};
     border:1px solid {T['border']};
     border-left:3px solid {T['navy']};
     border-radius:0 10px 10px 0;
     padding:14px 18px;margin-bottom:18px;
     box-shadow:0 1px 4px rgba(15,34,82,.05);">
  <div style="display:flex;align-items:center;gap:6px;margin-bottom:7px;">
    <div style="width:4px;height:4px;border-radius:50%;background:{T['navy']};"></div>
    <div style="font-size:8px;font-weight:800;letter-spacing:.15em;
                text-transform:uppercase;color:{T['navy']};">{title}</div>
  </div>
  <div style="font-size:13px;color:{T['text_sec']};line-height:1.7;
              font-family:{T['font']};">{text}</div>
</div>"""
    components.html(html, height=90, scrolling=False)


# ─────────────────────────────────────────────
# 4. KPI ROW — Ana metrik kartları
# Sol aksan çizgisi + büyük sayı
# ─────────────────────────────────────────────
def render_kpi_row(kpis, height=115):
    cards = ""
    for k in kpis:
        label    = k.get("label", "")
        value    = k.get("value", "—")
        delta    = k.get("delta", "")
        positive = k.get("positive", True)
        color    = k.get("color", T["text_pri"])
        acc      = k.get("accent_color", T["green"] if positive else T["red"])

        if delta:
            d_bg  = T["green_bg"]  if positive else T["red_bg"]
            d_clr = T["green"]     if positive else T["red"]
            d_bdr = T["green_bdr"] if positive else T["red_bdr"]
            sign  = "+" if positive else "−"
            dh = (
                f'<div style="display:inline-flex;align-items:center;'
                f'font-size:10px;font-weight:600;padding:3px 7px;'
                f'border-radius:4px;margin-top:7px;'
                f'background:{d_bg};color:{d_clr};border:1px solid {d_bdr};">'
                f'{sign} {delta}</div>'
            )
        else:
            dh = ""

        cards += f"""
<div style="background:{T['bg_surface']};
     border:1px solid {T['border']};
     border-radius:10px;
     padding:16px 18px 14px 20px;
     position:relative;overflow:hidden;flex:1;min-width:0;
     box-shadow:0 1px 3px rgba(15,34,82,.04);">
  <div style="position:absolute;left:0;top:12px;bottom:12px;
              width:3px;background:{acc};border-radius:0 2px 2px 0;"></div>
  <div style="font-size:9px;font-weight:700;letter-spacing:.12em;
              text-transform:uppercase;color:{T['text_ter']};
              margin-bottom:8px;">{label}</div>
  <div style="font-size:26px;font-weight:700;letter-spacing:-.04em;
              line-height:1;color:{color};
              font-family:{T['font']};">{value}</div>
  {dh}
</div>"""

    html = f"""{BASE}
<div style="display:flex;gap:10px;margin-bottom:4px;">{cards}</div>"""
    components.html(html, height=height, scrolling=False)


# ─────────────────────────────────────────────
# 5. KPI ROW — 2 satır (8 kart için)
# ─────────────────────────────────────────────
def render_kpi_grid(kpis, cols=4, height=240):
    """4'ten fazla KPI için 2 satırlık grid."""
    rows_html = ""
    for i in range(0, len(kpis), cols):
        chunk = kpis[i:i+cols]
        cards = ""
        for k in chunk:
            label    = k.get("label", "")
            value    = k.get("value", "—")
            delta    = k.get("delta", "")
            positive = k.get("positive", True)
            color    = k.get("color", T["text_pri"])
            acc      = k.get("accent_color", T["green"] if positive else T["red"])
            if delta:
                d_bg  = T["green_bg"]  if positive else T["red_bg"]
                d_clr = T["green"]     if positive else T["red"]
                d_bdr = T["green_bdr"] if positive else T["red_bdr"]
                sign  = "+" if positive else "−"
                dh = (
                    f'<div style="display:inline-flex;align-items:center;'
                    f'font-size:9px;font-weight:600;padding:2px 6px;'
                    f'border-radius:3px;margin-top:5px;'
                    f'background:{d_bg};color:{d_clr};border:1px solid {d_bdr};">'
                    f'{sign} {delta}</div>'
                )
            else:
                dh = ""
            cards += f"""
<div style="background:{T['bg_surface']};border:1px solid {T['border']};
     border-radius:10px;padding:14px 16px 12px 18px;
     position:relative;overflow:hidden;flex:1;min-width:0;">
  <div style="position:absolute;left:0;top:10px;bottom:10px;
              width:3px;background:{acc};border-radius:0 2px 2px 0;"></div>
  <div style="font-size:9px;font-weight:700;letter-spacing:.12em;
              text-transform:uppercase;color:{T['text_ter']};margin-bottom:6px;">{label}</div>
  <div style="font-size:22px;font-weight:700;letter-spacing:-.04em;
              line-height:1;color:{color};">{value}</div>
  {dh}
</div>"""
        rows_html += f'<div style="display:flex;gap:10px;margin-bottom:10px;">{cards}</div>'

    html = f"{BASE}<div>{rows_html}</div>"
    components.html(html, height=height, scrolling=False)


# ─────────────────────────────────────────────
# 6. SECTION HEADER
# ─────────────────────────────────────────────
def render_section(title, top_margin=24, icon=""):
    icon_html = (
        f'<span style="font-size:12px;margin-right:5px;opacity:.7;">{icon}</span>'
    ) if icon else ""

    html = f"""{BASE}
<div style="display:flex;align-items:center;gap:8px;
     padding-bottom:9px;border-bottom:1px solid {T['border']};
     margin-top:{top_margin}px;margin-bottom:4px;">
  {icon_html}
  <span style="font-size:9px;font-weight:800;letter-spacing:.13em;
        text-transform:uppercase;color:{T['text_ter']};">{title}</span>
</div>"""
    components.html(html, height=30 + top_margin, scrolling=False)


# ─────────────────────────────────────────────
# 7. ALERTS — Durum uyarı kartları
# ─────────────────────────────────────────────
def render_alerts(alerts):
    lvl_cfg = {
        "warning": (T["amber_bg"],  T["amber"],  T["amber_bdr"]),
        "info":    (T["navy_lt"],   T["navy"],   T["navy_bdr"]),
        "success": (T["green_bg"],  T["green"],  T["green_bdr"]),
        "danger":  (T["red_bg"],    T["red"],    T["red_bdr"]),
        "purple":  (T["purple_bg"], T["purple"], T["purple_bdr"]),
    }
    rows = ""
    for a in alerts:
        bg, clr, bdr = lvl_cfg.get(a.get("level", "info"), lvl_cfg["info"])
        rows += f"""
<div style="background:{bg};border:1px solid {bdr};
     border-left:3px solid {clr};border-radius:0 8px 8px 0;
     padding:11px 15px;margin-bottom:7px;">
  <div style="font-size:12px;font-weight:700;color:{T['text_pri']};margin-bottom:3px;">
    {a.get('title','')}</div>
  <div style="font-size:12px;color:{T['text_sec']};line-height:1.55;">
    {a.get('body','')}</div>
</div>"""
    html = f"{BASE}<div>{rows}</div>"
    components.html(html, height=len(alerts) * 74 + 8, scrolling=False)


# ─────────────────────────────────────────────
# 8. HEALTH BARS — Sağlık göstergesi
# ─────────────────────────────────────────────
def render_health_bars(scores):
    rows = ""
    for label, val in scores.items():
        val = min(int(val or 0), 100)
        if val >= 70:
            clr, bg = T["green"], T["green_bg"]
        elif val >= 40:
            clr, bg = T["amber"], T["amber_bg"]
        else:
            clr, bg = T["red"], T["red_bg"]

        rows += f"""
<div style="margin-bottom:14px;">
  <div style="display:flex;justify-content:space-between;
              align-items:center;margin-bottom:6px;">
    <span style="font-size:12px;font-weight:500;color:{T['text_sec']};">{label}</span>
    <span style="font-size:12px;font-weight:700;color:{clr};
                 background:{bg};padding:1px 7px;border-radius:4px;">{val}</span>
  </div>
  <div style="background:{T['bg_elevated']};border-radius:3px;height:6px;overflow:hidden;">
    <div style="background:{clr};width:{val}%;height:100%;
                border-radius:3px;transition:width .4s;"></div>
  </div>
</div>"""
    html = f"{BASE}<div style='padding:4px 0;'>{rows}</div>"
    components.html(html, height=len(scores) * 48 + 16, scrolling=False)


# ─────────────────────────────────────────────
# 9. STAT STRIP — Yatay özet şerit
# ─────────────────────────────────────────────
def render_stat_strip(stats):
    items = ""
    for i, s in enumerate(stats):
        sep = (
            f'<div style="width:1px;background:{T["border"]};height:32px;'
            f'flex-shrink:0;"></div>'
        ) if i else ""
        items += f"""{sep}
<div style="padding:0 18px;text-align:center;flex:1;min-width:0;">
  <div style="font-size:9px;font-weight:700;letter-spacing:.1em;
              text-transform:uppercase;color:{T['text_ter']};margin-bottom:4px;">
    {s['label']}</div>
  <div style="font-size:16px;font-weight:700;color:{T['navy']};
              letter-spacing:-.02em;">{s['value']}</div>
</div>"""

    html = f"""{BASE}
<div style="background:{T['bg_surface']};border:1px solid {T['border']};
     border-radius:10px;display:flex;align-items:center;
     padding:12px 0;margin-bottom:4px;
     box-shadow:0 1px 3px rgba(15,34,82,.04);">{items}</div>"""
    components.html(html, height=68, scrolling=False)


# ─────────────────────────────────────────────
# 10. INSIGHT CARD — İçgörü/öneri kartı
# ─────────────────────────────────────────────
def render_insight_card(title, items, icon="◈", level="brand"):
    lvl = {
        "brand":   (T["navy_lt"],   T["navy"],   T["navy_bdr"]),
        "success": (T["green_bg"],  T["green"],  T["green_bdr"]),
        "warning": (T["amber_bg"],  T["amber"],  T["amber_bdr"]),
        "danger":  (T["red_bg"],    T["red"],    T["red_bdr"]),
    }.get(level, (T["navy_lt"], T["navy"], T["navy_bdr"]))

    rows = "".join(
        f'<div style="display:flex;gap:8px;margin-bottom:8px;">'
        f'<span style="color:{lvl[1]};font-size:12px;flex-shrink:0;margin-top:1px;">›</span>'
        f'<span style="font-size:12px;color:{T["text_sec"]};line-height:1.6;">{item}</span>'
        f'</div>'
        for item in items
    )

    html = f"""{BASE}
<div style="background:{lvl[0]};border:1px solid {lvl[2]};
     border-radius:10px;padding:14px 16px;">
  <div style="display:flex;align-items:center;gap:7px;margin-bottom:11px;">
    <div style="width:24px;height:24px;background:{lvl[1]};border-radius:6px;
                display:flex;align-items:center;justify-content:center;
                font-size:11px;color:#fff;flex-shrink:0;">{icon}</div>
    <span style="font-size:12px;font-weight:700;color:{T['text_pri']};">{title}</span>
  </div>
  {rows}
</div>"""
    components.html(html, height=len(items) * 34 + 66, scrolling=False)


# ─────────────────────────────────────────────
# 11. METRIC DELTA — Satır içi delta göstergesi
# ─────────────────────────────────────────────
def render_metric_delta(label, value, delta, prev_value="", positive=True):
    acc = T["green"] if positive else T["red"]
    acc_bg = T["green_bg"] if positive else T["red_bg"]
    acc_bdr = T["green_bdr"] if positive else T["red_bdr"]
    arrow = "▲" if positive else "▼"

    prev_html = (
        f'<span style="font-size:11px;color:{T["text_ter"]};margin-left:8px;">'
        f'önceki: {prev_value}</span>'
    ) if prev_value else ""

    html = f"""{BASE}
<div style="background:{T['bg_surface']};border:1px solid {T['border']};
     border-radius:10px;padding:14px 18px;margin-bottom:8px;
     display:flex;align-items:center;justify-content:space-between;">
  <div>
    <div style="font-size:9px;font-weight:700;letter-spacing:.12em;
                text-transform:uppercase;color:{T['text_ter']};margin-bottom:6px;">
      {label}</div>
    <div style="font-size:24px;font-weight:700;color:{T['text_pri']};
                letter-spacing:-.03em;">{value}</div>
    {prev_html}
  </div>
  <div style="background:{acc_bg};border:1px solid {acc_bdr};
              border-radius:8px;padding:8px 14px;text-align:center;">
    <div style="font-size:9px;color:{acc};margin-bottom:3px;">{arrow}</div>
    <div style="font-size:16px;font-weight:700;color:{acc};">{delta}</div>
  </div>
</div>"""
    components.html(html, height=90, scrolling=False)


# ─────────────────────────────────────────────
# 12. CFO ACTION CARD — Aksiyon önerisi
# ─────────────────────────────────────────────
def render_action_card(title, actions):
    """
    actions: [{"text": "...", "priority": "acil|bu_ay|ceyrek", "impact": "..."}]
    """
    priority_cfg = {
        "acil":   (T["red"],    T["red_bg"],    T["red_bdr"],    "Acil"),
        "bu_ay":  (T["amber"],  T["amber_bg"],  T["amber_bdr"],  "Bu Ay"),
        "ceyrek": (T["navy"],   T["navy_lt"],   T["navy_bdr"],   "Çeyrek"),
    }
    rows = ""
    for a in actions:
        pr = a.get("priority", "bu_ay")
        clr, bg, bdr, pr_label = priority_cfg.get(pr, priority_cfg["bu_ay"])
        impact = a.get("impact", "")
        impact_html = (
            f'<span style="font-size:11px;color:{T["green"]};'
            f'font-weight:600;margin-left:8px;">→ {impact}</span>'
        ) if impact else ""
        rows += f"""
<div style="display:flex;align-items:flex-start;gap:10px;
            padding:10px 0;border-bottom:1px solid {T['bg_elevated']};">
  <div style="background:{bg};color:{clr};border:1px solid {bdr};
              font-size:8px;font-weight:800;letter-spacing:.06em;
              padding:2px 7px;border-radius:4px;flex-shrink:0;margin-top:2px;">
    {pr_label}</div>
  <div>
    <span style="font-size:12px;color:{T['text_sec']};line-height:1.5;">
      {a.get('text','')}</span>
    {impact_html}
  </div>
</div>"""

    html = f"""{BASE}
<div style="background:{T['bg_surface']};border:1px solid {T['border']};
     border-radius:10px;padding:14px 16px;
     box-shadow:0 1px 3px rgba(15,34,82,.04);">
  <div style="font-size:11px;font-weight:700;color:{T['navy']};
              margin-bottom:10px;letter-spacing:-.01em;">{title}</div>
  {rows}
</div>"""
    components.html(html, height=len(actions) * 55 + 50, scrolling=False)


# ─────────────────────────────────────────────
# 13. SCORE RING — Daire sağlık skoru
# ─────────────────────────────────────────────
def render_score_ring(skor, kategori, size=120):
    if skor >= 75:
        clr = T["green"]
    elif skor >= 50:
        clr = T["action"]
    elif skor >= 30:
        clr = T["amber"]
    else:
        clr = T["red"]

    radius = 42
    circumference = 2 * 3.14159 * radius
    offset = circumference * (1 - skor / 100)

    html = f"""{BASE}
<div style="display:flex;flex-direction:column;align-items:center;padding:8px 0;">
  <svg width="{size}" height="{size}" viewBox="0 0 100 100">
    <circle cx="50" cy="50" r="{radius}"
      fill="none" stroke="{T['bg_elevated']}" stroke-width="8"/>
    <circle cx="50" cy="50" r="{radius}"
      fill="none" stroke="{clr}" stroke-width="8"
      stroke-dasharray="{circumference:.1f}"
      stroke-dashoffset="{offset:.1f}"
      stroke-linecap="round"
      transform="rotate(-90 50 50)"/>
    <text x="50" y="46" text-anchor="middle"
      font-size="20" font-weight="700" fill="{clr}"
      font-family="{T['font']}">{skor}</text>
    <text x="50" y="60" text-anchor="middle"
      font-size="8" fill="{T['text_ter']}"
      font-family="{T['font']}">/ 100</text>
  </svg>
  <div style="font-size:12px;font-weight:700;color:{clr};margin-top:4px;">{kategori}</div>
</div>"""
    components.html(html, height=size + 36, scrolling=False)


# ─────────────────────────────────────────────
# 14. DIVIDER
# ─────────────────────────────────────────────
def render_divider():
    components.html(
        f'<hr style="border:none;border-top:1px solid {T["border"]};margin:2px 0;">',
        height=2, scrolling=False
    )


# ─────────────────────────────────────────────
# 15. BADGE HTML (inline string)
# ─────────────────────────────────────────────
def badge_html(text, level="info"):
    cfg = {
        "success": (T["green_bg"],  T["green"],  T["green_bdr"]),
        "warning": (T["amber_bg"],  T["amber"],  T["amber_bdr"]),
        "danger":  (T["red_bg"],    T["red"],    T["red_bdr"]),
        "info":    (T["action_lt"], T["action"], T["action_bdr"]),
        "brand":   (T["navy_lt"],   T["navy"],   T["navy_bdr"]),
        "neutral": (T["bg_elevated"], T["text_sec"], T["border"]),
        "purple":  (T["purple_bg"], T["purple"], T["purple_bdr"]),
    }
    bg, clr, bdr = cfg.get(level, cfg["info"])
    return (
        f'<span style="display:inline-flex;align-items:center;'
        f'padding:2px 8px;border-radius:4px;'
        f'font-size:9px;font-weight:700;letter-spacing:.06em;'
        f'text-transform:uppercase;'
        f'background:{bg};color:{clr};border:1px solid {bdr};">'
        f'{text}</span>'
    )


# ─────────────────────────────────────────────
# 16. YARDIMCILAR
# ─────────────────────────────────────────────
def fmt(v):
    try:
        v = float(v)
        if abs(v) >= 1_000_000_000: return f"{v/1_000_000_000:.1f}Mn ₺"
        if abs(v) >= 1_000_000:     return f"{v/1_000_000:.1f}M ₺"
        if abs(v) >= 1_000:         return f"{v/1_000:.0f}K ₺"
        return f"{v:,.0f} ₺"
    except Exception:
        return str(v)


def score_color(kategori):
    return {
        "Mükemmel": T["green"],
        "İyi":      T["action"],
        "Orta":     T["amber"],
        "Zayıf":    "#F97316",
        "Kritik":   T["red"],
    }.get(kategori, T["text_sec"])

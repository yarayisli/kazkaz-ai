"""
KazKaz AI - Yatırım Analizi PDF Rapor Eklentisi
================================================
pdf_report.py'deki PDFReportGenerator'a yatırım
analizi bölümü ekler.

Kullanım:
    from investment_pdf import add_investment_section
    # pdf_report.py içindeki generate() metoduna:
    story += add_investment_section(inv_rapor, mc_sonuc, S)
"""

from typing import Dict, Any, Optional, List

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart


# Renk sabitleri
C_ACCENT1  = colors.HexColor("#0066ff")
C_GREEN    = colors.HexColor("#10d994")
C_RED      = colors.HexColor("#ff4757")
C_YELLOW   = colors.HexColor("#fbbf24")
C_DARK_HDR = colors.HexColor("#0a1628")
C_BORDER   = colors.HexColor("#1e3a5f")
C_SUBTEXT  = colors.HexColor("#8899bb")
C_WHITE    = colors.white


def _fmt(v: float) -> str:
    if abs(v) >= 1_000_000: return f"{v/1_000_000:.2f}M TL"
    if abs(v) >= 1_000:     return f"{v/1_000:.1f}K TL"
    return f"{v:,.0f} TL"


def _pct(v: float) -> str:
    return f"%{v:.1f}"


def _val_color(v) -> colors.Color:
    if isinstance(v, (int, float)):
        return C_GREEN if v >= 0 else C_RED
    return colors.HexColor("#2a3a5a")


def add_investment_section(
    inv_rapor:  Dict[str, Any],
    mc_sonuc:   Optional[Dict[str, Any]],
    S:          Dict,
    bolum_no:   int = 9,
) -> List:
    """
    Yatırım analizi bölümünü PDF story listesi olarak döndürür.
    pdf_report.py generate() içinde story += add_investment_section(...) ile eklenir.
    """
    story = []
    ozet  = inv_rapor["ozet"]
    skor  = inv_rapor["skor"]
    kdf   = inv_rapor["kumulatif_df"]

    # ── Bölüm Başlığı ──
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"{bolum_no}. YATIRIM ANALİZİ", S["section"]))
    story.append(HRFlowable(width="100%", thickness=1.5, color=C_ACCENT1,
                             spaceAfter=8, spaceBefore=0))

    # ── Özet KPI tablosu ──
    cw = (A4[0] - 3*cm) / 4
    kpi_data = [
        [_label("YATIRIM ADI",  S), _label("MALİYET",  S),
         _label("ROI",          S), _label("NPV",       S)],
        [_val(ozet["ad"], S),
         _val(_fmt(ozet["maliyet"]), S),
         _val(_pct(ozet["roi"]),  S, C_GREEN if ozet["roi"]>0 else C_RED),
         _val(_fmt(ozet["npv"]),  S, C_GREEN if ozet["npv"]>0 else C_RED)],
        [_label("IRR",         S), _label("PI",          S),
         _label("GERİ ÖDEME",  S), _label("SKOR",        S)],
        [_val(f'%{ozet["irr"]}' if ozet["irr"] else "-", S,
              C_GREEN if (ozet.get("irr") or 0)>ozet["iskonto_orani"]*100 else C_RED),
         _val(str(ozet["pi"]),  S, C_GREEN if ozet["pi"]>1 else C_RED),
         _val(f'{ozet["payback_basit"]:.1f} Yıl' if ozet.get("payback_basit") else "-", S),
         _val(f'{skor["skor"]}/100', S,
              _score_col(skor["kategori"]))],
    ]
    t = Table(kpi_data, colWidths=[cw]*4)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#f0f4ff")),
        ("BACKGROUND",    (0,0), (-1, 0), colors.HexColor("#e0e8f8")),
        ("BACKGROUND",    (0,2), (-1, 2), colors.HexColor("#e0e8f8")),
        ("BOX",           (0,0), (-1,-1), 0.5, C_BORDER),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, C_BORDER),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.3*cm))

    # ── Tavsiye kutusu ──
    tavsiye_data = [[Paragraph(
        f"<b>Kategori:</b> {skor['kategori']}  —  {skor['tavsiye']}",
        ParagraphStyle("tv", fontName="KazFont", fontSize=9, leading=14,
                       textColor=colors.HexColor("#1a3060"),
                       leftIndent=8, rightIndent=8)
    )]]
    tv_t = Table(tavsiye_data, colWidths=[A4[0]-3*cm])
    tv_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), colors.HexColor("#eef4ff")),
        ("BOX",           (0,0),(-1,-1), 1, C_ACCENT1),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 12),
        ("RIGHTPADDING",  (0,0),(-1,-1), 12),
    ]))
    story.append(tv_t)
    story.append(Spacer(1, 0.3*cm))

    # ── Kümülatif nakit akışı bar chart ──
    story.append(Paragraph("Kümülatif Nakit Akışı", S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#dde8f8"), spaceAfter=6))

    d = Drawing(16*cm, 5.5*cm)
    chart = VerticalBarChart()
    chart.x, chart.y = 50, 30
    chart.width  = 16*cm - 70
    chart.height = 5.5*cm - 50
    chart.data   = [list(kdf["Kümülatif"])]
    chart.categoryAxis.categoryNames = [f"Yıl {y}" for y in kdf["Yıl"]]
    chart.categoryAxis.labels.angle  = 0
    chart.categoryAxis.labels.fontSize = 7
    chart.categoryAxis.labels.fontName = "KazFont"
    chart.valueAxis.labels.fontSize    = 7
    chart.valueAxis.labels.fontName    = "KazFont"
    chart.valueAxis.labelTextFormat    = lambda v: _fmt(v)
    for i, v in enumerate(kdf["Kümülatif"]):
        chart.bars[(0,i)].fillColor = C_GREEN if v >= 0 else C_RED
    chart.bars[0].strokeColor = colors.transparent
    d.add(chart)
    story.append(d)
    story.append(Spacer(1, 0.3*cm))

    # ── Yıllık tablo ──
    story.append(Paragraph("Yıllık Nakit Akışı Tablosu", S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=colors.HexColor("#dde8f8"), spaceAfter=6))

    table_data = [[
        Paragraph("Yıl",             S["table_header"]),
        Paragraph("Nakit Akışı",     S["table_header"]),
        Paragraph("PV Nakit Akışı",  S["table_header"]),
        Paragraph("Kümülatif",       S["table_header"]),
        Paragraph("Durum",           S["table_header"]),
    ]]
    for _, row in kdf.iterrows():
        kum_col = C_GREEN if row["Kümülatif"] >= 0 else C_RED
        table_data.append([
            Paragraph(str(int(row["Yıl"])),            S["table_cell"]),
            Paragraph(_fmt(row["Nakit Akışı"]),         S["table_cell"]),
            Paragraph(_fmt(row["PV Nakit Akışı"]),
                ParagraphStyle("pvc", parent=S["table_cell"], textColor=C_ACCENT1)),
            Paragraph(_fmt(row["Kümülatif"]),
                ParagraphStyle("kc", parent=S["table_cell"], textColor=kum_col)),
            Paragraph(str(row["Geri Ödendi"]),
                ParagraphStyle("gc", parent=S["table_cell"],
                               textColor=C_GREEN if "✅" in str(row["Geri Ödendi"]) else C_RED)),
        ])

    cw5 = (A4[0]-3*cm)/5
    t2 = Table(table_data, colWidths=[cw5]*5, repeatRows=1)
    t2.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1, 0), C_DARK_HDR),
        ("TEXTCOLOR",     (0,0),(-1, 0), C_WHITE),
        ("BOX",           (0,0),(-1,-1), 0.5, C_BORDER),
        ("INNERGRID",     (0,0),(-1,-1), 0.3, colors.HexColor("#dde8f8")),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f4f7fd")]),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
    ]))
    story.append(t2)

    # ── Monte Carlo özeti (varsa) ──
    if mc_sonuc:
        story.append(Spacer(1, 0.4*cm))
        story.append(Paragraph("Monte Carlo Risk Özeti", S["section"]))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                 color=colors.HexColor("#dde8f8"), spaceAfter=6))

        risk_col = {
            "Düşük Risk": C_GREEN, "Orta Risk": colors.HexColor("#fbbf24"),
            "Yüksek Risk": colors.HexColor("#f97316"), "Çok Yüksek Risk": C_RED,
        }.get(mc_sonuc["risk_seviyesi"], C_SUBTEXT)

        mc_kpi = [
            [_label("RİSK SEVİYESİ", S), _label("POZİTİF NPV ORANI", S),
             _label("ORT. NPV",      S), _label("NPV P10 / P90",      S)],
            [_val(mc_sonuc["risk_seviyesi"], S, risk_col),
             _val(_pct(mc_sonuc["npv_pozitif_oran"]), S,
                  C_GREEN if mc_sonuc["npv_pozitif_oran"]>65 else C_RED),
             _val(_fmt(mc_sonuc["npv_ortalama"]), S,
                  C_GREEN if mc_sonuc["npv_ortalama"]>0 else C_RED),
             _val(f'{_fmt(mc_sonuc["npv_p10"])} / {_fmt(mc_sonuc["npv_p90"])}', S)],
        ]
        mc_t = Table(mc_kpi, colWidths=[cw]*4)
        mc_t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), colors.HexColor("#f0f4ff")),
            ("BACKGROUND",    (0,0),(-1, 0), colors.HexColor("#e0e8f8")),
            ("BOX",           (0,0),(-1,-1), 0.5, C_BORDER),
            ("INNERGRID",     (0,0),(-1,-1), 0.3, C_BORDER),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
            ("TOPPADDING",    (0,0),(-1,-1), 5),
            ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ]))
        story.append(mc_t)
        story.append(Paragraph(
            f"* {mc_sonuc['n_sim']:,} simülasyon sonucuna göre NPV'nin "
            f"pozitif olma olasılığı %{mc_sonuc['npv_pozitif_oran']} olarak hesaplanmıştır.",
            ParagraphStyle("mc_note", fontName="KazFont", fontSize=8, leading=12,
                           textColor=colors.HexColor("#6080a0"),
                           spaceBefore=6)
        ))

    story.append(PageBreak())
    return story


# ─────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ─────────────────────────────────────────────

def _label(text: str, S: Dict) -> Paragraph:
    return Paragraph(text, S["kpi_label"])

def _val(text: str, S: Dict,
         col: colors.Color = None) -> Paragraph:
    if col:
        style = ParagraphStyle("dv", parent=S["kpi_value"], textColor=col)
    else:
        style = S["kpi_value"]
    return Paragraph(text, style)

def _score_col(kategori: str) -> colors.Color:
    return {
        "Mükemmel Yatırım": C_GREEN,
        "İyi Yatırım":      colors.HexColor("#0066ff"),
        "Kabul Edilebilir": colors.HexColor("#fbbf24"),
        "Riskli":           colors.HexColor("#f97316"),
        "Önerilmez":        C_RED,
    }.get(kategori, colors.HexColor("#2a3a5a"))

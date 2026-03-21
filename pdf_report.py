"""
KazKaz AI - PDF Rapor Motoru
==============================
Tek tıkla profesyonel finansal rapor üretir.

İçerik:
  - Kapak sayfası
  - Yönetici özeti
  - Gelir analizi tablosu + grafik
  - Gider analizi tablosu + grafik
  - Karlılık analizi
  - Finansal sağlık skoru
  - Senaryo analizi (opsiyonel)
  - Gelecek tahmini (opsiyonel)
  - AI yorumları (opsiyonel)

Kurulum: pip install reportlab
"""

import io
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)
from reportlab.platypus import Image as RLImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF


# ─────────────────────────────────────────────
# FONT KAYIT (Streamlit Cloud uyumlu)
# ─────────────────────────────────────────────

import urllib.request
import tempfile

FONT_REGISTERED = False

def _try_download_font(filename: str) -> Optional[str]:
    """Fontu internetten temp klasörüne indirir."""
    urls = {
        "DejaVuSans.ttf":
            "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf":
            "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans-Bold.ttf",
    }
    url = urls.get(filename)
    if not url:
        return None
    try:
        tmp = os.path.join(tempfile.gettempdir(), filename)
        if not os.path.exists(tmp) or os.path.getsize(tmp) < 1000:
            urllib.request.urlretrieve(url, tmp)
        if os.path.getsize(tmp) > 1000:
            return tmp
    except Exception:
        pass
    return None

def _find_font(filename: str) -> Optional[str]:
    """Fontu sırasıyla çeşitli konumlarda arar."""
    candidates = [
        # Linux sistem
        f"/usr/share/fonts/truetype/dejavu/{filename}",
        # Proje klasörü
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", filename),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), filename),
        # Windows
        os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", filename),
        # macOS
        f"/Library/Fonts/{filename}",
        f"/System/Library/Fonts/{filename}",
    ]
    for path in candidates:
        if os.path.exists(path) and os.path.getsize(path) > 1000:
            return path
    # İnternetten indir
    return _try_download_font(filename)

def register_fonts():
    global FONT_REGISTERED
    reg  = _find_font("DejaVuSans.ttf")
    bold = _find_font("DejaVuSans-Bold.ttf")
    if reg and bold:
        try:
            pdfmetrics.registerFont(TTFont("KazFont",      reg))
            pdfmetrics.registerFont(TTFont("KazFont-Bold", bold))
            FONT_REGISTERED = True
            return
        except Exception:
            pass
    # Fallback: Helvetica (her sistemde mevcut, Türkçe desteği sınırlı)
    FONT_REGISTERED = False

register_fonts()

# Font adları — kayıt başarısızsa Helvetica kullan
def _f(bold=False) -> str:
    if FONT_REGISTERED:
        return "KazFont-Bold" if bold else "KazFont"
    return "Helvetica-Bold" if bold else "Helvetica"


# ─────────────────────────────────────────────
# RENK PALETİ
# ─────────────────────────────────────────────

C_BG       = colors.HexColor("#0a0e1a")
C_CARD     = colors.HexColor("#111827")
C_BORDER   = colors.HexColor("#1e3a5f")
C_ACCENT1  = colors.HexColor("#0066ff")
C_ACCENT2  = colors.HexColor("#00d4ff")
C_GREEN    = colors.HexColor("#10d994")
C_RED      = colors.HexColor("#ff4757")
C_YELLOW   = colors.HexColor("#fbbf24")
C_TEXT     = colors.HexColor("#e8eaf0")
C_SUBTEXT  = colors.HexColor("#8899bb")
C_WHITE    = colors.white
C_LIGHT_BG = colors.HexColor("#f0f4ff")  # Açık tema arka plan
C_DARK_HDR = colors.HexColor("#0a1628")


# ─────────────────────────────────────────────
# STİL TANIMLAMALARI
# ─────────────────────────────────────────────

def make_styles() -> Dict[str, ParagraphStyle]:
    base = dict(fontName=_f(), leading=16, textColor=colors.HexColor("#1a2540"))
    return {
        "title": ParagraphStyle("title",
            fontName=_f(bold=True), fontSize=28, leading=34,
            textColor=C_WHITE, alignment=TA_CENTER, spaceAfter=6),
        "subtitle": ParagraphStyle("subtitle",
            fontName=_f(), fontSize=11, leading=14,
            textColor=colors.HexColor("#7090c0"), alignment=TA_CENTER, spaceAfter=4),
        "section": ParagraphStyle("section",
            fontName=_f(bold=True), fontSize=13, leading=18,
            textColor=C_DARK_HDR, spaceBefore=16, spaceAfter=8,
            borderPad=4),
        "body": ParagraphStyle("body",
            fontName=_f(), fontSize=9.5, leading=15,
            textColor=colors.HexColor("#2a3a5a"), spaceAfter=6),
        "body_small": ParagraphStyle("body_small",
            fontName=_f(), fontSize=8.5, leading=13,
            textColor=colors.HexColor("#4a6fa5")),
        "kpi_label": ParagraphStyle("kpi_label",
            fontName=_f(), fontSize=7.5, leading=10,
            textColor=colors.HexColor("#4a6fa5"), alignment=TA_CENTER),
        "kpi_value": ParagraphStyle("kpi_value",
            fontName=_f(bold=True), fontSize=16, leading=20,
            textColor=C_DARK_HDR, alignment=TA_CENTER),
        "kpi_delta": ParagraphStyle("kpi_delta",
            fontName=_f(), fontSize=8, leading=11,
            textColor=C_GREEN, alignment=TA_CENTER),
        "table_header": ParagraphStyle("table_header",
            fontName=_f(bold=True), fontSize=8.5, leading=12,
            textColor=C_WHITE, alignment=TA_CENTER),
        "table_cell": ParagraphStyle("table_cell",
            fontName=_f(), fontSize=8.5, leading=12,
            textColor=colors.HexColor("#1a2a4a"), alignment=TA_CENTER),
        "ai_text": ParagraphStyle("ai_text",
            fontName=_f(), fontSize=9, leading=15,
            textColor=colors.HexColor("#1a3060"),
            leftIndent=12, rightIndent=12, spaceAfter=6),
        "footer": ParagraphStyle("footer",
            fontName=_f(), fontSize=7.5, leading=10,
            textColor=colors.HexColor("#8899bb"), alignment=TA_CENTER),
        "cover_company": ParagraphStyle("cover_company",
            fontName=_f(bold=True), fontSize=14, leading=18,
            textColor=C_ACCENT2, alignment=TA_CENTER),
        "toc_item": ParagraphStyle("toc_item",
            fontName=_f(), fontSize=10, leading=16,
            textColor=colors.HexColor("#2a3a5a"), leftIndent=20),
    }


# ─────────────────────────────────────────────
# SAYFA ŞABLONU (header/footer)
# ─────────────────────────────────────────────

class KazkazTemplate(SimpleDocTemplate):
    def __init__(self, buffer, sirket_adi="", rapor_tarihi="", **kwargs):
        super().__init__(buffer, **kwargs)
        self.sirket_adi  = sirket_adi
        self.rapor_tarihi = rapor_tarihi

    def handle_pageBegin(self):
        super().handle_pageBegin()

    def afterPage(self):
        pass

    def build(self, flowables, **kwargs):
        self._sirket_adi   = self.sirket_adi
        self._rapor_tarihi = self.rapor_tarihi
        super().build(flowables, onFirstPage=self._first_page,
                      onLaterPages=self._later_pages, **kwargs)

    def _header_footer(self, canvas, doc, is_first=False):
        canvas.saveState()
        w, h = A4

        if not is_first:
            # Üst çizgi
            canvas.setFillColor(C_ACCENT1)
            canvas.rect(0, h - 28, w, 28, fill=1, stroke=0)
            canvas.setFont(_f(bold=True), 10)
            canvas.setFillColor(C_WHITE)
            canvas.drawString(1.5*cm, h - 19, "KazKaz AI")
            canvas.setFont(_f(), 8)
            canvas.drawRightString(w - 1.5*cm, h - 19,
                                   f"{self._sirket_adi}  |  {self._rapor_tarihi}")

        # Alt çizgi + sayfa numarası
        canvas.setFillColor(C_DARK_HDR)
        canvas.rect(0, 0, w, 22, fill=1, stroke=0)
        canvas.setFont(_f(), 7.5)
        canvas.setFillColor(colors.HexColor("#4a6fa5"))
        canvas.drawString(1.5*cm, 7, "KazKaz AI | Finansal Analiz Platformu")
        canvas.setFillColor(colors.HexColor("#60a5fa"))
        canvas.drawRightString(w - 1.5*cm, 7, f"Sayfa {doc.page}")
        canvas.restoreState()

    def _first_page(self, canvas, doc):
        self._header_footer(canvas, doc, is_first=True)

    def _later_pages(self, canvas, doc):
        self._header_footer(canvas, doc, is_first=False)


# ─────────────────────────────────────────────
# YARDIMCI: Para formatlama
# ─────────────────────────────────────────────

def fmt(v: float) -> str:
    if abs(v) >= 1_000_000:
        return f"{v/1_000_000:.2f}M TL"
    if abs(v) >= 1_000:
        return f"{v/1_000:.1f}K TL"
    return f"{v:,.0f} TL"

def fmt_pct(v: float) -> str:
    return f"%{v:.1f}"

def score_color(k: str) -> colors.Color:
    return {
        "Mukemmel": C_GREEN, "Mükemmel": C_GREEN,
        "Iyi": C_ACCENT1,   "İyi": C_ACCENT1,
        "Orta": C_YELLOW,
        "Zayif": colors.HexColor("#f97316"), "Zayıf": colors.HexColor("#f97316"),
        "Kritik": C_RED,
    }.get(k, C_SUBTEXT)


# ─────────────────────────────────────────────
# BLOK OLUŞTURUCULAR
# ─────────────────────────────────────────────

def _section_title(text: str, S: Dict) -> List:
    """Bölüm başlığı + yatay çizgi."""
    return [
        Spacer(1, 0.3*cm),
        Paragraph(text, S["section"]),
        HRFlowable(width="100%", thickness=1.5, color=C_ACCENT1,
                   spaceAfter=8, spaceBefore=0),
    ]


def _kpi_table(kpis: List[Dict], S: Dict) -> Table:
    """
    kpis: [{"label": str, "value": str, "delta": str, "positive": bool}, ...]
    """
    n = len(kpis)
    col_w = (A4[0] - 3*cm) / n

    data = []
    row_label = []
    row_value = []
    row_delta = []

    for kpi in kpis:
        row_label.append(Paragraph(kpi.get("label",""), S["kpi_label"]))
        row_value.append(Paragraph(kpi.get("value",""), S["kpi_value"]))
        delta_txt = kpi.get("delta","")
        delta_col = C_GREEN if kpi.get("positive", True) else C_RED
        row_delta.append(Paragraph(delta_txt,
            ParagraphStyle("kd", parent=S["kpi_delta"], textColor=delta_col)))

    data = [row_label, row_value, row_delta]
    t = Table(data, colWidths=[col_w]*n, rowHeights=[14, 24, 14])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#f0f4ff")),
        ("BACKGROUND",    (0,0), (-1, 0), colors.HexColor("#e0e8f8")),
        ("BOX",           (0,0), (-1,-1), 0.5, C_BORDER),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, C_BORDER),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("ROUNDEDCORNERS", [4]),
    ]))
    return t


def _df_table(df: pd.DataFrame, S: Dict,
              col_widths: Optional[List] = None,
              max_rows: int = 20) -> Table:
    """DataFrame'i styled table'a çevirir."""
    df = df.head(max_rows)
    headers = [Paragraph(str(c), S["table_header"]) for c in df.columns]
    rows = [headers]
    for i, row in df.iterrows():
        cells = [Paragraph(str(v), S["table_cell"]) for v in row.values]
        rows.append(cells)

    n = len(df.columns)
    if col_widths is None:
        col_widths = [(A4[0] - 3*cm) / n] * n

    t = Table(rows, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND",    (0,0), (-1, 0), C_DARK_HDR),
        ("TEXTCOLOR",     (0,0), (-1, 0), C_WHITE),
        ("FONTNAME", (0,0), (-1, 0), _f(bold=True)),
        ("FONTSIZE",      (0,0), (-1, 0), 8.5),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("INNERGRID",     (0,0), (-1,-1), 0.3, colors.HexColor("#ccd8f0")),
        ("BOX",           (0,0), (-1,-1), 0.5, C_BORDER),
        ("ROWBACKGROUNDS",(0,1), (-1,-1),
         [colors.white, colors.HexColor("#f4f7fd")]),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]
    t.setStyle(TableStyle(style))
    return t


def _bar_chart(labels: List[str], values: List[float],
               bar_color=None, width=15*cm, height=6*cm) -> Drawing:
    """Basit dikey bar chart."""
    if bar_color is None:
        bar_color = C_ACCENT1

    d = Drawing(width, height)
    chart = VerticalBarChart()
    chart.x        = 40
    chart.y        = 30
    chart.width    = width - 60
    chart.height   = height - 50

    chart.data     = [values]
    chart.categoryAxis.categoryNames = [str(l) for l in labels]
    chart.categoryAxis.labels.angle  = 35
    chart.categoryAxis.labels.dy     = -10
    chart.categoryAxis.labels.fontSize = 7
    chart.categoryAxis.labels.fontName = _f()
    chart.valueAxis.labels.fontSize    = 7
    chart.valueAxis.labels.fontName = _f()
    chart.valueAxis.labelTextFormat    = lambda v: fmt(v)

    chart.bars[0].fillColor   = bar_color
    chart.bars[0].strokeColor = colors.transparent
    chart.bars[0].strokeWidth = 0

    # Renk listesi (pozitif/negatif)
    for i, v in enumerate(values):
        chart.bars[(0, i)].fillColor = C_GREEN if v >= 0 else C_RED

    d.add(chart)
    return d


def _pie_chart(labels: List[str], values: List[float],
               width=9*cm, height=9*cm) -> Drawing:
    """Basit pasta grafik."""
    palette = [C_ACCENT1, C_ACCENT2, C_GREEN, C_YELLOW,
               colors.HexColor("#7c3aed"), colors.HexColor("#f97316"),
               colors.HexColor("#06b6d4"), colors.HexColor("#84cc16")]

    d = Drawing(width, height)
    pie = Pie()
    pie.x       = int(width * 0.1)
    pie.y       = int(height * 0.1)
    pie.width   = int(width * 0.55)
    pie.height  = int(height * 0.55)
    pie.data    = [max(v, 0.001) for v in values]
    pie.labels  = [f"{l}\n{fmt_pct(v/sum(values)*100)}" if sum(values) > 0 else l
                   for l, v in zip(labels, values)]

    for i in range(len(values)):
        pie.slices[i].fillColor    = palette[i % len(palette)]
        pie.slices[i].strokeColor  = colors.white
        pie.slices[i].strokeWidth  = 1
        pie.slices[i].labelRadius  = 1.3
        pie.slices[i].fontSize     = 7
        pie.slices[i].fontName = _f()

    d.add(pie)
    return d


def _score_gauge(skor: float, kategori: str, width=6*cm, height=3.5*cm) -> Drawing:
    """Sağlık skoru gauge görseli."""
    renk = score_color(kategori)
    d = Drawing(width, height)
    # Arka plan bar
    d.add(Rect(10, height/2-8, width-20, 16,
               fillColor=colors.HexColor("#e0e8f8"),
               strokeColor=colors.HexColor("#c0cce0"), strokeWidth=0.5))
    # Doluluk bar
    fill_w = (width - 20) * (skor / 100)
    d.add(Rect(10, height/2-8, fill_w, 16,
               fillColor=renk, strokeColor=colors.transparent))
    # Skor yazısı
    d.add(String(width/2, height/2-4, f"{skor}/100",
                 fontName=_f(bold=True), fontSize=12,
                 fillColor=colors.HexColor("#1a2a4a"),
                 textAnchor="middle"))
    d.add(String(width/2, height/2-18, kategori,
                 fontName=_f(bold=True), fontSize=9,
                 fillColor=renk, textAnchor="middle"))
    return d


# ─────────────────────────────────────────────
# ANA PDF OLUŞTURUCU
# ─────────────────────────────────────────────

class PDFReportGenerator:
    """
    KazKaz AI - PDF Rapor Motoru

    Kullanım:
        gen = PDFReportGenerator(rapor, engine, sirket_adi="Acme A.Ş.")
        pdf_bytes = gen.generate()

    Streamlit entegrasyonu:
        pdf_bytes = gen.generate()
        st.download_button("PDF İndir", pdf_bytes,
                           "kazkaz_rapor.pdf", "application/pdf")
    """

    def __init__(
        self,
        rapor:          Dict[str, Any],
        engine,                          # FinancialEngine instance
        sirket_adi:     str  = "Şirketim",
        hazırlayan:     str  = "KazKaz AI",
        ai_yorum:       Optional[str] = None,
        senaryo:        Optional[Dict] = None,
        tahmin:         Optional[Dict] = None,
        logo_path:      Optional[str] = None,
    ):
        self.rapor      = rapor
        self.engine     = engine
        self.sirket     = sirket_adi
        self.hazırlayan = hazırlayan
        self.ai_yorum   = ai_yorum
        self.senaryo    = senaryo
        self.tahmin     = tahmin
        self.logo_path  = logo_path
        self.tarih      = datetime.now().strftime("%d.%m.%Y %H:%M")
        self.S          = make_styles()

    # ─────────────────────────────────────────
    # ANA ÜRETIM METodu
    # ─────────────────────────────────────────

    def generate(self) -> bytes:
        """PDF üretir ve bytes olarak döndürür."""
        buffer = io.BytesIO()

        doc = KazkazTemplate(
            buffer,
            sirket_adi   = self.sirket,
            rapor_tarihi = self.tarih,
            pagesize     = A4,
            leftMargin   = 1.5*cm,
            rightMargin  = 1.5*cm,
            topMargin    = 1.8*cm,
            bottomMargin = 1.5*cm,
        )

        story = []
        story += self._cover_page()
        story += self._toc_page()
        story += self._executive_summary()
        story += self._gelir_section()
        story += self._gider_section()
        story += self._karlilik_section()
        story += self._saglik_section()

        if self.senaryo:
            story += self._senaryo_section()
        if self.tahmin:
            story += self._tahmin_section()
        if self.ai_yorum:
            story += self._ai_section()

        story += self._disclaimer_page()

        doc.build(story)
        buffer.seek(0)
        return buffer.read()

    # ─────────────────────────────────────────
    # KAPAK SAYFASI
    # ─────────────────────────────────────────

    def _cover_page(self) -> List:
        S = self.S
        g = self.rapor["gelir"]
        k = self.rapor["karlilik"]
        s = self.rapor["saglik_skoru"]

        story = []

        # Üst renkli alan
        story.append(Spacer(1, 0.5*cm))

        # Logo alanı (varsa)
        if self.logo_path and os.path.exists(self.logo_path):
            story.append(RLImage(self.logo_path, width=4*cm, height=1.5*cm))
            story.append(Spacer(1, 0.3*cm))

        # Başlık bloğu
        story.append(Spacer(1, 1.5*cm))
        story.append(Paragraph("KazKaz AI", S["title"]))
        story.append(Paragraph("FİNANSAL ANALİZ RAPORU", S["subtitle"]))
        story.append(Spacer(1, 0.4*cm))
        story.append(HRFlowable(width="60%", thickness=2,
                                color=C_ACCENT1, hAlign="CENTER"))
        story.append(Spacer(1, 0.6*cm))
        story.append(Paragraph(self.sirket, S["cover_company"]))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(f"Rapor Tarihi: {self.tarih}",
            ParagraphStyle("cd", parent=S["subtitle"], fontSize=9)))
        story.append(Paragraph(f"Hazırlayan: {self.hazırlayan}",
            ParagraphStyle("cp", parent=S["subtitle"], fontSize=9)))

        story.append(Spacer(1, 1.5*cm))

        # Özet KPI kutuları (kapakta)
        renk = score_color(s["kategori"])
        kar_positive = k["toplam_net_kar"] >= 0

        cover_data = [
            [
                Paragraph("TOPLAM GELİR",  S["kpi_label"]),
                Paragraph("NET KAR",        S["kpi_label"]),
                Paragraph("KAR MARJI",      S["kpi_label"]),
                Paragraph("SAĞLIK SKORU",   S["kpi_label"]),
            ],
            [
                Paragraph(fmt(g["toplam_gelir"]),   S["kpi_value"]),
                Paragraph(fmt(k["toplam_net_kar"]),
                    ParagraphStyle("cv", parent=S["kpi_value"],
                        textColor=C_GREEN if kar_positive else C_RED)),
                Paragraph(fmt_pct(k["kar_marji"]),  S["kpi_value"]),
                Paragraph(f'{s["skor"]}/100',
                    ParagraphStyle("cs", parent=S["kpi_value"], textColor=renk)),
            ],
            [
                Paragraph(f'Ort. Büyüme: {fmt_pct(g["ortalama_buyume_orani"])}', S["kpi_delta"]),
                Paragraph("↑ Trend: " + k["kar_trendi"],
                    ParagraphStyle("kt", parent=S["kpi_delta"],
                        textColor=C_GREEN if "Artış" in k["kar_trendi"] else C_YELLOW)),
                Paragraph(" ", S["kpi_delta"]),
                Paragraph(s["kategori"],
                    ParagraphStyle("sk", parent=S["kpi_delta"], textColor=renk)),
            ],
        ]
        cw = (A4[0] - 3*cm) / 4
        cover_t = Table(cover_data, colWidths=[cw]*4, rowHeights=[14, 26, 14])
        cover_t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), colors.HexColor("#0f1e36")),
            ("BACKGROUND",    (0,0), (-1, 0), colors.HexColor("#0a1628")),
            ("BOX",           (0,0), (-1,-1), 1, C_ACCENT1),
            ("INNERGRID",     (0,0), (-1,-1), 0.3, C_BORDER),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING",    (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("TEXTCOLOR",     (0,0), (-1,-1), C_TEXT),
        ]))
        story.append(cover_t)
        story.append(Spacer(1, 0.5*cm))

        # Alt not
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=C_BORDER, spaceAfter=8))
        story.append(Paragraph(
            "Bu rapor KazKaz AI tarafından otomatik olarak oluşturulmuştur. "
            "Finansal kararlar için uzman danışman görüşü alınması önerilir.",
            ParagraphStyle("disc", parent=S["footer"], alignment=TA_CENTER,
                           textColor=colors.HexColor("#4a6fa5"))))

        story.append(PageBreak())
        return story

    # ─────────────────────────────────────────
    # İÇİNDEKİLER
    # ─────────────────────────────────────────

    def _toc_page(self) -> List:
        S = self.S
        story = []
        story.append(Spacer(1, 0.8*cm))
        story += _section_title("İÇİNDEKİLER", S)

        bolumler = [
            ("1", "Yönetici Özeti"),
            ("2", "Gelir Analizi"),
            ("3", "Gider Analizi"),
            ("4", "Karlılık Analizi"),
            ("5", "Finansal Sağlık Skoru"),
        ]
        if self.senaryo:
            bolumler.append(("6", "Senaryo Analizi"))
        if self.tahmin:
            bolumler.append(("7", "Gelecek Tahmini"))
        if self.ai_yorum:
            bolumler.append(("8", "AI Yorumları ve Öneriler"))

        for no, baslik in bolumler:
            story.append(Paragraph(
                f"<b>{no}.</b>  {baslik}",
                ParagraphStyle("toc", parent=S["toc_item"],
                               spaceAfter=10)
            ))
            story.append(HRFlowable(width="100%", thickness=0.3,
                                    color=colors.HexColor("#dde8f8"),
                                    spaceBefore=0, spaceAfter=4))

        story.append(PageBreak())
        return story

    # ─────────────────────────────────────────
    # YÖNETİCİ ÖZETİ
    # ─────────────────────────────────────────

    def _executive_summary(self) -> List:
        S  = self.S
        g  = self.rapor["gelir"]
        e  = self.rapor["gider"]
        k  = self.rapor["karlilik"]
        s  = self.rapor["saglik_skoru"]

        story = []
        story.append(Spacer(1, 0.5*cm))
        story += _section_title("1. YÖNETİCİ ÖZETİ", S)

        # KPI satırı
        story.append(_kpi_table([
            {"label": "TOPLAM GELİR",  "value": fmt(g["toplam_gelir"]),
             "delta": f'Büyüme: {fmt_pct(g["ortalama_buyume_orani"])}',
             "positive": g["ortalama_buyume_orani"] >= 0},
            {"label": "TOPLAM GİDER",  "value": fmt(e["toplam_gider"]),
             "delta": f'Sabit: {fmt_pct(e["sabit_gider_orani"])}',
             "positive": e["sabit_gider_orani"] < 50},
            {"label": "NET KAR",       "value": fmt(k["toplam_net_kar"]),
             "delta": f'Marj: {fmt_pct(k["kar_marji"])}',
             "positive": k["toplam_net_kar"] >= 0},
            {"label": "SAĞLIK SKORU",  "value": f'{s["skor"]}/100',
             "delta": s["kategori"],
             "positive": s["skor"] >= 60},
        ], S))

        story.append(Spacer(1, 0.4*cm))

        # Alt skorlar tablosu
        alt = s["alt_skorlar"]
        alt_data = [
            [Paragraph("Faktör",   S["table_header"]),
             Paragraph("Skor",     S["table_header"]),
             Paragraph("Durum",    S["table_header"])],
        ]
        faktorler = [
            ("Karlılık",        alt["karlilik"]),
            ("Gelir Büyümesi",  alt["buyume"]),
            ("Gider Kontrolü",  alt["gider_kontrolu"]),
            ("Nakit Durumu",    alt["nakit"]),
        ]
        for fakt, val in faktorler:
            durum = "Güçlü" if val >= 70 else "Orta" if val >= 40 else "Zayıf"
            col   = C_GREEN  if val >= 70 else C_YELLOW if val >= 40 else C_RED
            alt_data.append([
                Paragraph(fakt, S["table_cell"]),
                Paragraph(f"{val}/100",
                    ParagraphStyle("av", parent=S["table_cell"], textColor=col)),
                Paragraph(durum,
                    ParagraphStyle("ad", parent=S["table_cell"], textColor=col)),
            ])
        cw = (A4[0] - 3*cm)
        alt_t = Table(alt_data, colWidths=[cw*0.4, cw*0.3, cw*0.3])
        alt_t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1, 0), C_DARK_HDR),
            ("TEXTCOLOR",     (0,0), (-1, 0), C_WHITE),
            ("BOX",           (0,0), (-1,-1), 0.5, C_BORDER),
            ("INNERGRID",     (0,0), (-1,-1), 0.3, colors.HexColor("#dde8f8")),
            ("ALIGN",         (0,0), (-1,-1), "CENTER"),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f4f7fd")]),
            ("TOPPADDING",    (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ]))
        story.append(alt_t)
        story.append(Spacer(1, 0.4*cm))

        # Genel yorum
        ozet_text = (
            f"{self.sirket} için hazırlanan bu finansal analiz raporu, "
            f"{g['ay_sayisi']} aylık dönemi kapsamaktadır. "
            f"Toplam {fmt(g['toplam_gelir'])} gelir elde edilmiş, "
            f"{fmt(e['toplam_gider'])} gider gerçekleşmiş ve "
            f"{fmt(k['toplam_net_kar'])} net kar elde edilmiştir. "
            f"Karlılık marjı {fmt_pct(k['kar_marji'])} olarak gerçekleşmiştir. "
            f"Finansal sağlık skoru {s['skor']}/100 ile <b>{s['kategori']}</b> kategorisindedir. "
            f"{s['aciklama']}"
        )
        story.append(Paragraph(ozet_text, S["body"]))
        story.append(PageBreak())
        return story

    # ─────────────────────────────────────────
    # GELİR ANALİZİ
    # ─────────────────────────────────────────

    def _gelir_section(self) -> List:
        S = self.S
        g = self.rapor["gelir"]
        story = []
        story.append(Spacer(1, 0.5*cm))
        story += _section_title("2. GELİR ANALİZİ", S)

        story.append(_kpi_table([
            {"label": "TOPLAM GELİR",   "value": fmt(g["toplam_gelir"]),
             "delta": "", "positive": True},
            {"label": "AYLIK ORTALAMA", "value": fmt(g["ortalama_aylik_gelir"]),
             "delta": "", "positive": True},
            {"label": "ORT. BÜYÜME",    "value": fmt_pct(g["ortalama_buyume_orani"]),
             "delta": "Aylık büyüme oranı",
             "positive": g["ortalama_buyume_orani"] >= 0},
            {"label": "EN KARLI KATEGORİ",
             "value": g["en_karli_kategori"].get("kategori", "-"),
             "delta": fmt(g["en_karli_kategori"].get("gelir", 0)),
             "positive": True},
        ], S))

        story.append(Spacer(1, 0.4*cm))

        # Aylık gelir grafiği
        monthly = self.engine.revenue.monthly_revenue()
        if not monthly.empty:
            story += _section_title("Aylık Gelir Trendi", S)
            chart = _bar_chart(
                labels=list(monthly["Dönem"]),
                values=list(monthly["Toplam Gelir"]),
                bar_color=C_ACCENT1,
                width=16*cm, height=6*cm,
            )
            story.append(chart)
            story.append(Spacer(1, 0.3*cm))

        # Kategori tablosu
        cat_rev = self.engine.revenue.revenue_by_category()
        cat_rev = cat_rev[cat_rev["Toplam Gelir"] > 0]
        if not cat_rev.empty:
            story += _section_title("Kategoriye Göre Gelir Dağılımı", S)
            col1_w = (A4[0] - 3*cm) * 0.6
            col2_w = (A4[0] - 3*cm) * 0.4
            story.append(_df_table(
                cat_rev.rename(columns={"Toplam Gelir": "Gelir (TL)"}),
                S, col_widths=[col1_w, col2_w]
            ))

        story.append(PageBreak())
        return story

    # ─────────────────────────────────────────
    # GİDER ANALİZİ
    # ─────────────────────────────────────────

    def _gider_section(self) -> List:
        S = self.S
        e = self.rapor["gider"]
        story = []
        story.append(Spacer(1, 0.5*cm))
        story += _section_title("3. GİDER ANALİZİ", S)

        story.append(_kpi_table([
            {"label": "TOPLAM GİDER",     "value": fmt(e["toplam_gider"]),
             "delta": "", "positive": False},
            {"label": "SABİT GİDER",      "value": fmt(e["sabit_gider"]),
             "delta": fmt_pct(e["sabit_gider_orani"]), "positive": True},
            {"label": "DEĞİŞKEN GİDER",   "value": fmt(e["degisken_gider"]),
             "delta": fmt_pct(100-e["sabit_gider_orani"]), "positive": True},
            {"label": "EN YÜKSEK KALem",
             "value": e["en_yuksek_gider_kalemi"].get("kategori", "-"),
             "delta": fmt(e["en_yuksek_gider_kalemi"].get("gider", 0)),
             "positive": False},
        ], S))

        story.append(Spacer(1, 0.4*cm))

        # Kategori tablosu + pasta
        cat_exp = self.engine.expense.expense_by_category()
        cat_exp = cat_exp[cat_exp["Toplam Gider"] > 0]

        if not cat_exp.empty:
            col1, col2 = [], []

            col1 += _section_title("Gider Dağılımı", S)
            col1.append(_df_table(
                cat_exp.rename(columns={"Toplam Gider": "Gider (TL)"}),
                S, col_widths=[(A4[0]-3*cm)*0.35, (A4[0]-3*cm)*0.25],
            ))

            col2 += _section_title("Pasta Grafik", S)
            col2.append(_pie_chart(
                labels=list(cat_exp["Kategori"]),
                values=list(cat_exp["Toplam Gider"]),
                width=8*cm, height=7*cm,
            ))

            t = Table([[col1, col2]], colWidths=[(A4[0]-3*cm)*0.55, (A4[0]-3*cm)*0.45])
            t.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"TOP"),
                                   ("LEFTPADDING",(0,0),(-1,-1),0),
                                   ("RIGHTPADDING",(0,0),(-1,-1),0)]))
            story.append(t)

        story.append(PageBreak())
        return story

    # ─────────────────────────────────────────
    # KARLILIK ANALİZİ
    # ─────────────────────────────────────────

    def _karlilik_section(self) -> List:
        S = self.S
        k = self.rapor["karlilik"]
        story = []
        story.append(Spacer(1, 0.5*cm))
        story += _section_title("4. KARLILIK ANALİZİ", S)

        story.append(_kpi_table([
            {"label": "NET KAR",    "value": fmt(k["toplam_net_kar"]),
             "delta": "Toplam dönem",  "positive": k["toplam_net_kar"] >= 0},
            {"label": "KAR MARJI",  "value": fmt_pct(k["kar_marji"]),
             "delta": "Gelire oranı",  "positive": k["kar_marji"] >= 0},
            {"label": "KAR TRENDİ", "value": k["kar_trendi"],
             "delta": "Dönem karşılaştırması",
             "positive": "Artış" in k["kar_trendi"]},
        ], S))

        story.append(Spacer(1, 0.4*cm))

        # Aylık kar bar chart
        mp = self.engine.profit.monthly_profit()
        if not mp.empty:
            story += _section_title("Aylık Net Kar", S)
            chart = _bar_chart(
                labels=list(mp["Dönem"]),
                values=list(mp["NetKar"]),
                width=16*cm, height=6*cm,
            )
            story.append(chart)
            story.append(Spacer(1, 0.3*cm))

            # Tablo
            story += _section_title("Aylık Karlılık Tablosu", S)
            show_cols = ["Dönem","Gelir","Gider","NetKar","KarMarji"]
            mp_show = mp[[c for c in show_cols if c in mp.columns]].copy()
            for col in ["Gelir","Gider","NetKar"]:
                if col in mp_show.columns:
                    mp_show[col] = mp_show[col].apply(fmt)
            if "KarMarji" in mp_show.columns:
                mp_show["KarMarji"] = mp_show["KarMarji"].apply(
                    lambda v: fmt_pct(v) if pd.notna(v) else "-")
            mp_show.columns = ["Dönem","Gelir","Gider","Net Kar","Kar Marjı"]
            cw = (A4[0]-3*cm)/5
            story.append(_df_table(mp_show, S, col_widths=[cw]*5))

        story.append(PageBreak())
        return story

    # ─────────────────────────────────────────
    # SAĞLIK SKORU
    # ─────────────────────────────────────────

    def _saglik_section(self) -> List:
        S  = self.S
        s  = self.rapor["saglik_skoru"]
        alt = s["alt_skorlar"]
        story = []
        story.append(Spacer(1, 0.5*cm))
        story += _section_title("5. FİNANSAL SAĞLIK SKORU", S)

        # Gauge
        gauge = _score_gauge(s["skor"], s["kategori"])
        story.append(gauge)
        story.append(Spacer(1, 0.3*cm))

        # Açıklama
        story.append(Paragraph(f"<b>Değerlendirme:</b> {s['aciklama']}", S["body"]))
        story.append(Spacer(1, 0.3*cm))

        # Alt skor çubukları
        story += _section_title("Faktör Bazlı Skor Dağılımı", S)
        faktor_labels = {
            "karlilik":      "Karlılık",
            "buyume":        "Gelir Büyümesi",
            "gider_kontrolu":"Gider Kontrolü",
            "nakit":         "Nakit Sürdürülebilirliği",
        }
        rows = [[
            Paragraph("Faktör", S["table_header"]),
            Paragraph("Skor", S["table_header"]),
            Paragraph("Görsel", S["table_header"]),
            Paragraph("Durum", S["table_header"]),
        ]]
        for key, lbl in faktor_labels.items():
            val  = alt.get(key, 0)
            col  = C_GREEN if val>=70 else C_YELLOW if val>=40 else C_RED
            durum = "Güçlü" if val>=70 else "Geliştirilmeli" if val>=40 else "Kritik"

            # Mini bar
            bar_d = Drawing(5*cm, 14)
            bar_d.add(Rect(0, 4, 5*cm, 8,
                           fillColor=colors.HexColor("#e0e8f8"),
                           strokeColor=colors.transparent))
            bar_d.add(Rect(0, 4, 5*cm * val/100, 8,
                           fillColor=col, strokeColor=colors.transparent))

            rows.append([
                Paragraph(lbl,   S["table_cell"]),
                Paragraph(f"{val}/100",
                    ParagraphStyle("sv", parent=S["table_cell"], textColor=col)),
                bar_d,
                Paragraph(durum,
                    ParagraphStyle("sd", parent=S["table_cell"], textColor=col)),
            ])

        cw = (A4[0]-3*cm)
        t = Table(rows, colWidths=[cw*0.28, cw*0.14, cw*0.38, cw*0.20])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1, 0), C_DARK_HDR),
            ("TEXTCOLOR",     (0,0),(-1, 0), C_WHITE),
            ("BOX",           (0,0),(-1,-1), 0.5, C_BORDER),
            ("INNERGRID",     (0,0),(-1,-1), 0.3, colors.HexColor("#dde8f8")),
            ("ALIGN",         (0,0),(-1,-1), "CENTER"),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f4f7fd")]),
            ("TOPPADDING",    (0,0),(-1,-1), 6),
            ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ]))
        story.append(t)
        story.append(PageBreak())
        return story

    # ─────────────────────────────────────────
    # SENARYO ANALİZİ
    # ─────────────────────────────────────────

    def _senaryo_section(self) -> List:
        S  = self.S
        sen = self.senaryo
        story = []
        story.append(Spacer(1, 0.5*cm))
        story += _section_title("6. SENARYO ANALİZİ", S)

        mevcut = sen["mevcut"]
        yeni   = sen["senaryo"]
        degisim= sen["degisim"]

        story.append(_kpi_table([
            {"label": "MEVCUT GELİR",  "value": fmt(mevcut["gelir"]),
             "delta": "", "positive": True},
            {"label": "YENİ GELİR",    "value": fmt(yeni["gelir"]),
             "delta": f'+{fmt(degisim["gelir_farki"])}', "positive": True},
            {"label": "MEVCUT NET KAR","value": fmt(mevcut["net_kar"]),
             "delta": "", "positive": mevcut["net_kar"]>=0},
            {"label": "YENİ NET KAR",  "value": fmt(yeni["net_kar"]),
             "delta": f'+{fmt(degisim["kar_farki"])}',
             "positive": degisim["kar_farki"]>=0},
        ], S))

        story.append(Spacer(1, 0.4*cm))

        # Karşılaştırma tablosu
        kar_data = [
            [Paragraph("Metrik",    S["table_header"]),
             Paragraph("Mevcut",    S["table_header"]),
             Paragraph("Senaryo",   S["table_header"]),
             Paragraph("Değişim",   S["table_header"])],
            [Paragraph("Gelir",     S["table_cell"]),
             Paragraph(fmt(mevcut["gelir"]),      S["table_cell"]),
             Paragraph(fmt(yeni["gelir"]),         S["table_cell"]),
             Paragraph(f'+{fmt(degisim["gelir_farki"])}',
                ParagraphStyle("pp", parent=S["table_cell"], textColor=C_GREEN))],
            [Paragraph("Gider",     S["table_cell"]),
             Paragraph(fmt(mevcut["gider"]),      S["table_cell"]),
             Paragraph(fmt(yeni["gider"]),         S["table_cell"]),
             Paragraph(fmt(yeni["gider"]-mevcut["gider"]),
                ParagraphStyle("np", parent=S["table_cell"], textColor=C_RED))],
            [Paragraph("Net Kar",   S["table_cell"]),
             Paragraph(fmt(mevcut["net_kar"]),    S["table_cell"]),
             Paragraph(fmt(yeni["net_kar"]),       S["table_cell"]),
             Paragraph(f'+{fmt(degisim["kar_farki"])}',
                ParagraphStyle("kp", parent=S["table_cell"], textColor=C_GREEN))],
            [Paragraph("Kar Marjı", S["table_cell"]),
             Paragraph(fmt_pct(mevcut["kar_marji"]),  S["table_cell"]),
             Paragraph(fmt_pct(yeni["kar_marji"]),     S["table_cell"]),
             Paragraph(fmt_pct(yeni["kar_marji"]-mevcut["kar_marji"]),
                ParagraphStyle("mp", parent=S["table_cell"], textColor=C_GREEN))],
        ]
        cw = (A4[0]-3*cm)/4
        t = Table(kar_data, colWidths=[cw]*4)
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1, 0), C_DARK_HDR),
            ("TEXTCOLOR",     (0,0),(-1, 0), C_WHITE),
            ("BOX",           (0,0),(-1,-1), 0.5, C_BORDER),
            ("INNERGRID",     (0,0),(-1,-1), 0.3, colors.HexColor("#dde8f8")),
            ("ALIGN",         (0,0),(-1,-1), "CENTER"),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#f4f7fd")]),
            ("TOPPADDING",    (0,0),(-1,-1), 6),
            ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ]))
        story.append(t)
        story.append(PageBreak())
        return story

    # ─────────────────────────────────────────
    # TAHMİN
    # ─────────────────────────────────────────

    def _tahmin_section(self) -> List:
        S = self.S
        tahmin = self.tahmin
        story = []
        story.append(Spacer(1, 0.5*cm))
        story += _section_title("7. GELECEK GELİR TAHMİNİ", S)

        story.append(_kpi_table([
            {"label": "TOPLAM TAHMİN",  "value": fmt(tahmin["toplam_tahmin"]),
             "delta": f'{tahmin["ay_sayisi"]} aylık', "positive": True},
            {"label": "AYLIK ORTALAMA", "value": fmt(tahmin["ortalama_tahmin"]),
             "delta": "", "positive": True},
            {"label": "BÜYÜME BEKLENTİSİ",
             "value": fmt_pct(tahmin["buyume_beklentisi"]),
             "delta": "Son gerçek vs son tahmin",
             "positive": tahmin["buyume_beklentisi"] >= 0},
            {"label": "TREND",          "value": tahmin["trend_yonu"],
             "delta": "", "positive": True},
        ], S))

        story.append(Spacer(1, 0.4*cm))

        # Tahmin tablosu
        tahmin_df = tahmin.get("tahmin_tablosu")
        if tahmin_df is not None and not tahmin_df.empty:
            story += _section_title("Aylık Tahmin Tablosu", S)
            cw = (A4[0]-3*cm)/4
            story.append(_df_table(tahmin_df, S, col_widths=[cw]*4))

        if tahmin.get("anomali_sayisi", 0) > 0:
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph(
                f"Uyarı: Gecmis veride {tahmin['anomali_sayisi']} anomali tespit edilmistir. "
                "Tahmin hassasiyeti etkilenmiş olabilir.",
                ParagraphStyle("warn", parent=S["body"],
                               textColor=C_YELLOW, fontName=_f(bold=True))))

        story.append(PageBreak())
        return story

    # ─────────────────────────────────────────
    # AI YORUMLARI
    # ─────────────────────────────────────────

    def _ai_section(self) -> List:
        S = self.S
        story = []
        story.append(Spacer(1, 0.5*cm))
        story += _section_title("8. AI YORUMLARI VE ÖNERİLER", S)

        # Mavi kutu background
        ai_paragraphs = []
        for line in self.ai_yorum.split("\n"):
            line = line.strip()
            if line:
                ai_paragraphs.append(Paragraph(line, S["ai_text"]))

        ai_box_data = [[ai_paragraphs]]
        ai_box = Table(ai_box_data,
                       colWidths=[A4[0]-3*cm])
        ai_box.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), colors.HexColor("#eef4ff")),
            ("BOX",           (0,0),(-1,-1), 1, C_ACCENT1),
            ("LEFTPADDING",   (0,0),(-1,-1), 14),
            ("RIGHTPADDING",  (0,0),(-1,-1), 14),
            ("TOPPADDING",    (0,0),(-1,-1), 12),
            ("BOTTOMPADDING", (0,0),(-1,-1), 12),
        ]))
        story.append(ai_box)
        story.append(Spacer(1, 0.4*cm))
        story.append(Paragraph(
            "* Bu yorumlar Google Gemini AI tarafından üretilmiştir. "
            "Bilgi amaçlıdır, yatırım tavsiyesi niteliği taşımaz.",
            ParagraphStyle("ai_disc", parent=S["body_small"],
                           textColor=colors.HexColor("#8090b0"))))
        story.append(PageBreak())
        return story

    # ─────────────────────────────────────────
    # YASAL UYARI
    # ─────────────────────────────────────────

    def _disclaimer_page(self) -> List:
        S = self.S
        story = []
        story.append(Spacer(1, 0.5*cm))
        story += _section_title("YASAL UYARI VE SORUMLULUK REDDİ", S)
        story.append(Paragraph(
            "Bu rapor KazKaz AI finansal analiz platformu tarafından otomatik olarak oluşturulmuştur. "
            "Raporda yer alan tüm analizler, tahminler ve yorumlar yalnızca bilgilendirme amacı taşımakta "
            "olup yatırım tavsiyesi, hukuki görüş veya muhasebe danışmanlığı niteliği taşımamaktadır. "
            "Finansal kararlarınızı vermeden önce lisanslı finansal danışmanlardan, muhasebecilerden "
            "veya ilgili uzmanlardan görüş almanız önerilir. "
            "KazKaz AI, bu rapordaki bilgilere dayanılarak alınan kararlardan doğabilecek "
            "herhangi bir zarar veya kayıptan sorumlu tutulamaz.",
            S["body"]
        ))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(
            f"Rapor Tarihi: {self.tarih}  |  Platform: KazKaz AI  |  Sürüm: v2.0",
            S["footer"]
        ))
        return story

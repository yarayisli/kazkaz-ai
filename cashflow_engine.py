"""
KazKaz AI - Nakit Akışı Analiz Motoru (v13)
=============================================
Modüller:
  - CashFlowAnalysis   : Operasyonel/yatırım/finansman nakit akışı
  - LiquidityMetrics   : Likidite oranları (cari, asit, nakit)
  - BurnRateAnalysis   : Yakma hızı ve runway hesabı
  - CashFlowForecast   : Kısa vadeli nakit akışı projeksiyonu
  - WorkingCapital     : İşletme sermayesi analizi
  - CashFlowScorer     : Nakit sağlık skoru (0-100)

Bağımlılıklar: pandas, numpy
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import warnings
warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────
# VERİ YAPISI
# ─────────────────────────────────────────────

@dataclass
class CashFlowInput:
    """Nakit akışı analizi için girdi verisi."""

    # Operasyonel nakit akışları (aylık)
    nakit_girisler:    List[float]   # Gelir tahsilatları
    nakit_cikislar:    List[float]   # Gider ödemeleri

    # Bilanço kalemleri (opsiyonel — likidite için)
    donen_varliklar:   float = 0.0   # Dönen varlıklar toplamı
    kisa_vadeli_borc:  float = 0.0   # Kısa vadeli borçlar toplamı
    stoklar:           float = 0.0   # Stok değeri
    alacaklar:         float = 0.0   # Ticari alacaklar
    borc_odeme_suresi: int   = 30    # Ortalama borç ödeme süresi (gün)
    alacak_tahsil_suresi: int = 45   # Ortalama alacak tahsil süresi (gün)

    # Mevcut nakit pozisyonu
    baslangic_nakiti:  float = 0.0

    def __post_init__(self):
        if len(self.nakit_girisler) != len(self.nakit_cikislar):
            raise ValueError("Giriş ve çıkış listesi aynı uzunlukta olmalı.")
        if not self.nakit_girisler:
            raise ValueError("En az bir dönem verisi gerekli.")


# ─────────────────────────────────────────────
# NAKİT AKIŞI ANALİZİ
# ─────────────────────────────────────────────

class CashFlowAnalysis:
    """Temel nakit akışı metrikleri."""

    def __init__(self, inp: CashFlowInput):
        self.inp = inp
        self.n   = len(inp.nakit_girisler)

    def net_cash_flow(self) -> List[float]:
        """Aylık net nakit akışı."""
        return [
            g - c for g, c in
            zip(self.inp.nakit_girisler, self.inp.nakit_cikislar)
        ]

    def cumulative_cash(self) -> List[float]:
        """Kümülatif nakit pozisyonu."""
        kumulatif = []
        toplam = self.inp.baslangic_nakiti
        for ncf in self.net_cash_flow():
            toplam += ncf
            kumulatif.append(round(toplam, 2))
        return kumulatif

    def operating_cash_flow(self) -> float:
        """Toplam operasyonel nakit akışı."""
        return round(sum(self.net_cash_flow()), 2)

    def average_monthly_inflow(self) -> float:
        return round(np.mean(self.inp.nakit_girisler), 2)

    def average_monthly_outflow(self) -> float:
        return round(np.mean(self.inp.nakit_cikislar), 2)

    def cash_flow_margin(self) -> float:
        """Nakit akışı marjı (%)."""
        toplam_giris = sum(self.inp.nakit_girisler)
        toplam_ncf   = self.operating_cash_flow()
        if toplam_giris == 0:
            return 0.0
        return round(toplam_ncf / toplam_giris * 100, 2)

    def positive_months(self) -> int:
        """Pozitif nakit akışlı ay sayısı."""
        return sum(1 for ncf in self.net_cash_flow() if ncf >= 0)

    def negative_months(self) -> int:
        return self.n - self.positive_months()

    def volatility(self) -> float:
        """Nakit akışı volatilitesi (std sapma)."""
        return round(float(np.std(self.net_cash_flow())), 2)

    def trend(self) -> str:
        """Nakit akışı trendi."""
        ncf = self.net_cash_flow()
        if len(ncf) < 2:
            return "Belirsiz"
        ilk = np.mean(ncf[:len(ncf)//2])
        son  = np.mean(ncf[len(ncf)//2:])
        degisim = (son - ilk) / max(abs(ilk), 1) * 100
        if degisim > 10:   return "Güçleniyor 📈"
        if degisim < -10:  return "Zayıflıyor 📉"
        return "Stabil ➡️"

    def monthly_table(self) -> pd.DataFrame:
        """Aylık nakit akışı tablosu."""
        ncf   = self.net_cash_flow()
        kumul = self.cumulative_cash()
        rows  = []
        for i in range(self.n):
            rows.append({
                "Dönem":         f"Ay {i+1}",
                "Nakit Girişi":  self.inp.nakit_girisler[i],
                "Nakit Çıkışı":  self.inp.nakit_cikislar[i],
                "Net Nakit":     ncf[i],
                "Kümülatif":     kumul[i],
                "Durum":         "✅ Pozitif" if ncf[i] >= 0 else "❌ Negatif",
            })
        return pd.DataFrame(rows)

    def summary(self) -> Dict[str, Any]:
        return {
            "operasyonel_ncf":    self.operating_cash_flow(),
            "ort_aylik_giris":    self.average_monthly_inflow(),
            "ort_aylik_cikis":    self.average_monthly_outflow(),
            "ncf_marji":          self.cash_flow_margin(),
            "pozitif_ay":         self.positive_months(),
            "negatif_ay":         self.negative_months(),
            "volatilite":         self.volatility(),
            "trend":              self.trend(),
            "son_nakit_pozisyon": self.cumulative_cash()[-1],
            "toplam_giris":       sum(self.inp.nakit_girisler),
            "toplam_cikis":       sum(self.inp.nakit_cikislar),
        }


# ─────────────────────────────────────────────
# LİKİDİTE METRİKLERİ
# ─────────────────────────────────────────────

class LiquidityMetrics:
    """
    Bilanço tabanlı likidite oranları.
    Dönen varlık ve kısa vadeli borç bilgisi gerektirir.
    """

    def __init__(self, inp: CashFlowInput):
        self.inp = inp

    def current_ratio(self) -> Optional[float]:
        """Cari oran = Dönen Varlıklar / Kısa Vadeli Borçlar. Hedef: > 2."""
        if self.inp.kisa_vadeli_borc == 0:
            return None
        return round(self.inp.donen_varliklar / self.inp.kisa_vadeli_borc, 2)

    def quick_ratio(self) -> Optional[float]:
        """Asit-test oranı = (Dönen Varlıklar - Stoklar) / KVB. Hedef: > 1."""
        if self.inp.kisa_vadeli_borc == 0:
            return None
        return round(
            (self.inp.donen_varliklar - self.inp.stoklar)
            / self.inp.kisa_vadeli_borc, 2)

    def cash_ratio(self) -> Optional[float]:
        """Nakit oranı = Nakit / KVB. Hedef: > 0.2."""
        nakit = self.inp.baslangic_nakiti
        if self.inp.kisa_vadeli_borc == 0 or nakit == 0:
            return None
        return round(nakit / self.inp.kisa_vadeli_borc, 2)

    def working_capital(self) -> float:
        """Net işletme sermayesi = Dönen Varlıklar - KVB."""
        return round(
            self.inp.donen_varliklar - self.inp.kisa_vadeli_borc, 2)

    def days_sales_outstanding(self) -> int:
        """Alacak tahsil süresi (gün)."""
        return self.inp.alacak_tahsil_suresi

    def days_payable_outstanding(self) -> int:
        """Borç ödeme süresi (gün)."""
        return self.inp.borc_odeme_suresi

    def cash_conversion_cycle(self) -> int:
        """Nakit dönüşüm döngüsü = DSO - DPO."""
        return self.inp.alacak_tahsil_suresi - self.inp.borc_odeme_suresi

    def summary(self) -> Dict[str, Any]:
        cr = self.current_ratio()
        qr = self.quick_ratio()
        cash_r = self.cash_ratio()
        ccc    = self.cash_conversion_cycle()
        return {
            "cari_oran":         cr,
            "asit_oran":         qr,
            "nakit_oran":        cash_r,
            "net_isletme_ser":   self.working_capital(),
            "alacak_tahsil_gun": self.days_sales_outstanding(),
            "borc_odeme_gun":    self.days_payable_outstanding(),
            "nakit_donusum_gun": ccc,
            "cari_oran_durum":   self._oran_durum(cr, 2.0, 1.0),
            "asit_oran_durum":   self._oran_durum(qr, 1.0, 0.5),
            "cash_oran_durum":   self._oran_durum(cash_r, 0.5, 0.2),
            "ccc_durum":         "Sağlıklı" if ccc <= 30 else
                                  "Dikkat"    if ccc <= 60 else "Kritik",
        }

    @staticmethod
    def _oran_durum(oran, iyi_esik, orta_esik) -> str:
        if oran is None:     return "Veri Yok"
        if oran >= iyi_esik: return "İyi"
        if oran >= orta_esik:return "Orta"
        return "Zayıf"


# ─────────────────────────────────────────────
# YAKMA HIZI (BURN RATE) ANALİZİ
# ─────────────────────────────────────────────

class BurnRateAnalysis:
    """
    Özellikle startup ve büyüme şirketleri için yakma hızı analizi.
    Mevcut nakit pozisyonu ve aylık net nakit akışına göre runway hesaplar.
    """

    def __init__(self, inp: CashFlowInput):
        self.inp    = inp
        self.cf     = CashFlowAnalysis(inp)

    def gross_burn_rate(self) -> float:
        """Brüt yakma hızı = Aylık ortalama nakit çıkışı."""
        return self.cf.average_monthly_outflow()

    def net_burn_rate(self) -> float:
        """
        Net yakma hızı = Aylık ortalama net nakit akışı.
        Negatifse şirket nakit yakıyor.
        """
        return round(np.mean(self.cf.net_cash_flow()), 2)

    def runway_months(self) -> Optional[float]:
        """
        Runway = Mevcut nakit / Aylık net yakma hızı.
        Sadece net yakma hızı negatifse hesaplanır.
        """
        net_burn = self.net_burn_rate()
        if net_burn >= 0:
            return None   # Nakit yakmıyor, runway sonsuza yakın
        nakit = self.inp.baslangic_nakiti
        if nakit <= 0:
            return 0.0
        return round(nakit / abs(net_burn), 1)

    def cash_zero_date(self) -> Optional[int]:
        """Mevcut gidişle nakit ne kadar ayda tükenir?"""
        runway = self.runway_months()
        if runway is None:
            return None
        return int(np.ceil(runway))

    def efficiency_ratio(self) -> float:
        """
        Nakit verimliliği = Toplam giriş / Toplam çıkış.
        > 1 → şirket üretiyor, < 1 → şirket yakıyor.
        """
        toplam_cikis = sum(self.inp.nakit_cikislar)
        if toplam_cikis == 0:
            return 0.0
        return round(sum(self.inp.nakit_girisler) / toplam_cikis, 3)

    def summary(self) -> Dict[str, Any]:
        gross  = self.gross_burn_rate()
        net    = self.net_burn_rate()
        runway = self.runway_months()
        return {
            "brut_yakma_hizi":   gross,
            "net_yakma_hizi":    net,
            "runway_ay":         runway,
            "nakit_bitis_ay":    self.cash_zero_date(),
            "verimlilik_orani":  self.efficiency_ratio(),
            "nakit_yakilip_yakilmiyor": net < 0,
            "durum":             "Kritik" if (runway and runway < 3) else
                                  "Dikkat" if (runway and runway < 6) else
                                  "Güvenli" if runway else "Nakit Yok",
        }


# ─────────────────────────────────────────────
# KISA VADELİ PROJEKSIYON
# ─────────────────────────────────────────────

class CashFlowForecast:
    """
    Son dönem verilerine göre kısa vadeli nakit projeksiyonu.
    Lineer trend + mevsimsellik varsayımı.
    """

    def __init__(self, inp: CashFlowInput, tahmin_ay: int = 3):
        self.inp       = inp
        self.tahmin_ay = tahmin_ay
        self.cf        = CashFlowAnalysis(inp)

    def project(self, buyume_orani: float = 0.0) -> pd.DataFrame:
        """
        buyume_orani: Aylık beklenen büyüme oranı (0.05 = %5)
        """
        # Son 3 ayın ortalamasını baz al
        son_n      = min(3, len(self.inp.nakit_girisler))
        baz_giris  = np.mean(self.inp.nakit_girisler[-son_n:])
        baz_cikis  = np.mean(self.inp.nakit_cikislar[-son_n:])
        son_kumulatif = self.cf.cumulative_cash()[-1]

        rows = []
        kumulatif = son_kumulatif
        for i in range(1, self.tahmin_ay + 1):
            proj_giris = baz_giris * (1 + buyume_orani) ** i
            proj_cikis = baz_cikis * (1 + buyume_orani * 0.5) ** i  # giderler daha yavaş büyür
            net        = proj_giris - proj_cikis
            kumulatif  += net
            rows.append({
                "Dönem":        f"T+{i}. Ay",
                "Proj. Giriş":  round(proj_giris, 0),
                "Proj. Çıkış":  round(proj_cikis, 0),
                "Net":          round(net, 0),
                "Kümülatif":    round(kumulatif, 0),
                "Durum":        "✅" if net >= 0 else "❌",
            })
        return pd.DataFrame(rows)

    def optimistic(self) -> pd.DataFrame:
        return self.project(buyume_orani=0.10)

    def base(self) -> pd.DataFrame:
        return self.project(buyume_orani=0.03)

    def pessimistic(self) -> pd.DataFrame:
        return self.project(buyume_orani=-0.05)


# ─────────────────────────────────────────────
# NAKİT SAĞLIK SKORU
# ─────────────────────────────────────────────

class CashFlowScorer:
    """0-100 nakit akışı sağlık skoru."""

    WEIGHTS = {
        "ncf_marji":    0.25,
        "pozitiflik":   0.25,
        "trend":        0.20,
        "likidite":     0.20,
        "burn":         0.10,
    }

    def __init__(self, cf: CashFlowAnalysis,
                 liq: LiquidityMetrics,
                 burn: BurnRateAnalysis):
        self.cf   = cf
        self.liq  = liq
        self.burn = burn

    def _ncf_marji_skoru(self) -> float:
        m = self.cf.cash_flow_margin()
        return float(np.clip(m * 4, 0, 100))

    def _pozitiflik_skoru(self) -> float:
        n = self.cf.n
        if n == 0: return 50.0
        return round(self.cf.positive_months() / n * 100, 1)

    def _trend_skoru(self) -> float:
        t = self.cf.trend()
        return 85.0 if "Güçleniyor" in t else 50.0 if "Stabil" in t else 20.0

    def _likidite_skoru(self) -> float:
        cr = self.liq.current_ratio()
        if cr is None: return 50.0
        return float(np.clip(cr / 2 * 100, 0, 100))

    def _burn_skoru(self) -> float:
        runway = self.burn.runway_months()
        if runway is None: return 100.0  # nakit yakmıyor
        return float(np.clip(runway / 12 * 100, 0, 100))

    def calculate(self) -> Dict[str, Any]:
        alt = {
            "ncf_marji":  round(self._ncf_marji_skoru(), 1),
            "pozitiflik": round(self._pozitiflik_skoru(), 1),
            "trend":      round(self._trend_skoru(), 1),
            "likidite":   round(self._likidite_skoru(), 1),
            "burn":       round(self._burn_skoru(), 1),
        }
        genel = sum(alt[k] * self.WEIGHTS[k] for k in alt)
        genel = round(genel, 1)
        return {
            "skor":       genel,
            "kategori":   self._kategori(genel),
            "alt_skorlar":alt,
            "aciklama":   self._aciklama(genel),
        }

    @staticmethod
    def _kategori(s: float) -> str:
        if s >= 80: return "Mükemmel"
        if s >= 65: return "İyi"
        if s >= 50: return "Orta"
        if s >= 35: return "Zayıf"
        return "Kritik"

    @staticmethod
    def _aciklama(s: float) -> str:
        return {
            range(80, 101): "Nakit akışı güçlü ve sürdürülebilir. Büyüme için hazır.",
            range(65, 80):  "Nakit durumu sağlıklı. Küçük iyileştirmelerle daha iyi olabilir.",
            range(50, 65):  "Nakit yönetimi dikkat gerektiriyor. Gider kontrolü önerilir.",
            range(35, 50):  "Nakit sıkışıklığı riski var. Acil önlemler alınmalı.",
            range(0, 35):   "Ciddi nakit sorunu. Likidite krizi riski yüksek.",
        }.get(next((r for r in [
            range(80,101), range(65,80), range(50,65), range(35,50), range(0,35)
        ] if int(s) in r), range(0,1)), "Değerlendirme yapılamadı.")


# ─────────────────────────────────────────────
# ANA NAKİT AKIŞI MOTORU
# ─────────────────────────────────────────────

class CashFlowEngine:
    """
    KazKaz AI Nakit Akışı Ana Motoru.

    Kullanım:
        engine = CashFlowEngine(inp)
        rapor  = engine.full_report()
    """

    def __init__(self, inp: CashFlowInput):
        self.inp   = inp
        self.cf    = CashFlowAnalysis(inp)
        self.liq   = LiquidityMetrics(inp)
        self.burn  = BurnRateAnalysis(inp)
        self.fc    = CashFlowForecast(inp)
        self.scorer= CashFlowScorer(self.cf, self.liq, self.burn)

    @classmethod
    def from_financial_engine(
        cls,
        fin_engine,          # FinancialEngine instance
        baslangic_nakiti: float = 0.0,
        donen_varliklar:  float = 0.0,
        kisa_vadeli_borc: float = 0.0,
        stoklar:          float = 0.0,
    ) -> "CashFlowEngine":
        """
        Mevcut FinancialEngine'den nakit akışı motoru oluşturur.
        Gelir → nakit giriş, Gider → nakit çıkış olarak kabul edilir.
        """
        df = fin_engine.df
        monthly = df.groupby("YilAy").agg(
            giris=("Gelir","sum"),
            cikis=("Gider","sum"),
        ).sort_index()

        inp = CashFlowInput(
            nakit_girisler   = list(monthly["giris"]),
            nakit_cikislar   = list(monthly["cikis"]),
            baslangic_nakiti = baslangic_nakiti,
            donen_varliklar  = donen_varliklar,
            kisa_vadeli_borc = kisa_vadeli_borc,
            stoklar          = stoklar,
        )
        return cls(inp)

    def full_report(self) -> Dict[str, Any]:
        return {
            "nakit_ozet":    self.cf.summary(),
            "likidite":      self.liq.summary(),
            "burn_rate":     self.burn.summary(),
            "skor":          self.scorer.calculate(),
            "aylik_tablo":   self.cf.monthly_table(),
            "projeksiyon":   {
                "iyimser":   self.fc.optimistic(),
                "baz":       self.fc.base(),
                "kotumser":  self.fc.pessimistic(),
            },
        }

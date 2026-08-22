"""
KazKaz AI - Borç Analiz Motoru (v13)
======================================
Modüller:
  - Debt              : Tekil borç tanımı
  - DebtPortfolio     : Borç portföyü yönetimi
  - DebtMetrics       : Borç oranları ve sağlık göstergeleri
  - AmortizationTable : İtfa tablosu hesabı
  - DebtCapacity      : Yeni borç kapasitesi analizi
  - DebtScorer        : Borç sağlık skoru (0-100)

Bağımlılıklar: pandas, numpy
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import warnings
warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────
# VERİ YAPILARI
# ─────────────────────────────────────────────

class DebtType(str, Enum):
    BANKA_KREDISI   = "Banka Kredisi"
    TAHVIL          = "Tahvil"
    LEASING         = "Leasing"
    ACIK_HESAP      = "Açık Hesap"
    ORTAK_BORCLAN   = "Ortak Borçlanması"
    DIGER           = "Diğer"


@dataclass
class Debt:
    """
    Tekil borç kalemi.

    TR-özel vergiler:
      bsmv_orani: Banka ve Sigorta Muameleleri Vergisi (TL kredide standart %5)
      kkdf_orani: Kaynak Kullanımını Destekleme Fonu (TL ticari nakit kredide
                  standart %15; yatırım kredisi ve leasing genellikle muaf)

    Efektif faiz = nominal × (1 + bsmv_orani + kkdf_orani).
    Örn. %35 nominal + %5 BSMV + %15 KKDF → %42 efektif.

    FX borçlarında para_birimi != "TRY" ve kur_baslangic set edilirse
    fx_yenidenle(guncel_kur) ile TL karşılığı güncellenir; fx_stress_test()
    kur artışına karşı toplam TL yükü tahmin eder.
    """
    ad:              str
    anapara:         float         # Kalan anapara (para_birimi cinsinden)
    faiz_orani:      float         # Yıllık nominal faiz oranı (0.35 = %35)
    vade_ay:         int           # Kalan vade (ay)
    aylik_odeme:     float = 0.0   # Aylık taksit (0 ise hesaplanır)
    borc_turu:       str   = DebtType.BANKA_KREDISI
    para_birimi:     str   = "TRY"
    teminat:         str   = ""
    aciklama:        str   = ""
    bsmv_orani:      float = 0.0   # 0.05 = %5 (TR default TL kredide %5)
    kkdf_orani:      float = 0.0   # 0.15 = %15 (TR default TL ticari nakit)
    kur_baslangic:   float = 1.0   # FX borçlarda başlangıç kuru (TRY/DOV)

    def __post_init__(self):
        if self.anapara < 0:
            raise ValueError("Anapara negatif olamaz.")
        if self.faiz_orani < 0:
            raise ValueError("Faiz oranı negatif olamaz.")
        if self.bsmv_orani < 0 or self.kkdf_orani < 0:
            raise ValueError("BSMV/KKDF oranı negatif olamaz.")
        # Aylık ödeme hesapla (sabit taksitli, nominal faiz üzerinden)
        if self.aylik_odeme == 0 and self.anapara > 0 and self.vade_ay > 0:
            r = self.faiz_orani / 12
            if r == 0:
                self.aylik_odeme = self.anapara / self.vade_ay
            else:
                self.aylik_odeme = round(
                    self.anapara * r * (1 + r) ** self.vade_ay /
                    ((1 + r) ** self.vade_ay - 1), 2)

    # ── TR vergi ve FX yardımcıları ──────────────────────────────────────────

    def efektif_faiz(self) -> float:
        """
        Efektif yıllık faiz (BSMV + KKDF dahil).
        Formül: nominal × (1 + BSMV + KKDF).
        Basit yaklaşımdır: gerçek yaşamda BSMV/KKDF her taksitte faiz
        ödemesi üzerine eklenir; bu formül ~aynı toplam maliyeti verir.
        """
        return round(self.faiz_orani * (1 + self.bsmv_orani + self.kkdf_orani), 4)

    def fx_yenidenle(self, guncel_kur: float) -> float:
        """
        FX borç anaparasının TL karşılığını verilen kurla döndür.
        TL borçlarda anapara olduğu gibi döner.

        Örn. anapara=100k USD, guncel_kur=35 → 3_500_000 TL.
        kur_baslangic (kayıt anındaki kur) sadece kur_farki() için kullanılır.
        """
        if self.para_birimi == "TRY":
            return self.anapara
        if guncel_kur <= 0:
            raise ValueError("guncel_kur > 0 olmalı.")
        if self.kur_baslangic <= 0:
            raise ValueError("kur_baslangic > 0 olmalı (kur_farki için gerekli).")
        return round(self.anapara * guncel_kur, 2)

    def kur_farki(self, guncel_kur: float) -> float:
        """
        Kur farkı = TL karşılığı (güncel) − TL karşılığı (başlangıç).
        Pozitif = TL değer kaybı → borç arttı.
        """
        if self.para_birimi == "TRY":
            return 0.0
        try_baslangic = self.anapara * self.kur_baslangic
        try_guncel    = self.fx_yenidenle(guncel_kur)
        return round(try_guncel - try_baslangic, 2)


# ─────────────────────────────────────────────
# İTFA TABLOSU
# ─────────────────────────────────────────────

class AmortizationTable:
    """Sabit taksitli borç için aylık itfa tablosu."""

    def __init__(self, debt: Debt):
        self.debt = debt

    def build(self) -> pd.DataFrame:
        r          = self.debt.faiz_orani / 12
        anapara    = self.debt.anapara
        taksit     = self.debt.aylik_odeme
        kalan      = anapara
        rows       = []

        for ay in range(1, self.debt.vade_ay + 1):
            faiz_odeme    = round(kalan * r, 2)
            ana_odeme     = round(min(taksit - faiz_odeme, kalan), 2)
            kalan         = round(max(kalan - ana_odeme, 0), 2)
            rows.append({
                "Ay":             ay,
                "Taksit":         taksit,
                "Anapara Ödemesi":ana_odeme,
                "Faiz Ödemesi":   faiz_odeme,
                "Kalan Anapara":  kalan,
            })
            if kalan == 0:
                break

        return pd.DataFrame(rows)

    def total_interest(self) -> float:
        """Toplam faiz ödemesi."""
        df = self.build()
        return round(float(df["Faiz Ödemesi"].sum()), 2)

    def total_payment(self) -> float:
        """Toplam ödeme."""
        df = self.build()
        return round(float(df["Taksit"].sum()), 2)


# ─────────────────────────────────────────────
# BORÇ PORTFÖYÜ
# ─────────────────────────────────────────────

class DebtPortfolio:
    """Çoklu borç kalemi yönetimi."""

    def __init__(self, debts: List[Debt]):
        self.debts = debts

    def total_debt(self) -> float:
        """Toplam kalan anapara."""
        return round(sum(d.anapara for d in self.debts), 2)

    def total_monthly_payment(self) -> float:
        """Toplam aylık taksit yükü."""
        return round(sum(d.aylik_odeme for d in self.debts), 2)

    def weighted_avg_rate(self) -> float:
        """Ağırlıklı ortalama nominal faiz oranı (%)."""
        toplam = self.total_debt()
        if toplam == 0:
            return 0.0
        return round(
            sum(d.anapara * d.faiz_orani for d in self.debts)
            / toplam * 100, 2)

    def weighted_avg_effective_rate(self) -> float:
        """
        Ağırlıklı ortalama efektif faiz oranı (%) — BSMV + KKDF dahil.
        TL nakit kredi ağırlıklı portföyde nominal ile %20+ fark açılabilir.
        """
        toplam = self.total_debt()
        if toplam == 0:
            return 0.0
        return round(
            sum(d.anapara * d.efektif_faiz() for d in self.debts)
            / toplam * 100, 2)

    def fx_exposure(self) -> Dict[str, Any]:
        """
        Yabancı para borç riski özeti.
        - toplam_fx_borc_baslangic: FX borçların TL karşılığı (giriş kurunda)
        - fx_pay_pct: FX borçların toplam portföydeki payı (%)
        - para_birimi_dagilim: {"USD": 1_500_000, "EUR": 500_000, ...}
        """
        toplam_try = self.total_debt()
        fx_debts   = [d for d in self.debts if d.para_birimi != "TRY"]
        if not fx_debts:
            return {
                "fx_borc_sayisi": 0,
                "toplam_fx_borc_baslangic": 0.0,
                "fx_pay_pct": 0.0,
                "para_birimi_dagilim": {},
            }

        toplam_fx_try_baslangic = round(
            sum(d.anapara * d.kur_baslangic for d in fx_debts), 2
        )
        dagilim: Dict[str, float] = {}
        for d in fx_debts:
            dagilim[d.para_birimi] = round(
                dagilim.get(d.para_birimi, 0.0) + d.anapara, 2
            )
        return {
            "fx_borc_sayisi": len(fx_debts),
            "toplam_fx_borc_baslangic": toplam_fx_try_baslangic,
            "fx_pay_pct": round(toplam_fx_try_baslangic / toplam_try * 100, 1)
                          if toplam_try > 0 else 0.0,
            "para_birimi_dagilim": dagilim,
        }

    def fx_stress_test(self, kur_artis_pct: float = 0.10) -> Dict[str, Any]:
        """
        Kur şoku simülasyonu — tüm FX borçlarda başlangıç kuru üzerine
        `kur_artis_pct` kadar artış varsayarak toplam TL borç yükü değişimi.

        Örn. kur_artis_pct=0.20 → tüm dövizlerde %20 kur artışı senaryosu.
        """
        toplam_baslangic_try = 0.0
        toplam_sok_try       = 0.0
        for d in self.debts:
            if d.para_birimi == "TRY":
                toplam_baslangic_try += d.anapara
                toplam_sok_try       += d.anapara
            else:
                sok_kur = d.kur_baslangic * (1 + kur_artis_pct)
                toplam_baslangic_try += d.anapara * d.kur_baslangic
                toplam_sok_try       += d.fx_yenidenle(sok_kur)

        delta = toplam_sok_try - toplam_baslangic_try
        return {
            "kur_artis_pct": kur_artis_pct,
            "toplam_borc_baslangic_try": round(toplam_baslangic_try, 2),
            "toplam_borc_sok_try":       round(toplam_sok_try, 2),
            "delta_try":                 round(delta, 2),
            "delta_pct":                 round(delta / toplam_baslangic_try * 100, 2)
                                         if toplam_baslangic_try > 0 else 0.0,
        }

    def by_type(self) -> pd.DataFrame:
        """Borç türüne göre dağılım."""
        rows = {}
        for d in self.debts:
            rows[d.borc_turu] = rows.get(d.borc_turu, 0) + d.anapara
        return pd.DataFrame(
            list(rows.items()),
            columns=["Tür","Tutar"]
        ).sort_values("Tutar", ascending=False)

    def summary_table(self) -> pd.DataFrame:
        """Tüm borçların özet tablosu."""
        rows = []
        for d in self.debts:
            amort = AmortizationTable(d)
            rows.append({
                "Borç Adı":          d.ad,
                "Tür":               d.borc_turu,
                "Para Birimi":       d.para_birimi,
                "Kalan Anapara":     d.anapara,
                "Faiz (%)":          round(d.faiz_orani * 100, 1),
                "Efektif Faiz (%)":  round(d.efektif_faiz() * 100, 2),
                "BSMV (%)":          round(d.bsmv_orani * 100, 2),
                "KKDF (%)":          round(d.kkdf_orani * 100, 2),
                "Vade (Ay)":         d.vade_ay,
                "Aylık Taksit":      d.aylik_odeme,
                "Toplam Faiz":       amort.total_interest(),
                "Toplam Ödeme":      amort.total_payment(),
            })
        return pd.DataFrame(rows)

    def payoff_priority(self) -> pd.DataFrame:
        """
        Ödeme önceliği (Avalanche yöntemi — yüksek faizden başla).
        """
        df = self.summary_table().copy()
        df = df.sort_values("Faiz (%)", ascending=False).reset_index(drop=True)
        df["Öncelik"] = range(1, len(df) + 1)
        return df[["Öncelik","Borç Adı","Faiz (%)","Kalan Anapara","Toplam Faiz"]]


# ─────────────────────────────────────────────
# BORÇ METRİKLERİ
# ─────────────────────────────────────────────

class DebtMetrics:
    """
    Borç sağlık oranları.
    Gelir ve FAVÖK bilgisi ile hesaplanır.
    """

    def __init__(self,
                 portfolio: DebtPortfolio,
                 yillik_gelir:   float,
                 yillik_favok:   float,
                 toplam_varlik:  float = 0.0,
                 ozkaynaklar:    float = 0.0):
        self.portfolio     = portfolio
        self.gelir         = yillik_gelir
        self.favok         = yillik_favok
        self.varlik        = toplam_varlik
        self.ozkaynak      = ozkaynaklar

    def debt_to_equity(self) -> Optional[float]:
        """Borç/Özkaynak oranı. Hedef: < 2."""
        if self.ozkaynak == 0:
            return None
        return round(self.portfolio.total_debt() / self.ozkaynak, 2)

    def debt_to_assets(self) -> Optional[float]:
        """Borç/Varlık oranı. Hedef: < 0.5."""
        if self.varlik == 0:
            return None
        return round(self.portfolio.total_debt() / self.varlik, 2)

    def debt_to_revenue(self) -> Optional[float]:
        """Borç/Gelir oranı. Hedef: < 3."""
        if self.gelir == 0:
            return None
        return round(self.portfolio.total_debt() / self.gelir, 2)

    def debt_service_coverage(self) -> Optional[float]:
        """
        DSCR = FAVÖK / Yıllık Borç Servisi.
        Hedef: > 1.25. < 1 → şirket borcunu ödeyemiyor.
        """
        yillik_borc_servisi = self.portfolio.total_monthly_payment() * 12
        if yillik_borc_servisi == 0:
            return None
        if self.favok == 0:
            return 0.0
        return round(self.favok / yillik_borc_servisi, 2)

    def interest_coverage(self) -> Optional[float]:
        """
        Faiz karşılama oranı = FAVÖK / Yıllık Faiz Gideri.
        Hedef: > 3.
        """
        yillik_faiz = sum(
            AmortizationTable(d).total_interest() / d.vade_ay * 12
            for d in self.portfolio.debts
            if d.vade_ay > 0
        )
        if yillik_faiz == 0:
            return None
        return round(self.favok / yillik_faiz, 2)

    def leverage_ratio(self) -> Optional[float]:
        """Net Borç / FAVÖK. Hedef: < 3."""
        if self.favok == 0:
            return None
        return round(self.portfolio.total_debt() / self.favok, 2)

    def monthly_burden_pct(self) -> Optional[float]:
        """Aylık borç servisi / Aylık gelir (%). Hedef: < 30%."""
        aylik_gelir = self.gelir / 12
        if aylik_gelir == 0:
            return None
        return round(
            self.portfolio.total_monthly_payment() / aylik_gelir * 100, 2)

    def summary(self) -> Dict[str, Any]:
        dscr = self.debt_service_coverage()
        ic   = self.interest_coverage()
        lev  = self.leverage_ratio()
        dte  = self.debt_to_equity()
        dta  = self.debt_to_assets()
        dtr  = self.debt_to_revenue()
        mb   = self.monthly_burden_pct()

        return {
            "toplam_borc":       self.portfolio.total_debt(),
            "aylik_taksit":      self.portfolio.total_monthly_payment(),
            "agirlikli_faiz":    self.portfolio.weighted_avg_rate(),
            "dscr":              dscr,
            "faiz_karsilama":    ic,
            "kaldirac_orani":    lev,
            "borc_ozkaynak":     dte,
            "borc_varlik":       dta,
            "borc_gelir":        dtr,
            "aylik_yuk_pct":     mb,
            "dscr_durum":        self._oran_durum(dscr, 1.5, 1.0),
            "ic_durum":          self._oran_durum(ic,   3.0, 1.5),
            "lev_durum":         self._oran_durum(lev,  3.0, 5.0, ters=True),
            "mb_durum":          self._oran_durum(mb,   30,  50,  ters=True),
        }

    @staticmethod
    def _oran_durum(val, iyi, orta, ters=False) -> str:
        if val is None: return "Veri Yok"
        if not ters:
            return "İyi" if val >= iyi else "Orta" if val >= orta else "Zayıf"
        else:
            return "İyi" if val <= iyi else "Orta" if val <= orta else "Zayıf"


# ─────────────────────────────────────────────
# BORÇ KAPASİTESİ
# ─────────────────────────────────────────────

class DebtCapacity:
    """
    Şirketin yeni borçlanma kapasitesini hesaplar.
    """

    def __init__(self, metrics: DebtMetrics):
        self.m = metrics

    def max_additional_debt(self) -> float:
        """
        DSCR ≥ 1.25 koşulunu sağlamak için alabileceği maksimum ek borç.
        """
        hedef_dscr       = 1.25
        yillik_bs_mevcut = self.m.portfolio.total_monthly_payment() * 12
        maks_yillik_bs   = self.m.favok / hedef_dscr if self.m.favok > 0 else 0
        kalan_kapasite   = max(0, maks_yillik_bs - yillik_bs_mevcut)

        # Varsayılan 36 ay vade, %40 faiz ile aylık taksit → anapara
        oran = 0.40 / 12
        if oran > 0:
            maks_anapara = kalan_kapasite / 12 * (
                (1 - (1 + oran) ** -36) / oran
            )
        else:
            maks_anapara = kalan_kapasite / 12 * 36
        return round(max(0, maks_anapara), 2)

    def debt_headroom(self) -> Dict[str, Any]:
        """Borçlanma başlık alanı analizi."""
        mevcut = self.m.portfolio.total_debt()
        maks   = self.max_additional_debt() + mevcut
        return {
            "mevcut_borc":       mevcut,
            "maks_ek_borc":      self.max_additional_debt(),
            "toplam_kapasite":   maks,
            "kullanim_orani":    round(mevcut / maks * 100, 1) if maks > 0 else 100,
            "tavsiye":           "Borçlanma kapasitesi yeterli." if self.max_additional_debt() > 0
                                  else "Mevcut borç yükü maksimum kapasitede.",
        }


# ─────────────────────────────────────────────
# BORÇ SAĞLIK SKORU
# ─────────────────────────────────────────────

class DebtScorer:
    """0-100 borç sağlık skoru."""

    WEIGHTS = {
        "dscr":    0.30,
        "ic":      0.25,
        "lev":     0.20,
        "mb":      0.15,
        "agirlik": 0.10,
    }

    def __init__(self, metrics: DebtMetrics):
        self.m = metrics

    def _dscr_skor(self) -> float:
        v = self.m.debt_service_coverage()
        if v is None: return 50.0
        return float(np.clip(v / 2.0 * 100, 0, 100))

    def _ic_skor(self) -> float:
        v = self.m.interest_coverage()
        if v is None: return 50.0
        return float(np.clip(v / 5.0 * 100, 0, 100))

    def _lev_skor(self) -> float:
        v = self.m.leverage_ratio()
        if v is None: return 50.0
        return float(np.clip((5 - v) / 5 * 100, 0, 100))

    def _mb_skor(self) -> float:
        v = self.m.monthly_burden_pct()
        if v is None: return 50.0
        return float(np.clip((50 - v) / 50 * 100, 0, 100))

    def _agirlik_skor(self) -> float:
        oran = self.m.portfolio.weighted_avg_rate()
        return float(np.clip((60 - oran) / 60 * 100, 0, 100))

    def calculate(self) -> Dict[str, Any]:
        alt = {
            "dscr":    round(self._dscr_skor(), 1),
            "ic":      round(self._ic_skor(), 1),
            "lev":     round(self._lev_skor(), 1),
            "mb":      round(self._mb_skor(), 1),
            "agirlik": round(self._agirlik_skor(), 1),
        }
        genel = sum(alt[k] * self.WEIGHTS[k] for k in alt)
        genel = round(genel, 1)
        return {
            "skor":       genel,
            "kategori":   self._kategori(genel),
            "alt_skorlar":alt,
            "tavsiye":    self._tavsiye(genel),
        }

    @staticmethod
    def _kategori(s: float) -> str:
        if s >= 80: return "Borç Sağlıklı"
        if s >= 65: return "Yönetilebilir"
        if s >= 50: return "Dikkat Gerektiriyor"
        if s >= 35: return "Riskli"
        return "Kritik"

    @staticmethod
    def _tavsiye(s: float) -> str:
        if s >= 80: return "Borç yapısı güçlü. Büyüme için yeni finansman değerlendirilebilir."
        if s >= 65: return "Borç yönetilebilir durumda. Yüksek faizli borçlar öncelikli ödenebilir."
        if s >= 50: return "Borç yükü dikkat gerektiriyor. Refinansman ve gider kısıtı önerilir."
        if s >= 35: return "Borç riski yüksek. Acil yeniden yapılandırma gerekebilir."
        return "Kritik borç durumu. Finansal danışman yardımı şiddetle önerilir."


# ─────────────────────────────────────────────
# ANA BORÇ MOTORU
# ─────────────────────────────────────────────

class DebtEngine:
    """
    KazKaz AI Borç Analizi Ana Motoru.

    Kullanım:
        debts  = [Debt("Banka Kredisi", 500000, 0.35, 24), ...]
        engine = DebtEngine(debts, yillik_gelir=2_000_000, yillik_favok=300_000)
        rapor  = engine.full_report()
    """

    def __init__(self,
                 debts:          List[Debt],
                 yillik_gelir:   float,
                 yillik_favok:   float,
                 toplam_varlik:  float = 0.0,
                 ozkaynaklar:    float = 0.0):
        self.portfolio = DebtPortfolio(debts)
        self.metrics   = DebtMetrics(
            self.portfolio, yillik_gelir, yillik_favok,
            toplam_varlik, ozkaynaklar)
        self.scorer    = DebtScorer(self.metrics)
        self.capacity  = DebtCapacity(self.metrics)

    def amortization_schedule(self, debt_index: int = 0) -> pd.DataFrame:
        """Belirtilen borcun itfa tablosunu döndür."""
        if debt_index >= len(self.portfolio.debts):
            return pd.DataFrame()
        return AmortizationTable(self.portfolio.debts[debt_index]).build()

    def full_report(self, fx_stres_kur_artis: float = 0.20) -> Dict[str, Any]:
        return {
            "portfolio_ozet":  {
                "toplam_borc":               self.portfolio.total_debt(),
                "aylik_taksit":              self.portfolio.total_monthly_payment(),
                "agirlikli_faiz":            self.portfolio.weighted_avg_rate(),
                "agirlikli_efektif_faiz":    self.portfolio.weighted_avg_effective_rate(),
                "borc_sayisi":               len(self.portfolio.debts),
            },
            "metrikler":       self.metrics.summary(),
            "skor":            self.scorer.calculate(),
            "kapasite":        self.capacity.debt_headroom(),
            "ozet_tablo":      self.portfolio.summary_table(),
            "odeme_onceligi":  self.portfolio.payoff_priority(),
            "tur_dagilimi":    self.portfolio.by_type(),
            "fx_exposure":     self.portfolio.fx_exposure(),
            "fx_stres_testi":  self.portfolio.fx_stress_test(fx_stres_kur_artis),
        }

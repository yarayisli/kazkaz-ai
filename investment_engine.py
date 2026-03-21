"""
KazKaz AI - Yatırım Analiz Motoru (v13)
=========================================
Modüller:
  - ROI Analizi          : Yatırım getiri oranı
  - NPV Analizi          : Net bugünkü değer
  - IRR Analizi          : İç verim oranı
  - Payback Analizi      : Geri ödeme süresi
  - PI Analizi           : Karlılık indeksi
  - Senaryo Karşılaştırma: Çoklu yatırım karşılaştırması
  - Monte Carlo          : Risk simülasyonu
  - Skor Motoru          : Yatırım kalite skoru (0-100)

Kurulum: pip install numpy pandas numpy-financial
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import warnings
warnings.filterwarnings("ignore")

try:
    import numpy_financial as npf
    NPF_OK = True
except ImportError:
    NPF_OK = False


# ─────────────────────────────────────────────
# VERİ YAPISI
# ─────────────────────────────────────────────

@dataclass
class Investment:
    """Tek bir yatırım tanımı."""
    ad:               str
    baslangic_maliyeti: float          # İlk yatırım tutarı (₺)
    nakit_akislari:   List[float]      # Yıllık nakit akışları listesi
    iskonto_orani:    float = 0.12     # Yıllık iskonto oranı (WACC)
    vergi_orani:      float = 0.22     # Kurumlar vergisi oranı
    enflasyon_orani:  float = 0.40     # Yıllık enflasyon oranı
    aciklama:         str   = ""

    def __post_init__(self):
        if self.baslangic_maliyeti <= 0:
            raise ValueError("Başlangıç maliyeti pozitif olmalıdır.")
        if not self.nakit_akislari:
            raise ValueError("En az bir nakit akışı girilmelidir.")


# ─────────────────────────────────────────────
# TEMEL METRİKLER
# ─────────────────────────────────────────────

class InvestmentMetrics:
    """
    Tek bir yatırım için tüm finansal metrikleri hesaplar.
    """

    def __init__(self, inv: Investment):
        self.inv = inv
        # NPV/IRR için nakit akışı = [-maliyet, cf1, cf2, ...]
        self._cf = [-inv.baslangic_maliyeti] + list(inv.nakit_akislari)

    # ── ROI ──────────────────────────────────
    def roi(self) -> float:
        """Toplam ROI (%)."""
        toplam_gelir = sum(self.inv.nakit_akislari)
        return round((toplam_gelir - self.inv.baslangic_maliyeti)
                     / self.inv.baslangic_maliyeti * 100, 2)

    def yillik_roi(self) -> float:
        """Yıllık ortalama ROI (%)."""
        n = len(self.inv.nakit_akislari)
        return round(self.roi() / n, 2) if n > 0 else 0.0

    # ── NPV ──────────────────────────────────
    def npv(self) -> float:
        """Net Bugünkü Değer (₺)."""
        if NPF_OK:
            return round(float(npf.npv(self.inv.iskonto_orani, self._cf)), 2)
        # Manuel hesap
        pv = 0.0
        for t, cf in enumerate(self._cf):
            pv += cf / ((1 + self.inv.iskonto_orani) ** t)
        return round(pv, 2)

    def npv_reel(self) -> float:
        """Enflasyona göre düzeltilmiş reel NPV."""
        r_nominal = self.inv.iskonto_orani
        r_enf     = self.inv.enflasyon_orani
        r_reel    = (1 + r_nominal) / (1 + r_enf) - 1

        pv = 0.0
        for t, cf in enumerate(self._cf):
            pv += cf / ((1 + r_reel) ** t)
        return round(pv, 2)

    # ── IRR ──────────────────────────────────
    def irr(self) -> Optional[float]:
        """İç Verim Oranı (%)."""
        try:
            if NPF_OK:
                val = npf.irr(self._cf)
            else:
                val = self._manual_irr()
            if val is None or np.isnan(val):
                return None
            return round(float(val) * 100, 2)
        except Exception:
            return None

    def _manual_irr(self) -> Optional[float]:
        """Newton-Raphson ile IRR."""
        r = 0.1
        for _ in range(1000):
            npv_val  = sum(cf / (1+r)**t for t, cf in enumerate(self._cf))
            dnpv_val = sum(-t * cf / (1+r)**(t+1) for t, cf in enumerate(self._cf))
            if dnpv_val == 0:
                return None
            r_new = r - npv_val / dnpv_val
            if abs(r_new - r) < 1e-8:
                return r_new
            r = r_new
        return None

    # ── PAYBACK ──────────────────────────────
    def payback_period(self) -> Dict[str, Any]:
        """
        Geri ödeme süresi (yıl).
        Hem basit hem iskontolu hesaplar.
        """
        # Basit payback
        kumulatif = 0.0
        basit_yil = None
        for i, cf in enumerate(self.inv.nakit_akislari, 1):
            kumulatif += cf
            if kumulatif >= self.inv.baslangic_maliyeti and basit_yil is None:
                onceki = kumulatif - cf
                kesir  = (self.inv.baslangic_maliyeti - onceki) / cf
                basit_yil = i - 1 + kesir

        # İskontolu payback
        kumulatif_pv = 0.0
        iskontolu_yil = None
        for i, cf in enumerate(self.inv.nakit_akislari, 1):
            pv_cf = cf / (1 + self.inv.iskonto_orani) ** i
            kumulatif_pv += pv_cf
            if kumulatif_pv >= self.inv.baslangic_maliyeti and iskontolu_yil is None:
                onceki_pv = kumulatif_pv - pv_cf
                kesir = (self.inv.baslangic_maliyeti - onceki_pv) / pv_cf
                iskontolu_yil = i - 1 + kesir

        return {
            "basit_yil":     round(basit_yil, 2)    if basit_yil    is not None else None,
            "iskontolu_yil": round(iskontolu_yil, 2) if iskontolu_yil is not None else None,
            "geri_odendi":   basit_yil is not None,
        }

    # ── PI (Profitability Index) ──────────────
    def pi(self) -> float:
        """
        Karlılık İndeksi.
        PI > 1 → yatırım kabul edilebilir.
        """
        pv_gelirler = sum(
            cf / (1 + self.inv.iskonto_orani) ** t
            for t, cf in enumerate(self.inv.nakit_akislari, 1)
        )
        return round(pv_gelirler / self.inv.baslangic_maliyeti, 4)

    # ── KÜMÜLATIF NAKİT AKIŞI ────────────────
    def cumulative_cashflow(self) -> pd.DataFrame:
        """Yıllık kümülatif nakit akışı tablosu."""
        rows = []
        kumulatif = -self.inv.baslangic_maliyeti
        for i, cf in enumerate(self.inv.nakit_akislari, 1):
            kumulatif += cf
            pv_cf = cf / (1 + self.inv.iskonto_orani) ** i
            rows.append({
                "Yıl":              i,
                "Nakit Akışı":      cf,
                "PV Nakit Akışı":   round(pv_cf, 2),
                "Kümülatif":        round(kumulatif, 2),
                "Geri Ödendi":      "✅" if kumulatif >= 0 else "❌",
            })
        return pd.DataFrame(rows)

    # ── VERGİ SONRASI NAKİT AKIŞI ────────────
    def after_tax_cashflow(self) -> List[float]:
        """Vergi sonrası nakit akışları."""
        return [cf * (1 - self.inv.vergi_orani)
                for cf in self.inv.nakit_akislari]

    def npv_after_tax(self) -> float:
        """Vergi sonrası NPV."""
        cf_list = [-self.inv.baslangic_maliyeti] + self.after_tax_cashflow()
        if NPF_OK:
            return round(float(npf.npv(self.inv.iskonto_orani, cf_list)), 2)
        pv = 0.0
        for t, cf in enumerate(cf_list):
            pv += cf / ((1 + self.inv.iskonto_orani) ** t)
        return round(pv, 2)

    # ── TAM ÖZET ─────────────────────────────
    def full_summary(self) -> Dict[str, Any]:
        pb = self.payback_period()
        return {
            "ad":               self.inv.ad,
            "maliyet":          self.inv.baslangic_maliyeti,
            "roi":              self.roi(),
            "yillik_roi":       self.yillik_roi(),
            "npv":              self.npv(),
            "npv_reel":         self.npv_reel(),
            "npv_vergi_sonrasi":self.npv_after_tax(),
            "irr":              self.irr(),
            "pi":               self.pi(),
            "payback_basit":    pb["basit_yil"],
            "payback_iskontolu":pb["iskontolu_yil"],
            "geri_odendi":      pb["geri_odendi"],
            "toplam_nakit_akisi": sum(self.inv.nakit_akislari),
            "yil_sayisi":       len(self.inv.nakit_akislari),
            "iskonto_orani":    self.inv.iskonto_orani,
        }


# ─────────────────────────────────────────────
# MONTE CARLO RİSK SİMÜLASYONU
# ─────────────────────────────────────────────

class MonteCarloSimulator:
    """
    NPV ve ROI için Monte Carlo risk simülasyonu.
    Nakit akışlarına belirsizlik (std sapma) ekleyerek
    olasılık dağılımı üretir.
    """

    def __init__(self, inv: Investment, n_sim: int = 10_000, seed: int = 42):
        self.inv    = inv
        self.n_sim  = n_sim
        self.seed   = seed

    def run(self, nakit_std_pct: float = 0.20,
            maliyet_std_pct: float = 0.10,
            iskonto_std:     float = 0.02) -> Dict[str, Any]:
        """
        nakit_std_pct   : Nakit akışlarının standart sapması (% olarak)
        maliyet_std_pct : Başlangıç maliyetinin std sapması
        iskonto_std     : İskonto oranının std sapması
        """
        rng = np.random.default_rng(self.seed)

        npv_list = []
        roi_list = []

        cf_mean    = np.array(self.inv.nakit_akislari)
        cf_std     = cf_mean * nakit_std_pct
        mal_std    = self.inv.baslangic_maliyeti * maliyet_std_pct

        for _ in range(self.n_sim):
            sim_maliyet = max(1, rng.normal(self.inv.baslangic_maliyeti, mal_std))
            sim_cfs     = rng.normal(cf_mean, cf_std)
            sim_r       = max(0.001, rng.normal(self.inv.iskonto_orani, iskonto_std))

            cf_list = [-sim_maliyet] + list(sim_cfs)
            if NPF_OK:
                sim_npv = float(npf.npv(sim_r, cf_list))
            else:
                sim_npv = sum(cf / (1+sim_r)**t for t, cf in enumerate(cf_list))

            sim_roi = (sum(sim_cfs) - sim_maliyet) / sim_maliyet * 100

            npv_list.append(sim_npv)
            roi_list.append(sim_roi)

        npv_arr = np.array(npv_list)
        roi_arr = np.array(roi_list)

        return {
            # NPV istatistikleri
            "npv_ortalama":   round(float(np.mean(npv_arr)),   2),
            "npv_medyan":     round(float(np.median(npv_arr)), 2),
            "npv_std":        round(float(np.std(npv_arr)),    2),
            "npv_p10":        round(float(np.percentile(npv_arr, 10)), 2),
            "npv_p25":        round(float(np.percentile(npv_arr, 25)), 2),
            "npv_p75":        round(float(np.percentile(npv_arr, 75)), 2),
            "npv_p90":        round(float(np.percentile(npv_arr, 90)), 2),
            "npv_pozitif_oran": round(float(np.mean(npv_arr > 0) * 100), 1),
            # ROI istatistikleri
            "roi_ortalama":   round(float(np.mean(roi_arr)),   2),
            "roi_std":        round(float(np.std(roi_arr)),    2),
            "roi_p10":        round(float(np.percentile(roi_arr, 10)), 2),
            "roi_p90":        round(float(np.percentile(roi_arr, 90)), 2),
            # Ham veriler (histogram için)
            "npv_data":       npv_arr.tolist(),
            "roi_data":       roi_arr.tolist(),
            # Risk seviyesi
            "risk_seviyesi":  self._risk_label(float(np.mean(npv_arr > 0) * 100)),
            "n_sim":          self.n_sim,
        }

    @staticmethod
    def _risk_label(pozitif_pct: float) -> str:
        if pozitif_pct >= 85: return "Düşük Risk"
        if pozitif_pct >= 65: return "Orta Risk"
        if pozitif_pct >= 45: return "Yüksek Risk"
        return "Çok Yüksek Risk"


# ─────────────────────────────────────────────
# SENARYO KARŞILAŞTIRICI
# ─────────────────────────────────────────────

class InvestmentComparator:
    """
    Birden fazla yatırım seçeneğini karşılaştırır ve sıralar.
    """

    def __init__(self, investments: List[Investment]):
        self.investments = investments
        self.metrics_list = [InvestmentMetrics(inv) for inv in investments]

    def compare(self) -> pd.DataFrame:
        """Tüm metrikleri karşılaştırma tablosunda göster."""
        rows = []
        for m in self.metrics_list:
            s = m.full_summary()
            rows.append({
                "Yatırım":        s["ad"],
                "Maliyet":        s["maliyet"],
                "ROI (%)":        s["roi"],
                "IRR (%)":        s["irr"] or "-",
                "NPV (₺)":        s["npv"],
                "PI":             s["pi"],
                "Geri Ödeme (Yıl)": s["payback_basit"] or "-",
                "Skor":           self._score(s),
            })
        df = pd.DataFrame(rows).sort_values("Skor", ascending=False)
        return df.reset_index(drop=True)

    def best_investment(self) -> Optional[str]:
        """En iyi yatırımı döndürür."""
        df = self.compare()
        return df.iloc[0]["Yatırım"] if not df.empty else None

    def _score(self, s: Dict) -> float:
        """Bileşik yatırım skoru (0-100)."""
        skor = 0.0
        # NPV > 0 → +30
        if s["npv"] > 0:
            skor += 30
        # IRR > iskonto oranı → +25
        irr_val = s.get("irr")
        if irr_val and irr_val > s["iskonto_orani"] * 100:
            skor += 25
        # PI > 1 → +20
        if s["pi"] > 1:
            skor += 20
        # ROI > 0 → +15
        if s["roi"] > 0:
            skor += 15
        # Geri ödendi → +10
        if s["geri_odendi"]:
            skor += 10
        return round(skor, 1)


# ─────────────────────────────────────────────
# YATIRIM KALİTE SKORU
# ─────────────────────────────────────────────

class InvestmentScorer:
    """
    0-100 arası yatırım kalite skoru üretir.
    """

    def __init__(self, metrics: InvestmentMetrics):
        self.m = metrics
        self.s = metrics.full_summary()

    def calculate(self) -> Dict[str, Any]:
        alt = {
            "npv_skoru":     self._npv_score(),
            "roi_skoru":     self._roi_score(),
            "irr_skoru":     self._irr_score(),
            "payback_skoru": self._payback_score(),
            "pi_skoru":      self._pi_score(),
        }
        agirliklar = {
            "npv_skoru":     0.30,
            "roi_skoru":     0.25,
            "irr_skoru":     0.20,
            "payback_skoru": 0.15,
            "pi_skoru":      0.10,
        }
        genel = sum(alt[k] * agirliklar[k] for k in alt)
        genel = round(genel, 1)
        return {
            "skor":      genel,
            "kategori":  self._kategori(genel),
            "alt_skorlar": {k: round(v, 1) for k, v in alt.items()},
            "tavsiye":   self._tavsiye(genel),
        }

    def _npv_score(self) -> float:
        npv = self.s["npv"]
        mal = self.s["maliyet"]
        if npv <= 0:          return max(0, 50 + npv / mal * 50)
        ratio = npv / mal
        return min(100, 50 + ratio * 50)

    def _roi_score(self) -> float:
        roi = self.s["roi"]
        return float(np.clip(roi * 2, 0, 100))

    def _irr_score(self) -> float:
        irr = self.s.get("irr")
        if irr is None: return 30.0
        target = self.s["iskonto_orani"] * 100
        if irr <= 0:    return 0.0
        ratio = irr / target
        return float(np.clip(ratio * 50, 0, 100))

    def _payback_score(self) -> float:
        pb = self.s.get("payback_basit")
        n  = self.s["yil_sayisi"]
        if pb is None: return 0.0
        # Daha hızlı geri ödeme → daha yüksek skor
        return float(np.clip((1 - pb / n) * 100, 0, 100))

    def _pi_score(self) -> float:
        pi = self.s["pi"]
        if pi <= 0: return 0.0
        return float(np.clip((pi - 0.5) * 100, 0, 100))

    @staticmethod
    def _kategori(skor: float) -> str:
        if skor >= 80: return "Mükemmel Yatırım"
        if skor >= 65: return "İyi Yatırım"
        if skor >= 50: return "Kabul Edilebilir"
        if skor >= 35: return "Riskli"
        return "Önerilmez"

    @staticmethod
    def _tavsiye(skor: float) -> str:
        if skor >= 80:
            return "Yatırım güçlü finansal göstergeler sunuyor. Uygulamaya geçilebilir."
        if skor >= 65:
            return "Yatırım olumlu görünüyor. Pazar koşulları da değerlendirilerek karar verilmeli."
        if skor >= 50:
            return "Yatırım sınırda kabul edilebilir. Risk faktörleri dikkatlice incelenmeli."
        if skor >= 35:
            return "Yatırım riskli. Nakit akışları ve maliyet yapısı gözden geçirilmeli."
        return "Yatırım mevcut koşullarda önerilmiyor. Alternatifler değerlendirilmeli."


# ─────────────────────────────────────────────
# ANA MOTOR
# ─────────────────────────────────────────────

class InvestmentEngine:
    """
    KazKaz AI Yatırım Analiz Ana Motoru.

    Kullanım:
        engine = InvestmentEngine(inv)
        rapor  = engine.full_report()
        mc     = engine.monte_carlo()
    """

    def __init__(self, investment: Investment):
        self.inv     = investment
        self.metrics = InvestmentMetrics(investment)
        self.scorer  = InvestmentScorer(self.metrics)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InvestmentEngine":
        inv = Investment(
            ad                   = data.get("ad", "Yatırım"),
            baslangic_maliyeti   = float(data["maliyet"]),
            nakit_akislari       = [float(v) for v in data["nakit_akislari"]],
            iskonto_orani        = float(data.get("iskonto_orani", 0.12)),
            vergi_orani          = float(data.get("vergi_orani", 0.22)),
            enflasyon_orani      = float(data.get("enflasyon_orani", 0.40)),
            aciklama             = data.get("aciklama", ""),
        )
        return cls(inv)

    def full_report(self) -> Dict[str, Any]:
        return {
            "ozet":          self.metrics.full_summary(),
            "skor":          self.scorer.calculate(),
            "kumulatif_df":  self.metrics.cumulative_cashflow(),
            "vergi_sonrasi_cf": self.metrics.after_tax_cashflow(),
        }

    def monte_carlo(self, n_sim: int = 10_000,
                    nakit_std_pct: float = 0.20,
                    maliyet_std_pct: float = 0.10) -> Dict[str, Any]:
        sim = MonteCarloSimulator(self.inv, n_sim=n_sim)
        return sim.run(nakit_std_pct=nakit_std_pct,
                       maliyet_std_pct=maliyet_std_pct)

    @staticmethod
    def compare(investments: List[Investment]) -> pd.DataFrame:
        return InvestmentComparator(investments).compare()

    @staticmethod
    def best(investments: List[Investment]) -> Optional[str]:
        return InvestmentComparator(investments).best_investment()

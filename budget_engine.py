"""
KazKaz AI - Bütçe vs Gerçekleşen Analiz Motoru
================================================
Özellikler:
  - Aylık bütçe girişi
  - Gerçekleşen vs bütçe sapma analizi
  - Sapma yüzdesi ve renk kodlaması
  - Kategori bazında bütçe takibi
  - Yıllık bütçe projeksiyonu
  - Bütçe sağlık skoru

Bağımlılıklar: pandas, numpy
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import warnings
warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────
# BÜTÇE VERİ YAPISI
# ─────────────────────────────────────────────

@dataclass
class BudgetPeriod:
    """Tek bir dönem bütçe kalemi."""
    donem:          str    # "2024-01" formatında
    butce_gelir:    float  # Planlanan gelir
    butce_gider:    float  # Planlanan gider
    kategori:       str = "Genel"


@dataclass
class BudgetPlan:
    """Tam bütçe planı."""
    donemler:    List[BudgetPeriod] = field(default_factory=list)
    sirket_adi:  str = "Şirket"
    yil:         int = 2024

    def to_dataframe(self) -> pd.DataFrame:
        rows = []
        for d in self.donemler:
            rows.append({
                "Dönem":        d.donem,
                "Bütçe Gelir":  d.butce_gelir,
                "Bütçe Gider":  d.butce_gider,
                "Bütçe Net":    d.butce_gelir - d.butce_gider,
                "Kategori":     d.kategori,
            })
        return pd.DataFrame(rows)

    @staticmethod
    def from_dataframe(df: pd.DataFrame) -> "BudgetPlan":
        """DataFrame'den bütçe planı oluştur."""
        plan = BudgetPlan()
        for _, row in df.iterrows():
            plan.donemler.append(BudgetPeriod(
                donem       = str(row.get("Dönem", row.get("donem", ""))),
                butce_gelir = float(row.get("Bütçe Gelir", row.get("butce_gelir", 0))),
                butce_gider = float(row.get("Bütçe Gider", row.get("butce_gider", 0))),
                kategori    = str(row.get("Kategori", "Genel")),
            ))
        return plan


# ─────────────────────────────────────────────
# SAPMA ANALİZİ
# ─────────────────────────────────────────────

class VarianceAnalysis:
    """
    Bütçe vs Gerçekleşen sapma analizi.
    """

    def __init__(self, gerceklesen_df: pd.DataFrame, butce_plan: BudgetPlan):
        self.gercek = gerceklesen_df
        self.butce  = butce_plan.to_dataframe()

    def _gercek_aylik(self) -> pd.DataFrame:
        """Gerçekleşen verileri aylık bazda grupla."""
        return (
            self.gercek.groupby("YilAy")
            .agg(
                Gercek_Gelir=("Gelir", "sum"),
                Gercek_Gider=("Gider", "sum"),
            )
            .reset_index()
            .rename(columns={"YilAy": "Dönem"})
            .assign(Gercek_Net=lambda x: x["Gercek_Gelir"] - x["Gercek_Gider"])
        )

    def compare(self) -> pd.DataFrame:
        """Bütçe vs gerçekleşen karşılaştırma tablosu."""
        gercek = self._gercek_aylik()
        merged = pd.merge(
            self.butce[["Dönem","Bütçe Gelir","Bütçe Gider","Bütçe Net"]],
            gercek,
            on="Dönem",
            how="outer"
        ).fillna(0)

        # Sapma hesapla
        merged["Gelir Sapma (₺)"] = merged["Gercek_Gelir"] - merged["Bütçe Gelir"]
        merged["Gider Sapma (₺)"] = merged["Gercek_Gider"] - merged["Bütçe Gider"]
        merged["Net Sapma (₺)"]   = merged["Gercek_Net"]   - merged["Bütçe Net"]

        # Sapma yüzdesi
        def sapma_pct(gercek, butce):
            if butce == 0:
                return 0.0
            return round((gercek - butce) / abs(butce) * 100, 1)

        merged["Gelir Sapma (%)"] = merged.apply(
            lambda r: sapma_pct(r["Gercek_Gelir"], r["Bütçe Gelir"]), axis=1)
        merged["Net Sapma (%)"]   = merged.apply(
            lambda r: sapma_pct(r["Gercek_Net"], r["Bütçe Net"]), axis=1)

        # Durum etiketi
        merged["Gelir Durumu"] = merged["Gelir Sapma (₺)"].apply(
            lambda v: "✅ Hedef Üstü" if v > 0 else
                      "⚠️ Hedefe Yakın" if v >= -v*0.1 else
                      "❌ Hedef Altı"
        )

        return merged.sort_values("Dönem").reset_index(drop=True)

    def summary(self) -> Dict[str, Any]:
        """Özet istatistikler."""
        df = self.compare()
        if df.empty:
            return {}

        toplam_butce_gelir  = df["Bütçe Gelir"].sum()
        toplam_gercek_gelir = df["Gercek_Gelir"].sum()
        toplam_butce_net    = df["Bütçe Net"].sum()
        toplam_gercek_net   = df["Gercek_Net"].sum()

        gelir_basari = (
            round(toplam_gercek_gelir / toplam_butce_gelir * 100, 1)
            if toplam_butce_gelir > 0 else 0
        )
        net_basari = (
            round(toplam_gercek_net / toplam_butce_net * 100, 1)
            if toplam_butce_net > 0 else 0
        )

        # Hedefe ulaşılan ay sayısı
        hedef_ay = len(df[df["Gelir Sapma (₺)"] >= 0])

        return {
            "toplam_butce_gelir":  toplam_butce_gelir,
            "toplam_gercek_gelir": toplam_gercek_gelir,
            "toplam_butce_net":    toplam_butce_net,
            "toplam_gercek_net":   toplam_gercek_net,
            "gelir_sapma":         toplam_gercek_gelir - toplam_butce_gelir,
            "net_sapma":           toplam_gercek_net - toplam_butce_net,
            "gelir_basari_pct":    gelir_basari,
            "net_basari_pct":      net_basari,
            "hedef_ay":            hedef_ay,
            "toplam_ay":           len(df),
            "performans":          self._performans(gelir_basari),
        }

    @staticmethod
    def _performans(pct: float) -> str:
        if pct >= 110: return "🏆 Hedefi Aştı"
        if pct >= 100: return "✅ Hedefe Ulaştı"
        if pct >= 90:  return "🟡 Hedefe Yakın"
        if pct >= 75:  return "⚠️ Hedef Altı"
        return "❌ Kritik Sapma"


# ─────────────────────────────────────────────
# KATEGORİ BAZINDA BÜTÇE TAKİBİ
# ─────────────────────────────────────────────

class CategoryBudgetTracker:
    """Kategori bazında bütçe takibi."""

    def __init__(self, gercek_df: pd.DataFrame,
                 kategori_butceleri: Dict[str, float]):
        """
        kategori_butceleri: {"Satış": 500000, "Pazarlama": 100000, ...}
        """
        self.gercek  = gercek_df
        self.butceler = kategori_butceleri

    def track(self) -> pd.DataFrame:
        """Kategori bazında bütçe vs gerçekleşen."""
        gercek_kat = (
            self.gercek.groupby("Kategori")
            .agg(Gercek=("Gelir", "sum"))
            .reset_index()
        )

        rows = []
        for kat, butce in self.butceler.items():
            gercek_row = gercek_kat[gercek_kat["Kategori"] == kat]
            gercek_val = float(gercek_row["Gercek"].iloc[0]) if not gercek_row.empty else 0
            sapma      = gercek_val - butce
            pct        = round(gercek_val / butce * 100, 1) if butce > 0 else 0
            rows.append({
                "Kategori":        kat,
                "Bütçe (₺)":       butce,
                "Gerçekleşen (₺)": gercek_val,
                "Sapma (₺)":       sapma,
                "Başarı (%)":      pct,
                "Durum":           "✅" if pct >= 100 else "⚠️" if pct >= 80 else "❌",
            })

        return pd.DataFrame(rows).sort_values("Sapma (₺)", ascending=False)


# ─────────────────────────────────────────────
# YILLIK PROJEKSİYON
# ─────────────────────────────────────────────

class YearlyProjection:
    """
    Mevcut performansa göre yıl sonu tahmini.
    """

    def __init__(self, variance: VarianceAnalysis):
        self.var = variance

    def project(self) -> Dict[str, Any]:
        df       = self.var.compare()
        ozet     = self.var.summary()
        n_ay     = len(df)

        if n_ay == 0:
            return {}

        # Aylık ortalamalar
        ort_gercek_gelir = df["Gercek_Gelir"].mean()
        ort_gercek_gider = df["Gercek_Gider"].mean()
        ort_butce_gelir  = df["Bütçe Gelir"].mean()

        # Kalan ay sayısı (yıl sonuna)
        kalan_ay = max(0, 12 - n_ay)

        # Projeksiyon
        proj_ek_gelir = ort_gercek_gelir * kalan_ay
        proj_ek_gider = ort_gercek_gider * kalan_ay

        yilsonu_gelir  = df["Gercek_Gelir"].sum() + proj_ek_gelir
        yilsonu_gider  = df["Gercek_Gider"].sum() + proj_ek_gider
        yilsonu_net    = yilsonu_gelir - yilsonu_gider
        yillik_butce   = ort_butce_gelir * 12

        return {
            "tamamlanan_ay":    n_ay,
            "kalan_ay":         kalan_ay,
            "yilsonu_gelir":    round(yilsonu_gelir, 0),
            "yilsonu_gider":    round(yilsonu_gider, 0),
            "yilsonu_net":      round(yilsonu_net, 0),
            "yillik_butce":     round(yillik_butce, 0),
            "yillik_basari_pct":round(
                yilsonu_gelir / yillik_butce * 100, 1
            ) if yillik_butce > 0 else 0,
            "butce_fark":       round(yilsonu_gelir - yillik_butce, 0),
        }


# ─────────────────────────────────────────────
# ANA BÜTÇE MOTORU
# ─────────────────────────────────────────────

class BudgetEngine:
    """
    KazKaz AI Bütçe vs Gerçekleşen Ana Motoru.

    Kullanım:
        engine = BudgetEngine(gercek_df, butce_plan)
        rapor  = engine.full_report()
    """

    def __init__(self, gercek_df: pd.DataFrame,
                 butce_plan: BudgetPlan,
                 kategori_butceleri: Dict[str, float] = None):
        self.gercek   = gercek_df
        self.butce    = butce_plan
        self.variance = VarianceAnalysis(gercek_df, butce_plan)
        self.kat_tracker = CategoryBudgetTracker(
            gercek_df, kategori_butceleri or {}
        )
        self.projeksiyon = YearlyProjection(self.variance)

    def full_report(self) -> Dict[str, Any]:
        return {
            "karsilastirma":   self.variance.compare(),
            "ozet":            self.variance.summary(),
            "projeksiyon":     self.projeksiyon.project(),
            "kategori_takip":  self.kat_tracker.track()
            if self.kat_tracker.butceler else pd.DataFrame(),
        }

    @staticmethod
    def ornek_butce(gercek_df: pd.DataFrame) -> BudgetPlan:
        """
        Gerçekleşen veriden otomatik bütçe taslağı oluşturur.
        Ortalama değerlerin %10 üzerini bütçe olarak ayarlar.
        """
        aylik = (
            gercek_df.groupby("YilAy")
            .agg(gelir=("Gelir","sum"), gider=("Gider","sum"))
            .reset_index()
        )
        ort_gelir = aylik["gelir"].mean() * 1.10
        ort_gider = aylik["gider"].mean() * 1.05

        plan = BudgetPlan()
        for _, row in aylik.iterrows():
            plan.donemler.append(BudgetPeriod(
                donem       = row["YilAy"],
                butce_gelir = round(ort_gelir, 0),
                butce_gider = round(ort_gider, 0),
            ))
        return plan

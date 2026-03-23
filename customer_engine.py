"""
KazKaz AI - Müşteri & Ürün Analiz Motoru
==========================================
Veri formatı (CSV/Excel):
  Tarih | Kategori | Gelir | Gider | Müşteri | Ürün

Modüller:
  - CustomerAnalysis  : Müşteri bazında gelir, karlılık, sıralama
  - ProductAnalysis   : Ürün/hizmet bazında gelir analizi
  - RFMAnalysis       : Recency-Frequency-Monetary müşteri segmentasyonu
  - ChurnRiskAnalysis : Churn riski tahmini
  - CustomerEngine    : Ana motor

Bağımlılıklar: pandas, numpy
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────
# VERİ HAZIRLIK
# ─────────────────────────────────────────────

def prepare_customer_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mevcut finansal DataFrame'e Müşteri/Ürün sütunları ekler.
    Eğer sütunlar yoksa 'Genel' olarak doldurur.
    """
    df = df.copy()

    # Müşteri sütunu
    if "Müşteri" not in df.columns and "Musteri" not in df.columns:
        df["Müşteri"] = "Genel"
    elif "Musteri" in df.columns:
        df = df.rename(columns={"Musteri": "Müşteri"})

    # Ürün sütunu
    if "Ürün" not in df.columns and "Urun" not in df.columns:
        # Kategori sütununu ürün olarak kullan
        df["Ürün"] = df.get("Kategori", "Genel")
    elif "Urun" in df.columns:
        df = df.rename(columns={"Urun": "Ürün"})

    # Boşları doldur
    df["Müşteri"] = df["Müşteri"].fillna("Belirtilmemiş")
    df["Ürün"]    = df["Ürün"].fillna("Belirtilmemiş")

    return df


# ─────────────────────────────────────────────
# MÜŞTERİ ANALİZİ
# ─────────────────────────────────────────────

class CustomerAnalysis:
    """Müşteri bazında gelir ve karlılık analizi."""

    def __init__(self, df: pd.DataFrame):
        self.df = prepare_customer_data(df)
        # Sadece geliri olan satırlar
        self.gelir_df = self.df[self.df["Gelir"] > 0].copy()

    def revenue_by_customer(self) -> pd.DataFrame:
        """Müşteri bazında toplam gelir."""
        return (
            self.gelir_df.groupby("Müşteri")
            .agg(
                Toplam_Gelir=("Gelir", "sum"),
                Islem_Sayisi=("Gelir", "count"),
                Ortalama_Islem=("Gelir", "mean"),
                Ilk_Islem=("Tarih", "min"),
                Son_Islem=("Tarih", "max"),
            )
            .round(2)
            .sort_values("Toplam_Gelir", ascending=False)
            .reset_index()
            .rename(columns={
                "Toplam_Gelir":  "Toplam Gelir (₺)",
                "Islem_Sayisi":  "İşlem Sayısı",
                "Ortalama_Islem":"Ort. İşlem (₺)",
                "Ilk_Islem":     "İlk İşlem",
                "Son_Islem":     "Son İşlem",
            })
        )

    def profitability_by_customer(self) -> pd.DataFrame:
        """Müşteri bazında karlılık (gelir - o müşteriye atfedilen gider)."""
        musteri_gelir = (
            self.df.groupby("Müşteri")["Gelir"].sum()
        )
        # Giderleri eşit dağıt (müşteri bazında gider yoksa)
        toplam_gider  = self.df["Gider"].sum()
        toplam_gelir  = self.df["Gelir"].sum()

        rows = []
        for musteri, gelir in musteri_gelir.items():
            # Gelir payına göre gider dağıt
            pay = gelir / toplam_gelir if toplam_gelir > 0 else 0
            tahmini_gider = toplam_gider * pay
            kar = gelir - tahmini_gider
            marj = round(kar / gelir * 100, 1) if gelir > 0 else 0
            rows.append({
                "Müşteri":          musteri,
                "Gelir (₺)":        round(gelir, 0),
                "Tahmini Gider (₺)":round(tahmini_gider, 0),
                "Net Kar (₺)":      round(kar, 0),
                "Kar Marjı (%)":    marj,
            })

        return (pd.DataFrame(rows)
                .sort_values("Net Kar (₺)", ascending=False)
                .reset_index(drop=True))

    def top_customers(self, n: int = 5) -> pd.DataFrame:
        """En değerli n müşteri."""
        return self.revenue_by_customer().head(n)

    def customer_concentration(self) -> Dict[str, Any]:
        """
        Pareto analizi — top %20 müşteri toplam gelirin kaçını oluşturuyor?
        """
        df = self.revenue_by_customer()
        if df.empty:
            return {}

        toplam = df["Toplam Gelir (₺)"].sum()
        df["Kümülatif Pay (%)"] = (
            df["Toplam Gelir (₺)"].cumsum() / toplam * 100
        ).round(1)

        # Top %20 müşteri kaç kişi?
        n_musteri   = len(df)
        top20_sayi  = max(1, int(n_musteri * 0.2))
        top20_gelir = df.head(top20_sayi)["Toplam Gelir (₺)"].sum()
        top20_pay   = round(top20_gelir / toplam * 100, 1) if toplam > 0 else 0

        # 80% geliri sağlayan minimum müşteri sayısı
        df80 = df[df["Kümülatif Pay (%)"] <= 80]
        musteri_80_pct = len(df80) if not df80.empty else n_musteri

        return {
            "toplam_musteri":    n_musteri,
            "top20_pct_pay":     top20_pay,
            "top20_sayi":        top20_sayi,
            "musteri_80_pct":    musteri_80_pct,
            "konsantrasyon_riski": top20_pay > 60,
            "pareto_df":         df,
        }

    def monthly_customer_revenue(self) -> pd.DataFrame:
        """Aylık müşteri bazında gelir trendi."""
        return (
            self.gelir_df.groupby(["YilAy", "Müşteri"])["Gelir"]
            .sum()
            .reset_index()
            .rename(columns={"YilAy": "Dönem", "Gelir": "Gelir (₺)"})
        )

    def summary(self) -> Dict[str, Any]:
        top = self.top_customers(3)
        conc = self.customer_concentration()
        return {
            "toplam_musteri":     conc.get("toplam_musteri", 0),
            "top3_musteri":       list(top["Müşteri"]) if not top.empty else [],
            "top3_gelir":         float(top["Toplam Gelir (₺)"].sum()) if not top.empty else 0,
            "konsantrasyon_riski":conc.get("konsantrasyon_riski", False),
            "top20_pay":          conc.get("top20_pct_pay", 0),
        }


# ─────────────────────────────────────────────
# ÜRÜN / HİZMET ANALİZİ
# ─────────────────────────────────────────────

class ProductAnalysis:
    """Ürün/hizmet bazında gelir analizi."""

    def __init__(self, df: pd.DataFrame):
        self.df = prepare_customer_data(df)
        self.gelir_df = self.df[self.df["Gelir"] > 0].copy()

    def revenue_by_product(self) -> pd.DataFrame:
        """Ürün bazında gelir."""
        return (
            self.gelir_df.groupby("Ürün")
            .agg(
                Toplam_Gelir=("Gelir", "sum"),
                Islem_Sayisi=("Gelir", "count"),
                Ortalama_Islem=("Gelir", "mean"),
                Musteri_Sayisi=("Müşteri", "nunique"),
            )
            .round(2)
            .sort_values("Toplam_Gelir", ascending=False)
            .reset_index()
            .rename(columns={
                "Toplam_Gelir":   "Toplam Gelir (₺)",
                "Islem_Sayisi":   "Satış Adedi",
                "Ortalama_Islem": "Ort. Fiyat (₺)",
                "Musteri_Sayisi": "Müşteri Sayısı",
            })
        )

    def product_profitability(self) -> pd.DataFrame:
        """Ürün bazında karlılık tahmini."""
        urun_gelir  = self.df.groupby("Ürün")["Gelir"].sum()
        toplam_gider = self.df["Gider"].sum()
        toplam_gelir = self.df["Gelir"].sum()

        rows = []
        for urun, gelir in urun_gelir.items():
            pay = gelir / toplam_gelir if toplam_gelir > 0 else 0
            tahmini_gider = toplam_gider * pay
            kar = gelir - tahmini_gider
            marj = round(kar / gelir * 100, 1) if gelir > 0 else 0
            rows.append({
                "Ürün/Hizmet":      urun,
                "Gelir (₺)":        round(gelir, 0),
                "Tahmini Gider (₺)":round(tahmini_gider, 0),
                "Katkı Marjı (₺)":  round(kar, 0),
                "Katkı Marjı (%)":  marj,
            })

        return (pd.DataFrame(rows)
                .sort_values("Katkı Marjı (%)", ascending=False)
                .reset_index(drop=True))

    def product_trend(self) -> pd.DataFrame:
        """Ürün bazında aylık trend."""
        return (
            self.gelir_df.groupby(["YilAy", "Ürün"])["Gelir"]
            .sum()
            .reset_index()
            .rename(columns={"YilAy": "Dönem", "Gelir": "Gelir (₺)"})
        )

    def best_product(self) -> Dict[str, Any]:
        df = self.revenue_by_product()
        if df.empty:
            return {}
        top = df.iloc[0]
        return {
            "urun":   top["Ürün"],
            "gelir":  float(top["Toplam Gelir (₺)"]),
            "adet":   int(top["Satış Adedi"]),
        }

    def summary(self) -> Dict[str, Any]:
        best = self.best_product()
        df   = self.revenue_by_product()
        return {
            "toplam_urun":   len(df),
            "en_iyi_urun":   best.get("urun", "-"),
            "en_iyi_gelir":  best.get("gelir", 0),
        }


# ─────────────────────────────────────────────
# RFM ANALİZİ
# ─────────────────────────────────────────────

class RFMAnalysis:
    """
    Recency - Frequency - Monetary müşteri segmentasyonu.

    Segmentler:
      - Şampiyonlar   : Son alışveriş yakın, sık alıyor, çok harcıyor
      - Sadık          : Sık alıyor, iyi harcıyor
      - Potansiyel     : Son alışveriş yakın ama az sıklık
      - Risk Altında   : Eskiden iyiydi, uzun süre gelmiyor
      - Kayıp          : Çok uzun süredir gelmemiyor
    """

    def __init__(self, df: pd.DataFrame):
        self.df = prepare_customer_data(df)
        self.gelir_df = self.df[self.df["Gelir"] > 0].copy()
        self.analiz_tarihi = self.gelir_df["Tarih"].max()

    def calculate(self) -> pd.DataFrame:
        """RFM skorlarını hesapla."""
        if self.gelir_df.empty or len(self.gelir_df["Müşteri"].unique()) < 2:
            return pd.DataFrame()

        rfm = (
            self.gelir_df.groupby("Müşteri")
            .agg(
                Recency=("Tarih",  lambda x: (self.analiz_tarihi - x.max()).days),
                Frequency=("Gelir", "count"),
                Monetary=("Gelir",  "sum"),
            )
            .reset_index()
        )

        # 1-5 arası skor ver (5 en iyi)
        try:
            rfm["R_Score"] = pd.qcut(
                rfm["Recency"], q=5, labels=[5,4,3,2,1], duplicates="drop"
            ).astype(int)
        except Exception:
            rfm["R_Score"] = 3

        try:
            rfm["F_Score"] = pd.qcut(
                rfm["Frequency"].rank(method="first"),
                q=5, labels=[1,2,3,4,5], duplicates="drop"
            ).astype(int)
        except Exception:
            rfm["F_Score"] = 3

        try:
            rfm["M_Score"] = pd.qcut(
                rfm["Monetary"].rank(method="first"),
                q=5, labels=[1,2,3,4,5], duplicates="drop"
            ).astype(int)
        except Exception:
            rfm["M_Score"] = 3

        rfm["RFM_Score"] = rfm["R_Score"] + rfm["F_Score"] + rfm["M_Score"]
        rfm["Segment"]   = rfm.apply(self._segment, axis=1)

        return rfm.sort_values("RFM_Score", ascending=False).reset_index(drop=True)

    @staticmethod
    def _segment(row) -> str:
        r, f, m = row["R_Score"], row["F_Score"], row["M_Score"]
        if r >= 4 and f >= 4 and m >= 4:
            return "🏆 Şampiyon"
        elif f >= 4 and m >= 4:
            return "💎 Sadık Müşteri"
        elif r >= 4 and f <= 2:
            return "🌱 Potansiyel"
        elif r <= 2 and f >= 3:
            return "⚠️ Risk Altında"
        elif r <= 2 and f <= 2:
            return "❌ Kayıp Müşteri"
        elif m >= 4:
            return "💰 Yüksek Değerli"
        else:
            return "📊 Ortalama"

    def segment_summary(self) -> pd.DataFrame:
        """Segment bazında özet."""
        rfm = self.calculate()
        if rfm.empty:
            return pd.DataFrame()
        return (
            rfm.groupby("Segment")
            .agg(
                Musteri_Sayisi=("Müşteri", "count"),
                Ort_Gelir=("Monetary", "mean"),
                Toplam_Gelir=("Monetary", "sum"),
            )
            .round(0)
            .reset_index()
            .sort_values("Toplam_Gelir", ascending=False)
            .rename(columns={
                "Musteri_Sayisi": "Müşteri Sayısı",
                "Ort_Gelir":      "Ort. Gelir (₺)",
                "Toplam_Gelir":   "Toplam Gelir (₺)",
            })
        )


# ─────────────────────────────────────────────
# CHURN RİSK ANALİZİ
# ─────────────────────────────────────────────

class ChurnRiskAnalysis:
    """
    Churn riski yüksek müşterileri tespit eder.
    Son işlem tarihine ve işlem sıklığına göre risk puanı hesaplar.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = prepare_customer_data(df)
        self.gelir_df = self.df[self.df["Gelir"] > 0].copy()
        self.son_tarih = self.gelir_df["Tarih"].max()

    def calculate_risk(self) -> pd.DataFrame:
        """Her müşteri için churn risk skoru hesapla."""
        if self.gelir_df.empty:
            return pd.DataFrame()

        musteri_stats = (
            self.gelir_df.groupby("Müşteri")
            .agg(
                son_islem=("Tarih", "max"),
                islem_sayisi=("Gelir", "count"),
                toplam_gelir=("Gelir", "sum"),
                ortalama_aralik=("Tarih", lambda x:
                    x.sort_values().diff().dt.days.mean()
                    if len(x) > 1 else 30),
            )
            .reset_index()
        )

        rows = []
        for _, row in musteri_stats.iterrows():
            gecen_gun    = (self.son_tarih - row["son_islem"]).days
            beklenen_gun = row["ortalama_aralik"] or 30

            # Risk skoru: beklenenin kaç katı geçmiş?
            risk_carpan  = gecen_gun / max(beklenen_gun, 1)
            risk_pct     = min(round(risk_carpan * 33, 0), 99)

            risk_seviye  = (
                "🔴 Yüksek" if risk_pct >= 70 else
                "🟡 Orta"   if risk_pct >= 40 else
                "🟢 Düşük"
            )

            rows.append({
                "Müşteri":           row["Müşteri"],
                "Son İşlem":         row["son_islem"].strftime("%Y-%m"),
                "Geçen Gün":         int(gecen_gun),
                "Beklenen Aralık":   int(beklened := max(int(beklenen_gun), 1)),
                "Risk Skoru (%)":    int(risk_pct),
                "Risk Seviyesi":     risk_seviye,
                "Toplam Gelir (₺)":  round(row["toplam_gelir"], 0),
            })

        return (pd.DataFrame(rows)
                .sort_values("Risk Skoru (%)", ascending=False)
                .reset_index(drop=True))

    def high_risk_customers(self) -> pd.DataFrame:
        """Sadece yüksek riskli müşteriler."""
        df = self.calculate_risk()
        if df.empty:
            return df
        return df[df["Risk Seviyesi"] == "🔴 Yüksek"]

    def risk_summary(self) -> Dict[str, Any]:
        df = self.calculate_risk()
        if df.empty:
            return {}
        yuksek = len(df[df["Risk Seviyesi"] == "🔴 Yüksek"])
        orta   = len(df[df["Risk Seviyesi"] == "🟡 Orta"])
        return {
            "yuksek_risk":    yuksek,
            "orta_risk":      orta,
            "toplam_musteri": len(df),
            "risk_gelir":     float(
                df[df["Risk Seviyesi"] == "🔴 Yüksek"]["Toplam Gelir (₺)"].sum()
            ),
        }


# ─────────────────────────────────────────────
# ANA MOTOR
# ─────────────────────────────────────────────

class CustomerEngine:
    """
    KazKaz AI Müşteri & Ürün Analiz Ana Motoru.

    Kullanım:
        engine = CustomerEngine(df)
        rapor  = engine.full_report()
    """

    def __init__(self, df: pd.DataFrame):
        self.df       = prepare_customer_data(df)
        self.customer = CustomerAnalysis(df)
        self.product  = ProductAnalysis(df)
        self.rfm      = RFMAnalysis(df)
        self.churn    = ChurnRiskAnalysis(df)

    @property
    def has_real_customers(self) -> bool:
        """Gerçek müşteri verisi var mı?"""
        musteri_list = self.df["Müşteri"].unique()
        return not (len(musteri_list) == 1 and
                    musteri_list[0] in ["Genel", "Belirtilmemiş"])

    @property
    def has_real_products(self) -> bool:
        """Gerçek ürün verisi var mı?"""
        urun_list = self.df["Ürün"].unique()
        return len(urun_list) > 1

    def full_report(self) -> Dict[str, Any]:
        return {
            "musteri_ozet":     self.customer.summary(),
            "urun_ozet":        self.product.summary(),
            "churn_ozet":       self.churn.risk_summary(),
            "musteri_gelir":    self.customer.revenue_by_customer(),
            "musteri_kar":      self.customer.profitability_by_customer(),
            "urun_gelir":       self.product.revenue_by_product(),
            "urun_kar":         self.product.product_profitability(),
            "rfm":              self.rfm.calculate(),
            "rfm_segment":      self.rfm.segment_summary(),
            "churn_risk":       self.churn.calculate_risk(),
            "konsantrasyon":    self.customer.customer_concentration(),
            "has_customers":    self.has_real_customers,
            "has_products":     self.has_real_products,
        }

    @staticmethod
    def ornek_veri() -> pd.DataFrame:
        """
        Müşteri/ürün sütunlu örnek veri.
        Kullanıcıya CSV formatını göstermek için.
        """
        return pd.DataFrame({
            "Tarih":    ["2024-01","2024-01","2024-01","2024-02","2024-02",
                         "2024-02","2024-03","2024-03","2024-03","2024-04"],
            "Kategori": ["Satış","Satış","Gider","Satış","Satış",
                         "Gider","Satış","Satış","Gider","Satış"],
            "Gelir":    [50000,80000,0,60000,90000,0,70000,100000,0,85000],
            "Gider":    [0,0,30000,0,0,35000,0,0,40000,0],
            "Müşteri":  ["Acme A.Ş.","Beta Ltd.","",
                         "Acme A.Ş.","Gamma Co.","",
                         "Beta Ltd.","Acme A.Ş.","",
                         "Gamma Co."],
            "Ürün":     ["ERP Yazılım","CRM Modül","Ofis Gideri",
                         "ERP Yazılım","Danışmanlık","Personel",
                         "CRM Modül","ERP Yazılım","Kira",
                         "Danışmanlık"],
        })

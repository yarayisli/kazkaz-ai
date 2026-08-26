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
        """
        Müşteri bazında karlılık analizi.

        Metodoloji önceliği (bulunan ilki uygulanır):

        1. **Doğrudan müşteri gideri:** Satırda hem Müşteri hem Gider > 0
           varsa, gider o müşteriye direkt atfedilir. Brüt marj gerçek.
        2. **Ürün maliyeti eşleşmesi:** Ürün başına birim maliyet oranı
           çıkarılabiliyorsa (Ürün etiketli gider satırları vs. Ürün geliri),
           her müşterinin ürün karması o oranla çarpılır.
        3. **Yalnız gelir + genel havuz:** Ne müşteri ne ürün bazında gider
           yoksa, brüt marj hesaplanmaz — tablo yalnızca geliri ve sabit
           giderlerin müşteri başı payını gösterir; ``attrs["veri_yetersiz"]``
           işareti eklenir. Eski davranış (değişken gideri gelir payına
           orantılı dağıtıp tüm müşteriler için aynı brüt marj göstermek)
           yanıltıcıydı, kaldırıldı.
        """
        toplam_gelir = float(self.df["Gelir"].sum())
        if toplam_gelir == 0:
            return pd.DataFrame()

        musteri_gelir = self.gelir_df.groupby("Müşteri")["Gelir"].sum()
        if musteri_gelir.empty:
            return pd.DataFrame()

        # Kaynak tespiti: doğrudan müşteri gideri, ürün maliyeti, ya da hiçbiri
        kaynak, musteri_gider_map = self._musteri_gider_haritasi(musteri_gelir.index)

        # Sabit/değişken sınıflandırması (net kâr hesabı için hâlâ gerekli)
        sabit_kelimeler = ["kira", "maaş", "amortisman", "sigorta", "abonelik"]
        pattern = "|".join(sabit_kelimeler)
        is_sabit = self.df["Kategori"].str.lower().str.contains(pattern, na=False)
        sabit_gider = float(self.df.loc[is_sabit, "Gider"].sum())
        degisken_gider_toplam = float(self.df.loc[~is_sabit, "Gider"].sum())

        n_musteri = musteri_gelir.shape[0]
        rows: List[Dict[str, Any]] = []
        for musteri, gelir in musteri_gelir.items():
            # Sabit gider: müşteri sayısına eşit dağıt (yaklaşık ABC)
            atfedilen_sabit = sabit_gider / max(n_musteri, 1)

            if kaynak == "musteri":
                atfedilen_degisken = float(musteri_gider_map.get(musteri, 0.0))
                brut_katki = gelir - atfedilen_degisken
                brut_marj = round(brut_katki / gelir * 100, 1) if gelir > 0 else 0
                net_kar = brut_katki - atfedilen_sabit
                net_marj = round(net_kar / gelir * 100, 1) if gelir > 0 else 0
                rows.append({
                    "Müşteri":              musteri,
                    "Gelir (₺)":            round(gelir, 0),
                    "Değişken Gider (₺)":   round(atfedilen_degisken, 0),
                    "Brüt Katkı (₺)":       round(brut_katki, 0),
                    "Brüt Katkı Marjı (%)": brut_marj,
                    "Sabit Gider Payı (₺)": round(atfedilen_sabit, 0),
                    "Net Kar (₺)":          round(net_kar, 0),
                    "Net Marj (%)":         net_marj,
                })
            elif kaynak == "urun":
                atfedilen_degisken = float(musteri_gider_map.get(musteri, 0.0))
                brut_katki = gelir - atfedilen_degisken
                brut_marj = round(brut_katki / gelir * 100, 1) if gelir > 0 else 0
                net_kar = brut_katki - atfedilen_sabit
                net_marj = round(net_kar / gelir * 100, 1) if gelir > 0 else 0
                rows.append({
                    "Müşteri":              musteri,
                    "Gelir (₺)":            round(gelir, 0),
                    "Ürün Maliyeti (₺)":    round(atfedilen_degisken, 0),
                    "Brüt Katkı (₺)":       round(brut_katki, 0),
                    "Brüt Katkı Marjı (%)": brut_marj,
                    "Sabit Gider Payı (₺)": round(atfedilen_sabit, 0),
                    "Net Kar (₺)":          round(net_kar, 0),
                    "Net Marj (%)":         net_marj,
                })
            else:  # kaynak == "yetersiz"
                # Brüt marj hesaplanamaz — yalnızca gelir + sabit gider payı
                rows.append({
                    "Müşteri":              musteri,
                    "Gelir (₺)":            round(gelir, 0),
                    "Gelir Payı (%)":       round(gelir / toplam_gelir * 100, 1),
                    "Sabit Gider Payı (₺)": round(atfedilen_sabit, 0),
                })

        siralama_sutunu = "Brüt Katkı (₺)" if kaynak != "yetersiz" else "Gelir (₺)"
        result = (pd.DataFrame(rows)
                  .sort_values(siralama_sutunu, ascending=False)
                  .reset_index(drop=True))

        if kaynak == "musteri":
            result.attrs["kaynak"] = "musteri"
            result.attrs["metodoloji_uyarisi"] = (
                "Değişken giderler doğrudan müşteri kaydından, sabit giderler müşteri "
                "sayısına eşit paylaştırılarak atfedilmiştir."
            )
        elif kaynak == "urun":
            result.attrs["kaynak"] = "urun"
            result.attrs["metodoloji_uyarisi"] = (
                "Değişken giderler ürün maliyet oranından, her müşterinin ürün karmasına "
                "göre atfedilmiştir; sabit giderler müşteri sayısına eşit dağıtılmıştır."
            )
        else:
            result.attrs["kaynak"] = "yetersiz"
            result.attrs["veri_yetersiz"] = True
            result.attrs["genel_katki_marji_yuzde"] = (
                round((1 - degisken_gider_toplam / toplam_gelir) * 100, 1)
                if toplam_gelir > 0 else 0.0
            )
            result.attrs["metodoloji_uyarisi"] = (
                "Müşteri bazlı brüt katkı marjı hesaplanamadı: gider kayıtları müşteri "
                "veya ürün ile eşleşmiyor. Sadece gelir ve sabit gider payı gösteriliyor. "
                "Marj için gider satırlarına Müşteri veya Ürün etiketi ekleyin."
            )
        return result

    def _musteri_gider_haritasi(
        self, musteri_indeksi: pd.Index
    ) -> Tuple[str, Dict[str, float]]:
        """Müşteri → değişken gider tutarı sözlüğü ve hangi kaynaktan üretildiği.

        Dönüş: ("musteri"|"urun"|"yetersiz", {müşteri: gider}). "yetersiz"
        için sözlük boştur.
        """
        genel_etiketler = {"", "-", "Belirtilmemiş", "Genel"}
        gider_df = self.df[self.df["Gider"] > 0].copy()
        if gider_df.empty:
            return "yetersiz", {}

        # 1) Doğrudan müşteri gideri
        musteri_gider = gider_df[~gider_df["Müşteri"].isin(genel_etiketler)]
        if not musteri_gider.empty:
            harita = (
                musteri_gider.groupby("Müşteri")["Gider"].sum().to_dict()
            )
            return "musteri", {m: float(harita.get(m, 0.0)) for m in musteri_indeksi}

        # 2) Ürün üzerinden dolaylı eşleşme
        urun_gider = gider_df[~gider_df["Ürün"].isin(genel_etiketler)]
        urun_gelir = self.gelir_df[~self.gelir_df["Ürün"].isin(genel_etiketler)]
        if urun_gider.empty or urun_gelir.empty:
            return "yetersiz", {}

        maliyet_per_urun = urun_gider.groupby("Ürün")["Gider"].sum()
        gelir_per_urun = urun_gelir.groupby("Ürün")["Gelir"].sum()
        ortak_urunler = gelir_per_urun.index.intersection(maliyet_per_urun.index)
        if len(ortak_urunler) == 0:
            return "yetersiz", {}

        maliyet_oran = (
            maliyet_per_urun.reindex(ortak_urunler) /
            gelir_per_urun.reindex(ortak_urunler).replace(0, np.nan)
        ).fillna(0)

        musteri_urun_gelir = (
            urun_gelir[urun_gelir["Ürün"].isin(ortak_urunler)]
            .groupby(["Müşteri", "Ürün"])["Gelir"].sum()
        )
        harita: Dict[str, float] = {m: 0.0 for m in musteri_indeksi}
        for (musteri, urun), gelir in musteri_urun_gelir.items():
            if musteri in harita:
                harita[musteri] += float(gelir * maliyet_oran.get(urun, 0))
        return "urun", harita

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
        """
        Ürün bazında karlılık.

        Metodoloji önceliği (bulunan ilki uygulanır):

        1. **Doğrudan ürün gideri:** Satırda hem Ürün hem Gider > 0 varsa gider
           o ürüne direkt atfedilir. Brüt marj gerçek.
        2. **Yalnız gelir + genel havuz:** Ürün bazında gider yoksa, brüt marj
           kolonu çıkarılır — tablo yalnızca gelir + gelir payı + sabit gider
           payı gösterir; ``attrs["veri_yetersiz"]`` işareti eklenir. Eski
           davranış (değişken gideri gelir payına orantılı dağıtıp tüm ürünler
           için aynı brüt marj göstermek) yanıltıcıydı, kaldırıldı.
        """
        toplam_gelir = float(self.df["Gelir"].sum())
        if toplam_gelir == 0:
            return pd.DataFrame()

        urun_gelir = self.gelir_df.groupby("Ürün")["Gelir"].sum()
        if urun_gelir.empty:
            return pd.DataFrame()

        # Doğrudan ürün gideri var mı?
        genel_etiketler = {"", "-", "Belirtilmemiş", "Genel"}
        gider_df = self.df[self.df["Gider"] > 0].copy()
        urun_gider_df = gider_df[~gider_df["Ürün"].isin(genel_etiketler)]
        urun_gider_map = (
            urun_gider_df.groupby("Ürün")["Gider"].sum().to_dict()
            if not urun_gider_df.empty else {}
        )
        kaynak = "urun" if urun_gider_map else "yetersiz"

        # Sabit/değişken sınıflandırması (net kâr hesabı için hâlâ gerekli)
        sabit_kelimeler = ["kira", "maaş", "amortisman", "sigorta", "abonelik"]
        pattern = "|".join(sabit_kelimeler)
        is_sabit = self.df["Kategori"].str.lower().str.contains(pattern, na=False)
        sabit_gider = float(self.df.loc[is_sabit, "Gider"].sum())
        degisken_gider_toplam = float(self.df.loc[~is_sabit, "Gider"].sum())

        n_urun = urun_gelir.shape[0]
        rows: List[Dict[str, Any]] = []
        for urun, gelir in urun_gelir.items():
            atfedilen_sabit = sabit_gider / max(n_urun, 1)

            if kaynak == "urun":
                atfedilen_degisken = float(urun_gider_map.get(urun, 0.0))
                brut_katki = gelir - atfedilen_degisken
                brut_marj = round(brut_katki / gelir * 100, 1) if gelir > 0 else 0
                net_kar = brut_katki - atfedilen_sabit
                net_marj = round(net_kar / gelir * 100, 1) if gelir > 0 else 0
                rows.append({
                    "Ürün/Hizmet":          urun,
                    "Gelir (₺)":            round(gelir, 0),
                    "Değişken Gider (₺)":   round(atfedilen_degisken, 0),
                    "Brüt Katkı (₺)":       round(brut_katki, 0),
                    "Brüt Katkı Marjı (%)": brut_marj,
                    "Sabit Gider Payı (₺)": round(atfedilen_sabit, 0),
                    "Net Kar (₺)":          round(net_kar, 0),
                    "Net Marj (%)":         net_marj,
                })
            else:
                rows.append({
                    "Ürün/Hizmet":          urun,
                    "Gelir (₺)":            round(gelir, 0),
                    "Gelir Payı (%)":       round(gelir / toplam_gelir * 100, 1),
                    "Sabit Gider Payı (₺)": round(atfedilen_sabit, 0),
                })

        siralama_sutunu = "Brüt Katkı (₺)" if kaynak == "urun" else "Gelir (₺)"
        result = (pd.DataFrame(rows)
                  .sort_values(siralama_sutunu, ascending=False)
                  .reset_index(drop=True))

        if kaynak == "urun":
            result.attrs["kaynak"] = "urun"
            result.attrs["metodoloji_uyarisi"] = (
                "Değişken giderler doğrudan ürün kaydından, sabit giderler ürün "
                "sayısına eşit paylaştırılarak atfedilmiştir."
            )
        else:
            result.attrs["kaynak"] = "yetersiz"
            result.attrs["veri_yetersiz"] = True
            result.attrs["genel_katki_marji_yuzde"] = (
                round((1 - degisken_gider_toplam / toplam_gelir) * 100, 1)
                if toplam_gelir > 0 else 0.0
            )
            result.attrs["metodoloji_uyarisi"] = (
                "Ürün bazlı brüt katkı marjı hesaplanamadı: gider satırları ürün "
                "ile eşleşmiyor. Sadece gelir ve sabit gider payı gösteriliyor. "
                "Marj için gider satırlarına Ürün etiketi (COGS) ekleyin."
            )
        return result

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
# CAC / LTV ANALİZİ (P1.7)
# ─────────────────────────────────────────────

class CACLTVAnalysis:
    """
    CAC (Customer Acquisition Cost) ve LTV (Lifetime Value) hesabı.

    Veri modeli:
      - PAZARLAMA GİDERİ: opsiyonel bool sütun "PazarlamaGideri" varsa onu
        kullan; yoksa Kategori adında "pazarlama", "reklam", "marketing",
        "ads" gibi anahtar kelimeler geçenleri pazarlama say.
      - MÜŞTERİ KAZANIM TARİHİ: müşterinin ilk gelir işlemi tarihi.
      - CHURN: son 90 günde işlem yapmayan müşteri sayısı / toplam ×
        (aylık ort. için 3'e böl). Yaklaşımdır — abonelik modeli için net.

    Formüller:
      CAC = Toplam Pazarlama Gideri / Yeni Kazanılan Müşteri Sayısı
      LTV = Ortalama Aylık Gelir/Müşteri × Brüt Marj × Müşteri Ömrü (ay)
      Müşteri Ömrü ≈ 1 / Aylık Churn (üst sınır 60 ay = 5 yıl)
      Sağlık göstergesi: LTV / CAC ≥ 3 → 🟢 Sağlıklı

    Şeffaflık: veri yetersizse "hesaplanamadı" + sebep döner; sahte sayı
    üretmez.
    """

    _PAZARLAMA_ANAHTARLAR = (
        "pazarlama", "reklam", "marketing", "ads",
        "google ads", "meta ads", "sosyal medya",
    )

    def __init__(self, df: pd.DataFrame):
        self.df = prepare_customer_data(df)
        self.gelir_df = self.df[self.df["Gelir"] > 0].copy()

    def _pazarlama_mask(self) -> pd.Series:
        """Bool mask: hangi satırlar pazarlama gideri?"""
        if "PazarlamaGideri" in self.df.columns:
            return self.df["PazarlamaGideri"].astype(bool)
        kat = self.df["Kategori"].astype(str).str.lower()
        pattern = "|".join(self._PAZARLAMA_ANAHTARLAR)
        return kat.str.contains(pattern, na=False, regex=True)

    def pazarlama_giderleri_aylik(self) -> pd.DataFrame:
        """Aylık pazarlama gideri toplamı."""
        pg_mask = self._pazarlama_mask() & (self.df["Gider"] > 0)
        pg = self.df[pg_mask].copy()
        if pg.empty:
            return pd.DataFrame(columns=["YilAy", "PazarlamaGideri"])
        pg["YilAy"] = pd.to_datetime(pg["Tarih"]).dt.to_period("M").astype(str)
        return (pg.groupby("YilAy")["Gider"]
                  .sum().reset_index(name="PazarlamaGideri"))

    def yeni_musteriler_aylik(self) -> pd.DataFrame:
        """Her müşteri ilk gelir işlemi ayında kazanılmış sayılır."""
        if self.gelir_df.empty:
            return pd.DataFrame(columns=["YilAy", "YeniMusteri"])
        ilk = (self.gelir_df.groupby("Müşteri")["Tarih"].min()
               .reset_index())
        ilk["YilAy"] = pd.to_datetime(ilk["Tarih"]).dt.to_period("M").astype(str)
        # "Genel"/"Belirtilmemiş" gibi placeholder isimleri say ama gerçek olmadıklarını rapor et
        return ilk.groupby("YilAy").size().reset_index(name="YeniMusteri")

    def cac(self) -> Dict[str, Any]:
        """
        Ortalama CAC (tüm dönem) + aylık kırılım.
        Veri yetersizse hesaplandi=False, sebep verir.
        """
        pg_df = self.pazarlama_giderleri_aylik()
        yc_df = self.yeni_musteriler_aylik()

        if pg_df.empty:
            return {
                "hesaplandi": False,
                "sebep": (
                    "Pazarlama gideri verisi bulunamadı. Kategori adında "
                    "'pazarlama', 'reklam', 'marketing' veya 'ads' geçen "
                    "gider kayıtları veya opsiyonel 'PazarlamaGideri' bool "
                    "sütunu ekleyin."
                ),
            }
        if yc_df.empty:
            return {
                "hesaplandi": False,
                "sebep": "Müşteri sütununda geçerli müşteri kayıtları yok.",
            }

        toplam_pg   = float(pg_df["PazarlamaGideri"].sum())
        toplam_yeni = int(yc_df["YeniMusteri"].sum())
        if toplam_yeni <= 0:
            return {
                "hesaplandi": False,
                "sebep": "Kazanılan yeni müşteri sayısı 0; CAC hesaplanamaz.",
            }

        cac_avg = round(toplam_pg / toplam_yeni, 2)
        aylik = (pg_df.merge(yc_df, on="YilAy", how="outer")
                       .fillna(0)
                       .sort_values("YilAy")
                       .reset_index(drop=True))
        aylik["CAC"] = aylik.apply(
            lambda r: round(r["PazarlamaGideri"] / r["YeniMusteri"], 2)
                      if r["YeniMusteri"] > 0 else None,
            axis=1,
        )
        return {
            "hesaplandi": True,
            "toplam_pazarlama_gideri": round(toplam_pg, 2),
            "toplam_yeni_musteri":     toplam_yeni,
            "ortalama_cac":            cac_avg,
            "aylik_cac":               aylik,
        }

    def churn_rate_aylik(self) -> float:
        """
        Yaklaşık aylık churn oranı:
          son 90 gün içinde işlem yapmayan müşteri sayısı / toplam × (1/3)
        Not: Abonelik olmayan iş modeli için üst sınır tahmin.
        """
        if self.gelir_df.empty:
            return 0.0
        son_tarih = self.gelir_df["Tarih"].max()
        son_islem = self.gelir_df.groupby("Müşteri")["Tarih"].max()
        gecen = (son_tarih - son_islem).dt.days
        kayip = int((gecen > 90).sum())
        toplam = len(son_islem)
        if toplam == 0:
            return 0.0
        return round(kayip / toplam / 3.0, 4)

    def ltv(self, brut_marj_pct: Optional[float] = None) -> Dict[str, Any]:
        """
        LTV = Ortalama Aylık Gelir/Müşteri × Brüt Marj × Müşteri Ömrü (ay)
        brut_marj_pct verilmezse marj %100 varsayılır (LTV üst sınırı).
        """
        if self.gelir_df.empty:
            return {"hesaplandi": False, "sebep": "Gelir verisi yok."}

        df = self.gelir_df.copy()
        df["YilAy"] = pd.to_datetime(df["Tarih"]).dt.to_period("M").astype(str)
        aylik_gelir_musteri = df.groupby(["YilAy", "Müşteri"])["Gelir"].sum()
        if aylik_gelir_musteri.empty:
            return {"hesaplandi": False, "sebep": "Aylık müşteri geliri boş."}
        ort_aylik_musteri = float(aylik_gelir_musteri.mean())

        churn_a = self.churn_rate_aylik()
        omur_ay = 24.0 if churn_a <= 0 else min(1.0 / churn_a, 60.0)

        marj = (brut_marj_pct if brut_marj_pct is not None else 100.0) / 100.0
        ltv_val = round(ort_aylik_musteri * marj * omur_ay, 2)

        return {
            "hesaplandi":                       True,
            "ortalama_aylik_gelir_per_musteri": round(ort_aylik_musteri, 2),
            "aylik_churn_orani":                churn_a,
            "musteri_omru_ay_tahmin":           round(omur_ay, 1),
            "brut_marj_kullanilan":             brut_marj_pct if brut_marj_pct is not None else "gelir_ustunden_100",
            "ltv":                              ltv_val,
        }

    def cac_ltv_ratio(self, brut_marj_pct: Optional[float] = None) -> Dict[str, Any]:
        """
        LTV / CAC — sağlıklı iş modeli için ≥3 olması beklenir.
        Eksik veride hesaplandi=False.
        """
        cac_r = self.cac()
        ltv_r = self.ltv(brut_marj_pct)
        if not cac_r.get("hesaplandi") or not ltv_r.get("hesaplandi"):
            return {
                "hesaplandi": False,
                "sebep": "CAC veya LTV hesaplanamadı; alt sonuçlarda detay var.",
                "cac": cac_r,
                "ltv": ltv_r,
            }
        cac_val = cac_r["ortalama_cac"]
        ltv_val = ltv_r["ltv"]
        if cac_val <= 0:
            return {"hesaplandi": False, "sebep": "CAC değeri 0."}

        ratio = round(ltv_val / cac_val, 2)
        durum = ("🟢 Sağlıklı" if ratio >= 3.0 else
                 "🟡 Dikkat"   if ratio >= 1.0 else
                 "🔴 Zayıf")
        return {
            "hesaplandi": True,
            "ltv":         ltv_val,
            "cac":         cac_val,
            "ratio":       ratio,
            "durum":       durum,
            "referans": (
                "Sağlıklı iş modeli: LTV/CAC ≥ 3. Geri dönüş süresi: "
                "CAC / (aylık gelir × brüt marj) ≈ ay."
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
        self.cac_ltv  = CACLTVAnalysis(df)

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

    def full_report(self, brut_marj_pct: Optional[float] = None) -> Dict[str, Any]:
        """
        brut_marj_pct: LTV hesabında kullanılacak brüt marj (%).
                       Verilmezse LTV üst-sınır (marj %100) hesabı yapılır.
        """
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
            "cac_ltv":          self.cac_ltv.cac_ltv_ratio(brut_marj_pct),
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

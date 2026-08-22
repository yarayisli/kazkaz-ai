"""
KazKaz AI - Finansal Analiz Motoru (Core)
==========================================
Modüller:
  - DataLoader     : CSV / Excel / Google Sheets veri yükleme
  - RevenueAnalysis: Gelir analizi
  - ExpenseAnalysis: Gider analizi
  - ProfitAnalysis : Karlılık analizi
  - HealthScore    : Finansal sağlık skoru (0-100)
  - FinancialEngine: Tüm modülleri birleştiren ana sınıf

Bağımlılıklar: pandas, numpy, openpyxl, gspread, oauth2client
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
import warnings
warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────
# 1. VERİ YÜKLEYICI
# ─────────────────────────────────────────────

class DataLoader:
    """
    CSV, Excel veya Google Sheets'ten veri yükler.
    Beklenen sütunlar: Tarih, Kategori, Gelir, Gider
    """

    REQUIRED_COLUMNS = {"Tarih", "Kategori", "Gelir", "Gider"}

    @staticmethod
    def from_csv(filepath: str) -> pd.DataFrame:
        df = pd.read_csv(filepath)
        return DataLoader._clean(df)

    @staticmethod
    def from_excel(filepath: str, sheet_name: int = 0) -> pd.DataFrame:
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        return DataLoader._clean(df)

    @staticmethod
    def from_google_sheets(sheet_url: str, credentials_json: str) -> pd.DataFrame:
        """
        credentials_json: Google Service Account JSON dosyasının yolu.
        """
        try:
            import gspread
            from oauth2client.service_account import ServiceAccountCredentials
        except ImportError:
            raise ImportError("gspread ve oauth2client kurulu olmalıdır: pip install gspread oauth2client")

        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_json, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(sheet_url).sheet1
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        return DataLoader._clean(df)

    @staticmethod
    def from_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Hazır bir DataFrame'i doğrulayıp temizler."""
        return DataLoader._clean(df)

    @staticmethod
    def _clean(df: pd.DataFrame) -> pd.DataFrame:
        # Sütun adlarını normalize et (baş/son boşluk temizle)
        df.columns = df.columns.str.strip()

        # Gerekli sütun kontrolü
        missing = DataLoader.REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Eksik sütunlar: {missing}. Gerekli: {DataLoader.REQUIRED_COLUMNS}")

        # Tarih dönüşümü
        df["Tarih"] = pd.to_datetime(df["Tarih"], errors="coerce")
        df = df.dropna(subset=["Tarih"])

        # Sayısal dönüşüm
        df["Gelir"] = pd.to_numeric(df["Gelir"], errors="coerce").fillna(0)
        df["Gider"] = pd.to_numeric(df["Gider"], errors="coerce").fillna(0)

        # Türetilmiş sütunlar
        df["YilAy"] = df["Tarih"].dt.to_period("M").astype(str)
        df["Yil"] = df["Tarih"].dt.year
        df["Ay"] = df["Tarih"].dt.month
        df["NetKar"] = df["Gelir"] - df["Gider"]

        return df.sort_values("Tarih").reset_index(drop=True)


# ─────────────────────────────────────────────
# 2. GELİR ANALİZİ
# ─────────────────────────────────────────────

class RevenueAnalysis:
    """Gelir tabanlı tüm analizleri üretir."""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def total_revenue(self) -> float:
        """Toplam gelir."""
        return float(self.df["Gelir"].sum())

    def monthly_revenue(self) -> pd.DataFrame:
        """Aylık gelir özeti."""
        return (
            self.df.groupby("YilAy")["Gelir"]
            .sum()
            .reset_index()
            .rename(columns={"YilAy": "Dönem", "Gelir": "Toplam Gelir"})
        )

    def revenue_by_category(self) -> pd.DataFrame:
        """Kategoriye göre gelir dağılımı."""
        return (
            self.df.groupby("Kategori")["Gelir"]
            .sum()
            .reset_index()
            .sort_values("Gelir", ascending=False)
            .rename(columns={"Gelir": "Toplam Gelir"})
        )

    def top_revenue_category(self) -> Dict[str, Any]:
        """En karlı kategori."""
        cat_df = self.revenue_by_category()
        if cat_df.empty:
            return {"kategori": None, "gelir": 0}
        top = cat_df.iloc[0]
        return {"kategori": top["Kategori"], "gelir": float(top["Toplam Gelir"])}

    def revenue_growth_rate(self) -> pd.DataFrame:
        """Aylık gelir büyüme oranı (%)."""
        monthly = self.monthly_revenue().set_index("Dönem")["Toplam Gelir"]
        growth = monthly.pct_change() * 100
        return growth.reset_index().rename(columns={"Toplam Gelir": "Büyüme Oranı (%)"})

    def average_monthly_revenue(self) -> float:
        """Ortalama aylık gelir."""
        monthly = self.monthly_revenue()
        return float(monthly["Toplam Gelir"].mean()) if not monthly.empty else 0.0

    def summary(self) -> Dict[str, Any]:
        monthly = self.monthly_revenue()
        growth = self.revenue_growth_rate()
        avg_growth = growth["Büyüme Oranı (%)"].mean()
        return {
            "toplam_gelir": self.total_revenue(),
            "ortalama_aylik_gelir": self.average_monthly_revenue(),
            "en_karli_kategori": self.top_revenue_category(),
            "ortalama_buyume_orani": round(float(avg_growth), 2) if not np.isnan(avg_growth) else 0.0,
            "ay_sayisi": len(monthly),
        }


# ─────────────────────────────────────────────
# 3. GİDER ANALİZİ
# ─────────────────────────────────────────────

class ExpenseAnalysis:
    """Gider tabanlı tüm analizleri üretir."""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def total_expense(self) -> float:
        """Toplam gider."""
        return float(self.df["Gider"].sum())

    def monthly_expense(self) -> pd.DataFrame:
        """Aylık gider özeti."""
        return (
            self.df.groupby("YilAy")["Gider"]
            .sum()
            .reset_index()
            .rename(columns={"YilAy": "Dönem", "Gider": "Toplam Gider"})
        )

    def expense_by_category(self) -> pd.DataFrame:
        """Kategoriye göre gider dağılımı."""
        return (
            self.df.groupby("Kategori")["Gider"]
            .sum()
            .reset_index()
            .sort_values("Gider", ascending=False)
            .rename(columns={"Gider": "Toplam Gider"})
        )

    def top_expense_category(self) -> Dict[str, Any]:
        """En yüksek gider kalemi."""
        cat_df = self.expense_by_category()
        if cat_df.empty:
            return {"kategori": None, "gider": 0}
        top = cat_df.iloc[0]
        return {"kategori": top["Kategori"], "gider": float(top["Toplam Gider"])}

    def fixed_vs_variable(self, fixed_keywords: Optional[list] = None) -> Dict[str, float]:
        """
        Sabit/değişken gider ayrımı.

        ÖNCELİK: Veride 'Gider Tipi' sütunu varsa ve doluysa onu kullan
        (kullanıcı gerçek sınıflandırma yapmış).
        Yoksa anahtar kelime tabanlı tespit (yaklaşık).

        fixed_keywords: sabit gider kategorilerini içeren anahtar kelimeler.
        Varsayılan: ['kira', 'maaş', 'amortisman', 'sigorta']
        """
        # Yöntem 1: Kullanıcı Gider Tipi işaretlemişse öncelikli
        if "Gider Tipi" in self.df.columns and self.df["Gider Tipi"].astype(str).str.strip().any():
            gt = self.df["Gider Tipi"].astype(str).str.strip()
            is_fixed = gt.isin(["Sabit"])
            is_var   = gt.isin(["Değişken", "COGS"])
            sabit    = float(self.df.loc[is_fixed, "Gider"].sum())
            degisken = float(self.df.loc[is_var,   "Gider"].sum())
            # Vergi + Finansal + CapEx = "diger"
            diger    = float(self.df.loc[~(is_fixed | is_var), "Gider"].sum())
            return {
                "sabit_gider": sabit,
                "degisken_gider": degisken,
                "diger_gider": diger,
                "kaynak": "kullanici_isaretlemesi",
            }

        # Yöntem 2: Anahtar kelime tabanlı (yaklaşık)
        if fixed_keywords is None:
            fixed_keywords = ["kira", "maaş", "amortisman", "sigorta", "abonelik"]

        pattern = "|".join(fixed_keywords)
        is_fixed = self.df["Kategori"].str.lower().str.contains(pattern, na=False)
        sabit = float(self.df.loc[is_fixed, "Gider"].sum())
        degisken = float(self.df.loc[~is_fixed, "Gider"].sum())
        return {
            "sabit_gider": sabit,
            "degisken_gider": degisken,
            "diger_gider": 0.0,
            "kaynak": "anahtar_kelime_tahmini",
        }

    def expense_growth_rate(self) -> pd.DataFrame:
        """Aylık gider büyüme oranı (%)."""
        monthly = self.monthly_expense().set_index("Dönem")["Toplam Gider"]
        growth = monthly.pct_change() * 100
        return growth.reset_index().rename(columns={"Toplam Gider": "Büyüme Oranı (%)"})

    def summary(self) -> Dict[str, Any]:
        fv = self.fixed_vs_variable()
        total = self.total_expense()
        return {
            "toplam_gider": total,
            "en_yuksek_gider_kalemi": self.top_expense_category(),
            "sabit_gider": fv["sabit_gider"],
            "degisken_gider": fv["degisken_gider"],
            "sabit_gider_orani": round(fv["sabit_gider"] / total * 100, 2) if total > 0 else 0,
        }


# ─────────────────────────────────────────────
# 4. KARLILIK ANALİZİ
# ─────────────────────────────────────────────

class ProfitAnalysis:
    """Net kar ve karlılık marjı analizleri."""

    def __init__(self, df: pd.DataFrame):
        self.df = df

    def total_profit(self) -> float:
        """Toplam net kar."""
        return float(self.df["NetKar"].sum())

    def profit_margin(self) -> float:
        """Genel karlılık marjı (%)."""
        total_revenue = self.df["Gelir"].sum()
        if total_revenue == 0:
            return 0.0
        return round(float(self.df["NetKar"].sum() / total_revenue * 100), 2)

    def monthly_profit(self) -> pd.DataFrame:
        """Aylık net kar tablosu."""
        return (
            self.df.groupby("YilAy")
            .agg(Gelir=("Gelir", "sum"), Gider=("Gider", "sum"))
            .assign(NetKar=lambda x: x["Gelir"] - x["Gider"])
            .assign(KarMarji=lambda x: (x["NetKar"] / x["Gelir"].replace(0, np.nan) * 100).round(2))
            .reset_index()
            .rename(columns={"YilAy": "Dönem"})
        )

    def profit_by_category(self) -> pd.DataFrame:
        """Kategoriye göre karlılık dağılımı."""
        return (
            self.df.groupby("Kategori")
            .agg(Gelir=("Gelir", "sum"), Gider=("Gider", "sum"))
            .assign(NetKar=lambda x: x["Gelir"] - x["Gider"])
            .reset_index()
            .sort_values("NetKar", ascending=False)
        )

    def profit_trend(self) -> str:
        """Kar trendi: 'Artış', 'Düşüş' veya 'Stabil'."""
        monthly = self.monthly_profit()
        if len(monthly) < 2:
            return "Yetersiz Veri"
        ilk_yari = monthly.iloc[: len(monthly) // 2]["NetKar"].mean()
        ikinci_yari = monthly.iloc[len(monthly) // 2 :]["NetKar"].mean()
        fark = ikinci_yari - ilk_yari
        if fark > ilk_yari * 0.05:
            return "Artış"
        elif fark < -ilk_yari * 0.05:
            return "Düşüş"
        return "Stabil"

    def summary(self) -> Dict[str, Any]:
        return {
            "toplam_net_kar": self.total_profit(),
            "kar_marji": self.profit_margin(),
            "kar_trendi": self.profit_trend(),
        }


# ─────────────────────────────────────────────
# 5. FİNANSAL SAĞLIK SKORU
# ─────────────────────────────────────────────

class HealthScore:
    """
    0-100 arası finansal sağlık skoru üretir.

    5 boyut (customer verilirse):
      - Karlılık marjı          : %25
      - Gelir büyüme oranı      : %20
      - Gider kontrol oranı     : %20
      - Nakit sürdürülebilirliği: %20
      - Konsantrasyon riski     : %15   (top müşteri gelir payı)

    4 boyut (customer verilmezse — backward compat):
      - Karlılık %30, Büyüme %25, Gider %25, Nakit %20
    """

    WEIGHTS_5D = {
        "karlilik": 0.25,
        "buyume": 0.20,
        "gider_kontrolu": 0.20,
        "nakit": 0.20,
        "konsantrasyon": 0.15,
    }

    WEIGHTS_4D = {
        "karlilik": 0.30,
        "buyume": 0.25,
        "gider_kontrolu": 0.25,
        "nakit": 0.20,
    }

    def __init__(
        self,
        profit: ProfitAnalysis,
        revenue: RevenueAnalysis,
        expense: ExpenseAnalysis,
        customer: Optional[Any] = None,
    ):
        self.profit = profit
        self.revenue = revenue
        self.expense = expense
        self.customer = customer
        self.WEIGHTS = self.WEIGHTS_5D if customer is not None else self.WEIGHTS_4D

    # --- Alt skor hesaplayıcılar (0-100) ---

    # ── Sektör hedef marjı (varsayılan)
    # Sektör verilirse override edilir; yoksa Türkiye KOBİ ortalaması %10 hedef, %20 mükemmel
    _default_target_margin: float = 10.0   # %10 → 60 puan
    _default_top_margin:    float = 20.0   # %20+ → 100 puan

    def set_sector_targets(self, hedef_marj: float, ust_marj: float):
        """Sektör bazlı marj eşiklerini ayarla."""
        self._default_target_margin = hedef_marj
        self._default_top_margin    = ust_marj

    def _karlilik_skoru(self) -> float:
        """
        Kar marjına göre skor (0-100).
        - Negatif marj → 0
        - Hedef marj (varsayılan %10) → 60 puan
        - Üst marj (varsayılan %20) → 100 puan
        - Arada doğrusal interpolasyon
        Bu yaklaşım her marjı ayrıştırır (eski clip*5 hatası çözüldü).
        """
        margin = self.profit.profit_margin()
        if margin <= 0:
            return 0.0
        if margin >= self._default_top_margin:
            return 100.0
        if margin >= self._default_target_margin:
            # Hedef ile üst marj arası: 60→100
            oran = (margin - self._default_target_margin) / \
                   (self._default_top_margin - self._default_target_margin)
            return round(60 + oran * 40, 1)
        # 0 ile hedef arası: 0→60
        oran = margin / self._default_target_margin
        return round(oran * 60, 1)

    def _buyume_skoru(self) -> float:
        """
        Gelir büyüme skoru (0-100).

        UYARI: Nominal büyüme kullanılır. 2024-2025 Türkiye'sinde
        yüksek enflasyon nedeniyle nominal büyüme yanıltıcı olabilir
        (%20 büyüme aslında enflasyon altında kalıp reel küçülme olabilir).
        TÜFE düzeltmesi ileride eklenecek.

        Metodoloji:
        - 12+ ay verisi varsa: YoY (yıllık aynı ay karşılaştırması) — mevsimsel gürültüden arındırılmış
        - 12 aydan az: MoM ortalaması (daha az güvenilir)
        - Eşikler yumuşak eğri: <0% → 0, 15% → 60, 30% → 100
        """
        monthly = self.revenue.monthly_revenue()
        if monthly.empty or len(monthly) < 2:
            return 50.0

        buyume_pct = self._compute_growth(monthly)

        # Negatif büyüme
        if buyume_pct <= 0:
            # -20% ve altı → 0, 0% → 40
            return round(float(np.clip(40 + buyume_pct * 2, 0, 40)), 1)

        # Pozitif büyüme: 0% → 40, 10% → 55, 20% → 80, 30%+ → 100
        if buyume_pct >= 30:
            return 100.0
        if buyume_pct >= 20:
            return round(80 + (buyume_pct - 20) / 10 * 20, 1)
        if buyume_pct >= 10:
            return round(55 + (buyume_pct - 10) / 10 * 25, 1)
        return round(40 + (buyume_pct / 10) * 15, 1)

    @staticmethod
    def _compute_growth(monthly: pd.DataFrame) -> float:
        """
        12+ ay verisi varsa YoY, yoksa MoM ortalaması.
        Mevsimsellikten arınmış büyüme.
        """
        rev = monthly["Toplam Gelir"].values
        n = len(rev)
        if n >= 13:
            # YoY: son 3 ay ile 12 ay önceki 3 ayı karşılaştır
            son_3 = rev[-3:].mean()
            eski_3 = rev[-15:-12].mean()
            if eski_3 <= 0:
                return 0.0
            return round((son_3 - eski_3) / eski_3 * 100, 2)
        else:
            # Yetersiz veri: MoM ortalaması, ama sinyal zayıf
            pct = pd.Series(rev).pct_change().dropna() * 100
            return round(float(pct.mean()) if not pct.empty else 0.0, 2)

    def _gider_kontrolu_skoru(self) -> float:
        """Gider/Gelir oranına göre skor. Düşük oran → yüksek skor."""
        total_rev = self.revenue.total_revenue()
        total_exp = self.expense.total_expense()
        if total_rev == 0:
            return 0.0
        ratio = total_exp / total_rev  # 0'a yakın iyi
        # ratio 0 → 100, ratio 1 → 0, ratio >1 → 0
        score = max(0, (1 - ratio) * 100)
        return float(np.clip(score, 0, 100))

    def _nakit_skoru(self) -> float:
        """
        Nakit sürdürülebilirliği skoru (0-100).
        UYARI: Bu skor NET KÂR üzerinden hesaplanır, gerçek NAKİT değil.
        Vadeli tahsilat/ödeme farklılıkları göz önüne alınmaz.
        Gerçek nakit analizi için cashflow_engine.CashFlowScorer kullanılmalı.

        Metodoloji:
        - Son 3 ayın net kâr trendi + istikrarı
        - Toplam gelire oranla marj sağlamlığı
        """
        monthly = self.profit.monthly_profit()
        if monthly.empty or len(monthly) < 2:
            return 50.0

        son_n = min(3, len(monthly))
        son_donem = monthly.tail(son_n)
        ort_kar   = son_donem["NetKar"].mean()

        # Aynı dönemin gelir tabanı
        toplam_gelir_son = son_donem["Gelir"].sum() if "Gelir" in son_donem.columns else 0
        if toplam_gelir_son <= 0:
            return 0.0

        # Marj yüzdesi
        kar_marj = (ort_kar * son_n) / toplam_gelir_son * 100

        # Negatif marj → 0-40 arası
        if kar_marj < 0:
            # -20% ve altı → 0, 0% → 40
            return round(float(np.clip(40 + kar_marj * 2, 0, 40)), 1)

        # Pozitif marj: 0% → 40, 5% → 60, 15% → 90, 20%+ → 100
        if kar_marj >= 20:
            base = 100.0
        elif kar_marj >= 15:
            base = 90 + (kar_marj - 15) / 5 * 10
        elif kar_marj >= 5:
            base = 60 + (kar_marj - 5) / 10 * 30
        else:
            base = 40 + (kar_marj / 5) * 20

        # İstikrar bonusu/cezası: son dönemler pozitif mi negatif mi?
        pozitif_ay = (son_donem["NetKar"] > 0).sum()
        if pozitif_ay == son_n:
            istikrar = 5   # tüm aylar pozitif → +5
        elif pozitif_ay == 0:
            istikrar = -15  # tüm aylar negatif → -15
        else:
            istikrar = -5   # karışık → -5

        return round(float(np.clip(base + istikrar, 0, 100)), 1)

    def _konsantrasyon_skoru(self) -> float:
        """
        Müşteri konsantrasyon riski skoru (0-100).
        Yüksek konsantrasyon = düşük skor (tek müşteri kaybı = büyük risk).

        Kaynak: customer_engine.CustomerAnalysis.customer_concentration()
        Sinyal: top %20 müşterinin toplam gelirdeki payı (top20_pct_pay).

        Eşikler:
        - Müşteri sayısı < 3 → 0-30 (yapısal tekilik, veriye bakmadan riskli)
        - top20 payı ≤ %40 → 100  (çok dağılmış, sağlıklı)
        - %40-60 → 90-60           (normal)
        - %60-80 → 60-30           (riskli — mevcut mühendisliğin de "risk var" eşiği)
        - > %80 → 30-0             (kritik bağımlılık)

        customer None ise 50 döner (nötr — skor dışı bırakmaz, ama yönlendirmez).
        """
        if self.customer is None:
            return 50.0

        try:
            conc = self.customer.customer_concentration()
        except Exception:
            return 50.0
        if not conc:
            return 50.0

        n_musteri = conc.get("toplam_musteri", 0)
        top20 = conc.get("top20_pct_pay", 100.0)

        if n_musteri < 3:
            return round(max(0.0, 30.0 - (3 - n_musteri) * 10.0), 1)

        if top20 <= 40:
            return 100.0
        if top20 <= 60:
            return round(90 - (top20 - 40) / 20 * 30, 1)
        if top20 <= 80:
            return round(60 - (top20 - 60) / 20 * 30, 1)
        return round(max(0.0, 30 - (top20 - 80) / 20 * 30), 1)

    def calculate(self) -> Dict[str, Any]:
        """Genel sağlık skorunu ve alt skorları döndürür."""
        alt_skorlar = {
            "karlilik": round(self._karlilik_skoru(), 1),
            "buyume": round(self._buyume_skoru(), 1),
            "gider_kontrolu": round(self._gider_kontrolu_skoru(), 1),
            "nakit": round(self._nakit_skoru(), 1),
        }
        if "konsantrasyon" in self.WEIGHTS:
            alt_skorlar["konsantrasyon"] = round(self._konsantrasyon_skoru(), 1)

        genel_skor = sum(
            alt_skorlar[k] * self.WEIGHTS[k] for k in self.WEIGHTS
        )
        genel_skor = round(genel_skor, 1)

        kategori = self._kategori(genel_skor)

        uyarilar = [
            "Bu skor nominal değerlere dayanır — enflasyon düzeltmesi uygulanmamıştır.",
            "Nakit skoru NET KÂR üzerinden hesaplanır, gerçek nakit pozisyonu değildir. "
            "Vadeli tahsilat/ödeme varsa gerçek nakit farklı olabilir.",
        ]
        if "konsantrasyon" not in self.WEIGHTS:
            uyarilar.append(
                "Konsantrasyon riski boyutu skorlanmadı (müşteri verisi verilmedi). "
                "Müşteri sütununu yüklerseniz 5 boyutlu skor devreye girer."
            )

        metodoloji = {f"{k}_agirlik": self.WEIGHTS[k] for k in self.WEIGHTS}
        metodoloji["not"] = "Ağırlıklı toplam formülü: Σ (alt_skor × ağırlık)"
        metodoloji["boyut_sayisi"] = len(self.WEIGHTS)

        return {
            "skor": genel_skor,
            "kategori": kategori,
            "alt_skorlar": alt_skorlar,
            "aciklama": self._aciklama(kategori),
            "uyarilar": uyarilar,
            "metodoloji": metodoloji,
        }

    @staticmethod
    def _kategori(skor: float) -> str:
        if skor >= 80:
            return "Mükemmel"
        elif skor >= 60:
            return "İyi"
        elif skor >= 40:
            return "Orta"
        elif skor >= 20:
            return "Zayıf"
        return "Kritik"

    @staticmethod
    def _aciklama(kategori: str) -> str:
        aciklamalar = {
            "Mükemmel": "Şirket finansal olarak çok güçlü. Büyüme ve yatırım için uygun.",
            "İyi": "Finansal durum sağlıklı. Küçük iyileştirmelerle daha iyi olabilir.",
            "Orta": "Dikkat edilmesi gereken alanlar var. Gider kontrolü önerilir.",
            "Zayıf": "Finansal riskler mevcut. Acil önlemler alınmalı.",
            "Kritik": "Ciddi finansal sorunlar var. Derhal müdahale gerekiyor.",
        }
        return aciklamalar.get(kategori, "")


# ─────────────────────────────────────────────
# 6. ANA FİNANSAL MOTor
# ─────────────────────────────────────────────

class FinancialEngine:
    """
    KazKaz AI'nın tüm analiz modüllerini bir araya getiren ana sınıf.

    Kullanım:
        engine = FinancialEngine.from_csv("veri.csv")
        rapor = engine.full_report()
    """

    def __init__(self, df: pd.DataFrame):
        self.df = DataLoader.from_dataframe(df)
        self.revenue = RevenueAnalysis(self.df)
        self.expense = ExpenseAnalysis(self.df)
        self.profit = ProfitAnalysis(self.df)

        # Müşteri sütunu varsa 5. boyutu (konsantrasyon riski) devreye al.
        # Yoksa HealthScore 4 boyutta çalışır (backward compat).
        self.customer = None
        if "Müşteri" in self.df.columns or "Musteri" in self.df.columns:
            try:
                from customer_engine import CustomerAnalysis
                self.customer = CustomerAnalysis(self.df)
            except Exception:
                self.customer = None

        self.health = HealthScore(
            self.profit, self.revenue, self.expense, self.customer
        )

    # --- Fabrika metodları ---

    @classmethod
    def from_csv(cls, filepath: str) -> "FinancialEngine":
        df = DataLoader.from_csv(filepath)
        return cls(df)

    @classmethod
    def from_excel(cls, filepath: str, sheet_name: int = 0) -> "FinancialEngine":
        df = DataLoader.from_excel(filepath, sheet_name)
        return cls(df)

    @classmethod
    def from_google_sheets(cls, sheet_url: str, credentials_json: str) -> "FinancialEngine":
        df = DataLoader.from_google_sheets(sheet_url, credentials_json)
        return cls(df)

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> "FinancialEngine":
        return cls(df)

    # --- Özet rapor ---

    def full_report(self) -> Dict[str, Any]:
        """Tüm analizlerin birleşik özet raporu."""
        return {
            "gelir": self.revenue.summary(),
            "gider": self.expense.summary(),
            "karlilik": self.profit.summary(),
            "saglik_skoru": self.health.calculate(),
        }

    def scenario_analysis(
        self,
        gelir_artis_orani: float = 0.0,
        gider_azalis_orani: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Senaryo analizi.
        gelir_artis_orani : 0.10 → %10 gelir artışı
        gider_azalis_orani: 0.05 → %5 gider azalışı
        """
        mevcut_gelir = self.revenue.total_revenue()
        mevcut_gider = self.expense.total_expense()

        yeni_gelir = mevcut_gelir * (1 + gelir_artis_orani)
        yeni_gider = mevcut_gider * (1 - gider_azalis_orani)
        yeni_net_kar = yeni_gelir - yeni_gider
        yeni_kar_marji = (yeni_net_kar / yeni_gelir * 100) if yeni_gelir > 0 else 0

        mevcut_net_kar = self.profit.total_profit()
        mevcut_kar_marji = self.profit.profit_margin()

        return {
            "mevcut": {
                "gelir": round(mevcut_gelir, 2),
                "gider": round(mevcut_gider, 2),
                "net_kar": round(mevcut_net_kar, 2),
                "kar_marji": round(mevcut_kar_marji, 2),
            },
            "senaryo": {
                "gelir": round(yeni_gelir, 2),
                "gider": round(yeni_gider, 2),
                "net_kar": round(yeni_net_kar, 2),
                "kar_marji": round(yeni_kar_marji, 2),
            },
            "degisim": {
                "gelir_farki": round(yeni_gelir - mevcut_gelir, 2),
                "kar_farki": round(yeni_net_kar - mevcut_net_kar, 2),
            },
        }


# ─────────────────────────────────────────────
# ÖRNEK KULLANIM (test)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # Örnek veri
    sample_data = pd.DataFrame({
        "Tarih": [
            "2024-01", "2024-01", "2024-02", "2024-02",
            "2024-03", "2024-03", "2024-04", "2024-04",
        ],
        "Kategori": [
            "Satış", "Pazarlama", "Satış", "Kira",
            "Satış", "Personel", "Satış", "Pazarlama",
        ],
        "Gelir":  [120000, 0,      140000, 0,      160000, 0,      180000, 0],
        "Gider":  [0,      15000,  0,      8000,   0,      45000,  0,      20000],
    })

    engine = FinancialEngine.from_dataframe(sample_data)
    rapor = engine.full_report()

    print("=" * 50)
    print("KazKaz AI - Finansal Özet Rapor")
    print("=" * 50)
    print(f"\n💰 Toplam Gelir    : {rapor['gelir']['toplam_gelir']:,.0f} ₺")
    print(f"📉 Toplam Gider    : {rapor['gider']['toplam_gider']:,.0f} ₺")
    print(f"📈 Net Kar         : {rapor['karlilik']['toplam_net_kar']:,.0f} ₺")
    print(f"📊 Kar Marjı       : %{rapor['karlilik']['kar_marji']}")
    print(f"🏥 Sağlık Skoru    : {rapor['saglik_skoru']['skor']} / 100 → {rapor['saglik_skoru']['kategori']}")
    print(f"💬 Yorum           : {rapor['saglik_skoru']['aciklama']}")

    print("\n📦 Senaryo: +%10 Gelir, -%5 Gider")
    senaryo = engine.scenario_analysis(gelir_artis_orani=0.10, gider_azalis_orani=0.05)
    print(f"   Yeni Net Kar  : {senaryo['senaryo']['net_kar']:,.0f} ₺")
    print(f"   Yeni Kar Marjı: %{senaryo['senaryo']['kar_marji']}")

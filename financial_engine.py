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
        fixed_keywords: sabit gider kategorilerini içeren anahtar kelimeler.
        Varsayılan: ['kira', 'maaş', 'amortisman', 'sigorta']
        """
        if fixed_keywords is None:
            fixed_keywords = ["kira", "maaş", "amortisman", "sigorta", "abonelik"]

        pattern = "|".join(fixed_keywords)
        is_fixed = self.df["Kategori"].str.lower().str.contains(pattern, na=False)
        sabit = float(self.df.loc[is_fixed, "Gider"].sum())
        degisken = float(self.df.loc[~is_fixed, "Gider"].sum())
        return {"sabit_gider": sabit, "degisken_gider": degisken}

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
    Faktörler ve ağırlıklar:
      - Karlılık marjı          : %30
      - Gelir büyüme oranı      : %25
      - Gider kontrol oranı     : %25
      - Nakit sürdürülebilirliği: %20
    """

    WEIGHTS = {
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
    ):
        self.profit = profit
        self.revenue = revenue
        self.expense = expense

    # --- Alt skor hesaplayıcılar (0-100) ---

    def _karlilik_skoru(self) -> float:
        """Kar marjına göre skor. >20% → 100, <0% → 0."""
        margin = self.profit.profit_margin()
        return float(np.clip(margin * 5, 0, 100))

    def _buyume_skoru(self) -> float:
        """Ortalama gelir büyüme oranına göre skor. >10% → 100."""
        growth = self.revenue.summary()["ortalama_buyume_orani"]
        return float(np.clip(growth * 10, 0, 100))

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
        Nakit sürdürülebilirliği: son 3 aydaki ortalama net kar pozitif mi?
        Pozitif → 100, negatif → 0, arada orantılı.
        """
        monthly = self.profit.monthly_profit()
        if monthly.empty:
            return 50.0
        son_3 = monthly.tail(3)["NetKar"].mean()
        if son_3 >= 0:
            return float(np.clip(50 + son_3 / max(abs(son_3), 1) * 50, 0, 100))
        return float(np.clip(50 + son_3 / max(abs(son_3), 1) * 50, 0, 100))

    def calculate(self) -> Dict[str, Any]:
        """Genel sağlık skorunu ve alt skorları döndürür."""
        alt_skorlar = {
            "karlilik": round(self._karlilik_skoru(), 1),
            "buyume": round(self._buyume_skoru(), 1),
            "gider_kontrolu": round(self._gider_kontrolu_skoru(), 1),
            "nakit": round(self._nakit_skoru(), 1),
        }

        genel_skor = sum(
            alt_skorlar[k] * self.WEIGHTS[k] for k in self.WEIGHTS
        )
        genel_skor = round(genel_skor, 1)

        kategori = self._kategori(genel_skor)

        return {
            "skor": genel_skor,
            "kategori": kategori,
            "alt_skorlar": alt_skorlar,
            "aciklama": self._aciklama(kategori),
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
        self.health = HealthScore(self.profit, self.revenue, self.expense)

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

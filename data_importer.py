"""
KazKaz AI - Veri Giriş & Dönüştürme Motoru
============================================
Desteklenen kaynaklar:
  1. Manuel form girişi
  2. Logo / Netsis Excel export
  3. Mikro export
  4. Zirve export
  5. Muhasebeci Excel (genel format algılama)
  6. Standart KazKaz CSV/Excel

Bağımlılıklar: pandas, numpy, openpyxl
"""

import pandas as pd
import numpy as np
import re
from typing import Dict, Any, List, Optional, Tuple
from io import BytesIO
import warnings
warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────
# STANDART KAZKAZ FORMATI
# ─────────────────────────────────────────────
# Tarih     | Kategori | Gelir | Gider | Müşteri | Ürün
# 2024-01   | Satış    | 50000 | 0     | Acme    | ERP
# 2024-01   | Kira     | 0     | 8000  |         |

STANDART_KOLONLAR = ["Tarih", "Kategori", "Gelir", "Gider"]
OPSIYONEL_KOLONLAR = ["Müşteri", "Ürün", "Açıklama"]


# ─────────────────────────────────────────────
# FORMAT ALGILAMA
# ─────────────────────────────────────────────

class FormatDetector:
    """Yüklenen dosyanın formatını otomatik algılar."""

    LOGO_BELIRTECLER = [
        "FİRMA", "HESAP KODU", "BORÇ", "ALACAK", "YEVMİYE",
        "LOGO", "Cari Hesap", "Fiş No"
    ]
    MIKRO_BELIRTECLER = [
        "MİKRO", "Mikro", "HESAP ADI", "TUTAR", "İşlem Türü"
    ]
    ZIRVE_BELIRTECLER = [
        "ZİRVE", "Zirve", "BELGE NO", "AÇIKLAMA", "KDV"
    ]
    NETSIS_BELIRTECLER = [
        "NETSİS", "Netsis", "HESAP NO", "MUHASEBE"
    ]

    @staticmethod
    def detect(df: pd.DataFrame, filename: str = "") -> str:
        """Format adını döndür."""
        tum_metin = " ".join([
            str(col) for col in df.columns
        ] + [str(df.iloc[0].tolist() if len(df) > 0 else [])]).upper()

        fn = filename.upper()

        if any(b.upper() in tum_metin for b in FormatDetector.LOGO_BELIRTECLER):
            return "logo"
        if any(b.upper() in tum_metin for b in FormatDetector.MIKRO_BELIRTECLER):
            return "mikro"
        if any(b.upper() in tum_metin for b in FormatDetector.ZIRVE_BELIRTECLER):
            return "zirve"
        if any(b.upper() in tum_metin for b in FormatDetector.NETSIS_BELIRTECLER):
            return "netsis"
        if "LOGO" in fn:
            return "logo"
        if "MIKRO" in fn or "MİKRO" in fn:
            return "mikro"
        if "ZIRVE" in fn or "ZİRVE" in fn:
            return "zirve"

        # Standart KazKaz formatı mı?
        kolonlar = [str(c).lower() for c in df.columns]
        if "tarih" in kolonlar and ("gelir" in kolonlar or "gider" in kolonlar):
            return "kazkaz"

        return "genel"  # Genel muhasebeci Excel


# ─────────────────────────────────────────────
# FORMAT DÖNÜŞTÜRÜCÜler
# ─────────────────────────────────────────────

class BaseConverter:
    """Tüm dönüştürücülerin temel sınıfı."""

    def convert(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    @staticmethod
    def _normalize_date(series: pd.Series) -> pd.Series:
        """Tarih sütununu YYYY-MM formatına çevir."""
        def parse(val):
            val = str(val).strip()
            # YYYY-MM zaten doğru
            if re.match(r'^\d{4}-\d{2}$', val):
                return val
            # DD.MM.YYYY veya DD/MM/YYYY
            for fmt in ["%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d",
                        "%d.%m.%y", "%m/%Y", "%Y/%m"]:
                try:
                    import datetime
                    dt = datetime.datetime.strptime(val[:10], fmt)
                    return dt.strftime("%Y-%m")
                except:
                    continue
            # Son çare: pandas parse
            try:
                return pd.to_datetime(val, dayfirst=True).strftime("%Y-%m")
            except:
                return val
        return series.apply(parse)

    @staticmethod
    def _clean_number(val) -> float:
        """Sayısal değeri temizle (nokta/virgül/TL vb.)."""
        try:
            if pd.isna(val):
                return 0.0
            s = str(val).replace(".", "").replace(",", ".").replace("₺", "").replace(" ", "").strip()
            s = re.sub(r'[^\d.-]', '', s)
            return float(s) if s else 0.0
        except:
            return 0.0

    @staticmethod
    def _to_standard(df: pd.DataFrame) -> pd.DataFrame:
        """Standart formata uygun son işlemler."""
        df = df.copy()
        df["Gelir"] = df["Gelir"].apply(lambda x: max(float(x or 0), 0))
        df["Gider"] = df["Gider"].apply(lambda x: max(float(x or 0), 0))
        df = df[df["Gelir"] + df["Gider"] > 0]  # Boş satırları sil
        for col in OPSIYONEL_KOLONLAR:
            if col not in df.columns:
                df[col] = ""
        return df[STANDART_KOLONLAR + [c for c in OPSIYONEL_KOLONLAR
                                        if c in df.columns]].reset_index(drop=True)


class KazKazConverter(BaseConverter):
    """Standart KazKaz formatı — doğrudan kullan."""

    def convert(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        # Kolon adlarını normalize et
        df.columns = [str(c).strip() for c in df.columns]

        col_map = {}
        for col in df.columns:
            cl = col.lower()
            if "tarih" in cl:          col_map[col] = "Tarih"
            elif "kateg" in cl:        col_map[col] = "Kategori"
            elif "gelir" in cl:        col_map[col] = "Gelir"
            elif "gider" in cl:        col_map[col] = "Gider"
            elif "müşteri" in cl or "musteri" in cl: col_map[col] = "Müşteri"
            elif "ürün" in cl or "urun" in cl:       col_map[col] = "Ürün"

        df = df.rename(columns=col_map)
        df["Tarih"] = self._normalize_date(df["Tarih"])
        df["Gelir"] = df.get("Gelir", pd.Series([0]*len(df))).apply(self._clean_number)
        df["Gider"] = df.get("Gider", pd.Series([0]*len(df))).apply(self._clean_number)
        if "Kategori" not in df.columns:
            df["Kategori"] = "Genel"
        return self._to_standard(df)


class LogoConverter(BaseConverter):
    """Logo / Netsis mizan/döküm export dönüştürücü."""

    def convert(self, df: pd.DataFrame) -> pd.DataFrame:
        # Logo genellikle: Tarih | Hesap Kodu | Hesap Adı | Borç | Alacak
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]

        # Tarih sütununu bul
        tarih_col = next((c for c in df.columns
                          if any(k in c.upper() for k in ["TARİH","TARIH","DATE"])), None)
        borc_col  = next((c for c in df.columns
                          if any(k in c.upper() for k in ["BORÇ","BORC","DEBIT"])), None)
        alacak_col= next((c for c in df.columns
                          if any(k in c.upper() for k in ["ALACAK","CREDIT"])), None)
        hesap_col = next((c for c in df.columns
                          if any(k in c.upper() for k in ["HESAP ADI","ACCOUNT","AÇIKLAMA"])), None)

        if not all([tarih_col, borc_col, alacak_col]):
            raise ValueError(
                "Logo formatı tanınamadı. "
                "Tarih, Borç ve Alacak sütunları bulunamadı."
            )

        result = pd.DataFrame()
        result["Tarih"]    = self._normalize_date(df[tarih_col])
        result["Kategori"] = df[hesap_col] if hesap_col else "Logo Kaydı"
        result["Gelir"]    = df[alacak_col].apply(self._clean_number)
        result["Gider"]    = df[borc_col].apply(self._clean_number)

        return self._to_standard(result)


class MikroConverter(BaseConverter):
    """Mikro muhasebe export dönüştürücü."""

    def convert(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]

        tarih_col  = next((c for c in df.columns
                           if "TARİH" in c.upper() or "TARIH" in c.upper()), None)
        tutar_col  = next((c for c in df.columns
                           if "TUTAR" in c.upper() or "AMOUNT" in c.upper()), None)
        tip_col    = next((c for c in df.columns
                           if "TÜR" in c.upper() or "TIP" in c.upper()
                           or "IŞLEM" in c.upper() or "ISLEM" in c.upper()), None)
        aciklama_col = next((c for c in df.columns
                             if "AÇIKLAMA" in c.upper() or "ACIKLAMA" in c.upper()
                             or "HESAP" in c.upper()), None)

        if not tarih_col or not tutar_col:
            raise ValueError(
                "Mikro formatı tanınamadı. "
                "Tarih ve Tutar sütunları bulunamadı."
            )

        result = pd.DataFrame()
        result["Tarih"]    = self._normalize_date(df[tarih_col])
        result["Kategori"] = df[aciklama_col] if aciklama_col else "Mikro Kaydı"

        # İşlem tipine göre gelir/gider ayır
        tutarlar = df[tutar_col].apply(self._clean_number)
        if tip_col:
            tip = df[tip_col].astype(str).str.upper()
            result["Gelir"] = np.where(
                tip.str.contains("ALACAK|GELİR|SATIŞ|CREDIT", na=False),
                tutarlar, 0
            )
            result["Gider"] = np.where(
                tip.str.contains("BORÇ|GİDER|ALIS|DEBIT", na=False),
                tutarlar.abs(), 0
            )
        else:
            # Pozitif = gelir, negatif = gider
            result["Gelir"] = tutarlar.apply(lambda x: x if x > 0 else 0)
            result["Gider"] = tutarlar.apply(lambda x: abs(x) if x < 0 else 0)

        return self._to_standard(result)


class GenelConverter(BaseConverter):
    """
    Muhasebecinin gönderdiği genel Excel formatları için
    akıllı sütun eşleştirme.
    """

    GELIR_ANAHTAR = ["gelir", "satış", "satis", "hasılat", "hasilat",
                      "tahsilat", "alacak", "credit", "income", "revenue"]
    GIDER_ANAHTAR = ["gider", "maliyet", "harcama", "ödeme", "odeme",
                      "borç", "borc", "debit", "expense", "cost"]
    TARIH_ANAHTAR = ["tarih", "dönem", "donem", "ay", "date", "period"]
    KATEG_ANAHTAR = ["kategori", "hesap", "açıklama", "aciklama",
                      "tür", "tur", "kalem", "account", "description"]

    def convert(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]

        col_lower = {c: c.lower() for c in df.columns}

        def find_col(keywords):
            for col, cl in col_lower.items():
                if any(k in cl for k in keywords):
                    return col
            return None

        tarih_col = find_col(self.TARIH_ANAHTAR)
        gelir_col = find_col(self.GELIR_ANAHTAR)
        gider_col = find_col(self.GIDER_ANAHTAR)
        kateg_col = find_col(self.KATEG_ANAHTAR)

        if not tarih_col:
            # İlk sütunu tarih say
            tarih_col = df.columns[0]

        result = pd.DataFrame()
        result["Tarih"]    = self._normalize_date(df[tarih_col])
        result["Kategori"] = df[kateg_col] if kateg_col else "Genel"

        if gelir_col:
            result["Gelir"] = df[gelir_col].apply(self._clean_number)
        else:
            result["Gelir"] = 0

        if gider_col:
            result["Gider"] = df[gider_col].apply(self._clean_number)
        else:
            result["Gider"] = 0

        # Eğer sadece tek tutar sütunu varsa (pozitif/negatif)
        if not gelir_col and not gider_col:
            tutar_col = next(
                (c for c in df.columns
                 if df[c].dtype in [np.float64, np.int64]
                 and c != tarih_col and c != kateg_col), None
            )
            if tutar_col:
                tutarlar = df[tutar_col].apply(self._clean_number)
                result["Gelir"] = tutarlar.apply(lambda x: x if x > 0 else 0)
                result["Gider"] = tutarlar.apply(lambda x: abs(x) if x < 0 else 0)

        return self._to_standard(result)


# ─────────────────────────────────────────────
# ANA DÖNÜŞTÜRÜCÜ
# ─────────────────────────────────────────────

class DataImporter:
    """
    KazKaz AI Ana Veri İthalatçısı.

    Kullanım:
        importer = DataImporter()
        df, bilgi = importer.import_file(uploaded_file)
    """

    CONVERTERS = {
        "kazkaz": KazKazConverter,
        "logo":   LogoConverter,
        "netsis": LogoConverter,
        "mikro":  MikroConverter,
        "zirve":  GenelConverter,
        "genel":  GenelConverter,
    }

    FORMAT_ISIMLERI = {
        "kazkaz": "KazKaz Standart",
        "logo":   "Logo / Netsis",
        "netsis": "Netsis",
        "mikro":  "Mikro",
        "zirve":  "Zirve",
        "genel":  "Genel Muhasebe Excel",
    }

    def __init__(self):
        self.detector = FormatDetector()

    def import_file(self, file_obj,
                    filename: str = "") -> Tuple[pd.DataFrame, Dict]:
        """
        Dosyayı yükle, formatı algıla, dönüştür.
        Returns: (standart_df, bilgi_dict)
        """
        # Dosyayı oku
        ext = filename.lower().split(".")[-1] if filename else "csv"
        try:
            if ext in ["xlsx", "xls"]:
                raw_df = pd.read_excel(file_obj, header=0)
            else:
                # CSV — encoding dene
                for enc in ["utf-8", "latin-1", "cp1254", "utf-8-sig"]:
                    try:
                        file_obj.seek(0)
                        raw_df = pd.read_csv(file_obj, encoding=enc)
                        break
                    except:
                        continue
        except Exception as e:
            raise ValueError(f"Dosya okunamadı: {e}")

        # Format algıla
        fmt = self.detector.detect(raw_df, filename)

        # Dönüştür
        converter = self.CONVERTERS[fmt]()
        try:
            df = converter.convert(raw_df)
        except Exception as e:
            # Başarısız olursa genel dönüştürücüyü dene
            try:
                df = GenelConverter().convert(raw_df)
                fmt = "genel"
            except:
                raise ValueError(
                    f"Dosya dönüştürülemedi: {e}\n"
                    "Lütfen KazKaz standart formatını kullanın."
                )

        bilgi = {
            "format":       self.FORMAT_ISIMLERI.get(fmt, fmt),
            "ham_satirlar": len(raw_df),
            "temiz_satirlar": len(df),
            "donemler":     sorted(df["Tarih"].unique()),
            "kategoriler":  list(df["Kategori"].unique()),
            "toplam_gelir": float(df["Gelir"].sum()),
            "toplam_gider": float(df["Gider"].sum()),
        }

        return df, bilgi

    @staticmethod
    def from_manual_entries(entries: List[Dict]) -> pd.DataFrame:
        """
        Manuel form girişlerinden DataFrame oluştur.
        entries: [{"tarih": "2024-01", "kategori": "Satış",
                   "gelir": 50000, "gider": 0}, ...]
        """
        rows = []
        for e in entries:
            rows.append({
                "Tarih":    e.get("tarih", ""),
                "Kategori": e.get("kategori", "Genel"),
                "Gelir":    float(e.get("gelir", 0) or 0),
                "Gider":    float(e.get("gider", 0) or 0),
                "Müşteri":  e.get("musteri", ""),
                "Ürün":     e.get("urun", ""),
            })
        df = pd.DataFrame(rows)
        df = df[df["Gelir"] + df["Gider"] > 0]
        return df.reset_index(drop=True)

    @staticmethod
    def standart_sablon() -> pd.DataFrame:
        """Kullanıcıya gösterilecek standart şablon."""
        return pd.DataFrame({
            "Tarih":    ["2024-01","2024-01","2024-02","2024-02","2024-03"],
            "Kategori": ["Satış","Personel Gideri","Satış","Kira","Danışmanlık"],
            "Gelir":    [150000,0,170000,0,50000],
            "Gider":    [0,45000,0,12000,0],
            "Müşteri":  ["Acme A.Ş.","","Beta Ltd.","","Gamma Co."],
            "Ürün":     ["ERP Yazılım","","CRM Modül","","Danışmanlık"],
        })

"""V1 API istek ve yanıt modelleri."""

from datetime import date
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class FinansSatiri(BaseModel):
    tarih: date
    kategori: str = Field(min_length=1, max_length=120)
    gelir: float = Field(default=0, ge=0)
    gider: float = Field(default=0, ge=0)


class BilançoBilgisi(BaseModel):
    baslangic_nakiti: float = Field(default=0, ge=0)
    donen_varliklar: float = Field(default=0, ge=0)
    kisa_vadeli_borc: float = Field(default=0, ge=0)
    stoklar: float = Field(default=0, ge=0)


class FinansalAnalizIstegi(BaseModel):
    satirlar: List[FinansSatiri] = Field(min_length=1, max_length=50_000)
    bilanco: BilançoBilgisi = Field(default_factory=BilançoBilgisi)


class MusteriCiroSatiri(BaseModel):
    musteri_id: str = Field(min_length=1, max_length=120)
    musteri_adi: str = Field(min_length=1, max_length=180)
    ciro: float = Field(ge=0)


class FinansalGorunum(BaseModel):
    sirket_adi: str = Field(default="Şirket", min_length=1, max_length=160)
    sektor: str = Field(default="Belirtilmedi", max_length=120)
    donem: str = Field(default="Güncel", max_length=80)
    para_birimi: str = Field(default="TRY", pattern="^(TRY|USD|EUR|GBP|CHF)$")
    ciro: float = Field(ge=0)
    satis_maliyeti: float = Field(default=0, ge=0)
    faaliyet_giderleri: float = Field(default=0, ge=0)
    net_kar: float
    nakit: float = Field(default=0, ge=0)
    kisa_vadeli_borc: float = Field(default=0, ge=0)
    uzun_vadeli_borc: float = Field(default=0, ge=0)
    alacaklar: float = Field(default=0, ge=0)
    borclar: float = Field(default=0, ge=0)
    stoklar: float = Field(default=0, ge=0)
    ozkaynak: float = Field(default=0, ge=0)
    faiz_gideri: Optional[float] = Field(default=None, ge=0)
    vergi_gideri: Optional[float] = Field(default=None, ge=0)
    amortisman: Optional[float] = Field(default=None, ge=0)
    capex: Optional[float] = Field(default=None, ge=0)
    donen_varliklar: Optional[float] = Field(default=None, ge=0)
    toplam_varliklar: Optional[float] = Field(default=None, gt=0)
    toplam_yukumlulukler: Optional[float] = Field(default=None, ge=0)
    dagitilmamis_karlar: Optional[float] = None
    operasyonel_nakit_akisi: Optional[float] = None
    donem_basi_nakit: Optional[float] = Field(default=None, ge=0)
    yatirim_nakit_akisi: Optional[float] = None
    finansman_nakit_akisi: Optional[float] = None
    donem_gun_sayisi: Optional[int] = Field(default=None, ge=1, le=366)
    etkin_vergi_orani: Optional[float] = Field(default=None, ge=0, le=100)
    musteri_cirolari: List[MusteriCiroSatiri] = Field(default_factory=list, max_length=10_000)


class SohbetMesaji(BaseModel):
    rol: str = Field(pattern="^(kullanici|asistan)$")
    icerik: str = Field(min_length=1, max_length=4_000)


class SirketTercihBaglami(BaseModel):
    ana_hedef: Literal["buyume", "karlilik", "nakit", "finansman", "maliyet"]
    ana_zorluk: Literal["nakit", "marj", "tahsilat", "maliyet", "gorunurluk"]


class CfoSohbetIstegi(BaseModel):
    mesaj: str = Field(min_length=2, max_length=2_000)
    finansal_veri: FinansalGorunum
    gecmis: List[SohbetMesaji] = Field(default_factory=list, max_length=10)
    ajan_denetimi: Optional[Dict[str, Any]] = None
    sirket_profili: Optional[SirketTercihBaglami] = None


class NakitAkisSatiri(BaseModel):
    donem: str = Field(min_length=1, max_length=40)
    giris: float = Field(ge=0)
    cikis: float = Field(ge=0)
    net_nakit: float
    kumulatif_nakit: Optional[float] = None


class BorcKalemi(BaseModel):
    ad: str = Field(min_length=1, max_length=160)
    tutar: float = Field(gt=0)
    faiz_orani: Optional[float] = Field(default=None, ge=0, le=200)
    vade: Optional[str] = Field(default=None, max_length=40)


class CfoAjanAnalizIstegi(BaseModel):
    finansal_veri: FinansalGorunum
    nakit_akisi: List[NakitAkisSatiri] = Field(default_factory=list, max_length=260)
    borclar: List[BorcKalemi] = Field(default_factory=list, max_length=500)


class MizanSatiri(BaseModel):
    donem: str = Field(min_length=1, max_length=40)
    hesap_kodu: str = Field(min_length=1, max_length=40)
    hesap_adi: str = Field(min_length=1, max_length=180)
    borc: float = Field(default=0, ge=0)
    alacak: float = Field(default=0, ge=0)
    esleme: Optional[str] = Field(default=None, max_length=60)


class HaftalikNakitSatiri(BaseModel):
    hafta: date
    tahsilat: float = Field(default=0, ge=0)
    nakit_satis: float = Field(default=0, ge=0)
    diger_giris: float = Field(default=0, ge=0)
    tedarikci: float = Field(default=0, ge=0)
    personel: float = Field(default=0, ge=0)
    vergi: float = Field(default=0, ge=0)
    borc_servisi: float = Field(default=0, ge=0)
    diger_cikis: float = Field(default=0, ge=0)


class AlacakFaturasi(BaseModel):
    fatura_id: str = Field(min_length=1, max_length=120)
    musteri_id: str = Field(min_length=1, max_length=120)
    musteri_adi: str = Field(min_length=1, max_length=180)
    fatura_tarihi: date
    vade_tarihi: date
    tutar: float = Field(gt=0)
    odenen: float = Field(default=0, ge=0)

    @model_validator(mode="after")
    def odeme_faturayi_asamaz(self):
        if self.odenen > self.tutar:
            raise ValueError("ödenen tutar fatura tutarını aşamaz")
        if self.vade_tarihi < self.fatura_tarihi:
            raise ValueError("vade tarihi fatura tarihinden önce olamaz")
        return self


class BorcServisSatiri(BaseModel):
    borc_id: str = Field(min_length=1, max_length=120)
    alacakli: str = Field(min_length=1, max_length=180)
    odeme_tarihi: date
    anapara: float = Field(default=0, ge=0)
    faiz: float = Field(default=0, ge=0)
    para_birimi: Literal["TRY", "USD", "EUR", "GBP", "CHF"] = "TRY"


class ButceGerceklesmeSatiri(BaseModel):
    ay: date
    kategori: str = Field(min_length=1, max_length=120)
    departman: str = Field(default="Genel", max_length=120)
    proje: str = Field(default="Genel", max_length=120)
    butce: float = Field(default=0, ge=0)
    gerceklesen: float = Field(default=0, ge=0)
    onceki_tahmin: Optional[float] = Field(default=None, ge=0)


class GelismisAjanIstegi(BaseModel):
    finansal_veri: FinansalGorunum
    rapor_tarihi: date = Field(default_factory=date.today)
    baslangic_nakdi: float = Field(default=0, ge=0)
    minimum_nakit_esigi: Optional[float] = Field(default=None, ge=0)
    operasyonel_nakit_akisi: Optional[float] = None
    mizan: List[MizanSatiri] = Field(default_factory=list, max_length=100_000)
    haftalik_nakit: List[HaftalikNakitSatiri] = Field(default_factory=list, max_length=52)
    alacak_faturalari: List[AlacakFaturasi] = Field(default_factory=list, max_length=100_000)
    borc_servisi: List[BorcServisSatiri] = Field(default_factory=list, max_length=20_000)
    butce: List[ButceGerceklesmeSatiri] = Field(default_factory=list, max_length=20_000)


class KimlikBilgisi(BaseModel):
    kullanici_id: str
    eposta: Optional[str] = None
    eposta_dogrulandi: bool = False
    sirket_id: Optional[str] = None
    roller: Dict[str, bool] = Field(default_factory=dict)
    plan: str = Field(default="free", pattern="^(free|trial|pro|uzman)$")
    deneme_bitis: Optional[date] = None
    sirket_durumu: str = Field(default="active", pattern="^(active|pilot|suspended|closed)$")


class SirketOlusturmaIstegi(BaseModel):
    sirket_adi: str = Field(min_length=2, max_length=160)
    sektor: Literal[
        "teknoloji", "uretim", "perakende", "hizmet", "insaat", "gida", "lojistik", "diger"
    ]
    calisan_olcegi: Literal["1-9", "10-49", "50-249", "250+"]
    ana_hedef: Literal["buyume", "karlilik", "nakit", "finansman", "maliyet"]
    ana_zorluk: Literal["nakit", "marj", "tahsilat", "maliyet", "gorunurluk"]
    veri_kaynagi: Literal["excel", "logo", "mikro", "parasut", "erp", "smmm", "diger"]
    veri_kapsami: List[Literal[
        "gelir_tablosu", "bilanco", "mizan", "nakit", "alacak", "borc", "butce"
    ]] = Field(default_factory=list, max_length=7)
    para_birimi: Literal["TRY", "USD", "EUR", "GBP", "CHF"] = "TRY"
    mali_yil_baslangic_ayi: int = Field(default=1, ge=1, le=12)


class RaporIstegi(BaseModel):
    finansal_veri: FinansalGorunum
    arsivle: bool = True


class UyeDavetIstegi(BaseModel):
    eposta: str = Field(min_length=5, max_length=254)
    rol: Literal["cfo", "analyst", "viewer"]


class UyeRolGuncellemeIstegi(BaseModel):
    kullanici_id: str = Field(min_length=1, max_length=128)
    rol: Literal["admin", "cfo", "analyst", "viewer"]


class UyeCikarmaIstegi(BaseModel):
    kullanici_id: str = Field(min_length=1, max_length=128)


class PlatformSirketGuncellemeIstegi(BaseModel):
    sirket_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    durum: Optional[Literal["active", "pilot", "suspended", "closed"]] = None
    plan: Optional[Literal["free", "trial", "pro", "uzman"]] = None
    gerekce: Optional[str] = Field(default=None, min_length=5, max_length=300)

    @model_validator(mode="after")
    def en_az_bir_degisiklik(self):
        if self.durum is None and self.plan is None:
            raise ValueError("durum veya plan değişikliği gerekli")
        return self


class PlatformSirketEylemIstegi(BaseModel):
    sirket_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    eylem: Literal["oturumlari_sonlandir"]
    gerekce: str = Field(min_length=5, max_length=300)


class PlatformGeriBildirimDurumIstegi(BaseModel):
    sirket_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    geri_bildirim_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    durum: Literal["new", "in_review", "resolved"]
    gerekce: Optional[str] = Field(default=None, min_length=5, max_length=300)


class GoogleSheetsIstegi(BaseModel):
    url: str = Field(min_length=30, max_length=500)
    sayfa_adi: Optional[str] = Field(default=None, max_length=120)


class KurSorgusu(BaseModel):
    tarih: date
    para_birimleri: List[str] = Field(default_factory=lambda: ["USD", "EUR", "GBP"], min_length=1, max_length=20)


class GeriBildirimIstegi(BaseModel):
    kategori: str = Field(pattern="^(hata|oneri|kullanilabilirlik|finansal_sonuc)$")
    mesaj: str = Field(min_length=10, max_length=2_000)
    sayfa: str = Field(default="bilinmiyor", max_length=80)
    iletisim_izni: bool = False


class CalismaAlaniKaydetIstegi(BaseModel):
    schema_version: int = Field(default=2, ge=2, le=2)
    snapshot: Dict[str, Any]

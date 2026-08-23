"""ESG ve TFRS/IFRS için uyum görüşü vermeyen veri hazırlık kontrolleri."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class EsgHazirlikIstegi(BaseModel):
    raporlama_yili: int = Field(ge=2000, le=2100)
    organizasyon_kapsami_tanimli: bool = False
    onemli_konular_belirlendi: bool = False
    enerji_kwh: Optional[float] = Field(default=None, ge=0)
    scope1_tco2e: Optional[float] = Field(default=None, ge=0)
    scope2_tco2e: Optional[float] = Field(default=None, ge=0)
    su_m3: Optional[float] = Field(default=None, ge=0)
    atik_ton: Optional[float] = Field(default=None, ge=0)
    calisan_sayisi: Optional[int] = Field(default=None, ge=0)
    kadin_calisan_orani: Optional[float] = Field(default=None, ge=0, le=100)
    kayip_gunlu_is_kazasi: Optional[int] = Field(default=None, ge=0)
    etik_politikasi_var: bool = False
    yonetim_sorumlusu_atandi: bool = False
    veri_kaynaklari_belgeli: bool = False
    uzman_onayi: bool = False


class TfrsHazirlikIstegi(BaseModel):
    standart_seti: str = Field(default="TFRS 2026", pattern=r"^TFRS 20\d{2}$")
    musteri_sozlesmeleri_var: bool = False
    hasilat_politikasi_belgeli: bool = False
    performans_yukumlulukleri_listeli: bool = False
    kiralama_sozlesmeleri_var: bool = False
    kiralama_envanteri_var: bool = False
    yabanci_para_islemleri_var: bool = False
    fonksiyonel_para_birimi_belgeli: bool = False
    stok_var: bool = False
    stok_degerleme_politikasi_belgeli: bool = False
    finansal_araclar_var: bool = False
    finansal_arac_siniflandirmasi_belgeli: bool = False
    iliskili_taraf_var: bool = False
    iliskili_taraf_listesi_var: bool = False
    nakit_akis_mutabakati_var: bool = False
    muhasebe_uzmani_onayi: bool = False


def _hazirlik_sonucu(alanlar: list[dict], *, metodoloji: str, uyari: str) -> dict:
    uygulanabilir = [alan for alan in alanlar if alan["uygulanabilir"]]
    hazir = [alan for alan in uygulanabilir if alan["hazir"]]
    uzman = next((alan for alan in uygulanabilir if alan["kod"] == "EXPERT_REVIEW"), None)
    uzman_harici = [alan for alan in uygulanabilir if alan["kod"] != "EXPERT_REVIEW"]
    oran = round(len(hazir) / len(uygulanabilir) * 100) if uygulanabilir else 0
    if uygulanabilir and len(hazir) == len(uygulanabilir):
        durum = "hazirlik_tamamlandi"
    elif uzman_harici and all(alan["hazir"] for alan in uzman_harici) and uzman and not uzman["hazir"]:
        durum = "uzman_onayi_bekliyor"
    else:
        durum = "veri_hazirligi"
    return {
        "durum": durum,
        "hazirlik_orani": oran,
        "hazir_baslik": len(hazir),
        "uygulanabilir_baslik": len(uygulanabilir),
        "basliklar": alanlar,
        "eksikler": [alan["gereken"] for alan in uygulanabilir if not alan["hazir"]],
        "metodoloji": metodoloji,
        "uyari": uyari,
    }


def esg_hazirligini_degerlendir(istek: EsgHazirlikIstegi) -> dict:
    alanlar = [
        {"kod": "GRI_UNIVERSAL", "ad": "Kuruluş kapsamı ve önemli konular", "uygulanabilir": True,
         "hazir": istek.organizasyon_kapsami_tanimli and istek.onemli_konular_belirlendi,
         "gereken": "Organizasyon kapsamı ve önemli konu belirleme kaydı"},
        {"kod": "GRI_ENERGY", "ad": "Enerji", "uygulanabilir": True, "hazir": istek.enerji_kwh is not None,
         "gereken": "Sayaç/fatura kaynaklı enerji tüketimi (kWh)"},
        {"kod": "GRI_EMISSIONS", "ad": "Emisyon", "uygulanabilir": True,
         "hazir": istek.scope1_tco2e is not None and istek.scope2_tco2e is not None,
         "gereken": "Scope 1 ve Scope 2 hesapları, faktör kaynağı ve dönem kapsamı"},
        {"kod": "GRI_303", "ad": "Su", "uygulanabilir": True, "hazir": istek.su_m3 is not None,
         "gereken": "Kaynak belgeli su çekimi/tüketimi (m³)"},
        {"kod": "GRI_306", "ad": "Atık", "uygulanabilir": True, "hazir": istek.atik_ton is not None,
         "gereken": "Atık türü, miktarı ve bertaraf yöntemi"},
        {"kod": "GRI_401", "ad": "İstihdam", "uygulanabilir": True,
         "hazir": istek.calisan_sayisi is not None and istek.kadin_calisan_orani is not None,
         "gereken": "Dönem sonu çalışan sayısı ve çeşitlilik kırılımı"},
        {"kod": "GRI_403", "ad": "İş sağlığı ve güvenliği", "uygulanabilir": True,
         "hazir": istek.kayip_gunlu_is_kazasi is not None,
         "gereken": "İş kazası tanımı, kayıt kaynağı ve kayıp gün sayısı"},
        {"kod": "GOVERNANCE", "ad": "Yönetişim", "uygulanabilir": True,
         "hazir": istek.etik_politikasi_var and istek.yonetim_sorumlusu_atandi,
         "gereken": "Etik politika ve atanmış ESG/veri sorumlusu"},
        {"kod": "EVIDENCE", "ad": "Veri kaynakları", "uygulanabilir": True,
         "hazir": istek.veri_kaynaklari_belgeli, "gereken": "Her gösterge için kaynak ve sorumlu kaydı"},
        {"kod": "EXPERT_REVIEW", "ad": "Uzman incelemesi", "uygulanabilir": True,
         "hazir": istek.uzman_onayi, "gereken": "Yetkili sürdürülebilirlik uzmanı onayı"},
    ]
    return _hazirlik_sonucu(
        alanlar,
        metodoloji="GRI Universal, Sector ve Topic Standards ayrımı gözetilerek yalnız veri kapsamı ölçülür.",
        uyari="Bu sonuç ESG performans skoru, GRI/SASB uyum görüşü veya güvence raporu değildir.",
    )


def tfrs_hazirligini_degerlendir(istek: TfrsHazirlikIstegi) -> dict:
    alanlar = [
        {"kod": "TFRS_15", "ad": "Müşteri sözleşmelerinden hasılat", "uygulanabilir": istek.musteri_sozlesmeleri_var,
         "hazir": istek.hasilat_politikasi_belgeli and istek.performans_yukumlulukleri_listeli,
         "gereken": "Hasılat politikası, sözleşme envanteri ve performans yükümlülükleri"},
        {"kod": "TFRS_16", "ad": "Kiralamalar", "uygulanabilir": istek.kiralama_sozlesmeleri_var,
         "hazir": istek.kiralama_envanteri_var, "gereken": "Kiralama envanteri, süre ve ödeme planı"},
        {"kod": "TMS_21", "ad": "Yabancı para işlemleri", "uygulanabilir": istek.yabanci_para_islemleri_var,
         "hazir": istek.fonksiyonel_para_birimi_belgeli, "gereken": "Fonksiyonel para birimi değerlendirmesi ve kur politikası"},
        {"kod": "TMS_2", "ad": "Stoklar", "uygulanabilir": istek.stok_var,
         "hazir": istek.stok_degerleme_politikasi_belgeli, "gereken": "Stok maliyet/değer düşüklüğü politikası"},
        {"kod": "TFRS_9", "ad": "Finansal araçlar", "uygulanabilir": istek.finansal_araclar_var,
         "hazir": istek.finansal_arac_siniflandirmasi_belgeli, "gereken": "Finansal araç sınıflandırması ve değerleme politikası"},
        {"kod": "TMS_24", "ad": "İlişkili taraf açıklamaları", "uygulanabilir": istek.iliskili_taraf_var,
         "hazir": istek.iliskili_taraf_listesi_var, "gereken": "İlişkili taraf ve işlem envanteri"},
        {"kod": "TMS_7", "ad": "Nakit akış tablosu", "uygulanabilir": True,
         "hazir": istek.nakit_akis_mutabakati_var, "gereken": "Nakit akış tablosu ve dönem başı/sonu nakit mutabakatı"},
        {"kod": "EXPERT_REVIEW", "ad": "Muhasebe uzmanı incelemesi", "uygulanabilir": True,
         "hazir": istek.muhasebe_uzmani_onayi, "gereken": "Yetkili muhasebe uzmanı/CFO onayı"},
    ]
    sonuc = _hazirlik_sonucu(
        alanlar,
        metodoloji=f"{istek.standart_seti} kapsamında yalnız uygulanabilir konu ve belge hazırlığı kontrol edilir.",
        uyari="Bu sonuç TFRS/IFRS uyum görüşü, muhasebe politikası onayı veya bağımsız denetim görüşü değildir.",
    )
    sonuc["standart_seti"] = istek.standart_seti
    sonuc["lisans_notu"] = "Standart metinleri ürüne kopyalanmaz; resmi KGK/IFRS kaynakları ve gerekli lisanslar kullanılmalıdır."
    return sonuc

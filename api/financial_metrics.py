"""Sürümlü ve kaynak gösterilebilir kurumsal finans metrikleri.

Her metrik aynı sonucu üretmekle kalmaz; kullanılan formülü, girdileri,
kaynak alanları ve veri eksiklerini de döndürür. Eksik veri halinde varsayım
uydurulmaz.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Optional

from api.models import FinansalGorunum


FORMUL_SURUMU = "2026.08-v1"


@dataclass(frozen=True)
class MetrikSonucu:
    deger: Optional[float]
    birim: str
    durum: str
    formula_id: str
    formula: str
    girdiler: Dict[str, Optional[float]]
    kaynak_alanlar: List[str]
    guven: str
    metodoloji_notu: str
    eksik_alanlar: List[str]
    formul_surumu: str = FORMUL_SURUMU

    def json(self) -> Dict[str, Any]:
        return asdict(self)


def _eksik(
    formula_id: str,
    formula: str,
    birim: str,
    girdiler: Dict[str, Optional[float]],
    kaynak_alanlar: Iterable[str],
    metodoloji_notu: str,
) -> MetrikSonucu:
    eksikler = [alan for alan, deger in girdiler.items() if deger is None]
    return MetrikSonucu(
        deger=None,
        birim=birim,
        durum="eksik_veri",
        formula_id=formula_id,
        formula=formula,
        girdiler=girdiler,
        kaynak_alanlar=list(kaynak_alanlar),
        guven="hesaplanamadi",
        metodoloji_notu=metodoloji_notu,
        eksik_alanlar=eksikler,
    )


def _sonuc(
    deger: float,
    formula_id: str,
    formula: str,
    birim: str,
    girdiler: Dict[str, Optional[float]],
    kaynak_alanlar: Iterable[str],
    metodoloji_notu: str,
    guven: str = "yuksek",
) -> MetrikSonucu:
    return MetrikSonucu(
        deger=round(float(deger), 4),
        birim=birim,
        durum="hesaplandi",
        formula_id=formula_id,
        formula=formula,
        girdiler=girdiler,
        kaynak_alanlar=list(kaynak_alanlar),
        guven=guven,
        metodoloji_notu=metodoloji_notu,
        eksik_alanlar=[],
    )


def _ebit(veri: FinansalGorunum) -> Optional[float]:
    if veri.faiz_gideri is None or veri.vergi_gideri is None:
        return None
    return veri.net_kar + veri.faiz_gideri + veri.vergi_gideri


def altman_z_prime(veri: FinansalGorunum) -> MetrikSonucu:
    """Özel imalat şirketleri için Altman Z' modeli."""
    ebit = _ebit(veri)
    girdiler = {
        "donen_varliklar": veri.donen_varliklar,
        "kisa_vadeli_borc": veri.kisa_vadeli_borc,
        "dagitilmamis_karlar": veri.dagitilmamis_karlar,
        "ebit": ebit,
        "ozkaynak": veri.ozkaynak if veri.ozkaynak > 0 else None,
        "toplam_yukumlulukler": veri.toplam_yukumlulukler,
        "ciro": veri.ciro if veri.ciro > 0 else None,
        "toplam_varliklar": veri.toplam_varliklar,
    }
    formula = "0.717×(İS/V) + 0.847×(DK/V) + 3.107×(FVÖK/V) + 0.420×(ÖK/Y) + 0.998×(Ciro/V)"
    if any(deger is None for deger in girdiler.values()) or not veri.toplam_yukumlulukler:
        return _eksik(
            "ALTMAN_Z_PRIME_PRIVATE_MANUFACTURING",
            formula,
            "skor",
            girdiler,
            girdiler.keys(),
            "Özel imalat şirketleri için Z' modeli; sektör ve şirket türü doğrulanmalıdır.",
        )
    varlik = float(veri.toplam_varliklar)
    isletme_sermayesi = float(veri.donen_varliklar) - veri.kisa_vadeli_borc
    z = (
        0.717 * (isletme_sermayesi / varlik)
        + 0.847 * (float(veri.dagitilmamis_karlar) / varlik)
        + 3.107 * (float(ebit) / varlik)
        + 0.420 * (veri.ozkaynak / float(veri.toplam_yukumlulukler))
        + 0.998 * (veri.ciro / varlik)
    )
    return _sonuc(
        z,
        "ALTMAN_Z_PRIME_PRIVATE_MANUFACTURING",
        formula,
        "skor",
        girdiler,
        girdiler.keys(),
        "Z' < 1,23 riskli; 1,23–2,90 gri; > 2,90 güvenli bölge. Tek başına kredi/iflas kararı değildir.",
    )


def dupont_roe(veri: FinansalGorunum) -> MetrikSonucu:
    girdiler = {
        "net_kar": veri.net_kar,
        "ciro": veri.ciro if veri.ciro > 0 else None,
        "toplam_varliklar": veri.toplam_varliklar,
        "ozkaynak": veri.ozkaynak if veri.ozkaynak > 0 else None,
    }
    formula = "(Net kâr/Ciro) × (Ciro/Toplam varlık) × (Toplam varlık/Özkaynak)"
    if any(deger is None for deger in girdiler.values()):
        return _eksik("DUPONT_ROE_3_STEP", formula, "%", girdiler, girdiler.keys(), "Üç aşamalı DuPont ROE ayrıştırması.")
    roe = (veri.net_kar / veri.ciro) * (veri.ciro / float(veri.toplam_varliklar)) * (float(veri.toplam_varliklar) / veri.ozkaynak) * 100
    return _sonuc(roe, "DUPONT_ROE_3_STEP", formula, "%", girdiler, girdiler.keys(), "Üç aşamalı DuPont ROE ayrıştırması.")


def roic(veri: FinansalGorunum) -> MetrikSonucu:
    ebit = _ebit(veri)
    if veri.etkin_vergi_orani is not None:
        vergi_orani = veri.etkin_vergi_orani / 100
        vergi_kaynagi = "etkin_vergi_orani"
    else:
        vergi_oncesi_kar = veri.net_kar + veri.vergi_gideri if veri.vergi_gideri is not None else None
        vergi_orani = (
            veri.vergi_gideri / vergi_oncesi_kar
            if veri.vergi_gideri is not None and vergi_oncesi_kar and vergi_oncesi_kar > 0
            else None
        )
        vergi_kaynagi = "vergi_gideri/net_kar"
    yatirilan_sermaye = veri.kisa_vadeli_borc + veri.uzun_vadeli_borc + veri.ozkaynak - veri.nakit
    girdiler = {
        "ebit": ebit,
        "etkin_vergi_orani": vergi_orani,
        "yatirilan_sermaye": yatirilan_sermaye if yatirilan_sermaye > 0 else None,
    }
    formula = "EBIT × (1 − etkin vergi oranı) / (Faizli borç + özkaynak − nakit)"
    if any(deger is None for deger in girdiler.values()):
        return _eksik("ROIC_NOPAT", formula, "%", girdiler, ["faiz_gideri", "vergi_gideri", vergi_kaynagi, "kisa_vadeli_borc", "uzun_vadeli_borc", "ozkaynak", "nakit"], "Kısa vadeli borcun faizli borç niteliği kullanıcı tarafından doğrulanmalıdır.")
    deger = float(ebit) * (1 - float(vergi_orani)) / yatirilan_sermaye * 100
    return _sonuc(deger, "ROIC_NOPAT", formula, "%", girdiler, ["faiz_gideri", "vergi_gideri", vergi_kaynagi, "kisa_vadeli_borc", "uzun_vadeli_borc", "ozkaynak", "nakit"], "Kısa vadeli borcun faizli borç niteliği kullanıcı tarafından doğrulanmalıdır.", guven="orta")


def serbest_nakit_akisi(veri: FinansalGorunum) -> MetrikSonucu:
    girdiler = {"operasyonel_nakit_akisi": veri.operasyonel_nakit_akisi, "capex": veri.capex}
    formula = "Operasyonel nakit akışı − CapEx"
    if any(deger is None for deger in girdiler.values()):
        return _eksik("FREE_CASH_FLOW", formula, "TRY", girdiler, girdiler.keys(), "Net kâr operasyonel nakit akışı yerine kullanılmaz.")
    return _sonuc(float(veri.operasyonel_nakit_akisi) - float(veri.capex), "FREE_CASH_FLOW", formula, "TRY", girdiler, girdiler.keys(), "Net kâr operasyonel nakit akışı yerine kullanılmaz.")


def nakit_donusum_dongusu(veri: FinansalGorunum) -> MetrikSonucu:
    gun = float(veri.donem_gun_sayisi) if veri.donem_gun_sayisi is not None else None
    girdiler = {
        "alacaklar": veri.alacaklar,
        "stoklar": veri.stoklar,
        "borclar": veri.borclar,
        "ciro": veri.ciro if veri.ciro > 0 else None,
        "satis_maliyeti": veri.satis_maliyeti if veri.satis_maliyeti > 0 else None,
        "donem_gun_sayisi": gun,
    }
    formula = "DSO + DIO − DPO; DSO=Alacak/Ciro×Gün, DIO=Stok/SM×Gün, DPO=Ticari borç/SM×Gün"
    if any(deger is None for deger in girdiler.values()):
        return _eksik("CASH_CONVERSION_CYCLE_FULL", formula, "gün", girdiler, girdiler.keys(), "Dönem sonu bakiyeleri kullanılıyorsa ortalama bakiye yöntemine göre güven sınırlıdır.")
    dso = veri.alacaklar / veri.ciro * gun
    dio = veri.stoklar / veri.satis_maliyeti * gun
    dpo = veri.borclar / veri.satis_maliyeti * gun
    return _sonuc(dso + dio - dpo, "CASH_CONVERSION_CYCLE_FULL", formula, "gün", girdiler, girdiler.keys(), f"Bileşenler: DSO={dso:.2f}, DIO={dio:.2f}, DPO={dpo:.2f}. Dönem sonu bakiye yöntemi.", guven="orta")


def _devir_gunu(
    pay: float,
    payda: Optional[float],
    gun: Optional[float],
    formula_id: str,
    formula: str,
    pay_adi: str,
    payda_adi: str,
    metodoloji: str,
) -> MetrikSonucu:
    """Alacak/stok/borç devir günü — üçü de aynı payda × gün kalıbını kullanır."""
    girdiler = {pay_adi: pay, payda_adi: payda, "donem_gun_sayisi": gun}
    if any(deger is None for deger in girdiler.values()):
        return _eksik(formula_id, formula, "gün", girdiler, girdiler.keys(), metodoloji)
    return _sonuc(
        pay / float(payda) * float(gun), formula_id, formula, "gün",
        girdiler, girdiler.keys(), metodoloji, guven="orta",
    )


def alacak_devir_gunu(veri: FinansalGorunum) -> MetrikSonucu:
    """DSO — tahsilat süresi. Ekranlarda 365 varsayımı yerine bu kullanılmalıdır."""
    return _devir_gunu(
        veri.alacaklar, veri.ciro if veri.ciro > 0 else None,
        float(veri.donem_gun_sayisi) if veri.donem_gun_sayisi is not None else None,
        "DAYS_SALES_OUTSTANDING", "Ticari alacaklar / Ciro × Dönem gün sayısı",
        "alacaklar", "ciro",
        "Dönem sonu bakiye yöntemi; dönem gün sayısı kayıttan alınır, sabit 365 varsayılmaz.",
    )


def stok_devir_gunu(veri: FinansalGorunum) -> MetrikSonucu:
    """DIO — stokta kalma süresi."""
    return _devir_gunu(
        veri.stoklar, veri.satis_maliyeti if veri.satis_maliyeti > 0 else None,
        float(veri.donem_gun_sayisi) if veri.donem_gun_sayisi is not None else None,
        "DAYS_INVENTORY_OUTSTANDING", "Stoklar / Satış maliyeti × Dönem gün sayısı",
        "stoklar", "satis_maliyeti",
        "Dönem sonu bakiye yöntemi; dönem gün sayısı kayıttan alınır.",
    )


def borc_devir_gunu(veri: FinansalGorunum) -> MetrikSonucu:
    """DPO — tedarikçiye ödeme süresi."""
    return _devir_gunu(
        veri.borclar, veri.satis_maliyeti if veri.satis_maliyeti > 0 else None,
        float(veri.donem_gun_sayisi) if veri.donem_gun_sayisi is not None else None,
        "DAYS_PAYABLE_OUTSTANDING", "Ticari borçlar / Satış maliyeti × Dönem gün sayısı",
        "borclar", "satis_maliyeti",
        "Dönem sonu bakiye yöntemi; dönem gün sayısı kayıttan alınır.",
    )


def musteri_hhi(veri: FinansalGorunum) -> MetrikSonucu:
    toplam = sum(satir.ciro for satir in veri.musteri_cirolari)
    girdiler = {"musteri_sayisi": float(len(veri.musteri_cirolari)) if veri.musteri_cirolari else None, "toplam_musteri_cirosu": toplam if toplam > 0 else None}
    formula = "Σ (müşteri cirosu / toplam müşteri cirosu × 100)²"
    if any(deger is None for deger in girdiler.values()):
        return _eksik("CUSTOMER_REVENUE_HHI", formula, "0-10000", girdiler, ["musteri_cirolari"], "Gelir konsantrasyonudur; alacak konsantrasyonundan farklıdır.")
    hhi = sum((satir.ciro / toplam * 100) ** 2 for satir in veri.musteri_cirolari)
    return _sonuc(hhi, "CUSTOMER_REVENUE_HHI", formula, "0-10000", girdiler, ["musteri_cirolari"], "HHI < 1.500 düşük; 1.500–2.500 orta; > 2.500 yüksek yoğunlaşma.")


def kurumsal_metrikleri_hesapla(veri: FinansalGorunum) -> Dict[str, Dict[str, Any]]:
    metrikler = {
        "altman_z_prime": altman_z_prime(veri),
        "dupont_roe": dupont_roe(veri),
        "roic": roic(veri),
        "serbest_nakit_akisi": serbest_nakit_akisi(veri),
        "nakit_donusum_dongusu": nakit_donusum_dongusu(veri),
        "alacak_devir_gunu": alacak_devir_gunu(veri),
        "stok_devir_gunu": stok_devir_gunu(veri),
        "borc_devir_gunu": borc_devir_gunu(veri),
        "musteri_hhi": musteri_hhi(veri),
    }
    return {ad: sonuc.json() for ad, sonuc in metrikler.items()}

"""AI açıklamalarını doğrulanmış finans motoru çıktılarıyla sınırlar.

Dil modeli hesaplama kaynağı değildir. Bu modül, modelin yanıtında geçen her
sayısal değerin finans motorunda veya motorun kontrollü politika metinlerinde
bir karşılığı olmasını zorunlu kılar. Karşılığı olmayan yanıt kullanıcıya
gösterilmez ve orkestratör bir sonraki sağlayıcıyı dener.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


_SAYI_DESENI = re.compile(
    r"(?<![\w])[-+]?(?:\d{1,3}(?:(?:[.,]|\s)\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)*)"
    r"(?:\s*(?:bin|milyon|milyar|k|m|bn))?(?![\w])",
    flags=re.IGNORECASE,
)
_LISTE_NUMARASI = re.compile(r"(?m)^\s*\d{1,2}[.)]\s+")
_CARPANLAR = {
    "bin": 1_000.0,
    "k": 1_000.0,
    "milyon": 1_000_000.0,
    "m": 1_000_000.0,
    "milyar": 1_000_000_000.0,
    "bn": 1_000_000_000.0,
}


#: Ham girdi alanlarının kullanıcıya gösterilecek kaynak adı.
_GIRDI_ETIKETLERI = {
    "ciro": "Gelir tablosu · Ciro",
    "satis_maliyeti": "Gelir tablosu · Satış maliyeti",
    "faaliyet_giderleri": "Gelir tablosu · Faaliyet giderleri",
    "net_kar": "Gelir tablosu · Net kâr",
    "faiz_gideri": "Gelir tablosu · Faiz gideri",
    "vergi_gideri": "Gelir tablosu · Vergi gideri",
    "amortisman": "Gelir tablosu · Amortisman",
    "nakit": "Bilanço · Hazır değerler",
    "alacaklar": "Bilanço · Ticari alacaklar",
    "borclar": "Bilanço · Ticari borçlar",
    "stoklar": "Bilanço · Stoklar",
    "kisa_vadeli_borc": "Bilanço · Kısa vadeli borçlar",
    "uzun_vadeli_borc": "Bilanço · Uzun vadeli borçlar",
    "ozkaynak": "Bilanço · Özkaynak",
    "donen_varliklar": "Bilanço · Dönen varlıklar",
    "toplam_varliklar": "Bilanço · Toplam varlıklar",
    "toplam_yukumlulukler": "Bilanço · Toplam yükümlülükler",
    "capex": "Nakit akışı · Yatırım harcaması",
    "operasyonel_nakit_akisi": "Nakit akışı · Faaliyet",
    "yatirim_nakit_akisi": "Nakit akışı · Yatırım",
    "finansman_nakit_akisi": "Nakit akışı · Finansman",
    "donem_basi_nakit": "Nakit akışı · Dönem başı nakit",
}

#: Hesaplanmış metriklerin kullanıcıya gösterilecek kaynak adı.
_METRIK_ETIKETLERI = {
    "brut_kar": "Hesaplandı · Brüt kâr",
    "faaliyet_kari_yaklasik": "Hesaplandı · Faaliyet kârı",
    "favok": "Hesaplandı · FAVÖK",
    "net_kar_marji": "Hesaplandı · Net kâr marjı",
    "cari_oran": "Hesaplandı · Cari oran",
    "borc_ozkaynak_orani": "Hesaplandı · Borç / özkaynak",
    "net_isletme_sermayesi": "Hesaplandı · Net işletme sermayesi",
    "altman_z_prime": "Hesaplandı · Altman Z'",
    "dupont_roe": "Hesaplandı · DuPont ROE",
    "roic": "Hesaplandı · ROIC",
    "serbest_nakit_akisi": "Hesaplandı · Serbest nakit akışı",
    "nakit_donusum_dongusu": "Hesaplandı · Nakit dönüşüm döngüsü",
    "musteri_hhi": "Hesaplandı · Müşteri HHI",
}


@dataclass(frozen=True)
class SayiKaynagi:
    """Yanıtta geçen bir sayı ve bulunduğu kaynak."""

    ham: str
    kaynak: str


@dataclass(frozen=True)
class AIYanitDogrulamasi:
    uygun: bool
    kontrol_edilen_sayi: int
    reddedilen_sayilar: List[str]
    #: Kabul edilen sayılar ve eşleştikleri kaynak (sunum katmanı için).
    kaynak_eslesmeleri: List[SayiKaynagi] = field(default_factory=list)


class AIYanitiDogrulamaHatasi(RuntimeError):
    """AI yanıtı doğrulanmış sayısal kaynaklarla uyuşmadığında oluşur."""


def _sayi_adaylari(ham: str) -> List[float]:
    """Türkçe/İngilizce sayı gösterimlerini karşılaştırılabilir adaylara çevirir."""
    metin = ham.strip().lower().replace("\u00a0", " ")
    carpan = 1.0
    carpan_eslesmesi = re.search(r"\s*(bin|milyon|milyar|k|m|bn)$", metin, flags=re.I)
    if carpan_eslesmesi:
        carpan = _CARPANLAR[carpan_eslesmesi.group(1).lower()]
        metin = metin[: carpan_eslesmesi.start()].strip()

    isaret = -1.0 if metin.startswith("-") else 1.0
    metin = metin.lstrip("+-").replace(" ", "")
    if not metin:
        return []

    adaylar: List[float] = []
    ayiraclar = [i for i, karakter in enumerate(metin) if karakter in ",."]
    try:
        if not ayiraclar:
            adaylar.append(float(metin))
        elif len(ayiraclar) > 1:
            son = ayiraclar[-1]
            ondalik_hane = len(metin) - son - 1
            if ondalik_hane in (1, 2):
                tam = re.sub(r"[,.]", "", metin[:son]) or "0"
                adaylar.append(float(f"{tam}.{metin[son + 1:]}"))
            else:
                adaylar.append(float(re.sub(r"[,.]", "", metin)))
        else:
            ayirac = metin[ayiraclar[0]]
            sol, sag = metin.split(ayirac, 1)
            adaylar.append(float(f"{sol or '0'}.{sag}"))
            if len(sag) == 3:
                adaylar.append(float(f"{sol}{sag}"))
    except ValueError:
        return []

    return list(dict.fromkeys(isaret * aday * carpan for aday in adaylar))


def _metindeki_sayilar(metin: str) -> List[tuple[str, List[float]]]:
    numarasiz = _LISTE_NUMARASI.sub("", metin)
    return [(eslesme.group(0), _sayi_adaylari(eslesme.group(0))) for eslesme in _SAYI_DESENI.finditer(numarasiz)]


def _sayisal_degerler(deger: Any) -> Iterable[float]:
    if isinstance(deger, bool) or deger is None:
        return
    if isinstance(deger, (int, float)):
        yield float(deger)
        return
    if isinstance(deger, dict):
        for alt in deger.values():
            yield from _sayisal_degerler(alt)
    elif isinstance(deger, (list, tuple)):
        for alt in deger:
            yield from _sayisal_degerler(alt)


def _izinli_kaynaklar(
    denetim: Dict[str, Any],
    ek_guvenilir_metinler: Sequence[str],
) -> List[Tuple[float, str]]:
    """İzin verilen her sayıyı, kullanıcıya gösterilebilir kaynak adıyla eşler."""
    kaynaklar: List[Tuple[float, str]] = []

    # Kullanıcının bildirdiği ham değerler — AI kendi verisinden söz edebilmelidir.
    for ad, deger in (denetim.get("girdi_degerleri") or {}).items():
        if isinstance(deger, (int, float)) and not isinstance(deger, bool):
            kaynaklar.append((float(deger), _GIRDI_ETIKETLERI.get(ad, f"Girdi · {ad}")))

    for ad, deger in (denetim.get("metrikler") or {}).items():
        for sayi in _sayisal_degerler(deger):
            kaynaklar.append((sayi, _METRIK_ETIKETLERI.get(ad, f"Hesaplandı · {ad}")))

    for ad, kayit in (denetim.get("metrik_kaydi") or {}).items():
        if (
            isinstance(kayit, dict)
            and kayit.get("durum") == "hesaplandi"
            and isinstance(kayit.get("deger"), (int, float))
        ):
            kaynaklar.append((float(kayit["deger"]), _METRIK_ETIKETLERI.get(ad, f"Hesaplandı · {ad}")))

    kalite_skoru = (denetim.get("veri_kalitesi") or {}).get("skor")
    if isinstance(kalite_skoru, (int, float)):
        kaynaklar.append((float(kalite_skoru), "Veri kalitesi skoru"))

    politika_metinleri = [
        *denetim.get("riskler", []),
        *denetim.get("aksiyonlar", []),
        *ek_guvenilir_metinler,
    ]
    for metin in politika_metinleri:
        for _, adaylar in _metindeki_sayilar(str(metin)):
            kaynaklar.extend((aday, "Kural tabanlı politika metni") for aday in adaylar)

    return kaynaklar


def _izinli_sayilar(denetim: Dict[str, Any], ek_guvenilir_metinler: Sequence[str]) -> List[float]:
    """Geriye dönük uyumluluk: yalnızca izin verilen sayı değerleri."""
    return list(dict.fromkeys(deger for deger, _ in _izinli_kaynaklar(denetim, ek_guvenilir_metinler)))


def _eslesen_kaynak(
    adaylar: Sequence[float],
    kaynaklar: Sequence[Tuple[float, str]],
) -> Optional[str]:
    """Adaylardan biri bir kaynağa oturuyorsa o kaynağın adını döndürür."""
    for aday in adaylar:
        for deger, etiket in kaynaklar:
            tolerans = max(0.015, abs(deger) * 0.005)
            if abs(aday - deger) <= tolerans:
                return etiket
    return None


def _eslesiyor(adaylar: Sequence[float], izinli: Sequence[float]) -> bool:
    return _eslesen_kaynak(adaylar, [(deger, "") for deger in izinli]) is not None


def ai_yanitini_dogrula(
    metin: str,
    denetim: Dict[str, Any],
    *,
    ek_guvenilir_metinler: Sequence[str] = (),
) -> AIYanitDogrulamasi:
    """Yanıttaki her sayının doğrulanmış veya kontrollü bir kaynağı olduğunu denetler."""
    sayilar = _metindeki_sayilar(metin)
    kaynaklar = _izinli_kaynaklar(denetim, ek_guvenilir_metinler)

    reddedilen: List[str] = []
    eslesmeler: List[SayiKaynagi] = []
    for ham, adaylar in sayilar:
        etiket = _eslesen_kaynak(adaylar, kaynaklar) if adaylar else None
        if etiket is None:
            reddedilen.append(ham)
        else:
            eslesmeler.append(SayiKaynagi(ham=ham, kaynak=etiket))

    return AIYanitDogrulamasi(
        uygun=not reddedilen,
        kontrol_edilen_sayi=len(sayilar),
        reddedilen_sayilar=list(dict.fromkeys(reddedilen)),
        kaynak_eslesmeleri=eslesmeler,
    )

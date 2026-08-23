"""AI açıklamalarını doğrulanmış finans motoru çıktılarıyla sınırlar.

Dil modeli hesaplama kaynağı değildir. Bu modül, modelin yanıtında geçen her
sayısal değerin finans motorunda veya motorun kontrollü politika metinlerinde
bir karşılığı olmasını zorunlu kılar. Karşılığı olmayan yanıt kullanıcıya
gösterilmez ve orkestratör bir sonraki sağlayıcıyı dener.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Sequence


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


@dataclass(frozen=True)
class AIYanitDogrulamasi:
    uygun: bool
    kontrol_edilen_sayi: int
    reddedilen_sayilar: List[str]


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


def _izinli_sayilar(denetim: Dict[str, Any], ek_guvenilir_metinler: Sequence[str]) -> List[float]:
    izinli = list(_sayisal_degerler(denetim.get("metrikler", {})))
    izinli.extend(
        float(kayit["deger"])
        for kayit in denetim.get("metrik_kaydi", {}).values()
        if isinstance(kayit, dict)
        and kayit.get("durum") == "hesaplandi"
        and isinstance(kayit.get("deger"), (int, float))
    )
    kalite_skoru = denetim.get("veri_kalitesi", {}).get("skor")
    if isinstance(kalite_skoru, (int, float)):
        izinli.append(float(kalite_skoru))

    politika_metinleri = [
        *denetim.get("riskler", []),
        *denetim.get("aksiyonlar", []),
        *ek_guvenilir_metinler,
    ]
    for metin in politika_metinleri:
        for _, adaylar in _metindeki_sayilar(str(metin)):
            izinli.extend(adaylar)
    return list(dict.fromkeys(izinli))


def _eslesiyor(adaylar: Sequence[float], izinli: Sequence[float]) -> bool:
    for aday in adaylar:
        for kaynak in izinli:
            tolerans = max(0.015, abs(kaynak) * 0.005)
            if abs(aday - kaynak) <= tolerans:
                return True
    return False


def ai_yanitini_dogrula(
    metin: str,
    denetim: Dict[str, Any],
    *,
    ek_guvenilir_metinler: Sequence[str] = (),
) -> AIYanitDogrulamasi:
    """Yanıttaki her sayının doğrulanmış veya kontrollü bir kaynağı olduğunu denetler."""
    sayilar = _metindeki_sayilar(metin)
    izinli = _izinli_sayilar(denetim, ek_guvenilir_metinler)
    reddedilen = [ham for ham, adaylar in sayilar if not adaylar or not _eslesiyor(adaylar, izinli)]
    return AIYanitDogrulamasi(
        uygun=not reddedilen,
        kontrol_edilen_sayi=len(sayilar),
        reddedilen_sayilar=list(dict.fromkeys(reddedilen)),
    )

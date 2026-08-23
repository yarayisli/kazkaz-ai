"""TCMB döviz alış kurlarını açıklanabilir ve önbellekli biçimde okur."""

from __future__ import annotations

import threading
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from typing import Callable, Dict, Iterable, Tuple


DESTEKLENEN_KURLAR = {"USD", "EUR", "GBP", "CHF", "JPY", "CAD", "AUD", "SEK", "NOK", "DKK", "SAR"}
_ONBELLEK: Dict[date, Tuple[date, Dict[str, float]]] = {}
_KILIT = threading.Lock()


class KurHatasi(ValueError):
    pass


def para_birimlerini_dogrula(para_birimleri: Iterable[str]) -> list[str]:
    temiz = []
    for kod in para_birimleri:
        kod = str(kod).strip().upper()
        if kod == "TRY":
            continue
        if kod not in DESTEKLENEN_KURLAR:
            raise KurHatasi(f"Desteklenmeyen para birimi: {kod}")
        if kod not in temiz:
            temiz.append(kod)
    return temiz


def tcmb_xml_kurlarini_oku(icerik: bytes) -> Dict[str, float]:
    """TCMB XML içindeki birim başına döviz alış kurunu TRY olarak çözer."""
    try:
        kok = ET.fromstring(icerik)
    except ET.ParseError as exc:
        raise KurHatasi("TCMB kur yanıtı geçerli XML değil.") from exc
    kurlar: Dict[str, float] = {}
    for dugum in kok.findall("Currency"):
        kod = (dugum.attrib.get("CurrencyCode") or "").upper()
        alis = (dugum.findtext("ForexBuying") or "").strip()
        birim = (dugum.findtext("Unit") or "1").strip()
        if kod and alis:
            try:
                deger = float(alis) / float(birim)
            except (TypeError, ValueError, ZeroDivisionError):
                continue
            if deger > 0:
                kurlar[kod] = deger
    if not kurlar:
        raise KurHatasi("TCMB yanıtında kullanılabilir döviz alış kuru bulunamadı.")
    return kurlar


def _indir(tarih: date, timeout: float = 8.0) -> bytes:
    url = f"https://www.tcmb.gov.tr/kurlar/{tarih:%Y%m}/{tarih:%d%m%Y}.xml"
    istek = urllib.request.Request(url, headers={"User-Agent": "KazKaz-AI/1.0"})
    with urllib.request.urlopen(istek, timeout=timeout) as yanit:
        if getattr(yanit, "status", 200) != 200:
            raise KurHatasi("TCMB kur servisi başarılı yanıt vermedi.")
        return yanit.read(1_000_000)


def tarihsel_kurlari_getir(
    istenen_tarih: date,
    para_birimleri: Iterable[str],
    indirici: Callable[[date], bytes] = _indir,
) -> dict:
    """Tatil/hafta sonunda en fazla 7 gün geriye giderek resmi kuru bulur."""
    if istenen_tarih > date.today():
        raise KurHatasi("Gelecek tarih için gerçekleşmiş TCMB kuru kullanılamaz.")
    kodlar = para_birimlerini_dogrula(para_birimleri)
    if not kodlar:
        return {
            "istenen_tarih": istenen_tarih.isoformat(), "kur_tarihi": istenen_tarih.isoformat(),
            "baz_para_birimi": "TRY", "kurlar": {"TRY": 1.0}, "kaynak": "sabit",
            "metodoloji": "TRY için dönüşüm uygulanmadı.",
        }

    with _KILIT:
        onbellek = _ONBELLEK.get(istenen_tarih)
    if onbellek and all(kod in onbellek[1] for kod in kodlar):
        kur_tarihi, tum_kurlar = onbellek
    else:
        son_hata: Exception | None = None
        tum_kurlar = {}
        kur_tarihi = istenen_tarih
        for gun_farki in range(8):
            aday = istenen_tarih - timedelta(days=gun_farki)
            try:
                tum_kurlar = tcmb_xml_kurlarini_oku(indirici(aday))
                kur_tarihi = aday
                break
            except (KurHatasi, urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
                son_hata = exc
        if not tum_kurlar:
            raise KurHatasi("İstenen tarih veya önceki 7 gün için TCMB kuru alınamadı.") from son_hata
        with _KILIT:
            _ONBELLEK[istenen_tarih] = (kur_tarihi, tum_kurlar)

    eksik = [kod for kod in kodlar if kod not in tum_kurlar]
    if eksik:
        raise KurHatasi(f"TCMB yanıtında kur bulunamadı: {', '.join(eksik)}")
    return {
        "istenen_tarih": istenen_tarih.isoformat(),
        "kur_tarihi": kur_tarihi.isoformat(),
        "baz_para_birimi": "TRY",
        "kurlar": {"TRY": 1.0, **{kod: round(tum_kurlar[kod], 8) for kod in kodlar}},
        "kaynak": "TCMB Elektronik Veri Dağıtım Sistemi",
        "metodoloji": "Bir döviz birimi için TCMB döviz alış kuru; tatilde önceki mevcut iş günü kullanılır.",
    }

"""Excel sütun başlıklarını kanonik alanlara eşler ve raporlar.

Şirketler aynı finansal veriyi farklı başlıklarla tutar: biri "Ciro"
yazar, diğeri "Hasılat", bir başkası "Gelir". Yerleşik eş anlamlı
listesi bunların çoğunu yakalar ama hepsini değil. Yakalayamadığında
kullanıcı bir kez elle eşler; bu eşleme şirket bazında kaydedilir ve
sonraki yüklemelerde tekrar sorulmaz.

Bu modül iki işi yapar:
  1. Tespit edilen başlıkları (yerleşik + kayıtlı eşleme ile) çözer.
  2. Neyin tanındığını, neyin çözülemediğini raporlar — arayüz bu
     rapora bakıp yalnızca eksik sütunları kullanıcıya sorar.

Kayıtlı eşleme anahtarları normalize edilmiş başlıktır (_anahtar ile:
"Firma Adı" → "firma_adi"); değeri kanonik alandır ("musteri").
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def sutunlari_coz(
    basliklar: Dict[int, str],
    yerlesik: Dict[str, str],
    kayitli_esleme: Optional[Dict[str, str]] = None,
) -> Dict[int, Optional[str]]:
    """Her sütun indeksini kanonik alana çözer.

    Öncelik: kayıtlı eşleme > yerleşik eş anlamlılar. Kullanıcının
    kaydettiği eşleme, yerleşik tahmini bilerek ezebilir.
    """
    kayitli = kayitli_esleme or {}
    cozum: Dict[int, Optional[str]] = {}
    for indeks, normalize_baslik in basliklar.items():
        if normalize_baslik in kayitli:
            cozum[indeks] = kayitli[normalize_baslik]
        else:
            cozum[indeks] = yerlesik.get(normalize_baslik)
    return cozum


def sutun_raporu(
    basliklar: Dict[int, str],
    cozum: Dict[int, Optional[str]],
    ham_basliklar: Optional[Dict[int, Any]] = None,
) -> Dict[str, Any]:
    """Tanınan ve çözülemeyen sütunları arayüz için raporlar.

    ham_basliklar verilirse kullanıcıya orijinal başlık metni gösterilir
    (normalize edilmiş "firma_adi" değil, gerçekteki "Firma Adı").
    """
    ham = ham_basliklar or {}
    taninanlar: List[Dict[str, Any]] = []
    cozulemeyenler: List[Dict[str, Any]] = []
    for indeks, normalize_baslik in basliklar.items():
        kayit = {
            "indeks": indeks,
            "baslik": str(ham.get(indeks, normalize_baslik)),
            "normalize": normalize_baslik,
        }
        alan = cozum.get(indeks)
        if alan:
            taninanlar.append({**kayit, "alan": alan})
        else:
            cozulemeyenler.append(kayit)
    return {
        "taninan_sutunlar": taninanlar,
        "cozulemeyen_sutunlar": cozulemeyenler,
        "tam_eslesme": not cozulemeyenler,
    }

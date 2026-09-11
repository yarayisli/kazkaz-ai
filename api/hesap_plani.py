"""Tekdüzen Hesap Planı kodlarını finansal tablo kategorilerine eşler.

Türkiye'de hesap kodları Tekdüzen Hesap Planı ile standarttır: 600 her
zaman yurtiçi satış, 100 her zaman kasadır. Bu yüzden mizan satırları
kullanıcı hiçbir şey etiketlemeden sınıflandırılabilir.

Kullanıcının verdiği `esleme` alanı her zaman önceliklidir; buradaki
eşleme yalnızca o alan boşken devreye girer.

**7'li maliyet hesapları bilerek eşlenmez.** 7/A ve 7/B gruplarındaki
giderler yansıtma hesapları üzerinden 6'lı gruba aktarılır; ikisini de
toplamak gideri iki kez sayar. Bu hesaplar `yansitma_hesaplari()` ile
ayrıca raporlanır, "tanınmayan hesap" gibi gösterilmez.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

#: (önek, kategori) — en uzun önek kazanır, bu yüzden sıra önemsizdir.
_ONEK_ESLEMESI: Dict[str, str] = {
    # ── 1 · Dönen varlıklar ────────────────────────────────────────────
    "10": "nakit",            # Hazır değerler: kasa, banka, alınan çekler
    "11": "diger_donen",      # Menkul kıymetler
    "12": "alacaklar",        # Ticari alacaklar (129 karşılık negatiftir)
    "13": "alacaklar",        # Diğer alacaklar
    "15": "stoklar",
    "17": "diger_donen",      # Yıllara yaygın inşaat maliyetleri
    "18": "diger_donen",      # Gelecek aylara ait giderler
    "19": "diger_donen",

    # ── 2 · Duran varlıklar ───────────────────────────────────────────
    "22": "duran_varlik",     # Uzun vadeli ticari alacaklar
    "23": "duran_varlik",
    "24": "duran_varlik",     # Mali duran varlıklar
    "25": "duran_varlik",     # Maddi duran varlıklar (257 amortisman negatiftir)
    "26": "duran_varlik",     # Maddi olmayan duran varlıklar
    "27": "duran_varlik",     # Özel tükenmeye tabi varlıklar
    "28": "duran_varlik",     # Gelecek yıllara ait giderler
    "29": "duran_varlik",

    # ── 3 · Kısa vadeli yabancı kaynaklar ─────────────────────────────
    "30": "kisa_vadeli_borc",  # Mali borçlar: banka kredileri
    "32": "ticari_borc",       # Satıcılar, borç senetleri
    "33": "kisa_vadeli_borc",  # Diğer borçlar
    "34": "kisa_vadeli_borc",  # Alınan avanslar
    "35": "kisa_vadeli_borc",  # Yıllara yaygın inşaat hakedişleri
    "36": "kisa_vadeli_borc",  # Ödenecek vergi ve yükümlülükler
    "37": "karsilik",          # Borç ve gider karşılıkları
    "38": "kisa_vadeli_borc",  # Gelecek aylara ait gelirler
    "39": "kisa_vadeli_borc",

    # ── 4 · Uzun vadeli yabancı kaynaklar ─────────────────────────────
    "40": "uzun_vadeli_borc",
    "42": "uzun_vadeli_borc",
    "43": "uzun_vadeli_borc",
    "44": "uzun_vadeli_borc",
    "47": "karsilik",          # Borç ve gider karşılıkları (uzun vadeli)
    "48": "uzun_vadeli_borc",
    "49": "uzun_vadeli_borc",

    # ── 5 · Özkaynaklar ───────────────────────────────────────────────
    "50": "ozkaynak",          # Sermaye (501 ödenmemiş sermaye negatiftir)
    "52": "ozkaynak",          # Sermaye yedekleri
    "54": "ozkaynak",          # Kâr yedekleri
    "57": "gecmis_yil_kari",   # Geçmiş yıllar kârları
    "58": "gecmis_yil_kari",   # Geçmiş yıllar zararları (negatif)
    "59": "donem_kari",        # 590 dönem net kârı / 591 zararı

    # ── 6 · Gelir tablosu ─────────────────────────────────────────────
    "60": "ciro",              # Brüt satışlar
    "61": "ciro",              # Satış indirimleri (borç bakiye → ciroyu düşürür)
    "62": "satis_maliyeti",
    "63": "faaliyet_gideri",   # Ar-Ge, pazarlama, genel yönetim
    "64": "diger_gelir",       # Diğer faaliyetlerden olağan gelirler
    "65": "faaliyet_gideri",   # Diğer faaliyetlerden gider ve zararlar
    "66": "faiz_gideri",       # Finansman giderleri
    "67": "diger_gelir",       # Olağandışı gelir ve kârlar
    "68": "faaliyet_gideri",   # Çalışmayan kısım gider ve zararları
}

#: Sonuç hesapları — bakiyeleri türetilmiş tutarlardır, toplanmaz.
_SONUC_HESAPLARI = {"690", "692", "693"}

#: Dönem kârı vergi karşılığı, gelir tablosunda vergi gideri satırıdır.
_OZEL_KODLAR: Dict[str, str] = {
    "691": "vergi_gideri",
}


def _temiz_kod(hesap_kodu: Optional[str]) -> str:
    """Kodu rakamlara indirger: '120.01.001' → '12001001', '120-01' → '12001'."""
    if not hesap_kodu:
        return ""
    return "".join(karakter for karakter in str(hesap_kodu) if karakter.isdigit())


def maliyet_hesabi_mi(hesap_kodu: Optional[str]) -> bool:
    """7'li maliyet hesabı mı? Bunlar 6'lı gruba yansıtılır, ayrıca toplanmaz."""
    return _temiz_kod(hesap_kodu).startswith("7")


def kategori_bul(hesap_kodu: Optional[str]) -> Optional[str]:
    """Hesap kodundan finansal tablo kategorisini bulur.

    Eşleşme bulunamazsa None döner — uyduran bir tahmin üretilmez.
    """
    kod = _temiz_kod(hesap_kodu)
    if not kod:
        return None

    uc_hane = kod[:3]
    if uc_hane in _SONUC_HESAPLARI:
        return None
    if uc_hane in _OZEL_KODLAR:
        return _OZEL_KODLAR[uc_hane]

    # 7'li maliyet hesapları bilerek eşlenmez (yansıtma çift sayıma yol açar).
    if kod.startswith("7"):
        return None

    return _ONEK_ESLEMESI.get(kod[:2])


def kod_ozeti() -> Tuple[int, int]:
    """(eşlenen önek sayısı, özel kod sayısı) — teşhis ve test için."""
    return len(_ONEK_ESLEMESI), len(_OZEL_KODLAR)

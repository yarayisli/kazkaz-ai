"""Şirketi sektör ortalamasıyla değil, kendi geçmişiyle karşılaştırır.

Sektör ortalaması "normal miyim?" sorusuna cevap verir; bu bir karar
üretmez. Şirketin kendi trendi "ne değişti, ne yapmalıyım?" sorusuna
cevap verir — ve o soru nakit kararına dönüşür.

Ayrıca kaynak sorumluluğu doğurmaz: veri kullanıcının kendi mizanından
gelir, dışarıdan alınmaz, güncelliği kullanıcının yükleme sıklığına
bağlıdır.

Gün bazlı metrikler (DSO/DIO/DPO) dönem gün sayısını ister. Mizan
dönemleri gün sayısı taşımadığı için çağıran taraf `donem_gun_sayisi`
verir; verilmezse bu metrikler hesaplanmaz — 365 varsayılmaz.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

#: Bir metriğin anlamlı sayılması için gereken en küçük göreli değişim.
#: Bunun altındaki oynamalar gürültüdür, kullanıcıya bildirilmez.
ONEMLI_DEGISIM_ESIGI = 0.05  # %5


def _bol(pay: Optional[float], payda: Optional[float]) -> Optional[float]:
    """Sıfır ve None paydayı güvenle eler; 0 ile eksik veriyi ayırır."""
    if pay is None or payda is None or payda == 0:
        return None
    return pay / payda


def _donem_metrikleri(tablo: Dict[str, Any], donem_gun_sayisi: Optional[int]) -> Dict[str, Optional[float]]:
    """Tek bir mizan döneminden karşılaştırılabilir metrikleri çıkarır."""
    g = tablo.get("gelir_tablosu") or {}
    b = tablo.get("bilanco") or {}
    ciro = g.get("ciro")
    smm = g.get("satis_maliyeti")
    gun = float(donem_gun_sayisi) if donem_gun_sayisi else None

    yuzde = lambda pay, payda: (None if _bol(pay, payda) is None else _bol(pay, payda) * 100)

    return {
        "ciro": ciro,
        "brut_kar_marji": yuzde(g.get("brut_kar"), ciro),
        "faaliyet_kar_marji": yuzde(g.get("faaliyet_kari"), ciro),
        "net_kar_marji": yuzde(g.get("net_kar"), ciro),
        "alacak_devir_gunu": None if gun is None or _bol(b.get("alacaklar"), ciro) is None
            else _bol(b.get("alacaklar"), ciro) * gun,
        "stok_devir_gunu": None if gun is None or _bol(b.get("stoklar"), smm) is None
            else _bol(b.get("stoklar"), smm) * gun,
        "borc_devir_gunu": None if gun is None or _bol(b.get("ticari_borc"), smm) is None
            else _bol(b.get("ticari_borc"), smm) * gun,
        "cari_oran": _bol(b.get("donen_varliklar"), b.get("kisa_vadeli_borc")),
        "nakit": b.get("nakit"),
    }


#: Metrik adı → (kullanıcıya görünen ad, birim, artış iyi mi?)
METRIK_TANIMLARI: Dict[str, tuple] = {
    "ciro": ("Ciro", "tutar", True),
    "brut_kar_marji": ("Brüt kâr marjı", "yuzde", True),
    "faaliyet_kar_marji": ("Faaliyet kâr marjı", "yuzde", True),
    "net_kar_marji": ("Net kâr marjı", "yuzde", True),
    "alacak_devir_gunu": ("Tahsilat süresi", "gun", False),
    "stok_devir_gunu": ("Stokta kalma süresi", "gun", False),
    "borc_devir_gunu": ("Tedarikçiye ödeme süresi", "gun", True),
    "cari_oran": ("Cari oran", "kat", True),
    "nakit": ("Kasadaki nakit", "tutar", True),
}


def _nakit_etkisi(
    metrik: str,
    onceki: Optional[float],
    son: Optional[float],
    son_ciro: Optional[float],
    donem_gun_sayisi: Optional[int],
) -> Optional[float]:
    """Tahsilat süresindeki değişimin bağladığı/serbest bıraktığı para.

    DSO 30 günden 42 güne çıktıysa, 12 günlük fark × günlük ciro kadar
    para müşteride bağlı kalıyor demektir. Pozitif değer bağlanan,
    negatif değer serbest kalan tutardır.
    """
    if metrik != "alacak_devir_gunu":
        return None
    if onceki is None or son is None or not son_ciro or not donem_gun_sayisi:
        return None
    gunluk_ciro = son_ciro / float(donem_gun_sayisi)
    return round((son - onceki) * gunluk_ciro, 2)


def donem_karsilastirmasi(
    tablolar: List[Dict[str, Any]],
    donem_gun_sayisi: Optional[int] = None,
) -> Dict[str, Any]:
    """Son dönemi bir öncekiyle karşılaştırır.

    En az iki dönem yoksa `durum: "gecmis_yok"` döner — uydurma bir
    karşılaştırma üretilmez.
    """
    if not tablolar or len(tablolar) < 2:
        return {
            "durum": "gecmis_yok",
            "donem_sayisi": len(tablolar or []),
            "aciklama": "Karşılaştırma için en az iki dönemlik mizan gerekir.",
            "degisimler": [],
        }

    onceki_tablo, son_tablo = tablolar[-2], tablolar[-1]
    onceki = _donem_metrikleri(onceki_tablo, donem_gun_sayisi)
    son = _donem_metrikleri(son_tablo, donem_gun_sayisi)
    son_ciro = son.get("ciro")

    degisimler: List[Dict[str, Any]] = []
    for metrik, (etiket, birim, artis_iyi) in METRIK_TANIMLARI.items():
        onceki_deger, son_deger = onceki.get(metrik), son.get(metrik)
        if onceki_deger is None or son_deger is None:
            continue

        fark = son_deger - onceki_deger
        # Göreli değişim: önceki sıfırsa oran tanımsızdır, None kalır.
        goreli = None if onceki_deger == 0 else fark / abs(onceki_deger)
        onemli = goreli is not None and abs(goreli) >= ONEMLI_DEGISIM_ESIGI

        yon = "sabit" if fark == 0 else ("artti" if fark > 0 else "azaldi")
        # Yön iyi mi kötü mü, metriğin doğasına bağlı: ciro artışı iyi,
        # tahsilat süresi artışı kötü.
        if fark == 0:
            deger_yargisi = "notr"
        else:
            deger_yargisi = "iyi" if (fark > 0) == artis_iyi else "kotu"

        degisimler.append({
            "metrik": metrik,
            "etiket": etiket,
            "birim": birim,
            "onceki": round(onceki_deger, 2),
            "son": round(son_deger, 2),
            "fark": round(fark, 2),
            "goreli_degisim_yuzde": None if goreli is None else round(goreli * 100, 2),
            "yon": yon,
            "deger_yargisi": deger_yargisi,
            "onemli": onemli,
            "nakit_etkisi": _nakit_etkisi(metrik, onceki_deger, son_deger, son_ciro, donem_gun_sayisi),
        })

    onemli_olanlar = [d for d in degisimler if d["onemli"]]
    return {
        "durum": "hazir",
        "onceki_donem": onceki_tablo.get("donem"),
        "son_donem": son_tablo.get("donem"),
        "donem_sayisi": len(tablolar),
        "degisimler": degisimler,
        "onemli_degisim_sayisi": len(onemli_olanlar),
        "kotulesen_sayisi": sum(1 for d in onemli_olanlar if d["deger_yargisi"] == "kotu"),
        "metodoloji": (
            f"Son dönem bir önceki dönemle karşılaştırılır. %{ONEMLI_DEGISIM_ESIGI * 100:.0f} "
            "altındaki değişimler gürültü sayılır. Gün bazlı metrikler dönem gün "
            "sayısını ister; verilmezse hesaplanmaz."
        ),
    }

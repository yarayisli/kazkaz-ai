"""İşlem satırlarından deterministik müşteri, ürün ve tahmin analizi."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any, Dict, List


def _puan(deger: float, dizi: List[float], ters: bool = False) -> int:
    if len(dizi) < 2:
        return 3
    sirali = sorted(dizi, reverse=ters)
    sira = sirali.index(deger)
    return max(1, min(5, 5 - int(sira / max(1, len(sirali) - 1) * 4)))


def _ay_ekle(yil: int, ay: int, artis: int) -> str:
    toplam = yil * 12 + ay - 1 + artis
    return f"{toplam // 12:04d}-{toplam % 12 + 1:02d}"


def _dogrusal_tahmin(aylik: List[Dict[str, Any]], ufuk: int = 3) -> Dict[str, Any]:
    gelirler = [float(s["gelir"]) for s in aylik]
    n = len(gelirler)
    if n < 3:
        return {"durum": "veri_bekliyor", "gereken": "En az 3 aylık gelir işlemi", "noktalar": []}

    def katsayi(dizi: List[float]) -> tuple[float, float]:
        adet = len(dizi)
        ort_x = (adet - 1) / 2
        ort_y = sum(dizi) / adet
        payda = sum((x - ort_x) ** 2 for x in range(adet))
        egim = sum((x - ort_x) * (y - ort_y) for x, y in enumerate(dizi)) / payda if payda else 0
        return egim, ort_y - egim * ort_x

    test_adedi = min(3, max(1, n // 4)) if n >= 5 else 1
    egitim = gelirler[:-test_adedi]
    gercek = gelirler[-test_adedi:]
    if len(egitim) >= 2:
        egim_test, sabit_test = katsayi(egitim)
        tahminler = [max(0, sabit_test + egim_test * (len(egitim) + i)) for i in range(test_adedi)]
        hatalar = [abs(g - t) / abs(g) for g, t in zip(gercek, tahminler) if g]
        mape = round(sum(hatalar) / len(hatalar) * 100, 1) if hatalar else None
    else:
        mape = None
    egim, sabit = katsayi(gelirler)
    yil, ay = map(int, aylik[-1]["donem"].split("-"))
    hata_payi = min(0.5, max(0.1, (mape or 25) / 100))
    noktalar = []
    for ileri in range(1, ufuk + 1):
        tahmin = max(0, sabit + egim * (n - 1 + ileri))
        noktalar.append({
            "donem": _ay_ekle(yil, ay, ileri), "tahmin": round(tahmin, 2),
            "alt": round(max(0, tahmin * (1 - hata_payi)), 2),
            "ust": round(tahmin * (1 + hata_payi), 2),
        })
    return {
        "durum": "hazir", "yontem": "Doğrusal eğilim + geçmiş dönem geri testi",
        "gecmis_hata_mape": mape, "veri_ayi": n,
        "guven": "orta" if n >= 12 and (mape or 100) <= 20 else "dusuk",
        "uyari": "Mevsimsellik ve enflasyon modeli içermez; karar değil planlama aralığıdır.",
        "noktalar": noktalar,
    }


def islem_analizleri(islemler: List[Dict[str, Any]]) -> Dict[str, Any]:
    aylik: Dict[str, Dict[str, float]] = defaultdict(lambda: {"gelir": 0, "gider": 0})
    musteriler: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"gelir": 0, "adet": 0, "son": ""})
    urunler: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"gelir": 0, "adet": 0, "musteriler": set()})

    for satir in islemler:
        donem = str(satir["tarih"])[:7]
        aylik[donem]["gelir"] += satir["gelir"]
        aylik[donem]["gider"] += satir["gider"]
        musteri = str(satir.get("musteri") or "").strip()
        if musteri and satir["gelir"] > 0:
            musteriler[musteri]["gelir"] += satir["gelir"]
            musteriler[musteri]["adet"] += 1
            musteriler[musteri]["son"] = max(musteriler[musteri]["son"], satir["tarih"])
        urun = str(satir.get("urun") or "").strip()
        if urun and satir["gelir"] > 0:
            urunler[urun]["gelir"] += satir["gelir"]
            urunler[urun]["adet"] += 1
            if musteri:
                urunler[urun]["musteriler"].add(musteri)

    aylik_liste = [
        {"donem": donem, **tutarlar, "net": tutarlar["gelir"] - tutarlar["gider"]}
        for donem, tutarlar in sorted(aylik.items())
    ]
    musteri_liste: List[Dict[str, Any]] = []
    toplam_gelir = sum(m["gelir"] for m in musteriler.values())
    if musteriler:
        analiz_tarihi = max(date.fromisoformat(m["son"]) for m in musteriler.values())
        recency = [(analiz_tarihi - date.fromisoformat(m["son"])).days for m in musteriler.values()]
        frequency = [m["adet"] for m in musteriler.values()]
        monetary = [m["gelir"] for m in musteriler.values()]
        for ad, metrik in musteriler.items():
            gun = (analiz_tarihi - date.fromisoformat(metrik["son"])).days
            r, f, m = _puan(gun, recency, ters=False), _puan(metrik["adet"], frequency, ters=True), _puan(metrik["gelir"], monetary, ters=True)
            skor = r + f + m
            segment = "Şampiyon" if r >= 4 and f >= 4 and m >= 4 else "Sadık" if f >= 4 and m >= 4 else "Risk altında" if r <= 2 and f >= 3 else "Kayıp" if r <= 2 and f <= 2 else "Gelişen"
            musteri_liste.append({
                "id": ad, "ad": ad, "gelir": round(metrik["gelir"], 2), "islem_sayisi": metrik["adet"],
                "son_islem": metrik["son"], "son_islemden_gun": gun, "rfm_skoru": skor, "segment": segment,
                "gelir_payi": round(metrik["gelir"] / toplam_gelir * 100, 2) if toplam_gelir else 0,
            })
        musteri_liste.sort(key=lambda s: s["gelir"], reverse=True)

    urun_liste = [{
        "urun": ad, "gelir": round(m["gelir"], 2), "islem_sayisi": m["adet"],
        "musteri_sayisi": len(m["musteriler"]),
        "gelir_payi": round(m["gelir"] / toplam_gelir * 100, 2) if toplam_gelir else 0,
    } for ad, m in urunler.items()]
    urun_liste.sort(key=lambda s: s["gelir"], reverse=True)
    return {
        "aylik_trend": aylik_liste,
        "musteriler": musteri_liste,
        "urunler": urun_liste,
        "tahmin": _dogrusal_tahmin(aylik_liste),
        "metodoloji": {
            "musteri_karliligi": "Ürün/müşteri bazlı doğrudan maliyet yoksa kârlılık üretilmez.",
            "rfm": "Son işlem, işlem sıklığı ve gelir tutarının 1-5 göreli puanları.",
        },
    }

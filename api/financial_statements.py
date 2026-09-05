"""Mizan kaynaklı finansal tablolar ve tablolar arası mutabakat motoru."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional

from api.donem_karsilastirma import donem_karsilastirmasi
from api.hesap_plani import kategori_bul, maliyet_hesabi_mi
from api.models import FinansalGorunum, MizanSatiri


TABLO_SURUMU = "2026.08-v1"
TOLERANS = 1.0

VARLIK = {"aktif", "varlik", "varlık", "nakit", "alacaklar", "stoklar", "diger_donen", "duran_varlik", "diger_varlik"}
KISA_VARLIK = {"nakit", "alacaklar", "stoklar", "diger_donen"}
DURAN_VARLIK = {"duran_varlik", "diger_varlik"}
YUKUMLULUK = {"pasif", "yukumluluk", "yükümlülük", "kisa_vadeli_borc", "ticari_borc", "uzun_vadeli_borc", "karsilik"}
OZKAYNAK = {"ozkaynak", "özkaynak", "sermaye", "gecmis_yil_kari", "diger_ozkaynak"}
DONEM_KARI = {"donem_kari", "donem_net_kari"}
GELIR = {"ciro", "diger_gelir"}
SATIS_MALIYETI = {"satis_maliyeti"}
FAALIYET_GIDERI = {"faaliyet_gideri"}
AMORTISMAN = {"amortisman"}
FAIZ = {"faiz_gideri"}
VERGI = {"vergi_gideri"}
TANINAN_ESLEMELER = (
    VARLIK | YUKUMLULUK | OZKAYNAK | DONEM_KARI | GELIR | SATIS_MALIYETI
    | FAALIYET_GIDERI | AMORTISMAN | FAIZ | VERGI
)


def _kategori(satir: MizanSatiri) -> Optional[str]:
    """Satırın kategorisi: kullanıcının etiketi öncelikli, yoksa hesap kodu.

    Tekdüzen Hesap Planı kodları standart olduğu için mizan hiçbir şey
    etiketlenmeden sınıflandırılabilir; `esleme` verildiğinde onu ezmez.
    """
    if satir.esleme and satir.esleme.strip():
        return satir.esleme.strip().lower()
    return kategori_bul(satir.hesap_kodu)


def _borc_bakiye(satir: MizanSatiri) -> float:
    return satir.borc - satir.alacak


def _alacak_bakiye(satir: MizanSatiri) -> float:
    return satir.alacak - satir.borc


def _topla(satirlar: Iterable[MizanSatiri], kategoriler: set[str], alacak: bool = False) -> float:
    bakiye = _alacak_bakiye if alacak else _borc_bakiye
    return sum(bakiye(satir) for satir in satirlar if _kategori(satir) in kategoriler)


def _donem_anahtari(donem: str) -> List[Any]:
    """2026-9 ve 2026-10 gibi dönemleri metinsel değil doğal sırada tutar."""
    return [int(parca) if parca.isdigit() else parca.lower() for parca in re.split(r"(\d+)", donem)]


def _gelir_tablosu(satirlar: List[MizanSatiri]) -> Dict[str, float]:
    ciro = _topla(satirlar, GELIR, alacak=True)
    satis_maliyeti = _topla(satirlar, SATIS_MALIYETI)
    brut_kar = ciro - satis_maliyeti
    faaliyet_giderleri = _topla(satirlar, FAALIYET_GIDERI)
    amortisman = _topla(satirlar, AMORTISMAN)
    faaliyet_kari = brut_kar - faaliyet_giderleri - amortisman
    faiz_gideri = _topla(satirlar, FAIZ)
    vergi_oncesi_kar = faaliyet_kari - faiz_gideri
    vergi_gideri = _topla(satirlar, VERGI)
    net_kar = vergi_oncesi_kar - vergi_gideri
    return {
        "ciro": round(ciro, 2),
        "satis_maliyeti": round(satis_maliyeti, 2),
        "brut_kar": round(brut_kar, 2),
        "faaliyet_giderleri": round(faaliyet_giderleri, 2),
        "amortisman": round(amortisman, 2),
        "faaliyet_kari": round(faaliyet_kari, 2),
        "faiz_gideri": round(faiz_gideri, 2),
        "vergi_oncesi_kar": round(vergi_oncesi_kar, 2),
        "vergi_gideri": round(vergi_gideri, 2),
        "net_kar": round(net_kar, 2),
    }


def _bilanco(satirlar: List[MizanSatiri], net_kar: float) -> Dict[str, Any]:
    nakit = _topla(satirlar, {"nakit"})
    alacaklar = _topla(satirlar, {"alacaklar"})
    stoklar = _topla(satirlar, {"stoklar"})
    diger_donen = _topla(satirlar, {"diger_donen"})
    diger_kisa_varlik = _topla(satirlar, {"aktif", "varlik", "varlık"})
    donen_varliklar = nakit + alacaklar + stoklar + diger_donen + diger_kisa_varlik
    duran_varliklar = _topla(satirlar, DURAN_VARLIK)
    toplam_varliklar = donen_varliklar + duran_varliklar

    kisa_vadeli_borc = _topla(satirlar, {"kisa_vadeli_borc"}, alacak=True)
    ticari_borc = _topla(satirlar, {"ticari_borc"}, alacak=True)
    karsilik = _topla(satirlar, {"karsilik"}, alacak=True)
    diger_yukumluluk = _topla(satirlar, {"pasif", "yukumluluk", "yükümlülük"}, alacak=True)
    uzun_vadeli_borc = _topla(satirlar, {"uzun_vadeli_borc"}, alacak=True)
    toplam_yukumlulukler = kisa_vadeli_borc + ticari_borc + karsilik + diger_yukumluluk + uzun_vadeli_borc

    kayitli_ozkaynak = _topla(satirlar, OZKAYNAK, alacak=True)
    kayitli_donem_kari = _topla(satirlar, DONEM_KARI, alacak=True)
    eklenecek_donem_kari = 0.0 if abs(kayitli_donem_kari) > TOLERANS else net_kar
    donem_kari_farki = kayitli_donem_kari - net_kar if abs(kayitli_donem_kari) > TOLERANS else 0.0
    toplam_ozkaynak = kayitli_ozkaynak + kayitli_donem_kari + eklenecek_donem_kari
    fark = toplam_varliklar - toplam_yukumlulukler - toplam_ozkaynak
    return {
        "nakit": round(nakit, 2),
        "alacaklar": round(alacaklar, 2),
        "stoklar": round(stoklar, 2),
        "diger_donen_varliklar": round(diger_donen + diger_kisa_varlik, 2),
        "donen_varliklar": round(donen_varliklar, 2),
        "duran_varliklar": round(duran_varliklar, 2),
        "toplam_varliklar": round(toplam_varliklar, 2),
        "kisa_vadeli_borc": round(kisa_vadeli_borc, 2),
        "ticari_borc": round(ticari_borc, 2),
        "karsiliklar": round(karsilik, 2),
        "diger_yukumlulukler": round(diger_yukumluluk, 2),
        "uzun_vadeli_borc": round(uzun_vadeli_borc, 2),
        "toplam_yukumlulukler": round(toplam_yukumlulukler, 2),
        "kayitli_ozkaynak": round(kayitli_ozkaynak, 2),
        "kayitli_donem_kari": round(kayitli_donem_kari, 2),
        "donem_net_kari": round(net_kar, 2),
        "donem_kari_farki": round(donem_kari_farki, 2),
        "donem_kari_tutarli": abs(donem_kari_farki) <= TOLERANS,
        "donem_kari_ozkaynaga_eklendi": abs(eklenecek_donem_kari) > TOLERANS,
        "toplam_ozkaynak": round(toplam_ozkaynak, 2),
        "bilanco_farki": round(fark, 2),
        "denk": abs(fark) <= TOLERANS,
    }


def _nakit_koprusu(veri: FinansalGorunum) -> Dict[str, Any]:
    girdiler = {
        "donem_basi_nakit": veri.donem_basi_nakit,
        "operasyonel_nakit_akisi": veri.operasyonel_nakit_akisi,
        "yatirim_nakit_akisi": veri.yatirim_nakit_akisi,
        "finansman_nakit_akisi": veri.finansman_nakit_akisi,
        "donem_sonu_nakit": veri.nakit,
    }
    eksikler = [alan for alan, deger in girdiler.items() if deger is None]
    if eksikler:
        return {
            "durum": "eksik_veri",
            "girdiler": girdiler,
            "eksik_alanlar": eksikler,
            "formul": "Dönem başı nakit + CFO + CFI + CFF = Dönem sonu nakit",
        }
    beklenen = (
        float(veri.donem_basi_nakit)
        + float(veri.operasyonel_nakit_akisi)
        + float(veri.yatirim_nakit_akisi)
        + float(veri.finansman_nakit_akisi)
    )
    fark = beklenen - veri.nakit
    return {
        "durum": "mutabik" if abs(fark) <= TOLERANS else "inceleme_gerekli",
        "girdiler": girdiler,
        "beklenen_donem_sonu_nakit": round(beklenen, 2),
        "gerceklesen_donem_sonu_nakit": round(veri.nakit, 2),
        "fark": round(fark, 2),
        "formul": "Dönem başı nakit + CFO + CFI + CFF = Dönem sonu nakit",
    }


def _gorunum_mutabakati(veri: FinansalGorunum, gelir: Dict[str, float], bilanco: Dict[str, Any]) -> Dict[str, Any]:
    karsilastirmalar = {
        "ciro": (gelir["ciro"], veri.ciro),
        "satis_maliyeti": (gelir["satis_maliyeti"], veri.satis_maliyeti),
        "faaliyet_giderleri": (gelir["faaliyet_giderleri"], veri.faaliyet_giderleri),
        "net_kar": (gelir["net_kar"], veri.net_kar),
        "nakit": (bilanco["nakit"], veri.nakit),
        "alacaklar": (bilanco["alacaklar"], veri.alacaklar),
        "stoklar": (bilanco["stoklar"], veri.stoklar),
        "ticari_borc": (bilanco["ticari_borc"], veri.borclar),
        "kisa_vadeli_borc": (bilanco["kisa_vadeli_borc"], veri.kisa_vadeli_borc),
        "uzun_vadeli_borc": (bilanco["uzun_vadeli_borc"], veri.uzun_vadeli_borc),
        "ozkaynak": (bilanco["toplam_ozkaynak"], veri.ozkaynak),
    }
    if veri.toplam_varliklar is not None:
        karsilastirmalar["toplam_varliklar"] = (bilanco["toplam_varliklar"], veri.toplam_varliklar)
    satirlar = [
        {
            "alan": alan,
            "mizan": round(mizan, 2),
            "finansal_gorunum": round(gorunum, 2),
            "fark": round(mizan - gorunum, 2),
            "mutabik": abs(mizan - gorunum) <= TOLERANS,
        }
        for alan, (mizan, gorunum) in karsilastirmalar.items()
    ]
    return {
        "durum": "mutabik" if all(s["mutabik"] for s in satirlar) else "inceleme_gerekli",
        "satirlar": satirlar,
        "uyusmayan_alanlar": [s["alan"] for s in satirlar if not s["mutabik"]],
    }


def finansal_tablo_paketi(mizan: List[MizanSatiri], veri: FinansalGorunum) -> Dict[str, Any]:
    if not mizan:
        return {
            "durum": "veri_bekliyor",
            "gerekenler": ["dönem", "hesap kodu", "borç", "alacak", "hesap eşlemesi"],
            "tablo_surumu": TABLO_SURUMU,
        }
    donem_satirlari: Dict[str, List[MizanSatiri]] = defaultdict(list)
    for satir in mizan:
        donem_satirlari[satir.donem].append(satir)
    tablolar = []
    for donem, satirlar in sorted(donem_satirlari.items(), key=lambda oge: _donem_anahtari(oge[0])):
        gelir = _gelir_tablosu(satirlar)
        bilanco = _bilanco(satirlar, gelir["net_kar"])
        mizan_farki = sum(s.borc for s in satirlar) - sum(s.alacak for s in satirlar)
        tablolar.append({
            "donem": donem,
            "gelir_tablosu": gelir,
            "bilanco": bilanco,
            "mizan_farki": round(mizan_farki, 2),
            "mizan_denk": abs(mizan_farki) <= TOLERANS,
        })
    son = tablolar[-1]
    onceki = tablolar[-2] if len(tablolar) >= 2 else None
    degisim = None
    if onceki:
        degisim = {
            alan: round(son["bilanco"][alan] - onceki["bilanco"][alan], 2)
            for alan in ("nakit", "alacaklar", "stoklar", "ticari_borc", "toplam_varliklar", "toplam_yukumlulukler", "toplam_ozkaynak")
        }
    mutabakat = _gorunum_mutabakati(veri, son["gelir_tablosu"], son["bilanco"])
    nakit = _nakit_koprusu(veri)
    # 7'li maliyet hesapları 6'lı gruba yansıtıldığı için toplanmaz; bunlar
    # "tanınmayan hesap" değildir, ayrı raporlanır ki kullanıcı endişelenmesin.
    yansitma = [s.hesap_kodu for s in mizan if maliyet_hesabi_mi(s.hesap_kodu)]
    eslesmeyen = [
        s.hesap_kodu for s in mizan
        if not maliyet_hesabi_mi(s.hesap_kodu) and _kategori(s) not in TANINAN_ESLEMELER
    ]
    sorun_var = (
        any(
            not t["mizan_denk"]
            or not t["bilanco"]["denk"]
            or not t["bilanco"]["donem_kari_tutarli"]
            for t in tablolar
        )
        or mutabakat["durum"] != "mutabik"
        or nakit["durum"] == "inceleme_gerekli"
        or bool(eslesmeyen)
    )
    return {
        "durum": "inceleme_gerekli" if sorun_var else "tamamlandi",
        "guven": "yuksek" if not sorun_var and nakit["durum"] != "eksik_veri" else "orta",
        "tablo_surumu": TABLO_SURUMU,
        "donemler": [t["donem"] for t in tablolar],
        "tablolar": tablolar,
        "son_donem": son,
        "donem_degisimleri": degisim,
        # Şirketi sektör ortalamasıyla değil kendi geçmişiyle karşılaştırır.
        "kendi_trendi": donem_karsilastirmasi(tablolar, veri.donem_gun_sayisi),
        "finansal_gorunum_mutabakati": mutabakat,
        "nakit_koprusu": nakit,
        "eslesmeyen_hesaplar": eslesmeyen[:100],
        "yansitma_hesaplari": yansitma[:100],
        "metodoloji": {
            "gelir_tablosu": "Kapanmamış gelir/gider hesaplarından hesaplanır.",
            "bilanco": "Ayrı dönem kârı hesabı yoksa hesaplanan net kâr özkaynağa eklenir.",
            "nakit": "CFO, CFI ve CFF açıkça girilmeden nakit köprüsü varsayım yapmaz.",
            "hesap_eslemesi": (
                "Hesap kodları Tekdüzen Hesap Planı'na göre otomatik eşlenir; "
                "mizandaki Eşleme sütunu doldurulmuşsa o önceliklidir."
            ),
            "maliyet_hesaplari": (
                "7'li maliyet hesapları 6'lı gruba yansıtıldığı için ayrıca "
                "toplanmaz; çift sayımı önler."
            ),
        },
    }

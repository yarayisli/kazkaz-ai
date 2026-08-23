"""Kanıta dayalı gelişmiş finans ajanları.

Bu modül yalnızca deterministik hesaplama yapar. Eksik veri halinde tahmin
uydurmak yerine gereken alanları açıkça döndürür.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import timedelta
from statistics import mean, pstdev
from typing import Any, Dict, Iterable, List, Optional

from api.financial_statements import finansal_tablo_paketi
from api.models import GelismisAjanIstegi


def _bekliyor(ajan: str, gerekenler: Iterable[str]) -> Dict[str, Any]:
    return {
        "ajan": ajan,
        "durum": "veri_bekliyor",
        "guven": "hesaplanamadi",
        "gerekenler": list(gerekenler),
        "bulgular": [],
    }


def mizan_ajani(istek: GelismisAjanIstegi) -> Dict[str, Any]:
    if not istek.mizan:
        return _bekliyor("mizan_esleme_ajani", ["hesap kodu", "borç", "alacak", "dönem", "hesap eşlemesi"])

    toplam_borc = sum(s.borc for s in istek.mizan)
    toplam_alacak = sum(s.alacak for s in istek.mizan)
    fark = toplam_borc - toplam_alacak
    eslesmeyen = [s.hesap_kodu for s in istek.mizan if not s.esleme]
    kapsam = (len(istek.mizan) - len(eslesmeyen)) / len(istek.mizan) * 100

    kategori_bakiye: Dict[str, float] = defaultdict(float)
    for satir in istek.mizan:
        if satir.esleme:
            kategori = satir.esleme.strip().lower()
            if kategori in {"aktif", "varlik", "varlık"}:
                kategori_bakiye["aktif"] += satir.borc - satir.alacak
            elif kategori in {"pasif", "yukumluluk", "yükümlülük"}:
                kategori_bakiye["pasif"] += satir.alacak - satir.borc
            elif kategori in {"ozkaynak", "özkaynak"}:
                kategori_bakiye["ozkaynak"] += satir.alacak - satir.borc

    denklem_hazir = all(k in kategori_bakiye for k in ("aktif", "pasif", "ozkaynak"))
    denklem_farki = (
        kategori_bakiye["aktif"] - kategori_bakiye["pasif"] - kategori_bakiye["ozkaynak"]
        if denklem_hazir
        else None
    )
    donemler = sorted({s.donem for s in istek.mizan})
    return {
        "ajan": "mizan_esleme_ajani",
        "durum": "tamamlandi" if abs(fark) <= 0.01 and kapsam == 100 else "inceleme_gerekli",
        "guven": "yuksek" if abs(fark) <= 0.01 and kapsam == 100 else "sinirli",
        "toplam_borc": round(toplam_borc, 2),
        "toplam_alacak": round(toplam_alacak, 2),
        "mizan_farki": round(fark, 2),
        "esleme_kapsami": round(kapsam, 2),
        "eslesmeyen_hesaplar": eslesmeyen[:100],
        "bilanco_denklemi": {
            "hesaplanabilir": denklem_hazir,
            "aktif": round(kategori_bakiye.get("aktif", 0), 2),
            "pasif": round(kategori_bakiye.get("pasif", 0), 2),
            "ozkaynak": round(kategori_bakiye.get("ozkaynak", 0), 2),
            "fark": round(denklem_farki, 2) if denklem_farki is not None else None,
        },
        "donem_karsilastirmasi": {
            "hazir": len(donemler) >= 2,
            "donemler": donemler,
        },
        "bulgular": [
            f"Borç ve alacak toplamı farkı ₺{fark:,.2f}.",
            f"Hesap eşleme kapsamı %{kapsam:.1f}.",
        ],
    }


def finansal_tablo_mutabakat_ajani(istek: GelismisAjanIstegi) -> Dict[str, Any]:
    """Mizandan ortak finansal tabloları üretir ve özet verilerle uzlaştırır."""
    paket = finansal_tablo_paketi(istek.mizan, istek.finansal_veri)
    if paket["durum"] == "veri_bekliyor":
        return {
            "ajan": "finansal_tablo_mutabakat_ajani",
            "guven": "hesaplanamadi",
            "bulgular": [],
            **paket,
        }

    son = paket["son_donem"]
    uyusmayan = paket["finansal_gorunum_mutabakati"]["uyusmayan_alanlar"]
    nakit_durumu = paket["nakit_koprusu"]["durum"]
    return {
        "ajan": "finansal_tablo_mutabakat_ajani",
        **paket,
        "gerekenler": paket["nakit_koprusu"].get("eksik_alanlar", []),
        "bulgular": [
            f"{len(paket['donemler'])} dönem için gelir tablosu ve bilanço üretildi.",
            f"Son dönem bilanço farkı ₺{son['bilanco']['bilanco_farki']:,.2f}.",
            "Finansal görünümle tüm alanlar mutabık."
            if not uyusmayan else f"Mutabakat bekleyen alanlar: {', '.join(uyusmayan)}.",
            f"Nakit köprüsü durumu: {nakit_durumu}.",
        ],
    }


def nakit_13_hafta_ajani(istek: GelismisAjanIstegi) -> Dict[str, Any]:
    if not istek.haftalik_nakit:
        return _bekliyor(
            "nakit_13_hafta_ajani",
            ["başlangıç nakdi", "13 haftalık tahsilat", "ödemeler", "minimum nakit eşiği"],
        )

    tum_satirlar = sorted(istek.haftalik_nakit, key=lambda s: s.hafta)
    tekrar_haftalar = sorted({s.hafta.isoformat() for s in tum_satirlar if sum(1 for x in tum_satirlar if x.hafta == s.hafta) > 1})
    benzersiz_satirlar = []
    gorulen = set()
    for satir in tum_satirlar:
        if satir.hafta not in gorulen:
            benzersiz_satirlar.append(satir)
            gorulen.add(satir.hafta)
    bosluklar = [
        {
            "onceki": onceki.hafta.isoformat(),
            "sonraki": sonraki.hafta.isoformat(),
            "gun_farki": (sonraki.hafta - onceki.hafta).days,
        }
        for onceki, sonraki in zip(benzersiz_satirlar, benzersiz_satirlar[1:])
        if (sonraki.hafta - onceki.hafta).days != 7
    ]

    ileri_indeksler = [i for i, satir in enumerate(benzersiz_satirlar) if satir.hafta >= istek.rapor_tarihi]
    baslangic_indeksi = ileri_indeksler[0] if ileri_indeksler else max(0, len(benzersiz_satirlar) - 13)
    satirlar = benzersiz_satirlar[baslangic_indeksi: baslangic_indeksi + 13]

    def net_hareket(satir) -> tuple[float, float, float]:
        giris = satir.tahsilat + satir.nakit_satis + satir.diger_giris
        cikis = satir.tedarikci + satir.personel + satir.vergi + satir.borc_servisi + satir.diger_cikis
        return giris, cikis, giris - cikis

    bakiye = istek.baslangic_nakdi
    for onceki in benzersiz_satirlar[:baslangic_indeksi]:
        bakiye += net_hareket(onceki)[2]
    pencere_baslangic_nakdi = bakiye
    esik = istek.minimum_nakit_esigi
    projeksiyon = []
    ilk_acik = None
    for satir in satirlar:
        giris, cikis, net = net_hareket(satir)
        bakiye += net
        esik_alti = esik is not None and bakiye < esik
        if esik_alti and ilk_acik is None:
            ilk_acik = satir.hafta.isoformat()
        projeksiyon.append(
            {
                "hafta": satir.hafta.isoformat(),
                "giris": round(giris, 2),
                "cikis": round(cikis, 2),
                "net": round(net, 2),
                "donem_sonu_nakit": round(bakiye, 2),
                "esik_alti": esik_alti,
            }
        )

    gerekenler = []
    if len(satirlar) < 13:
        gerekenler.append(f"{13 - len(satirlar)} haftalık ek veri")
    if esik is None:
        gerekenler.append("minimum nakit eşiği")
    if tekrar_haftalar:
        gerekenler.append("tekrar eden hafta kayıtlarının düzeltilmesi")
    if bosluklar:
        gerekenler.append("haftalık tarih boşluklarının tamamlanması")

    kayan_pencereler = []
    yuruyen_bakiye = istek.baslangic_nakdi
    pencere_baslangic_bakiyeleri = []
    for satir in benzersiz_satirlar:
        pencere_baslangic_bakiyeleri.append(yuruyen_bakiye)
        yuruyen_bakiye += net_hareket(satir)[2]
    for indeks in range(max(0, len(benzersiz_satirlar) - 12)):
        pencere = benzersiz_satirlar[indeks: indeks + 13]
        pencere_bakiye = pencere_baslangic_bakiyeleri[indeks]
        pencere_ilk_acik = None
        for satir in pencere:
            pencere_bakiye += net_hareket(satir)[2]
            if esik is not None and pencere_bakiye < esik and pencere_ilk_acik is None:
                pencere_ilk_acik = satir.hafta.isoformat()
        kayan_pencereler.append({
            "baslangic": pencere[0].hafta.isoformat(),
            "bitis": pencere[-1].hafta.isoformat(),
            "baslangic_nakdi": round(pencere_baslangic_bakiyeleri[indeks], 2),
            "donem_sonu_nakit": round(pencere_bakiye, 2),
            "ilk_esik_alti_tarih": pencere_ilk_acik,
        })

    durum = "tamamlandi"
    if tekrar_haftalar:
        durum = "inceleme_gerekli"
    elif gerekenler:
        durum = "sinirli"
    return {
        "ajan": "nakit_13_hafta_ajani",
        "durum": durum,
        "guven": "yuksek" if not gerekenler else "sinirli",
        "toplam_veri_haftasi": len(benzersiz_satirlar),
        "hafta_sayisi": len(satirlar),
        "tahmin_baslangici": satirlar[0].hafta.isoformat() if satirlar else None,
        "baslangic_nakdi": round(pencere_baslangic_nakdi, 2),
        "donem_sonu_nakit": round(bakiye, 2),
        "minimum_nakit_esigi": esik,
        "ilk_esik_alti_tarih": ilk_acik,
        "projeksiyon": projeksiyon,
        "kayan_13_hafta_pencereleri": kayan_pencereler,
        "tekrar_haftalar": tekrar_haftalar,
        "hafta_bosluklari": bosluklar,
        "gerekenler": gerekenler,
        "bulgular": [
            f"{len(satirlar)} haftalık projeksiyon sonunda nakit ₺{bakiye:,.0f}.",
            f"İlk eşik altı tarih: {ilk_acik or 'oluşmadı / eşik girilmedi'}.",
        ],
    }


def veri_ufku_ozeti(istek: GelismisAjanIstegi) -> Dict[str, Any]:
    """Her finans alanında sağlanan zaman kapsamını görünür kılar."""
    mizan_donemleri = sorted({s.donem for s in istek.mizan})
    nakit_haftalari = sorted({s.hafta for s in istek.haftalik_nakit})
    fatura_tarihleri = sorted({s.fatura_tarihi for s in istek.alacak_faturalari})
    borc_tarihleri = sorted({s.odeme_tarihi for s in istek.borc_servisi})
    butce_aylari = sorted({s.ay for s in istek.butce})

    def aralik(tarihler) -> Dict[str, Any]:
        return {
            "kayit_sayisi": len(tarihler),
            "ilk": tarihler[0].isoformat() if tarihler else None,
            "son": tarihler[-1].isoformat() if tarihler else None,
        }

    return {
        "mizan": {
            "donem_sayisi": len(mizan_donemleri),
            "donemler": mizan_donemleri,
            "karsilastirma_hazir": len(mizan_donemleri) >= 2,
        },
        "nakit": {**aralik(nakit_haftalari), "tam_13_hafta_penceresi": len(nakit_haftalari) >= 13},
        "alacak": aralik(fatura_tarihleri),
        "borc_servisi": aralik(borc_tarihleri),
        "butce": {**aralik(butce_aylari), "temel_tahmin_hazir": len(butce_aylari) >= 3},
    }


def alacak_ajani(istek: GelismisAjanIstegi) -> Dict[str, Any]:
    if not istek.alacak_faturalari:
        return _bekliyor(
            "alacak_yaslandirma_ajani",
            ["fatura kimliği", "müşteri", "vade tarihi", "fatura tutarı", "ödenen tutar"],
        )

    buckets = {"vadesi_gelmemis": 0.0, "0_30": 0.0, "31_60": 0.0, "61_90": 0.0, "90_plus": 0.0}
    musteri_toplam: Dict[str, float] = defaultdict(float)
    hatali = []
    acik_toplam = 0.0
    for fatura in istek.alacak_faturalari:
        acik = fatura.tutar - fatura.odenen
        if acik < 0:
            hatali.append(fatura.fatura_id)
            continue
        if acik == 0:
            continue
        gecikme = (istek.rapor_tarihi - fatura.vade_tarihi).days
        if gecikme < 0:
            bucket = "vadesi_gelmemis"
        elif gecikme <= 30:
            bucket = "0_30"
        elif gecikme <= 60:
            bucket = "31_60"
        elif gecikme <= 90:
            bucket = "61_90"
        else:
            bucket = "90_plus"
        buckets[bucket] += acik
        musteri_toplam[fatura.musteri_adi] += acik
        acik_toplam += acik

    yogunlasma = sorted(
        (
            {"musteri": musteri, "acik_alacak": round(tutar, 2), "pay": round(tutar / acik_toplam * 100, 2)}
            for musteri, tutar in musteri_toplam.items()
        ),
        key=lambda s: s["acik_alacak"],
        reverse=True,
    ) if acik_toplam else []
    return {
        "ajan": "alacak_yaslandirma_ajani",
        "durum": "inceleme_gerekli" if hatali else "tamamlandi",
        "guven": "yuksek" if not hatali else "sinirli",
        "acik_alacak": round(acik_toplam, 2),
        "yaslandirma": {k: round(v, 2) for k, v in buckets.items()},
        "musteri_yogunlasmasi": yogunlasma[:20],
        "hatali_faturalar": hatali,
        "tahsilat_risk_skoru": None,
        "gerekenler": ["tahsilat risk skoru için geçmiş ödeme hareketleri"],
        "bulgular": [
            f"Toplam açık alacak ₺{acik_toplam:,.0f}.",
            f"90+ gün gecikmiş alacak ₺{buckets['90_plus']:,.0f}.",
        ],
    }


def borc_servis_ajani(istek: GelismisAjanIstegi) -> Dict[str, Any]:
    if not istek.borc_servisi:
        return _bekliyor(
            "borc_servis_ajani",
            ["borç kimliği", "ödeme tarihi", "anapara", "faiz", "para birimi", "operasyonel nakit akışı"],
        )

    para_birimleri = sorted({s.para_birimi.upper() for s in istek.borc_servisi})
    aylik: Dict[str, Dict[str, float]] = defaultdict(lambda: {"anapara": 0.0, "faiz": 0.0})
    for satir in istek.borc_servisi:
        anahtar = f"{satir.odeme_tarihi:%Y-%m}:{satir.para_birimi.upper()}"
        aylik[anahtar]["anapara"] += satir.anapara
        aylik[anahtar]["faiz"] += satir.faiz

    tek_para = len(para_birimleri) == 1
    toplam_servis = sum(s.anapara + s.faiz for s in istek.borc_servisi) if tek_para else None
    dscr = (
        istek.operasyonel_nakit_akisi / toplam_servis
        if toplam_servis not in (None, 0) and istek.operasyonel_nakit_akisi is not None
        else None
    )
    doksan_gun = istek.rapor_tarihi + timedelta(days=90)
    yakin_vade = sum(
        s.anapara + s.faiz
        for s in istek.borc_servisi
        if istek.rapor_tarihi <= s.odeme_tarihi <= doksan_gun
    ) if tek_para else None
    gerekenler = []
    if not tek_para:
        gerekenler.append("çoklu para birimi için kur tarihi ve döviz kurları")
    if istek.operasyonel_nakit_akisi is None:
        gerekenler.append("DSCR için operasyonel nakit akışı")
    return {
        "ajan": "borc_servis_ajani",
        "durum": "tamamlandi" if not gerekenler else "sinirli",
        "guven": "yuksek" if not gerekenler else "sinirli",
        "para_birimleri": para_birimleri,
        "toplam_borc_servisi": round(toplam_servis, 2) if toplam_servis is not None else None,
        "dscr": round(dscr, 2) if dscr is not None else None,
        "doksan_gunluk_odeme": round(yakin_vade, 2) if yakin_vade is not None else None,
        "aylik_takvim": [
            {"donem": donem, "anapara": round(v["anapara"], 2), "faiz": round(v["faiz"], 2), "toplam": round(v["anapara"] + v["faiz"], 2)}
            for donem, v in sorted(aylik.items())
        ],
        "gerekenler": gerekenler,
        "bulgular": [
            f"Borç servis para birimleri: {', '.join(para_birimleri)}.",
            f"DSCR: {dscr:.2f}" if dscr is not None else "DSCR için gerekli veri tamamlanmadı.",
        ],
    }


def butce_tahmin_ajani(istek: GelismisAjanIstegi) -> Dict[str, Any]:
    if not istek.butce:
        return _bekliyor(
            "butce_tahmin_ajani",
            ["aylık bütçe", "gerçekleşen", "departman", "proje", "geçmiş tahmin"],
        )

    toplam_butce = sum(s.butce for s in istek.butce)
    toplam_gerceklesen = sum(s.gerceklesen for s in istek.butce)
    aylar = sorted({s.ay.strftime("%Y-%m") for s in istek.butce})
    gercek_ay = len(aylar)
    yil_sonu_tahmin = toplam_gerceklesen / gercek_ay * 12 if gercek_ay else None
    hata_oranlari = [
        abs(s.onceki_tahmin - s.gerceklesen) / s.gerceklesen * 100
        for s in istek.butce
        if s.onceki_tahmin is not None and s.gerceklesen > 0
    ]
    boyutlar: Dict[str, Dict[str, float]] = defaultdict(lambda: {"butce": 0.0, "gerceklesen": 0.0})
    for satir in istek.butce:
        anahtar = f"{satir.departman} / {satir.proje} / {satir.kategori}"
        boyutlar[anahtar]["butce"] += satir.butce
        boyutlar[anahtar]["gerceklesen"] += satir.gerceklesen
    return {
        "ajan": "butce_tahmin_ajani",
        "durum": "tamamlandi" if gercek_ay >= 3 else "sinirli",
        "guven": "orta" if gercek_ay >= 3 else "dusuk",
        "gerceklesen_ay": gercek_ay,
        "toplam_butce": round(toplam_butce, 2),
        "toplam_gerceklesen": round(toplam_gerceklesen, 2),
        "sapma": round(toplam_gerceklesen - toplam_butce, 2),
        "yil_sonu_gerceklesme_tahmini": round(yil_sonu_tahmin, 2) if yil_sonu_tahmin is not None else None,
        "gecmis_tahmin_hatasi_mape": round(mean(hata_oranlari), 2) if hata_oranlari else None,
        "boyutlar": [
            {"boyut": boyut, "butce": round(v["butce"], 2), "gerceklesen": round(v["gerceklesen"], 2), "sapma": round(v["gerceklesen"] - v["butce"], 2)}
            for boyut, v in sorted(boyutlar.items())
        ],
        "gerekenler": [] if hata_oranlari else ["tahmin hatası için geçmiş tahmin değerleri"],
        "bulgular": [
            f"Bütçe sapması ₺{toplam_gerceklesen - toplam_butce:,.0f}.",
            f"Yıl sonu basit gerçekleşme tahmini ₺{yil_sonu_tahmin:,.0f}." if yil_sonu_tahmin is not None else "Yıl sonu tahmini hesaplanamadı.",
        ],
    }


def anomali_ve_denetim_ajani(istek: GelismisAjanIstegi, sonuclar: List[Dict[str, Any]]) -> Dict[str, Any]:
    anomaliler = []
    fatura_idleri = [f.fatura_id for f in istek.alacak_faturalari]
    tekrarlar = sorted({fid for fid in fatura_idleri if fatura_idleri.count(fid) > 1})
    if tekrarlar:
        anomaliler.append({"tip": "tekrar_fatura", "deger": tekrarlar[:100]})

    gerceklesenler = [s.gerceklesen for s in istek.butce]
    if len(gerceklesenler) >= 6:
        ortalama = mean(gerceklesenler)
        sapma = pstdev(gerceklesenler)
        if sapma > 0:
            for satir in istek.butce:
                z = abs(satir.gerceklesen - ortalama) / sapma
                if z >= 3:
                    anomaliler.append({"tip": "butce_aykiri_deger", "kategori": satir.kategori, "z_skoru": round(z, 2)})

    payload = istek.model_dump(mode="json")
    parmak_izi = hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    eksik_ajan = [s["ajan"] for s in sonuclar if s["durum"] == "veri_bekliyor"]
    return {
        "ajan": "anomali_ve_denetim_ajani",
        "durum": "inceleme_gerekli" if anomaliler else "tamamlandi",
        "guven": "yuksek",
        "anomaliler": anomaliler,
        "veri_bekleyen_ajanlar": eksik_ajan,
        "denetim_izi": {
            "girdi_sha256": parmak_izi,
            "rapor_tarihi": istek.rapor_tarihi.isoformat(),
            "ajan_sayisi": len(sonuclar) + 1,
        },
        "bulgular": [
            f"{len(anomaliler)} veri anomalisi bulundu.",
            f"{len(eksik_ajan)} ajan ek veri bekliyor.",
        ],
    }


def bas_denetci(istek: GelismisAjanIstegi, sonuclar: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Ajan çıktılarını bağımsız kalite kapılarından geçirir.

    Bu katman yeni finansal değer hesaplamaz. Ajanların aynı veri seti üzerinde
    ürettiği sonuçların birbirini destekleyip desteklemediğini kontrol eder ve
    kritik çelişkide AI/karar akışını durduracak bir sonuç üretir.
    """
    ajanlar = {sonuc["ajan"]: sonuc for sonuc in sonuclar}
    kritikler: List[Dict[str, Any]] = []
    uyarilar: List[Dict[str, Any]] = []
    kontroller: List[Dict[str, Any]] = []

    def kaydet(kontrol_id: str, durum: str, mesaj: str, kaynaklar: List[str]) -> None:
        kayit = {
            "kontrol_id": kontrol_id,
            "durum": durum,
            "mesaj": mesaj,
            "kaynak_ajanlar": kaynaklar,
        }
        kontroller.append(kayit)
        if durum == "kritik":
            kritikler.append(kayit)
        elif durum == "uyari":
            uyarilar.append(kayit)

    mizan = ajanlar.get("mizan_esleme_ajani", {})
    if mizan.get("durum") == "veri_bekliyor":
        kaydet("mizan_hazirligi", "uyari", "Mizan denetimi için veri bekleniyor.", ["mizan_esleme_ajani"])
    else:
        mizan_farki = abs(float(mizan.get("mizan_farki", 0)))
        kaydet(
            "mizan_borc_alacak_denkiligi",
            "gecti" if mizan_farki <= 0.01 else "kritik",
            f"Mizan borç/alacak farkı ₺{mizan_farki:,.2f}.",
            ["mizan_esleme_ajani"],
        )
        denklem = mizan.get("bilanco_denklemi", {})
        if denklem.get("hesaplanabilir"):
            fark = abs(float(denklem.get("fark") or 0))
            kaydet(
                "aktif_pasif_ozkaynak_denkiligi",
                "gecti" if fark <= 0.01 else "kritik",
                f"Aktif - pasif - özkaynak farkı ₺{fark:,.2f}.",
                ["mizan_esleme_ajani"],
            )
        else:
            kaydet(
                "aktif_pasif_ozkaynak_denkiligi",
                "uyari",
                "Bilanço denklemi için aktif, pasif ve özkaynak eşlemeleri tamamlanmadı.",
                ["mizan_esleme_ajani"],
            )

    tablo = ajanlar.get("finansal_tablo_mutabakat_ajani", {})
    if tablo.get("durum") == "veri_bekliyor":
        kaydet("tablo_mutabakati", "uyari", "Finansal tablo mutabakatı için veri bekleniyor.", ["finansal_tablo_mutabakat_ajani"])
    else:
        son_donem = tablo.get("son_donem", {})
        bilanco = son_donem.get("bilanco", {})
        if bilanco:
            kaydet(
                "uretilen_bilanco_denkiligi",
                "gecti" if bilanco.get("denk") else "kritik",
                f"Üretilen bilanço farkı ₺{abs(float(bilanco.get('bilanco_farki') or 0)):,.2f}.",
                ["finansal_tablo_mutabakat_ajani"],
            )
        uyusmayan = tablo.get("finansal_gorunum_mutabakati", {}).get("uyusmayan_alanlar", [])
        kaydet(
            "mizan_finansal_gorunum_mutabakati",
            "gecti" if not uyusmayan else "kritik",
            "Mizan ile finansal görünüm mutabık."
            if not uyusmayan
            else f"Mutabakat bekleyen alanlar: {', '.join(uyusmayan)}.",
            ["mizan_esleme_ajani", "finansal_tablo_mutabakat_ajani"],
        )
        nakit_koprusu = tablo.get("nakit_koprusu", {})
        if nakit_koprusu.get("durum") == "inceleme_gerekli":
            kaydet(
                "nakit_koprusu_mutabakati",
                "kritik",
                f"Nakit köprüsü farkı ₺{abs(float(nakit_koprusu.get('fark') or 0)):,.2f}.",
                ["finansal_tablo_mutabakat_ajani", "nakit_13_hafta_ajani"],
            )
        elif nakit_koprusu.get("durum") == "eksik_veri":
            kaydet(
                "nakit_koprusu_mutabakati",
                "uyari",
                "Nakit köprüsü için CFO, CFI ve CFF girdileri tamamlanmadı.",
                ["finansal_tablo_mutabakat_ajani"],
            )
        else:
            kaydet("nakit_koprusu_mutabakati", "gecti", "Nakit köprüsü mutabık.", ["finansal_tablo_mutabakat_ajani"])

    alacak = ajanlar.get("alacak_yaslandirma_ajani", {})
    if alacak.get("durum") != "veri_bekliyor":
        hatali_faturalar = alacak.get("hatali_faturalar", [])
        kaydet(
            "alacak_fatura_tutarliligi",
            "gecti" if not hatali_faturalar else "kritik",
            "Açık alacak faturalarında negatif bakiye yok."
            if not hatali_faturalar else f"Hatalı faturalar: {', '.join(hatali_faturalar[:10])}.",
            ["alacak_yaslandirma_ajani"],
        )
        acik_alacak = float(alacak.get("acik_alacak") or 0)
        finansal_alacak = float(istek.finansal_veri.alacaklar or 0)
        if finansal_alacak > 0 and acik_alacak > finansal_alacak * 1.01:
            kaydet(
                "alacak_toplam_kapsami",
                "kritik",
                "Fatura bazlı açık alacak, finansal görünümdeki toplam alacağı aşıyor.",
                ["alacak_yaslandirma_ajani", "finansal_tablo_mutabakat_ajani"],
            )
        elif finansal_alacak > 0 and abs(acik_alacak - finansal_alacak) > finansal_alacak * 0.05:
            kaydet(
                "alacak_toplam_kapsami",
                "uyari",
                "Fatura bazlı açık alacak ile finansal görünüm arasında kapsam farkı var.",
                ["alacak_yaslandirma_ajani", "finansal_tablo_mutabakat_ajani"],
            )
        else:
            kaydet(
                "alacak_toplam_kapsami",
                "gecti",
                "Fatura bazlı açık alacak finansal görünüm sınırları içinde.",
                ["alacak_yaslandirma_ajani", "finansal_tablo_mutabakat_ajani"],
            )

    nakit = ajanlar.get("nakit_13_hafta_ajani", {})
    if nakit.get("tekrar_haftalar"):
        kaydet(
            "nakit_tekrar_hafta",
            "kritik",
            "13 haftalık nakit verisinde tekrar eden hafta kayıtları var.",
            ["nakit_13_hafta_ajani", "anomali_ve_denetim_ajani"],
        )
    elif nakit.get("hafta_bosluklari"):
        kaydet(
            "nakit_hafta_surekliligi",
            "uyari",
            "13 haftalık nakit verisinde tarih boşlukları var.",
            ["nakit_13_hafta_ajani"],
        )

    borc = ajanlar.get("borc_servis_ajani", {})
    if borc.get("durum") == "sinirli":
        kaydet(
            "borc_servis_kapsami",
            "uyari",
            "; ".join(borc.get("gerekenler", [])) or "Borç servis analizi sınırlı veriyle tamamlandı.",
            ["borc_servis_ajani"],
        )

    butce = ajanlar.get("butce_tahmin_ajani", {})
    if butce.get("durum") == "sinirli":
        kaydet(
            "butce_tahmin_kapsami",
            "uyari",
            "Bütçe tahmini için en az üç gerçekleşen ay gerekli.",
            ["butce_tahmin_ajani"],
        )

    anomali = ajanlar.get("anomali_ve_denetim_ajani", {})
    anomaliler = anomali.get("anomaliler", [])
    kaydet(
        "anomali_kapisi",
        "gecti" if not anomaliler else "kritik",
        "Tanımlı veri anomalisi bulunmadı."
        if not anomaliler else f"{len(anomaliler)} veri anomalisi insan incelemesi gerektiriyor.",
        ["anomali_ve_denetim_ajani"],
    )

    veri_bekleyenler = [sonuc["ajan"] for sonuc in sonuclar if sonuc.get("durum") == "veri_bekliyor"]
    durum = "engellendi" if kritikler else "inceleme_gerekli" if uyarilar else "onaylandi"
    ai_kapsami = (
        "engelli" if kritikler
        else "temel_finansal_gorunum" if len(veri_bekleyenler) >= 6
        else "sinirli" if veri_bekleyenler or uyarilar
        else "tam"
    )
    return {
        "denetci": "bas_denetci",
        "durum": durum,
        "ai_kullanilabilir": not kritikler,
        "ai_kapsami": ai_kapsami,
        "kritik_sorun_sayisi": len(kritikler),
        "uyari_sayisi": len(uyarilar),
        "veri_bekleyen_ajanlar": veri_bekleyenler,
        "kontroller": kontroller,
        "kritikler": kritikler,
        "uyarilar": uyarilar,
        "metodoloji": "Baş denetçi yeni finansal değer üretmez; ajan sonuçlarını çapraz mutabakat kapılarından geçirir.",
    }


def gelismis_ajan_analizi(istek: GelismisAjanIstegi) -> Dict[str, Any]:
    sonuclar = [
        mizan_ajani(istek),
        finansal_tablo_mutabakat_ajani(istek),
        nakit_13_hafta_ajani(istek),
        alacak_ajani(istek),
        borc_servis_ajani(istek),
        butce_tahmin_ajani(istek),
    ]
    sonuclar.append(anomali_ve_denetim_ajani(istek, sonuclar))
    denetim = bas_denetci(istek, sonuclar)
    return {
        "durum": "aktif",
        "ajanlar": {sonuc["ajan"]: sonuc for sonuc in sonuclar},
        "bas_denetim": denetim,
        "veri_ufku": veri_ufku_ozeti(istek),
        "ozet": {
            "toplam": len(sonuclar),
            "tamamlanan": sum(1 for s in sonuclar if s["durum"] == "tamamlandi"),
            "inceleme_gerekli": sum(1 for s in sonuclar if s["durum"] in {"inceleme_gerekli", "sinirli"}),
            "veri_bekliyor": sum(1 for s in sonuclar if s["durum"] == "veri_bekliyor"),
        },
    }

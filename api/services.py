"""HTTP katmanından bağımsız V1 finans ve CFO servisleri."""

from typing import Any, Dict, Optional

import pandas as pd

from cashflow_engine import CashFlowEngine
from financial_engine import FinancialEngine
from api.financial_metrics import kurumsal_metrikleri_hesapla
from api.ai_orchestrator import (
    ai_durumu,
    ai_yaniti_uret,
    eksik_veri_metni,
    metrik_ozeti,
    veri_kalitesini_degerlendir,
)
from api.models import FinansalAnalizIstegi, FinansalGorunum


def _json_uyumlu(deger: Any) -> Any:
    if isinstance(deger, pd.DataFrame):
        return [_json_uyumlu(satir) for satir in deger.to_dict(orient="records")]
    if isinstance(deger, dict):
        return {anahtar: _json_uyumlu(alt) for anahtar, alt in deger.items()}
    if isinstance(deger, (list, tuple)):
        return [_json_uyumlu(alt) for alt in deger]
    if hasattr(deger, "item"):
        return deger.item()
    if pd.isna(deger):
        return None
    return deger


def zaman_serisi_analizi(istek: FinansalAnalizIstegi) -> Dict[str, Any]:
    veri = pd.DataFrame(
        {
            "Tarih": [satir.tarih for satir in istek.satirlar],
            "Kategori": [satir.kategori for satir in istek.satirlar],
            "Gelir": [satir.gelir for satir in istek.satirlar],
            "Gider": [satir.gider for satir in istek.satirlar],
        }
    )
    finans = FinancialEngine.from_dataframe(veri)
    nakit = CashFlowEngine.from_financial_engine(
        finans,
        baslangic_nakiti=istek.bilanco.baslangic_nakiti,
        donen_varliklar=istek.bilanco.donen_varliklar,
        kisa_vadeli_borc=istek.bilanco.kisa_vadeli_borc,
        stoklar=istek.bilanco.stoklar,
    )
    return _json_uyumlu({"finansal": finans.full_report(), "nakit": nakit.full_report()})


def finansal_denetim(veri: FinansalGorunum) -> Dict[str, Any]:
    brut_kar = veri.ciro - veri.satis_maliyeti
    faaliyet_kari_yaklasik = brut_kar - veri.faaliyet_giderleri
    favok_girdileri_hazir = all(
        deger is not None for deger in (veri.faiz_gideri, veri.vergi_gideri, veri.amortisman)
    )
    favok = (
        veri.net_kar + veri.faiz_gideri + veri.vergi_gideri + veri.amortisman
        if favok_girdileri_hazir
        else None
    )
    kar_marji = (veri.net_kar / veri.ciro * 100) if veri.ciro else 0.0
    cari_oran = (
        (veri.nakit + veri.alacaklar + veri.stoklar) / veri.kisa_vadeli_borc
        if veri.kisa_vadeli_borc
        else None
    )
    borc_ozkaynak = (
        (veri.kisa_vadeli_borc + veri.uzun_vadeli_borc) / veri.ozkaynak
        if veri.ozkaynak
        else None
    )
    isletme_sermayesi = veri.nakit + veri.alacaklar + veri.stoklar - veri.kisa_vadeli_borc
    kurumsal_metrikler = kurumsal_metrikleri_hesapla(veri)

    riskler = []
    aksiyonlar = []
    if kar_marji < 0:
        riskler.append("Şirket incelenen dönemde zarar ediyor.")
        aksiyonlar.append("Negatif katkı marjına sahip ürün ve gider kalemlerini 7 gün içinde ayırın.")
    elif kar_marji < 10:
        riskler.append(f"Net kâr marjı %{kar_marji:.1f} ile hassas seviyede.")
        aksiyonlar.append("Fiyatlama ve faaliyet giderlerinde en az üç tasarruf senaryosu oluşturun.")

    if cari_oran is not None and cari_oran < 1.2:
        riskler.append(f"Cari oran {cari_oran:.2f}; kısa vadeli ödeme tamponu sınırlı.")
        aksiyonlar.append("13 haftalık nakit planı çıkarıp kısa vadeli borçları vade önceliğine göre sıralayın.")

    if veri.alacaklar > veri.borclar * 1.5 and veri.alacaklar > 0:
        riskler.append("Alacak bakiyesi ticari borçların belirgin üzerinde.")
        aksiyonlar.append("En büyük beş alacak için tahsilat sahibi ve hedef tarihi belirleyin.")

    altman = kurumsal_metrikler["altman_z_prime"]
    if altman["durum"] == "hesaplandi" and altman["deger"] < 1.23:
        riskler.append(f"Altman Z' skoru {altman['deger']:.2f}; finansal sıkıntı bölgesinde.")
        aksiyonlar.append("Likidite, borç vadesi ve işletme sermayesi için stres senaryosunu CFO onayına sunun.")

    hhi = kurumsal_metrikler["musteri_hhi"]
    if hhi["durum"] == "hesaplandi" and hhi["deger"] > 2_500:
        riskler.append(f"Müşteri ciro HHI skoru {hhi['deger']:.0f}; gelir yoğunlaşması yüksek.")
        aksiyonlar.append("En büyük müşteriler için kayıp ve tahsilat stres senaryosu hazırlayın.")

    if not aksiyonlar:
        aksiyonlar.append("Mevcut marj ve likidite seviyelerini aylık eşiklerle izlemeye devam edin.")

    kalite = veri_kalitesini_degerlendir(veri)
    return {
        "sirket_adi": veri.sirket_adi,
        "donem": veri.donem,
        # Kullanıcının bildirdiği ham değerler. AI bunlardan söz edebilmelidir;
        # guardrail izin listesini buradan da besler ve kaynağını adıyla gösterir.
        "girdi_degerleri": {
            ad: deger
            for ad, deger in (
                ("ciro", veri.ciro),
                ("satis_maliyeti", veri.satis_maliyeti),
                ("faaliyet_giderleri", veri.faaliyet_giderleri),
                ("net_kar", veri.net_kar),
                ("nakit", veri.nakit),
                ("alacaklar", veri.alacaklar),
                ("borclar", veri.borclar),
                ("stoklar", veri.stoklar),
                ("kisa_vadeli_borc", veri.kisa_vadeli_borc),
                ("uzun_vadeli_borc", veri.uzun_vadeli_borc),
                ("ozkaynak", veri.ozkaynak),
                ("faiz_gideri", veri.faiz_gideri),
                ("vergi_gideri", veri.vergi_gideri),
                ("amortisman", veri.amortisman),
                ("capex", veri.capex),
                ("donen_varliklar", veri.donen_varliklar),
                ("toplam_varliklar", veri.toplam_varliklar),
                ("toplam_yukumlulukler", veri.toplam_yukumlulukler),
                ("operasyonel_nakit_akisi", veri.operasyonel_nakit_akisi),
                ("donem_basi_nakit", veri.donem_basi_nakit),
                ("yatirim_nakit_akisi", veri.yatirim_nakit_akisi),
                ("finansman_nakit_akisi", veri.finansman_nakit_akisi),
            )
            if isinstance(deger, (int, float))
        },
        "metrikler": {
            "brut_kar": round(brut_kar, 2),
            "faaliyet_kari_yaklasik": round(faaliyet_kari_yaklasik, 2),
            "favok": round(favok, 2) if favok is not None else None,
            "favok_durumu": "hesaplandi" if favok is not None else "eksik_veri",
            "net_kar_marji": round(kar_marji, 2),
            "cari_oran": round(cari_oran, 2) if cari_oran is not None else None,
            "borc_ozkaynak_orani": round(borc_ozkaynak, 2) if borc_ozkaynak is not None else None,
            "net_isletme_sermayesi": round(isletme_sermayesi, 2),
            "altman_z_prime": altman["deger"],
            "dupont_roe": kurumsal_metrikler["dupont_roe"]["deger"],
            "roic": kurumsal_metrikler["roic"]["deger"],
            "serbest_nakit_akisi": kurumsal_metrikler["serbest_nakit_akisi"]["deger"],
            "nakit_donusum_dongusu": kurumsal_metrikler["nakit_donusum_dongusu"]["deger"],
            "musteri_hhi": hhi["deger"],
        },
        "metrik_kaydi": kurumsal_metrikler,
        "riskler": riskler,
        "aksiyonlar": aksiyonlar,
        "veri_kalitesi": {
            "seviye": kalite.seviye,
            "skor": kalite.skor,
            "eksikler": kalite.eksikler,
            "uyarilar": kalite.uyarilar,
        },
        "hesaplama_notlari": {
            "favok": "Net kâr + faiz gideri + vergi gideri + amortisman. Eksik girdide hesaplanmaz.",
            "nakit_akisi": "Net kâr nakit akışı değildir; CapEx ve nakit hareketleri ayrıca girilmelidir.",
        },
        "uyari": "Bu çıktı karar destek amaçlıdır; bağımsız mali veya hukuki danışmanlık yerine geçmez.",
    }


def cfo_yaniti(
    mesaj: str,
    veri: FinansalGorunum,
    ajan_denetimi: Optional[Dict[str, Any]] = None,
    sirket_profili: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    denetim = finansal_denetim(veri)
    kalite = veri_kalitesini_degerlendir(veri)
    risk_metni = " ".join(denetim["riskler"]) or "Tanımlı eşiklerde kritik ihlal görülmedi."
    aksiyon_metni = "\n".join(
        f"{sira}. {aksiyon}" for sira, aksiyon in enumerate(denetim["aksiyonlar"], start=1)
    )

    temel = (
        f"**{veri.sirket_adi} — doğrulanmış finans motoru**\n\n"
        f"{metrik_ozeti(denetim)}\n\n"
        f"**Risk özeti:** {risk_metni}"
    )

    if ajan_denetimi and not ajan_denetimi.get("ai_kullanilabilir", False):
        sorunlar = [
            kayit.get("mesaj", "Ajan mutabakatı tamamlanmadı.")
            for kayit in ajan_denetimi.get("kritikler", [])[:5]
        ]
        engel_metni = "\n".join(f"- {sorun}" for sorun in sorunlar) or "- Baş denetçi AI kullanımına onay vermedi."
        yanit = (
            f"{temel}\n\n**AI yorumu üretilmedi.** Baş denetçi ajan sonuçlarında kritik "
            f"mutabakat sorunu buldu:\n{engel_metni}\n\n"
            f"**İnsan onaylı sonraki adımlar:**\n{aksiyon_metni}"
        )
        return {
            "yanit": yanit,
            "kaynak": "bas_denetci",
            "model": "yok",
            "guven": "dusuk",
            "yedek_kullanildi": False,
            "ai_dogrulama": {
                "durum": "ajan_engeli",
                "kontrol_edilen_sayi": 0,
                "reddedilen_sayilar": [],
            },
            "veri_kalitesi": denetim["veri_kalitesi"],
            "ajanlar": ai_durumu()["aktif_ajanlar"],
            "insan_onayi_gerekli": True,
            "denetim": denetim,
        }

    if not kalite.ai_kullanilabilir:
        yanit = (
            f"{temel}\n\n**AI yorumu üretilmedi.** Veri kalitesi kesin öneri için yetersiz.\n"
            f"{eksik_veri_metni(kalite)}\n\n**İnsan onaylı sonraki adımlar:**\n{aksiyon_metni}"
        )
        return {
            "yanit": yanit,
            "kaynak": "kuralli_finans_motoru",
            "model": "yok",
            "guven": "dusuk",
            "yedek_kullanildi": False,
            "ai_dogrulama": {
                "durum": "veri_engeli",
                "kontrol_edilen_sayi": 0,
                "reddedilen_sayilar": [],
            },
            "veri_kalitesi": denetim["veri_kalitesi"],
            "ajanlar": ai_durumu()["aktif_ajanlar"],
            "insan_onayi_gerekli": True,
            "denetim": denetim,
        }

    uretim = ai_yaniti_uret(mesaj, denetim, kalite, sirket_profili)
    if uretim.metin:
        ai_bolumu = f"**AI açıklaması:**\n{uretim.metin}"
        guven = "orta" if kalite.seviye == "sinirli" else "yuksek"
    else:
        ai_bolumu = (
            "**AI açıklaması:** AI yanıtı sağlayıcı veya doğrulama kontrolünü geçemediği için "
            "kurallı finans özeti kullanıldı."
        )
        guven = "orta" if kalite.seviye == "iyi" else "dusuk"

    yanit = (
        f"{temel}\n\n{ai_bolumu}\n\n"
        f"**İnsan onayı gerektiren olası aksiyonlar:**\n{aksiyon_metni}\n\n"
        "KazKaz yalnızca karar desteği sağlar; hiçbir finansal işlemi otomatik başlatmaz."
    )
    return {
        "yanit": yanit,
        "kaynak": uretim.saglayici,
        "model": uretim.model,
        "guven": guven,
        "yedek_kullanildi": uretim.yedek_kullanildi,
        "ai_dogrulama": {
            "durum": uretim.dogrulama_durumu,
            "kontrol_edilen_sayi": uretim.kontrol_edilen_sayi,
            "reddedilen_sayilar": uretim.reddedilen_sayilar,
            "kaynak_eslesmeleri": uretim.kaynak_eslesmeleri,
        },
        "veri_kalitesi": denetim["veri_kalitesi"],
        "ajanlar": ai_durumu()["aktif_ajanlar"],
        "insan_onayi_gerekli": True,
        "denetim": denetim,
    }

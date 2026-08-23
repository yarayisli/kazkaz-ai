"""Eski CFO araçlarını V1 veri sözleşmesine güvenli biçimde bağlayan adaptör."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from cfo_agent import Alert, CFOAgent

from api.models import CfoAjanAnalizIstegi
from api.services import finansal_denetim


METODOLOJI_ONAYLARI = [
    {
        "alan": "Finansal sağlık ve likidite eşikleri",
        "teknik_test": "otomatik test kapsamında",
        "uzman_onayi": "bekliyor",
        "kullanim": "uyarı ve inceleme önceliği",
    },
    {
        "alan": "FAVÖK formülü",
        "teknik_test": "eksik girdide hesaplamama testi aktif",
        "uzman_onayi": "muhasebeci/CFO onayı bekliyor",
        "kullanim": "faiz, vergi ve amortisman eksikse gösterilmez",
    },
    {
        "alan": "Yatırım ve borç aksiyonları",
        "teknik_test": "otomatik aksiyon engeli aktif",
        "uzman_onayi": "her karar için gerekli",
        "kullanim": "yalnızca iş vakası ve veri ihtiyacı üretir",
    },
]


def _uyari_json(uyari: Alert) -> Dict[str, Any]:
    return {
        "seviye": uyari.seviye.value,
        "baslik": uyari.baslik,
        "mesaj": uyari.mesaj,
        "oneri": uyari.oneri,
        "arac": uyari.araç,
        "deger": uyari.deger,
        "insan_onayi_gerekli": True,
    }


def _finans_raporu(istek: CfoAjanAnalizIstegi) -> Dict[str, Any]:
    veri = istek.finansal_veri
    denetim = finansal_denetim(veri)
    return {
        "gelir": {
            "toplam_gelir": veri.ciro,
            "ortalama_aylik_gelir": None,
            "ortalama_buyume_orani": None,
        },
        "gider": {"toplam_gider": veri.satis_maliyeti + veri.faaliyet_giderleri,
                  "sabit_gider_orani": None},
        "karlilik": {
            "toplam_net_kar": veri.net_kar,
            "kar_marji": denetim["metrikler"]["net_kar_marji"],
            "kar_trendi": "Zaman serisi gerekli",
        },
        "saglik_skoru": {"skor": None, "kategori": "Zaman serisi gerekli"},
    }


def _nakit_raporu(istek: CfoAjanAnalizIstegi, cari_oran: Optional[float]) -> Dict[str, Any]:
    if not istek.nakit_akisi:
        return {}

    toplam_giris = sum(satir.giris for satir in istek.nakit_akisi)
    toplam_cikis = sum(satir.cikis for satir in istek.nakit_akisi)
    toplam_net = sum(satir.net_nakit for satir in istek.nakit_akisi)
    ortalama_net = toplam_net / len(istek.nakit_akisi)
    nakit_yakiliyor = ortalama_net < 0
    runway = (
        istek.finansal_veri.nakit / abs(ortalama_net)
        if nakit_yakiliyor and istek.finansal_veri.nakit > 0
        else None
    )
    return {
        "nakit_ozet": {
            "operasyonel_ncf": toplam_net,
            "ncf_marji": (toplam_net / toplam_giris * 100) if toplam_giris else None,
            "son_nakit_pozisyon": istek.finansal_veri.nakit,
        },
        "likidite": {"cari_oran": cari_oran, "nakit_donusum_gun": None},
        "burn_rate": {
            "runway_ay": runway,
            "nakit_yakilip_yakilmiyor": nakit_yakiliyor,
            "verimlilik_orani": toplam_giris / toplam_cikis if toplam_cikis else None,
        },
    }


def _borc_raporu(istek: CfoAjanAnalizIstegi) -> Dict[str, Any]:
    kalemler = istek.borclar
    toplam = sum(kalem.tutar for kalem in kalemler) or (
        istek.finansal_veri.kisa_vadeli_borc + istek.finansal_veri.uzun_vadeli_borc
    )
    faizli = [kalem for kalem in kalemler if kalem.faiz_orani is not None]
    faiz_taban = sum(kalem.tutar for kalem in faizli)
    agirlikli_faiz = (
        sum(kalem.tutar * kalem.faiz_orani for kalem in faizli) / faiz_taban
        if faiz_taban
        else None
    )
    return {
        "portfolio_ozet": {
            "toplam_borc": toplam,
            "agirlikli_faiz": agirlikli_faiz,
        }
    }


def cfo_ajan_analizi(istek: CfoAjanAnalizIstegi) -> Dict[str, Any]:
    denetim = finansal_denetim(istek.finansal_veri)
    agent = CFOAgent(
        ai_engine=None,
        fin_rapor=_finans_raporu(istek),
        sirket_adi=istek.finansal_veri.sirket_adi,
        cf_rapor=_nakit_raporu(istek, denetim["metrikler"]["cari_oran"]),
        debt_rapor=_borc_raporu(istek),
    )
    analiz = agent.analyze()
    return {
        "durum": "aktif_kontrollu",
        "araclar": [
            "FinancialHealthTool",
            "CashFlowAlertTool",
            "InvestmentAdvisorTool",
            "DebtAdvisorTool",
            "ReportGeneratorTool",
        ],
        "uyarilar": [_uyari_json(uyari) for uyari in analiz["uyarilar"]],
        "nakit": analiz["cf"],
        "yatirim": analiz["inv"],
        "borc": analiz["debt"],
        "rapor": agent.generate_report(periyot=istek.finansal_veri.donem),
        "metodoloji_onaylari": METODOLOJI_ONAYLARI,
        "sinirlar": [
            "Sağlık skoru için doğrulanmış zaman serisi gereklidir.",
            "DSCR için operasyonel nakit ve gerçek anapara/faiz ödemeleri gereklidir.",
            "Yatırım tutarı ve ROI yalnızca proje iş vakası ile hesaplanır.",
            "Hiçbir araç ödeme, kredi, yatırım veya muhasebe kaydı başlatmaz.",
        ],
    }

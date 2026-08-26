"""KazKaz veri kalitesi katmanı — cross-field tutarlılık + anomali taraması.

Kullanıcı hatasından doğan sessiz sorunları erken yakalar. İki kategori:

**Tutarlılık:** finansal veri kalemleri arasındaki muhasebe eşitlikleri
(ör. bilanço eşitliği, net kâr = gelir - gider - faiz - vergi).

**Anomali:** istatistiksel olarak anormal sinyaller (aşırı marj, tek
müşteri konsantrasyonu, imkânsız oranlar).

Her bulgu ``seviye`` alanı taşır: ``"hata"`` (kesin problem, düzeltilmeli)
veya ``"uyari"`` (kontrol edilmeli). ``kod`` alanı programatik gruplamak
içindir. Bu modül hiçbir hesap yapmaz — sadece bakar ve söyler.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Optional


# ─────────────────────────────────────────────
# Yardımcılar
# ─────────────────────────────────────────────

def _sayi(deger: Any) -> Optional[float]:
    """None-safe float; sonlu değilse None döner."""
    if deger is None:
        return None
    try:
        v = float(deger)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(v):
        return None
    return v


def _bulgu(
    kod: str, alan: str, mesaj: str, seviye: str = "uyari",
    beklenen: Optional[float] = None, gozlemlenen: Optional[float] = None,
    sapma_yuzde: Optional[float] = None,
) -> Dict[str, Any]:
    b: Dict[str, Any] = {"kod": kod, "alan": alan, "mesaj": mesaj, "seviye": seviye}
    if beklenen is not None:
        b["beklenen"] = round(beklenen, 2)
    if gozlemlenen is not None:
        b["gozlemlenen"] = round(gozlemlenen, 2)
    if sapma_yuzde is not None:
        b["sapma_yuzde"] = round(sapma_yuzde, 2)
    return b


# ─────────────────────────────────────────────
# Cross-field tutarlılık kontrolleri
# ─────────────────────────────────────────────

TOLERANS_YUZDE = 5.0  # muhasebe eşitliklerinde ±%5 tolerans


def tutarlilik_kontrolu(finansal_veri: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Muhasebe kimlikleri arasındaki tutarlılığı kontrol eder."""
    bulgular: List[Dict[str, Any]] = []
    fv = finansal_veri or {}

    ciro          = _sayi(fv.get("ciro"))
    satis_mal     = _sayi(fv.get("satis_maliyeti"))
    faaliyet_gid  = _sayi(fv.get("faaliyet_giderleri"))
    faiz          = _sayi(fv.get("faiz_gideri")) or 0.0
    vergi         = _sayi(fv.get("vergi_gideri")) or 0.0
    net_kar       = _sayi(fv.get("net_kar"))

    # 1) Ciro pozitif olmalı
    if ciro is not None and ciro < 0:
        bulgular.append(_bulgu(
            "negatif_ciro", "ciro",
            "Ciro negatif giriliyor; iade toplamı ciroyu aşamaz.",
            seviye="hata", gozlemlenen=ciro,
        ))

    # 2) Net kâr = Ciro − COGS − OpEx − Faiz − Vergi (±%5 tolerans)
    if all(v is not None for v in (ciro, satis_mal, faaliyet_gid, net_kar)):
        beklenen_kar = ciro - satis_mal - faaliyet_gid - faiz - vergi
        if abs(ciro) > 0:
            fark_yuzde = abs(beklenen_kar - net_kar) / abs(ciro) * 100
            if fark_yuzde > TOLERANS_YUZDE:
                bulgular.append(_bulgu(
                    "kar_tanimi_tutarsiz", "net_kar",
                    "Net kâr = Ciro − Satış Maliyeti − Faaliyet Giderleri − "
                    "Faiz − Vergi eşitliği tolerans dışında. Amortisman veya "
                    "diğer gelir/gider ayrımı eksik olabilir.",
                    seviye="uyari",
                    beklenen=beklenen_kar, gozlemlenen=net_kar,
                    sapma_yuzde=fark_yuzde,
                ))

    # 3) Bilanço eşitliği: Toplam Varlıklar = Toplam Yükümlülükler + Özkaynak
    toplam_varliklar = _sayi(fv.get("toplam_varliklar"))
    toplam_yukum     = _sayi(fv.get("toplam_yukumlulukler"))
    ozkaynak         = _sayi(fv.get("ozkaynak"))
    if all(v is not None for v in (toplam_varliklar, toplam_yukum, ozkaynak)):
        pasif = toplam_yukum + ozkaynak
        if toplam_varliklar > 0:
            fark_yuzde = abs(pasif - toplam_varliklar) / toplam_varliklar * 100
            if fark_yuzde > TOLERANS_YUZDE:
                bulgular.append(_bulgu(
                    "bilanco_esitsizligi", "toplam_varliklar",
                    "Bilanço eşitliği tolerans dışında: Varlıklar ≠ "
                    "Yükümlülükler + Özkaynak.",
                    seviye="hata",
                    beklenen=pasif, gozlemlenen=toplam_varliklar,
                    sapma_yuzde=fark_yuzde,
                ))

    # 4) Dönen varlıklar toplam varlıkları aşamaz
    donen = _sayi(fv.get("donen_varliklar"))
    if donen is not None and toplam_varliklar is not None and donen > toplam_varliklar:
        bulgular.append(_bulgu(
            "donen_varlik_asimi", "donen_varliklar",
            "Dönen varlıklar toplam varlıkları aşamaz.",
            seviye="hata",
            beklenen=toplam_varliklar, gozlemlenen=donen,
        ))

    # 5) Nakit dönen varlıkları aşamaz
    nakit = _sayi(fv.get("nakit"))
    if nakit is not None and donen is not None and nakit > donen:
        bulgular.append(_bulgu(
            "nakit_donen_varlik_asimi", "nakit",
            "Nakit dönen varlıkları aşamaz.",
            seviye="hata",
            beklenen=donen, gozlemlenen=nakit,
        ))

    # 6) Kısa vadeli borç toplam yükümlülükleri aşamaz
    kvborc = _sayi(fv.get("kisa_vadeli_borc"))
    if kvborc is not None and toplam_yukum is not None and kvborc > toplam_yukum:
        bulgular.append(_bulgu(
            "kvborc_yukumluluk_asimi", "kisa_vadeli_borc",
            "Kısa vadeli borç toplam yükümlülükleri aşamaz.",
            seviye="hata",
            beklenen=toplam_yukum, gozlemlenen=kvborc,
        ))

    # 7) Nakit akış özeti: Op + Yatırım + Finansman ≈ Nakit değişimi
    op_akis  = _sayi(fv.get("operasyonel_nakit_akisi"))
    yat_akis = _sayi(fv.get("yatirim_nakit_akisi"))
    fin_akis = _sayi(fv.get("finansman_nakit_akisi"))
    donem_basi_nakit = _sayi(fv.get("donem_basi_nakit"))
    if all(v is not None for v in (op_akis, yat_akis, fin_akis, nakit, donem_basi_nakit)):
        beklenen_nakit = donem_basi_nakit + op_akis + yat_akis + fin_akis
        ref = max(abs(nakit), abs(donem_basi_nakit), 1.0)
        fark_yuzde = abs(beklenen_nakit - nakit) / ref * 100
        if fark_yuzde > TOLERANS_YUZDE:
            bulgular.append(_bulgu(
                "nakit_akis_tutarsiz", "nakit",
                "Nakit akış özeti tutarlı değil: Dönem başı + Operasyonel + "
                "Yatırım + Finansman ≠ Dönem sonu nakit.",
                seviye="uyari",
                beklenen=beklenen_nakit, gozlemlenen=nakit,
                sapma_yuzde=fark_yuzde,
            ))

    return bulgular


# ─────────────────────────────────────────────
# Anomali taraması
# ─────────────────────────────────────────────

# Net kâr marjı %100'ü aşarsa hemen hemen daima veri hatasıdır (giriş
# yanlış sütuna yazılmış, katlar karışmış vb.). %-100 altı da benzer.
MAX_MAKUL_MARJ = 100.0
MIN_MAKUL_MARJ = -100.0

# Tek müşteri konsantrasyonu — %80 üstü tek müşteriye bağımlılık kırmızı bayrak.
KONSANTRASYON_ESIGI = 80.0

# Toplam gider ciroyu %500'ün üstünde aşarsa muhtemelen dönem/birim karışıklığı.
GIDER_CIRO_KAT_ESIGI = 5.0

# Ay-üstü büyüme %500 (5x) — muhtemelen düşük veri veya iade dalgası
AY_USTU_SICRAMA_ESIGI = 500.0


def anomali_taramasi(
    finansal_veri: Dict[str, Any],
    zaman_serisi: Optional[List[Dict[str, Any]]] = None,
    musteri_cirolari: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """İstatistiksel olarak anormal sinyalleri işaretler."""
    bulgular: List[Dict[str, Any]] = []
    fv = finansal_veri or {}

    ciro = _sayi(fv.get("ciro"))
    net_kar = _sayi(fv.get("net_kar"))

    # 1) Net kâr marjı imkânsız aralıkta mı?
    if ciro is not None and net_kar is not None and ciro > 0:
        marj = net_kar / ciro * 100
        if marj > MAX_MAKUL_MARJ or marj < MIN_MAKUL_MARJ:
            bulgular.append(_bulgu(
                "olağandışı_marj", "net_kar",
                f"Net kâr marjı %{round(marj, 1)} — makul aralığın dışında "
                f"({MIN_MAKUL_MARJ:.0f} – {MAX_MAKUL_MARJ:.0f}). "
                "Ciro veya net kâr yanlış sütuna yazılmış olabilir.",
                seviye="hata",
                gozlemlenen=marj,
            ))

    # 2) Toplam gider ciroyu aşırı aşıyor mu?
    satis_mal = _sayi(fv.get("satis_maliyeti")) or 0.0
    faaliyet_gid = _sayi(fv.get("faaliyet_giderleri")) or 0.0
    toplam_gider = satis_mal + faaliyet_gid
    if ciro is not None and ciro > 0 and toplam_gider > ciro * GIDER_CIRO_KAT_ESIGI:
        bulgular.append(_bulgu(
            "gider_ciro_orani_asiri", "faaliyet_giderleri",
            f"Toplam işletme gideri ciroyu {round(toplam_gider / ciro, 1)}× "
            "aşıyor. Dönem farkı veya birim (adet/bin ₺) karışıklığı olabilir.",
            seviye="uyari",
            gozlemlenen=toplam_gider, beklenen=ciro,
        ))

    # 3) Tek müşteri konsantrasyonu
    if musteri_cirolari:
        toplam = sum(_sayi(m.get("ciro")) or 0.0 for m in musteri_cirolari)
        if toplam > 0:
            en_buyuk = max(_sayi(m.get("ciro")) or 0.0 for m in musteri_cirolari)
            pay = en_buyuk / toplam * 100
            if pay >= KONSANTRASYON_ESIGI:
                bulgular.append(_bulgu(
                    "musteri_konsantrasyonu", "musteri_cirolari",
                    f"Tek müşteri toplam cironun %{round(pay, 1)}'ini "
                    "oluşturuyor. Bu müşteri kaybı iş sürekliliği için "
                    "kritik risk.",
                    seviye="uyari",
                    gozlemlenen=pay,
                ))

    # 4) Ay-üstü aşırı sıçrama (zaman serisi verildiyse)
    if zaman_serisi:
        aylik: Dict[str, float] = {}
        for satir in zaman_serisi:
            gelir = _sayi(satir.get("gelir")) or 0.0
            tarih = str(satir.get("tarih") or "")[:7]  # YYYY-MM
            if not tarih:
                continue
            aylik[tarih] = aylik.get(tarih, 0.0) + gelir
        aylar = sorted(aylik.keys())
        for i in range(1, len(aylar)):
            oncekii, sonraki = aylik[aylar[i - 1]], aylik[aylar[i]]
            if oncekii <= 0:
                continue
            degisim = (sonraki - oncekii) / oncekii * 100
            if abs(degisim) >= AY_USTU_SICRAMA_ESIGI:
                bulgular.append(_bulgu(
                    "ay_ustu_sicrama", "zaman_serisi",
                    f"{aylar[i - 1]} → {aylar[i]}: gelir %{round(degisim, 0):.0f} "
                    "değişti. Veri girişinde birim/dönem karışıklığı olabilir.",
                    seviye="uyari",
                    gozlemlenen=degisim,
                ))

    return bulgular


# ─────────────────────────────────────────────
# Birleşik rapor
# ─────────────────────────────────────────────

def kalite_raporu(
    finansal_veri: Dict[str, Any],
    zaman_serisi: Optional[List[Dict[str, Any]]] = None,
    musteri_cirolari: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Tutarlılık + anomali bulgularını tek payload'ta döner."""
    tutarlilik = tutarlilik_kontrolu(finansal_veri)
    anomali = anomali_taramasi(
        finansal_veri,
        zaman_serisi=zaman_serisi,
        musteri_cirolari=musteri_cirolari,
    )
    hepsi = tutarlilik + anomali
    hata_sayisi = sum(1 for b in hepsi if b["seviye"] == "hata")
    uyari_sayisi = sum(1 for b in hepsi if b["seviye"] == "uyari")
    return {
        "tutarlilik_bulgulari": tutarlilik,
        "anomali_bulgulari": anomali,
        "toplam_hata": hata_sayisi,
        "toplam_uyari": uyari_sayisi,
        "durum": (
            "temiz" if hata_sayisi == 0 and uyari_sayisi == 0
            else "uyarili" if hata_sayisi == 0
            else "hatali"
        ),
    }

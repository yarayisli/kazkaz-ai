"""Ödeme sağlayıcısından bağımsız sunucu tarafı paket/özellik kapıları."""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from typing import Callable

from fastapi import Depends, HTTPException, status

from api.auth import mevcut_sirket_uyesi
from api.models import KimlikBilgisi


PLAN_OZELLIKLERI = {
    "free": {"temel_analiz", "excel_yukleme"},
    "trial": {"temel_analiz", "excel_yukleme", "google_sheets", "rapor", "ai_cfo", "gelismis_ajanlar"},
    "pro": {"temel_analiz", "excel_yukleme", "google_sheets", "rapor", "ai_cfo", "gelismis_ajanlar"},
    "uzman": {"temel_analiz", "excel_yukleme", "google_sheets", "rapor", "ai_cfo", "gelismis_ajanlar", "uzman_onayi"},
}

DESTEKLENEN_ODEME_SAGLAYICILARI = {"iyzico", "paytr", "stripe"}


def _pozitif_tamsayi(adi: str, varsayilan: int) -> int:
    try:
        return max(1, int(os.getenv(adi, str(varsayilan))))
    except ValueError:
        return varsayilan


def odeme_hazirlik_durumu() -> dict:
    """Fiyat veya garanti yayınlamadan önce ticari yapılandırmayı doğrular."""
    saglayici = os.getenv("PAYMENT_PROVIDER", "yapilandirilmadi").strip().lower()
    fiyat_ham = os.getenv("PRO_MONTHLY_PRICE_KURUS", "").strip()
    try:
        fiyat_kurus = int(fiyat_ham) if fiyat_ham else 0
    except ValueError:
        fiyat_kurus = 0
    kontroller = {
        "desteklenen_saglayici": saglayici in DESTEKLENEN_ODEME_SAGLAYICILARI,
        "saglayici_anahtari": bool(os.getenv("PAYMENT_API_KEY", "").strip()),
        "webhook_imza_anahtari": bool(os.getenv("PAYMENT_WEBHOOK_SECRET", "").strip()),
        "pro_fiyati": fiyat_kurus > 0,
        "satis_sozlesmesi_surumu": bool(os.getenv("SALES_TERMS_VERSION", "").strip()),
        "iade_politikasi_surumu": bool(os.getenv("REFUND_POLICY_VERSION", "").strip()),
    }
    eksikler = [ad for ad, tamam in kontroller.items() if not tamam]
    return {
        "durum": "hazir" if not eksikler else "pilot",
        "odeme_saglayicisi": saglayici,
        "kontroller": kontroller,
        "eksikler": eksikler,
        "pro_aylik_fiyat_kurus": fiyat_kurus if not eksikler else None,
        "para_birimi": "TRY",
        "iade_penceresi_gun": _pozitif_tamsayi("REFUND_WINDOW_DAYS", 30),
    }


def kamuya_acik_paketler() -> dict:
    hazirlik = odeme_hazirlik_durumu()
    if hazirlik["durum"] != "hazir":
        return {
            "durum": "pilot",
            "mesaj": "Canlı fiyatlandırma ve ödeme henüz etkin değil.",
            "paketler": [],
            "iade_taahhudu_yayinda": False,
        }
    return {
        "durum": "hazir",
        "paketler": [{
            "kod": "pro",
            "ad": "KazKaz Pro",
            "aylik_fiyat_kurus": hazirlik["pro_aylik_fiyat_kurus"],
            "para_birimi": hazirlik["para_birimi"],
            "ozellikler": sorted(PLAN_OZELLIKLERI["pro"]),
        }],
        "iade_taahhudu_yayinda": True,
        "iade_penceresi_gun": hazirlik["iade_penceresi_gun"],
        "satis_sozlesmesi_surumu": os.environ["SALES_TERMS_VERSION"],
        "iade_politikasi_surumu": os.environ["REFUND_POLICY_VERSION"],
    }


def iade_uygunlugu(odeme_zamani: datetime, *, simdi: datetime | None = None, daha_once_iade_edildi: bool = False) -> dict:
    """Sağlayıcı işleminden bağımsız, test edilebilir iade penceresi hesabı."""
    if odeme_zamani.tzinfo is None:
        odeme_zamani = odeme_zamani.replace(tzinfo=timezone.utc)
    kontrol_zamani = simdi or datetime.now(timezone.utc)
    if kontrol_zamani.tzinfo is None:
        kontrol_zamani = kontrol_zamani.replace(tzinfo=timezone.utc)
    gun = _pozitif_tamsayi("REFUND_WINDOW_DAYS", 30)
    son_tarih = odeme_zamani + timedelta(days=gun)
    uygun = not daha_once_iade_edildi and kontrol_zamani <= son_tarih
    gerekce = "uygun" if uygun else "daha_once_iade_edildi" if daha_once_iade_edildi else "iade_suresi_doldu"
    return {
        "uygun": uygun,
        "gerekce": gerekce,
        "son_basvuru_zamani": son_tarih.isoformat(),
        "iade_penceresi_gun": gun,
        "insan_onayi_gerekli": True,
    }


def etkin_plan(kullanici: KimlikBilgisi) -> str:
    if kullanici.roller.get("gelistirici"):
        return "uzman"
    if kullanici.plan == "trial" and kullanici.deneme_bitis and kullanici.deneme_bitis < date.today():
        return "free"
    return kullanici.plan if kullanici.plan in PLAN_OZELLIKLERI else "free"


def abonelik_durumu(kullanici: KimlikBilgisi) -> dict:
    plan = etkin_plan(kullanici)
    return {
        "plan": plan,
        "ozellikler": sorted(PLAN_OZELLIKLERI[plan]),
        "deneme_bitis": kullanici.deneme_bitis.isoformat() if kullanici.deneme_bitis else None,
        "odeme_saglayicisi": os.getenv("PAYMENT_PROVIDER", "yapilandirilmadi"),
        "sunucu_kapilari": "aktif" if _plan_kapilari_aktif() else "raporlama_modu",
        "odeme_hazirligi": odeme_hazirlik_durumu()["durum"],
    }


def _plan_kapilari_aktif() -> bool:
    varsayilan = "true" if os.getenv("APP_ENV", "development").lower() == "production" else "false"
    return os.getenv("ENFORCE_PLAN_LIMITS", varsayilan).lower() == "true"


def ozellik_kapisi(ozellik: str) -> Callable:
    if ozellik not in set().union(*PLAN_OZELLIKLERI.values()):
        raise ValueError(f"Bilinmeyen paket özelliği: {ozellik}")

    def dogrula(kullanici: KimlikBilgisi = Depends(mevcut_sirket_uyesi)) -> KimlikBilgisi:
        if _plan_kapilari_aktif() and ozellik not in PLAN_OZELLIKLERI[etkin_plan(kullanici)]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Bu özellik mevcut pakette kullanılamıyor: {ozellik}",
            )
        return kullanici

    return dogrula

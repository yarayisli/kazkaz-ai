"""Canlı ortamın gizli değerleri açmadan hazır olup olmadığını denetler."""

import os
from pathlib import Path


def _evet(adi: str) -> bool:
    return os.getenv(adi, "false").strip().lower() in {"1", "true", "yes", "evet"}


def _saklama_suresi_gecerli(env_adi: str = "DATA_RETENTION_DAYS") -> bool:
    try:
        return 1 <= int(os.getenv(env_adi, "0")) <= 3650
    except ValueError:
        return False


def _firebase_admin_kimligi_var() -> bool:
    if os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip():
        return True
    adc_yolu = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    return bool(adc_yolu) and Path(adc_yolu).is_file()


def canli_hazirlik_durumu() -> dict:
    from api.subscription_service import odeme_hazirlik_durumu

    originler = [x.strip() for x in os.getenv("CORS_ORIGINS", "").split(",") if x.strip()]
    hostlar = [x.strip() for x in os.getenv("ALLOWED_HOSTS", "").split(",") if x.strip()]
    kontroller = {
        "production_modu": os.getenv("APP_ENV", "development").lower() == "production",
        "kimlik_bypass_kapali": os.getenv("KAZKAZ_AUTH_DISABLED", "false").lower() != "true",
        "firebase_projesi": bool(os.getenv("FIREBASE_PROJECT_ID", "").strip()),
        "firebase_servis_hesabi": _firebase_admin_kimligi_var(),
        "canli_cors": bool(originler) and all("localhost" not in x and "127.0.0.1" not in x for x in originler),
        "izinli_hostlar": bool(hostlar) and "*" not in hostlar,
        "https_zorunlu": _evet("ENFORCE_HTTPS"),
        "paket_kapilari": os.getenv("ENFORCE_PLAN_LIMITS", "false").lower() == "true",
        "firebase_kurallari_dagitildi": _evet("FIRESTORE_RULES_DEPLOYED"),
        "tenant_izolasyon_testi": _evet("TENANT_ISOLATION_TEST_PASSED"),
        "veri_saklama_politikasi": _saklama_suresi_gecerli(),
        "rapor_saklama_politikasi": _saklama_suresi_gecerli("REPORT_RETENTION_DAYS"),
        "finans_metodoloji_onayi": _evet("FINANCIAL_METHODOLOGY_APPROVED"),
        "kvkk_hukuk_onayi": _evet("KVKK_REVIEW_APPROVED"),
    }
    ai_anahtarlari = [os.getenv(ad, "").strip() for ad in ("NVIDIA_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY")]
    operasyon = {
        "hata_izleme": bool(os.getenv("SENTRY_DSN", "").strip()),
        "yedekleme_hedefi": bool(os.getenv("FIRESTORE_BACKUP_BUCKET", "").strip()),
        "odeme_saglayicisi": odeme_hazirlik_durumu()["durum"] == "hazir",
        "google_sheets": bool(os.getenv("GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON", "").strip()),
        "ai_saglayicisi": any(ai_anahtarlari),
        "ai_yedek_saglayicisi": sum(bool(anahtar) for anahtar in ai_anahtarlari) >= 2,
        "geri_yukleme_tatbikati": bool(os.getenv("BACKUP_RESTORE_TESTED_AT", "").strip()),
    }
    eksikler = [ad for ad, tamam in kontroller.items() if not tamam]
    operasyon_eksikleri = [ad for ad, tamam in operasyon.items() if not tamam]
    return {
        "durum": "hazir" if not eksikler else "eksik",
        "kritik_kontroller": kontroller,
        "operasyon_kontrolleri": operasyon,
        "kritik_eksikler": eksikler,
        "operasyon_eksikleri": operasyon_eksikleri,
    }

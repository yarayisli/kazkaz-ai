"""Firebase kimlik jetonunu doğrulayan FastAPI bağımlılığı."""

import json
import logging
import os
from datetime import date
from functools import lru_cache

from fastapi import Depends, Header, HTTPException, status
from google.auth.exceptions import DefaultCredentialsError

from api.models import KimlikBilgisi


logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _firebase_uygulamasi():
    try:
        import firebase_admin
    except ImportError as exc:
        raise RuntimeError("firebase-admin kurulu değil") from exc

    try:
        return firebase_admin.get_app()
    except ValueError:
        pass

    proje_id = os.getenv("FIREBASE_PROJECT_ID", "").strip()
    if not proje_id:
        raise RuntimeError("FIREBASE_PROJECT_ID tanımlı değil")

    servis_hesabi = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    if servis_hesabi:
        try:
            from firebase_admin import credentials

            kimlik = credentials.Certificate(json.loads(servis_hesabi))
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON geçerli JSON değil") from exc
        return firebase_admin.initialize_app(kimlik, options={"projectId": proje_id})

    return firebase_admin.initialize_app(options={"projectId": proje_id})


def _iptal_kontrolu_gerekli(app, ortam: str) -> bool:
    """Admin kimliği olmayan yerel ortamda yalnızca uzak iptal sorgusunu atlar."""
    if ortam == "production":
        return True
    try:
        app.credential.get_credential()
    except DefaultCredentialsError:
        logger.info("Yerel Firebase Admin kimliği yok; token iptal kontrolü atlanıyor.")
        return False
    return True


def _firebase_tokenini_dogrula(token: str, app, ortam: str) -> dict:
    """Firebase ID tokenını üretimde Admin Client, yerelde imza doğrulayıcıyla denetler."""
    iptal_kontrolu = _iptal_kontrolu_gerekli(app, ortam)
    if not iptal_kontrolu:
        # auth.verify_id_token(), check_revoked=False olsa bile Auth Client
        # kurulurken Admin kimliği ister. TokenVerifier ise Firebase'in resmi
        # sertifikalarıyla imza, issuer, audience ve süre denetimini yapar.
        from firebase_admin import _token_gen

        return _token_gen.TokenVerifier(app).verify_id_token(token)

    from firebase_admin import auth

    return auth.verify_id_token(token, app=app, check_revoked=True)


def mevcut_kullanici(authorization: str = Header(default="")) -> KimlikBilgisi:
    """Bearer Firebase ID token zorunludur; üretimde bypass desteklenmez."""
    ortam = os.getenv("APP_ENV", "development").lower()
    auth_devre_disi = os.getenv("KAZKAZ_AUTH_DISABLED", "false").lower() == "true"
    # Yerel bypass yalnızca istemci gerçek bir Firebase tokenı göndermediğinde
    # devreye girer. Aksi halde giriş yapmış kullanıcıyı yanlışlıkla demo tenant'a
    # dönüştürür ve kalıcı şirket oluşturma gibi işlemleri engeller.
    if auth_devre_disi and ortam != "production" and not authorization.startswith("Bearer "):
        return KimlikBilgisi(
            kullanici_id="yerel-gelistirici",
            eposta="developer@localhost",
            eposta_dogrulandi=True,
            sirket_id="yerel-demo",
            roller={"gelistirici": True},
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Geçerli bir oturum jetonu gerekli.",
        )

    token = authorization.removeprefix("Bearer ").strip()
    try:
        app = _firebase_uygulamasi()
        decoded = _firebase_tokenini_dogrula(token, app, ortam)
    except Exception as exc:
        if ortam != "production":
            logger.warning("Firebase token doğrulaması başarısız: %s: %s", type(exc).__name__, str(exc)[:300])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Oturum doğrulanamadı.",
        ) from exc

    roller = {k: bool(v) for k, v in decoded.items() if k in {"admin", "cfo", "analist", "viewer", "platform_admin"}}
    tekil_rol = str(decoded.get("role", "")).lower()
    rol_esleme = {"admin": "admin", "cfo": "cfo", "analyst": "analist", "analist": "analist", "viewer": "viewer"}
    if tekil_rol in rol_esleme:
        roller[rol_esleme[tekil_rol]] = True

    return KimlikBilgisi(
        kullanici_id=decoded["uid"],
        eposta=decoded.get("email"),
        eposta_dogrulandi=bool(decoded.get("email_verified", False)),
        sirket_id=decoded.get("company_id") or decoded.get("companyId"),
        roller=roller,
        plan=str(decoded.get("plan", "free")).lower(),
        deneme_bitis=date.fromisoformat(decoded["trial_ends_at"]) if decoded.get("trial_ends_at") else None,
        sirket_durumu=str(decoded.get("company_status", "active")).lower(),
    )


def sirket_uyeligini_dogrula(kullanici: KimlikBilgisi) -> KimlikBilgisi:
    """Üretim finans uçları için güvenilir token claim'lerini zorunlu kılar."""
    if kullanici.roller.get("gelistirici"):
        return kullanici
    if kullanici.sirket_durumu in {"suspended", "closed"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Şirket çalışma alanı sistem yöneticisi tarafından askıya alınmış veya kapatılmış.",
        )
    if not kullanici.sirket_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Şirket üyeliği gerekli.",
        )
    if not any(kullanici.roller.get(rol) for rol in {"admin", "cfo", "analist", "viewer"}):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için atanmış bir şirket rolü gerekli.",
        )
    return kullanici


def mevcut_sirket_uyesi(
    kullanici: KimlikBilgisi = Depends(mevcut_kullanici),
) -> KimlikBilgisi:
    return sirket_uyeligini_dogrula(kullanici)


def platform_yoneticisi(
    kullanici: KimlikBilgisi = Depends(mevcut_kullanici),
) -> KimlikBilgisi:
    """KazKaz platform yönetimini şirket admin rolünden kesin olarak ayırır."""
    ortam = os.getenv("APP_ENV", "development").lower()
    if ortam != "production" and (kullanici.roller.get("gelistirici") or kullanici.roller.get("admin")):
        return kullanici
    izinli_epostalar = {
        eposta.strip().lower()
        for eposta in os.getenv("PLATFORM_ADMIN_EMAILS", "").split(",")
        if eposta.strip()
    }
    eposta_izinli = bool(
        kullanici.eposta_dogrulandi
        and kullanici.eposta
        and kullanici.eposta.strip().lower() in izinli_epostalar
    )
    if not kullanici.roller.get("platform_admin") and not eposta_izinli:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="KazKaz sistem yönetimi yetkisi gerekli.",
        )
    return kullanici

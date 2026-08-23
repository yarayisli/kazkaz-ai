"""Şirket çalışma alanı oluşturma ve üyelik yetkilendirme servisi."""

from __future__ import annotations

from uuid import uuid4
from datetime import date, timedelta

from fastapi import HTTPException, status
from firebase_admin import auth as firebase_auth
from firebase_admin import firestore
from google.auth.exceptions import DefaultCredentialsError

from api.auth import _firebase_uygulamasi
from api.models import KimlikBilgisi, SirketOlusturmaIstegi


def _temiz_sirket_adi(ad: str) -> str:
    return " ".join(ad.split())


def _claimleri_guncelle(kullanici_id: str, sirket_id: str, rol: str, app, plan: str = "free", deneme_bitis: str | None = None, sirket_durumu: str | None = None) -> None:
    firebase_kullanici = firebase_auth.get_user(kullanici_id, app=app)
    claimler = dict(firebase_kullanici.custom_claims or {})
    claimler.update({"company_id": sirket_id, "role": rol, "plan": plan})
    if sirket_durumu:
        claimler["company_status"] = sirket_durumu
    if deneme_bitis:
        claimler["trial_ends_at"] = deneme_bitis
    firebase_auth.set_custom_user_claims(kullanici_id, claimler, app=app)


def sirket_olustur(
    istek: SirketOlusturmaIstegi,
    kullanici: KimlikBilgisi,
) -> dict:
    """Yeni şirketi oluşturur ve çağıran kullanıcıyı güvenli biçimde admin yapar.

    İşlem tekrarlandığında mevcut şirket üyeliğini onarır; kullanıcı ikinci bir
    şirket oluşturarak tenant sınırını aşamaz.
    """
    if kullanici.roller.get("gelistirici"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Yerel geliştirme hesabı için kalıcı şirket oluşturulmaz.",
        )

    try:
        app = _firebase_uygulamasi()
        app.credential.get_credential()
        db = firestore.client(app=app)
    except DefaultCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Girişiniz doğrulandı; ancak bu bilgisayar henüz kalıcı şirket kaydı için "
                "Firebase sunucu kimliğine bağlı değil. Firebase Admin kurulumu tamamlandıktan sonra tekrar deneyin."
            ),
        ) from exc
    kullanici_ref = db.collection("users").document(kullanici.kullanici_id)
    kullanici_belgesi = kullanici_ref.get()
    kullanici_verisi = kullanici_belgesi.to_dict() if kullanici_belgesi.exists else {}
    mevcut_sirket = kullanici.sirket_id or kullanici_verisi.get("companyId")
    zaman = firestore.SERVER_TIMESTAMP
    profil = {
        "sector": istek.sektor,
        "employeeScale": istek.calisan_olcegi,
        "primaryGoal": istek.ana_hedef,
        "primaryChallenge": istek.ana_zorluk,
        "dataSource": istek.veri_kaynagi,
        "availableData": sorted(set(istek.veri_kapsami)),
        "currency": istek.para_birimi,
        "fiscalYearStartMonth": istek.mali_yil_baslangic_ayi,
        "source": "self_reported_onboarding",
        "completedAt": zaman,
    }

    if mevcut_sirket:
        uye_ref = db.collection("companies").document(mevcut_sirket).collection("members").document(kullanici.kullanici_id)
        uye = uye_ref.get()
        rol = (uye.to_dict() or {}).get("role", "member") if uye.exists else "member"
        if rol not in {"admin", "cfo", "analyst", "viewer"}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Kullanıcı zaten bir şirkete bağlı; üyelik yöneticisiyle iletişime geçin.",
            )
        if rol not in {"admin", "cfo"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Şirket profilini yalnızca Admin veya CFO tamamlayabilir.",
            )
        batch = db.batch()
        batch.set(db.collection("companies").document(mevcut_sirket), {"profile": profil}, merge=True)
        batch.set(kullanici_ref, {"onboardingProfile": profil}, merge=True)
        batch.commit()
        plan = kullanici_verisi.get("plan", "free")
        _claimleri_guncelle(kullanici.kullanici_id, mevcut_sirket, rol, app, plan, kullanici_verisi.get("trialEndsAt"))
        return {
            "durum": "mevcut",
            "sirket_id": mevcut_sirket,
            "sirket_adi": kullanici_verisi.get("companyName", "Şirket"),
            "rol": rol,
            "token_yenile": True,
            "profil": {**profil, "completedAt": None},
        }

    sirket_adi = _temiz_sirket_adi(istek.sirket_adi)
    if len(sirket_adi) < 2:
        raise HTTPException(status_code=422, detail="Geçerli bir şirket adı girin.")

    sirket_id = f"cmp_{uuid4().hex[:20]}"
    sirket_ref = db.collection("companies").document(sirket_id)
    uye_ref = sirket_ref.collection("members").document(kullanici.kullanici_id)
    batch = db.batch()
    deneme_bitis = (date.today() + timedelta(days=14)).isoformat()
    batch.set(sirket_ref, {
        "name": sirket_adi,
        "status": "active",
        "createdBy": kullanici.kullanici_id,
        "createdAt": zaman,
        "plan": "trial",
        "trialEndsAt": deneme_bitis,
        "profile": profil,
    })
    batch.set(uye_ref, {
        "userId": kullanici.kullanici_id,
        "email": kullanici.eposta,
        "role": "admin",
        "plan": "trial",
        "trialEndsAt": deneme_bitis,
        "addedAt": zaman,
    })
    batch.set(kullanici_ref, {
        "uid": kullanici.kullanici_id,
        "email": kullanici.eposta,
        "companyId": sirket_id,
        "companyName": sirket_adi,
        "role": "admin",
        "plan": "trial",
        "trialEndsAt": deneme_bitis,
        "onboardingProfile": profil,
    }, merge=True)
    batch.commit()

    _claimleri_guncelle(kullanici.kullanici_id, sirket_id, "admin", app, "trial", deneme_bitis)
    return {
        "durum": "olusturuldu",
        "sirket_id": sirket_id,
        "sirket_adi": sirket_adi,
        "rol": "admin",
        "token_yenile": True,
        "plan": "trial",
        "deneme_bitis": deneme_bitis,
        "profil": {
            **profil,
            "completedAt": None,
        },
    }

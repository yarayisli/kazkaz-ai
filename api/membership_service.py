"""Şirket kullanıcı daveti ve rol yaşam döngüsü.

Tüm yazma işlemleri Firebase Admin üzerinden yapılır. İstemci yalnız kendi
profilini okuyabilir; şirket ve rol kimliği güvenilir token claim'lerine yazılır.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import HTTPException, status
from firebase_admin import auth as firebase_auth
from firebase_admin import firestore

from api.auth import _firebase_uygulamasi
from api.company_service import _claimleri_guncelle
from api.models import KimlikBilgisi, UyeCikarmaIstegi, UyeDavetIstegi, UyeRolGuncellemeIstegi


ROLLER = {"admin", "cfo", "analyst", "viewer"}


def _db():
    return firestore.client(app=_firebase_uygulamasi())


def _admin_ister(kullanici: KimlikBilgisi) -> None:
    if kullanici.roller.get("gelistirici"):
        raise HTTPException(status_code=409, detail="Yerel demo üyelik yönetimi kalıcı değildir.")
    if not kullanici.sirket_id or not kullanici.roller.get("admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Üyelik yönetimi yalnızca şirket Admin rolüne açıktır.")


def _eposta(eposta: str) -> str:
    sonuc = eposta.strip().lower()
    if "@" not in sonuc or sonuc.startswith("@") or sonuc.endswith("@"):
        raise HTTPException(status_code=422, detail="Geçerli bir e-posta adresi girin.")
    return sonuc


def _davet_id(eposta: str) -> str:
    return hashlib.sha256(eposta.encode("utf-8")).hexdigest()


def _audit(db, kullanici: KimlikBilgisi, aksiyon: str, hedef: str, ek: Dict[str, Any] | None = None) -> None:
    veri = {
        "action": aksiyon,
        "resource": f"members/{hedef}",
        "actorId": kullanici.kullanici_id,
        "actorRole": "admin",
        "companyId": kullanici.sirket_id,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "containsFinancialData": False,
    }
    if ek:
        veri.update(ek)
    db.collection("companies").document(str(kullanici.sirket_id)).collection("auditLogs").document().set(veri)


def uye_listesi(kullanici: KimlikBilgisi) -> Dict[str, Any]:
    _admin_ister(kullanici)
    db = _db()
    sirket = db.collection("companies").document(str(kullanici.sirket_id))
    uyeler = []
    for belge in sirket.collection("members").stream():
        veri = belge.to_dict() or {}
        uyeler.append({
            "kullanici_id": belge.id,
            "eposta": veri.get("email"),
            "rol": veri.get("role", "viewer"),
            "durum": "aktif",
            "eklenme": veri.get("addedAt"),
        })
    davetler = []
    simdi = datetime.now(timezone.utc)
    for belge in sirket.collection("invitations").stream():
        veri = belge.to_dict() or {}
        son = veri.get("expiresAt")
        if veri.get("status") != "pending" or (isinstance(son, datetime) and son < simdi):
            continue
        davetler.append({
            "davet_id": belge.id,
            "eposta": veri.get("email"),
            "rol": veri.get("role"),
            "durum": "bekliyor",
            "son_gecerlilik": son,
        })
    uyeler.sort(key=lambda item: ((item["rol"] != "admin"), item.get("eposta") or ""))
    davetler.sort(key=lambda item: item.get("eposta") or "")
    return {"uyeler": uyeler, "davetler": davetler}


def uye_davet_et(istek: UyeDavetIstegi, kullanici: KimlikBilgisi) -> Dict[str, Any]:
    _admin_ister(kullanici)
    eposta = _eposta(istek.eposta)
    db = _db()
    sirket = db.collection("companies").document(str(kullanici.sirket_id))
    davet_kimligi = _davet_id(eposta)
    davet_ref = sirket.collection("invitations").document(davet_kimligi)
    indeks_ref = db.collection("invitationIndex").document(davet_kimligi)
    davet_verisi = {
        "email": eposta,
        "role": istek.rol,
        "status": "pending",
        "companyId": kullanici.sirket_id,
        "invitedBy": kullanici.kullanici_id,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "expiresAt": datetime.now(timezone.utc) + timedelta(days=7),
    }
    batch = db.batch()
    batch.set(davet_ref, davet_verisi)
    batch.set(indeks_ref, {"companyId": kullanici.sirket_id, "email": eposta, "status": "pending", "expiresAt": davet_verisi["expiresAt"]})
    batch.commit()
    _audit(db, kullanici, "member.invite", davet_kimligi, {"targetRole": istek.rol})
    return {"durum": "davet_olusturuldu", "eposta": eposta, "rol": istek.rol, "gecerlilik_gunu": 7}


def daveti_kabul_et(kullanici: KimlikBilgisi) -> Dict[str, Any]:
    if kullanici.sirket_id:
        raise HTTPException(status_code=409, detail="Kullanıcı zaten bir şirkete bağlı.")
    if not kullanici.eposta or not kullanici.eposta_dogrulandi:
        raise HTTPException(status_code=403, detail="Davet kabulü için doğrulanmış e-posta adresi gerekir.")
    eposta = _eposta(kullanici.eposta)
    db = _db()
    davet_kimligi = _davet_id(eposta)
    indeks_ref = db.collection("invitationIndex").document(davet_kimligi)
    indeks_belgesi = indeks_ref.get()
    indeks = indeks_belgesi.to_dict() if indeks_belgesi.exists else None
    if not indeks or indeks.get("status") != "pending" or indeks.get("email") != eposta:
        raise HTTPException(status_code=404, detail="Bu e-posta için geçerli şirket daveti bulunamadı.")
    sirket_ref = db.collection("companies").document(str(indeks.get("companyId")))
    sirket_belgesi = sirket_ref.get()
    davet_ref = sirket_ref.collection("invitations").document(davet_kimligi)
    davet_belgesi = davet_ref.get()
    davet = davet_belgesi.to_dict() if davet_belgesi.exists else None
    if not sirket_belgesi.exists or not davet or davet.get("status") != "pending" or davet.get("email") != eposta:
        raise HTTPException(status_code=404, detail="Şirket daveti doğrulanamadı.")
    son = davet.get("expiresAt")
    if isinstance(son, datetime) and son < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Şirket davetinin süresi dolmuş.")
    rol = davet.get("role")
    if rol not in ROLLER - {"admin"}:
        raise HTTPException(status_code=422, detail="Davet rolü geçersiz.")
    sirket_id = str(indeks.get("companyId"))
    sirket_verisi = sirket_belgesi.to_dict() or {}
    uye_ref = sirket_ref.collection("members").document(kullanici.kullanici_id)
    kullanici_ref = db.collection("users").document(kullanici.kullanici_id)
    batch = db.batch()
    batch.set(uye_ref, {"userId": kullanici.kullanici_id, "email": eposta, "role": rol, "addedAt": firestore.SERVER_TIMESTAMP})
    batch.set(kullanici_ref, {"companyId": sirket_id, "companyName": sirket_verisi.get("name", "Şirket"), "role": rol}, merge=True)
    batch.set(davet_ref, {"status": "accepted", "acceptedBy": kullanici.kullanici_id, "acceptedAt": firestore.SERVER_TIMESTAMP}, merge=True)
    batch.set(indeks_ref, {"status": "accepted", "acceptedBy": kullanici.kullanici_id, "acceptedAt": firestore.SERVER_TIMESTAMP}, merge=True)
    batch.commit()
    app = _firebase_uygulamasi()
    _claimleri_guncelle(kullanici.kullanici_id, sirket_id, rol, app, sirket_verisi.get("plan", "free"), sirket_verisi.get("trialEndsAt"))
    return {"durum": "kabul_edildi", "sirket_id": sirket_id, "rol": rol, "token_yenile": True}


def uye_rolunu_guncelle(istek: UyeRolGuncellemeIstegi, kullanici: KimlikBilgisi) -> Dict[str, Any]:
    _admin_ister(kullanici)
    if istek.kullanici_id == kullanici.kullanici_id:
        raise HTTPException(status_code=409, detail="Kendi rolünüzü bu ekrandan değiştiremezsiniz.")
    db = _db()
    sirket = db.collection("companies").document(str(kullanici.sirket_id))
    uye_ref = sirket.collection("members").document(istek.kullanici_id)
    uye = uye_ref.get()
    if not uye.exists:
        raise HTTPException(status_code=404, detail="Şirket üyesi bulunamadı.")
    uye_verisi = uye.to_dict() or {}
    batch = db.batch()
    batch.set(uye_ref, {"role": istek.rol, "updatedAt": firestore.SERVER_TIMESTAMP, "updatedBy": kullanici.kullanici_id}, merge=True)
    batch.set(db.collection("users").document(istek.kullanici_id), {"role": istek.rol}, merge=True)
    sirket_verisi = sirket.get().to_dict() or {}
    app = _firebase_uygulamasi()
    # Özellikle rol düşürmede eski yetkileri taşıyan refresh tokenları geçersiz
    # kıl; backend her korumalı istekte check_revoked=True kullanır.
    firebase_auth.revoke_refresh_tokens(istek.kullanici_id, app=app)
    plan = sirket_verisi.get("plan", uye_verisi.get("plan", "free"))
    deneme = sirket_verisi.get("trialEndsAt")
    _claimleri_guncelle(istek.kullanici_id, str(kullanici.sirket_id), istek.rol, app, plan, deneme)
    try:
        batch.commit()
    except Exception as exc:
        # Firebase Auth ve Firestore tek atomik işlem sunmadığı için Firestore
        # yazımı başarısızsa claim'i eski güvenli role geri al.
        _claimleri_guncelle(
            istek.kullanici_id, str(kullanici.sirket_id), uye_verisi.get("role", "viewer"),
            app, plan, deneme,
        )
        firebase_auth.revoke_refresh_tokens(istek.kullanici_id, app=app)
        raise HTTPException(status_code=503, detail="Rol değişikliği tamamlanamadı; önceki rol korundu.") from exc
    _audit(db, kullanici, "member.role_update", istek.kullanici_id, {"targetRole": istek.rol})
    return {"durum": "rol_guncellendi", "kullanici_id": istek.kullanici_id, "rol": istek.rol, "token_yenile": True}


def uye_cikar(istek: UyeCikarmaIstegi, kullanici: KimlikBilgisi) -> Dict[str, Any]:
    _admin_ister(kullanici)
    if istek.kullanici_id == kullanici.kullanici_id:
        raise HTTPException(status_code=409, detail="Kendi üyeliğinizi bu ekrandan kaldıramazsınız.")
    db = _db()
    sirket = db.collection("companies").document(str(kullanici.sirket_id))
    uye_ref = sirket.collection("members").document(istek.kullanici_id)
    if not uye_ref.get().exists:
        raise HTTPException(status_code=404, detail="Şirket üyesi bulunamadı.")
    app = _firebase_uygulamasi()
    firebase_kullanici = firebase_auth.get_user(istek.kullanici_id, app=app)
    claimler = dict(firebase_kullanici.custom_claims or {})
    for anahtar in ("company_id", "companyId", "role", "admin", "cfo", "analist", "viewer"):
        claimler.pop(anahtar, None)
    firebase_auth.revoke_refresh_tokens(istek.kullanici_id, app=app)
    firebase_auth.set_custom_user_claims(istek.kullanici_id, claimler, app=app)
    batch = db.batch()
    batch.delete(uye_ref)
    batch.set(db.collection("users").document(istek.kullanici_id), {"companyId": None, "companyName": "Şirket üyeliği bekleniyor", "role": "member"}, merge=True)
    batch.commit()
    _audit(db, kullanici, "member.remove", istek.kullanici_id)
    return {"durum": "uye_cikarildi", "kullanici_id": istek.kullanici_id, "token_yenile": True}

"""Şirket çalışma alanı için sunucu taraflı saklama, dışa aktarma ve silme.

İstemci Firestore'a doğrudan finans verisi yazmaz. Şirket kimliği doğrulanmış
Firebase token claim'inden alınır; her veri yaşam döngüsü işlemi auditLogs
altında içeriksiz bir denetim kaydı bırakır.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable

from fastapi import HTTPException, status
from firebase_admin import firestore

from api.auth import _firebase_uygulamasi
from api.models import CalismaAlaniKaydetIstegi, KimlikBilgisi


ZORUNLU_SNAPSHOT_ALANLARI = {
    "financialData",
    "cashFlow",
    "debts",
    "customers",
    "budget",
    "financialAudit",
    "isSampleData",
}


def _rol_ister(kullanici: KimlikBilgisi, izinli: Iterable[str]) -> None:
    if kullanici.roller.get("gelistirici"):
        raise HTTPException(status_code=409, detail="Yerel demo için kalıcı bulut işlemi yapılmaz.")
    if not any(kullanici.roller.get(rol) for rol in izinli):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu veri işlemi için yetkiniz yok.")


def _db():
    return firestore.client(app=_firebase_uygulamasi())


def _referanslar(db, sirket_id: str):
    sirket = db.collection("companies").document(sirket_id)
    return sirket.collection("workspaces").document("current"), sirket.collection("auditLogs").document()


def _audit(aksiyon: str, kullanici: KimlikBilgisi) -> Dict[str, Any]:
    return {
        "action": aksiyon,
        "resource": "workspace/current",
        "actorId": kullanici.kullanici_id,
        "actorRole": next((rol for rol, aktif in kullanici.roller.items() if aktif), "unknown"),
        "companyId": kullanici.sirket_id,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "containsFinancialData": False,
    }


def _snapshot_dogrula(snapshot: Dict[str, Any]) -> bytes:
    eksikler = sorted(ZORUNLU_SNAPSHOT_ALANLARI - set(snapshot))
    if eksikler:
        raise HTTPException(status_code=422, detail="Çalışma alanı eksik: " + ", ".join(eksikler))
    try:
        kodlanmis = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="Çalışma alanı JSON biçimine dönüştürülemedi.") from exc
    limit = max(50_000, int(os.getenv("MAX_WORKSPACE_BYTES", "750000")))
    if len(kodlanmis) > limit:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Çalışma alanı en fazla {limit} bayt olabilir.",
        )
    return kodlanmis


def calisma_alani_kaydet(istek: CalismaAlaniKaydetIstegi, kullanici: KimlikBilgisi) -> Dict[str, Any]:
    _rol_ister(kullanici, {"admin", "cfo", "analist"})
    kodlanmis = _snapshot_dogrula(istek.snapshot)
    db = _db()
    workspace_ref, audit_ref = _referanslar(db, str(kullanici.sirket_id))
    saklama_gunu = max(1, int(os.getenv("DATA_RETENTION_DAYS", "365")))
    batch = db.batch()
    batch.set(workspace_ref, {
        "schemaVersion": 2,
        "companyId": kullanici.sirket_id,
        "snapshot": istek.snapshot,
        "updatedBy": kullanici.kullanici_id,
        "updatedAt": firestore.SERVER_TIMESTAMP,
        "retentionUntil": datetime.now(timezone.utc) + timedelta(days=saklama_gunu),
        "dataClassification": "confidential-financial",
    })
    batch.set(audit_ref, _audit("workspace.save", kullanici))
    batch.commit()
    return {"durum": "kaydedildi", "schema_version": 2, "boyut": len(kodlanmis), "saklama_gunu": saklama_gunu}


def calisma_alani_yukle(kullanici: KimlikBilgisi) -> Dict[str, Any]:
    _rol_ister(kullanici, {"admin", "cfo", "analist", "viewer"})
    db = _db()
    workspace_ref, audit_ref = _referanslar(db, str(kullanici.sirket_id))
    belge = workspace_ref.get()
    if not belge.exists:
        return {"durum": "bos", "snapshot": None}
    veri = belge.to_dict() or {}
    snapshot = veri.get("snapshot")
    if snapshot is None:  # Eski düz schemaVersion 1/2 kayıtlarını güvenli biçimde okuyup taşıyabilmek için.
        snapshot = {k: v for k, v in veri.items() if k not in {
            "schemaVersion", "companyId", "updatedBy", "updatedAt", "retentionUntil", "dataClassification"
        }}
    db.batch().set(audit_ref, _audit("workspace.read", kullanici)).commit()
    return {"durum": "hazir", "schema_version": veri.get("schemaVersion", 1), "snapshot": snapshot}


def calisma_alani_sil(kullanici: KimlikBilgisi) -> Dict[str, Any]:
    _rol_ister(kullanici, {"admin", "cfo"})
    db = _db()
    workspace_ref, audit_ref = _referanslar(db, str(kullanici.sirket_id))
    batch = db.batch()
    batch.delete(workspace_ref)
    batch.set(audit_ref, _audit("workspace.delete", kullanici))
    batch.commit()
    return {"durum": "silindi", "kapsam": "workspace/current"}


def calisma_alani_disa_aktar(kullanici: KimlikBilgisi) -> bytes:
    sonuc = calisma_alani_yukle(kullanici)
    if sonuc["snapshot"] is None:
        raise HTTPException(status_code=404, detail="Dışa aktarılacak çalışma alanı bulunamadı.")
    db = _db()
    _, audit_ref = _referanslar(db, str(kullanici.sirket_id))
    audit_ref.set(_audit("workspace.export", kullanici))
    paket = {
        "exportVersion": 1,
        "exportedAt": datetime.now(timezone.utc).isoformat(),
        "companyId": kullanici.sirket_id,
        "workspace": sonuc["snapshot"],
    }
    return json.dumps(paket, ensure_ascii=False, indent=2).encode("utf-8")

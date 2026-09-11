"""Şirket kapsamlı, özgün çıktıyı değişmez saklayan rapor arşivi."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import os
from typing import Any, Dict, Iterable
from uuid import uuid4

from fastapi import HTTPException, status
from firebase_admin import firestore, storage

from api.auth import _firebase_uygulamasi
from api.models import FinansalGorunum, KimlikBilgisi
from api.report_engine import RAPOR_MOTOR_SURUMU, excel_raporu_olustur, pdf_raporu_olustur


def _db():
    return firestore.client(app=_firebase_uygulamasi())


def _bucket():
    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET", "").strip()
    if not bucket_name:
        raise HTTPException(
            status_code=503,
            detail="Değişmez rapor arşivi için FIREBASE_STORAGE_BUCKET yapılandırılmamış.",
        )
    try:
        return storage.bucket(bucket_name, app=_firebase_uygulamasi())
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Rapor arşiv deposuna erişilemiyor.") from exc


def _rol_ister(kullanici: KimlikBilgisi, roller: Iterable[str]) -> None:
    if kullanici.roller.get("gelistirici"):
        raise HTTPException(status_code=409, detail="Yerel demo için kalıcı rapor arşivi oluşturulmaz.")
    if not kullanici.sirket_id or not any(kullanici.roller.get(rol) for rol in roller):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu rapor işlemi için yetkiniz yok.")


def _refs(db, company_id: str, report_id: str | None = None):
    company = db.collection("companies").document(company_id)
    reports = company.collection("reports")
    return company, reports.document(report_id) if report_id else reports


def _audit(db, user: KimlikBilgisi, action: str, report_id: str) -> None:
    db.collection("companies").document(str(user.sirket_id)).collection("auditLogs").document().set({
        "action": action,
        "resource": f"reports/{report_id}",
        "actorId": user.kullanici_id,
        "companyId": user.sirket_id,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "containsFinancialData": False,
    })


def _summary(data: FinansalGorunum) -> Dict[str, float | None]:
    return {
        "revenue": data.ciro,
        "netProfit": data.net_kar,
        "cash": data.nakit,
        "totalDebt": data.kisa_vadeli_borc + data.uzun_vadeli_borc,
        "equity": data.ozkaynak,
        "netMargin": round(data.net_kar / data.ciro * 100, 4) if data.ciro else None,
        "currentRatio": round(data.donen_varliklar / data.kisa_vadeli_borc, 4)
        if data.donen_varliklar is not None and data.kisa_vadeli_borc > 0 else None,
    }


def _rapor_icerigi(data: FinansalGorunum, format_name: str) -> bytes:
    return pdf_raporu_olustur(data) if format_name == "pdf" else excel_raporu_olustur(data)


def _saklama_suresi() -> int:
    try:
        gun = int(os.getenv("REPORT_RETENTION_DAYS", os.getenv("DATA_RETENTION_DAYS", "365")))
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="Rapor saklama süresi geçersiz yapılandırılmış.") from exc
    if not 1 <= gun <= 3650:
        raise HTTPException(status_code=503, detail="Rapor saklama süresi 1-3650 gün arasında olmalı.")
    return gun


def _artifact_yolu(artifact: Dict[str, Any], company_id: str, report_id: str) -> str:
    path = artifact.get("storagePath")
    expected_prefix = f"companies/{company_id}/reports/{report_id}/"
    if not isinstance(path, str) or not path.startswith(expected_prefix) or "/../" in f"/{path}/":
        raise HTTPException(status_code=500, detail="Arşiv raporu depo kapsamı doğrulanamadı.")
    return path


def rapor_arsivle(
    data: FinansalGorunum,
    user: KimlikBilgisi,
    format_name: str,
    content: bytes | None = None,
) -> str:
    _rol_ister(user, {"admin", "cfo", "analist", "viewer"})
    if format_name not in {"pdf", "excel"}:
        raise HTTPException(status_code=422, detail="Rapor formatı geçersiz.")
    db = _db()
    bucket = _bucket()
    report_id = f"rpt_{uuid4().hex[:20]}"
    _, report_ref = _refs(db, str(user.sirket_id), report_id)
    now = datetime.now(timezone.utc)
    retention_days = _saklama_suresi()
    original = content if content is not None else _rapor_icerigi(data, format_name)
    if not original:
        raise HTTPException(status_code=500, detail="Rapor çıktısı boş üretildi; arşivlenmedi.")
    extension = "pdf" if format_name == "pdf" else "xlsx"
    content_type = "application/pdf" if format_name == "pdf" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    storage_path = f"companies/{user.sirket_id}/reports/{report_id}/original.{extension}"
    digest = hashlib.sha256(original).hexdigest()
    retention_until = now + timedelta(days=retention_days)
    blob = bucket.blob(storage_path)
    blob.metadata = {
        "companyId": str(user.sirket_id),
        "reportId": report_id,
        "engineVersion": RAPOR_MOTOR_SURUMU,
        "sha256": digest,
        "retentionUntil": retention_until.isoformat(),
    }
    try:
        # UUID yoluna rağmen oluşturma önkoşulu kullanılır; var olan nesne hiçbir
        # koşulda sessizce ezilemez.
        blob.upload_from_string(original, content_type=content_type, if_generation_match=0)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Özgün rapor çıktısı arşiv deposuna yazılamadı.") from exc
    belge = {
        "reportId": report_id,
        "companyId": user.sirket_id,
        "companyName": data.sirket_adi,
        "period": data.donem,
        "currency": data.para_birimi,
        "version": now.strftime("%Y%m%d-%H%M%S"),
        "engineVersion": RAPOR_MOTOR_SURUMU,
        "formats": [format_name],
        "immutableOutput": True,
        "artifacts": {
            format_name: {
                "storagePath": storage_path,
                "sha256": digest,
                "size": len(original),
                "contentType": content_type,
            },
        },
        "financialData": data.model_dump(mode="json"),
        "summary": _summary(data),
        "createdBy": user.kullanici_id,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "retentionUntil": retention_until,
        "dataClassification": "confidential-financial",
    }
    try:
        report_ref.set(belge)
    except Exception as exc:
        try:
            blob.delete()
        except Exception:
            pass
        raise HTTPException(status_code=503, detail="Rapor arşiv kaydı tamamlanamadı.") from exc
    _audit(db, user, "report.archive", report_id)
    return report_id


def rapor_listesi(user: KimlikBilgisi) -> Dict[str, Any]:
    _rol_ister(user, {"admin", "cfo", "analist", "viewer"})
    db = _db()
    _, reports = _refs(db, str(user.sirket_id))
    rows = []
    for document in reports.stream():
        data = document.to_dict() or {}
        rows.append({
            "rapor_id": document.id,
            "sirket_adi": data.get("companyName"),
            "donem": data.get("period"),
            "para_birimi": data.get("currency", "TRY"),
            "surum": data.get("version"),
            "motor_surumu": data.get("engineVersion", "bilinmiyor"),
            # Bu bilgi karşılaştırma içindir. Yeni kayıtlarda motor değişse bile
            # indirme özgün baytları döndürür; yalnız eski kayıtlar tekrar üretilir.
            "guncel_motor": data.get("engineVersion") == RAPOR_MOTOR_SURUMU,
            "ozgun_cikti": bool(data.get("immutableOutput") and data.get("artifacts")),
            "formatlar": data.get("formats", []),
            "ozet": data.get("summary", {}),
            "olusturan": data.get("createdBy"),
            "olusturma": data.get("createdAt"),
        })
    rows.sort(key=lambda row: str(row.get("surum") or ""), reverse=True)
    return {"raporlar": rows[:50]}


def arsiv_raporu_olustur(report_id: str, format_name: str, user: KimlikBilgisi) -> tuple[bytes, Dict[str, Any]]:
    """Yeni kayıtta özgün baytları döndürür; eski kaydı uyumluluk için yeniden üretir."""
    _rol_ister(user, {"admin", "cfo", "analist", "viewer"})
    if format_name not in {"pdf", "excel"}:
        raise HTTPException(status_code=422, detail="Rapor formatı geçersiz.")
    db = _db()
    _, report_ref = _refs(db, str(user.sirket_id), report_id)
    document = report_ref.get()
    if not document.exists:
        raise HTTPException(status_code=404, detail="Rapor arşiv kaydı bulunamadı.")
    stored = document.to_dict() or {}
    if stored.get("companyId") != user.sirket_id:
        raise HTTPException(status_code=403, detail="Rapor şirket kapsamıyla eşleşmiyor.")
    arsiv_surum = str(stored.get("engineVersion") or "bilinmiyor")
    artifact = (stored.get("artifacts") or {}).get(format_name)
    if artifact:
        if not isinstance(artifact, dict):
            raise HTTPException(status_code=500, detail="Arşiv raporu dosya kaydı geçersiz.")
        storage_path = _artifact_yolu(artifact, str(user.sirket_id), report_id)
        try:
            content = _bucket().blob(storage_path).download_as_bytes()
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Özgün rapor çıktısı arşiv deposundan okunamadı.") from exc
        try:
            kayitli_boyut = int(artifact.get("size", -1))
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=500, detail="Arşiv raporu bütünlük kaydı geçersiz.") from exc
        gercek_hash = hashlib.sha256(content).hexdigest()
        if len(content) != kayitli_boyut or gercek_hash != artifact.get("sha256"):
            raise HTTPException(status_code=500, detail="Arşiv raporu bütünlük kontrolünden geçmedi.")
        _audit(db, user, "report.download", report_id)
        return content, {
            "motor_surumu_arsiv": arsiv_surum,
            "motor_surumu_guncel": RAPOR_MOTOR_SURUMU,
            "yeniden_uretildi": False,
            "ozgun_cikti": True,
        }
    if format_name not in stored.get("formats", []):
        raise HTTPException(status_code=404, detail="İstenen rapor formatı arşiv kaydında bulunamadı.")
    try:
        data = FinansalGorunum.model_validate(stored.get("financialData") or {})
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Arşiv raporu veri sözleşmesiyle uyumsuz.") from exc
    yeniden_uretildi = arsiv_surum != RAPOR_MOTOR_SURUMU
    _audit(db, user, "report.download", report_id)
    icerik = _rapor_icerigi(data, format_name)
    return icerik, {
        "motor_surumu_arsiv": arsiv_surum,
        "motor_surumu_guncel": RAPOR_MOTOR_SURUMU,
        "yeniden_uretildi": yeniden_uretildi,
        "ozgun_cikti": False,
    }


def arsiv_raporu_sil(report_id: str, user: KimlikBilgisi) -> Dict[str, str]:
    _rol_ister(user, {"admin", "cfo"})
    db = _db()
    _, report_ref = _refs(db, str(user.sirket_id), report_id)
    document = report_ref.get()
    if not document.exists:
        raise HTTPException(status_code=404, detail="Rapor arşiv kaydı bulunamadı.")
    stored = document.to_dict() or {}
    for artifact in (stored.get("artifacts") or {}).values():
        if not isinstance(artifact, dict):
            raise HTTPException(status_code=500, detail="Arşiv raporu dosya kaydı geçersiz.")
        storage_path = _artifact_yolu(artifact, str(user.sirket_id), report_id)
        try:
            blob = _bucket().blob(str(storage_path))
            if blob.exists():
                blob.delete()
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Rapor dosyası silinemedi; arşiv kaydı korundu.") from exc
    report_ref.delete()
    _audit(db, user, "report.delete", report_id)
    return {"durum": "silindi", "rapor_id": report_id}

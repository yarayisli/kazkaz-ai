"""Şirket kapsamlı sürümlü rapor arşivi.

Üretilen dosya yerine doğrulanmış finans girdisi ve özet metrikler saklanır.
Yeniden indirmede rapor deterministik motorla tekrar üretilir; böylece ikili
dosya kopyaları ve Firestore belge boyutu büyümez.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from typing import Any, Dict, Iterable
from uuid import uuid4

from fastapi import HTTPException, status
from firebase_admin import firestore

from api.auth import _firebase_uygulamasi
from api.models import FinansalGorunum, KimlikBilgisi
from api.report_engine import excel_raporu_olustur, pdf_raporu_olustur


def _db():
    return firestore.client(app=_firebase_uygulamasi())


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


def rapor_arsivle(data: FinansalGorunum, user: KimlikBilgisi, format_name: str) -> str:
    _rol_ister(user, {"admin", "cfo", "analist", "viewer"})
    if format_name not in {"pdf", "excel"}:
        raise HTTPException(status_code=422, detail="Rapor formatı geçersiz.")
    db = _db()
    report_id = f"rpt_{uuid4().hex[:20]}"
    _, report_ref = _refs(db, str(user.sirket_id), report_id)
    now = datetime.now(timezone.utc)
    retention_days = max(1, int(os.getenv("REPORT_RETENTION_DAYS", os.getenv("DATA_RETENTION_DAYS", "365"))))
    report_ref.set({
        "reportId": report_id,
        "companyId": user.sirket_id,
        "companyName": data.sirket_adi,
        "period": data.donem,
        "currency": data.para_birimi,
        "version": now.strftime("%Y%m%d-%H%M%S"),
        "formats": [format_name],
        "financialData": data.model_dump(mode="json"),
        "summary": _summary(data),
        "createdBy": user.kullanici_id,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "retentionUntil": now + timedelta(days=retention_days),
        "dataClassification": "confidential-financial",
    })
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
            "formatlar": data.get("formats", []),
            "ozet": data.get("summary", {}),
            "olusturan": data.get("createdBy"),
            "olusturma": data.get("createdAt"),
        })
    rows.sort(key=lambda row: str(row.get("surum") or ""), reverse=True)
    return {"raporlar": rows[:50]}


def arsiv_raporu_olustur(report_id: str, format_name: str, user: KimlikBilgisi) -> bytes:
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
    try:
        data = FinansalGorunum.model_validate(stored.get("financialData") or {})
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Arşiv raporu veri sözleşmesiyle uyumsuz.") from exc
    _audit(db, user, "report.download", report_id)
    return pdf_raporu_olustur(data) if format_name == "pdf" else excel_raporu_olustur(data)


def arsiv_raporu_sil(report_id: str, user: KimlikBilgisi) -> Dict[str, str]:
    _rol_ister(user, {"admin", "cfo"})
    db = _db()
    _, report_ref = _refs(db, str(user.sirket_id), report_id)
    if not report_ref.get().exists:
        raise HTTPException(status_code=404, detail="Rapor arşiv kaydı bulunamadı.")
    report_ref.delete()
    _audit(db, user, "report.delete", report_id)
    return {"durum": "silindi", "rapor_id": report_id}

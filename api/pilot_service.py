"""Dört haftalık pilot için finansal içerik taşımayan ürün kanıtı."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import math
import os
from statistics import median
from typing import Any

from fastapi import HTTPException
from firebase_admin import firestore

from api.auth import _firebase_uygulamasi
from api.models import KimlikBilgisi, PilotNiyetIstegi


PILOT_GOREVLERI = {
    "veri_dogrulama": lambda action: action == "data.file_validated",
    "calisma_alani_kaydi": lambda action: action == "workspace.save",
    "finansal_analiz": lambda action: action.startswith("analysis."),
    "rapor_uretimi": lambda action: action == "report.archive",
}


def _db():
    return firestore.client(app=_firebase_uygulamasi())


def _datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    return None


def pilot_olcumlerini_hesapla(rows: list[dict[str, Any]], now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    total_checkpoints = 0
    full_journeys = 0
    completed_full_journeys = 0
    finished_windows = 0
    resolved_minutes: list[float] = []
    feedback_total = 0
    error_feedback = 0
    satisfaction: list[bool] = []
    continuation: list[bool] = []
    paid_continuation: list[bool] = []

    for row in rows:
        start = _datetime(row.get("startedAt"))
        window_end = min(now, start + timedelta(days=28)) if start else None
        window_finished = bool(start and now >= start + timedelta(days=28))
        if window_finished:
            finished_windows += 1
        def in_window(item: dict[str, Any]) -> bool:
            created = _datetime(item.get("createdAt"))
            return bool(start and window_end and created and start <= created <= window_end)

        actions = {
            str(item.get("action") or "") for item in row.get("audits", []) if in_window(item)
        }
        completed = sum(1 for matcher in PILOT_GOREVLERI.values() if any(matcher(action) for action in actions))
        total_checkpoints += completed
        full_journeys += int(completed == len(PILOT_GOREVLERI))
        completed_full_journeys += int(window_finished and completed == len(PILOT_GOREVLERI))
        for feedback in (item for item in row.get("feedback", []) if in_window(item)):
            feedback_total += 1
            error_feedback += int(feedback.get("category") == "hata")
            sat = feedback.get("satisfaction")
            if isinstance(sat, dict) and isinstance(sat.get("satisfied"), bool):
                satisfaction.append(sat["satisfied"])
            if feedback.get("status") == "resolved":
                created = _datetime(feedback.get("createdAt"))
                resolved = _datetime(feedback.get("updatedAt") or feedback.get("respondedAt"))
                if created and resolved and resolved >= created:
                    resolved_minutes.append((resolved - created).total_seconds() / 60)
        survey = row.get("survey") if isinstance(row.get("survey"), dict) else None
        survey_time = _datetime(survey.get("respondedAt")) if survey else None
        if survey and start and window_end and survey_time and start <= survey_time <= window_end:
            intent = survey.get("continuationIntent")
            if intent in {"kesinlikle", "muhtemelen", "kararsiz", "muhtemelen_hayir", "kesinlikle_hayir"}:
                continuation.append(intent in {"kesinlikle", "muhtemelen"})
            if isinstance(survey.get("paidContinuation"), bool):
                paid_continuation.append(survey["paidContinuation"])

    company_count = len(rows)
    checkpoint_denominator = company_count * len(PILOT_GOREVLERI)
    resolved_sorted = sorted(resolved_minutes)
    p90_index = max(0, math.ceil(len(resolved_sorted) * 0.9) - 1) if resolved_sorted else 0
    percentage = lambda yes, total: round(yes / total * 100, 1) if total else None
    return {
        "durum": "olculuyor" if company_count else "pilot_yok",
        "hedef_sirket_araligi": "3-5",
        "pilot_sirket": company_count,
        "kapsam_gecerli": 3 <= company_count <= 5,
        "dort_haftayi_tamamlayan": finished_windows,
        "gorev_tamamlama": {
            "tam_yolculuk_sirket": full_journeys,
            "tamamlanmis_tam_yolculuk_sirket": completed_full_journeys,
            "kontrol_noktasi": total_checkpoints,
            "kontrol_noktasi_toplami": checkpoint_denominator,
            "oran_yuzde": percentage(total_checkpoints, checkpoint_denominator),
        },
        "destek": {
            "talep": feedback_total,
            "cozulen_sure_ornegi": len(resolved_minutes),
            "medyan_cozum_dakika": round(median(resolved_minutes), 1) if resolved_minutes else None,
            "p90_cozum_dakika": round(resolved_sorted[p90_index], 1) if resolved_sorted else None,
            "memnuniyet_yanit": len(satisfaction),
            "memnuniyet_yuzde": percentage(sum(satisfaction), len(satisfaction)),
        },
        "bildirilen_hata": {
            "adet": error_feedback,
            "tamamlanan_100_kontrol_noktasi_basina": (
                round(error_feedback / total_checkpoints * 100, 1) if total_checkpoints else None
            ),
            "tanim": "Müşteri tarafından hata kategorisinde açılan talep; teknik 5xx oranı değildir.",
        },
        "devam_niyeti": {
            "yanit": len(continuation),
            "olumlu_yuzde": percentage(sum(continuation), len(continuation)),
            "ucretli_devam_yanit": len(paid_continuation),
            "ucretli_devam_yuzde": percentage(sum(paid_continuation), len(paid_continuation)),
        },
        "finansal_veri_gosterilir": False,
        "asgari_kanit_hazir": (
            3 <= company_count <= 5
            and finished_windows >= 3
            and completed_full_journeys >= 3
            and len(continuation) >= 3
            and len(paid_continuation) >= 3
        ),
    }


def platform_pilot_ozeti() -> dict[str, Any]:
    try:
        db = _db()
        rows = []
        for company in db.collection("companies").where("status", "==", "pilot").limit(6).stream():
            data = company.to_dict() or {}
            start = _datetime(data.get("pilotStartedAt"))
            end = min(datetime.now(timezone.utc), start + timedelta(days=28)) if start else None

            def pilot_documents(collection_name: str, limit: int) -> list[dict[str, Any]]:
                if not start or not end:
                    return []
                query = company.reference.collection(collection_name)
                query = query.where("createdAt", ">=", start).where("createdAt", "<=", end)
                return [doc.to_dict() or {} for doc in query.order_by("createdAt").limit(limit).stream()]

            rows.append({
                "startedAt": start,
                "audits": pilot_documents("auditLogs", 500),
                "feedback": pilot_documents("feedback", 200),
                "survey": (company.reference.collection("pilotSurveys").document("current").get().to_dict() or {}),
            })
        return pilot_olcumlerini_hesapla(rows)
    except Exception:
        return {**pilot_olcumlerini_hesapla([]), "durum": "veri_kaynagi_kullanilamiyor"}


def pilot_niyet_durumu(user: KimlikBilgisi) -> dict[str, Any]:
    company = _db().collection("companies").document(str(user.sirket_id)).get()
    data = company.to_dict() or {}
    if not company.exists or str(data.get("status")) != "pilot":
        return {"uygun": False, "yanitlandi": False}
    start = _datetime(data.get("pilotStartedAt"))
    try:
        min_days = int(os.getenv("PILOT_SURVEY_MIN_DAYS", "21"))
    except ValueError:
        min_days = 21
    min_days = min(28, max(0, min_days))
    is_manager = any(user.roller.get(role) for role in {"admin", "cfo"})
    eligible = bool(is_manager and start and datetime.now(timezone.utc) >= start + timedelta(days=min_days))
    survey = company.reference.collection("pilotSurveys").document("current").get()
    return {"uygun": eligible, "yanitlandi": survey.exists, "asgari_gun": min_days}


def pilot_niyet_kaydet(request: PilotNiyetIstegi, user: KimlikBilgisi) -> dict[str, Any]:
    if not any(user.roller.get(role) for role in {"admin", "cfo"}):
        raise HTTPException(status_code=403, detail="Pilot değerlendirmesini şirket yöneticisi yanıtlayabilir.")
    db = _db()
    company_ref = db.collection("companies").document(str(user.sirket_id))
    company = company_ref.get()
    data = company.to_dict() or {}
    if not company.exists or str(data.get("status")) != "pilot":
        raise HTTPException(status_code=409, detail="Şirket aktif pilot kapsamında değil.")
    start = _datetime(data.get("pilotStartedAt"))
    try:
        min_days = int(os.getenv("PILOT_SURVEY_MIN_DAYS", "21"))
    except ValueError:
        min_days = 21
    min_days = min(28, max(0, min_days))
    if not start or datetime.now(timezone.utc) < start + timedelta(days=min_days):
        raise HTTPException(status_code=409, detail="Pilot değerlendirmesi ölçüm döneminin son haftasında açılır.")
    batch = db.batch()
    batch.set(company_ref.collection("pilotSurveys").document("current"), {
        "companyId": user.sirket_id,
        "continuationIntent": request.devam_niyeti,
        "paidContinuation": request.ucretli_devam,
        "respondedBy": user.kullanici_id,
        "respondedAt": firestore.SERVER_TIMESTAMP,
        "containsFinancialData": False,
    })
    batch.set(company_ref.collection("auditLogs").document(), {
        "action": "pilot.intent_recorded",
        "resource": "pilot/survey",
        "actorId": user.kullanici_id,
        "companyId": user.sirket_id,
        "createdAt": firestore.SERVER_TIMESTAMP,
        "containsFinancialData": False,
    })
    batch.commit()
    return {"durum": "kaydedildi"}

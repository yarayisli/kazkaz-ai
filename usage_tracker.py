"""
KazKaz AI — Kullanım Metrikleri (Usage Tracker)
=================================================
Basit event counter. Firestore backend kullanır; DB yoksa no-op
(uygulama etkilenmez).

Veri modeli:
  Koleksiyon:  usage_daily
  Doküman ID:  YYYY-MM-DD  (her gün bir doküman)
  Alanlar:
    events:       { "login": N, "ai_activation": N, "pdf_download": N, ... }
    pages:        { "genel": N, "cfo": N, "gelir": N, ... }
    unique_users: [uid1, uid2, ...]   (o gün gelen kullanıcı kimlikleri)
    plans:        { "free": N, "pro": N, "uzman": N }

Firestore atomic Increment ve ArrayUnion ile thread-safe.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional


class UsageTracker:
    """
    Kullanım event'leri kaydeder, admin dashboard için okur.

    Kullanım:
        tracker = UsageTracker(firestore_client)
        tracker.track("page_view", user_id="uid_1", page="cfo", plan="pro")
        tracker.track("ai_call",    user_id="uid_1", plan="pro")

    Admin okuma:
        stats  = tracker.daily_stats("2026-08-23")
        recent = tracker.range_stats(n_days=30)
    """

    def __init__(self, firestore_db, collection: str = "usage_daily"):
        """
        firestore_db: google.cloud.firestore.Client veya uyumlu (mock/None).
        None ise tüm çağrılar no-op olur.
        """
        self._db = firestore_db
        self._col = collection

    def _coll(self):
        return self._db.collection(self._col)

    # ── Yazma ────────────────────────────────────────────────────────────────

    def track(
        self,
        event: str,
        user_id: Optional[str] = None,
        page: Optional[str] = None,
        plan: Optional[str] = None,
    ) -> bool:
        """Bugünün document'ine atomic increment. Başarı bool döner."""
        if self._db is None or not event:
            return False
        try:
            from google.cloud import firestore
            today = date.today().isoformat()
            ref = self._coll().document(today)
            updates: Dict[str, Any] = {
                "date": today,
                f"events.{event}": firestore.Increment(1),
            }
            if page:
                updates[f"pages.{page}"] = firestore.Increment(1)
            if plan:
                updates[f"plans.{plan}"] = firestore.Increment(1)
            if user_id:
                updates["unique_users"] = firestore.ArrayUnion([user_id])
            ref.set(updates, merge=True)
            return True
        except Exception:
            return False

    # ── Okuma ────────────────────────────────────────────────────────────────

    def daily_stats(self, day: str) -> Dict[str, Any]:
        """Bir günün ham istatistikleri."""
        if self._db is None:
            return {}
        try:
            doc = self._coll().document(day).get()
            if not doc.exists:
                return {}
            data = doc.to_dict() or {}
            return {
                "date":         day,
                "events":       dict(data.get("events", {})),
                "pages":        dict(data.get("pages", {})),
                "plans":        dict(data.get("plans", {})),
                "unique_users": len(data.get("unique_users", []) or []),
            }
        except Exception:
            return {}

    def range_stats(self, n_days: int = 7) -> List[Dict[str, Any]]:
        """Son N günün istatistikleri (eskiden yeniye)."""
        today = date.today()
        results = []
        for i in range(n_days):
            d = (today - timedelta(days=i)).isoformat()
            stats = self.daily_stats(d)
            if not stats:
                stats = {"date": d, "events": {}, "pages": {},
                         "plans": {}, "unique_users": 0}
            results.append(stats)
        return list(reversed(results))

    def totals(self, n_days: int = 30) -> Dict[str, Any]:
        """N gün için toplu özet — DAU (bugün), aktif kullanıcı, toplam olaylar."""
        rows = self.range_stats(n_days)
        if not rows:
            return {
                "dau_today": 0, "aktif_toplam": 0,
                "toplam_events": {}, "toplam_pages": {},
                "toplam_plans": {}, "gunluk_seri": [],
            }
        toplam_events: Dict[str, int] = {}
        toplam_pages:  Dict[str, int] = {}
        toplam_plans:  Dict[str, int] = {}
        aktif_toplam = 0
        for r in rows:
            aktif_toplam += r.get("unique_users", 0)
            for k, v in (r.get("events") or {}).items():
                toplam_events[k] = toplam_events.get(k, 0) + int(v)
            for k, v in (r.get("pages") or {}).items():
                toplam_pages[k] = toplam_pages.get(k, 0) + int(v)
            for k, v in (r.get("plans") or {}).items():
                toplam_plans[k] = toplam_plans.get(k, 0) + int(v)
        dau_today = rows[-1].get("unique_users", 0)
        return {
            "dau_today":     dau_today,
            "aktif_toplam":  aktif_toplam,
            "toplam_events": toplam_events,
            "toplam_pages":  toplam_pages,
            "toplam_plans":  toplam_plans,
            "gunluk_seri":   rows,
        }

"""
Admin dashboard / Usage tracker testleri.
Firestore mock ile — canlı DB bağlantısı gerekmez.
"""
import unittest
from datetime import date

from usage_tracker import UsageTracker


# ─── Minimal Firestore mock ──────────────────────────────────────────────────

class _Doc:
    def __init__(self, data=None):
        self.exists = data is not None
        self._data = data or {}
    def to_dict(self): return dict(self._data)


class _DocRef:
    def __init__(self, store, key):
        self._store, self._key = store, key
    def get(self):
        data = self._store.get(self._key)
        return _Doc(data)
    def set(self, data, merge=False):
        if not merge or self._key not in self._store:
            self._store[self._key] = {}
        existing = self._store[self._key]
        for k, v in data.items():
            # dot-notation: events.foo → nested set
            if "." in k:
                outer, inner = k.split(".", 1)
                existing.setdefault(outer, {})
                # Increment nesnesi ise +N
                if hasattr(v, "value"):
                    existing[outer][inner] = existing[outer].get(inner, 0) + v.value
                else:
                    existing[outer][inner] = v
            else:
                # ArrayUnion mı? _values attr'ı var
                if hasattr(v, "_values"):
                    arr = existing.get(k, [])
                    for x in v._values:
                        if x not in arr:
                            arr.append(x)
                    existing[k] = arr
                else:
                    existing[k] = v


class _Coll:
    def __init__(self, store): self._store = store
    def document(self, k): return _DocRef(self._store, k)


class _MockDb:
    def __init__(self): self._store = {}
    def collection(self, name): return _Coll(self._store)


# ─── google.cloud.firestore.Increment / ArrayUnion mock ─────────────────────

class _Increment:
    def __init__(self, value): self.value = value


class _ArrayUnion:
    def __init__(self, values): self._values = values


class _FirestoreMock:
    Increment = _Increment
    ArrayUnion = _ArrayUnion


def _patch_firestore():
    """usage_tracker içindeki 'from google.cloud import firestore' import'unu mock'la."""
    import sys, types
    google_mod = types.ModuleType("google")
    cloud_mod = types.ModuleType("google.cloud")
    cloud_mod.firestore = _FirestoreMock
    google_mod.cloud = cloud_mod
    sys.modules["google"] = google_mod
    sys.modules["google.cloud"] = cloud_mod
    sys.modules["google.cloud.firestore"] = _FirestoreMock


class TestUsageTracker(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _patch_firestore()

    def setUp(self):
        self.db = _MockDb()
        self.tracker = UsageTracker(self.db)

    # ── Track ────────────────────────────────────────────────────────────

    def test_track_event_kaydediliyor(self):
        ok = self.tracker.track("login", user_id="u1", plan="free")
        self.assertTrue(ok)
        today = date.today().isoformat()
        self.assertIn(today, self.db._store)

    def test_track_none_db_no_op(self):
        """Firestore None ise track no-op — hata atmaz, False döner."""
        t = UsageTracker(None)
        self.assertFalse(t.track("login", user_id="u1"))

    def test_track_bos_event_reddedilir(self):
        self.assertFalse(self.tracker.track("", user_id="u1"))

    def test_unique_users_biriktiriliyor(self):
        self.tracker.track("page_view", user_id="u1", page="cfo")
        self.tracker.track("page_view", user_id="u1", page="cfo")  # aynı user
        self.tracker.track("page_view", user_id="u2", page="cfo")
        stats = self.tracker.daily_stats(date.today().isoformat())
        self.assertEqual(stats["unique_users"], 2)  # u1 tekrar sayılmaz

    def test_event_counter_artiyor(self):
        for _ in range(5):
            self.tracker.track("ai_call", user_id="u1")
        stats = self.tracker.daily_stats(date.today().isoformat())
        self.assertEqual(stats["events"]["ai_call"], 5)

    def test_page_counter_ayrildi(self):
        self.tracker.track("page_view", user_id="u1", page="cfo")
        self.tracker.track("page_view", user_id="u1", page="gelir")
        self.tracker.track("page_view", user_id="u1", page="cfo")
        stats = self.tracker.daily_stats(date.today().isoformat())
        self.assertEqual(stats["pages"]["cfo"], 2)
        self.assertEqual(stats["pages"]["gelir"], 1)

    def test_plan_counter_ayrildi(self):
        self.tracker.track("login", user_id="u1", plan="free")
        self.tracker.track("login", user_id="u2", plan="pro")
        self.tracker.track("login", user_id="u3", plan="pro")
        stats = self.tracker.daily_stats(date.today().isoformat())
        self.assertEqual(stats["plans"]["free"], 1)
        self.assertEqual(stats["plans"]["pro"], 2)

    # ── Okuma ────────────────────────────────────────────────────────────

    def test_daily_stats_bos_gun(self):
        stats = self.tracker.daily_stats("1990-01-01")
        self.assertEqual(stats, {})

    def test_range_stats_n_days(self):
        self.tracker.track("login", user_id="u1")
        rows = self.tracker.range_stats(n_days=7)
        self.assertEqual(len(rows), 7)
        # Bugünkü kayıt en sonda
        self.assertEqual(rows[-1]["events"].get("login"), 1)

    def test_totals_dau_ve_toplam(self):
        self.tracker.track("login",   user_id="u1", plan="free")
        self.tracker.track("ai_call", user_id="u1", plan="free")
        self.tracker.track("ai_call", user_id="u2", plan="pro")
        totals = self.tracker.totals(n_days=7)
        self.assertEqual(totals["dau_today"], 2)  # u1 ve u2
        self.assertEqual(totals["toplam_events"]["ai_call"], 2)
        self.assertEqual(totals["toplam_events"]["login"], 1)


# Not: admin_ui.is_admin() Streamlit session_state kullandığı için sadece
# Streamlit runtime içinde test edilebilir. Manuel doğrulama: farklı
# e-posta ile giriş yap, sidebar'da "Admin Dashboard" nav_item'ı
# görünüyor mu kontrol et.


if __name__ == "__main__":
    unittest.main()

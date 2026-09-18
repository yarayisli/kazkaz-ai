"""Şirket durumu güvenilir okumasının son-bilinen-durum önbelleği (Fix-3).

Firestore geçici olarak ulaşılamazsa sirket_durumu_guvenilir artık ham
None (→ token'a fail-open) yerine, kısa süreli bir önbellekteki son
doğrulanmış duruma düşer. Önbellek yoksa veya süresi geçmişse yine None
döner — sonsuza dek eski bir değere güvenilmez.
"""

import unittest
from unittest.mock import MagicMock, patch

from api.auth import (
    sirket_durumu_guvenilir,
    sirket_durumu_onbellegini_sifirla,
)


def _fake_db(exists=True, status="active", raise_on_get=None):
    db = MagicMock()
    doc_ref = db.collection.return_value.document.return_value
    if raise_on_get is not None:
        doc_ref.get.side_effect = raise_on_get
    else:
        snap = MagicMock()
        snap.exists = exists
        snap.to_dict.return_value = {"status": status}
        doc_ref.get.return_value = snap
    return db


class TestSirketDurumuOnbellek(unittest.TestCase):
    def setUp(self):
        sirket_durumu_onbellegini_sifirla()
        # _firebase_uygulamasi() gerçek Firebase kurulumu dener (env yoksa
        # RuntimeError fırlatır); tüm testlerde sahte bir "app" ile atlanır.
        self.app_patch = patch("api.auth._firebase_uygulamasi", return_value=object())
        self.app_patch.start()

    def tearDown(self):
        self.app_patch.stop()
        sirket_durumu_onbellegini_sifirla()

    def test_basarili_okuma_dogru_durumu_doner_ve_onbellegi_gunceller(self):
        with patch("firebase_admin.firestore.client", return_value=_fake_db(status="suspended")):
            self.assertEqual(sirket_durumu_guvenilir("c1"), "suspended")

    def test_okuma_basarisiz_ve_onbellek_yoksa_none_doner(self):
        # Bu şirket için hiç başarılı okuma yapılmamış: düşecek bir önbellek yok.
        with patch("firebase_admin.firestore.client", return_value=_fake_db(raise_on_get=RuntimeError("kesinti"))):
            self.assertIsNone(sirket_durumu_guvenilir("c-hic-okunmamis"))

    def test_okuma_basarisiz_olunca_son_bilinen_duruma_duser_token_a_degil(self):
        # Önce başarılı bir okuma önbelleği doldursun.
        with patch("firebase_admin.firestore.client", return_value=_fake_db(status="suspended")):
            self.assertEqual(sirket_durumu_guvenilir("c2"), "suspended")
        # Şimdi Firestore geçici olarak ulaşılamaz olsun (TTL içinde).
        with patch("firebase_admin.firestore.client", return_value=_fake_db(raise_on_get=RuntimeError("kesinti"))):
            self.assertEqual(sirket_durumu_guvenilir("c2"), "suspended")

    def test_onbellek_ttl_disindaysa_none_a_duser_sonsuza_dek_guvenilmez(self):
        with patch("firebase_admin.firestore.client", return_value=_fake_db(status="suspended")):
            self.assertEqual(sirket_durumu_guvenilir("c3"), "suspended")
        # Önbellek kaydını TTL penceresinin çok dışına it (uzun süreli kesinti simülasyonu).
        import api.auth as auth_mod
        durum, _ = auth_mod._DURUM_ONBELLEK["c3"]
        auth_mod._DURUM_ONBELLEK["c3"] = (durum, auth_mod.time.monotonic() - 10_000)
        with patch("firebase_admin.firestore.client", return_value=_fake_db(raise_on_get=RuntimeError("kesinti"))):
            self.assertIsNone(sirket_durumu_guvenilir("c3"))

    def test_sirket_bulunamazsa_onbellege_bakmadan_none_doner(self):
        with patch("firebase_admin.firestore.client", return_value=_fake_db(exists=False)):
            self.assertIsNone(sirket_durumu_guvenilir("c-yok"))


if __name__ == "__main__":
    unittest.main()

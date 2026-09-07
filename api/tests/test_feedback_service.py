"""Destek döngüsü: talep no, kullanıcının kendi talepleri, memnuniyet (P2-4)."""

import unittest
from unittest.mock import patch

from fastapi import HTTPException

from api.feedback_service import (
    geri_bildirim_kaydet,
    geri_bildirim_memnuniyeti,
    geri_bildirimlerim,
)
from api.models import GeriBildirimIstegi, GeriBildirimMemnuniyetIstegi, KimlikBilgisi


class _Snap:
    def __init__(self, data):
        self._data = data
        self.exists = data is not None

    def to_dict(self):
        return self._data


class _Doc:
    def __init__(self, db, path):
        self.db, self.path, self.id = db, path, path[-1]

    def collection(self, name):
        return _Col(self.db, (*self.path, name))

    def get(self):
        return _Snap(self.db.store.get(self.path))

    def set(self, data, merge=False):
        mevcut = self.db.store.get(self.path)
        if merge and isinstance(mevcut, dict):
            self.db.store[self.path] = {**mevcut, **data}
        else:
            self.db.store[self.path] = data


class _Col:
    def __init__(self, db, path):
        self.db, self.path = db, path

    def document(self, name=None):
        if name is None:
            self.db.counter += 1
            name = f"fbdoc{self.db.counter:04d}"
        return _Doc(self.db, (*self.path, name))

    def stream(self):
        for key, val in list(self.db.store.items()):
            if key[:-1] == self.path and len(key) == len(self.path) + 1 and isinstance(val, dict):
                snap = _Snap(val)
                snap.id = key[-1]
                yield snap


class _Db:
    def __init__(self):
        self.store, self.counter = {}, 0

    def collection(self, name):
        return _Col(self, (name,))


def _user(uid="user-a", company="company-a"):
    return KimlikBilgisi(kullanici_id=uid, sirket_id=company, roller={"admin": True})


class TestFeedbackLoop(unittest.TestCase):
    def setUp(self):
        self.db = _Db()
        self.patch = patch("api.feedback_service._db", return_value=self.db)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()

    def _gonder(self, uid="user-a"):
        return geri_bildirim_kaydet(
            GeriBildirimIstegi(kategori="hata", mesaj="Bir sorun yaşadım burada.", sayfa="overview"),
            _user(uid),
        )

    def test_kayit_talep_no_dondurur(self):
        sonuc = self._gonder()
        self.assertTrue(sonuc["talep_no"].startswith("T-"))
        self.assertEqual(sonuc["durum"], "alindi")

    def test_taleplerim_yalniz_kendi_taleplerini_doner(self):
        self._gonder("user-a")
        self._gonder("user-b")  # başka kullanıcı
        talepler = geri_bildirimlerim(_user("user-a"))["talepler"]
        self.assertEqual(len(talepler), 1)
        self.assertEqual(talepler[0]["durum"], "new")
        self.assertIsNone(talepler[0]["memnun"])

    def test_memnuniyet_yalniz_cozulmus_talepte_kabul_edilir(self):
        kayit = self._gonder()
        fb_id = kayit["kayit_id"]
        # Henüz 'new' — memnuniyet reddedilmeli.
        with self.assertRaises(HTTPException) as ctx:
            geri_bildirim_memnuniyeti(GeriBildirimMemnuniyetIstegi(geri_bildirim_id=fb_id, memnun=True), _user())
        self.assertEqual(ctx.exception.status_code, 409)
        # Çözülmüş yap.
        self.db.store[("companies", "company-a", "feedback", fb_id)]["status"] = "resolved"
        sonuc = geri_bildirim_memnuniyeti(GeriBildirimMemnuniyetIstegi(geri_bildirim_id=fb_id, memnun=True), _user())
        self.assertTrue(sonuc["memnun"])
        talepler = geri_bildirimlerim(_user())["talepler"]
        self.assertTrue(talepler[0]["memnun"])

    def test_baskasinin_talebine_memnuniyet_verilemez(self):
        kayit = self._gonder("user-a")
        fb_id = kayit["kayit_id"]
        self.db.store[("companies", "company-a", "feedback", fb_id)]["status"] = "resolved"
        with self.assertRaises(HTTPException) as ctx:
            geri_bildirim_memnuniyeti(GeriBildirimMemnuniyetIstegi(geri_bildirim_id=fb_id, memnun=False), _user("user-b"))
        self.assertEqual(ctx.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()

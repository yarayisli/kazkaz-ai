"""Askı sırasında iptali başarısız kalan üyelerin kuyruğa alınması ve yeniden
denenmesi (P1-C Bölüm 3)."""

import unittest
from unittest.mock import MagicMock, patch

from api.models import KimlikBilgisi, PlatformSirketGuncellemeIstegi
from api.platform_admin_service import (
    platform_bekleyen_claimleri_yeniden_dene,
    platform_sirketini_guncelle,
)


class _Snap:
    def __init__(self, data, doc_id=None):
        self._data = data
        self.exists = data is not None
        self.id = doc_id

    def to_dict(self):
        return self._data


class _DocRef:
    def __init__(self, store, path):
        self.store = store
        self.path = path
        self.id = path[-1]

    def collection(self, name):
        return _ColRef(self.store, (*self.path, name))

    def get(self):
        return _Snap(self.store.get(self.path), self.id)

    def set(self, data, merge=False):
        mevcut = self.store.get(self.path)
        if merge and isinstance(mevcut, dict):
            self.store[self.path] = {**mevcut, **data}
        else:
            self.store[self.path] = data

    def delete(self):
        self.store.pop(self.path, None)


class _ColRef:
    def __init__(self, store, path):
        self.store = store
        self.path = path

    def document(self, name=None):
        if name is None:
            anahtar = ("__auto__", self.path)
            self.store[anahtar] = self.store.get(anahtar, 0) + 1
            name = f"auto-{self.store[anahtar]}"
        return _DocRef(self.store, (*self.path, name))

    def limit(self, _n):
        return self

    def stream(self):
        for anahtar, deger in list(self.store.items()):
            if (
                isinstance(anahtar, tuple)
                and len(anahtar) == len(self.path) + 1
                and anahtar[: len(self.path)] == self.path
                and isinstance(deger, dict)
            ):
                yield _Snap(deger, anahtar[-1])


class _FakeBatch:
    def __init__(self, store):
        self.store = store
        self.ops = []

    def set(self, ref, data, merge=False):
        self.ops.append((ref, data, merge))
        return self

    def commit(self):
        for ref, data, merge in self.ops:
            ref.set(data, merge=merge)


class _FakeDb:
    def __init__(self):
        self.store = {}

    def collection(self, name):
        return _ColRef(self.store, (name,))

    def batch(self):
        return _FakeBatch(self.store)


def _yonetici():
    return KimlikBilgisi(kullanici_id="platform-admin", roller={"platform_admin": True})


BEKLEYEN = ("companies", "c1", "bekleyenClaimGuncellemeleri", "m2")


class TestClaimYenidenDeneme(unittest.TestCase):
    def setUp(self):
        self.db = _FakeDb()
        # Şirket + iki üye: m1 iptal edilebilir, m2 iptali başarısız olacak.
        self.db.store[("companies", "c1")] = {"status": "active", "plan": "pro"}
        self.db.store[("companies", "c1", "members", "m1")] = {"role": "admin"}
        self.db.store[("companies", "c1", "members", "m2")] = {"role": "cfo"}
        self.db.store[("users", "m2")] = {"companyId": "c1"}

        self.patches = [
            patch("api.platform_admin_service._db", return_value=self.db),
            patch("api.platform_admin_service._firebase_uygulamasi", return_value=MagicMock()),
            patch("api.platform_admin_service._claimleri_guncelle", return_value=None),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def _revoke_m2_basarisiz(self, uye_id, app=None):
        if uye_id == "m2":
            raise RuntimeError("iptal edilemedi")

    def test_iptali_basarisiz_uye_kismen_doner_ve_kuyruga_yazilir(self):
        with patch(
            "api.platform_admin_service.firebase_auth.revoke_refresh_tokens",
            side_effect=self._revoke_m2_basarisiz,
        ):
            sonuc = platform_sirketini_guncelle(
                PlatformSirketGuncellemeIstegi(sirket_id="c1", durum="suspended"),
                _yonetici(),
            )
        self.assertEqual(sonuc["durum"], "kismen_guncellendi")
        self.assertEqual(sonuc["basarili_uye"], 1)
        self.assertEqual(sonuc["basarisiz_uye"], 1)
        self.assertEqual(sonuc["oturum_yenileme_uyarisi"], 1)  # geriye dönük uyum
        # Şirket durumu yine de güncellenmiş olmalı (finans erişimi kapanır).
        self.assertEqual(self.db.store[("companies", "c1")]["status"], "suspended")
        # Başarısız üye yeniden denenecek iş olarak kuyruğa yazılmalı.
        self.assertIn(BEKLEYEN, self.db.store)
        self.assertEqual(self.db.store[BEKLEYEN]["attempts"], 1)

    def test_yeniden_deneme_cozulen_uyeyi_kuyruktan_siler(self):
        # Önce çakışmayı oluştur.
        with patch(
            "api.platform_admin_service.firebase_auth.revoke_refresh_tokens",
            side_effect=self._revoke_m2_basarisiz,
        ):
            platform_sirketini_guncelle(
                PlatformSirketGuncellemeIstegi(sirket_id="c1", durum="suspended"),
                _yonetici(),
            )
        self.assertIn(BEKLEYEN, self.db.store)
        # Şimdi iptal başarılı: yeniden deneme kuyruğu temizlemeli.
        with patch("api.platform_admin_service.firebase_auth.revoke_refresh_tokens", return_value=None):
            sonuc = platform_bekleyen_claimleri_yeniden_dene("c1", _yonetici())
        self.assertEqual(sonuc["durum"], "tamamlandi")
        self.assertEqual(sonuc["cozulen_uye"], 1)
        self.assertEqual(sonuc["kalan_uye"], 0)
        self.assertNotIn(BEKLEYEN, self.db.store)

    def test_tum_uyeler_basariliysa_guncellendi_doner(self):
        with patch("api.platform_admin_service.firebase_auth.revoke_refresh_tokens", return_value=None):
            sonuc = platform_sirketini_guncelle(
                PlatformSirketGuncellemeIstegi(sirket_id="c1", durum="suspended"),
                _yonetici(),
            )
        self.assertEqual(sonuc["durum"], "guncellendi")
        self.assertEqual(sonuc["basarisiz_uye"], 0)
        self.assertNotIn(BEKLEYEN, self.db.store)

    def test_pilot_baslatilinca_olcum_baslangici_sabitlenir(self):
        with patch("api.platform_admin_service.firebase_auth.revoke_refresh_tokens", return_value=None):
            sonuc = platform_sirketini_guncelle(
                PlatformSirketGuncellemeIstegi(sirket_id="c1", durum="pilot"),
                _yonetici(),
            )
        self.assertEqual(sonuc["degisiklikler"], {"status": "pilot"})
        self.assertIn("pilotStartedAt", self.db.store[("companies", "c1")])


if __name__ == "__main__":
    unittest.main()

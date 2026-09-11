import json
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from api.models import CalismaAlaniKaydetIstegi, CalismaAlaniSilIstegi, KimlikBilgisi
from api.workspace_service import (
    calisma_alani_disa_aktar,
    calisma_alani_kaydet,
    calisma_alani_sil,
    calisma_alani_yukle,
)


class FakeSnapshot:
    def __init__(self, data):
        self._data = data
        self.exists = data is not None

    def to_dict(self):
        return self._data


class FakeDocument:
    def __init__(self, db, path):
        self.db = db
        self.path = path

    def collection(self, name):
        return FakeCollection(self.db, (*self.path, name))

    def get(self, transaction=None):
        # Gerçek SDK'da transaction okuması işlemin içindedir; sahte db
        # tek iş parçacıklı testte doğrudan mağazadan okur.
        return FakeSnapshot(self.db.store.get(self.path))

    def set(self, data):
        self.db.store[self.path] = data


class FakeCollection:
    def __init__(self, db, path):
        self.db = db
        self.path = path

    def document(self, name=None):
        if name is None:
            self.db.counter += 1
            name = f"auto-{self.db.counter}"
        return FakeDocument(self.db, (*self.path, name))


class FakeBatch:
    def __init__(self, db):
        self.db = db
        self.operations = []

    def set(self, ref, data):
        self.operations.append(("set", ref, data))
        # google-cloud-firestore WriteBatch.set() dönüş değeri None'dır.
        # Sahte istemci gerçek SDK davranışını taklit ederek zincirleme çağrı
        # hatalarının testten kaçmasını engeller.
        return None

    def delete(self, ref):
        self.operations.append(("delete", ref, None))
        return self

    def commit(self):
        for operation, ref, data in self.operations:
            if operation == "set":
                self.db.store[ref.path] = data
            else:
                self.db.store.pop(ref.path, None)


class FakeTransaction:
    """Oku-karşılaştır-yaz gövdesini doğrudan mağazaya uygular.

    `firestore.transactional` testte kimlik dekoratörüyle değiştirildiği için
    gövde bir kez çalışır; atomiklik SDK'nın işi, burada doğrulanan çakışma
    mantığıdır.
    """

    def __init__(self, db):
        self.db = db

    def set(self, ref, data):
        self.db.store[ref.path] = data
        return self


class FakeDb:
    def __init__(self):
        self.store = {}
        self.counter = 0

    def collection(self, name):
        return FakeCollection(self, (name,))

    def batch(self):
        return FakeBatch(self)

    def transaction(self):
        return FakeTransaction(self)


def snapshot():
    return {
        "financialData": {"companyName": "Test A.Ş."},
        "cashFlow": [],
        "debts": [],
        "customers": [],
        "budget": [],
        "financialAudit": None,
        "isSampleData": False,
    }


def kullanici(rol="admin"):
    return KimlikBilgisi(
        kullanici_id=f"user-{rol}",
        sirket_id="company-a",
        roller={rol: True},
    )


class TestWorkspaceService(unittest.TestCase):
    def setUp(self):
        self.db = FakeDb()
        self.db_patch = patch("api.workspace_service._db", return_value=self.db)
        self.db_patch.start()
        # Gerçek transactional dekoratörü SDK işlem nesnesi bekler; testte
        # gövdeyi doğrudan çalıştıran kimlik dekoratörüyle değiştiriyoruz.
        self.txn_patch = patch("api.workspace_service.firestore.transactional", lambda fn: fn)
        self.txn_patch.start()

    def tearDown(self):
        self.txn_patch.stop()
        self.db_patch.stop()

    def test_admin_kaydeder_viewer_okur_ve_audit_olusur(self):
        sonuc = calisma_alani_kaydet(
            CalismaAlaniKaydetIstegi(snapshot=snapshot(), baz_revizyon=0),
            kullanici("admin"),
        )
        self.assertEqual(sonuc["durum"], "kaydedildi")
        self.assertIn(("companies", "company-a", "workspaces", "current"), self.db.store)

        yuklenen = calisma_alani_yukle(kullanici("viewer"))
        self.assertEqual(yuklenen["snapshot"]["financialData"]["companyName"], "Test A.Ş.")
        aksiyonlar = [v.get("action") for k, v in self.db.store.items() if "auditLogs" in k]
        self.assertIn("workspace.save", aksiyonlar)
        self.assertIn("workspace.read", aksiyonlar)

    def test_export_finansal_veriyi_json_olarak_dondurur_ve_loglar(self):
        calisma_alani_kaydet(CalismaAlaniKaydetIstegi(snapshot=snapshot(), baz_revizyon=0), kullanici("cfo"))
        paket = json.loads(calisma_alani_disa_aktar(kullanici("viewer")).decode("utf-8"))
        self.assertEqual(paket["companyId"], "company-a")
        self.assertEqual(paket["workspace"]["financialData"]["companyName"], "Test A.Ş.")
        aksiyonlar = [v.get("action") for k, v in self.db.store.items() if "auditLogs" in k]
        self.assertIn("workspace.export", aksiyonlar)

    def test_silme_yalniz_admin_ve_cfo_rolune_aciktir(self):
        calisma_alani_kaydet(CalismaAlaniKaydetIstegi(snapshot=snapshot(), baz_revizyon=0), kullanici("admin"))
        with self.assertRaises(HTTPException) as context:
            calisma_alani_sil(CalismaAlaniSilIstegi(baz_revizyon=1), kullanici("analist"))
        self.assertEqual(context.exception.status_code, 403)

        sonuc = calisma_alani_sil(CalismaAlaniSilIstegi(baz_revizyon=1), kullanici("cfo"))
        self.assertEqual(sonuc["durum"], "silindi")
        self.assertIsNone(calisma_alani_yukle(kullanici())["snapshot"])
        self.assertNotIn("snapshot", self.db.store[("companies", "company-a", "workspaces", "current")])

    def test_eksik_snapshot_reddedilir(self):
        with self.assertRaises(HTTPException) as context:
            calisma_alani_kaydet(
                CalismaAlaniKaydetIstegi(snapshot={"financialData": {}}, baz_revizyon=0),
                kullanici("admin"),
            )
        self.assertEqual(context.exception.status_code, 422)

    def test_ilk_kayit_revizyonu_bire_cikarir(self):
        sonuc = calisma_alani_kaydet(
            CalismaAlaniKaydetIstegi(snapshot=snapshot(), baz_revizyon=0),
            kullanici("admin"),
        )
        self.assertEqual(sonuc["revizyon"], 1)
        self.assertEqual(calisma_alani_yukle(kullanici("viewer"))["revizyon"], 1)

    def test_eszamanli_eski_surume_kayit_409_ve_ilk_korunur(self):
        # İki oturum da revizyon 0'ı görüyor. İlki kaydeder → revizyon 1.
        calisma_alani_kaydet(CalismaAlaniKaydetIstegi(snapshot=snapshot(), baz_revizyon=0), kullanici("admin"))
        # İkinci oturum hâlâ eski tabanla (0) kaydetmeye çalışır → çakışma.
        ezen = {**snapshot(), "financialData": {"companyName": "Ezen Oturum"}}
        with self.assertRaises(HTTPException) as context:
            calisma_alani_kaydet(CalismaAlaniKaydetIstegi(snapshot=ezen, baz_revizyon=0), kullanici("cfo"))
        self.assertEqual(context.exception.status_code, 409)
        self.assertEqual(context.exception.detail["kod"], "calisma_alani_cakismasi")
        self.assertEqual(context.exception.detail["mevcut_revizyon"], 1)
        # İlk kayıt korunmalı; ezen oturumun verisi yazılmamalı.
        yuklenen = calisma_alani_yukle(kullanici("viewer"))
        self.assertEqual(yuklenen["snapshot"]["financialData"]["companyName"], "Test A.Ş.")
        self.assertEqual(yuklenen["revizyon"], 1)

    def test_dogru_taban_surumle_kayit_gecer(self):
        calisma_alani_kaydet(CalismaAlaniKaydetIstegi(snapshot=snapshot(), baz_revizyon=0), kullanici("admin"))
        guncel = {**snapshot(), "financialData": {"companyName": "Güncel A.Ş."}}
        ikinci = calisma_alani_kaydet(CalismaAlaniKaydetIstegi(snapshot=guncel, baz_revizyon=1), kullanici("admin"))
        self.assertEqual(ikinci["revizyon"], 2)
        self.assertEqual(
            calisma_alani_yukle(kullanici("viewer"))["snapshot"]["financialData"]["companyName"],
            "Güncel A.Ş.",
        )

    def test_baz_revizyon_zorunlu(self):
        from pydantic import ValidationError
        for ek in ({}, {"baz_revizyon": None}):
            with self.assertRaises(ValidationError):
                CalismaAlaniKaydetIstegi(snapshot=snapshot(), **ek)

    def test_silme_yeniden_olusturma_eski_oturumu_kabul_etmez(self):
        calisma_alani_kaydet(CalismaAlaniKaydetIstegi(snapshot=snapshot(), baz_revizyon=0), kullanici())
        silinen = calisma_alani_sil(CalismaAlaniSilIstegi(baz_revizyon=1), kullanici())
        self.assertEqual(silinen["revizyon"], 2)
        self.assertEqual(calisma_alani_yukle(kullanici())["revizyon"], 2)
        calisma_alani_kaydet(CalismaAlaniKaydetIstegi(snapshot=snapshot(), baz_revizyon=2), kullanici())
        with self.assertRaises(HTTPException) as hata:
            calisma_alani_kaydet(CalismaAlaniKaydetIstegi(snapshot=snapshot(), baz_revizyon=1), kullanici())
        self.assertEqual(hata.exception.status_code, 409)

    def test_eski_oturum_guncel_calisma_alanini_silemez(self):
        calisma_alani_kaydet(CalismaAlaniKaydetIstegi(snapshot=snapshot(), baz_revizyon=0), kullanici())
        guncel = dict(snapshot())
        guncel["financialData"] = {"companyName": "Korunacak A.Ş."}
        calisma_alani_kaydet(CalismaAlaniKaydetIstegi(snapshot=guncel, baz_revizyon=1), kullanici())
        with self.assertRaises(HTTPException) as hata:
            calisma_alani_sil(CalismaAlaniSilIstegi(baz_revizyon=1), kullanici())
        self.assertEqual(hata.exception.status_code, 409)
        self.assertEqual(
            calisma_alani_yukle(kullanici())["snapshot"]["financialData"]["companyName"],
            "Korunacak A.Ş.",
        )

    def test_yerel_gelistirici_buluta_yazamaz(self):
        dev = KimlikBilgisi(kullanici_id="dev", sirket_id="yerel-demo", roller={"gelistirici": True})
        with self.assertRaises(HTTPException) as context:
            calisma_alani_kaydet(CalismaAlaniKaydetIstegi(snapshot=snapshot(), baz_revizyon=0), dev)
        self.assertEqual(context.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()

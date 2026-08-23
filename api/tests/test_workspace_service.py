import json
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from api.models import CalismaAlaniKaydetIstegi, KimlikBilgisi
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

    def get(self):
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
        return self

    def delete(self, ref):
        self.operations.append(("delete", ref, None))
        return self

    def commit(self):
        for operation, ref, data in self.operations:
            if operation == "set":
                self.db.store[ref.path] = data
            else:
                self.db.store.pop(ref.path, None)


class FakeDb:
    def __init__(self):
        self.store = {}
        self.counter = 0

    def collection(self, name):
        return FakeCollection(self, (name,))

    def batch(self):
        return FakeBatch(self)


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

    def tearDown(self):
        self.db_patch.stop()

    def test_admin_kaydeder_viewer_okur_ve_audit_olusur(self):
        sonuc = calisma_alani_kaydet(
            CalismaAlaniKaydetIstegi(snapshot=snapshot()),
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
        calisma_alani_kaydet(CalismaAlaniKaydetIstegi(snapshot=snapshot()), kullanici("cfo"))
        paket = json.loads(calisma_alani_disa_aktar(kullanici("viewer")).decode("utf-8"))
        self.assertEqual(paket["companyId"], "company-a")
        self.assertEqual(paket["workspace"]["financialData"]["companyName"], "Test A.Ş.")
        aksiyonlar = [v.get("action") for k, v in self.db.store.items() if "auditLogs" in k]
        self.assertIn("workspace.export", aksiyonlar)

    def test_silme_yalniz_admin_ve_cfo_rolune_aciktir(self):
        calisma_alani_kaydet(CalismaAlaniKaydetIstegi(snapshot=snapshot()), kullanici("admin"))
        with self.assertRaises(HTTPException) as context:
            calisma_alani_sil(kullanici("analist"))
        self.assertEqual(context.exception.status_code, 403)

        sonuc = calisma_alani_sil(kullanici("cfo"))
        self.assertEqual(sonuc["durum"], "silindi")
        self.assertNotIn(("companies", "company-a", "workspaces", "current"), self.db.store)

    def test_eksik_snapshot_reddedilir(self):
        with self.assertRaises(HTTPException) as context:
            calisma_alani_kaydet(
                CalismaAlaniKaydetIstegi(snapshot={"financialData": {}}),
                kullanici("admin"),
            )
        self.assertEqual(context.exception.status_code, 422)

    def test_yerel_gelistirici_buluta_yazamaz(self):
        dev = KimlikBilgisi(kullanici_id="dev", sirket_id="yerel-demo", roller={"gelistirici": True})
        with self.assertRaises(HTTPException) as context:
            calisma_alani_kaydet(CalismaAlaniKaydetIstegi(snapshot=snapshot()), dev)
        self.assertEqual(context.exception.status_code, 409)


if __name__ == "__main__":
    unittest.main()

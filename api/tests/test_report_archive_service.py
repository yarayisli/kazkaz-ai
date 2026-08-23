import unittest
from unittest.mock import patch

from fastapi import HTTPException

from api.models import FinansalGorunum, KimlikBilgisi
from api.report_archive_service import arsiv_raporu_olustur, arsiv_raporu_sil, rapor_arsivle, rapor_listesi


class Snapshot:
    def __init__(self, document, data):
        self.id, self._document, self._data = document.id, document, data
        self.exists = data is not None

    def to_dict(self):
        return self._data


class Document:
    def __init__(self, db, path):
        self.db, self.path, self.id = db, path, path[-1]

    def collection(self, name):
        return Collection(self.db, (*self.path, name))

    def get(self):
        return Snapshot(self, self.db.store.get(self.path))

    def set(self, data):
        self.db.store[self.path] = data

    def delete(self):
        self.db.store.pop(self.path, None)


class Collection:
    def __init__(self, db, path):
        self.db, self.path = db, path

    def document(self, name=None):
        if name is None:
            self.db.counter += 1
            name = f"auto-{self.db.counter}"
        return Document(self.db, (*self.path, name))

    def stream(self):
        return [Snapshot(Document(self.db, key), value) for key, value in self.db.store.items() if key[:-1] == self.path and len(key) == len(self.path) + 1]


class Db:
    def __init__(self):
        self.store, self.counter = {}, 0

    def collection(self, name):
        return Collection(self, (name,))


def user(company="company-a", role="admin"):
    claim = "analist" if role == "analyst" else role
    return KimlikBilgisi(kullanici_id=f"user-{company}-{role}", sirket_id=company, roller={claim: True})


def financial_data():
    return FinansalGorunum(
        sirket_adi="Arşiv Test A.Ş.", sektor="Üretim", donem="2026 Q2", ciro=1_000_000,
        satis_maliyeti=550_000, faaliyet_giderleri=220_000, net_kar=120_000,
        nakit=180_000, kisa_vadeli_borc=140_000, uzun_vadeli_borc=200_000,
        alacaklar=160_000, borclar=100_000, stoklar=90_000, ozkaynak=500_000,
        donen_varliklar=430_000,
    )


class TestReportArchiveService(unittest.TestCase):
    def setUp(self):
        self.db = Db()
        self.patch = patch("api.report_archive_service._db", return_value=self.db)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()

    def test_rapor_sirket_altinda_surumlenir_ve_listelenir(self):
        report_id = rapor_arsivle(financial_data(), user(), "pdf")
        result = rapor_listesi(user())
        self.assertEqual(result["raporlar"][0]["rapor_id"], report_id)
        self.assertEqual(result["raporlar"][0]["ozet"]["netMargin"], 12.0)

    def test_sirketler_arasi_rapor_erisimi_yoktur(self):
        report_id = rapor_arsivle(financial_data(), user("company-a"), "pdf")
        with self.assertRaises(HTTPException) as context:
            arsiv_raporu_olustur(report_id, "pdf", user("company-b", "viewer"))
        self.assertEqual(context.exception.status_code, 404)

    def test_arsiv_raporu_yeniden_uretilir(self):
        report_id = rapor_arsivle(financial_data(), user(), "pdf")
        content = arsiv_raporu_olustur(report_id, "pdf", user(role="viewer"))
        self.assertTrue(content.startswith(b"%PDF"))

    def test_silme_yalniz_admin_ve_cfo(self):
        report_id = rapor_arsivle(financial_data(), user(), "excel")
        with self.assertRaises(HTTPException) as context:
            arsiv_raporu_sil(report_id, user(role="analyst"))
        self.assertEqual(context.exception.status_code, 403)
        self.assertEqual(arsiv_raporu_sil(report_id, user(role="cfo"))["durum"], "silindi")


if __name__ == "__main__":
    unittest.main()

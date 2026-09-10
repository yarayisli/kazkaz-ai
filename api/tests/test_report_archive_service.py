import unittest
from unittest.mock import patch

from fastapi import HTTPException

from api.models import FinansalGorunum, KimlikBilgisi, RaporIstegi
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


class Blob:
    def __init__(self, bucket, path):
        self.bucket, self.path, self.metadata = bucket, path, None

    def upload_from_string(self, content, content_type=None, if_generation_match=None):
        if if_generation_match == 0 and self.path in self.bucket.store:
            raise RuntimeError("nesne zaten var")
        self.bucket.store[self.path] = bytes(content)
        self.bucket.meta[self.path] = {"metadata": self.metadata, "content_type": content_type}

    def download_as_bytes(self):
        return self.bucket.store[self.path]

    def exists(self):
        return self.path in self.bucket.store

    def delete(self):
        self.bucket.store.pop(self.path, None)
        self.bucket.meta.pop(self.path, None)


class Bucket:
    def __init__(self):
        self.store, self.meta = {}, {}

    def blob(self, path):
        return Blob(self, path)


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
        self.bucket = Bucket()
        self.patches = [
            patch("api.report_archive_service._db", return_value=self.db),
            patch("api.report_archive_service._bucket", return_value=self.bucket),
        ]
        for active_patch in self.patches:
            active_patch.start()

    def tearDown(self):
        for active_patch in self.patches:
            active_patch.stop()

    def test_rapor_sirket_altinda_surumlenir_ve_listelenir(self):
        report_id = rapor_arsivle(financial_data(), user(), "pdf")
        result = rapor_listesi(user())
        self.assertEqual(result["raporlar"][0]["rapor_id"], report_id)
        self.assertEqual(result["raporlar"][0]["ozet"]["netMargin"], 12.0)
        self.assertTrue(result["raporlar"][0]["ozgun_cikti"])

    def test_sirketler_arasi_rapor_erisimi_yoktur(self):
        report_id = rapor_arsivle(financial_data(), user("company-a"), "pdf")
        with self.assertRaises(HTTPException) as context:
            arsiv_raporu_olustur(report_id, "pdf", user("company-b", "viewer"))
        self.assertEqual(context.exception.status_code, 404)

    def test_arsiv_raporu_ozgun_baytlari_dondurur(self):
        report_id = rapor_arsivle(financial_data(), user(), "pdf")
        content, bilgi = arsiv_raporu_olustur(report_id, "pdf", user(role="viewer"))
        self.assertTrue(content.startswith(b"%PDF"))
        self.assertFalse(bilgi["yeniden_uretildi"])
        self.assertTrue(bilgi["ozgun_cikti"])

    def test_motor_surumu_degisse_de_ozgun_cikti_degismez(self):
        original = b"%PDF-ozgun-rapor-baytlari"
        report_id = rapor_arsivle(financial_data(), user(), "pdf", original)
        # İndirme anında motor sürümü değişmiş gibi davran.
        with patch("api.report_archive_service.RAPOR_MOTOR_SURUMU", "2.0.0"):
            content, bilgi = arsiv_raporu_olustur(report_id, "pdf", user(role="viewer"))
            liste = rapor_listesi(user())
        self.assertEqual(content, original)
        self.assertFalse(bilgi["yeniden_uretildi"])
        self.assertTrue(bilgi["ozgun_cikti"])
        self.assertEqual(bilgi["motor_surumu_guncel"], "2.0.0")
        self.assertNotEqual(bilgi["motor_surumu_arsiv"], "2.0.0")
        self.assertFalse(liste["raporlar"][0]["guncel_motor"])

    def test_kullaniciya_donen_pdf_ile_arsivlenen_baytlar_aynidir(self):
        from api.main import pdf_raporu

        original = b"%PDF-teslim-edilen-cikti"
        request = RaporIstegi(finansal_veri=financial_data())
        with patch("api.main.pdf_raporu_olustur", return_value=original), patch(
            "api.main.rapor_arsivle", return_value="rpt_same"
        ) as archive:
            response = pdf_raporu(request, user())
        self.assertEqual(response.body, original)
        self.assertIs(archive.call_args.args[3], original)
        self.assertEqual(response.headers["x-kazkaz-report-id"], "rpt_same")

    def test_depo_baytlari_degistiyse_butunluk_kontrolu_reddeder(self):
        report_id = rapor_arsivle(financial_data(), user(), "pdf", b"%PDF-dogru")
        path = next(iter(self.bucket.store))
        self.bucket.store[path] = b"%PDF-degistirilmis"
        with self.assertRaises(HTTPException) as context:
            arsiv_raporu_olustur(report_id, "pdf", user(role="viewer"))
        self.assertEqual(context.exception.status_code, 500)

    def test_baska_sirket_depo_yoluna_yonlendirilmis_kayit_reddedilir(self):
        report_id = rapor_arsivle(financial_data(), user(), "pdf", b"%PDF-dogru")
        report_path = ("companies", "company-a", "reports", report_id)
        self.db.store[report_path]["artifacts"]["pdf"]["storagePath"] = (
            "companies/company-b/reports/rpt_other/original.pdf"
        )
        with self.assertRaises(HTTPException) as context:
            arsiv_raporu_olustur(report_id, "pdf", user(role="viewer"))
        self.assertEqual(context.exception.status_code, 500)

    def test_eski_arsiv_kaydi_uyumluluk_icin_yeniden_uretilir(self):
        report_id = "rpt_legacy"
        self.db.collection("companies").document("company-a").collection("reports").document(report_id).set({
            "companyId": "company-a",
            "engineVersion": "0.9.0",
            "formats": ["pdf"],
            "financialData": financial_data().model_dump(mode="json"),
        })
        with patch("api.report_archive_service.RAPOR_MOTOR_SURUMU", "2.0.0"):
            content, bilgi = arsiv_raporu_olustur(report_id, "pdf", user(role="viewer"))
        self.assertTrue(content.startswith(b"%PDF"))
        self.assertTrue(bilgi["yeniden_uretildi"])
        self.assertFalse(bilgi["ozgun_cikti"])

    def test_silme_yalniz_admin_ve_cfo(self):
        report_id = rapor_arsivle(financial_data(), user(), "excel")
        with self.assertRaises(HTTPException) as context:
            arsiv_raporu_sil(report_id, user(role="analyst"))
        self.assertEqual(context.exception.status_code, 403)
        self.assertEqual(arsiv_raporu_sil(report_id, user(role="cfo"))["durum"], "silindi")
        self.assertEqual(self.bucket.store, {})


if __name__ == "__main__":
    unittest.main()

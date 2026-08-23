import json
import os
import unittest
from unittest.mock import patch

from api.google_sheets_service import (
    GoogleSheetsHatasi,
    google_sheet_dogrula,
    google_sheets_adresini_coz,
    google_sheets_durumu,
)
from api.models import GoogleSheetsIstegi


class _SahteSayfa:
    id = 42
    title = "İşlemler"

    def get_all_values(self):
        return [
            ["Tarih", "Kategori", "Gelir", "Gider"],
            ["2026-01-01", "Satış", "125000", "0"],
            ["2026-01-02", "Kira", "0", "25000"],
        ]


class _SahteKitap:
    sheet1 = _SahteSayfa()

    def worksheet(self, ad):
        if ad != "İşlemler":
            raise RuntimeError("bulunamadı")
        return self.sheet1

    def worksheets(self):
        return [self.sheet1]


class _SahteIstemci:
    def open_by_key(self, sheet_id):
        if sheet_id != "1AbCdEfGhIjKlMnOpQrStUvWxYz":
            raise RuntimeError("yanlış kimlik")
        return _SahteKitap()


class TestGoogleSheetsBaglantisi(unittest.TestCase):
    def setUp(self):
        self.url = "https://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/edit#gid=42"
        self.secret = json.dumps({
            "client_email": "kazkaz-sheets@example.iam.gserviceaccount.com",
            "private_key": "-----BEGIN PRIVATE KEY-----\\nTEST\\n-----END PRIVATE KEY-----\\n",
        })

    def test_resmi_url_kimlik_ve_gid_olarak_cozulur(self):
        self.assertEqual(
            google_sheets_adresini_coz(self.url),
            ("1AbCdEfGhIjKlMnOpQrStUvWxYz", 42),
        )

    def test_benzer_gorunen_kotu_host_reddedilir(self):
        with self.assertRaises(GoogleSheetsHatasi):
            google_sheets_adresini_coz(
                "https://docs.google.com.evil.example/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/edit"
            )

    def test_http_ve_gecersiz_yol_reddedilir(self):
        with self.assertRaises(GoogleSheetsHatasi):
            google_sheets_adresini_coz(
                "http://docs.google.com/spreadsheets/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/edit"
            )
        with self.assertRaises(GoogleSheetsHatasi):
            google_sheets_adresini_coz("https://docs.google.com/document/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/edit")

    def test_durum_gizli_anahtari_aciga_cikarmaz(self):
        with patch.dict(os.environ, {"GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON": self.secret}, clear=False):
            durum = google_sheets_durumu()
        self.assertTrue(durum["yapilandirildi"])
        self.assertEqual(durum["yetki"], "salt_okunur")
        self.assertEqual(durum["servis_hesabi_epostasi"], "kazkaz-sheets@example.iam.gserviceaccount.com")
        self.assertNotIn("private_key", durum)

    def test_yapilandirilmamis_durum_guvenle_bildirilir(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON", None)
            durum = google_sheets_durumu()
        self.assertFalse(durum["yapilandirildi"])
        self.assertIsNone(durum["servis_hesabi_epostasi"])

    def test_sheet_ortak_csv_dogrulama_motoruna_aktarilir(self):
        with patch.dict(os.environ, {"GOOGLE_SHEETS_SERVICE_ACCOUNT_JSON": self.secret}, clear=False):
            sonuc = google_sheet_dogrula(
                GoogleSheetsIstegi(url=self.url),
                istemci_uretici=lambda _bilgi: _SahteIstemci(),
            )
        self.assertEqual(sonuc["ozet"]["gecerli_satirlar"], 2)
        self.assertEqual(sonuc["ozet"]["toplam_gelir"], 125000)
        self.assertEqual(sonuc["ozet"]["toplam_gider"], 25000)
        self.assertEqual(sonuc["dosya"]["tur"], "csv")


if __name__ == "__main__":
    unittest.main()

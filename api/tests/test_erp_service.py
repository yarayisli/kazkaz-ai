import os
import unittest
from unittest.mock import Mock, patch

from api.erp_service import (
    ErpYapilandirmaHatasi,
    LogoSaltOkunurBaglayici,
    erp_baglanti_durumu,
)


LOGO_ENV = {
    "LOGO_API_BASE_URL": "https://erp.example.com/api",
    "LOGO_TOKEN_URL": "https://erp.example.com/oauth/token",
    "LOGO_CLIENT_ID": "client-id",
    "LOGO_CLIENT_SECRET": "cok-gizli-secret",
    "LOGO_COMPANY_CODE": "001",
    "LOGO_READONLY_SCOPE": "ledger.read invoices.read",
}


class TestErpService(unittest.TestCase):
    def test_durum_anahtar_ve_firma_kodu_aciga_cikarmaz(self):
        with patch.dict(os.environ, LOGO_ENV, clear=False):
            durum = erp_baglanti_durumu()
        self.assertEqual(durum["saglayicilar"]["logo"]["durum"], "yapilandirildi")
        self.assertNotIn("cok-gizli-secret", str(durum))
        self.assertNotIn("001", str(durum))
        self.assertEqual(durum["saglayicilar"]["logo"]["yetki"], "salt_okunur")

    def test_eksik_ayar_baglayiciyi_baslatmaz(self):
        with patch.dict(os.environ, {**LOGO_ENV, "LOGO_CLIENT_SECRET": ""}, clear=False):
            with self.assertRaises(ErpYapilandirmaHatasi):
                LogoSaltOkunurBaglayici.ortamdan()

    def test_http_ve_origin_disina_cikan_yol_reddedilir(self):
        with patch.dict(os.environ, {**LOGO_ENV, "LOGO_API_BASE_URL": "http://erp.example.com"}, clear=False):
            with self.assertRaises(ErpYapilandirmaHatasi):
                LogoSaltOkunurBaglayici.ortamdan()

        with patch.dict(os.environ, LOGO_ENV, clear=False):
            baglayici = LogoSaltOkunurBaglayici.ortamdan()
            with self.assertRaises(ErpYapilandirmaHatasi):
                baglayici.salt_okunur_get("../baska-servis")

    @patch("api.erp_service.requests.get")
    @patch("api.erp_service.requests.post")
    def test_logo_istegi_oauth_ve_salt_okunur_get_kullanir(self, post: Mock, get: Mock):
        post.return_value.raise_for_status.return_value = None
        post.return_value.json.return_value = {"access_token": "gecici-token"}
        get.return_value.raise_for_status.return_value = None
        get.return_value.json.return_value = {"items": []}
        with patch.dict(os.environ, LOGO_ENV, clear=False):
            sonuc = LogoSaltOkunurBaglayici.ortamdan().salt_okunur_get("v1/trial-balance")

        self.assertEqual(sonuc, {"items": []})
        self.assertEqual(post.call_args.kwargs["data"]["grant_type"], "client_credentials")
        self.assertEqual(get.call_args.kwargs["headers"]["Authorization"], "Bearer gecici-token")
        self.assertEqual(get.call_args.kwargs["params"]["company"], "001")


if __name__ == "__main__":
    unittest.main()

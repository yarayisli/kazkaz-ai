import os
import unittest
from unittest.mock import patch

from api.readiness import canli_hazirlik_durumu


class TestCanliHazirlik(unittest.TestCase):
    def test_adc_dosyasi_firebase_admin_kimligi_olarak_kabul_edilir(self):
        from tempfile import NamedTemporaryFile

        with NamedTemporaryFile() as kimlik, patch.dict(
            os.environ,
            {
                "FIREBASE_SERVICE_ACCOUNT_JSON": "",
                "GOOGLE_APPLICATION_CREDENTIALS": kimlik.name,
            },
            clear=False,
        ):
            sonuc = canli_hazirlik_durumu()

        self.assertTrue(sonuc["kritik_kontroller"]["firebase_servis_hesabi"])

    def test_kritik_ayarlar_tamamlaninca_hazir(self):
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "KAZKAZ_AUTH_DISABLED": "false",
            "FIREBASE_PROJECT_ID": "kazkaz-live",
            "FIREBASE_SERVICE_ACCOUNT_JSON": "{secret}",
            "CORS_ORIGINS": "https://supermantarik.com",
            "ALLOWED_HOSTS": "supermantarik.com,*.onrender.com",
            "ENFORCE_HTTPS": "true",
            "ENFORCE_PLAN_LIMITS": "true",
            "FIRESTORE_RULES_DEPLOYED": "true",
            "TENANT_ISOLATION_TEST_PASSED": "true",
            "DATA_RETENTION_DAYS": "365",
            "REPORT_RETENTION_DAYS": "365",
            "FINANCIAL_METHODOLOGY_APPROVED": "true",
            "KVKK_REVIEW_APPROVED": "true",
        }, clear=False):
            sonuc = canli_hazirlik_durumu()
        self.assertEqual(sonuc["durum"], "hazir")
        self.assertEqual(sonuc["kritik_eksikler"], [])

    def test_localhost_cors_canlida_eksik_sayilir(self):
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "KAZKAZ_AUTH_DISABLED": "false",
            "FIREBASE_PROJECT_ID": "kazkaz-live",
            "FIREBASE_SERVICE_ACCOUNT_JSON": "{secret}",
            "CORS_ORIGINS": "http://localhost:3000",
            "ALLOWED_HOSTS": "supermantarik.com",
            "ENFORCE_HTTPS": "true",
            "ENFORCE_PLAN_LIMITS": "true",
            "FIRESTORE_RULES_DEPLOYED": "true",
            "TENANT_ISOLATION_TEST_PASSED": "true",
            "DATA_RETENTION_DAYS": "365",
            "FINANCIAL_METHODOLOGY_APPROVED": "true",
            "KVKK_REVIEW_APPROVED": "true",
        }, clear=False):
            sonuc = canli_hazirlik_durumu()
        self.assertEqual(sonuc["durum"], "eksik")
        self.assertIn("canli_cors", sonuc["kritik_eksikler"])

    def test_onay_ve_izolasyon_bayraklari_yoksa_canli_hazir_degil(self):
        with patch.dict(os.environ, {
            "APP_ENV": "production",
            "KAZKAZ_AUTH_DISABLED": "false",
            "FIREBASE_PROJECT_ID": "kazkaz-live",
            "FIREBASE_SERVICE_ACCOUNT_JSON": "{secret}",
            "CORS_ORIGINS": "https://supermantarik.com",
            "ALLOWED_HOSTS": "*",
            "ENFORCE_HTTPS": "false",
            "ENFORCE_PLAN_LIMITS": "true",
            "FIRESTORE_RULES_DEPLOYED": "false",
            "TENANT_ISOLATION_TEST_PASSED": "false",
            "DATA_RETENTION_DAYS": "0",
            "FINANCIAL_METHODOLOGY_APPROVED": "false",
            "KVKK_REVIEW_APPROVED": "false",
        }, clear=False):
            sonuc = canli_hazirlik_durumu()
        self.assertEqual(sonuc["durum"], "eksik")
        self.assertIn("tenant_izolasyon_testi", sonuc["kritik_eksikler"])
        self.assertIn("kvkk_hukuk_onayi", sonuc["kritik_eksikler"])
        self.assertIn("izinli_hostlar", sonuc["kritik_eksikler"])
        self.assertIn("https_zorunlu", sonuc["kritik_eksikler"])


if __name__ == "__main__":
    unittest.main()

import os
import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import HTTPException

from api.models import KimlikBilgisi
from api.subscription_service import (
    abonelik_durumu,
    etkin_plan,
    iade_uygunlugu,
    kamuya_acik_paketler,
    odeme_hazirlik_durumu,
    ozellik_kapisi,
)


class TestPaketKorumalari(unittest.TestCase):
    def test_suresi_dolmus_deneme_free_pakete_doner(self):
        kullanici = KimlikBilgisi(
            kullanici_id="u1", sirket_id="c1", roller={"admin": True},
            plan="trial", deneme_bitis=date.today() - timedelta(days=1),
        )
        self.assertEqual(etkin_plan(kullanici), "free")

    def test_aktif_deneme_pro_ozelliklerini_tasir(self):
        kullanici = KimlikBilgisi(
            kullanici_id="u2", sirket_id="c1", roller={"cfo": True},
            plan="trial", deneme_bitis=date.today() + timedelta(days=1),
        )
        self.assertIn("ai_cfo", abonelik_durumu(kullanici)["ozellikler"])

    def test_canlida_free_kullanici_ai_cfoya_giremez(self):
        kullanici = KimlikBilgisi(
            kullanici_id="u3", sirket_id="c1", roller={"admin": True}, plan="free",
        )
        with patch.dict(os.environ, {"APP_ENV": "production", "ENFORCE_PLAN_LIMITS": "true"}, clear=False):
            with self.assertRaises(HTTPException) as context:
                ozellik_kapisi("ai_cfo")(kullanici)
        self.assertEqual(context.exception.status_code, 403)

    def test_gelistirici_tum_ozelliklere_sahiptir(self):
        kullanici = KimlikBilgisi(kullanici_id="dev", roller={"gelistirici": True})
        self.assertEqual(etkin_plan(kullanici), "uzman")

    def test_odeme_yapilandirilmadan_fiyat_ve_iade_taahhudu_yayinlanmaz(self):
        with patch.dict(os.environ, {
            "PAYMENT_PROVIDER": "yapilandirilmadi",
            "PAYMENT_API_KEY": "",
            "PAYMENT_WEBHOOK_SECRET": "",
            "PRO_MONTHLY_PRICE_KURUS": "49900",
            "SALES_TERMS_VERSION": "",
            "REFUND_POLICY_VERSION": "",
        }, clear=False):
            self.assertEqual(odeme_hazirlik_durumu()["durum"], "pilot")
            paketler = kamuya_acik_paketler()
        self.assertEqual(paketler["paketler"], [])
        self.assertFalse(paketler["iade_taahhudu_yayinda"])

    def test_tum_ticari_kanitlarla_fiyat_yayinlanabilir(self):
        with patch.dict(os.environ, {
            "PAYMENT_PROVIDER": "iyzico",
            "PAYMENT_API_KEY": "test-key",
            "PAYMENT_WEBHOOK_SECRET": "test-webhook",
            "PRO_MONTHLY_PRICE_KURUS": "49900",
            "SALES_TERMS_VERSION": "2026-08-v1",
            "REFUND_POLICY_VERSION": "2026-08-v1",
        }, clear=False):
            paketler = kamuya_acik_paketler()
        self.assertEqual(paketler["durum"], "hazir")
        self.assertEqual(paketler["paketler"][0]["aylik_fiyat_kurus"], 49900)
        self.assertTrue(paketler["iade_taahhudu_yayinda"])

    def test_otuz_gunluk_iade_penceresi_sinirda_dahildir(self):
        odeme = datetime(2026, 8, 1, tzinfo=timezone.utc)
        with patch.dict(os.environ, {"REFUND_WINDOW_DAYS": "30"}, clear=False):
            sinir = iade_uygunlugu(odeme, simdi=odeme + timedelta(days=30))
            gec = iade_uygunlugu(odeme, simdi=odeme + timedelta(days=30, seconds=1))
            iade_edilmis = iade_uygunlugu(odeme, simdi=odeme + timedelta(days=1), daha_once_iade_edildi=True)
        self.assertTrue(sinir["uygun"])
        self.assertFalse(gec["uygun"])
        self.assertEqual(iade_edilmis["gerekce"], "daha_once_iade_edildi")


if __name__ == "__main__":
    unittest.main()

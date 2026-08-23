import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import uygulama
from api.telemetry import operasyonu_olc, performans_ozeti, telemetriyi_sifirla


class TestTelemetri(unittest.TestCase):
    def setUp(self):
        telemetriyi_sifirla()
        self.client = TestClient(uygulama)

    def tearDown(self):
        telemetriyi_sifirla()

    def test_asgari_ornek_altinda_hiz_iddiasi_yayinlanmaz(self):
        with patch.dict(os.environ, {"PUBLIC_PERFORMANCE_MIN_SAMPLES": "3"}, clear=False):
            with operasyonu_olc("finansal_denetim", satir_sayisi=1):
                pass
            ozet = performans_ozeti(kamuya_acik=True)

        self.assertEqual(ozet["durum"], "yetersiz_veri")
        self.assertNotIn("p50_ms", ozet)
        self.assertNotIn("orneklem", ozet)
        self.assertFalse(ozet["kisisel_veri_toplanir"])

    def test_yeterli_ornekte_yuzdelikler_ve_basari_orani_yayinlanir(self):
        with patch.dict(os.environ, {"PUBLIC_PERFORMANCE_MIN_SAMPLES": "3"}, clear=False):
            for _ in range(3):
                with operasyonu_olc("zaman_serisi", satir_sayisi=20):
                    pass
            ozet = performans_ozeti(kamuya_acik=True)

        self.assertEqual(ozet["durum"], "yayina_hazir")
        self.assertEqual(ozet["orneklem"], "3+")
        self.assertEqual(ozet["basari_orani"], 100.0)
        self.assertGreaterEqual(ozet["p95_ms"], ozet["p50_ms"])
        self.assertNotIn("operasyonlar", ozet)

    def test_istisna_basarisiz_ve_http_durumu_ile_kaydedilir(self):
        with self.assertRaisesRegex(ValueError, "test hatasi"):
            with operasyonu_olc("dosya_dogrulama", istek_bayti=100):
                raise ValueError("test hatasi")

        ayrintili = performans_ozeti()
        operasyon = ayrintili["operasyonlar"]["dosya_dogrulama"]
        self.assertEqual(operasyon["orneklem"], 1)
        self.assertEqual(operasyon["basari_orani"], 0.0)

    def test_public_performans_ucu_kisisel_veri_dondurmez(self):
        with patch.dict(os.environ, {"PUBLIC_PERFORMANCE_MIN_SAMPLES": "1"}, clear=False):
            with operasyonu_olc("finansal_denetim", satir_sayisi=1):
                pass
            yanit = self.client.get("/api/public/performance")

        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.json()["durum"], "yayina_hazir")
        self.assertNotIn("kullanici", yanit.text.lower())
        self.assertNotIn("sirket", yanit.text.lower())
        self.assertEqual(yanit.headers["cache-control"], "no-store")


if __name__ == "__main__":
    unittest.main()

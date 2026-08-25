import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.auth import mevcut_kullanici, mevcut_sirket_uyesi
from api.main import uygulama
from api.models import KimlikBilgisi
from api.security_middleware import hiz_limitlerini_sifirla


class TestApi(unittest.TestCase):
    def setUp(self):
        hiz_limitlerini_sifirla()
        self.client = TestClient(uygulama)

    def tearDown(self):
        hiz_limitlerini_sifirla()
        uygulama.dependency_overrides.clear()

    def test_sirket_olusturma_kimligi_sunucu_servisine_iletir(self):
        kullanici = KimlikBilgisi(kullanici_id="user-company", eposta="cfo@example.com")
        uygulama.dependency_overrides[mevcut_kullanici] = lambda: kullanici
        beklenen = {
            "durum": "olusturuldu",
            "sirket_id": "cmp_test",
            "sirket_adi": "Test A.Ş.",
            "rol": "admin",
            "token_yenile": True,
        }
        with patch("api.main.sirket_olustur", return_value=beklenen) as servis:
            yanit = self.client.post("/api/v1/sirket/olustur", json={
                "sirket_adi": "Test A.Ş.",
                "sektor": "teknoloji",
                "calisan_olcegi": "10-49",
                "ana_hedef": "nakit",
                "ana_zorluk": "tahsilat",
                "veri_kaynagi": "excel",
                "veri_kapsami": ["gelir_tablosu", "nakit", "alacak"],
                "para_birimi": "TRY",
                "mali_yil_baslangic_ayi": 1,
            })
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.json(), beklenen)
        self.assertEqual(servis.call_args.args[1].kullanici_id, "user-company")
        self.assertEqual(servis.call_args.args[0].ana_hedef, "nakit")
        self.assertEqual(servis.call_args.args[0].veri_kapsami, ["gelir_tablosu", "nakit", "alacak"])

    def test_sirket_adi_asgari_uzunluk_ister(self):
        kullanici = KimlikBilgisi(kullanici_id="user-company")
        uygulama.dependency_overrides[mevcut_kullanici] = lambda: kullanici
        yanit = self.client.post("/api/v1/sirket/olustur", json={"sirket_adi": "X"})
        self.assertEqual(yanit.status_code, 422)

    def test_calisma_alani_yasam_dongusu_uclari_sirket_kullanicisini_iletir(self):
        kullanici = KimlikBilgisi(
            kullanici_id="workspace-admin",
            sirket_id="company-a",
            roller={"admin": True},
        )
        uygulama.dependency_overrides[mevcut_sirket_uyesi] = lambda: kullanici
        snapshot = {
            "financialData": {}, "cashFlow": [], "debts": [], "customers": [],
            "budget": [], "financialAudit": None, "isSampleData": False,
        }
        with patch("api.main.calisma_alani_kaydet", return_value={"durum": "kaydedildi"}) as kaydet:
            yanit = self.client.post(
                "/api/v1/veri/calisma-alani/kaydet",
                json={"schema_version": 2, "snapshot": snapshot},
            )
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(kaydet.call_args.args[1].sirket_id, "company-a")

        with patch("api.main.calisma_alani_sil", return_value={"durum": "silindi"}) as sil:
            yanit = self.client.post("/api/v1/veri/calisma-alani/sil", json={})
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(sil.call_args.args[0].kullanici_id, "workspace-admin")

    def test_saglik_ucu_acik(self):
        yanit = self.client.get("/api/health")
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.json()["durum"], "ok")
        self.assertEqual(yanit.headers["x-content-type-options"], "nosniff")
        self.assertEqual(yanit.headers["cache-control"], "no-store")
        self.assertIn("frame-ancestors 'none'", yanit.headers["content-security-policy"])
        self.assertEqual(yanit.headers["cross-origin-opener-policy"], "same-origin-allow-popups")
        self.assertEqual(yanit.headers["cross-origin-resource-policy"], "same-origin")
        self.assertGreaterEqual(len(yanit.headers["x-request-id"]), 8)

    def test_gecerli_istek_kimligi_korunur_gecersizi_degistirilir(self):
        korunan = self.client.get("/api/health", headers={"X-Request-ID": "pilot-test-123"})
        degistirilen = self.client.get("/api/health", headers={"X-Request-ID": "uygunsuz kimlik!"})
        self.assertEqual(korunan.headers["x-request-id"], "pilot-test-123")
        self.assertNotEqual(degistirilen.headers["x-request-id"], "uygunsuz kimlik!")

    @unittest.skipUnless(
        os.path.exists(os.path.join(os.path.dirname(__file__), "..", "..", "web", "dist", "index.html")),
        "web/dist henüz derlenmedi — CI'da `npm run build` yapıldığında etkinleşir.",
    )
    def test_web_kabugu_eski_derleme_dosyalarini_onbellekte_tutmaz(self):
        yanit = self.client.get("/")
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.headers["cache-control"], "no-cache")

    def test_buyuk_istek_govdesi_reddedilir(self):
        with patch.dict(os.environ, {"MAX_REQUEST_BYTES": "80"}, clear=False):
            yanit = self.client.post(
                "/api/v1/finans/denetim",
                json={"ciro": 100_000, "net_kar": 10_000, "sirket_adi": "X" * 200},
            )
        self.assertEqual(yanit.status_code, 413)
        self.assertEqual(yanit.headers["x-content-type-options"], "nosniff")
        self.assertGreaterEqual(len(yanit.headers["x-request-id"]), 8)

    def test_dakikalik_hiz_limiti_uygulanir(self):
        with patch.dict(
            os.environ,
            {
                "API_RATE_LIMIT_PER_MINUTE": "1",
                "KAZKAZ_AUTH_DISABLED": "true",
                "APP_ENV": "development",
            },
            clear=False,
        ):
            ilk = self.client.get("/api/v1/ai/durum")
            ikinci = self.client.get("/api/v1/ai/durum")
        self.assertEqual(ilk.status_code, 200)
        self.assertEqual(ikinci.status_code, 429)
        self.assertEqual(ikinci.headers["retry-after"], "60")

    def test_korumali_uc_token_ister(self):
        with patch.dict(os.environ, {"KAZKAZ_AUTH_DISABLED": "false"}, clear=False):
            yanit = self.client.post(
                "/api/v1/finans/denetim",
                json={"ciro": 100_000, "net_kar": 10_000},
            )
        self.assertEqual(yanit.status_code, 401)

    def test_yerel_gelistirmede_denetim_calısır(self):
        with patch.dict(
            os.environ,
            {"KAZKAZ_AUTH_DISABLED": "true", "APP_ENV": "development"},
            clear=False,
        ):
            yanit = self.client.post(
                "/api/v1/finans/denetim",
                json={
                    "sirket_adi": "API Test",
                    "ciro": 100_000,
                    "net_kar": 10_000,
                    "nakit": 20_000,
                    "kisa_vadeli_borc": 10_000,
                },
            )
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.json()["metrikler"]["net_kar_marji"], 10.0)

    def test_ai_durumu_anahtarlari_aciga_cikarmaz(self):
        with patch.dict(
            os.environ,
            {
                "KAZKAZ_AUTH_DISABLED": "true",
                "APP_ENV": "development",
                "GROQ_API_KEY": "gsk-cok-gizli",
            },
            clear=False,
        ):
            yanit = self.client.get("/api/v1/ai/durum")
        self.assertEqual(yanit.status_code, 200)
        self.assertNotIn("gsk-cok-gizli", yanit.text)
        self.assertEqual(yanit.json()["finans_motoru"], "aktif")

    def test_cfo_ajan_analizi_yerelde_calisir(self):
        with patch.dict(
            os.environ,
            {"KAZKAZ_AUTH_DISABLED": "true", "APP_ENV": "development"},
            clear=False,
        ):
            yanit = self.client.post(
                "/api/v1/cfo/ajan-analizi",
                json={
                    "finansal_veri": {
                        "sirket_adi": "API Ajan Test",
                        "ciro": 500000,
                        "satis_maliyeti": 200000,
                        "faaliyet_giderleri": 150000,
                        "net_kar": 100000,
                        "nakit": 120000,
                        "kisa_vadeli_borc": 100000,
                        "ozkaynak": 300000,
                    },
                    "nakit_akisi": [],
                    "borclar": [],
                },
            )
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.json()["durum"], "aktif_kontrollu")

    def test_gelismis_ajanlar_eksik_veriyi_aciklar(self):
        with patch.dict(
            os.environ,
            {"KAZKAZ_AUTH_DISABLED": "true", "APP_ENV": "development"},
            clear=False,
        ):
            yanit = self.client.post(
                "/api/v1/cfo/gelismis-ajanlar",
                json={
                    "finansal_veri": {"ciro": 0, "net_kar": 0},
                    "rapor_tarihi": "2026-04-30",
                },
            )
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.json()["ozet"]["veri_bekliyor"], 6)

    def test_google_sheets_durumu_sirket_uyesine_aciktir(self):
        with patch.dict(
            os.environ,
            {"KAZKAZ_AUTH_DISABLED": "true", "APP_ENV": "development"},
            clear=False,
        ):
            yanit = self.client.get("/api/v1/veri/google-sheets/durum")
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.json()["yetki"], "salt_okunur")

    def test_geri_bildirim_sirket_kapsaminda_servise_iletilir(self):
        with patch.dict(os.environ, {"KAZKAZ_AUTH_DISABLED": "true", "APP_ENV": "development"}, clear=False):
            with patch("api.main.geri_bildirim_kaydet", return_value={"durum": "alindi", "kayit_id": "fb_1"}) as servis:
                yanit = self.client.post("/api/v1/geri-bildirim", json={
                    "kategori": "hata", "mesaj": "Rapor ekranında beklenmeyen bir sonuç gördüm.", "sayfa": "overview",
                })
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(servis.call_args.args[1].sirket_id, "yerel-demo")


if __name__ == "__main__":
    unittest.main()

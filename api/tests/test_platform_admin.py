import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from api.auth import platform_yoneticisi, sirket_uyeligini_dogrula
from api.main import uygulama
from api.models import KimlikBilgisi
from api.platform_admin_service import _aktivite_ozeti, _eposta_maskele, platform_olaylari, platform_sirketleri


class TestPlatformAdminYetkisi(unittest.TestCase):
    def test_sirket_admini_uretimde_platform_yoneticisi_degildir(self):
        kullanici = KimlikBilgisi(
            kullanici_id="u1", eposta="admin@sirket.test", eposta_dogrulandi=True,
            sirket_id="c1", roller={"admin": True},
        )
        with patch.dict(os.environ, {"APP_ENV": "production", "PLATFORM_ADMIN_EMAILS": ""}, clear=False):
            with self.assertRaises(HTTPException) as hata:
                platform_yoneticisi(kullanici)
        self.assertEqual(hata.exception.status_code, 403)

    def test_dogrulanmis_izinli_eposta_kabul_edilir(self):
        kullanici = KimlikBilgisi(
            kullanici_id="u1", eposta="owner@kazkaz.test", eposta_dogrulandi=True,
            roller={},
        )
        with patch.dict(os.environ, {"APP_ENV": "production", "PLATFORM_ADMIN_EMAILS": "owner@kazkaz.test"}, clear=False):
            self.assertEqual(platform_yoneticisi(kullanici).kullanici_id, "u1")

    def test_platform_admin_claimi_kabul_edilir(self):
        kullanici = KimlikBilgisi(kullanici_id="u1", roller={"platform_admin": True})
        with patch.dict(os.environ, {"APP_ENV": "production", "PLATFORM_ADMIN_EMAILS": ""}, clear=False):
            self.assertEqual(platform_yoneticisi(kullanici).kullanici_id, "u1")

    def test_askidaki_sirket_finans_uclarina_giremez(self):
        kullanici = KimlikBilgisi(
            kullanici_id="u1", sirket_id="c1", roller={"admin": True}, sirket_durumu="suspended",
        )
        with self.assertRaises(HTTPException) as hata:
            sirket_uyeligini_dogrula(kullanici)
        self.assertEqual(hata.exception.status_code, 403)


class TestPlatformAdminVeriMinimizasyonu(unittest.TestCase):
    def test_eposta_platform_panelinde_maskelenir(self):
        self.assertEqual(_eposta_maskele("owner@example.com"), "o***@e***.com")
        self.assertNotIn("owner", _eposta_maskele("owner@example.com"))

    def test_aktivite_ozeti_finansal_deger_tasimaz(self):
        sonuc = _aktivite_ozeti([
            {"action": "workspace.save", "createdAt": "2026-08-21T12:00:00+00:00", "revenue": 1_000_000},
            {"action": "report.archive", "createdAt": "2026-08-21T13:00:00+00:00", "netProfit": 90_000},
        ])
        self.assertEqual(sonuc["rapor_arsivleme"], 1)
        self.assertNotIn("revenue", sonuc)
        self.assertNotIn("netProfit", sonuc)

    def test_firestore_yokken_guvenli_bos_liste_doner(self):
        with patch("api.platform_admin_service._db", side_effect=RuntimeError("gizli hata")):
            sirketler = platform_sirketleri()
            olaylar = platform_olaylari()
        self.assertFalse(sirketler["finansal_veri_gosterilir"])
        self.assertFalse(olaylar["mesaj_icerigi_gosterilir"])
        self.assertNotIn("gizli hata", str(sirketler))

    def test_yerel_erisim_ucu_finansal_veri_yetkisi_vermez(self):
        with patch.dict(os.environ, {"APP_ENV": "development", "KAZKAZ_AUTH_DISABLED": "true"}, clear=False):
            with TestClient(uygulama) as istemci:
                yanit = istemci.get("/api/v1/platform-admin/erisim")
        self.assertEqual(yanit.status_code, 200)
        self.assertFalse(yanit.json()["finansal_veri_erisimi"])

    def test_ozet_finansal_deger_tasimaz(self):
        sayac = {"toplam_sirket": 1, "finansal_veri_gosterilir": False}
        with patch.dict(os.environ, {"APP_ENV": "development", "KAZKAZ_AUTH_DISABLED": "true"}, clear=False), \
             patch("api.main.platform_sayaclari", return_value=sayac):
            with TestClient(uygulama) as istemci:
                yanit = istemci.get("/api/v1/platform-admin/ozet")
        self.assertEqual(yanit.status_code, 200)
        govde = yanit.json()
        self.assertFalse(govde["gizlilik"]["finansal_veri_gosterilir"])
        self.assertNotIn("ciro", str(govde).lower())
        self.assertNotIn("net_kar", str(govde).lower())

    def test_sirket_guncelleme_ucu_yetkili_servisi_cagirir(self):
        sonuc = {"durum": "guncellendi", "sirket_id": "company-1", "degisiklikler": {"plan": "pro"}}
        with patch.dict(os.environ, {"APP_ENV": "development", "KAZKAZ_AUTH_DISABLED": "true"}, clear=False), \
             patch("api.main.platform_sirketini_guncelle", return_value=sonuc) as servis:
            with TestClient(uygulama) as istemci:
                yanit = istemci.post("/api/v1/platform-admin/sirket-guncelle", json={"sirket_id": "company-1", "plan": "pro"})
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.json()["degisiklikler"]["plan"], "pro")
        servis.assert_called_once()

    def test_bos_sirket_degisikligi_reddedilir(self):
        with patch.dict(os.environ, {"APP_ENV": "development", "KAZKAZ_AUTH_DISABLED": "true"}, clear=False):
            with TestClient(uygulama) as istemci:
                yanit = istemci.post("/api/v1/platform-admin/sirket-guncelle", json={"sirket_id": "company-1"})
        self.assertEqual(yanit.status_code, 422)

    def test_sirket_detayi_yetkili_servisi_cagirir(self):
        sonuc = {"durum": "hazir", "gizlilik": {"finansal_veri_gosterilir": False}}
        with patch.dict(os.environ, {"APP_ENV": "development", "KAZKAZ_AUTH_DISABLED": "true"}, clear=False), \
             patch("api.main.platform_sirket_detayi", return_value=sonuc) as servis:
            with TestClient(uygulama) as istemci:
                yanit = istemci.get("/api/v1/platform-admin/sirket/company-1")
        self.assertEqual(yanit.status_code, 200)
        self.assertFalse(yanit.json()["gizlilik"]["finansal_veri_gosterilir"])
        servis.assert_called_once_with("company-1")

    def test_oturum_sonlandirma_gerekcesiz_reddedilir(self):
        with patch.dict(os.environ, {"APP_ENV": "development", "KAZKAZ_AUTH_DISABLED": "true"}, clear=False):
            with TestClient(uygulama) as istemci:
                yanit = istemci.post("/api/v1/platform-admin/sirket-eylemi", json={
                    "sirket_id": "company-1", "eylem": "oturumlari_sonlandir", "gerekce": "kisa",
                })
        self.assertEqual(yanit.status_code, 422)

    def test_oturum_sonlandirma_denetimli_servisi_cagirir(self):
        sonuc = {"durum": "tamamlandi", "sirket_id": "company-1", "eylem": "oturumlari_sonlandir", "etkilenen_kullanici": 3, "basarisiz_kullanici": 0}
        with patch.dict(os.environ, {"APP_ENV": "development", "KAZKAZ_AUTH_DISABLED": "true"}, clear=False), \
             patch("api.main.platform_sirket_eylemi", return_value=sonuc) as servis:
            with TestClient(uygulama) as istemci:
                yanit = istemci.post("/api/v1/platform-admin/sirket-eylemi", json={
                    "sirket_id": "company-1", "eylem": "oturumlari_sonlandir", "gerekce": "Güvenlik incelemesi gerekiyor",
                })
        self.assertEqual(yanit.status_code, 200)
        self.assertEqual(yanit.json()["etkilenen_kullanici"], 3)
        servis.assert_called_once()

    def test_geri_bildirim_durumu_mesaj_govdesiz_guncellenir(self):
        sonuc = {"durum": "guncellendi", "sirket_id": "company-1", "geri_bildirim_id": "fb-1", "geri_bildirim_durumu": "in_review"}
        with patch.dict(os.environ, {"APP_ENV": "development", "KAZKAZ_AUTH_DISABLED": "true"}, clear=False), \
             patch("api.main.platform_geri_bildirim_durumu", return_value=sonuc) as servis:
            with TestClient(uygulama) as istemci:
                yanit = istemci.post("/api/v1/platform-admin/geri-bildirim-durumu", json={
                    "sirket_id": "company-1", "geri_bildirim_id": "fb-1", "durum": "in_review",
                })
        self.assertEqual(yanit.status_code, 200)
        self.assertNotIn("mesaj", yanit.json())
        servis.assert_called_once()


if __name__ == "__main__":
    unittest.main()

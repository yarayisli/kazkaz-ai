import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from google.auth.exceptions import DefaultCredentialsError

from api.auth import mevcut_kullanici, sirket_uyeligini_dogrula
from api.models import KimlikBilgisi


class TestSirketYetkilendirmesi(unittest.TestCase):
    def test_production_ortaminda_yerel_bypass_etkisizdir(self):
        with patch.dict(
            os.environ,
            {"APP_ENV": "production", "KAZKAZ_AUTH_DISABLED": "true"},
            clear=False,
        ), self.assertRaises(HTTPException) as context:
            mevcut_kullanici(authorization="")
        self.assertEqual(context.exception.status_code, 401)

    def test_yerel_gelistirici_kontrollu_bypass_kullanabilir(self):
        kullanici = KimlikBilgisi(
            kullanici_id="dev",
            sirket_id="yerel-demo",
            roller={"gelistirici": True},
        )
        self.assertEqual(sirket_uyeligini_dogrula(kullanici), kullanici)

    def test_gercek_token_yerel_bypasstan_once_gelir(self):
        firebase_app = MagicMock()
        with patch.dict(
            os.environ,
            {"APP_ENV": "development", "KAZKAZ_AUTH_DISABLED": "true"},
            clear=False,
        ), patch("api.auth._firebase_uygulamasi", return_value=firebase_app), patch(
            "firebase_admin.auth.verify_id_token",
            return_value={"uid": "firebase-user", "email": "cfo@example.com", "role": "admin"},
        ):
            kullanici = mevcut_kullanici("Bearer gercek-token")
        self.assertEqual(kullanici.kullanici_id, "firebase-user")
        self.assertTrue(kullanici.roller["admin"])
        self.assertFalse(kullanici.roller.get("gelistirici", False))

    @patch("api.auth._firebase_uygulamasi")
    @patch("firebase_admin._token_gen.TokenVerifier")
    @patch("firebase_admin.auth.verify_id_token")
    def test_yerelde_admin_kimligi_yoksa_imza_dogrulayici_kullanilir(self, dogrula, token_verifier, uygulama):
        uygulama.return_value.credential.get_credential.side_effect = DefaultCredentialsError()
        token_verifier.return_value.verify_id_token.return_value = {
            "uid": "firebase-user",
            "email": "test@example.com",
        }

        with patch.dict(os.environ, {"APP_ENV": "development", "KAZKAZ_AUTH_DISABLED": "true"}):
            kullanici = mevcut_kullanici("Bearer gercek-token")

        self.assertEqual(kullanici.kullanici_id, "firebase-user")
        token_verifier.assert_called_once_with(uygulama.return_value)
        token_verifier.return_value.verify_id_token.assert_called_once_with("gercek-token")
        dogrula.assert_not_called()

    @patch("api.auth._firebase_uygulamasi")
    @patch("firebase_admin.auth.verify_id_token")
    def test_uretimde_iptal_kontrolu_zorunludur(self, dogrula, uygulama):
        dogrula.return_value = {"uid": "firebase-user", "email": "test@example.com"}

        with patch.dict(os.environ, {"APP_ENV": "production", "KAZKAZ_AUTH_DISABLED": "false"}):
            kullanici = mevcut_kullanici("Bearer gercek-token")

        self.assertEqual(kullanici.kullanici_id, "firebase-user")
        self.assertTrue(dogrula.call_args.kwargs["check_revoked"])

    def test_sirket_claimi_olmayan_kullanici_reddedilir(self):
        with self.assertRaises(HTTPException) as context:
            sirket_uyeligini_dogrula(
                KimlikBilgisi(kullanici_id="user-1", roller={"cfo": True})
            )
        self.assertEqual(context.exception.status_code, 403)

    def test_atanmis_rolu_olmayan_uye_reddedilir(self):
        with self.assertRaises(HTTPException) as context:
            sirket_uyeligini_dogrula(
                KimlikBilgisi(
                    kullanici_id="user-2",
                    sirket_id="company-a",
                    roller={"member": True},
                )
            )
        self.assertEqual(context.exception.status_code, 403)

    def test_sirket_ve_rol_claimi_olan_uye_kabul_edilir(self):
        kullanici = KimlikBilgisi(
            kullanici_id="user-3",
            sirket_id="company-a",
            roller={"analist": True},
        )
        self.assertEqual(sirket_uyeligini_dogrula(kullanici), kullanici)


class TestFirestoreKuralSozlesmesi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = (Path(__file__).parents[2] / "firestore.rules").read_text(encoding="utf-8")

    def test_eski_kullanici_kapsamli_finans_yolu_kapali(self):
        self.assertIn("match /financialRecords/{kayitId}", self.rules)
        self.assertIn("allow read, write: if false", self.rules)

    def test_finans_kaydi_sirket_uyeligi_ve_rol_ister(self):
        self.assertIn("match /companies/{sirketId}", self.rules)
        self.assertIn("function sirketUyesi(sirketId)", self.rules)
        self.assertIn("function finansYazabilir(sirketId)", self.rules)
        self.assertIn("request.resource.data.companyId == sirketId", self.rules)

    def test_yeni_kullanici_kendini_cfo_yapamaz(self):
        self.assertIn("request.resource.data.role == 'member'", self.rules)
        self.assertNotIn("request.resource.data.role == 'cfo'", self.rules)

    def test_calisma_alani_sirket_uyeligi_ve_yazma_rolu_ister(self):
        self.assertIn("match /workspaces/{calismaAlaniId}", self.rules)
        workspace_kurali = self.rules.split("match /workspaces/{calismaAlaniId}", 1)[1].split("}", 1)[0]
        self.assertIn("allow read, write: if false", workspace_kurali)

    def test_sirket_uyeligi_taninmis_rol_ister(self):
        self.assertIn("in ['admin', 'cfo', 'analyst', 'viewer']", self.rules)

    def test_kullanici_kendi_planini_ve_sirketini_degistiremez(self):
        self.assertIn(
            "affectedKeys().hasOnly(['displayName', 'photoURL'])",
            self.rules,
        )

    def test_finans_kaydi_sahibi_degistirilemez(self):
        self.assertIn("request.resource.data.userId == resource.data.userId", self.rules)
        self.assertIn("resource.data.userId == request.auth.uid", self.rules)

    def test_geri_bildirim_istemciden_dogrudan_yazilamaz(self):
        self.assertIn("match /feedback/{geriBildirimId}", self.rules)
        self.assertIn("allow read, write: if false", self.rules)

    def test_rapor_davet_ve_davet_indeksi_istemciye_kapalidir(self):
        for yol in ("match /reports/{raporId}", "match /invitations/{davetId}", "match /invitationIndex/{davetId}"):
            with self.subTest(yol=yol):
                self.assertIn(yol, self.rules)


if __name__ == "__main__":
    unittest.main()

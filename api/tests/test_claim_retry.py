"""Bekleyen yetki işi geçmiş rolü veya kaldırılmış üyeliği geri veremez."""
import unittest
from unittest.mock import patch
from api.tests.test_membership_service import Db, Document, Collection, user
from api.platform_admin_service import platform_bekleyen_claimleri_yeniden_dene


class TestClaimRetry(unittest.TestCase):
    def setUp(self):
        self.db = Db()
        self.db.store[("companies", "company-a")] = {"status": "active", "plan": "pro"}
        self.queue = ("companies", "company-a", "bekleyenClaimGuncellemeleri", "target")
        self.db.store[self.queue] = {"role": "admin"}
        self.member = ("companies", "company-a", "members", "target")
        self.db.store[self.member] = {"role": "viewer"}
        self.db.store[("users", "target")] = {"companyId": "company-a"}

    def run_retry(self):
        with patch("api.platform_admin_service._db", return_value=self.db), \
             patch("api.platform_admin_service._firebase_uygulamasi", return_value="app"), \
             patch("api.platform_admin_service._uye_claimini_yenile", return_value=True) as update, \
             patch.object(Collection, "limit", lambda col, n: col, create=True), \
             patch.object(Document, "delete", lambda doc: doc.db.store.pop(doc.path, None), create=True):
            result = platform_bekleyen_claimleri_yeniden_dene("company-a", user())
            return result, update.call_args_list

    def test_rol_dusurulduyse_guncel_rol_kullanilir(self):
        result, calls = self.run_retry()
        self.assertEqual(calls[0].args[3], "viewer")
        self.assertEqual(result["cozulen_uye"], 1)
        self.assertNotIn(self.queue, self.db.store)

    def test_cikarilan_uye_geri_eklenmez(self):
        del self.db.store[self.member]
        _, calls = self.run_retry()
        self.assertEqual(calls, [])
        self.assertNotIn(self.queue, self.db.store)

    def test_baska_sirkete_gecen_kullanicinin_claimi_degismez(self):
        self.db.store[("users", "target")]["companyId"] = "company-b"
        _, calls = self.run_retry()
        self.assertEqual(calls, [])

    def test_profil_yoksa_yetki_verilmez(self):
        del self.db.store[("users", "target")]
        _, calls = self.run_retry()
        self.assertEqual(calls, [])

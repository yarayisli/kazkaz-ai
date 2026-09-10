import unittest
from unittest.mock import MagicMock, patch

from api.company_service import _claimleri_guncelle


class TestSirketClaimleri(unittest.TestCase):
    @patch("api.company_service.firebase_auth.set_custom_user_claims")
    @patch("api.company_service.firebase_auth.get_user")
    def test_rol_degisiminde_eski_boolean_yetkiler_temizlenir(self, get_user, set_claims):
        get_user.return_value.custom_claims = {
            "companyId": "eski-sirket",
            "admin": True,
            "cfo": True,
            "analist": True,
            "viewer": True,
            "platform_admin": True,
        }
        app = MagicMock()

        _claimleri_guncelle("u1", "yeni-sirket", "viewer", app, plan="pro")

        guncel = set_claims.call_args.args[1]
        self.assertEqual(guncel["company_id"], "yeni-sirket")
        self.assertEqual(guncel["role"], "viewer")
        self.assertEqual(guncel["plan"], "pro")
        self.assertTrue(guncel["platform_admin"])
        for eski in ("companyId", "admin", "cfo", "analist", "viewer"):
            self.assertNotIn(eski, guncel)
        set_claims.assert_called_once_with("u1", guncel, app=app)


if __name__ == "__main__":
    unittest.main()

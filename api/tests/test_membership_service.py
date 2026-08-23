import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from api.membership_service import daveti_kabul_et, uye_cikar, uye_davet_et, uye_rolunu_guncelle
from api.models import KimlikBilgisi, UyeCikarmaIstegi, UyeDavetIstegi, UyeRolGuncellemeIstegi


class Snapshot:
    def __init__(self, document, data):
        self.id = document.path[-1]
        self.reference = document
        self._data = data
        self.exists = data is not None

    def to_dict(self):
        return self._data


class Document:
    def __init__(self, db, path):
        self.db, self.path = db, path
        self.id = path[-1]
        self.reference = self

    def collection(self, name):
        return Collection(self.db, (*self.path, name))

    def get(self):
        return Snapshot(self, self.db.store.get(self.path))

    def set(self, data, merge=False):
        current = self.db.store.get(self.path, {}) if merge else {}
        self.db.store[self.path] = {**current, **data}


class Collection:
    def __init__(self, db, path):
        self.db, self.path = db, path

    def document(self, name=None):
        if name is None:
            self.db.counter += 1
            name = f"auto-{self.db.counter}"
        return Document(self.db, (*self.path, name))

    def stream(self):
        target_len = len(self.path) + 1
        return [Snapshot(Document(self.db, key), value) for key, value in self.db.store.items() if len(key) == target_len and key[:-1] == self.path]


class Batch:
    def __init__(self, db):
        self.db, self.operations = db, []

    def set(self, ref, data, merge=False):
        self.operations.append(("set", ref, data, merge))
        return self

    def delete(self, ref):
        self.operations.append(("delete", ref, None, False))
        return self

    def commit(self):
        for operation, ref, data, merge in self.operations:
            if operation == "delete":
                self.db.store.pop(ref.path, None)
            else:
                current = self.db.store.get(ref.path, {}) if merge else {}
                self.db.store[ref.path] = {**current, **data}


class Db:
    def __init__(self):
        self.store, self.counter = {}, 0

    def collection(self, name):
        return Collection(self, (name,))

    def batch(self):
        return Batch(self)


def user(role="admin", company="company-a", email="admin@example.com", verified=True, uid=None):
    role_claim = "analist" if role == "analyst" else role
    return KimlikBilgisi(
        kullanici_id=uid or f"user-{role}", eposta=email, eposta_dogrulandi=verified,
        sirket_id=company, roller={role_claim: True} if role else {},
    )


class TestMembershipService(unittest.TestCase):
    def setUp(self):
        self.db = Db()
        self.db.store[("companies", "company-a")] = {"name": "Test A.Ş.", "plan": "trial"}
        self.db.store[("companies", "company-a", "members", "user-admin")] = {"email": "admin@example.com", "role": "admin"}
        self.db_patch = patch("api.membership_service._db", return_value=self.db)
        self.db_patch.start()

    def tearDown(self):
        self.db_patch.stop()

    def test_yalniz_admin_davet_olusturabilir(self):
        with self.assertRaises(HTTPException) as context:
            uye_davet_et(UyeDavetIstegi(eposta="cfo@example.com", rol="cfo"), user("cfo"))
        self.assertEqual(context.exception.status_code, 403)

    def test_davet_tenant_altinda_ve_indekste_olusturulur(self):
        result = uye_davet_et(UyeDavetIstegi(eposta="CFO@Example.com", rol="cfo"), user())
        self.assertEqual(result["eposta"], "cfo@example.com")
        invitations = [value for key, value in self.db.store.items() if "invitations" in key]
        indexes = [value for key, value in self.db.store.items() if key[0] == "invitationIndex"]
        self.assertEqual(invitations[0]["companyId"], "company-a")
        self.assertEqual(indexes[0]["companyId"], "company-a")

    @patch("api.membership_service._claimleri_guncelle")
    @patch("api.membership_service._firebase_uygulamasi", return_value=MagicMock())
    def test_dogrulanmis_eposta_daveti_kabul_edebilir(self, _app, claims):
        uye_davet_et(UyeDavetIstegi(eposta="new@example.com", rol="analyst"), user())
        invited = user(role="", company=None, email="new@example.com", verified=True, uid="new-user")
        result = daveti_kabul_et(invited)
        self.assertEqual(result["rol"], "analyst")
        self.assertEqual(self.db.store[("companies", "company-a", "members", "new-user")]["role"], "analyst")
        claims.assert_called_once()

    def test_dogrulanmamis_eposta_daveti_kabul_edemez(self):
        invited = user(role="", company=None, email="new@example.com", verified=False, uid="new-user")
        with self.assertRaises(HTTPException) as context:
            daveti_kabul_et(invited)
        self.assertEqual(context.exception.status_code, 403)

    def test_admin_kendi_rolunu_degistiremez(self):
        with self.assertRaises(HTTPException) as context:
            uye_rolunu_guncelle(UyeRolGuncellemeIstegi(kullanici_id="user-admin", rol="viewer"), user())
        self.assertEqual(context.exception.status_code, 409)

    @patch("api.membership_service._claimleri_guncelle")
    @patch("api.membership_service.firebase_auth.revoke_refresh_tokens")
    @patch("api.membership_service._firebase_uygulamasi", return_value=MagicMock())
    def test_rol_degisiminde_eski_oturumlar_iptal_edilir(self, _app, revoke, _claims):
        self.db.store[("companies", "company-a", "members", "target-user")] = {
            "email": "target@example.com", "role": "cfo",
        }
        uye_rolunu_guncelle(
            UyeRolGuncellemeIstegi(kullanici_id="target-user", rol="viewer"), user(),
        )
        revoke.assert_called_once_with("target-user", app=_app.return_value)

    @patch("api.membership_service.firebase_auth.set_custom_user_claims")
    @patch("api.membership_service.firebase_auth.revoke_refresh_tokens")
    @patch("api.membership_service.firebase_auth.get_user")
    @patch("api.membership_service._firebase_uygulamasi", return_value=MagicMock())
    def test_uye_cikarilinca_eski_oturumlar_iptal_edilir(self, _app, get_user, revoke, _set_claims):
        self.db.store[("companies", "company-a", "members", "target-user")] = {
            "email": "target@example.com", "role": "analyst",
        }
        get_user.return_value.custom_claims = {"company_id": "company-a", "role": "analyst"}
        uye_cikar(UyeCikarmaIstegi(kullanici_id="target-user"), user())
        revoke.assert_called_once_with("target-user", app=_app.return_value)


if __name__ == "__main__":
    unittest.main()

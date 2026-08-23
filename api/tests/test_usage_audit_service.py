import unittest
from unittest.mock import MagicMock, patch

from api.models import KimlikBilgisi
from api.usage_audit_service import _satir_araligi, kullanim_olayi_kaydet


class TestKullanimDenetimi(unittest.TestCase):
    def test_satir_sayisi_tam_deger_yerine_aralik_olur(self):
        self.assertEqual(_satir_araligi(500), "101-1000")
        self.assertEqual(_satir_araligi(50_000), "10000+")

    def test_finansal_deger_ve_izinsiz_meta_kaydedilmez(self):
        db = MagicMock()
        belge = db.collection.return_value.document.return_value.collection.return_value.document.return_value
        kullanici = KimlikBilgisi(kullanici_id="u1", sirket_id="c1", roller={"admin": True})
        with patch("api.usage_audit_service._firebase_uygulamasi"), \
             patch("api.usage_audit_service.firestore.client", return_value=db):
            kullanim_olayi_kaydet(
                kullanici, "analysis.financial_audit", "analysis/financial",
                satir_sayisi=421,
                meta={"revenue": 1_000_000, "message": "gizli", "ajan_kapsami": "cfo_chat"},
            )
        kayit = belge.set.call_args.args[0]
        self.assertEqual(kayit["metadata"], {"ajan_kapsami": "cfo_chat", "satir_araligi": "101-1000"})
        self.assertFalse(kayit["containsFinancialData"])
        self.assertFalse(kayit["containsMessageBody"])
        self.assertNotIn("revenue", str(kayit))

    def test_gelistirici_hesabinda_firestore_yazilmaz(self):
        kullanici = KimlikBilgisi(kullanici_id="local", sirket_id="local-development", roller={"gelistirici": True})
        with patch("api.usage_audit_service.firestore.client") as istemci:
            kullanim_olayi_kaydet(kullanici, "ai.cfo_chat", "ai/cfo")
        istemci.assert_not_called()


if __name__ == "__main__":
    unittest.main()

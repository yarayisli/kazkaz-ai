from datetime import datetime, timedelta, timezone
import unittest

from fastapi import HTTPException

from api.models import KimlikBilgisi, PilotNiyetIstegi
from api.pilot_service import pilot_niyet_kaydet, pilot_olcumlerini_hesapla


NOW = datetime(2026, 9, 11, tzinfo=timezone.utc)


def pilot_row(*, full=True, paid=True, offset_days=30):
    start = NOW - timedelta(days=offset_days)
    actions = ["data.file_validated", "workspace.save", "analysis.financial_audit", "report.archive"]
    if not full:
        actions.pop()
    return {
        "startedAt": start,
        "audits": [
            {"action": action, "createdAt": start + timedelta(days=1)} for action in actions
        ] + [{"action": "report.archive", "createdAt": start - timedelta(days=1)}],
        "feedback": [{
            "category": "hata", "status": "resolved", "createdAt": start + timedelta(days=2),
            "updatedAt": start + timedelta(days=2, hours=2),
            "satisfaction": {"satisfied": True},
            "message": "Finansal içerik özette görünmemeli: ciro 1000000",
        }],
        "survey": {
            "continuationIntent": "kesinlikle", "paidContinuation": paid,
            "respondedAt": start + timedelta(days=22),
        },
    }


class TestPilotService(unittest.TestCase):
    def test_uc_sirket_dort_haftalik_asgari_kaniti_olusturur(self):
        result = pilot_olcumlerini_hesapla(
            [pilot_row(), pilot_row(), pilot_row(paid=False)], NOW
        )
        self.assertTrue(result["kapsam_gecerli"])
        self.assertEqual(result["dort_haftayi_tamamlayan"], 3)
        self.assertEqual(result["gorev_tamamlama"]["kontrol_noktasi"], 12)
        self.assertEqual(result["gorev_tamamlama"]["oran_yuzde"], 100.0)
        self.assertEqual(result["destek"]["medyan_cozum_dakika"], 120.0)
        self.assertEqual(result["devam_niyeti"]["ucretli_devam_yuzde"], 66.7)
        self.assertTrue(result["asgari_kanit_hazir"])

    def test_uc_sirketten_biri_ana_akisi_bitirmediyse_kanit_hazir_degil(self):
        result = pilot_olcumlerini_hesapla([pilot_row(), pilot_row(), pilot_row(full=False)], NOW)
        self.assertFalse(result["asgari_kanit_hazir"])

    def test_tamamlanmamis_sirketin_tam_akisi_kanit_sayilmaz(self):
        result = pilot_olcumlerini_hesapla([
            pilot_row(full=False), pilot_row(full=False), pilot_row(full=False),
            pilot_row(offset_days=10), pilot_row(offset_days=10), pilot_row(offset_days=10),
        ], NOW)
        self.assertEqual(result["dort_haftayi_tamamlayan"], 3)
        self.assertEqual(result["gorev_tamamlama"]["tam_yolculuk_sirket"], 3)
        self.assertEqual(result["gorev_tamamlama"]["tamamlanmis_tam_yolculuk_sirket"], 0)
        self.assertFalse(result["asgari_kanit_hazir"])

    def test_pilot_oncesi_olaylar_gorev_tamamlamaya_sayilmaz(self):
        row = pilot_row(full=False, offset_days=10)
        result = pilot_olcumlerini_hesapla([row], NOW)
        self.assertEqual(result["gorev_tamamlama"]["kontrol_noktasi"], 3)
        self.assertEqual(result["dort_haftayi_tamamlayan"], 0)

    def test_hata_talebi_teknik_hata_orani_gibi_sunulmaz(self):
        result = pilot_olcumlerini_hesapla([pilot_row()], NOW)
        self.assertIn("teknik 5xx oranı değildir", result["bildirilen_hata"]["tanim"])
        self.assertNotIn("message", str(result))
        self.assertFalse(result["finansal_veri_gosterilir"])

    def test_pilot_donemi_disindaki_niyet_yaniti_sayilmaz(self):
        row = pilot_row()
        row["survey"]["respondedAt"] = row["startedAt"] + timedelta(days=29)
        result = pilot_olcumlerini_hesapla([row], NOW)
        self.assertEqual(result["devam_niyeti"]["yanit"], 0)

    def test_izleyici_pilot_niyetini_sirket_adina_yazamaz(self):
        request = PilotNiyetIstegi(devam_niyeti="kesinlikle", ucretli_devam=True)
        user = KimlikBilgisi(kullanici_id="viewer", sirket_id="c1", roller={"viewer": True})
        with self.assertRaises(HTTPException) as error:
            pilot_niyet_kaydet(request, user)
        self.assertEqual(error.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()

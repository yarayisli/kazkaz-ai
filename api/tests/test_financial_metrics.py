import json
import unittest
from pathlib import Path

from api.financial_metrics import FORMUL_SURUMU, kurumsal_metrikleri_hesapla
from api.models import FinansalGorunum, MusteriCiroSatiri
from api.services import finansal_denetim


FIXTURE = Path(__file__).parent / "fixtures" / "financial_metrics_expected.json"


def tam_finansal_veri() -> FinansalGorunum:
    return FinansalGorunum(
        sirket_adi="Golden Test A.Ş.",
        sektor="İmalat",
        donem="2025",
        ciro=1_000_000,
        satis_maliyeti=400_000,
        faaliyet_giderleri=250_000,
        net_kar=200_000,
        nakit=150_000,
        kisa_vadeli_borc=250_000,
        uzun_vadeli_borc=100_000,
        alacaklar=250_000,
        borclar=200_000,
        stoklar=100_000,
        ozkaynak=500_000,
        faiz_gideri=25_000,
        vergi_gideri=75_000,
        amortisman=50_000,
        capex=80_000,
        donen_varliklar=550_000,
        toplam_varliklar=1_000_000,
        toplam_yukumlulukler=500_000,
        dagitilmamis_karlar=200_000,
        operasyonel_nakit_akisi=300_000,
        donem_gun_sayisi=365,
        etkin_vergi_orani=25,
        musteri_cirolari=[
            MusteriCiroSatiri(musteri_id="M1", musteri_adi="Müşteri 1", ciro=500_000),
            MusteriCiroSatiri(musteri_id="M2", musteri_adi="Müşteri 2", ciro=300_000),
            MusteriCiroSatiri(musteri_id="M3", musteri_adi="Müşteri 3", ciro=200_000),
        ],
    )


class TestKurumsalFinansMetrikleri(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.beklenen = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_golden_beklenen_sonuclar(self):
        sonuclar = kurumsal_metrikleri_hesapla(tam_finansal_veri())
        for metrik, beklenen in self.beklenen.items():
            with self.subTest(metrik=metrik):
                self.assertEqual(sonuclar[metrik]["durum"], "hesaplandi")
                self.assertAlmostEqual(sonuclar[metrik]["deger"], beklenen, places=4)
                self.assertEqual(sonuclar[metrik]["formul_surumu"], FORMUL_SURUMU)
                self.assertTrue(sonuclar[metrik]["formula_id"])
                self.assertTrue(sonuclar[metrik]["kaynak_alanlar"])

    def test_eksik_veride_sonuc_uydurulmaz(self):
        sonuclar = kurumsal_metrikleri_hesapla(FinansalGorunum(ciro=100_000, net_kar=10_000))
        for metrik, sonuc in sonuclar.items():
            with self.subTest(metrik=metrik):
                self.assertEqual(sonuc["durum"], "eksik_veri")
                self.assertIsNone(sonuc["deger"])
                self.assertTrue(sonuc["eksik_alanlar"])

    def test_api_geriye_uyumlu_ve_kaynakli_metrik_dondurur(self):
        sonuc = finansal_denetim(tam_finansal_veri())
        self.assertEqual(sonuc["metrikler"]["altman_z_prime"], self.beklenen["altman_z_prime"])
        self.assertEqual(sonuc["metrikler"]["musteri_hhi"], self.beklenen["musteri_hhi"])
        self.assertIn("metrik_kaydi", sonuc)
        self.assertEqual(
            sonuc["metrik_kaydi"]["serbest_nakit_akisi"]["formula_id"],
            "FREE_CASH_FLOW",
        )
        self.assertTrue(any("yoğunlaşması yüksek" in risk for risk in sonuc["riskler"]))


if __name__ == "__main__":
    unittest.main()

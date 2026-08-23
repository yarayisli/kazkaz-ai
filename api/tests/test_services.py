import unittest

from api.models import FinansalGorunum
from api.services import finansal_denetim


class TestFinansalDenetim(unittest.TestCase):
    def test_temel_metrikler_hesaplanir(self):
        veri = FinansalGorunum(
            sirket_adi="Test A.Ş.",
            ciro=1_000_000,
            satis_maliyeti=400_000,
            faaliyet_giderleri=250_000,
            net_kar=200_000,
            nakit=150_000,
            alacaklar=250_000,
            stoklar=100_000,
            kisa_vadeli_borc=250_000,
            ozkaynak=500_000,
            faiz_gideri=25_000,
            vergi_gideri=75_000,
            amortisman=50_000,
            capex=80_000,
        )
        sonuc = finansal_denetim(veri)
        self.assertEqual(sonuc["metrikler"]["brut_kar"], 600_000)
        self.assertEqual(sonuc["metrikler"]["favok"], 350_000)
        self.assertEqual(sonuc["metrikler"]["net_kar_marji"], 20.0)
        self.assertEqual(sonuc["metrikler"]["cari_oran"], 2.0)

    def test_zarar_aksiyon_uretir(self):
        veri = FinansalGorunum(ciro=100_000, net_kar=-10_000, kisa_vadeli_borc=50_000)
        sonuc = finansal_denetim(veri)
        self.assertTrue(any("zarar" in risk.lower() for risk in sonuc["riskler"]))
        self.assertGreater(len(sonuc["aksiyonlar"]), 0)

    def test_favok_eksik_girdilerle_uydurulmaz(self):
        veri = FinansalGorunum(ciro=500_000, net_kar=50_000)
        sonuc = finansal_denetim(veri)
        self.assertIsNone(sonuc["metrikler"]["favok"])
        self.assertEqual(sonuc["metrikler"]["favok_durumu"], "eksik_veri")


if __name__ == "__main__":
    unittest.main()

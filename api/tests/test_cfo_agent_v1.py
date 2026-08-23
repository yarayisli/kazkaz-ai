import unittest

from cfo_agent import CashFlowAlertTool, DebtAdvisorTool, FinancialHealthTool, InvestmentAdvisorTool

from api.agent_services import cfo_ajan_analizi
from api.models import BorcKalemi, CfoAjanAnalizIstegi, FinansalGorunum, NakitAkisSatiri


class TestGuvenliCfoAraclari(unittest.TestCase):
    def test_eksik_saglik_skoru_kritik_diye_sunulmaz(self):
        _, uyarilar = FinancialHealthTool().run(
            {
                "saglik_skoru": {"skor": None, "kategori": "Hesaplanmadı"},
                "karlilik": {"kar_marji": 12},
                "gelir": {"ortalama_buyume_orani": None},
                "gider": {"sabit_gider_orani": None},
            }
        )
        self.assertFalse(any("Sağlık Kritik" in uyari.baslik for uyari in uyarilar))

    def test_nakit_runway_gercek_ortalama_nakitten_hesaplanir(self):
        ozet, uyarilar = CashFlowAlertTool().run(
            {
                "operasyonel_ncf": -300_000,
                "ncf_marji": -10,
                "runway_ay": 2.5,
                "nakit_yakilip_yakilmiyor": True,
                "verimlilik_orani": 0.9,
                "cari_oran": 0.8,
                "nakit_donusum_gun": None,
            }
        )
        self.assertEqual(ozet["runway"], 2.5)
        self.assertTrue(any("Runway" in uyari.baslik for uyari in uyarilar))

    def test_yatirim_araci_kaynaksiz_roi_ve_tutar_uretmez(self):
        sonuc = InvestmentAdvisorTool().run(
            {
                "saglik_skoru": {"skor": None},
                "karlilik": {"kar_marji": 18},
                "gelir": {"toplam_gelir": 1_000_000, "ortalama_buyume_orani": None},
            },
            nakit_pozisyon=250_000,
        )
        self.assertFalse(sonuc["hesaplanabilir"])
        self.assertEqual(sonuc["max_yatirim"], 0)
        self.assertTrue(all("%" not in oneri["beklenen_roi"] for oneri in sonuc["oneriler"]))

    def test_dscr_gercek_borc_servisi_olmadan_hesaplanmaz(self):
        sonuc = DebtAdvisorTool().run(
            {"gelir": {"toplam_gelir": 1_000_000}, "karlilik": {"toplam_net_kar": 200_000}},
            mevcut_borc=500_000,
            faiz_orani=0.30,
        )
        self.assertIsNone(sonuc["dscr"])
        self.assertTrue(any(oneri["tip"] == "DSCR veri tamamlama" for oneri in sonuc["oneriler"]))

    def test_v1_adaptoru_bes_araci_kontrollu_baglar(self):
        istek = CfoAjanAnalizIstegi(
            finansal_veri=FinansalGorunum(
                sirket_adi="Test A.Ş.",
                ciro=1_000_000,
                satis_maliyeti=400_000,
                faaliyet_giderleri=250_000,
                net_kar=200_000,
                nakit=300_000,
                kisa_vadeli_borc=250_000,
                uzun_vadeli_borc=200_000,
                alacaklar=200_000,
                borclar=100_000,
                stoklar=100_000,
                ozkaynak=500_000,
            ),
            nakit_akisi=[
                NakitAkisSatiri(donem="Ocak", giris=200_000, cikis=250_000, net_nakit=-50_000),
                NakitAkisSatiri(donem="Şubat", giris=210_000, cikis=260_000, net_nakit=-50_000),
            ],
            borclar=[BorcKalemi(ad="Test kredi", tutar=450_000, faiz_orani=30)],
        )
        sonuc = cfo_ajan_analizi(istek)
        self.assertEqual(sonuc["durum"], "aktif_kontrollu")
        self.assertEqual(len(sonuc["araclar"]), 5)
        self.assertTrue(sonuc["yatirim"]["insan_onayi_gerekli"])
        self.assertIn("muhasebeci/CFO onayı bekliyor", str(sonuc["metodoloji_onaylari"]))


if __name__ == "__main__":
    unittest.main()

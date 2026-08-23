import unittest

from api.compliance_readiness import (
    EsgHazirlikIstegi,
    TfrsHazirlikIstegi,
    esg_hazirligini_degerlendir,
    tfrs_hazirligini_degerlendir,
)


class TestComplianceReadiness(unittest.TestCase):
    def test_esg_eksik_veride_performans_skoru_uretmez(self):
        sonuc = esg_hazirligini_degerlendir(EsgHazirlikIstegi(raporlama_yili=2026))
        self.assertEqual(sonuc["durum"], "veri_hazirligi")
        self.assertEqual(sonuc["hazirlik_orani"], 0)
        self.assertIn("ESG performans skoru", sonuc["uyari"])
        self.assertNotIn("performans_skoru", sonuc)

    def test_esg_tum_kaynaklar_ve_uzman_onayiyla_inceleme_asamasina_girer(self):
        sonuc = esg_hazirligini_degerlendir(EsgHazirlikIstegi(
            raporlama_yili=2026,
            organizasyon_kapsami_tanimli=True,
            onemli_konular_belirlendi=True,
            enerji_kwh=1000,
            scope1_tco2e=10,
            scope2_tco2e=20,
            su_m3=50,
            atik_ton=3,
            calisan_sayisi=40,
            kadin_calisan_orani=45,
            kayip_gunlu_is_kazasi=0,
            etik_politikasi_var=True,
            yonetim_sorumlusu_atandi=True,
            veri_kaynaklari_belgeli=True,
            uzman_onayi=True,
        ))
        self.assertEqual(sonuc["hazirlik_orani"], 100)
        self.assertEqual(sonuc["durum"], "hazirlik_tamamlandi")

    def test_esg_veri_hazirsa_uzman_onayi_bekler(self):
        istek = EsgHazirlikIstegi(
            raporlama_yili=2026,
            organizasyon_kapsami_tanimli=True,
            onemli_konular_belirlendi=True,
            enerji_kwh=1000,
            scope1_tco2e=10,
            scope2_tco2e=20,
            su_m3=50,
            atik_ton=3,
            calisan_sayisi=40,
            kadin_calisan_orani=45,
            kayip_gunlu_is_kazasi=0,
            etik_politikasi_var=True,
            yonetim_sorumlusu_atandi=True,
            veri_kaynaklari_belgeli=True,
        )
        sonuc = esg_hazirligini_degerlendir(istek)
        self.assertEqual(sonuc["durum"], "uzman_onayi_bekliyor")
        self.assertEqual(sonuc["hazirlik_orani"], 90)

    def test_tfrs_yalniz_uygulanabilir_basliklari_sayar(self):
        sonuc = tfrs_hazirligini_degerlendir(TfrsHazirlikIstegi(
            musteri_sozlesmeleri_var=True,
            hasilat_politikasi_belgeli=True,
            performans_yukumlulukleri_listeli=True,
            kiralama_sozlesmeleri_var=False,
            nakit_akis_mutabakati_var=False,
        ))
        self.assertEqual(sonuc["uygulanabilir_baslik"], 3)  # TFRS 15 + TMS 7 + uzman
        self.assertEqual(sonuc["hazir_baslik"], 1)
        self.assertTrue(any("Nakit akış" in eksik for eksik in sonuc["eksikler"]))
        self.assertIn("uyum görüşü", sonuc["uyari"])

    def test_tfrs_standart_setini_ve_lisans_sinirini_gosterir(self):
        sonuc = tfrs_hazirligini_degerlendir(TfrsHazirlikIstegi(
            standart_seti="TFRS 2026",
            nakit_akis_mutabakati_var=True,
            muhasebe_uzmani_onayi=True,
        ))
        self.assertEqual(sonuc["standart_seti"], "TFRS 2026")
        self.assertIn("lisans", sonuc["lisans_notu"].lower())


if __name__ == "__main__":
    unittest.main()

"""Şirketin kendi geçmişiyle karşılaştırılması."""

import unittest

from api.donem_karsilastirma import ONEMLI_DEGISIM_ESIGI, donem_karsilastirmasi


def _tablo(donem, ciro, smm, faaliyet_gid, alacaklar, stoklar, ticari_borc, nakit,
           donen=10_000_000, kv_borc=8_000_000):
    brut = ciro - smm
    faaliyet = brut - faaliyet_gid
    return {
        "donem": donem,
        "gelir_tablosu": {
            "ciro": ciro, "satis_maliyeti": smm, "brut_kar": brut,
            "faaliyet_giderleri": faaliyet_gid, "faaliyet_kari": faaliyet,
            "net_kar": faaliyet,
        },
        "bilanco": {
            "alacaklar": alacaklar, "stoklar": stoklar, "ticari_borc": ticari_borc,
            "nakit": nakit, "donen_varliklar": donen, "kisa_vadeli_borc": kv_borc,
        },
    }


class TestGecmisYok(unittest.TestCase):

    def test_tek_donemde_karsilastirma_yapilmaz(self):
        sonuc = donem_karsilastirmasi([_tablo("2025-Q4", 11_000_000, 7_000_000, 3_000_000,
                                              4_500_000, 1_400_000, 2_200_000, 1_400_000)], 90)
        self.assertEqual(sonuc["durum"], "gecmis_yok")
        self.assertEqual(sonuc["degisimler"], [])

    def test_bos_listede_cokmez(self):
        self.assertEqual(donem_karsilastirmasi([], 90)["durum"], "gecmis_yok")


class TestDegisimYonu(unittest.TestCase):

    def setUp(self):
        # Q3 -> Q4: ciro düşüyor, alacak artıyor (tahsilat bozuluyor)
        self.tablolar = [
            _tablo("2025-Q3", 12_000_000, 7_500_000, 3_500_000, 3_000_000, 1_400_000, 2_200_000, 2_000_000),
            _tablo("2025-Q4", 11_000_000, 7_200_000, 3_500_000, 4_500_000, 1_400_000, 2_200_000, 1_400_000),
        ]
        self.sonuc = donem_karsilastirmasi(self.tablolar, 90)
        self.degisim = {d["metrik"]: d for d in self.sonuc["degisimler"]}

    def test_ciro_dususu_kotu_sayilir(self):
        d = self.degisim["ciro"]
        self.assertEqual(d["yon"], "azaldi")
        self.assertEqual(d["deger_yargisi"], "kotu")

    def test_tahsilat_suresi_uzamasi_kotu_sayilir(self):
        # Artış her metrikte iyi değildir: tahsilat süresi uzaması kötüdür.
        d = self.degisim["alacak_devir_gunu"]
        self.assertEqual(d["yon"], "artti")
        self.assertEqual(d["deger_yargisi"], "kotu")

    def test_tahsilat_bozulmasinin_nakit_etkisi_hesaplanir(self):
        d = self.degisim["alacak_devir_gunu"]
        # (36.82 − 22.5) gün × (11.000.000 / 90) günlük ciro ≈ 1.750.000
        self.assertIsNotNone(d["nakit_etkisi"])
        self.assertAlmostEqual(d["nakit_etkisi"], 1_750_000, delta=5_000)
        self.assertGreater(d["nakit_etkisi"], 0, "süre uzayınca para bağlanır")

    def test_nakit_etkisi_yalnizca_tahsilat_suresinde_uretilir(self):
        for metrik in ("ciro", "net_kar_marji", "stok_devir_gunu", "cari_oran"):
            self.assertIsNone(self.degisim[metrik]["nakit_etkisi"], metrik)


class TestGurultuEsigi(unittest.TestCase):

    def test_kucuk_oynama_onemli_sayilmaz(self):
        # %1 ciro artışı eşiğin (%5) altında
        tablolar = [
            _tablo("2025-Q3", 10_000_000, 6_000_000, 3_000_000, 2_000_000, 1_000_000, 1_500_000, 1_000_000),
            _tablo("2025-Q4", 10_100_000, 6_060_000, 3_030_000, 2_020_000, 1_010_000, 1_515_000, 1_010_000),
        ]
        sonuc = donem_karsilastirmasi(tablolar, 90)
        self.assertEqual(sonuc["onemli_degisim_sayisi"], 0)
        self.assertTrue(all(not d["onemli"] for d in sonuc["degisimler"]))

    def test_esik_ustu_degisim_onemli_sayilir(self):
        artis = 1 + ONEMLI_DEGISIM_ESIGI + 0.01
        tablolar = [
            _tablo("2025-Q3", 10_000_000, 6_000_000, 3_000_000, 2_000_000, 1_000_000, 1_500_000, 1_000_000),
            _tablo("2025-Q4", int(10_000_000 * artis), 6_000_000, 3_000_000, 2_000_000, 1_000_000, 1_500_000, 1_000_000),
        ]
        sonuc = donem_karsilastirmasi(tablolar, 90)
        self.assertTrue({d["metrik"] for d in sonuc["degisimler"] if d["onemli"]})


class TestEksikVeri(unittest.TestCase):

    def test_donem_gunu_yoksa_gun_metrikleri_uretilmez(self):
        tablolar = [
            _tablo("2025-Q3", 12_000_000, 7_500_000, 3_500_000, 3_000_000, 1_400_000, 2_200_000, 2_000_000),
            _tablo("2025-Q4", 11_000_000, 7_200_000, 3_500_000, 4_500_000, 1_400_000, 2_200_000, 1_400_000),
        ]
        metrikler = {d["metrik"] for d in donem_karsilastirmasi(tablolar, None)["degisimler"]}
        # 365 varsayılmaz: gün bazlı metrikler hiç çıkmaz
        self.assertNotIn("alacak_devir_gunu", metrikler)
        self.assertNotIn("stok_devir_gunu", metrikler)
        # Oran bazlı metrikler etkilenmez
        self.assertIn("net_kar_marji", metrikler)

    def test_sifir_ciro_orani_bozmaz(self):
        tablolar = [
            _tablo("2025-Q3", 0, 0, 0, 0, 0, 0, 1_000_000),
            _tablo("2025-Q4", 5_000_000, 3_000_000, 1_000_000, 1_000_000, 500_000, 800_000, 1_200_000),
        ]
        sonuc = donem_karsilastirmasi(tablolar, 90)
        self.assertEqual(sonuc["durum"], "hazir")  # çökmemeli


if __name__ == "__main__":
    unittest.main()

"""api/data_quality — cross-field tutarlılık + anomali tarama testleri."""

import unittest

from api.data_quality import (
    anomali_taramasi,
    kalite_raporu,
    tutarlilik_kontrolu,
)


class TestTutarlilikKontrolu(unittest.TestCase):

    def test_dogru_veri_uyari_uretmez(self):
        veri = {
            "ciro": 1_000_000, "satis_maliyeti": 400_000,
            "faaliyet_giderleri": 300_000, "faiz_gideri": 50_000,
            "vergi_gideri": 40_000, "net_kar": 210_000,
            "toplam_varliklar": 2_000_000, "toplam_yukumlulukler": 800_000,
            "ozkaynak": 1_200_000, "donen_varliklar": 1_100_000,
            "nakit": 300_000, "kisa_vadeli_borc": 400_000,
        }
        self.assertEqual(tutarlilik_kontrolu(veri), [])

    def test_bilanco_esitsizligi_yakalanir(self):
        veri = {
            "toplam_varliklar": 1_000_000,
            "toplam_yukumlulukler": 400_000,
            "ozkaynak": 500_000,   # 400+500=900 ≠ 1000, %10 sapma
        }
        bulgular = tutarlilik_kontrolu(veri)
        self.assertTrue(any(b["kod"] == "bilanco_esitsizligi" for b in bulgular))

    def test_donen_varlik_toplami_asamaz(self):
        veri = {"donen_varliklar": 1_500_000, "toplam_varliklar": 1_000_000}
        bulgular = tutarlilik_kontrolu(veri)
        self.assertTrue(any(b["kod"] == "donen_varlik_asimi" for b in bulgular))
        self.assertEqual(
            next(b for b in bulgular if b["kod"] == "donen_varlik_asimi")["seviye"],
            "hata",
        )

    def test_kar_tanimi_tutarsizligi_uyari_seviyesinde(self):
        # Beklenen: 100-40-30-5-4 = 21, verilen 50 → %29 sapma
        veri = {
            "ciro": 100, "satis_maliyeti": 40, "faaliyet_giderleri": 30,
            "faiz_gideri": 5, "vergi_gideri": 4, "net_kar": 50,
        }
        bulgular = tutarlilik_kontrolu(veri)
        b = next((b for b in bulgular if b["kod"] == "kar_tanimi_tutarsiz"), None)
        self.assertIsNotNone(b)
        self.assertEqual(b["seviye"], "uyari")

    def test_nakit_akis_tutarsizligi_yakalanir(self):
        veri = {
            "nakit": 300_000, "donem_basi_nakit": 100_000,
            "operasyonel_nakit_akisi": 50_000,
            "yatirim_nakit_akisi": -20_000,
            "finansman_nakit_akisi": 10_000,
        }
        # Beklenen: 100+50-20+10=140K, verilen 300K → büyük sapma
        bulgular = tutarlilik_kontrolu(veri)
        self.assertTrue(any(b["kod"] == "nakit_akis_tutarsiz" for b in bulgular))

    def test_none_alanlar_hata_atmaz(self):
        veri = {"ciro": None, "net_kar": None, "toplam_varliklar": None}
        self.assertEqual(tutarlilik_kontrolu(veri), [])


class TestAnomaliTaramasi(unittest.TestCase):

    def test_olagandisi_marj_yakalanir(self):
        # Net kâr ciroyu 2× aşıyor → %200 marj imkânsız
        bulgular = anomali_taramasi({"ciro": 100, "net_kar": 200})
        self.assertTrue(any(b["kod"] == "olağandışı_marj" for b in bulgular))

    def test_asiri_gider_uyari_verir(self):
        # Toplam gider ciroyu 6× aşıyor
        bulgular = anomali_taramasi({
            "ciro": 100, "satis_maliyeti": 400, "faaliyet_giderleri": 200,
        })
        self.assertTrue(any(b["kod"] == "gider_ciro_orani_asiri" for b in bulgular))

    def test_musteri_konsantrasyonu_bayrak(self):
        musteri = [
            {"ciro": 900_000},
            {"ciro": 50_000},
            {"ciro": 50_000},
        ]
        bulgular = anomali_taramasi({"ciro": 1_000_000}, musteri_cirolari=musteri)
        self.assertTrue(any(b["kod"] == "musteri_konsantrasyonu" for b in bulgular))

    def test_ay_ustu_sicrama_yakalanir(self):
        zaman_serisi = [
            {"tarih": "2024-01-15", "gelir": 100},
            {"tarih": "2024-02-15", "gelir": 700},  # 7× sıçrama
        ]
        bulgular = anomali_taramasi({}, zaman_serisi=zaman_serisi)
        self.assertTrue(any(b["kod"] == "ay_ustu_sicrama" for b in bulgular))

    def test_saglikli_veri_uyari_uretmez(self):
        bulgular = anomali_taramasi({
            "ciro": 1_000_000, "satis_maliyeti": 400_000,
            "faaliyet_giderleri": 300_000, "net_kar": 210_000,
        })
        self.assertEqual(bulgular, [])


class TestKaliteRaporu(unittest.TestCase):

    def test_bulgu_yoksa_temiz_durum(self):
        r = kalite_raporu({
            "ciro": 1_000_000, "satis_maliyeti": 400_000,
            "faaliyet_giderleri": 300_000, "net_kar": 300_000,
        })
        self.assertEqual(r["durum"], "temiz")
        self.assertEqual(r["toplam_hata"], 0)
        self.assertEqual(r["toplam_uyari"], 0)

    def test_hata_ve_uyari_ayri_sayilir(self):
        # bilanço eşitsizliği (hata) + tek müşteri konsantrasyonu (uyari)
        r = kalite_raporu(
            {"toplam_varliklar": 1000, "toplam_yukumlulukler": 400, "ozkaynak": 500},
            musteri_cirolari=[{"ciro": 900}, {"ciro": 100}],
        )
        self.assertEqual(r["durum"], "hatali")
        self.assertGreaterEqual(r["toplam_hata"], 1)
        self.assertGreaterEqual(r["toplam_uyari"], 1)


if __name__ == "__main__":
    unittest.main()

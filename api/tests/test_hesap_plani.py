"""Tekdüzen Hesap Planı otomatik eşlemesi ve mizandan tablo türetme."""

import unittest

from api.financial_statements import finansal_tablo_paketi
from api.hesap_plani import kategori_bul, maliyet_hesabi_mi
from api.models import FinansalGorunum, MizanSatiri


class TestKategoriEslemesi(unittest.TestCase):

    def test_standart_kodlar_eslesir(self):
        beklenen = {
            "100": "nakit", "102": "nakit", "120": "alacaklar", "153": "stoklar",
            "255": "duran_varlik", "300": "kisa_vadeli_borc", "320": "ticari_borc",
            "400": "uzun_vadeli_borc", "500": "ozkaynak", "570": "gecmis_yil_kari",
            "590": "donem_kari", "600": "ciro", "621": "satis_maliyeti",
            "632": "faaliyet_gideri", "660": "faiz_gideri", "691": "vergi_gideri",
        }
        for kod, kategori in beklenen.items():
            self.assertEqual(kategori_bul(kod), kategori, f"{kod} yanlış eşleşti")

    def test_alt_kirilimli_kodlar_da_eslesir(self):
        # Muhasebe programları 120.01.001 gibi alt kırılım üretir.
        self.assertEqual(kategori_bul("120.01.001"), "alacaklar")
        self.assertEqual(kategori_bul("600-01"), "ciro")
        self.assertEqual(kategori_bul("100 01"), "nakit")

    def test_sonuc_hesaplari_eslesmez(self):
        # 690/692 türetilmiş bakiyelerdir; toplanırsa çift sayım olur.
        for kod in ("690", "692", "693"):
            self.assertIsNone(kategori_bul(kod))

    def test_maliyet_hesaplari_eslesmez_ama_isaretlenir(self):
        self.assertIsNone(kategori_bul("770"))
        self.assertTrue(maliyet_hesabi_mi("770"))
        self.assertTrue(maliyet_hesabi_mi("710"))
        self.assertFalse(maliyet_hesabi_mi("632"))

    def test_bos_ve_gecersiz_kod_none_doner(self):
        for kod in (None, "", "ABC", "-"):
            self.assertIsNone(kategori_bul(kod))


def _denk_mizan():
    """Çift taraflı denk mizan: borç toplamı = alacak toplamı."""
    return [
        # Varlıklar
        MizanSatiri(donem="2025-12", hesap_kodu="100", hesap_adi="Kasa", borc=3_250_000, alacak=0),
        MizanSatiri(donem="2025-12", hesap_kodu="120", hesap_adi="Alıcılar", borc=9_600_000, alacak=0),
        MizanSatiri(donem="2025-12", hesap_kodu="153", hesap_adi="Ticari Mallar", borc=1_400_000, alacak=0),
        MizanSatiri(donem="2025-12", hesap_kodu="255", hesap_adi="Demirbaşlar", borc=5_000_000, alacak=0),
        MizanSatiri(donem="2025-12", hesap_kodu="257", hesap_adi="Birikmiş Amortisman", borc=0, alacak=1_200_000),
        # Kaynaklar
        MizanSatiri(donem="2025-12", hesap_kodu="320", hesap_adi="Satıcılar", borc=0, alacak=2_200_000),
        MizanSatiri(donem="2025-12", hesap_kodu="300", hesap_adi="Banka Kredileri", borc=0, alacak=8_400_000),
        MizanSatiri(donem="2025-12", hesap_kodu="400", hesap_adi="Banka Kredileri UV", borc=0, alacak=5_100_000),
        MizanSatiri(donem="2025-12", hesap_kodu="500", hesap_adi="Sermaye", borc=0, alacak=1_330_000),
        # Gelir tablosu
        MizanSatiri(donem="2025-12", hesap_kodu="600", hesap_adi="Yurtiçi Satışlar", borc=0, alacak=47_000_000),
        MizanSatiri(donem="2025-12", hesap_kodu="621", hesap_adi="STMM", borc=29_300_000, alacak=0),
        MizanSatiri(donem="2025-12", hesap_kodu="632", hesap_adi="Genel Yönetim Gideri", borc=14_900_000, alacak=0),
        MizanSatiri(donem="2025-12", hesap_kodu="660", hesap_adi="Faiz Gideri", borc=1_400_000, alacak=0),
        MizanSatiri(donem="2025-12", hesap_kodu="691", hesap_adi="Vergi Karşılığı", borc=380_000, alacak=0),
    ]


def _gorunum():
    return FinansalGorunum(
        sirket_adi="Test", ciro=47_000_000, satis_maliyeti=29_300_000,
        faaliyet_giderleri=14_900_000, net_kar=1_020_000, nakit=3_250_000,
        alacaklar=9_600_000, stoklar=1_400_000, borclar=2_200_000,
        kisa_vadeli_borc=8_400_000, uzun_vadeli_borc=5_100_000, ozkaynak=1_330_000,
    )


class TestMizandanTabloTuretme(unittest.TestCase):
    """Etiketsiz mizandan gelir tablosu ve bilanço çıkarılmalı."""

    def setUp(self):
        self.paket = finansal_tablo_paketi(_denk_mizan(), _gorunum())
        self.son = self.paket["son_donem"]

    def test_hicbir_hesap_etiketsiz_kalmaz(self):
        self.assertEqual(self.paket["eslesmeyen_hesaplar"], [])

    def test_gelir_tablosu_dogru_turetilir(self):
        g = self.son["gelir_tablosu"]
        self.assertEqual(g["ciro"], 47_000_000)
        self.assertEqual(g["satis_maliyeti"], 29_300_000)
        self.assertEqual(g["brut_kar"], 17_700_000)
        self.assertEqual(g["faaliyet_kari"], 2_800_000)
        self.assertEqual(g["net_kar"], 1_020_000)

    def test_bilanco_denk_cikar(self):
        b = self.son["bilanco"]
        self.assertTrue(b["denk"], f"bilanço farkı: {b['bilanco_farki']}")
        self.assertEqual(b["toplam_varliklar"], 18_050_000)

    def test_ters_bakiyeli_hesaplar_dusulur(self):
        # 257 Birikmiş amortisman duran varlığı azaltmalı: 5.000.000 − 1.200.000
        self.assertEqual(self.son["bilanco"]["duran_varliklar"], 3_800_000)

    def test_mizan_cift_tarafli_denk(self):
        self.assertTrue(self.son["mizan_denk"], f"mizan farkı: {self.son['mizan_farki']}")

    def test_kullanici_eslemesi_hesap_kodunu_ezer(self):
        mizan = _denk_mizan()
        # 600 normalde ciroya gider. Kullanıcı özkaynak diye etiketlerse
        # hesap kodu değil kullanıcının etiketi geçerli olmalı.
        mizan[9] = MizanSatiri(
            donem="2025-12", hesap_kodu="600", hesap_adi="Yurtiçi Satışlar",
            borc=0, alacak=47_000_000, esleme="ozkaynak",
        )
        paket = finansal_tablo_paketi(mizan, _gorunum())
        self.assertEqual(paket["son_donem"]["gelir_tablosu"]["ciro"], 0)

    def test_maliyet_hesabi_gideri_iki_kez_saymaz(self):
        mizan = _denk_mizan()
        mizan.append(MizanSatiri(
            donem="2025-12", hesap_kodu="770", hesap_adi="Genel Yönetim Gideri 7/A",
            borc=14_900_000, alacak=0,
        ))
        paket = finansal_tablo_paketi(mizan, _gorunum())
        self.assertEqual(paket["son_donem"]["gelir_tablosu"]["faaliyet_giderleri"], 14_900_000)
        self.assertIn("770", paket["yansitma_hesaplari"])
        self.assertNotIn("770", paket["eslesmeyen_hesaplar"])


if __name__ == "__main__":
    unittest.main()

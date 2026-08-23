import unittest
from datetime import date

from api.fx_engine import KurHatasi, para_birimlerini_dogrula, tarihsel_kurlari_getir, tcmb_xml_kurlarini_oku


XML = b'''<?xml version="1.0" encoding="UTF-8"?>
<Tarih_Date Tarih="19.08.2026">
  <Currency CurrencyCode="USD"><Unit>1</Unit><ForexBuying>40.1234</ForexBuying></Currency>
  <Currency CurrencyCode="EUR"><Unit>1</Unit><ForexBuying>46.5678</ForexBuying></Currency>
  <Currency CurrencyCode="JPY"><Unit>100</Unit><ForexBuying>27.5000</ForexBuying></Currency>
</Tarih_Date>'''


class TestTarihselKurMotoru(unittest.TestCase):
    def test_xml_doviz_alis_ve_birim_ile_okunur(self):
        kurlar = tcmb_xml_kurlarini_oku(XML)
        self.assertEqual(kurlar["USD"], 40.1234)
        self.assertEqual(kurlar["JPY"], 0.275)

    def test_tatil_gununde_onceki_is_gunune_doner(self):
        denenen = []

        def indirici(tarih):
            denenen.append(tarih)
            if tarih == date(2026, 8, 19):
                return XML
            raise KurHatasi("kur yok")

        sonuc = tarihsel_kurlari_getir(date(2026, 8, 20), ["USD", "EUR"], indirici=indirici)
        self.assertEqual(sonuc["kur_tarihi"], "2026-08-19")
        self.assertEqual(sonuc["kurlar"]["USD"], 40.1234)
        self.assertEqual(len(denenen), 2)

    def test_desteklenmeyen_kod_reddedilir(self):
        with self.assertRaises(KurHatasi):
            para_birimlerini_dogrula(["BTC"])

    def test_try_icin_dis_servise_cikmaz(self):
        sonuc = tarihsel_kurlari_getir(
            date(2026, 8, 20), ["TRY"], indirici=lambda _tarih: self.fail("çağrılmamalı"),
        )
        self.assertEqual(sonuc["kurlar"], {"TRY": 1.0})


if __name__ == "__main__":
    unittest.main()

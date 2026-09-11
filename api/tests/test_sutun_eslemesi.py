"""Excel sütun eşlemesi: tanıma raporu + kayıtlı eşlemeyle tekrar yüklenmeme."""

import io
import unittest

from openpyxl import Workbook

from api.excel_import import dosya_dogrula
from api.sutun_eslemesi import sutun_raporu, sutunlari_coz


class TestCozumveRapor(unittest.TestCase):

    def test_kayitli_esleme_yerlesigi_ezer(self):
        basliklar = {0: "tarih", 1: "ciro"}
        yerlesik = {"tarih": "tarih"}  # "ciro" yerleşikte yok
        cozum = sutunlari_coz(basliklar, yerlesik, {"ciro": "gelir"})
        self.assertEqual(cozum[1], "gelir")

    def test_kayitli_esleme_dogru_yerlesigi_de_degistirebilir(self):
        basliklar = {0: "tutar"}
        yerlesik = {"tutar": "gelir"}
        cozum = sutunlari_coz(basliklar, yerlesik, {"tutar": "gider"})
        self.assertEqual(cozum[0], "gider")  # kullanıcı bilerek override etti

    def test_rapor_gercek_baslik_metnini_gosterir(self):
        basliklar = {0: "firma_adi", 1: "ciro"}
        cozum = {0: None, 1: "gelir"}
        ham = {0: "Firma Adı", 1: "Ciro"}
        rapor = sutun_raporu(basliklar, cozum, ham)
        self.assertFalse(rapor["tam_eslesme"])
        self.assertEqual(rapor["cozulemeyen_sutunlar"][0]["baslik"], "Firma Adı")
        self.assertEqual(rapor["taninan_sutunlar"][0]["baslik"], "Ciro")


def _dosya(basliklar, *satirlar):
    wb = Workbook(); ws = wb.active; ws.title = "İşlemler"
    ws.append(basliklar)
    for s in satirlar:
        ws.append(s)
    buf = io.BytesIO(); wb.save(buf)
    return buf.getvalue()


class TestUctanUca(unittest.TestCase):

    def setUp(self):
        # Standart dışı başlıklar: Ciro (gelir), Firma (müşteri)
        self.icerik = _dosya(
            ["Tarih", "Kategori", "Ciro", "Gider", "Firma"],
            ["2025-01-15", "Satış", 100000, 60000, "Aygaz"],
            ["2025-02-15", "Satış", 120000, 70000, "Mercan"],
        )

    def test_eslesmeyen_sutun_esleme_gerekli_dondurur(self):
        sonuc = dosya_dogrula(self.icerik, "t.xlsx")
        self.assertEqual(sonuc["durum"], "eslesme_gerekli")
        cozulemeyen = {c["baslik"] for c in sonuc["sutun_eslemesi"]["cozulemeyen_sutunlar"]}
        self.assertEqual(cozulemeyen, {"Ciro", "Firma"})
        # Kullanıcıya seçenek sunulmalı
        self.assertIn("gelir", sonuc["eslenebilir_alanlar"])
        self.assertIn("musteri", sonuc["eslenebilir_alanlar"])

    def test_kayitli_eslemeyle_hazir_olur(self):
        sonuc = dosya_dogrula(self.icerik, "t.xlsx",
                              kayitli_esleme={"ciro": "gelir", "firma": "musteri"})
        self.assertIn(sonuc["durum"], ("hazir", "uyarili"))
        self.assertEqual(sonuc["ozet"]["islem_satirlari"], 2)
        self.assertEqual(sonuc["zaman_serisi"][0]["gelir"], 100000)
        self.assertEqual(sonuc["zaman_serisi"][0]["musteri"], "Aygaz")
        self.assertTrue(sonuc["sutun_eslemesi"]["tam_eslesme"])

    def test_standart_baslik_esleme_gerektirmez(self):
        icerik = _dosya(
            ["Tarih", "Kategori", "Gelir", "Gider"],
            ["2025-01-15", "Satış", 100000, 60000],
        )
        sonuc = dosya_dogrula(icerik, "t.xlsx")
        self.assertIn(sonuc["durum"], ("hazir", "uyarili"))
        self.assertTrue(sonuc["sutun_eslemesi"]["tam_eslesme"])


if __name__ == "__main__":
    unittest.main()

import json
import unittest
from pathlib import Path

from api.financial_statements import finansal_tablo_paketi
from api.models import FinansalGorunum, MizanSatiri


BEKLENEN = json.loads(
    (Path(__file__).parent / "fixtures" / "financial_statements_expected.json").read_text(encoding="utf-8")
)


def _satir(kod: str, ad: str, *, borc: float = 0, alacak: float = 0, esleme: str) -> MizanSatiri:
    return MizanSatiri(
        donem="2026", hesap_kodu=kod, hesap_adi=ad, borc=borc, alacak=alacak, esleme=esleme
    )


def ornek_mizan():
    return [
        _satir("100", "Kasa ve bankalar", borc=300, esleme="nakit"),
        _satir("120", "Ticari alacaklar", borc=200, esleme="alacaklar"),
        _satir("150", "Stoklar", borc=100, esleme="stoklar"),
        _satir("180", "Diğer dönen", borc=50, esleme="diger_donen"),
        _satir("250", "Maddi duran varlık", borc=600, esleme="duran_varlik"),
        _satir("280", "Diğer varlık", borc=50, esleme="diger_varlik"),
        _satir("300", "Kısa vadeli banka", alacak=200, esleme="kisa_vadeli_borc"),
        _satir("320", "Ticari borç", alacak=150, esleme="ticari_borc"),
        _satir("400", "Uzun vadeli banka", alacak=250, esleme="uzun_vadeli_borc"),
        _satir("470", "Karşılıklar", alacak=44, esleme="karsilik"),
        _satir("500", "Sermaye", alacak=300, esleme="sermaye"),
        _satir("570", "Geçmiş yıl kârı", alacak=100, esleme="gecmis_yil_kari"),
        _satir("600", "Yurt içi satış", alacak=1000, esleme="ciro"),
        _satir("620", "Satış maliyeti", borc=400, esleme="satis_maliyeti"),
        _satir("630", "Faaliyet gideri", borc=200, esleme="faaliyet_gideri"),
        _satir("640", "Amortisman", borc=50, esleme="amortisman"),
        _satir("660", "Faiz", borc=30, esleme="faiz_gideri"),
        _satir("691", "Vergi", borc=64, esleme="vergi_gideri"),
    ]


def ornek_gorunum(**degisiklikler):
    veri = {
        "sirket_adi": "Mutabakat A.Ş.", "donem": "2026", "ciro": 1000,
        "satis_maliyeti": 400, "faaliyet_giderleri": 200, "net_kar": 256,
        "nakit": 300, "kisa_vadeli_borc": 200, "uzun_vadeli_borc": 250,
        "alacaklar": 200, "borclar": 150, "stoklar": 100, "ozkaynak": 656,
        "faiz_gideri": 30, "vergi_gideri": 64, "amortisman": 50,
        "donen_varliklar": 650, "toplam_varliklar": 1300,
        "toplam_yukumlulukler": 644, "dagitilmamis_karlar": 100,
        "operasyonel_nakit_akisi": 330, "donem_basi_nakit": 250,
        "yatirim_nakit_akisi": -200, "finansman_nakit_akisi": -80,
    }
    veri.update(degisiklikler)
    return FinansalGorunum(**veri)


class TestFinansalTablolar(unittest.TestCase):
    def test_mizandan_beklenen_tablolari_ve_nakit_koprusunu_uretir(self):
        sonuc = finansal_tablo_paketi(ornek_mizan(), ornek_gorunum())
        gelir = sonuc["son_donem"]["gelir_tablosu"]
        bilanco = sonuc["son_donem"]["bilanco"]

        self.assertEqual(sonuc["durum"], "tamamlandi")
        self.assertEqual(sonuc["tablo_surumu"], BEKLENEN["tablo_surumu"])
        for alan in ("ciro", "brut_kar", "faaliyet_kari", "net_kar"):
            self.assertEqual(gelir[alan], BEKLENEN[alan])
        for alan in ("donen_varliklar", "toplam_varliklar", "toplam_yukumlulukler", "toplam_ozkaynak", "bilanco_farki"):
            self.assertEqual(bilanco[alan], BEKLENEN[alan])
        self.assertTrue(bilanco["donem_kari_ozkaynaga_eklendi"])
        self.assertEqual(sonuc["finansal_gorunum_mutabakati"]["durum"], "mutabik")
        self.assertEqual(sonuc["nakit_koprusu"]["durum"], "mutabik")
        self.assertEqual(sonuc["nakit_koprusu"]["beklenen_donem_sonu_nakit"], BEKLENEN["nakit"])

    def test_farkli_ozet_degerini_acikca_isaretler(self):
        sonuc = finansal_tablo_paketi(ornek_mizan(), ornek_gorunum(net_kar=300))
        self.assertEqual(sonuc["durum"], "inceleme_gerekli")
        self.assertIn("net_kar", sonuc["finansal_gorunum_mutabakati"]["uyusmayan_alanlar"])

    def test_nakit_akisi_eksikse_deger_uydurmaz(self):
        sonuc = finansal_tablo_paketi(
            ornek_mizan(),
            ornek_gorunum(operasyonel_nakit_akisi=None, yatirim_nakit_akisi=None, finansman_nakit_akisi=None),
        )
        self.assertEqual(sonuc["nakit_koprusu"]["durum"], "eksik_veri")
        self.assertIn("operasyonel_nakit_akisi", sonuc["nakit_koprusu"]["eksik_alanlar"])
        self.assertNotIn("beklenen_donem_sonu_nakit", sonuc["nakit_koprusu"])

    def test_mizan_yokken_guvenli_bekler(self):
        sonuc = finansal_tablo_paketi([], ornek_gorunum())
        self.assertEqual(sonuc["durum"], "veri_bekliyor")


if __name__ == "__main__":
    unittest.main()

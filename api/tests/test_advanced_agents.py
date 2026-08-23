import json
import unittest
from datetime import date, timedelta
from pathlib import Path

from api.advanced_agents import bas_denetci, gelismis_ajan_analizi
from api.models import (
    AlacakFaturasi,
    BorcServisSatiri,
    ButceGerceklesmeSatiri,
    FinansalGorunum,
    GelismisAjanIstegi,
    HaftalikNakitSatiri,
    MizanSatiri,
)


FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "advanced_agents_expected.json").read_text(encoding="utf-8")
)


def ornek_istek() -> GelismisAjanIstegi:
    ilk_hafta = date(2026, 1, 6)
    return GelismisAjanIstegi(
        finansal_veri=FinansalGorunum(
            sirket_adi="Beklenen Sonuç A.Ş.",
            ciro=1_000,
            satis_maliyeti=400,
            faaliyet_giderleri=250,
            net_kar=200,
            nakit=1_000,
            kisa_vadeli_borc=400,
            uzun_vadeli_borc=200,
            alacaklar=950,
            borclar=150,
            stoklar=100,
            ozkaynak=600,
        ),
        rapor_tarihi=date(2026, 4, 30),
        baslangic_nakdi=1_000,
        minimum_nakit_esigi=800,
        operasyonel_nakit_akisi=436,
        mizan=[
            MizanSatiri(donem="2026-03", hesap_kodu="100", hesap_adi="Kasa", borc=1_000, esleme="aktif"),
            MizanSatiri(donem="2026-03", hesap_kodu="300", hesap_adi="Borç", alacak=400, esleme="pasif"),
            MizanSatiri(donem="2026-03", hesap_kodu="500", hesap_adi="Sermaye", alacak=600, esleme="özkaynak"),
        ],
        haftalik_nakit=[
            HaftalikNakitSatiri(
                hafta=ilk_hafta + timedelta(weeks=index),
                tahsilat=100,
                tedarikci=120,
            )
            for index in range(13)
        ],
        alacak_faturalari=[
            AlacakFaturasi(fatura_id="F1", musteri_id="A", musteri_adi="Müşteri A", fatura_tarihi=date(2026, 4, 1), vade_tarihi=date(2026, 4, 20), tutar=100),
            AlacakFaturasi(fatura_id="F2", musteri_id="A", musteri_adi="Müşteri A", fatura_tarihi=date(2026, 2, 1), vade_tarihi=date(2026, 2, 15), tutar=200, odenen=50),
            AlacakFaturasi(fatura_id="F3", musteri_id="B", musteri_adi="Müşteri B", fatura_tarihi=date(2025, 12, 1), vade_tarihi=date(2025, 12, 31), tutar=300),
            AlacakFaturasi(fatura_id="F4", musteri_id="C", musteri_adi="Müşteri C", fatura_tarihi=date(2026, 4, 15), vade_tarihi=date(2026, 5, 31), tutar=400),
        ],
        borc_servisi=[
            BorcServisSatiri(borc_id="B1", alacakli="Banka", odeme_tarihi=date(2026, 5, 15), anapara=100, faiz=10),
            BorcServisSatiri(borc_id="B1", alacakli="Banka", odeme_tarihi=date(2026, 6, 15), anapara=100, faiz=8),
        ],
        butce=[
            ButceGerceklesmeSatiri(ay=date(2026, 1, 1), kategori="Operasyon", butce=100, gerceklesen=110, onceki_tahmin=100),
            ButceGerceklesmeSatiri(ay=date(2026, 2, 1), kategori="Operasyon", butce=100, gerceklesen=90, onceki_tahmin=100),
            ButceGerceklesmeSatiri(ay=date(2026, 3, 1), kategori="Operasyon", butce=100, gerceklesen=120, onceki_tahmin=100),
        ],
    )


class TestGelismisAjanlar(unittest.TestCase):
    def setUp(self):
        self.sonuc = gelismis_ajan_analizi(ornek_istek())
        self.ajanlar = self.sonuc["ajanlar"]

    def test_mizan_beklenen_sonuc(self):
        ajan = self.ajanlar["mizan_esleme_ajani"]
        self.assertEqual(ajan["mizan_farki"], FIXTURE["mizan"]["mizan_farki"])
        self.assertEqual(ajan["esleme_kapsami"], FIXTURE["mizan"]["esleme_kapsami"])
        self.assertEqual(ajan["bilanco_denklemi"]["fark"], FIXTURE["mizan"]["bilanco_farki"])

    def test_13_haftalik_nakit_beklenen_sonuc(self):
        ajan = self.ajanlar["nakit_13_hafta_ajani"]
        self.assertEqual(ajan["hafta_sayisi"], FIXTURE["nakit"]["hafta_sayisi"])
        self.assertEqual(ajan["donem_sonu_nakit"], FIXTURE["nakit"]["donem_sonu_nakit"])
        self.assertEqual(ajan["ilk_esik_alti_tarih"], FIXTURE["nakit"]["ilk_esik_alti_tarih"])

    def test_26_hafta_kayan_13_haftalik_pencerelere_donusur(self):
        ilk_hafta = date(2026, 1, 6)
        istek = ornek_istek().model_copy(update={
            "rapor_tarihi": ilk_hafta,
            "haftalik_nakit": [
                HaftalikNakitSatiri(
                    hafta=ilk_hafta + timedelta(weeks=index),
                    tahsilat=100,
                    tedarikci=120,
                )
                for index in range(26)
            ],
        })
        ajan = gelismis_ajan_analizi(istek)["ajanlar"]["nakit_13_hafta_ajani"]
        self.assertEqual(ajan["toplam_veri_haftasi"], 26)
        self.assertEqual(ajan["hafta_sayisi"], 13)
        self.assertEqual(len(ajan["kayan_13_hafta_pencereleri"]), 14)
        self.assertEqual(ajan["donem_sonu_nakit"], 740)

        sonraki = istek.model_copy(update={"rapor_tarihi": ilk_hafta + timedelta(weeks=1)})
        kayan = gelismis_ajan_analizi(sonraki)["ajanlar"]["nakit_13_hafta_ajani"]
        self.assertEqual(kayan["tahmin_baslangici"], (ilk_hafta + timedelta(weeks=1)).isoformat())
        self.assertEqual(kayan["baslangic_nakdi"], 980)
        self.assertEqual(kayan["donem_sonu_nakit"], 720)

    def test_tekrar_hafta_bas_denetci_tarafindan_engellenir(self):
        istek = ornek_istek()
        tekrarli = istek.model_copy(update={
            "haftalik_nakit": [*istek.haftalik_nakit, istek.haftalik_nakit[0]],
        })
        sonuc = gelismis_ajan_analizi(tekrarli)
        ajan = sonuc["ajanlar"]["nakit_13_hafta_ajani"]
        self.assertEqual(ajan["durum"], "inceleme_gerekli")
        self.assertTrue(ajan["tekrar_haftalar"])
        self.assertEqual(sonuc["bas_denetim"]["durum"], "engellendi")

    def test_veri_ufku_donem_kapsamini_aciklar(self):
        ufuk = self.sonuc["veri_ufku"]
        self.assertEqual(ufuk["mizan"]["donem_sayisi"], 1)
        self.assertFalse(ufuk["mizan"]["karsilastirma_hazir"])
        self.assertTrue(ufuk["nakit"]["tam_13_hafta_penceresi"])

    def test_alacak_yaslandirma_beklenen_sonuc(self):
        ajan = self.ajanlar["alacak_yaslandirma_ajani"]
        self.assertEqual(ajan["acik_alacak"], FIXTURE["alacak"]["acik_alacak"])
        for bucket in ("vadesi_gelmemis", "0_30", "61_90", "90_plus"):
            self.assertEqual(ajan["yaslandirma"][bucket], FIXTURE["alacak"][bucket])

    def test_borc_servisi_ve_dscr_beklenen_sonuc(self):
        ajan = self.ajanlar["borc_servis_ajani"]
        self.assertEqual(ajan["toplam_borc_servisi"], FIXTURE["borc"]["toplam_borc_servisi"])
        self.assertEqual(ajan["dscr"], FIXTURE["borc"]["dscr"])

    def test_butce_ve_tahmin_beklenen_sonuc(self):
        ajan = self.ajanlar["butce_tahmin_ajani"]
        self.assertEqual(ajan["toplam_butce"], FIXTURE["butce"]["toplam_butce"])
        self.assertEqual(ajan["toplam_gerceklesen"], FIXTURE["butce"]["toplam_gerceklesen"])
        self.assertEqual(ajan["sapma"], FIXTURE["butce"]["sapma"])
        self.assertEqual(ajan["yil_sonu_gerceklesme_tahmini"], FIXTURE["butce"]["yil_sonu_tahmini"])
        self.assertEqual(ajan["gecmis_tahmin_hatasi_mape"], FIXTURE["butce"]["mape"])

    def test_anomali_ajani_denetim_izi_uretir(self):
        ajan = self.ajanlar["anomali_ve_denetim_ajani"]
        self.assertEqual(len(ajan["denetim_izi"]["girdi_sha256"]), 64)
        self.assertEqual(ajan["denetim_izi"]["ajan_sayisi"], 7)

    def test_bas_denetci_mutabakat_farkinda_ai_akisini_engeller(self):
        denetim = self.sonuc["bas_denetim"]
        self.assertEqual(denetim["durum"], "engellendi")
        self.assertFalse(denetim["ai_kullanilabilir"])
        self.assertGreater(denetim["kritik_sorun_sayisi"], 0)
        self.assertTrue(
            any(k["kontrol_id"] == "mizan_finansal_gorunum_mutabakati" for k in denetim["kritikler"])
        )

    def test_bas_denetci_tutarlı_ajan_sonuclarini_onaylar(self):
        sonuclar = [
            {
                "ajan": "mizan_esleme_ajani", "durum": "tamamlandi", "mizan_farki": 0,
                "bilanco_denklemi": {"hesaplanabilir": True, "fark": 0},
            },
            {
                "ajan": "finansal_tablo_mutabakat_ajani", "durum": "tamamlandi",
                "son_donem": {"bilanco": {"denk": True, "bilanco_farki": 0}},
                "finansal_gorunum_mutabakati": {"uyusmayan_alanlar": []},
                "nakit_koprusu": {"durum": "mutabik", "fark": 0},
            },
            {
                "ajan": "alacak_yaslandirma_ajani", "durum": "tamamlandi",
                "hatali_faturalar": [], "acik_alacak": 950,
            },
            {"ajan": "nakit_13_hafta_ajani", "durum": "tamamlandi"},
            {"ajan": "borc_servis_ajani", "durum": "tamamlandi"},
            {"ajan": "butce_tahmin_ajani", "durum": "tamamlandi"},
            {"ajan": "anomali_ve_denetim_ajani", "durum": "tamamlandi", "anomaliler": []},
        ]
        denetim = bas_denetci(ornek_istek(), sonuclar)
        self.assertEqual(denetim["durum"], "onaylandi")
        self.assertTrue(denetim["ai_kullanilabilir"])
        self.assertEqual(denetim["kritik_sorun_sayisi"], 0)

    def test_bos_veride_alti_ajan_guvenli_bekler(self):
        bos = GelismisAjanIstegi(
            finansal_veri=FinansalGorunum(ciro=0, net_kar=0),
            rapor_tarihi=date(2026, 4, 30),
        )
        sonuc = gelismis_ajan_analizi(bos)
        self.assertEqual(sonuc["ozet"]["veri_bekliyor"], 6)
        self.assertEqual(sonuc["ozet"]["toplam"], 7)
        self.assertTrue(sonuc["bas_denetim"]["ai_kullanilabilir"])
        self.assertEqual(sonuc["bas_denetim"]["ai_kapsami"], "temel_finansal_gorunum")


if __name__ == "__main__":
    unittest.main()

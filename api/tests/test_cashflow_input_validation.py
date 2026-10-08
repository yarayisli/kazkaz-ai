"""Sonlu olmayan tutarların finans girdisine sızması için regresyon testleri.

Owner onaylı golden/invariant dosyalarını değiştirmez; geçersiz girdi
reddini ve mevcut geçerli istek sözleşmesinin korunmasını denetler.
"""

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import ValidationError

from cashflow_engine import CashFlowAnalysis, CashFlowInput
from api.models import (
    AlacakFaturasi, BilançoBilgisi, BorcKalemi, BorcServisSatiri,
    ButceGerceklesmeSatiri, FinansalAnalizIstegi, FinansalGorunum,
    FinansSatiri, GelismisAjanIstegi, HaftalikNakitSatiri, MizanSatiri,
    MusteriCiroSatiri, NakitAkisSatiri,
)


HATALI_TUTARLAR = (float("nan"), float("inf"), -float("inf"))


class TestNakitMotoruGirdiReddi(unittest.TestCase):
    def test_hareket_listelerinde_sonlu_olmayan_degerler_reddedilir(self):
        for alan in ("nakit_girisler", "nakit_cikislar"):
            for deger in HATALI_TUTARLAR:
                with self.subTest(alan=alan, deger=deger):
                    veri = {"nakit_girisler": [100, 200], "nakit_cikislar": [20, 30]}
                    veri[alan][1] = deger
                    with self.assertRaisesRegex(ValueError, alan):
                        CashFlowInput(**veri)

    def test_bakiye_ve_likidite_girdileri_sonlu_olmali(self):
        for alan in ("baslangic_nakiti", "donen_varliklar", "kisa_vadeli_borc", "stoklar", "alacaklar"):
            for deger in HATALI_TUTARLAR:
                with self.subTest(alan=alan, deger=deger):
                    with self.assertRaisesRegex(ValueError, alan):
                        CashFlowInput([100], [20], **{alan: deger})

    def test_gecersiz_tutarlar_sessizce_sifira_cevrilmez(self):
        for deger in (None, "bozuk", "NaN", "Infinity"):
            with self.subTest(deger=deger):
                with self.assertRaises(ValueError):
                    CashFlowInput([deger], [0])

    def test_gecerli_sayisal_verinin_mevcut_sonucu_korunur(self):
        motor = CashFlowAnalysis(CashFlowInput([1000, 1200, 1500], [800, 900, 1000], baslangic_nakiti=5000))
        self.assertEqual(motor.net_cash_flow(), [200, 300, 500])
        self.assertEqual(motor.cumulative_cash(), [5200, 5500, 6000])

    def test_iade_ve_negatif_bakiye_mevcut_motor_sozlesmesini_korur(self):
        # Bu değişiklik iade/negatif bakiye için yeni iş kuralı getirmez.
        motor = CashFlowAnalysis(CashFlowInput([-10], [-5], baslangic_nakiti=-20))
        self.assertEqual(motor.cumulative_cash(), [-25])


class TestApiSonluFinansGirdileri(unittest.TestCase):
    def test_finansal_modellerde_tum_float_alanlar_sonlu_olmali(self):
        ornekler = [
            (FinansSatiri, {"tarih": "2026-10-08", "kategori": "Test"}),
            (BilançoBilgisi, {}),
            (MusteriCiroSatiri, {"musteri_id": "m1", "musteri_adi": "Test", "ciro": 1}),
            (FinansalGorunum, {"ciro": 100, "net_kar": 10}),
            (NakitAkisSatiri, {"donem": "2026-10", "giris": 100, "cikis": 20, "net_nakit": 80}),
            (BorcKalemi, {"ad": "Test", "tutar": 1}),
            (MizanSatiri, {"donem": "2026-10", "hesap_kodu": "100", "hesap_adi": "Test"}),
            (HaftalikNakitSatiri, {"hafta": "2026-10-08"}),
            (AlacakFaturasi, {"fatura_id": "f1", "musteri_id": "m1", "musteri_adi": "Test", "fatura_tarihi": "2026-10-08", "vade_tarihi": "2026-10-09", "tutar": 1}),
            (BorcServisSatiri, {"borc_id": "b1", "alacakli": "Test", "odeme_tarihi": "2026-10-08"}),
            (ButceGerceklesmeSatiri, {"ay": "2026-10-01", "kategori": "Test"}),
            (GelismisAjanIstegi, {"finansal_veri": {"ciro": 100, "net_kar": 10}}),
        ]
        for model, veri in ornekler:
            # Önce örneğin geçerli olduğunu doğrula: ilgisiz zorunlu alan
            # hatası geçersiz tutar reddi gibi yorumlanmamalı.
            model.model_validate(veri)
            for alan, tanim in model.model_fields.items():
                if "float" not in str(tanim.annotation):
                    continue
                for deger in (*HATALI_TUTARLAR, "NaN", "Infinity", "-Infinity"):
                    with self.subTest(model=model.__name__, alan=alan, deger=deger):
                        with self.assertRaises(ValidationError) as sonuc:
                            model.model_validate({**veri, alan: deger})
                        self.assertTrue(any(hata["loc"] == (alan,) for hata in sonuc.exception.errors()))

    def test_json_icindeki_sonsuz_sayi_satis_satirinda_reddedilir(self):
        # 1e400 standart JSON sayısıdır; decoder sonucu infinity olabilir.
        veri = '{"satirlar":[{"tarih":"2026-10-08","kategori":"Test","gelir":1e400}]}'
        with self.assertRaises(ValidationError) as sonuc:
            FinansalAnalizIstegi.model_validate_json(veri)
        self.assertTrue(any(hata["loc"] == ("satirlar", 0, "gelir") for hata in sonuc.exception.errors()))

    def test_ic_ice_haftalik_nakit_girdisi_sonlu_olmali(self):
        veri = {"finansal_veri": {"ciro": 100, "net_kar": 10}, "haftalik_nakit": [{"hafta": "2026-10-08", "tahsilat": "Infinity"}]}
        with self.assertRaises(ValidationError) as sonuc:
            GelismisAjanIstegi.model_validate(veri)
        self.assertTrue(any(hata["loc"] == ("haftalik_nakit", 0, "tahsilat") for hata in sonuc.exception.errors()))

    def test_gecerli_istekte_eksik_opsiyonel_nakit_uydurulmaz(self):
        veri = FinansalGorunum(ciro=100, net_kar=-10)
        self.assertIsNone(veri.operasyonel_nakit_akisi)
        self.assertIsNone(veri.yatirim_nakit_akisi)
        self.assertEqual(veri.net_kar, -10)


class TestHttpGecersizNakitIstegi(unittest.TestCase):
    def test_sonlu_olmayan_json_tutari_500_yerine_422_doner(self):
        from api.auth import mevcut_sirket_uyesi_dogrulanmis
        from api.main import uygulama
        from api.models import KimlikBilgisi
        from api.security_middleware import hiz_limitlerini_sifirla

        onceki = dict(uygulama.dependency_overrides)
        uygulama.dependency_overrides[mevcut_sirket_uyesi_dogrulanmis] = lambda: KimlikBilgisi(
            kullanici_id="cashflow-input-test", sirket_id="cashflow-test", roller={"admin": True},
        )
        hiz_limitlerini_sifirla()
        try:
            with TestClient(uygulama, raise_server_exceptions=False) as client:
                for ham in ("1e400", "NaN", "Infinity", "-Infinity", '"NaN"', '"Infinity"'):
                    with self.subTest(ham=ham), patch("api.main.zaman_serisi_analizi") as hesap:
                        yanit = client.post(
                            "/api/v1/finans/zaman-serisi",
                            content='{"satirlar":[{"tarih":"2026-10-08","kategori":"Test","gelir":' + ham + '}] }',
                            headers={"Content-Type": "application/json"},
                        )
                        self.assertEqual(yanit.status_code, 422)
                        self.assertTrue(any(hata["loc"] == ["body", "satirlar", 0, "gelir"] for hata in yanit.json()["detail"]))
                        hesap.assert_not_called()
        finally:
            uygulama.dependency_overrides.clear()
            uygulama.dependency_overrides.update(onceki)
            hiz_limitlerini_sifirla()


if __name__ == "__main__":
    unittest.main()

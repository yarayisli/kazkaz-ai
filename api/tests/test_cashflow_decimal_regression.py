"""Ondalık hesap değişikliğinin regresyonları; owner kabul paketi yerine geçmez."""

import copy
import json
import unittest
from datetime import date, timedelta
from decimal import Decimal, localcontext
from itertools import permutations
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from api.advanced_agents import nakit_13_hafta_ajani
from api.financial_statements import _nakit_koprusu
from api.models import FinansalGorunum, GelismisAjanIstegi, HaftalikNakitSatiri
from api.nakit_aritmetik import NakitHesaplamaHatasi, para, topla
from cashflow_engine import CashFlowAnalysis, CashFlowEngine, CashFlowForecast, CashFlowInput, LiquidityMetrics


def haftalik(hareketler, **alanlar):
    return GelismisAjanIstegi(
        finansal_veri=FinansalGorunum(ciro=100, net_kar=10),
        rapor_tarihi=date(2026, 10, 12),
        haftalik_nakit=[HaftalikNakitSatiri(hafta=date(2026, 10, 12) + timedelta(weeks=i), **v)
                       for i, v in enumerate(hareketler)],
        **alanlar,
    )


class TestOndalikNakitRegresyonu(unittest.TestCase):
    def test_iptal_olan_buyuk_tutarin_yanindaki_kurus_kaybolmaz(self):
        for tutarlar in permutations([1e100, .01, -1e100]):
            with self.subTest(tutarlar=tutarlar):
                cf = CashFlowAnalysis(CashFlowInput(list(tutarlar), [0, 0, 0]))
                self.assertEqual(cf.operating_cash_flow(), .01)
                self.assertEqual(cf.cumulative_cash()[-1], .01)

    def test_kurus_toplami_ve_acilis_hareket_baglantisi(self):
        cf = CashFlowAnalysis(CashFlowInput([100.10, 200.20], [0, 0], baslangic_nakiti=10))
        self.assertEqual(cf.operating_cash_flow(), 300.30)
        self.assertEqual(cf.cumulative_cash(), [110.10, 310.30])

    def test_ara_toplam_satir_basina_yuvarlanmaz(self):
        cf = CashFlowAnalysis(CashFlowInput([.005, .005], [0, 0]))
        self.assertEqual(cf.net_cash_flow(), [.005, .005])
        self.assertEqual(cf.cumulative_cash(), [0, .01])

    def test_half_even_tie_ve_negatif_tutar(self):
        for girdi, beklenen in [('2.675', 2.68), ('2.685', 2.68), ('-2.675', -2.68)]:
            self.assertEqual(para(Decimal(girdi)), beklenen)

    def test_decimal_baglami_dusuk_hassasiyette_degisikliksiz_kalir(self):
        with localcontext() as baglam:
            baglam.prec = 6
            self.assertEqual(topla([Decimal('1e100'), Decimal('.01'), Decimal('-1e100')]), Decimal('.01'))
            self.assertEqual(para(Decimal('100.105')), 100.10)
            self.assertEqual(baglam.prec, 6)

    def test_desteklenen_sayi_araligini_asan_toplam_acikca_reddedilir(self):
        cf = CashFlowAnalysis(CashFlowInput([1e308, 1e308], [0, 0]))
        for hesap in [cf.operating_cash_flow, cf.cumulative_cash, cf.summary]:
            with self.subTest(hesap=hesap.__name__), self.assertRaises(NakitHesaplamaHatasi):
                hesap()

    def test_donem_netindeki_tasma_reddedilir(self):
        cf = CashFlowAnalysis(CashFlowInput([1e308], [-1e308]))
        with self.assertRaises(NakitHesaplamaHatasi):
            cf.net_cash_flow()

    def test_likidite_orani_tasmasi_reddedilir(self):
        liq = LiquidityMetrics(CashFlowInput([1], [0], donen_varliklar=1e308, kisa_vadeli_borc=1e-308))
        with self.assertRaises(NakitHesaplamaHatasi):
            liq.current_ratio()

    def test_projeksiyon_tasmasi_reddedilir(self):
        with self.assertRaises(NakitHesaplamaHatasi):
            CashFlowForecast(CashFlowInput([1e308], [0])).optimistic()

    def test_sifir_hareket_ve_dengeli_hareket_acilisi_korur(self):
        for giris, cikis in [([0], [0]), ([1000], [1000])]:
            self.assertEqual(CashFlowAnalysis(CashFlowInput(giris, cikis, baslangic_nakiti=100.10)).cumulative_cash(), [100.10])

    def test_pandas_aylik_gruplama_kurusu_kaybetmez(self):
        for gelirler in permutations([1e16, 1, 0]):
            veri = pd.DataFrame({'YilAy': ['2026-10'] * 3, 'Gelir': gelirler, 'Gider': [1e16, 0, 0]})
            motor = CashFlowEngine.from_financial_engine(SimpleNamespace(df=veri))
            self.assertEqual(motor.cf.operating_cash_flow(), 1)
            self.assertEqual(motor.cf.cumulative_cash(), [1])
            # Numpy/forecast yoluna Decimal sızması TypeError üretmemeli.
            motor.fc.base()

    def test_tekrarlanan_hesap_girdiyi_degistirmez(self):
        inp = CashFlowInput([100.10, 200.20], [20.05, 50.25])
        onceki = copy.deepcopy(inp)
        cf = CashFlowAnalysis(inp)
        self.assertEqual(cf.summary(), cf.summary())
        self.assertEqual(inp, onceki)


class TestHaftalikVeKopruRegresyonu(unittest.TestCase):
    def test_hafta_netinde_buyuk_tutar_kurusu_yutmaz(self):
        rapor = nakit_13_hafta_ajani(haftalik([{'tahsilat': 1e16, 'nakit_satis': 1, 'tedarikci': 1e16}], baslangic_nakdi=10))
        self.assertEqual(rapor['projeksiyon'][0]['net'], 1)
        self.assertEqual(rapor['donem_sonu_nakit'], 11)
        json.dumps(rapor, allow_nan=False)

    def test_pencere_acilisi_onceki_haftalarin_hareketini_tasir(self):
        istek = haftalik([{'tahsilat': .005}] * 15, baslangic_nakdi=100)
        istek.rapor_tarihi += timedelta(weeks=2)
        rapor = nakit_13_hafta_ajani(istek)
        self.assertEqual(rapor['baslangic_nakdi'], 100.01)
        self.assertEqual(rapor['donem_sonu_nakit'], 100.08)
        self.assertEqual(rapor['kayan_13_hafta_pencereleri'][2]['donem_sonu_nakit'], 100.08)

    def test_haftalik_girdi_sirasi_tarih_sirasindaki_sonucu_degistirmez(self):
        istek = haftalik([{'tahsilat': 100.10}, {'vergi': 20.05}, {'tahsilat': 200.20}])
        ilk = nakit_13_hafta_ajani(istek)
        istek.haftalik_nakit.reverse()
        self.assertEqual(ilk, nakit_13_hafta_ajani(istek))

    def test_haftalik_ayni_tarihli_tekrar_ve_bosluk_isaretleri_korunur(self):
        istek = haftalik([{'tahsilat': 1}, {'tahsilat': 2}])
        istek.haftalik_nakit[1].hafta += timedelta(weeks=1)
        istek.haftalik_nakit.append(copy.deepcopy(istek.haftalik_nakit[0]))
        rapor = nakit_13_hafta_ajani(istek)
        self.assertEqual(rapor['durum'], 'inceleme_gerekli')
        self.assertTrue(rapor['tekrar_haftalar'])
        self.assertTrue(rapor['hafta_bosluklari'])

    def test_haftalik_sonlu_girdinin_toplam_tasmasi_reddedilir(self):
        with self.assertRaises(NakitHesaplamaHatasi):
            nakit_13_hafta_ajani(haftalik([{'tahsilat': 1e308}, {'tahsilat': 1e308}]))

    def test_kopru_buyuk_cfo_cfi_iptalinde_kurusu_korur(self):
        rapor = _nakit_koprusu(FinansalGorunum(ciro=100, net_kar=10, nakit=.01,
            donem_basi_nakit=.01, operasyonel_nakit_akisi=1e100, yatirim_nakit_akisi=-1e100, finansman_nakit_akisi=0))
        self.assertEqual(rapor['beklenen_donem_sonu_nakit'], .01)
        self.assertEqual(rapor['fark'], 0)

    def test_kopru_hassasiyet_farki_yuvarlanmadan_degerlendirilir(self):
        # Mevcut 1 TL mutabakat toleransı değiştirilmez.
        rapor = _nakit_koprusu(FinansalGorunum(ciro=100, net_kar=10, nakit=0,
            donem_basi_nakit=1.004, operasyonel_nakit_akisi=0, yatirim_nakit_akisi=0, finansman_nakit_akisi=0))
        self.assertEqual(rapor['durum'], 'inceleme_gerekli')
        self.assertEqual(rapor['fark'], 1)


class TestApiNakitTasmasi(unittest.TestCase):
    def test_gercek_zaman_serisi_rotasi_tasmada_500_yerine_422_verir(self):
        from api.auth import mevcut_sirket_uyesi_dogrulanmis
        from api.main import uygulama
        from api.models import KimlikBilgisi
        from api.security_middleware import hiz_limitlerini_sifirla
        onceki = dict(uygulama.dependency_overrides)
        uygulama.dependency_overrides[mevcut_sirket_uyesi_dogrulanmis] = lambda: KimlikBilgisi(
            kullanici_id='decimal-test', sirket_id='decimal-test', roller={'admin': True})
        hiz_limitlerini_sifirla()
        try:
            with TestClient(uygulama, raise_server_exceptions=False) as client, patch('api.main.kullanim_olayi_kaydet') as kayit:
                for aylar in ([1, 2, 3], [1, 1, 1]):
                    with self.subTest(aylar=aylar):
                        yanit = client.post('/api/v1/finans/zaman-serisi', json={'satirlar': [
                            {'tarih': f'2026-{ay:02d}-01', 'kategori': 'Test', 'gelir': 1e308} for ay in aylar]})
                        self.assertEqual(yanit.status_code, 422, yanit.text)
                        self.assertEqual(yanit.json()['kod'], 'nakit_hesaplama_araligi')
                        kayit.assert_not_called()
        finally:
            uygulama.dependency_overrides.clear()
            uygulama.dependency_overrides.update(onceki)
            hiz_limitlerini_sifirla()

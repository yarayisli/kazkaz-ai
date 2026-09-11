import os
import unittest
from unittest.mock import MagicMock, patch

from gemini_engine import GeminiEngine
from api.ai_guardrails import ai_yanitini_dogrula
from api.ai_orchestrator import (
    ai_durumu,
    ai_yaniti_uret,
    hassas_veriyi_maskele,
    veri_kalitesini_degerlendir,
)
from api.models import FinansalGorunum
from api.services import cfo_yaniti, finansal_denetim


def tam_veri() -> FinansalGorunum:
    return FinansalGorunum(
        sirket_adi="Test A.Ş.",
        ciro=1_000_000,
        satis_maliyeti=400_000,
        faaliyet_giderleri=250_000,
        net_kar=200_000,
        nakit=150_000,
        alacaklar=250_000,
        stoklar=100_000,
        kisa_vadeli_borc=250_000,
        uzun_vadeli_borc=100_000,
        borclar=150_000,
        ozkaynak=500_000,
        faiz_gideri=25_000,
        vergi_gideri=75_000,
        amortisman=50_000,
        capex=80_000,
    )


class TestAIOrchestrator(unittest.TestCase):
    def test_ai_dogrulama_finans_motorundaki_sayilari_kabul_eder(self):
        denetim = finansal_denetim(tam_veri())
        sonuc = ai_yanitini_dogrula(
            "1. Net kâr marjı %20, cari oran 2,00; FAVÖK 350 bin TL ve brüt kâr 600 000 TL.",
            denetim,
        )
        self.assertTrue(sonuc.uygun)
        self.assertEqual(sonuc.kontrol_edilen_sayi, 4)

    def test_ai_dogrulama_kaynaksiz_hedefleri_reddeder(self):
        denetim = finansal_denetim(tam_veri())
        sonuc = ai_yanitini_dogrula(
            "Nakit döngüsünü 5-7 gün kısaltın ve 2 milyon TL tampon tutun.",
            denetim,
        )
        self.assertFalse(sonuc.uygun)
        self.assertIn("5", sonuc.reddedilen_sayilar)
        self.assertIn("7", sonuc.reddedilen_sayilar)
        self.assertIn("2 milyon", sonuc.reddedilen_sayilar)

    def test_nvidia_gpt_oss_resmi_ornekleme_ayarlarini_kullanir(self):
        motor = GeminiEngine.__new__(GeminiEngine)
        motor.provider = "nvidia"
        motor._model = "openai/gpt-oss-120b"
        self.assertEqual(motor._sampling_options(), {"temperature": 1.0, "top_p": 1.0, "reasoning_effort": "low"})

    def test_nvidia_20b_v1_dusuk_gecikme_ayarlarini_kullanir(self):
        motor = GeminiEngine.__new__(GeminiEngine)
        motor.provider = "nvidia"
        motor._model = "openai/gpt-oss-20b"
        self.assertEqual(motor._sampling_options(), {"temperature": 1.0, "top_p": 1.0, "reasoning_effort": "low"})

    def test_nvidia_durumda_birincil_ve_anahtarsiz_listelenir(self):
        with patch.dict(
            os.environ,
            {
                "AI_PROVIDER_ORDER": "nvidia,groq,gemini",
                "NVIDIA_API_KEY": "nvapi-test-secret",
            },
            clear=False,
        ):
            durum = ai_durumu()

        self.assertEqual(durum["saglayicilar"][0]["ad"], "nvidia")
        self.assertEqual(durum["saglayicilar"][0]["rol"], "birincil")
        self.assertTrue(durum["saglayicilar"][0]["hazir"])
        self.assertNotIn("nvapi-test-secret", str(durum))

    def test_nvidia_birincil_saglayici_olarak_kullanilir(self):
        veri = tam_veri()
        kalite = veri_kalitesini_degerlendir(veri)
        denetim = finansal_denetim(veri)
        nvidia = MagicMock()
        nvidia.generate.return_value = "Doğrulanmış NVIDIA açıklaması."
        nvidia.model_name = "meta/llama-test"

        with patch.dict(
            os.environ,
            {
                "AI_PROVIDER_ORDER": "nvidia,groq,gemini",
                "NVIDIA_API_KEY": "nvapi-test-secret",
                "GROQ_API_KEY": "",
                "GEMINI_API_KEY": "",
            },
            clear=False,
        ), patch("api.ai_orchestrator.GeminiEngine", return_value=nvidia) as motor:
            sonuc = ai_yaniti_uret("Nakit durumunu açıkla", denetim, kalite)

        motor.assert_called_once_with(api_key="nvapi-test-secret", provider="nvidia")
        self.assertEqual(sonuc.saglayici, "nvidia")
        self.assertFalse(sonuc.yedek_kullanildi)
        self.assertEqual(sonuc.model, "meta/llama-test")

    def test_nvidia_hatasinda_groq_yedegi_kullanilir(self):
        veri = tam_veri()
        kalite = veri_kalitesini_degerlendir(veri)
        denetim = finansal_denetim(veri)

        nvidia = MagicMock()
        nvidia.generate.return_value = "⚠️ geçici NVIDIA hatası"
        nvidia.model_name = "meta/llama-test"
        groq = MagicMock()
        groq.generate.return_value = "Doğrulanmış Groq yedek açıklaması."
        groq.model_name = "llama-groq-test"

        with patch.dict(
            os.environ,
            {
                "AI_PROVIDER_ORDER": "nvidia,groq,gemini",
                "NVIDIA_API_KEY": "nvapi-test-secret",
                "GROQ_API_KEY": "gsk-test-secret",
                "GEMINI_API_KEY": "",
            },
            clear=False,
        ), patch("api.ai_orchestrator.GeminiEngine", side_effect=[nvidia, groq]):
            sonuc = ai_yaniti_uret("Nakit durumunu açıkla", denetim, kalite)

        self.assertEqual(sonuc.saglayici, "groq")
        self.assertTrue(sonuc.yedek_kullanildi)
        self.assertEqual(sonuc.hatalar, ["nvidia:RuntimeError"])

    def test_nvidia_kaynaksiz_sayi_uretirsa_groq_yedegi_kullanilir(self):
        veri = tam_veri()
        kalite = veri_kalitesini_degerlendir(veri)
        denetim = finansal_denetim(veri)

        nvidia = MagicMock()
        nvidia.generate.return_value = "Nakit tamponunu 2 milyon TL seviyesine çıkarın."
        nvidia.model_name = "nvidia-test"
        groq = MagicMock()
        groq.generate.return_value = "Cari oran 2,00 seviyesinde; doğrulanmış likiditeyi izleyin."
        groq.model_name = "groq-test"

        with patch.dict(
            os.environ,
            {
                "AI_PROVIDER_ORDER": "nvidia,groq,gemini",
                "NVIDIA_API_KEY": "nvapi-test-secret",
                "GROQ_API_KEY": "gsk-test-secret",
                "GEMINI_API_KEY": "",
            },
            clear=False,
        ), patch("api.ai_orchestrator.GeminiEngine", side_effect=[nvidia, groq]):
            sonuc = ai_yaniti_uret("Nakit durumunu açıkla", denetim, kalite)

        self.assertEqual(sonuc.saglayici, "groq")
        self.assertTrue(sonuc.yedek_kullanildi)
        self.assertEqual(sonuc.dogrulama_durumu, "dogrulandi")
        self.assertEqual(sonuc.hatalar, ["nvidia:AIYanitiDogrulamaHatasi"])

    def test_tum_saglayicilar_kaynaksiz_sayi_uretirsa_kuralli_ozete_doner(self):
        veri = tam_veri()
        kalite = veri_kalitesini_degerlendir(veri)
        denetim = finansal_denetim(veri)
        nvidia = MagicMock()
        nvidia.generate.return_value = "Ödemeleri 45 güne çıkarın."
        nvidia.model_name = "nvidia-test"

        with patch.dict(
            os.environ,
            {
                "AI_PROVIDER_ORDER": "nvidia",
                "NVIDIA_API_KEY": "nvapi-test-secret",
                "GROQ_API_KEY": "",
                "GEMINI_API_KEY": "",
            },
            clear=False,
        ), patch("api.ai_orchestrator.GeminiEngine", return_value=nvidia):
            sonuc = ai_yaniti_uret("Nakit durumunu açıkla", denetim, kalite)

        self.assertEqual(sonuc.saglayici, "kuralli_finans_motoru")
        self.assertEqual(sonuc.dogrulama_durumu, "kuralli_yedek")
        self.assertEqual(sonuc.reddedilen_sayilar, ["45"])

    def test_hassas_veri_saglayici_oncesi_maskelenir(self):
        metin = hassas_veriyi_maskele(
            "ali@example.com ve TR120006200000000000000001 hesabı, 12345678901"
        )
        self.assertNotIn("ali@example.com", metin)
        self.assertNotIn("12345678901", metin)
        self.assertIn("[E-POSTA]", metin)
        self.assertIn("[IBAN]", metin)

    def test_anahtar_yoksa_kuralli_motor_kullanilir(self):
        with patch.dict(
            os.environ,
            {"GROQ_API_KEY": "", "GEMINI_API_KEY": "", "AI_PROVIDER_ORDER": "groq,gemini"},
            clear=False,
        ):
            sonuc = cfo_yaniti("Durumumuz nasıl?", tam_veri())
        self.assertEqual(sonuc["kaynak"], "kuralli_finans_motoru")
        self.assertIn("doğrulanmış finans motoru", sonuc["yanit"])

    def test_yetersiz_veri_ai_cagrisini_engeller(self):
        veri = FinansalGorunum(ciro=0, net_kar=0)
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk-test"}, clear=False), patch(
            "api.ai_orchestrator.GeminiEngine"
        ) as motor:
            sonuc = cfo_yaniti("Ne yapmalıyım?", veri)
        motor.assert_not_called()
        self.assertEqual(sonuc["guven"], "dusuk")
        self.assertIn("AI yorumu üretilmedi", sonuc["yanit"])

    def test_bas_denetci_kritik_mutabakatta_ai_cagrisini_engeller(self):
        ajan_denetimi = {
            "ai_kullanilabilir": False,
            "kritikler": [
                {"mesaj": "Mizan ile finansal görünüm arasında kritik fark var."},
            ],
        }
        with patch.dict(os.environ, {"NVIDIA_API_KEY": "nvapi-test"}, clear=False), patch(
            "api.ai_orchestrator.GeminiEngine"
        ) as motor:
            sonuc = cfo_yaniti("Durumumuz nasıl?", tam_veri(), ajan_denetimi)
        motor.assert_not_called()
        self.assertEqual(sonuc["kaynak"], "bas_denetci")
        self.assertEqual(sonuc["ai_dogrulama"]["durum"], "ajan_engeli")
        self.assertIn("kritik fark", sonuc["yanit"])

    def test_groq_hatasinda_gemini_yedegi_kullanilir(self):
        veri = tam_veri()
        kalite = veri_kalitesini_degerlendir(veri)
        denetim = finansal_denetim(veri)

        groq = MagicMock()
        groq.generate.return_value = "⚠️ geçici hata"
        groq.model_name = "llama-test"
        gemini = MagicMock()
        gemini.generate.return_value = "Doğrulanmış metriklere dayalı açıklama."
        gemini.model_name = "gemini-test"

        with patch.dict(
            os.environ,
            {
                "AI_PROVIDER_ORDER": "groq,gemini",
                "GROQ_API_KEY": "gsk-test",
                "GEMINI_API_KEY": "gemini-test-key",
            },
            clear=False,
        ), patch("api.ai_orchestrator.GeminiEngine", side_effect=[groq, gemini]):
            sonuc = ai_yaniti_uret("Nakit durumunu açıkla", denetim, kalite)

        self.assertEqual(sonuc.saglayici, "gemini")
        self.assertTrue(sonuc.yedek_kullanildi)
        self.assertEqual(sonuc.model, "gemini-test")


if __name__ == "__main__":
    unittest.main()


class TestKaynakKilidi(unittest.TestCase):
    """Guardrail hem ham girdileri kabul etmeli hem kaynağını söylemeli."""

    def test_kullanicinin_bildirdigi_ham_degerler_kabul_edilir(self):
        denetim = finansal_denetim(tam_veri())
        sonuc = ai_yanitini_dogrula("Kasanızda 150.000 TL nakit ve 250.000 TL alacak var.", denetim)
        self.assertTrue(sonuc.uygun, f"reddedilenler: {sonuc.reddedilen_sayilar}")

    def test_ciro_ve_ozkaynak_da_izinli(self):
        denetim = finansal_denetim(tam_veri())
        sonuc = ai_yanitini_dogrula("Ciro 1.000.000 TL, özkaynak 500.000 TL.", denetim)
        self.assertTrue(sonuc.uygun, f"reddedilenler: {sonuc.reddedilen_sayilar}")

    def test_uydurma_sayi_hala_reddedilir(self):
        denetim = finansal_denetim(tam_veri())
        sonuc = ai_yanitini_dogrula("Nakit tamponunu 2.000.000 TL'ye çıkarın.", denetim)
        self.assertFalse(sonuc.uygun)
        self.assertIn("2.000.000", sonuc.reddedilen_sayilar)

    def test_kabul_edilen_sayinin_kaynagi_raporlanir(self):
        denetim = finansal_denetim(tam_veri())
        sonuc = ai_yanitini_dogrula("Kasanızda 150.000 TL nakit var.", denetim)
        kaynaklar = {e.ham: e.kaynak for e in sonuc.kaynak_eslesmeleri}
        self.assertEqual(kaynaklar.get("150.000"), "Bilanço · Hazır değerler")

    def test_hesaplanmis_metrigin_kaynagi_ayirt_edilir(self):
        denetim = finansal_denetim(tam_veri())
        sonuc = ai_yanitini_dogrula("Cari oranınız 2,00 seviyesinde.", denetim)
        kaynaklar = {e.ham: e.kaynak for e in sonuc.kaynak_eslesmeleri}
        self.assertEqual(kaynaklar.get("2,00"), "Hesaplandı · Cari oran")

    def test_reddedilen_sayi_kaynak_listesine_girmez(self):
        denetim = finansal_denetim(tam_veri())
        sonuc = ai_yanitini_dogrula("Nakit 150.000 TL, hedef 2.000.000 TL.", denetim)
        self.assertFalse(sonuc.uygun)
        self.assertNotIn("2.000.000", [e.ham for e in sonuc.kaynak_eslesmeleri])
        self.assertIn("150.000", [e.ham for e in sonuc.kaynak_eslesmeleri])


class TestKaynakEslesmesiUctanUca(unittest.TestCase):
    """kaynak_eslesmeleri guardrail'den API cevabına kadar taşınmalı."""

    def _sahte_saglayici(self, cevap: str):
        motor = MagicMock()
        motor.generate.return_value = cevap
        motor.model_name = "test-model"
        return motor

    def test_cfo_yaniti_kabul_edilen_sayilarin_kaynagini_dondurur(self):
        veri = tam_veri()
        motor = self._sahte_saglayici("Kasanızda 150.000 TL nakit var, cari oranınız 2,00.")

        with patch.dict(
            os.environ,
            {"AI_PROVIDER_ORDER": "groq", "GROQ_API_KEY": "test", "NVIDIA_API_KEY": "", "GEMINI_API_KEY": ""},
            clear=False,
        ), patch("api.ai_orchestrator.GeminiEngine", return_value=motor):
            yanit = cfo_yaniti("Nakit durumu nedir?", veri)

        eslesmeler = yanit["ai_dogrulama"]["kaynak_eslesmeleri"]
        kaynaklar = {e["ham"]: e["kaynak"] for e in eslesmeler}
        self.assertEqual(kaynaklar.get("150.000"), "Bilanço · Hazır değerler")
        self.assertEqual(kaynaklar.get("2,00"), "Hesaplandı · Cari oran")
        self.assertEqual(yanit["ai_dogrulama"]["durum"], "dogrulandi")

    def test_uydurma_sayi_yaniti_engeller_ve_kaynak_listesinde_yer_almaz(self):
        veri = tam_veri()
        motor = self._sahte_saglayici("Nakit tamponunu 2.000.000 TL'ye çıkarın.")

        with patch.dict(
            os.environ,
            {"AI_PROVIDER_ORDER": "groq", "GROQ_API_KEY": "test", "NVIDIA_API_KEY": "", "GEMINI_API_KEY": ""},
            clear=False,
        ), patch("api.ai_orchestrator.GeminiEngine", return_value=motor):
            yanit = cfo_yaniti("Ne kadar tampon ayırmalıyım?", veri)

        dogrulama = yanit["ai_dogrulama"]
        self.assertEqual(dogrulama["durum"], "kuralli_yedek")
        self.assertIn("2.000.000", dogrulama["reddedilen_sayilar"])
        self.assertNotIn("2.000.000", [e["ham"] for e in dogrulama["kaynak_eslesmeleri"]])


class TestSaglikSkoruUcu(unittest.TestCase):
    """Sağlık skoru zaman serisi ucundan gelmeli; müşteri sütunu 5. boyutu açmalı."""

    @staticmethod
    def _satirlar(musteri_ile: bool):
        musteriler = [('Aygaz', 1_900_000), ('Mercan', 850_000), ('Toros', 550_000)]
        satirlar = []
        for ay in range(1, 13):
            for ad, gelir in musteriler:
                satir = {
                    "tarih": f"2025-{ay:02d}-15", "kategori": ad,
                    "gelir": gelir, "gider": int(gelir * 0.62),
                }
                if musteri_ile:
                    satir["musteri"] = ad
                satirlar.append(satir)
        return satirlar

    def _skor(self, musteri_ile: bool):
        from api.models import FinansalAnalizIstegi
        from api.services import zaman_serisi_analizi
        istek = FinansalAnalizIstegi(satirlar=self._satirlar(musteri_ile))
        return zaman_serisi_analizi(istek)["finansal"]["saglik_skoru"]

    def test_musteri_sutunu_besinci_boyutu_acar(self):
        skor = self._skor(musteri_ile=True)
        self.assertEqual(skor["metodoloji"]["boyut_sayisi"], 5)
        self.assertIn("konsantrasyon", skor["alt_skorlar"])

    def test_musteri_yoksa_dort_boyutta_kalir(self):
        skor = self._skor(musteri_ile=False)
        self.assertEqual(skor["metodoloji"]["boyut_sayisi"], 4)
        self.assertNotIn("konsantrasyon", skor["alt_skorlar"])

    def test_skor_ve_kategori_uretilir(self):
        skor = self._skor(musteri_ile=True)
        self.assertIsInstance(skor["skor"], float)
        self.assertGreaterEqual(skor["skor"], 0)
        self.assertLessEqual(skor["skor"], 100)
        self.assertTrue(skor["kategori"])

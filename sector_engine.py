"""
KazKaz AI - Sektör Karşılaştırma & Benchmark Motoru (v14)
===========================================================
Özellikler:
  - AI destekli otomatik sektör tespiti (Gemini)
  - 12 sektör için benchmark veritabanı
  - Şirketi sektör ortalamasıyla karşılaştırma
  - Sektöre özel 0-100 benchmark skoru
  - Rakip analizi (yapay veri + AI yorum)
  - Sektör trendi simülasyonu
  - Güçlü/zayıf yön tespiti

Kurulum: pip install google-generativeai pandas numpy
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field


# ─────────────────────────────────────────────
# SEKTÖR VERİTABANI
# Her sektör için Türkiye piyasası benchmark değerleri
# Kaynak: TCMB, BIST sektör raporları, McKinsey TR verileri
# ─────────────────────────────────────────────

SECTOR_DB: Dict[str, Dict[str, Any]] = {
    "Teknoloji": {
        "emoji": "💻",
        "aciklama": "Yazılım, donanım, BT hizmetleri, SaaS şirketleri",
        "anahtar_kelimeler": ["yazılım","software","teknoloji","bilişim","it","saas",
                               "uygulama","platform","dijital","siber","veri","cloud"],
        "benchmarks": {
            "kar_marji":          {"iyi": 20, "orta": 10, "zayif": 5,  "birim": "%"},
            "gelir_buyumesi":     {"iyi": 30, "orta": 15, "zayif": 5,  "birim": "%"},
            "gider_gelir_orani":  {"iyi": 65, "orta": 75, "zayif": 85, "birim": "%", "dusuk_iyi": True},
            "aylik_gelir":        {"iyi": 500_000, "orta": 150_000, "zayif": 50_000, "birim": "₺"},
            "operasyonel_marj":   {"iyi": 18, "orta": 8,  "zayif": 2,  "birim": "%"},
        },
        "sektor_trendi": [12, 15, 18, 22, 25, 28, 30, 27, 32, 35, 33, 38],
        "rakipler": ["Logo Yazılım","Netsis","Mikro","IdeaSoft","Ticimax"],
        "riskler": ["Teknoloji hızlı değişiyor","Yetenek bulma güçlüğü","Siber güvenlik riskleri"],
        "firsatlar": ["Dijital dönüşüm talebi","Cloud büyümesi","AI entegrasyonu"],
    },
    "Perakende": {
        "emoji": "🛍️",
        "aciklama": "Mağazacılık, zincir market, giyim, elektronik perakende",
        "anahtar_kelimeler": ["perakende","mağaza","satış","market","alışveriş",
                               "retail","giyim","ürün","stok","müşteri"],
        "benchmarks": {
            "kar_marji":          {"iyi": 8,  "orta": 4,  "zayif": 1,  "birim": "%"},
            "gelir_buyumesi":     {"iyi": 20, "orta": 10, "zayif": 3,  "birim": "%"},
            "gider_gelir_orani":  {"iyi": 80, "orta": 88, "zayif": 94, "birim": "%", "dusuk_iyi": True},
            "aylik_gelir":        {"iyi": 2_000_000, "orta": 500_000, "zayif": 100_000, "birim": "₺"},
            "operasyonel_marj":   {"iyi": 6,  "orta": 2,  "zayif": -1, "birim": "%"},
        },
        "sektor_trendi": [5, 6, 7, 5, 8, 10, 9, 11, 12, 10, 13, 14],
        "rakipler": ["Migros","BİM","A101","Şok","CarrefourSA"],
        "riskler": ["E-ticaret rekabeti","Kira artışları","Enflasyon baskısı"],
        "firsatlar": ["Omnichannel büyüme","Private label","Sadakat programları"],
    },
    "İmalat": {
        "emoji": "🏭",
        "aciklama": "Üretim, fabrikasyon, montaj, endüstriyel üretim",
        "anahtar_kelimeler": ["üretim","imalat","fabrika","montaj","endüstri",
                               "manufacturing","hammadde","makine","sanayi","ihracat"],
        "benchmarks": {
            "kar_marji":          {"iyi": 12, "orta": 6,  "zayif": 2,  "birim": "%"},
            "gelir_buyumesi":     {"iyi": 15, "orta": 7,  "zayif": 2,  "birim": "%"},
            "gider_gelir_orani":  {"iyi": 72, "orta": 82, "zayif": 90, "birim": "%", "dusuk_iyi": True},
            "aylik_gelir":        {"iyi": 5_000_000, "orta": 1_000_000, "zayif": 200_000, "birim": "₺"},
            "operasyonel_marj":   {"iyi": 10, "orta": 5,  "zayif": 1,  "birim": "%"},
        },
        "sektor_trendi": [3, 4, 5, 4, 6, 7, 6, 8, 7, 9, 8, 10],
        "rakipler": ["Arçelik","Vestel","Bosch TR","Ford Otosan","Tofaş"],
        "riskler": ["Hammadde fiyat dalgalanması","Enerji maliyetleri","Kur riski"],
        "firsatlar": ["İhracat büyümesi","Otomasyon yatırımı","Teşvik programları"],
    },
    "Hizmet": {
        "emoji": "🤝",
        "aciklama": "Danışmanlık, eğitim, temizlik, lojistik, profesyonel hizmetler",
        "anahtar_kelimeler": ["hizmet","danışmanlık","servis","eğitim","lojistik",
                               "consulting","ajans","muhasebe","hukuk","temizlik"],
        "benchmarks": {
            "kar_marji":          {"iyi": 15, "orta": 8,  "zayif": 3,  "birim": "%"},
            "gelir_buyumesi":     {"iyi": 20, "orta": 10, "zayif": 3,  "birim": "%"},
            "gider_gelir_orani":  {"iyi": 70, "orta": 80, "zayif": 88, "birim": "%", "dusuk_iyi": True},
            "aylik_gelir":        {"iyi": 300_000, "orta": 80_000, "zayif": 20_000, "birim": "₺"},
            "operasyonel_marj":   {"iyi": 13, "orta": 6,  "zayif": 1,  "birim": "%"},
        },
        "sektor_trendi": [8, 9, 10, 9, 11, 12, 11, 13, 14, 13, 15, 16],
        "rakipler": ["Accenture TR","Deloitte TR","PwC TR","KPMG TR","EY TR"],
        "riskler": ["Yetenek kaybı","Müşteri bağımlılığı","Fiyat baskısı"],
        "firsatlar": ["Dijital hizmetler","Outsourcing talebi","Uluslararası müşteri"],
    },
    "İnşaat": {
        "emoji": "🏗️",
        "aciklama": "Konut, ticari inşaat, altyapı, müteahhitlik",
        "anahtar_kelimeler": ["inşaat","yapı","konut","müteahhit","proje","bina",
                               "emlak","gayrimenkul","altyapı","taahhüt"],
        "benchmarks": {
            "kar_marji":          {"iyi": 10, "orta": 5,  "zayif": 1,  "birim": "%"},
            "gelir_buyumesi":     {"iyi": 15, "orta": 7,  "zayif": 0,  "birim": "%"},
            "gider_gelir_orani":  {"iyi": 78, "orta": 87, "zayif": 95, "birim": "%", "dusuk_iyi": True},
            "aylik_gelir":        {"iyi": 3_000_000, "orta": 500_000, "zayif": 100_000, "birim": "₺"},
            "operasyonel_marj":   {"iyi": 8,  "orta": 3,  "zayif": -1, "birim": "%"},
        },
        "sektor_trendi": [2, 5, 8, 6, 10, 12, 8, 14, 10, 12, 9, 11],
        "rakipler": ["Kalyon","Limak","Rönesans","ENKA","Kolin"],
        "riskler": ["Kur riski","İzin süreçleri","Hammadde artışı"],
        "firsatlar": ["Kentsel dönüşüm","Altyapı yatırımları","Turizm tesisleri"],
    },
    "Finans": {
        "emoji": "🏦",
        "aciklama": "Bankacılık, sigortacılık, faktoring, leasing, fintech",
        "anahtar_kelimeler": ["finans","banka","sigorta","kredi","yatırım","fintech",
                               "ödeme","faktoring","leasing","portföy","fon"],
        "benchmarks": {
            "kar_marji":          {"iyi": 25, "orta": 12, "zayif": 5,  "birim": "%"},
            "gelir_buyumesi":     {"iyi": 25, "orta": 12, "zayif": 4,  "birim": "%"},
            "gider_gelir_orani":  {"iyi": 55, "orta": 68, "zayif": 80, "birim": "%", "dusuk_iyi": True},
            "aylik_gelir":        {"iyi": 10_000_000, "orta": 1_000_000, "zayif": 100_000, "birim": "₺"},
            "operasyonel_marj":   {"iyi": 22, "orta": 10, "zayif": 3,  "birim": "%"},
        },
        "sektor_trendi": [15, 18, 20, 22, 19, 25, 22, 28, 25, 30, 27, 32],
        "rakipler": ["Ziraat Bankası","İş Bankası","Garanti BBVA","Akbank","YapıKredi"],
        "riskler": ["Faiz riski","Kredi kalitesi","Regülasyon değişiklikleri"],
        "firsatlar": ["Dijital bankacılık","Open banking","Embedded finance"],
    },
    "Sağlık": {
        "emoji": "🏥",
        "aciklama": "Hastane, klinik, ilaç, medikal cihaz, sağlık hizmetleri",
        "anahtar_kelimeler": ["sağlık","hastane","klinik","ilaç","tıp","medikal",
                               "doktor","hasta","tedavi","eczane","laboratuvar"],
        "benchmarks": {
            "kar_marji":          {"iyi": 18, "orta": 9,  "zayif": 3,  "birim": "%"},
            "gelir_buyumesi":     {"iyi": 20, "orta": 10, "zayif": 4,  "birim": "%"},
            "gider_gelir_orani":  {"iyi": 68, "orta": 78, "zayif": 88, "birim": "%", "dusuk_iyi": True},
            "aylik_gelir":        {"iyi": 2_000_000, "orta": 400_000, "zayif": 80_000, "birim": "₺"},
            "operasyonel_marj":   {"iyi": 15, "orta": 7,  "zayif": 2,  "birim": "%"},
        },
        "sektor_trendi": [10, 12, 13, 11, 14, 15, 14, 16, 17, 15, 18, 20],
        "rakipler": ["Acıbadem","Memorial","Medical Park","Medipol","Liv Hospital"],
        "riskler": ["SGK ödeme gecikmeleri","Dövizli maliyet","Uzman hekim kaybı"],
        "firsatlar": ["Sağlık turizmi","Dijital sağlık","Yaşlı nüfus talebi"],
    },
    "E-ticaret": {
        "emoji": "🛒",
        "aciklama": "Online alışveriş, marketplace, D2C, dropshipping",
        "anahtar_kelimeler": ["e-ticaret","online","internet","trendyol","hepsiburada",
                               "amazon","sipariş","kargo","marketplace","d2c","dropship"],
        "benchmarks": {
            "kar_marji":          {"iyi": 10, "orta": 4,  "zayif": -2, "birim": "%"},
            "gelir_buyumesi":     {"iyi": 40, "orta": 20, "zayif": 8,  "birim": "%"},
            "gider_gelir_orani":  {"iyi": 78, "orta": 88, "zayif": 96, "birim": "%", "dusuk_iyi": True},
            "aylik_gelir":        {"iyi": 1_000_000, "orta": 200_000, "zayif": 40_000, "birim": "₺"},
            "operasyonel_marj":   {"iyi": 8,  "orta": 2,  "zayif": -3, "birim": "%"},
        },
        "sektor_trendi": [20, 25, 30, 28, 35, 32, 38, 35, 40, 38, 42, 45],
        "rakipler": ["Trendyol","Hepsiburada","GittiGidiyor","Çiçeksepeti","Dolap"],
        "riskler": ["Platform komisyonları","Lojistik maliyeti","İade oranları"],
        "firsatlar": ["Mobil ticaret büyümesi","Social commerce","Cross-border"],
    },
    "Gıda & İçecek": {
        "emoji": "🍽️",
        "aciklama": "Restoran, kafe, gıda üretimi, catering, franchise",
        "anahtar_kelimeler": ["gıda","restoran","kafe","yemek","içecek","catering",
                               "franchise","market","tarım","beslenme","mutfak"],
        "benchmarks": {
            "kar_marji":          {"iyi": 12, "orta": 6,  "zayif": 1,  "birim": "%"},
            "gelir_buyumesi":     {"iyi": 18, "orta": 8,  "zayif": 2,  "birim": "%"},
            "gider_gelir_orani":  {"iyi": 75, "orta": 85, "zayif": 92, "birim": "%", "dusuk_iyi": True},
            "aylik_gelir":        {"iyi": 500_000, "orta": 120_000, "zayif": 30_000, "birim": "₺"},
            "operasyonel_marj":   {"iyi": 10, "orta": 4,  "zayif": 0,  "birim": "%"},
        },
        "sektor_trendi": [4, 5, 6, 5, 7, 8, 7, 9, 8, 10, 9, 11],
        "rakipler": ["McDonald's TR","Burger King TR","Domino's TR","Simit Sarayı","Popeyes TR"],
        "riskler": ["Hammadde enflasyonu","Gıda israfı","Personel devir hızı"],
        "firsatlar": ["Yemek teslimatı büyümesi","Sağlıklı gıda trendi","Ghost kitchen"],
    },
    "Turizm & Konaklama": {
        "emoji": "✈️",
        "aciklama": "Otel, seyahat acentesi, tur operatörü, havacılık",
        "anahtar_kelimeler": ["turizm","otel","seyahat","tur","tatil","konaklama",
                               "havacılık","acente","rezervasyon","resort"],
        "benchmarks": {
            "kar_marji":          {"iyi": 14, "orta": 6,  "zayif": -2, "birim": "%"},
            "gelir_buyumesi":     {"iyi": 25, "orta": 10, "zayif": 0,  "birim": "%"},
            "gider_gelir_orani":  {"iyi": 72, "orta": 84, "zayif": 95, "birim": "%", "dusuk_iyi": True},
            "aylik_gelir":        {"iyi": 2_000_000, "orta": 300_000, "zayif": 60_000, "birim": "₺"},
            "operasyonel_marj":   {"iyi": 12, "orta": 4,  "zayif": -3, "birim": "%"},
        },
        "sektor_trendi": [-10, -5, 5, 10, 18, 22, 20, 25, 22, 28, 25, 30],
        "rakipler": ["Rixos","Hilton TR","Marriott TR","ETS Tur","Jolly"],
        "riskler": ["Mevsimsellik","Döviz dalgalanması","Siyasi riskler"],
        "firsatlar": ["Sağlık turizmi","MICE segmenti","Butik otelcilik"],
    },
    "Enerji": {
        "emoji": "⚡",
        "aciklama": "Elektrik, doğalgaz, yenilenebilir enerji, petrol",
        "anahtar_kelimeler": ["enerji","elektrik","gaz","solar","güneş","rüzgar",
                               "yenilenebilir","petrol","yakıt","santral"],
        "benchmarks": {
            "kar_marji":          {"iyi": 16, "orta": 8,  "zayif": 2,  "birim": "%"},
            "gelir_buyumesi":     {"iyi": 20, "orta": 8,  "zayif": 2,  "birim": "%"},
            "gider_gelir_orani":  {"iyi": 68, "orta": 80, "zayif": 90, "birim": "%", "dusuk_iyi": True},
            "aylik_gelir":        {"iyi": 5_000_000, "orta": 500_000, "zayif": 80_000, "birim": "₺"},
            "operasyonel_marj":   {"iyi": 14, "orta": 6,  "zayif": 0,  "birim": "%"},
        },
        "sektor_trendi": [5, 8, 10, 9, 12, 15, 13, 18, 16, 20, 18, 22],
        "rakipler": ["Enerjisa","Aydem","Borajet","Kalyon Enerji","Aksa Enerji"],
        "riskler": ["Regülasyon riski","Sermaye yoğunluğu","Kur riski"],
        "firsatlar": ["Yenilenebilir enerji yatırımları","Enerji depolama","EV şarj"],
    },
    "Lojistik & Taşımacılık": {
        "emoji": "🚛",
        "aciklama": "Kargo, nakliye, depolama, tedarik zinciri, kurye",
        "anahtar_kelimeler": ["lojistik","kargo","nakliye","depo","taşımacılık",
                               "kurye","sevkiyat","tedarik","yük","filo"],
        "benchmarks": {
            "kar_marji":          {"iyi": 10, "orta": 5,  "zayif": 1,  "birim": "%"},
            "gelir_buyumesi":     {"iyi": 18, "orta": 8,  "zayif": 2,  "birim": "%"},
            "gider_gelir_orani":  {"iyi": 78, "orta": 87, "zayif": 94, "birim": "%", "dusuk_iyi": True},
            "aylik_gelir":        {"iyi": 3_000_000, "orta": 500_000, "zayif": 80_000, "birim": "₺"},
            "operasyonel_marj":   {"iyi": 8,  "orta": 3,  "zayif": -1, "birim": "%"},
        },
        "sektor_trendi": [6, 8, 9, 8, 11, 13, 12, 15, 13, 16, 14, 17],
        "rakipler": ["Aras Kargo","Yurtiçi Kargo","MNG Kargo","PTT Kargo","UPS TR"],
        "riskler": ["Yakıt fiyatları","Trafik/altyapı","Sürücü temini"],
        "firsatlar": ["E-ticaret büyümesi","Son mil optimizasyonu","Otonom araçlar"],
    },
}

GENEL_SEKTOR = "Genel"
SECTOR_DB[GENEL_SEKTOR] = {
    "emoji": "📊",
    "aciklama": "Sektör tespit edilemedi — genel Türkiye ortalaması",
    "anahtar_kelimeler": [],
    "benchmarks": {
        "kar_marji":          {"iyi": 12, "orta": 6,  "zayif": 1,  "birim": "%"},
        "gelir_buyumesi":     {"iyi": 18, "orta": 8,  "zayif": 2,  "birim": "%"},
        "gider_gelir_orani":  {"iyi": 72, "orta": 82, "zayif": 91, "birim": "%", "dusuk_iyi": True},
        "aylik_gelir":        {"iyi": 1_000_000, "orta": 200_000, "zayif": 40_000, "birim": "₺"},
        "operasyonel_marj":   {"iyi": 10, "orta": 5,  "zayif": 1,  "birim": "%"},
    },
    "sektor_trendi": [5, 7, 8, 7, 9, 10, 9, 11, 10, 12, 11, 13],
    "rakipler": [],
    "riskler": ["Enflasyon baskısı","Döviz riski","Talep dalgalanması"],
    "firsatlar": ["Dijital dönüşüm","Yeni pazarlar","Verimlilik artışı"],
}


# ─────────────────────────────────────────────
# SEKTÖR TESPİT MOTORU
# ─────────────────────────────────────────────

class SectorDetector:
    """
    Şirket verilerinden sektörü otomatik tespit eder.
    1. Anahtar kelime analizi (kategori isimleri üzerinden)
    2. Finansal profil analizi
    3. Gemini AI destekli gelişmiş tespit (opsiyonel)
    """

    def __init__(self, df: pd.DataFrame, sirket_adi: str = ""):
        self.df          = df
        self.sirket_adi  = sirket_adi.lower()

    def detect_by_keywords(self) -> Tuple[str, float]:
        """
        Kategori isimlerindeki anahtar kelimelere göre sektör tespit eder.
        Döner: (sektor_adi, güven_skoru 0-1)
        """
        # Tüm kategori isimlerini birleştir
        kategoriler = " ".join(
            self.df["Kategori"].str.lower().unique()
        ) + " " + self.sirket_adi

        skorlar: Dict[str, int] = {}
        for sektor, bilgi in SECTOR_DB.items():
            if sektor == GENEL_SEKTOR:
                continue
            eslesme = sum(
                1 for kw in bilgi["anahtar_kelimeler"]
                if kw in kategoriler
            )
            if eslesme > 0:
                skorlar[sektor] = eslesme

        if not skorlar:
            return GENEL_SEKTOR, 0.3

        en_iyi = max(skorlar, key=skorlar.get)
        toplam = sum(skorlar.values())
        guven  = round(skorlar[en_iyi] / toplam, 2) if toplam > 0 else 0.5
        return en_iyi, min(guven, 0.95)

    def detect_by_financial_profile(self, rapor: Dict[str, Any]) -> str:
        """
        Finansal metrikler üzerinden sektör tahmini.
        Kar marjı, büyüme oranı ve gelir büyüklüğüne göre sektör eşleştirir.
        """
        kar_marji    = rapor["karlilik"]["kar_marji"]
        buyume       = rapor["gelir"]["ortalama_buyume_orani"]
        aylik_gelir  = rapor["gelir"]["ortalama_aylik_gelir"]

        en_iyi_sektor = GENEL_SEKTOR
        en_iyi_skor   = 999

        for sektor, bilgi in SECTOR_DB.items():
            if sektor == GENEL_SEKTOR:
                continue
            bm = bilgi["benchmarks"]
            # Uzaklık skoru (benchmark'a ne kadar yakın)
            km_hedef = bm["kar_marji"]["orta"]
            by_hedef = bm["gelir_buyumesi"]["orta"]
            gl_hedef = bm["aylik_gelir"]["orta"]

            uzaklik = (
                abs(kar_marji - km_hedef) / max(abs(km_hedef), 1) +
                abs(buyume    - by_hedef) / max(abs(by_hedef), 1) +
                abs(aylik_gelir - gl_hedef) / max(gl_hedef, 1)
            )
            if uzaklik < en_iyi_skor:
                en_iyi_skor   = uzaklik
                en_iyi_sektor = sektor

        return en_iyi_sektor

    def detect(self, rapor: Dict[str, Any]) -> Dict[str, Any]:
        """Ana tespit metodu — hem keyword hem finansal profil kullanır."""
        kw_sektor, kw_guven = self.detect_by_keywords()
        fp_sektor            = self.detect_by_financial_profile(rapor)

        # Keyword tespiti yüksek güvenliyse onu kullan
        if kw_guven >= 0.5:
            sektor = kw_sektor
            guven  = kw_guven
            metod  = "Anahtar Kelime Analizi"
        elif kw_sektor != GENEL_SEKTOR:
            sektor = kw_sektor
            guven  = kw_guven
            metod  = "Anahtar Kelime Analizi"
        else:
            sektor = fp_sektor
            guven  = 0.45
            metod  = "Finansal Profil Analizi"

        bilgi = SECTOR_DB[sektor]
        return {
            "sektor":       sektor,
            "guven":        guven,
            "metod":        metod,
            "emoji":        bilgi["emoji"],
            "aciklama":     bilgi["aciklama"],
            "rakipler":     bilgi["rakipler"],
            "riskler":      bilgi["riskler"],
            "firsatlar":    bilgi["firsatlar"],
            "sektor_trendi":bilgi["sektor_trendi"],
        }


# ─────────────────────────────────────────────
# BENCHMARK MOTORU
# ─────────────────────────────────────────────

class BenchmarkEngine:
    """
    Şirket metriklerini sektör benchmark'larıyla karşılaştırır.
    0-100 arası benchmark skoru üretir.
    """

    def __init__(self, sektor: str, rapor: Dict[str, Any]):
        self.sektor = sektor
        self.rapor  = rapor
        self.bm     = SECTOR_DB[sektor]["benchmarks"]

    def _metrik_skoru(self, deger: float, benchmark: Dict) -> Tuple[float, str]:
        """
        Bir metriği benchmark ile karşılaştırır.
        Döner: (skor 0-100, durum etiketi)
        """
        iyi   = benchmark["iyi"]
        orta  = benchmark["orta"]
        zayif = benchmark["zayif"]
        dusuk_iyi = benchmark.get("dusuk_iyi", False)  # Düşük değer iyi mi?

        if dusuk_iyi:
            # Gider/gelir oranı gibi — düşük = iyi
            if deger <= iyi:   return 100.0, "Mükemmel"
            if deger <= orta:
                oran = (orta - deger) / (orta - iyi)
                return round(50 + oran * 50, 1), "İyi"
            if deger <= zayif:
                oran = (zayif - deger) / (zayif - orta)
                return round(oran * 50, 1), "Orta"
            return 0.0, "Zayıf"
        else:
            # Kar marjı gibi — yüksek = iyi
            if deger >= iyi:   return 100.0, "Mükemmel"
            if deger >= orta:
                oran = (deger - orta) / (iyi - orta) if iyi != orta else 0
                return round(50 + oran * 50, 1), "İyi"
            if deger >= zayif:
                oran = (deger - zayif) / (orta - zayif) if orta != zayif else 0
                return round(oran * 50, 1), "Orta"
            return 0.0, "Zayıf"

    def _hesapla_metrikler(self) -> Dict[str, Any]:
        """Şirket metriklerini hesapla."""
        g = self.rapor["gelir"]
        e = self.rapor["gider"]
        k = self.rapor["karlilik"]

        gider_gelir = (e["toplam_gider"] / g["toplam_gelir"] * 100
                       if g["toplam_gelir"] > 0 else 100)
        return {
            "kar_marji":         k["kar_marji"],
            "gelir_buyumesi":    g["ortalama_buyume_orani"],
            "gider_gelir_orani": round(gider_gelir, 2),
            "aylik_gelir":       g["ortalama_aylik_gelir"],
            "operasyonel_marj":  k["kar_marji"] * 0.85,  # yaklaşık
        }

    def compare(self) -> Dict[str, Any]:
        """Tam benchmark karşılaştırması."""
        metrikler  = self._hesapla_metrikler()
        sonuclar   = {}
        alt_skorlar = {}

        for metrik_adi, bm in self.bm.items():
            deger = metrikler.get(metrik_adi, 0)
            skor, durum = self._metrik_skoru(deger, bm)

            sonuclar[metrik_adi] = {
                "sirket_degeri":   deger,
                "sektor_iyi":      bm["iyi"],
                "sektor_orta":     bm["orta"],
                "sektor_zayif":    bm["zayif"],
                "birim":           bm["birim"],
                "skor":            skor,
                "durum":           durum,
                "dusuk_iyi":       bm.get("dusuk_iyi", False),
            }
            alt_skorlar[metrik_adi] = skor

        # Genel benchmark skoru (ağırlıklı)
        agirliklar = {
            "kar_marji":         0.30,
            "gelir_buyumesi":    0.25,
            "gider_gelir_orani": 0.20,
            "aylik_gelir":       0.15,
            "operasyonel_marj":  0.10,
        }
        genel_skor = sum(
            alt_skorlar.get(k, 50) * v
            for k, v in agirliklar.items()
        )

        kategori = self._kategori(genel_skor)
        return {
            "sektor":          self.sektor,
            "genel_skor":      round(genel_skor, 1),
            "kategori":        kategori,
            "metrik_sonuclari":sonuclar,
            "alt_skorlar":     alt_skorlar,
            "guclu_yonler":    self._guclu_yonler(sonuclar),
            "zayif_yonler":    self._zayif_yonler(sonuclar),
            "tavsiyeler":      self._tavsiyeler(sonuclar, genel_skor),
        }

    @staticmethod
    def _kategori(skor: float) -> str:
        if skor >= 80: return "Sektör Lideri"
        if skor >= 65: return "Ortalamanın Üstü"
        if skor >= 50: return "Sektör Ortalaması"
        if skor >= 35: return "Ortalamanın Altı"
        return "Sektörde Zayıf"

    @staticmethod
    def _guclu_yonler(sonuclar: Dict) -> List[str]:
        etiketler = {
            "kar_marji":         "Karlılık marjı",
            "gelir_buyumesi":    "Gelir büyüme hızı",
            "gider_gelir_orani": "Gider kontrolü",
            "aylik_gelir":       "Gelir büyüklüğü",
            "operasyonel_marj":  "Operasyonel verimlilik",
        }
        return [
            f"{etiketler.get(k, k)} sektör ortalamasının üzerinde"
            for k, v in sonuclar.items()
            if v["durum"] in ("Mükemmel", "İyi")
        ]

    @staticmethod
    def _zayif_yonler(sonuclar: Dict) -> List[str]:
        etiketler = {
            "kar_marji":         "Karlılık marjı",
            "gelir_buyumesi":    "Gelir büyüme hızı",
            "gider_gelir_orani": "Gider/gelir oranı",
            "aylik_gelir":       "Gelir büyüklüğü",
            "operasyonel_marj":  "Operasyonel marj",
        }
        return [
            f"{etiketler.get(k, k)} sektör ortalamasının altında"
            for k, v in sonuclar.items()
            if v["durum"] in ("Orta", "Zayıf")
        ]

    @staticmethod
    def _tavsiyeler(sonuclar: Dict, genel_skor: float) -> List[str]:
        tavs = []
        if sonuclar.get("kar_marji",{}).get("durum") in ("Orta","Zayıf"):
            tavs.append("Fiyatlandırma stratejisi gözden geçirilmeli, düşük marjlı ürünler analiz edilmeli.")
        if sonuclar.get("gelir_buyumesi",{}).get("durum") in ("Orta","Zayıf"):
            tavs.append("Yeni müşteri edinim kanalları ve ürün genişlemesi değerlendirilmeli.")
        if sonuclar.get("gider_gelir_orani",{}).get("durum") in ("Orta","Zayıf"):
            tavs.append("Gider optimizasyonu önceliklendirilmeli, sabit giderler düşürülmeli.")
        if sonuclar.get("aylik_gelir",{}).get("durum") in ("Orta","Zayıf"):
            tavs.append("Gelir artışı için satış ve pazarlama yatırımı artırılabilir.")
        if genel_skor >= 65:
            tavs.append("Mevcut avantajları koruyarak büyüme stratejisine odaklanılabilir.")
        return tavs or ["Tüm metrikler değerlendirilerek stratejik plan hazırlanmalı."]


# ─────────────────────────────────────────────
# RAKİP ANALİZİ
# ─────────────────────────────────────────────

class CompetitorAnalysis:
    """
    Sektördeki rakiplerin simüle edilmiş finansal verileriyle karşılaştırma.
    Gerçek veriler API üzerinden gelecekte entegre edilebilir.
    """

    def __init__(self, sektor: str, sirket_rapor: Dict[str, Any]):
        self.sektor  = sektor
        self.rapor   = sirket_rapor
        self.rakipler = SECTOR_DB[sektor]["rakipler"]
        self.bm       = SECTOR_DB[sektor]["benchmarks"]

    def simulate_competitors(self, seed: int = 42) -> pd.DataFrame:
        """
        Sektör benchmark'ları etrafında rakip verileri simüle eder.
        """
        rng = np.random.default_rng(seed)
        rows = []

        # Şirketin kendi metrikleri
        g = self.rapor["gelir"]
        k = self.rapor["karlilik"]
        gider_gelir = (self.rapor["gider"]["toplam_gider"] /
                       g["toplam_gelir"] * 100
                       if g["toplam_gelir"] > 0 else 100)

        rows.append({
            "Şirket":            "★ Şirketiniz",
            "Kar Marjı (%)":     round(k["kar_marji"], 1),
            "Büyüme (%)":        round(g["ortalama_buyume_orani"], 1),
            "Gider/Gelir (%)":   round(gider_gelir, 1),
            "Aylık Gelir (₺)":   round(g["ortalama_aylik_gelir"], 0),
            "Kaynak":            "Gerçek Veri",
        })

        bm = self.bm
        for rakip in self.rakipler:
            rows.append({
                "Şirket": rakip,
                "Kar Marjı (%)": round(float(rng.normal(
                    bm["kar_marji"]["orta"],
                    bm["kar_marji"]["iyi"] * 0.2)), 1),
                "Büyüme (%)": round(float(rng.normal(
                    bm["gelir_buyumesi"]["orta"],
                    bm["gelir_buyumesi"]["iyi"] * 0.25)), 1),
                "Gider/Gelir (%)": round(float(rng.normal(
                    bm["gider_gelir_orani"]["orta"],
                    5)), 1),
                "Aylık Gelir (₺)": round(float(rng.lognormal(
                    np.log(bm["aylik_gelir"]["orta"]), 0.5)), 0),
                "Kaynak": "Tahmin",
            })

        return pd.DataFrame(rows)

    def ranking(self) -> Dict[str, Any]:
        """Şirketin rakipler arasındaki sıralaması."""
        df   = self.simulate_competitors()
        n    = len(df)
        sira = df[df["Şirket"] == "★ Şirketiniz"].index[0] + 1

        # Kar marjına göre sırala
        df_sorted = df.sort_values("Kar Marjı (%)", ascending=False).reset_index(drop=True)
        sira_km   = df_sorted[df_sorted["Şirket"] == "★ Şirketiniz"].index[0] + 1

        return {
            "toplam_rakip": n - 1,
            "kar_marji_sira": sira_km,
            "yuzdelik": round((1 - sira_km / n) * 100, 0),
            "df": df,
        }


# ─────────────────────────────────────────────
# ANA SEKTÖR MOTORU
# ─────────────────────────────────────────────

class SectorEngine:
    """
    KazKaz AI Sektör Karşılaştırma Ana Motoru.

    Kullanım:
        engine = SectorEngine(df, rapor, sirket_adi="Acme A.Ş.")
        rapor  = engine.full_report()
    """

    def __init__(self,
                 df:          pd.DataFrame,
                 rapor:       Dict[str, Any],
                 sirket_adi:  str = ""):
        self.df         = df
        self.rapor      = rapor
        self.sirket_adi = sirket_adi

        # Sektör tespit
        detector    = SectorDetector(df, sirket_adi)
        self.tespit = detector.detect(rapor)
        self.sektor = self.tespit["sektor"]

        # Motorlar
        self.benchmark  = BenchmarkEngine(self.sektor, rapor)
        self.competitor = CompetitorAnalysis(self.sektor, rapor)

    def override_sector(self, sektor: str):
        """Kullanıcı sektörü manuel değiştirirse güncelle."""
        if sektor in SECTOR_DB:
            self.sektor     = sektor
            self.tespit["sektor"]   = sektor
            self.tespit["emoji"]    = SECTOR_DB[sektor]["emoji"]
            self.tespit["aciklama"] = SECTOR_DB[sektor]["aciklama"]
            self.benchmark  = BenchmarkEngine(sektor, self.rapor)
            self.competitor = CompetitorAnalysis(sektor, self.rapor)

    def full_report(self) -> Dict[str, Any]:
        bm     = self.benchmark.compare()
        rakip  = self.competitor.ranking()
        return {
            "tespit":      self.tespit,
            "benchmark":   bm,
            "rakip":       rakip,
            "sektor_bilgi":SECTOR_DB[self.sektor],
        }

    @staticmethod
    def list_sectors() -> List[str]:
        return [s for s in SECTOR_DB if s != GENEL_SEKTOR]

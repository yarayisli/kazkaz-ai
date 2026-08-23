"""
KazKaz AI - CFO AI Agent (v15)
================================
Yarı otonom CFO ajanı. Şirket verilerini analiz eder,
proaktif uyarılar üretir, yatırım/borç önerileri sunar
ve yönetici ile sohbet ederek karar sürecini destekler.

Araçlar (Tools):
  - FinancialHealthTool  : Sağlık skoru + uyarılar
  - CashFlowAlertTool    : Nakit akışı uyarıları
  - InvestmentAdvisorTool: Yatırım önerisi
  - DebtAdvisorTool      : Borç yönetimi önerisi
  - ReportGeneratorTool  : Otomatik rapor üretimi
  - CFOAgent             : Tüm araçları yöneten ana ajan

Bağımlılıklar: pandas, numpy, groq (veya google-generativeai)
"""

import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd


# ─────────────────────────────────────────────
# UYARI SEVİYELERİ
# ─────────────────────────────────────────────

class AlertLevel(str, Enum):
    KRITIK  = "🔴 KRİTİK"
    DIKKAT  = "🟡 DİKKAT"
    BILGI   = "🔵 BİLGİ"
    POZITIF = "🟢 POZİTİF"


@dataclass
class Alert:
    """Tek bir proaktif uyarı."""
    seviye:   AlertLevel
    baslik:   str
    mesaj:    str
    oneri:    str
    araç:     str = ""
    deger:    float = 0.0


@dataclass
class AgentMemory:
    """Agent'ın konuşma ve analiz geçmişi."""
    mesajlar:     List[Dict] = field(default_factory=list)
    son_analiz:   Optional[Dict] = None
    uyarilar:     List[Alert] = field(default_factory=list)
    karar_gecmisi:List[Dict] = field(default_factory=list)
    pending_actions: List["PendingAction"] = field(default_factory=list)
    oturum_baslangic: str = field(default_factory=lambda: datetime.now().isoformat())


# ─────────────────────────────────────────────
# ONAY KUYRUĞU (P1.5 foundation)
# ─────────────────────────────────────────────

class PendingActionStatus(str, Enum):
    BEKLIYOR   = "bekliyor"
    ONAYLANDI  = "onaylandi"
    REDDEDILDI = "reddedildi"
    UYGULANDI  = "uygulandi"


@dataclass
class PendingAction:
    """
    Bir agent'ın "yapmak istediği" ama henüz insan onayı beklediği eylem.
    Şu an tüm tool'lar salt-okunur — bu tip write/yan-etkili eylemler
    için hazırlanmış temel. Kullanım: cache invalidate, e-posta gönder,
    borç ödeme rezervi ayır, vs.
    """
    tur:         str                    # ör. "e-posta_gonder", "cache_invalidate"
    payload:     Dict[str, Any]
    aciklama:    str
    onerilen_zamanı: str = field(default_factory=lambda: datetime.now().isoformat())
    status:      PendingActionStatus = PendingActionStatus.BEKLIYOR
    onay_veren:  Optional[str] = None


# ─────────────────────────────────────────────
# CFO ARAÇLARI (TOOLS)
# ─────────────────────────────────────────────

class FinancialHealthTool:
    """Finansal sağlık analizi ve uyarı üretimi."""

    def run(self, rapor: Dict) -> Tuple[Dict, List[Alert]]:
        s = rapor.get("saglik_skoru", {})
        k = rapor.get("karlilik", {})
        g = rapor.get("gelir", {})
        e = rapor.get("gider", {})

        skor     = s.get("skor")
        kategori = s.get("kategori", "Hesaplanmadı")
        uyarilar = []

        # Kritik sağlık skoru
        if skor is not None and skor < 35:
            uyarilar.append(Alert(
                seviye=AlertLevel.KRITIK,
                baslik="Finansal Sağlık Kritik",
                mesaj=f"Sağlık skoru {skor}/100 — {kategori}. Şirket ciddi finansal risk altında.",
                oneri="Acil gider kısıtlaması ve gelir artırıcı önlemler alınmalı.",
                araç="FinancialHealthTool", deger=skor
            ))
        elif skor is not None and skor < 50:
            uyarilar.append(Alert(
                seviye=AlertLevel.DIKKAT,
                baslik="Finansal Sağlık Zayıf",
                mesaj=f"Sağlık skoru {skor}/100. İyileştirme gerekiyor.",
                oneri="Gider kontrolü ve nakit yönetimine odaklanın.",
                araç="FinancialHealthTool", deger=skor
            ))

        # Kar marjı uyarısı
        kar_marji = k.get("kar_marji", 0)
        if kar_marji < 0:
            uyarilar.append(Alert(
                seviye=AlertLevel.KRITIK,
                baslik="Negatif Kar Marjı",
                mesaj=f"Kar marjı %{kar_marji} — şirket zarar ediyor.",
                oneri="Fiyatlandırma ve maliyet yapısını acil gözden geçirin.",
                araç="FinancialHealthTool", deger=kar_marji
            ))
        elif kar_marji < 5:
            uyarilar.append(Alert(
                seviye=AlertLevel.DIKKAT,
                baslik="Düşük Kar Marjı",
                mesaj=f"Kar marjı %{kar_marji} — sektör ortalamasının altında olabilir.",
                oneri="Verimsiz gider kalemlerini tespit edin ve azaltın.",
                araç="FinancialHealthTool", deger=kar_marji
            ))

        # Büyüme uyarısı
        buyume = g.get("ortalama_buyume_orani")
        if buyume is not None and buyume > 20:
            uyarilar.append(Alert(
                seviye=AlertLevel.POZITIF,
                baslik="Güçlü Büyüme",
                mesaj=f"Aylık ortalama %{buyume} gelir büyümesi — mükemmel performans.",
                oneri="Büyümeyi sürdürmek için operasyonel kapasiteyi artırın.",
                araç="FinancialHealthTool", deger=buyume
            ))
        elif buyume is not None and buyume < 0:
            uyarilar.append(Alert(
                seviye=AlertLevel.DIKKAT,
                baslik="Negatif Büyüme",
                mesaj=f"Gelir %{abs(buyume)} azalıyor.",
                oneri="Müşteri kaybı ve pazar dinamiklerini analiz edin.",
                araç="FinancialHealthTool", deger=buyume
            ))

        # Gider oranı
        gider_oran = e.get("sabit_gider_orani")
        if gider_oran is not None and gider_oran > 70:
            uyarilar.append(Alert(
                seviye=AlertLevel.DIKKAT,
                baslik="Yüksek Sabit Gider Oranı",
                mesaj=f"Sabit giderler toplam giderin %{gider_oran}'ini oluşturuyor.",
                oneri="Sabit giderleri değişkene dönüştürecek modeller değerlendirin.",
                araç="FinancialHealthTool", deger=gider_oran
            ))

        ozet = {
            "skor":        skor,
            "kategori":    kategori,
            "kar_marji":   kar_marji,
            "buyume":      buyume,
            "gider_oran":  gider_oran,
            "uyari_sayisi":len(uyarilar),
        }
        return ozet, uyarilar


class CashFlowAlertTool:
    """Nakit akışı uyarı motoru."""

    def run(self, rapor: Dict) -> Tuple[Dict, List[Alert]]:
        uyarilar = []
        ncf = rapor.get("operasyonel_ncf")
        ncf_marji = rapor.get("ncf_marji")
        runway = rapor.get("runway_ay")
        burn   = rapor.get("nakit_yakilip_yakilmiyor", False)
        verim  = rapor.get("verimlilik_orani")
        cari   = rapor.get("cari_oran")
        ccc    = rapor.get("nakit_donusum_gun")

        # Runway uyarısı
        if runway is not None:
            if runway < 3:
                uyarilar.append(Alert(
                    seviye=AlertLevel.KRITIK,
                    baslik="Kritik Runway",
                    mesaj=f"Mevcut gidişle nakit {runway:.0f} ayda tükeniyor.",
                    oneri="13 haftalık nakit planını güncelleyip finansman ve gider senaryolarını CFO onayına sunun.",
                    araç="CashFlowAlertTool", deger=runway
                ))
            elif runway < 6:
                uyarilar.append(Alert(
                    seviye=AlertLevel.DIKKAT,
                    baslik="Kısa Runway",
                    mesaj=f"Nakit {runway:.0f} ay içinde tükenebilir.",
                    oneri="Tahsilat, ödeme vadesi ve finansman alternatiflerini senaryo bazında inceleyin.",
                    araç="CashFlowAlertTool", deger=runway
                ))

        # Verimlilik uyarısı
        if verim is not None and verim < 1:
            uyarilar.append(Alert(
                seviye=AlertLevel.KRITIK,
                baslik="Nakit Yakılıyor",
                mesaj=f"Nakit verimliliği {verim:.2f} — giderler geliri aşıyor.",
                oneri="Negatif nakit etkisi yaratan gider ve tahsilat kalemlerini doğrulayın.",
                araç="CashFlowAlertTool", deger=verim
            ))

        # CCC uyarısı
        if ccc is not None and ccc > 60:
            uyarilar.append(Alert(
                seviye=AlertLevel.DIKKAT,
                baslik="Uzun Nakit Dönüşüm Döngüsü",
                mesaj=f"Nakit dönüşüm döngüsü {ccc} gün — likidite riski var.",
                oneri="Alacak, stok ve ödeme günlerini ayrı ayrı doğrulayıp etki senaryosu oluşturun.",
                araç="CashFlowAlertTool", deger=ccc
            ))

        # Cari oran uyarısı
        if cari is not None and cari < 1:
            uyarilar.append(Alert(
                seviye=AlertLevel.KRITIK,
                baslik="Cari Oran Kritik",
                mesaj=f"Cari oran {cari} — kısa vadeli borçlar karşılanamıyor.",
                oneri="Kısa vadeli ödeme planını ve kullanılabilir likidite kaynaklarını CFO ile inceleyin.",
                araç="CashFlowAlertTool", deger=cari
            ))
        elif cari is not None and cari < 1.5:
            uyarilar.append(Alert(
                seviye=AlertLevel.DIKKAT,
                baslik="Düşük Cari Oran",
                mesaj=f"Cari oran {cari} — likidite sıkışıklığı riski var.",
                oneri="Dönen varlık kalitesi ile kısa vadeli ödeme takvimini birlikte doğrulayın.",
                araç="CashFlowAlertTool", deger=cari
            ))

        if ncf is not None and ncf > 0 and not burn:
            uyarilar.append(Alert(
                seviye=AlertLevel.POZITIF,
                baslik="Pozitif Nakit Akışı",
                mesaj=f"Operasyonel nakit akışı pozitif — şirket nakit üretiyor.",
                oneri="Minimum nakit eşiği ve onaylı fon kullanım politikası sonrasında kullanım senaryosu hazırlayın.",
                araç="CashFlowAlertTool", deger=ncf
            ))

        return {"ncf": ncf, "ncf_marji": ncf_marji, "runway": runway}, uyarilar


class InvestmentAdvisorTool:
    """Yatırım için doğrulanabilir iş vakası hazırlık motoru.

    Kaynaksız ROI, gelir yüzdesi veya yatırım limiti üretmez. Nihai yatırım
    kararı her zaman insan onayı gerektirir.
    """

    def run(self, fin_rapor: Dict, nakit_pozisyon: float = 0) -> Dict:
        g = fin_rapor.get("gelir", {})
        k = fin_rapor.get("karlilik", {})
        s = fin_rapor.get("saglik_skoru", {})

        skor       = s.get("skor", 0)
        kar_marji  = k.get("kar_marji", 0)
        buyume = g.get("ortalama_buyume_orani")
        donem_geliri = g.get("toplam_gelir", 0)

        risk_profili = "Veri onayı gerekli"
        if skor is not None and buyume is not None:
            risk_profili = "İncelemeye uygun" if skor >= 50 and kar_marji > 0 else "Likidite öncelikli"

        oneriler = [
            {
                "tip": "Yatırım iş vakası",
                "oran": "Politika onayı gerekli",
                "tutar": 0,
                "sure": "Proje bazında girilmeli",
                "beklenen_roi": "Gelir/maliyet tahmini gerekli",
                "oncelik": "Yüksek",
                "dayanak": f"Dönem kâr marjı %{kar_marji:.1f}; nakit ₺{nakit_pozisyon:,.0f}",
                "insan_onayi": True,
            },
            {
                "tip": "Likidite etkisi kontrolü",
                "oran": "Belirlenmedi",
                "tutar": 0,
                "sure": "13 haftalık nakit planıyla",
                "beklenen_roi": "Hesaplanmadı",
                "oncelik": "Yüksek",
                "dayanak": "Yatırım sonrası minimum nakit eşiği henüz tanımlı değil.",
                "insan_onayi": True,
            },
        ]

        return {
            "risk_profili":  risk_profili,
            "yillik_gelir":  0,
            "donem_geliri":  donem_geliri,
            "nakit":         nakit_pozisyon,
            "oneriler":      oneriler,
            "max_yatirim":   0,
            "hesaplanabilir": False,
            "eksik_veriler": ["minimum nakit eşiği", "proje nakit akışları", "iskonto oranı", "yönetim yatırım limiti"],
            "insan_onayi_gerekli": True,
        }


class DebtAdvisorTool:
    """Borç yönetimi öneri motoru."""

    def run(self, fin_rapor: Dict, mevcut_borc: float = 0,
            faiz_orani: Optional[float] = None,
            yillik_borc_servisi: Optional[float] = None,
            operasyonel_nakit: Optional[float] = None) -> Dict:
        g = fin_rapor.get("gelir", {})
        k = fin_rapor.get("karlilik", {})

        donem_geliri = g.get("toplam_gelir", 0)
        borc_gelir_orani = mevcut_borc / donem_geliri if donem_geliri > 0 else None
        dscr = (
            operasyonel_nakit / yillik_borc_servisi
            if operasyonel_nakit is not None and yillik_borc_servisi not in (None, 0)
            else None
        )

        oneriler = []
        if mevcut_borc > 0:
            oneriler.append({
                "tip": "Borç koşulları incelemesi",
                "aciklama": "Anapara, faiz, vade ve teminat koşullarını teklif bazında karşılaştırın.",
                "eylem": "Refinansman kararı öncesi toplam geri ödeme ve nakit etkisini CFO onayına sunun.",
                "tasarruf": None,
                "dayanak": f"Toplam borç ₺{mevcut_borc:,.0f}",
                "insan_onayi": True,
            })
        if dscr is None:
            oneriler.append({
                "tip": "DSCR veri tamamlama",
                "aciklama": "Borç servis karşılama oranı net kârdan hesaplanamaz.",
                "eylem": "Operasyonel nakit akışı ile dönem anapara ve faiz ödemelerini girin.",
                "tasarruf": None,
                "dayanak": "Operasyonel nakit veya borç servisi eksik.",
                "insan_onayi": True,
            })

        return {
            "mevcut_borc":           mevcut_borc,
            "faiz_orani_pct":        round(faiz_orani * 100, 1) if faiz_orani is not None else None,
            "max_yillik_borc_servis":None,
            "oneriler":              oneriler,
            "borc_gelir_orani":      round(borc_gelir_orani, 2) if borc_gelir_orani is not None else None,
            "dscr":                   round(dscr, 2) if dscr is not None else None,
            "insan_onayi_gerekli":   True,
        }


class ReportGeneratorTool:
    """Otomatik periyodik rapor üretici."""

    RAPOR_SABLONU = """
# 📊 KazKaz AI — {periyot} Finansal Raporu
**Tarih:** {tarih}
**Şirket:** {sirket}

---

## 🏥 Finansal Sağlık
- **Skor:** {skor}/100 → {kategori}
- **Kar Marjı:** %{kar_marji}
- **Gelir Büyümesi:** %{buyume}

## ⚠️ Önemli Uyarılar ({uyari_sayisi} adet)
{uyarilar}

## 💡 Bu Dönem Öncelikli Aksiyonlar
{aksiyonlar}

## 🧭 Veri ve Onay Durumu
- Otomatik aksiyon yoktur. Ödeme, kredi ve yatırım kararları insan onayı gerektirir.
- Gelecek dönem tahmini yalnızca doğrulanmış zaman serisiyle ayrıca üretilir.

---
*Bu rapor KazKaz AI CFO Agent tarafından otomatik oluşturulmuştur.*
"""

    def run(self, fin_rapor: Dict, uyarilar: List[Alert],
            sirket: str = "Şirket",
            periyot: str = "Aylık") -> str:
        s = fin_rapor.get("saglik_skoru", {})
        k = fin_rapor.get("karlilik", {})
        g = fin_rapor.get("gelir", {})

        # Uyarıları formatla
        uyari_metni = "\n".join([
            f"- {u.seviye} **{u.baslik}**: {u.mesaj}"
            for u in uyarilar[:5]
        ]) if uyarilar else "- ✅ Önemli uyarı yok"

        # Aksiyonlar
        aksiyonlar = "\n".join([
            f"{i+1}. {u.oneri}"
            for i, u in enumerate(
                [u for u in uyarilar if u.seviye in
                 [AlertLevel.KRITIK, AlertLevel.DIKKAT]][:3]
            )
        ]) if uyarilar else "1. Mevcut performansı koruyun\n2. Büyüme fırsatlarını değerlendirin"

        # Trend yorumu
        trend = k.get("kar_trendi", "Stabil")
        if "Artış" in trend:
            trend_yorum = "Karlılık artış eğiliminde; tahmin değildir"
        elif "Düşüş" in trend:
            trend_yorum = "Karlılık düşüş eğiliminde; neden analizi gerekir"
        else:
            trend_yorum = "Tahmin üretmek için yeterli doğrulanmış zaman serisi yok"

        return self.RAPOR_SABLONU.format(
            periyot     = periyot,
            tarih       = datetime.now().strftime("%d.%m.%Y %H:%M"),
            sirket      = sirket,
            skor        = s.get("skor", 0),
            kategori    = s.get("kategori", "-"),
            kar_marji   = k.get("kar_marji", 0),
            buyume      = g.get("ortalama_buyume_orani", 0),
            uyari_sayisi= len(uyarilar),
            uyarilar    = uyari_metni,
            aksiyonlar  = aksiyonlar,
            trend_yorum = trend_yorum,
        )


# ─────────────────────────────────────────────
# ANA CFO AGENT
# ─────────────────────────────────────────────

class CFOAgent:
    """
    KazKaz AI CFO AI Agent — Ana Motor.

    Tüm araçları koordine eder, AI ile yorumlar,
    proaktif uyarılar ve öneriler üretir.

    Kullanım:
        agent = CFOAgent(ai_engine, fin_rapor, sirket_adi)
        durum = agent.analyze()
        cevap = agent.chat("Nakit durumum nasıl?")
    """

    def __init__(self,
                 ai_engine,              # GeminiEngine instance
                 fin_rapor: Dict,
                 sirket_adi: str = "Şirket",
                 cf_rapor: Optional[Dict] = None,
                 debt_rapor: Optional[Dict] = None):
        self.ai        = ai_engine
        self.fin_rapor = fin_rapor
        self.sirket    = sirket_adi
        self.cf_rapor  = cf_rapor or {}
        self.debt_rapor= debt_rapor or {}
        self.memory    = AgentMemory()

        # Araçları başlat
        self.health_tool  = FinancialHealthTool()
        self.cf_tool      = CashFlowAlertTool()
        self.inv_tool     = InvestmentAdvisorTool()
        self.debt_tool    = DebtAdvisorTool()
        self.report_tool  = ReportGeneratorTool()

    # ─────────────────────────────────────────
    # ANA ANALİZ — tüm araçları çalıştır
    # ─────────────────────────────────────────

    def analyze(self) -> Dict[str, Any]:
        """Tüm araçları çalıştırır, analiz sonucunu döner."""
        tum_uyarilar = []

        # 1. Finansal sağlık
        health_ozet, health_alerts = self.health_tool.run(self.fin_rapor)
        tum_uyarilar.extend(health_alerts)

        # 2. Nakit akışı (varsa)
        cf_ozet = {}
        if self.cf_rapor:
            nakit_ozet = self.cf_rapor.get("nakit_ozet", {})
            likidite   = self.cf_rapor.get("likidite", {})
            burn       = self.cf_rapor.get("burn_rate", {})
            cf_data    = {**nakit_ozet, **likidite, **burn}
            cf_ozet, cf_alerts = self.cf_tool.run(cf_data)
            tum_uyarilar.extend(cf_alerts)

        # 3. Yatırım önerileri
        nakit = self.cf_rapor.get("nakit_ozet", {}).get(
            "son_nakit_pozisyon", 0) if self.cf_rapor else 0
        inv_oneri = self.inv_tool.run(self.fin_rapor, nakit)

        # 4. Borç önerileri
        toplam_borc = 0
        faiz_orani  = None
        if self.debt_rapor:
            toplam_borc = self.debt_rapor.get(
                "portfolio_ozet", {}).get("toplam_borc", 0)
            agirlikli_faiz = self.debt_rapor.get(
                "portfolio_ozet", {}).get("agirlikli_faiz")
            faiz_orani = agirlikli_faiz / 100 if agirlikli_faiz is not None else None
        try:
            debt_oneri = self.debt_tool.run(self.fin_rapor, toplam_borc, faiz_orani)
        except Exception:
            debt_oneri = {
                "mevcut_borc": 0, "faiz_orani_pct": 0,
                "max_yillik_borc_servis": None, "oneriler": [],
                "borc_gelir_orani": None, "dscr": None,
            }

        # 5. Uyarıları önceliklendir
        tum_uyarilar.sort(key=lambda x: (
            0 if x.seviye == AlertLevel.KRITIK else
            1 if x.seviye == AlertLevel.DIKKAT else
            2 if x.seviye == AlertLevel.BILGI else 3
        ))

        # Memory'ye kaydet
        self.memory.son_analiz = {
            "tarih":      datetime.now().isoformat(),
            "health":     health_ozet,
            "cf":         cf_ozet,
            "inv":        inv_oneri,
            "debt":       debt_oneri,
            "uyarilar":   tum_uyarilar,
        }
        self.memory.uyarilar = tum_uyarilar

        return self.memory.son_analiz

    # ─────────────────────────────────────────
    # RAPOR ÜRET
    # ─────────────────────────────────────────

    def generate_report(self, periyot: str = "Aylık") -> str:
        if not self.memory.son_analiz:
            self.analyze()
        return self.report_tool.run(
            self.fin_rapor,
            self.memory.uyarilar,
            sirket=self.sirket,
            periyot=periyot,
        )

    # ─────────────────────────────────────────
    # CFO SOHBET
    # ─────────────────────────────────────────

    def chat(self, kullanici_mesaji: str) -> str:
        """
        Kullanıcı ile CFO bağlamında sohbet.
        Tüm analiz verilerini context olarak kullanır.
        """
        if not self.memory.son_analiz:
            self.analyze()

        # Context oluştur
        analiz = self.memory.son_analiz
        context = f"""
Sen {self.sirket} şirketinin CFO'su gibi davranıyorsun.
Şu an elimdeki veriler:

Finansal Sağlık Skoru: {analiz['health']['skor']}/100 — {analiz['health']['kategori']}
Kar Marjı: %{analiz['health']['kar_marji']}
Büyüme: %{analiz['health']['buyume']}
Aktif Uyarı Sayısı: {len(analiz['uyarilar'])}

Kritik Uyarılar:
{chr(10).join([f"- {u.baslik}: {u.mesaj}" for u in analiz['uyarilar']
               if u.seviye == AlertLevel.KRITIK][:3]) or "Yok"}

Yatırım Profili: {analiz['inv']['risk_profili']}
"""
        # Memory'ye ekle
        self.memory.mesajlar.append({
            "role": "user", "content": kullanici_mesaji})

        # AI'ya sor
        prompt = f"{context}\n\nYönetici soruyor: {kullanici_mesaji}\n\nCFO olarak Türkçe, net ve uygulanabilir cevap ver."

        try:
            cevap = self.ai._call(prompt)
        except Exception as e:
            cevap = f"⚠️ Yanıt üretilemedi: {e}"

        self.memory.mesajlar.append({
            "role": "assistant", "content": cevap})
        return cevap

    def reset_chat(self):
        self.memory.mesajlar = []

    # ─────────────────────────────────────────
    # FUNCTION-CALLING (P1.5)
    # ─────────────────────────────────────────

    def tool_specs(self) -> List[Dict[str, Any]]:
        """
        Groq / OpenAI function-calling şemasında araç tanımları.
        LLM bu listeyi görür ve hangi araçları çağıracağına kendisi karar verir.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_financial_health",
                    "description": (
                        "Şirketin finansal sağlık skorunu (0-100), kategorisini "
                        "ve tüm sağlık uyarılarını döner. Kullanıcı sağlık, "
                        "skor, kar marjı veya genel durum sorduğunda çağır."
                    ),
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_cash_flow_alerts",
                    "description": (
                        "Nakit akışı uyarılarını, runway'i, verimlilik oranını "
                        "ve cari oranı döner. Kullanıcı nakit, likidite veya "
                        "borç ödeme kapasitesi sorduğunda çağır."
                    ),
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_investment_advice",
                    "description": (
                        "Şirketin risk profiline (Muhafazakâr/Dengeli/Büyüme) "
                        "göre 2-3 yatırım önerisi döner. Kullanıcı yatırım, "
                        "genişleme, teknoloji yatırımı veya nakdi nereye "
                        "koyayım sorduğunda çağır."
                    ),
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_debt_advice",
                    "description": (
                        "Mevcut borç yükü ve faiz oranına göre refinansman, "
                        "borç azaltma veya stratejik borçlanma önerisi. "
                        "Borç, kredi, faiz konularında çağır."
                    ),
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "generate_report",
                    "description": (
                        "Tam bir finansal dönem raporu üretir (Markdown). "
                        "Kullanıcı 'rapor', 'özet çıkar', 'dönemsel değerlendirme' "
                        "gibi talepler yaptığında çağır."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "periyot": {
                                "type": "string",
                                "enum": ["Aylık", "Çeyreklik", "Yıllık"],
                                "description": "Rapor dönemi",
                            }
                        },
                        "required": [],
                    },
                },
            },
        ]

    def dispatch_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """
        Verilen adı taşıyan aracı çalıştırır ve LLM'e döndürmek üzere JSON
        string sonuç verir. Bilinmeyen ad için nazik hata mesajı döner
        (LLM'in retry veya alternatif tool denemesi için).
        """
        try:
            if name == "get_financial_health":
                ozet, alerts = self.health_tool.run(self.fin_rapor)
                return json.dumps({
                    "ozet": ozet,
                    "uyarilar": [
                        {"seviye": a.seviye, "baslik": a.baslik,
                         "mesaj": a.mesaj, "oneri": a.oneri}
                        for a in alerts
                    ],
                }, ensure_ascii=False, default=str)

            if name == "get_cash_flow_alerts":
                if not self.cf_rapor:
                    return json.dumps({
                        "hata": "Nakit akışı verisi yok. Kullanıcı önce "
                                "nakit akışı sekmesinden veri girmeli."
                    }, ensure_ascii=False)
                cf_data = {
                    **self.cf_rapor.get("nakit_ozet", {}),
                    **self.cf_rapor.get("likidite", {}),
                    **self.cf_rapor.get("burn_rate", {}),
                }
                ozet, alerts = self.cf_tool.run(cf_data)
                return json.dumps({
                    "ozet": ozet,
                    "uyarilar": [
                        {"seviye": a.seviye, "baslik": a.baslik,
                         "mesaj": a.mesaj, "oneri": a.oneri}
                        for a in alerts
                    ],
                }, ensure_ascii=False, default=str)

            if name == "get_investment_advice":
                nakit = self.cf_rapor.get("nakit_ozet", {}).get(
                    "son_nakit_pozisyon", 0) if self.cf_rapor else 0
                return json.dumps(
                    self.inv_tool.run(self.fin_rapor, nakit),
                    ensure_ascii=False, default=str,
                )

            if name == "get_debt_advice":
                toplam_borc = 0
                faiz_orani  = 0.40
                if self.debt_rapor:
                    ozet = self.debt_rapor.get("portfolio_ozet", {})
                    toplam_borc = ozet.get("toplam_borc", 0)
                    faiz_orani  = ozet.get("agirlikli_faiz", 40) / 100
                return json.dumps(
                    self.debt_tool.run(self.fin_rapor, toplam_borc, faiz_orani),
                    ensure_ascii=False, default=str,
                )

            if name == "generate_report":
                periyot = arguments.get("periyot", "Aylık")
                if not self.memory.son_analiz:
                    self.analyze()
                return self.report_tool.run(
                    self.fin_rapor, self.memory.uyarilar,
                    sirket=self.sirket, periyot=periyot,
                )

            return json.dumps({
                "hata": f"Bilinmeyen araç: {name}. Kullanılabilir araçlar için "
                        "tool_specs()'e bak.",
            }, ensure_ascii=False)

        except Exception as e:
            return json.dumps({
                "hata": f"{name} çalıştırılırken hata: {e}",
            }, ensure_ascii=False)

    def chat_with_tools(
        self,
        kullanici_mesaji: str,
        max_turns: int = 5,
    ) -> Dict[str, Any]:
        """
        Function-calling agent döngüsü.

        1. LLM'e mesaj + tool specs verilir
        2. LLM tool_calls döndürürse, her biri dispatch edilir, sonuçlar
           mesaj listesine 'tool' rolüyle eklenir, LLM tekrar çağrılır
        3. LLM final text döndürürse döngü biter
        4. max_turns aşılırsa güvenli kesim

        Döner: {
            "cevap":        final metin,
            "tool_calls":   [{name, arguments, result_preview}...],
            "turns":        kaç tur döndü,
            "kesildi":      max_turns aşıldıysa True,
        }

        Kullandığı LLM istemcisi self.ai._client (GeminiEngine wrapper); Groq
        veya OpenAI olmalı — Gemini function-calling şeması farklı olduğu için
        şu sürümde desteklenmez, o durumda düz chat'e düşer.
        """
        provider = getattr(self.ai, "provider", "groq")
        if provider not in ("groq", "openai"):
            # Gemini function-calling şeması farklı; şu sürümde düz chat'e düş
            return {
                "cevap":      self.chat(kullanici_mesaji),
                "tool_calls": [],
                "turns":      0,
                "kesildi":    False,
                "fallback":   f"{provider} için function-calling desteklenmiyor, düz chat kullanıldı.",
            }

        if not self.memory.son_analiz:
            self.analyze()

        messages = [
            {"role": "system", "content": (
                f"Sen {self.sirket} şirketinin CFO asistanısın. "
                "Kullanıcı sorularını yanıtlamadan önce, sana sağlanan araçlarla "
                "gerekli veriyi topla, sonra Türkçe, net, uygulanabilir bir "
                "cevap ver. Aynı aracı gereksiz yere iki kez çağırma. "
                "Sağlığa yanıt vermek için önce get_financial_health, nakit için "
                "get_cash_flow_alerts, yatırım için get_investment_advice, borç "
                "için get_debt_advice, rapor için generate_report kullan."
            )},
            {"role": "user", "content": kullanici_mesaji},
        ]

        tool_calls_log: List[Dict[str, Any]] = []
        tools = self.tool_specs()
        client = self.ai._client
        model  = self.ai._model

        for turn in range(1, max_turns + 1):
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    max_tokens=1500,
                )
            except Exception as e:
                return {
                    "cevap": f"⚠️ Ajan çağrısı başarısız: {e}",
                    "tool_calls": tool_calls_log,
                    "turns": turn,
                    "kesildi": False,
                    "hata": str(e),
                }

            choice = resp.choices[0].message
            calls = getattr(choice, "tool_calls", None) or []

            if not calls:
                # LLM cevap üretti → dön
                cevap = choice.content or ""
                self.memory.mesajlar.append(
                    {"role": "user", "content": kullanici_mesaji})
                self.memory.mesajlar.append(
                    {"role": "assistant", "content": cevap})
                return {
                    "cevap":      cevap,
                    "tool_calls": tool_calls_log,
                    "turns":      turn,
                    "kesildi":    False,
                }

            # Tool çağrılarını mesaja ekle
            messages.append({
                "role": "assistant",
                "content": choice.content,
                "tool_calls": [
                    {"id": c.id, "type": "function",
                     "function": {"name": c.function.name,
                                  "arguments": c.function.arguments}}
                    for c in calls
                ],
            })

            for c in calls:
                name = c.function.name
                try:
                    args = json.loads(c.function.arguments or "{}")
                except Exception:
                    args = {}
                result = self.dispatch_tool(name, args)
                tool_calls_log.append({
                    "name": name,
                    "arguments": args,
                    "result_preview": (result[:200] + "…") if len(result) > 200 else result,
                })
                messages.append({
                    "role":         "tool",
                    "tool_call_id": c.id,
                    "content":      result,
                })

        return {
            "cevap":      "⚠️ Ajan yanıt döngüsü tamamlanamadı (max turns).",
            "tool_calls": tool_calls_log,
            "turns":      max_turns,
            "kesildi":    True,
        }

    # ─────────────────────────────────────────
    # ONAY KUYRUĞU YÖNETİMİ (P1.5 foundation)
    # ─────────────────────────────────────────

    def enqueue_pending_action(
        self, tur: str, payload: Dict[str, Any], aciklama: str,
    ) -> PendingAction:
        """
        Bir write/yan-etkili eylemi onay kuyruğuna al.
        LLM veya tool bir aksiyon önerdiğinde bu metod çağrılır;
        insan onayı gelene kadar uygulanmaz.
        """
        pa = PendingAction(tur=tur, payload=payload, aciklama=aciklama)
        self.memory.pending_actions.append(pa)
        return pa

    def approve_pending(self, index: int, onay_veren: str) -> PendingAction:
        pa = self.memory.pending_actions[index]
        pa.status = PendingActionStatus.ONAYLANDI
        pa.onay_veren = onay_veren
        return pa

    def reject_pending(self, index: int, onay_veren: str) -> PendingAction:
        pa = self.memory.pending_actions[index]
        pa.status = PendingActionStatus.REDDEDILDI
        pa.onay_veren = onay_veren
        return pa

    def pending_summary(self) -> Dict[str, int]:
        """Kaç aksiyon hangi statüde?"""
        s = {v.value: 0 for v in PendingActionStatus}
        for pa in self.memory.pending_actions:
            s[pa.status.value] += 1
        return s

    # ─────────────────────────────────────────
    # KOMPAKt DURUM ÖZETİ
    # ─────────────────────────────────────────

    def status_summary(self) -> Dict[str, Any]:
        """Hızlı durum özeti — dashboard için."""
        if not self.memory.son_analiz:
            self.analyze()
        a = self.memory.son_analiz
        return {
            "skor":           a["health"]["skor"],
            "kategori":       a["health"]["kategori"],
            "kritik_uyari":   sum(1 for u in a["uyarilar"]
                                  if u.seviye == AlertLevel.KRITIK),
            "dikkat_uyari":   sum(1 for u in a["uyarilar"]
                                  if u.seviye == AlertLevel.DIKKAT),
            "pozitif_uyari":  sum(1 for u in a["uyarilar"]
                                  if u.seviye == AlertLevel.POZITIF),
            "risk_profili":   a["inv"]["risk_profili"],
            "son_guncelleme": a["tarih"],
        }

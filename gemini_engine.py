"""
KazKaz AI - Gemini AI Entegrasyon Motoru
=========================================
Görevler:
  - Finansal yorum üretmek
  - Stratejik öneriler
  - Yönetici raporu
  - Sohbet asistanı (şirket verisi üzerinden)

Kurulum:
  pip install google-generativeai
"""

import google.generativeai as genai
from typing import Optional, Dict, Any, List
import json


# ─────────────────────────────────────────────
# AYARLAR
# ─────────────────────────────────────────────

GEMINI_MODEL = "gemini-1.5-flash"

SYSTEM_PROMPT = """
Sen KazKaz AI'nın finansal analiz asistanısın. Adın "KazKaz".
Görevin şirket finansal verilerini analiz ederek yöneticilere:
- Net, anlaşılır ve profesyonel yorumlar sunmak
- Uygulanabilir stratejik öneriler vermek
- Riskleri ve fırsatları öne çıkarmak

Cevaplarında:
✓ Türkçe yaz
✓ Yönetici dostu, kısa ve öz ol
✓ Somut sayılar ve oranlar kullan
✓ Her yorumun sonunda 1-2 öneri ekle
✗ Teknik jargondan kaçın
✗ Belirsiz veya genel ifadeler kullanma
"""


# ─────────────────────────────────────────────
# GEMİNİ MOTORU
# ─────────────────────────────────────────────

class GeminiEngine:
    """
    KazKaz AI için Gemini tabanlı yapay zeka motoru.

    Kullanım:
        ai = GeminiEngine(api_key="YOUR_KEY")
        yorum = ai.analyze(rapor)
    """

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=SYSTEM_PROMPT,
        )
        self.chat_history: List[Dict[str, str]] = []

    # ─────────────────────────────────────────
    # 1. FİNANSAL ANALİZ YORUMU
    # ─────────────────────────────────────────

    def analyze(self, rapor: Dict[str, Any]) -> str:
        """
        full_report() çıktısını alır, kapsamlı yorum üretir.
        """
        prompt = self._build_analysis_prompt(rapor)
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"⚠️ AI analizi şu anda kullanılamıyor: {str(e)}"

    def _build_analysis_prompt(self, rapor: Dict[str, Any]) -> str:
        gelir   = rapor.get("gelir", {})
        gider   = rapor.get("gider", {})
        kar     = rapor.get("karlilik", {})
        saglik  = rapor.get("saglik_skoru", {})

        return f"""
Aşağıdaki finansal verileri analiz et ve kapsamlı bir yönetici raporu yaz.

## Finansal Özet

**Gelir:**
- Toplam Gelir: {gelir.get('toplam_gelir', 0):,.0f} ₺
- Ortalama Aylık Gelir: {gelir.get('ortalama_aylik_gelir', 0):,.0f} ₺
- Ortalama Büyüme Oranı: %{gelir.get('ortalama_buyume_orani', 0)}
- En Karlı Kategori: {gelir.get('en_karli_kategori', {}).get('kategori', '-')} ({gelir.get('en_karli_kategori', {}).get('gelir', 0):,.0f} ₺)

**Gider:**
- Toplam Gider: {gider.get('toplam_gider', 0):,.0f} ₺
- En Yüksek Gider Kalemi: {gider.get('en_yuksek_gider_kalemi', {}).get('kategori', '-')}
- Sabit Gider Oranı: %{gider.get('sabit_gider_orani', 0)}

**Karlılık:**
- Net Kar: {kar.get('toplam_net_kar', 0):,.0f} ₺
- Kar Marjı: %{kar.get('kar_marji', 0)}
- Trend: {kar.get('kar_trendi', '-')}

**Finansal Sağlık Skoru:** {saglik.get('skor', 0)} / 100 → {saglik.get('kategori', '-')}

---
Lütfen şunları içeren bir rapor yaz:
1. 📊 Genel Değerlendirme (2-3 cümle)
2. ✅ Güçlü Yönler
3. ⚠️ Riskler ve Dikkat Edilmesi Gerekenler
4. 🎯 Stratejik Öneriler (en az 3 madde)
"""

    # ─────────────────────────────────────────
    # 2. STRATEJİK ÖNERİLER
    # ─────────────────────────────────────────

    def strategic_recommendations(self, rapor: Dict[str, Any]) -> str:
        """Sadece stratejik öneriler üretir."""
        kar_marji = rapor.get("karlilik", {}).get("kar_marji", 0)
        saglik    = rapor.get("saglik_skoru", {}).get("skor", 50)
        trend     = rapor.get("karlilik", {}).get("kar_trendi", "Stabil")

        prompt = f"""
Şirketin finansal durumu:
- Kar Marjı: %{kar_marji}
- Sağlık Skoru: {saglik}/100
- Karlılık Trendi: {trend}

Bu verilere göre yöneticiye 5 somut ve uygulanabilir stratejik öneri sun.
Her öneri için: ne yapılmalı, neden yapılmalı, beklenen etki.
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"⚠️ Öneri üretilemedi: {str(e)}"

    # ─────────────────────────────────────────
    # 3. SOHBET ASİSTANI
    # ─────────────────────────────────────────

    def chat(self, user_message: str, rapor: Dict[str, Any]) -> str:
        """
        Şirket verisi üzerinden sohbet.
        Konuşma geçmişini korur (çok turlu).
        """
        # İlk mesajda şirket verisini context olarak ekle
        if not self.chat_history:
            self.chat_history.append({
                "role": "user",
                "content": f"Şirket verim:\n{json.dumps(rapor, ensure_ascii=False, indent=2)}\n\nBu veriler üzerinden sorularıma cevap ver."
            })
            self.chat_history.append({
                "role": "model",
                "content": "Anladım! Şirketinizin finansal verilerini inceledim. Sorularınızı yanıtlamaya hazırım."
            })

        self.chat_history.append({"role": "user", "content": user_message})

        # Gemini formatına dönüştür
        messages = [
            {"role": m["role"], "parts": [m["content"]]}
            for m in self.chat_history
        ]

        try:
            chat_session = self.model.start_chat(history=messages[:-1])
            response = chat_session.send_message(user_message)
            ai_reply = response.text
            self.chat_history.append({"role": "model", "content": ai_reply})
            return ai_reply
        except Exception as e:
            return f"⚠️ Sohbet hatası: {str(e)}"

    def reset_chat(self):
        """Sohbet geçmişini temizler."""
        self.chat_history = []

    # ─────────────────────────────────────────
    # 4. SENARYO YORUMU
    # ─────────────────────────────────────────

    def scenario_comment(self, mevcut: Dict, senaryo: Dict) -> str:
        """Senaryo analizi sonucunu yorumlar."""
        prompt = f"""
Bir senaryo analizi yapıldı. Sonuçları yöneticiye yorum:

Mevcut Durum:
- Gelir: {mevcut.get('gelir', 0):,.0f} ₺
- Net Kar: {mevcut.get('net_kar', 0):,.0f} ₺
- Kar Marjı: %{mevcut.get('kar_marji', 0)}

Senaryo (gelir artışı + gider azalışı):
- Yeni Gelir: {senaryo.get('gelir', 0):,.0f} ₺
- Yeni Net Kar: {senaryo.get('net_kar', 0):,.0f} ₺
- Yeni Kar Marjı: %{senaryo.get('kar_marji', 0)}

Bu senaryonun gerçekçiliği ve uygulanabilirliği hakkında 3-4 cümle yorum yaz.
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"⚠️ Senaryo yorumu üretilemedi: {str(e)}"

"""
KazKaz AI - AI Analiz Motoru (Groq + Gemini destekli)
======================================================
Groq (ücretsiz, hızlı) veya Gemini ile çalışır.
Groq modelleri: llama-3.3-70b-versatile, mixtral-8x7b-32768
"""

from typing import Dict, Any, List, Optional
import json


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


class GeminiEngine:
    """
    KazKaz AI için AI motoru.
    Groq (varsayılan) veya Gemini ile çalışır.

    Kullanım:
        ai = GeminiEngine(api_key="gsk_...", provider="groq")
        yorum = ai.analyze(rapor)
    """

    def __init__(self, api_key: str, provider: str = "groq"):
        self.api_key  = api_key
        self.provider = provider.lower()
        self.chat_history: List[Dict[str, str]] = []
        self._client = None
        self._init_client()

    def _init_client(self):
        if self.provider == "groq":
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
                self._model  = "llama-3.3-70b-versatile"
            except ImportError:
                raise ImportError("groq kurulu değil: pip install groq")

        elif self.provider == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(
                    model_name="gemini-2.0-flash",
                    system_instruction=SYSTEM_PROMPT,
                )
                self._model = "gemini-2.0-flash"
            except ImportError:
                raise ImportError("google-generativeai kurulu değil")

        elif self.provider == "openai":
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
                self._model  = "gpt-4o-mini"
            except ImportError:
                raise ImportError("openai kurulu değil: pip install openai")

        else:
            raise ValueError(f"Bilinmeyen provider: {self.provider}")

    def _call(self, prompt: str) -> str:
        """Provider'a göre API çağrısı yapar."""
        try:
            if self.provider == "groq":
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": prompt},
                    ],
                    max_tokens=1500,
                    temperature=0.7,
                )
                return response.choices[0].message.content

            elif self.provider == "gemini":
                response = self._client.generate_content(prompt)
                return response.text

            elif self.provider == "openai":
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": prompt},
                    ],
                    max_tokens=1500,
                )
                return response.choices[0].message.content

        except Exception as e:
            return f"⚠️ AI yanıt üretemedi: {str(e)}"

    # ─────────────────────────────────────────
    # 1. FİNANSAL ANALİZ YORUMU
    # ─────────────────────────────────────────

    def analyze(self, rapor: Dict[str, Any]) -> str:
        prompt = self._build_analysis_prompt(rapor)
        return self._call(prompt)

    def _build_analysis_prompt(self, rapor: Dict[str, Any]) -> str:
        g = rapor.get("gelir", {})
        e = rapor.get("gider", {})
        k = rapor.get("karlilik", {})
        s = rapor.get("saglik_skoru", {})

        # Şirket profili varsa ekle
        profil = rapor.get("sirket_profili", {})
        profil_metni = ""
        if profil:
            profil_metni = f"""
## Şirket Profili
- Şirket: {profil.get('sirket_adi', '-')}
- Sektör: {profil.get('sektor', '-')} / {profil.get('alt_sektor', '')}
- Büyüklük: {profil.get('buyukluk', '-')} ({profil.get('calissan_sayisi', 0)} çalışan)
- Kuruluş: {profil.get('kuruluş_yili', '-')} ({profil.get('yas', 0)} yaşında)
- Şehir: {profil.get('sehir', '-')}
- Aktif Müşteri: {profil.get('musteri_sayisi', 0)}
- Aylık Yeni Müşteri: {profil.get('aylik_yeni_musteri', 0)}
- Churn Oranı: %{profil.get('musteri_kayip_orani', 0)}
- Ortalama Sepet: {profil.get('ortalama_sepet', 0):,.0f} ₺
- Hedef Pazar: {profil.get('hedef_pazar', '-')}
- Dijital Satış: %{profil.get('dijital_satis_orani', 0)}
- Ana Rakipler: {profil.get('ana_rakipler', 'Belirtilmemiş')}
- Rekabet Avantajı: {profil.get('rekabet_avantaji', 'Belirtilmemiş')}
- En Büyük Gider: {profil.get('en_buyuk_gider', 'Belirtilmemiş')}
- Büyüme Hedefi: %{profil.get('buyume_hedefi', 0)}
- Ciro Hedefi: {profil.get('yillik_ciro_hedef', 0):,.0f} ₺
- Şirket Açıklaması: {profil.get('aciklama', '-')}
"""

        return f"""
{profil_metni}
## Finansal Özet
- Toplam Gelir: {g.get('toplam_gelir', 0):,.0f} ₺
- Ortalama Aylık Gelir: {g.get('ortalama_aylik_gelir', 0):,.0f} ₺
- Ortalama Büyüme: %{g.get('ortalama_buyume_orani', 0)}
- En Karlı Kategori: {g.get('en_karli_kategori', {}).get('kategori', '-')}
- Toplam Gider: {e.get('toplam_gider', 0):,.0f} ₺
- Sabit Gider Oranı: %{e.get('sabit_gider_orani', 0)}
- Net Kar: {k.get('toplam_net_kar', 0):,.0f} ₺
- Kar Marjı: %{k.get('kar_marji', 0)}
- Trend: {k.get('kar_trendi', '-')}
- Sağlık Skoru: {s.get('skor', 0)}/100 → {s.get('kategori', '-')}

Şirkete özel, somut ve uygulanabilir bir rapor yaz:
1. 📊 Genel Değerlendirme — şirkete özel (2-3 cümle)
2. ✅ Güçlü Yönler — verilerden destekle
3. ⚠️ Riskler — rakipler ve pazar bağlamında
4. 🎯 Stratejik Öneriler — en az 3 somut adım, bu şirkete özgü
"""

    # ─────────────────────────────────────────
    # 2. STRATEJİK ÖNERİLER
    # ─────────────────────────────────────────

    def strategic_recommendations(self, rapor: Dict[str, Any]) -> str:
        k = rapor.get("karlilik", {})
        s = rapor.get("saglik_skoru", {})
        prompt = f"""
Şirketin finansal durumu:
- Kar Marjı: %{k.get('kar_marji', 0)}
- Sağlık Skoru: {s.get('skor', 50)}/100
- Karlılık Trendi: {k.get('kar_trendi', 'Stabil')}

Bu verilere göre yöneticiye 5 somut ve uygulanabilir stratejik öneri sun.
Her öneri için: ne yapılmalı, neden yapılmalı, beklenen etki.
"""
        return self._call(prompt)

    # ─────────────────────────────────────────
    # 3. SOHBET ASİSTANI
    # ─────────────────────────────────────────

    def chat(self, user_message: str, rapor: Dict[str, Any]) -> str:
        if not self.chat_history:
            self.chat_history.append({
                "role": "user",
                "content": f"Şirket verim:\n{json.dumps(rapor, ensure_ascii=False, indent=2)}\n\nBu veriler üzerinden sorularıma cevap ver."
            })
            self.chat_history.append({
                "role": "assistant",
                "content": "Anladım! Şirketinizin finansal verilerini inceledim. Sorularınızı yanıtlamaya hazırım."
            })

        self.chat_history.append({"role": "user", "content": user_message})

        try:
            if self.provider in ["groq", "openai"]:
                messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
                    {"role": m["role"], "content": m["content"]}
                    for m in self.chat_history
                ]
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    max_tokens=1000,
                )
                reply = response.choices[0].message.content

            elif self.provider == "gemini":
                history = [
                    {"role": m["role"], "parts": [m["content"]]}
                    for m in self.chat_history[:-1]
                ]
                session = self._client.start_chat(history=history)
                reply   = session.send_message(user_message).text

            self.chat_history.append({"role": "assistant", "content": reply})
            return reply

        except Exception as e:
            return f"⚠️ Sohbet hatası: {str(e)}"

    def reset_chat(self):
        self.chat_history = []

    # ─────────────────────────────────────────
    # 4. SENARYO YORUMU
    # ─────────────────────────────────────────

    def scenario_comment(self, mevcut: Dict, senaryo: Dict) -> str:
        prompt = f"""
Bir senaryo analizi yapıldı:
Mevcut: Gelir {mevcut.get('gelir', 0):,.0f} ₺, Net Kar {mevcut.get('net_kar', 0):,.0f} ₺, Kar Marjı %{mevcut.get('kar_marji', 0)}
Senaryo: Gelir {senaryo.get('gelir', 0):,.0f} ₺, Net Kar {senaryo.get('net_kar', 0):,.0f} ₺, Kar Marjı %{senaryo.get('kar_marji', 0)}

Bu senaryonun gerçekçiliği ve uygulanabilirliği hakkında 3-4 cümle yorum yaz.
"""
        return self._call(prompt)

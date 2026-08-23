"""
KazKaz AI - AI Analiz Motoru (NVIDIA + Groq + Gemini destekli)
======================================================
v2.1 — Streaming desteği eklendi.

NVIDIA NIM, Groq veya Gemini ile çalışır.
NVIDIA varsayılan modeli: openai/gpt-oss-20b (düşük gecikmeli V1 profili)
Groq modelleri: llama-3.3-70b-versatile, mixtral-8x7b-32768

Kullanım:
    ai = GeminiEngine(api_key="gsk_...", provider="groq")

    # Bloke eden (eski davranış — geriye dönük uyumlu):
    yorum = ai.analyze(rapor)

    # Streaming (UI donmaz — önerilen):
    placeholder = st.empty()
    ai.analyze_stream(rapor, placeholder)
"""

from typing import Dict, Any, List, Optional, Generator
import json
import os

try:
    from llm_guardrail import Guardrail, GuardrailError
except Exception:   # guardrail modülü yoksa bile motor çalışsın
    Guardrail = None
    class GuardrailError(Exception):
        pass

try:
    from llm_cache import LLMCache
except Exception:   # cache modülü yoksa bile motor çalışsın
    LLMCache = None


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
✓ Yalnızca verilen ve doğrulanmış sayıları kullan
✓ Her önerinin dayandığı metriği açıkça göster
✓ Eksik veya çelişkili veride kesin hüküm yerine veri ihtiyacını belirt
✓ İnsan onayı gerektiren aksiyonları açıkça işaretle
✗ Teknik jargondan kaçın
✗ Finansal değer, sektör ortalaması veya tahmin uydurma
✗ Kullanıcı adına ödeme, kredi, yatırım ya da muhasebe işlemi başlatma
"""


class GeminiEngine:
    """
    KazKaz AI için AI motoru.
    NVIDIA NIM, Groq, Gemini veya OpenAI ile çalışır.
    Her metod hem bloke hem streaming modunda çalışabilir.
    """

    def __init__(
        self,
        api_key: str,
        provider: str = "groq",
        guardrail: Optional["Guardrail"] = None,
        user_id: Optional[str] = None,
        cache: Optional["LLMCache"] = None,
    ):
        """
        guardrail: opsiyonel LLM guardrail (llm_guardrail.Guardrail).
                   None ise geri uyumluluk için hiçbir kontrol yapılmaz.
        user_id  : rate-limit, usage metering ve cache anahtarı için kimlik.
        cache    : opsiyonel LLM response cache (llm_cache.LLMCache).
                   None ise her çağrı LLM'e gider.
        """
        self.api_key      = api_key
        self.provider     = provider.lower()
        self.chat_history: List[Dict[str, str]] = []
        self._client      = None
        self.guardrail    = guardrail
        self.user_id      = user_id
        self.cache        = cache
        self._init_client()

    # ── Guardrail yardımcıları ──────────────────────────────────────────────

    def _guard_pre(self, prompt: str) -> str:
        """Guardrail varsa prompt'u temizle/onayla; yoksa aynen döndür."""
        if self.guardrail is None:
            return prompt
        return self.guardrail.pre_call(self.user_id, prompt)

    def _guard_post(self, prompt: str, response: str) -> None:
        """Guardrail varsa token metering yaz."""
        if self.guardrail is not None:
            self.guardrail.post_call(self.user_id, prompt, response)

    def _init_client(self):
        if self.provider == "groq":
            try:
                from groq import Groq
                self._client = Groq(api_key=self.api_key)
                self._model  = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
            except ImportError:
                raise ImportError("groq kurulu değil: pip install groq")

        elif self.provider == "gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(
                    model_name=os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip(),
                    system_instruction=SYSTEM_PROMPT,
                )
                self._model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
            except ImportError:
                raise ImportError("google-generativeai kurulu değil")

        elif self.provider == "openai":
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
                self._model  = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
            except ImportError:
                raise ImportError("openai kurulu değil: pip install openai")

        elif self.provider == "nvidia":
            try:
                from openai import OpenAI

                self._client = OpenAI(
                    base_url=os.getenv(
                        "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
                    ).strip().rstrip("/"),
                    api_key=self.api_key,
                    timeout=float(os.getenv("NVIDIA_TIMEOUT_SECONDS", "30")),
                    max_retries=int(os.getenv("NVIDIA_MAX_RETRIES", "0")),
                )
                self._model = os.getenv(
                    "NVIDIA_MODEL", "openai/gpt-oss-20b"
                ).strip()
            except ImportError:
                raise ImportError("openai kurulu değil: pip install openai")

        else:
            raise ValueError(f"Bilinmeyen provider: {self.provider}")

    # ─────────────────────────────────────────────────────────────────────────
    # DÜŞÜK SEVİYE ÇAĞRI — Bloke eden (geriye dönük uyumlu)
    # ─────────────────────────────────────────────────────────────────────────

    def _sampling_options(self) -> Dict[str, Any]:
        """Sağlayıcının resmi örneğine uygun örnekleme ayarlarını döndürür."""
        if self.provider == "nvidia" and self._model in {"openai/gpt-oss-20b", "openai/gpt-oss-120b"}:
            return {"temperature": 1.0, "top_p": 1.0, "reasoning_effort": "low"}
        if self.provider == "nvidia":
            return {"temperature": 0.2, "top_p": 0.7}
        return {"temperature": 0.7}

    def _call(self, prompt: str, max_tokens: int = 1500) -> str:
        """Provider'a göre tam yanıt döner (bloke eder). Guardrail + cache sarmalıyla."""
        try:
            prompt = self._guard_pre(prompt)
        except GuardrailError as ge:
            return f"⚠️ İstek reddedildi: {ge}"

        cache_ctx = {"model": self._model, "provider": self.provider,
                     "max_tokens": max_tokens, "system": "default"}
        if self.cache is not None:
            cached = self.cache.get(self.user_id, prompt, cache_ctx)
            if cached is not None:
                self._guard_post(prompt, cached)
                return cached

        result = ""
        try:
            if self.provider in ("groq", "openai", "nvidia"):
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": prompt},
                    ],
                    max_tokens=max_tokens,
                    **self._sampling_options(),
                )
                result = response.choices[0].message.content

            elif self.provider == "gemini":
                response = self._client.generate_content(prompt)
                result = response.text

        except Exception as e:
            return f"⚠️ AI yanıt üretemedi: {str(e)}"

        if self.cache is not None and result and not result.startswith("⚠️"):
            self.cache.set(self.user_id, prompt, cache_ctx, result)

        self._guard_post(prompt, result)
        return result

    def generate(self, prompt: str, max_tokens: int = 1500) -> str:
        """Sağlayıcıdan metin üretir; API orkestrasyonunun açık giriş noktasıdır."""
        return self._call(prompt, max_tokens=max_tokens)

    @property
    def model_name(self) -> str:
        """Gizli bilgi içermeyen, gözlemlenebilir model adını döndürür."""
        return self._model

    # ─────────────────────────────────────────────────────────────────────────
    # DÜŞÜK SEVİYE ÇAĞRI — Streaming generator
    # ─────────────────────────────────────────────────────────────────────────

    def _stream(self, prompt: str, max_tokens: int = 1500) -> Generator[str, None, None]:
        """
        Token token metin üretir.
        Her yield bir string chunk'tır.

        Kullanım:
            for chunk in ai._stream(prompt):
                collected += chunk
        """
        try:
            if self.provider in ("groq", "openai", "nvidia"):
                stream = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": prompt},
                    ],
                    max_tokens=max_tokens,
                    stream=True,
                    **self._sampling_options(),
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta

            elif self.provider == "gemini":
                response = self._client.generate_content(prompt, stream=True)
                for chunk in response:
                    if chunk.text:
                        yield chunk.text

        except Exception as e:
            yield f"\n\n⚠️ Streaming hatası: {str(e)}"

    # ─────────────────────────────────────────────────────────────────────────
    # YÜKSEK SEVİYE YARDIMCI — st.empty() placeholder'a yaz
    # ─────────────────────────────────────────────────────────────────────────

    def _stream_to_placeholder(
        self,
        prompt:      str,
        placeholder,               # st.empty() objesi
        max_tokens:  int = 1500,
        prefix:      str = "",     # Yanıtın başına eklenecek sabit metin
    ) -> str:
        """
        Streaming çıktısını Streamlit placeholder'a token token yazar.
        Tamamlandığında tam metni döner (kaydetmek için).

        Örnek:
            ph = st.empty()
            tam_yorum = ai._stream_to_placeholder(prompt, ph)
        """
        try:
            prompt = self._guard_pre(prompt)
        except GuardrailError as ge:
            mesaj = f"⚠️ İstek reddedildi: {ge}"
            placeholder.markdown(
                f'<div style="background:#FEF2F2;border:1px solid #FECACA;'
                f'border-radius:12px;padding:16px 20px;color:#991B1B;">'
                f'{mesaj}</div>',
                unsafe_allow_html=True,
            )
            return mesaj

        toplam = prefix
        for chunk in self._stream(prompt, max_tokens):
            toplam += chunk
            placeholder.markdown(
                f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
                f'border-radius:12px;padding:16px 20px;color:#334155;'
                f'font-size:0.88rem;line-height:1.8;white-space:pre-wrap;">'
                f'{toplam}▌</div>',
                unsafe_allow_html=True,
            )
        # İmleç kaldır, son hali yaz
        placeholder.markdown(
            f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
            f'border-radius:12px;padding:16px 20px;color:#334155;'
            f'font-size:0.88rem;line-height:1.8;white-space:pre-wrap;">'
            f'{toplam}</div>',
            unsafe_allow_html=True,
        )
        self._guard_post(prompt, toplam)
        return toplam

    # ─────────────────────────────────────────────────────────────────────────
    # 1. FİNANSAL ANALİZ YORUMU
    # ─────────────────────────────────────────────────────────────────────────

    def analyze(self, rapor: Dict[str, Any]) -> str:
        """Tam analiz — bloke eder, geriye dönük uyumlu."""
        return self._call(self._build_analysis_prompt(rapor))

    def analyze_stream(self, rapor: Dict[str, Any], placeholder) -> str:
        """
        Tam analiz — streaming, UI donmaz.

        Kullanım:
            ph = st.empty()
            with st.spinner("Analiz yapılıyor..."):
                yorum = ai.analyze_stream(rapor, ph)
            st.session_state["ai_analiz"] = yorum
        """
        return self._stream_to_placeholder(
            self._build_analysis_prompt(rapor), placeholder
        )

    def _build_analysis_prompt(self, rapor: Dict[str, Any]) -> str:
        g = rapor.get("gelir", {})
        e = rapor.get("gider", {})
        k = rapor.get("karlilik", {})
        s = rapor.get("saglik_skoru", {})

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

    # ─────────────────────────────────────────────────────────────────────────
    # 2. STRATEJİK ÖNERİLER
    # ─────────────────────────────────────────────────────────────────────────

    def strategic_recommendations(self, rapor: Dict[str, Any]) -> str:
        """Bloke eden versiyon — geriye dönük uyumlu."""
        return self._call(self._build_strategy_prompt(rapor))

    def strategic_recommendations_stream(
        self, rapor: Dict[str, Any], placeholder
    ) -> str:
        """Streaming versiyon."""
        return self._stream_to_placeholder(
            self._build_strategy_prompt(rapor), placeholder
        )

    def _build_strategy_prompt(self, rapor: Dict[str, Any]) -> str:
        k = rapor.get("karlilik", {})
        s = rapor.get("saglik_skoru", {})
        g = rapor.get("gelir", {})
        return f"""
Şirketin finansal durumu:
- Kar Marjı: %{k.get('kar_marji', 0)}
- Sağlık Skoru: {s.get('skor', 50)}/100
- Karlılık Trendi: {k.get('kar_trendi', 'Stabil')}
- Aylık Büyüme: %{g.get('ortalama_buyume_orani', 0)}
- Sabit Gider Oranı: %{rapor.get('gider', {}).get('sabit_gider_orani', 0)}

Bu verilere göre yöneticiye 5 somut ve uygulanabilir stratejik öneri sun.
Her öneri için: ne yapılmalı, neden yapılmalı, beklenen etki.
"""

    # ─────────────────────────────────────────────────────────────────────────
    # 3. SOHBET ASİSTANI
    # ─────────────────────────────────────────────────────────────────────────

    def chat(self, user_message: str, rapor: Dict[str, Any]) -> str:
        """Sohbet — bloke eden, geriye dönük uyumlu."""
        self._prepare_chat_context(rapor)
        self.chat_history.append({"role": "user", "content": user_message})
        try:
            reply = self._chat_call()
            self.chat_history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            return f"⚠️ Sohbet hatası: {str(e)}"

    def chat_stream(
        self,
        user_message: str,
        rapor:        Dict[str, Any],
        placeholder,
    ) -> str:
        """
        Sohbet — streaming versiyon, UI donmaz.

        Kullanım:
            ph = st.empty()
            reply = ai.chat_stream(soru, rapor, ph)
            st.session_state.chat_history.append({"role":"ai","content":reply})
        """
        self._prepare_chat_context(rapor)
        self.chat_history.append({"role": "user", "content": user_message})

        prompt = self._build_chat_prompt(user_message)
        reply  = self._stream_to_placeholder(prompt, placeholder, max_tokens=1000)

        self.chat_history.append({"role": "assistant", "content": reply})
        return reply

    def _prepare_chat_context(self, rapor: Dict[str, Any]):
        """İlk mesajda finansal bağlamı history'e ekler."""
        if not self.chat_history:
            try:
                rapor_str = json.dumps(
                    {k: v for k, v in rapor.items()
                     if not hasattr(v, "to_dict")},   # DataFrame'leri atla
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
            except Exception:
                rapor_str = str(rapor)[:3000]

            self.chat_history.append({
                "role": "user",
                "content": (
                    f"Şirket finansal verim:\n{rapor_str[:3000]}\n\n"
                    "Bu veriler üzerinden sorularıma cevap ver."
                ),
            })
            self.chat_history.append({
                "role": "assistant",
                "content": (
                    "Anladım! Şirketinizin finansal verilerini inceledim. "
                    "Sorularınızı yanıtlamaya hazırım."
                ),
            })

    def _build_chat_prompt(self, user_message: str) -> str:
        """Tüm sohbet geçmişini tek prompt'a çevirir (streaming için)."""
        gecmis = ""
        for m in self.chat_history[:-1]:   # son mesaj (user) hariç
            rol = "Kullanıcı" if m["role"] == "user" else "KazKaz"
            gecmis += f"{rol}: {m['content']}\n\n"
        return f"{SYSTEM_PROMPT}\n\n{gecmis}Kullanıcı: {user_message}\n\nKazKaz:"

    def _chat_call(self) -> str:
        """Sohbet — bloke eden tam çağrı."""
        if self.provider in ("groq", "openai", "nvidia"):
            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
                {"role": m["role"], "content": m["content"]}
                for m in self.chat_history
            ]
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=1000,
                **self._sampling_options(),
            )
            return response.choices[0].message.content

        elif self.provider == "gemini":
            history = [
                {"role": m["role"], "parts": [m["content"]]}
                for m in self.chat_history[:-1]
            ]
            session = self._client.start_chat(history=history)
            return session.send_message(
                self.chat_history[-1]["content"]
            ).text

        return "⚠️ Provider desteklenmiyor."

    def reset_chat(self):
        self.chat_history = []

    # ─────────────────────────────────────────────────────────────────────────
    # 4. SENARYO YORUMU
    # ─────────────────────────────────────────────────────────────────────────

    def scenario_comment(self, mevcut: Dict, senaryo: Dict) -> str:
        """Bloke eden — geriye dönük uyumlu."""
        return self._call(self._build_scenario_prompt(mevcut, senaryo))

    def scenario_comment_stream(
        self, mevcut: Dict, senaryo: Dict, placeholder
    ) -> str:
        """Streaming versiyon."""
        return self._stream_to_placeholder(
            self._build_scenario_prompt(mevcut, senaryo),
            placeholder,
            max_tokens=600,
        )

    def _build_scenario_prompt(self, mevcut: Dict, senaryo: Dict) -> str:
        return f"""
Bir senaryo analizi yapıldı:
Mevcut: Gelir {mevcut.get('gelir', 0):,.0f} ₺, Net Kar {mevcut.get('net_kar', 0):,.0f} ₺, Kar Marjı %{mevcut.get('kar_marji', 0)}
Senaryo: Gelir {senaryo.get('gelir', 0):,.0f} ₺, Net Kar {senaryo.get('net_kar', 0):,.0f} ₺, Kar Marjı %{senaryo.get('kar_marji', 0)}

Bu senaryonun gerçekçiliği ve uygulanabilirliği hakkında 3-4 cümle yorum yaz.
"""

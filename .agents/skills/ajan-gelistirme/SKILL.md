---
name: ajan-gelistirme
description: KazKaz AI'da ajan (agent) ekleme/güncelleme standardı. Deterministik ajan deseni, bas_denetci kapısı, guardrail entegrasyonu, insan onayı bayrakları, LLM araç döngüsü ve hafıza kuralları. Tetikleyiciler yeni ajan, cfo_agent, advanced_agents, ai_orchestrator, guardrail, sohbet, hafıza.
---

# Ajan Geliştirme Standardı

## Mimari Felsefe (değiştirilemez)

> Deterministik motor hakimdir. LLM yalnızca yorumcudur. İnsan onayı yapısal olarak zorunludur.

- Ajan = saf Python fonksiyonu/sınıfı (LLM'siz) → deterministik, maliyetsiz, test edilebilir. Örnek: `api/advanced_agents.py` (mizan, 13 hafta nakit, alacak yaşlandırma, vade duvarı, anomali).
- LLM'e giden her yanıt `api/ai_guardrails.py:ai_yanitini_dogrula()`'dan geçer. Sayısı doğrulanamayan cevap reddedilir → provider failover (nvidia→groq→gemini, `ai_orchestrator.py:18-22`) → deterministik fallback.
- Kritik mutabakat hatasında `bas_denetci` AI'ı tamamen kapatabilir (`advanced_agents.py:625-636`).
- Tüm tavsiyelerde `insan_onayi: True` bayrağı; ajan kendi başına işlem başlatamaz.

## Yeni Ajan Ekleme Kontrol Listesi

```
- [ ] Saf hesaplama, LLM bağımlılığı yok (LLM sadece anlatım katmanında)
- [ ] Girdi: Pydantic modeller / dataclass — serbest string enjeksiyonu yok
- [ ] Çıktı: bulgular + şiddet seviyesi + kanıt (file:line/formula_id)
- [ ] bas_denetci çapraz mutabakat kapısına bağlandı mı? (kritikse)
- [ ] api/tests/test_advanced_agents.py'e test
- [ ] Kullanıcı-facing metinler Türkçe
```

## LLM Katmanı Kuralları

1. **Guardrail bypass YASAK:** Yeni bir LLM çağrı noktası eklerken (Streamlit dahil) mutlaka guardrail + PII maskeleme (`hassas_veriyi_maskele`) + failover zinciri kullan. Doğrudan `GeminiEngine._call` UI'dan çağrılamaz.
2. **Prompt enjeksiyonu:** Şirket profili serbest metin alanları (`aciklama`, `ana_rakipler`, `sirket_adi`...) prompt'a maskelenmeden/konumlandırılmadan sokulamaz; talimat hiyerarşisi bloğu (KURALLAR) korunmalı.
3. **Hafıza:** Sohbet geçmişi kabul ediliyorsa GERÇEKTEN prompt'a beslenmeli (`main.py`'deki ölü `gecmis` alanı hatası tekrarlanmaz). Kalıcı hafıza için Firestore koleksiyonu + KVKK retention (365 gün) uygulanır.
4. **Token ekonomisi:** Her LLM çağrısı token kullanımını loglar; chat history sınırlı/özetlenmiş; aynı veri+ soru için cache düşünülür.
5. **Hata kanalı:** Sentinel emoji string yerine exception/typed result kullan (mevcut `⚠️` prefix kontrolü kırılgandır — yeni kodda tekrar etme).

## Ajansal Yükseltme Yolu (plan)

Araç döngüsü/function-calling eklenirken:
- Motor araçları salt-okunur başlar (hesapla/raporla); yazma araçları (örn. "bütçe taslağı oluştur") ayrı onay kuyruğu state machine'i ile gelir.
- Her araç çağrısı audit log'a (Firestore `auditLogs`) yazılır.
- Maksimum döngü sayısı ve token bütçesi config'den sınırlanır.

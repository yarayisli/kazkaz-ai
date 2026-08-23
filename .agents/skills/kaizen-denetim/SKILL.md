---
name: kaizen-denetim
description: KazKaz AI'da periyodik kaizen denetimi — bilinen hata kalıplarını tara, test kapsamı kapılarını kontrol et, vizyon-kod sapmasını ve kök/API metodoloji ayrışmasını tespit et. Tetikleyiciler kaizen, denetim, audit, kod inceleme, kalite kontrol, sürüm öncesi kontrol.
---

# Kaizen Denetimi

Periyodik (veya büyük değişiklik sonrası) çalıştırılan tarama protokolü.

## Faz 1 — Bilinen Hata Kalıpları Taraması

Her biri geçmişte gerçek hata oldu; grep ile tara:

| Kalıp | Nasıl taranır | Nerede yaşandı |
|---|---|---|
| Nominal/reel baz karışımı | `npv_reel`, `(1+r_nom)/(1+r_inf)` çevresindeki akış işlemleri | investment_engine.py:112 |
| Girdi echo eden metrik | Metrik fonksiyonlarında `return` edilen değer input alanıyla aynı mı | cashflow_engine.py:192 |
| Default sapması | Dataclass default vs from_dict default karşılaştırması | investment_engine.py:62/520 |
| Sabit ±% CI | `%15`, `%20`, `±0.15` gibi sabitler üst/alt olarak | forecast_engine.py:214 |
| Guardrailsiz LLM çağrısı | `_call(`, `.generate(`, `.analyze(` çağrılarının guardrail içinde olup olmadığı | cfo_ui.py |
| Çift tanım | Aynı formülün iki implementasyonu (current ratio, DSCR, marj eşikleri) | services.py vs cashflow_engine.py |
| Ölü alan | Modelde tanımlı ama hiç okunmayan alanlar (gecmis, para_birimi) | models.py, debt_engine.py |

## Faz 2 — Test Kapsamı Kapıları

Şu anlık minimum bar (yükseltilecek):

- [ ] CI kök `test_engines.py`'i çalıştırıyor mu? (şu an ÇALIŞTIRMIYOR — açık borç)
- [ ] Her motorda en az: bilinen-değer testi + eksik-veri testi
- [ ] Monte Carlo, DSCR/scorer, sektör motoru smoke testi var mı?
- [ ] Yeni özellik PR'ında test diff'i var mı?

## Faz 3 — Vizyon-Kod Sapması

Vizyon belgesi iddialarını kodla karşılaştır:
- Landing/dokümanda vaat edilen her özellik kodda karşılığına sahip mi? ("GRI uyumlu" gibi kanıtsız iddia = yayın blokeri, docs/KVKK_UYUM_PAKETI.md yayin kuralına aykırı)
- UI'da gösterilen her metrik gerçekten hesaplanıyor mu? (CAC/LTV vakası gibi)

## Faz 4 — Nesil Ayrışması (kök Streamlit ↔ API/web)

- Aynı kullanıcı işlemi iki yolda farklı sonuç veriyor mu? (farklı skor/farklı AI güvenliği)
- Kök motorlarda düzeltilen hata API tarafında da mı? (ve tersi)
- Hedef: API metodolojisi tek standart; kök zayıf metodoloji sunmamalı.

## Rapor Formatı

```markdown
# Kaizen Denetimi YYYY-AA-GG
## 🔴 Bloker (P0) — hesaplama hataları
## 🟡 Borç (P1) — metodoloji/mimari
## 🟢 İyileştirme (P2)
## Metrik: test sayısı, kapsam boşlukları, açık borç sayısı (önceki denetime göre Δ)
```

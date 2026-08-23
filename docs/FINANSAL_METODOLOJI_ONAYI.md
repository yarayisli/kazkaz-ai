# KazKaz AI V1 finansal metodoloji kabul formu

Durum: **teknik testler tamamlanabilir; uzman onayı bekliyor**.

Bu belge CFO/SMMM onayı olmadan `FINANCIAL_METHODOLOGY_APPROVED=true` yapılmaması için imza kapısıdır.

## Kontrol edilecek tanımlar

- FAVÖK: `Net kâr + faiz gideri + vergi gideri + amortisman`.
- FVÖK: `Net kâr + faiz gideri + vergi gideri`.
- Serbest nakit akışı: `Operasyonel nakit akışı − CapEx`.
- Net kâr, operasyonel nakit ve dönem sonu nakit birbirinin yerine kullanılmaz.
- Cari oran yalnız `Dönen varlıklar / Kısa vadeli yükümlülükler` ile hesaplanır.
- DSCR, aynı para birimine çevrilmiş borç servisi ve uzman tarafından kabul edilen operasyonel nakit tanımıyla hesaplanır.
- Bilanço kontrolü: `Aktifler = Yükümlülükler + Özkaynak`.
- Nakit köprüsü: `Dönem başı nakit + faaliyet + yatırım + finansman = dönem sonu nakit`.

## Otomatik kanıt dosyaları

- `api/tests/fixtures/financial_metrics_expected.json`
- `api/tests/fixtures/financial_statements_expected.json`
- `api/tests/fixtures/advanced_agents_expected.json`
- `api/tests/test_financial_metrics.py`
- `api/tests/test_financial_statements.py`
- `api/tests/test_advanced_agents.py`

## Uzman kabul kaydı

- İnceleyen CFO/SMMM:
- Mesleki unvan / sicil:
- İnceleme tarihi:
- Kabul edilen formül sürümü: `2026.08-v1`
- Sonuç: `[ ] Onaylandı  [ ] Düzeltme gerekli`
- Açıklama:
- İmza / doğrulanabilir onay kaydı:

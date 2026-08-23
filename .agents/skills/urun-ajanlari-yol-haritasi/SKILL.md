---
name: urun-ajanlari-yol-haritasi
description: KazKaz AI ürün ajanları envanteri ve eksik ajanlar yol haritası. Yeni ürün özelliği/ajan planlarken, backlog oluştururken, vizyon belgesiyle hizalama yaparken kullan. Mevcut 16 ajanın listesi + eksik 10 ajanın öncelik sırası.
---

# Ürün Ajanları Envanteri ve Yol Haritası

## Mevcut Ajanlar (kodda canlı)

### Deterministik (api/advanced_agents.py)
| Ajan | İş |
|---|---|
| mizan_ajani | Borç/alacak eşitliği, hesap karışımı kapsamı, bilanço denklemi |
| finansal_tablo_mutabakat_ajani | Gelir tablosu/bilanço üretimi + beyanla mutabakat |
| nakit_13_hafta_ajani | 13 haftalık nakit projeksiyonu, eşik ihlali tarihi |
| alacak_ajani | Alacak yaşlandırma kovaları, müşteri konsantrasyonu |
| borc_servis_ajani | Borç servis takvimi, DSCR, 90 gün vade duvarı |
| butce_tahmin_ajani | Bütçe-gerçekleşen sapma, MAPE ile tahmin doğrulama |
| anomali_ve_denetim_ajani | Mükerrer fatura, z-skor anomalisi, SHA-256 denetim izi |
| bas_denetci | Çapraz mutabakat kapısı; kritik bulguda AI'ı kapatır |

### Orkestrasyon (api/ai_orchestrator.py + services.py)
veri_kalitesi_ajani (AI kapısı), finansal_denetim_ajani (kanonik metrikler+kural riskleri), ai_anlatim_ajani (tek LLM çağrısı)

### Kök Streamlit (cfo_agent.py)
FinancialHealthTool, CashFlowAlertTool, InvestmentAdvisorTool (nötrleştirilmiş), DebtAdvisorTool, ReportGeneratorTool

## Eksik Ajanlar (öncelik sırasıyla — vizyon belgesi hedefleri)

1. **kompozit_skor_ajani** — Finans+Risk+Likidite+Konsantrasyon+VeriOlgunluğu tek skor; vizyonun "CFO Kompozit Skoru"nun gerçek hali (ESG/İK başlangıçta veri-hazırlığı alt boyutu).
2. **cac_ltv_ajani** — Pazarlama gideri+kazanım tarihi verisiyle cohort retansiyonu, LTV, CAC; churn girdisini hesaba bağlar.
3. **strateji_ajani** — Kural+LLM hibrit "3 adımlı değer artışı yol haritası" üretici; çıktı insan onayına düşer.
4. **esg_veri_ajani** — compliance_readiness'ın ötesine geçen ham ESG veri toplama/skorlama (GRI kod eşlemeli, iddiasız dil).
5. **ik_analitik_ajani** — Personel sayısı/ciro/kayıp gün verisinden İK KPI'ları (vizyonun "İnsan" boyutu).
6. **risk_birlestirici_ajani** — Müşteri konsantrasyonu + borç vade duvarı + FX pozisyonu + nakit runway → birleşik risk skoru.
7. **efatura_ajani** — GİB e-Fatura XML / Paraşüt API'den otomatik veri çekme (veri giriş yükünü çözen kanal).
8. **odeme_ajani** — Iyzico/PayTR abonelik yükseltme akışı; plan limitleriyle entegre.
9. **portfoy_izleme_ajani** — Yatırımcı için çoklu şirket portföy paneli (workspace_service altyapısını kullanır).
10. **benchmark_yenileme_ajani** — Statik SECTOR_DB'nin CPI endekslemesi + anonim havuz beslemesi.

## Kural

Yeni ajan eklerken `/ajan-gelistirme` standardını, finansal hesap içeriyorsa `/finans-metodoloji` kurallarını uygula. Vizyon belgesindeki her yeni vaadin bu listede karşılığı olmalı.

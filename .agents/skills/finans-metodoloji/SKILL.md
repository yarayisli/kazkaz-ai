---
name: finans-metodoloji
description: KazKaz AI finansal hesaplama metodolojisi kuralları ve yasakları. Finansal motor/kod yazarken veya düzeltirken KULLAN — BSMV/KKDF, nominal-reel tutarlılık, oran tanımları, sahte güven aralığı yasağı, sayı uydurma yasağı. Tetikleyiciler finansal hesaplama, NPV, DSCR, sağlık skoru, nakit akışı, tahmin, bütçe.
---

# Finans Metodolojisi Kuralları

Bu depoda finansal hesaplama yazarken/düzeltirken bu kurallar ZORUNLUDUR. Amaç: 360° denetimde bulunan P0/P1 hata kalıplarının tekrar etmesini önlemek.

## Mutlak Yasaklar (P0 hata kalıpları)

1. **Nominal/reel baz karışımı YASAK.** Nominal nakit akışlarını reel iskonto oranıyla iskonto etme (`investment_engine.py:112-121` hatası). Doğru ikisinden biri:
   - Akışları enflasyonla deflante et → reel oranla iskonto et, VEYA
   - Nominal akış + nominal iskonto (tercih edilen).
2. **Aynı hesap için girişe göre farklı default YASAK.** Dataclass default'ları ile `from_dict`/API path default'ları birebir aynı olmalı (bkz. `investment_engine.py:62-64` vs `:520-522` sapması).
3. **Girdiyi geri yansıtan metrik YASAK.** DSO/DPO/DIO gibi oranlar bakiyelerden HESAPLANMALI, kullanıcının yazdığı değerin aynısı dönülmemeli (`cashflow_engine.py:192-202` hatası).
4. **Sahte güven aralığı YASAK.** Nokta tahmin ± sabit yüzde (±15%/±20%) üst-alt sınır olarak sunulamaz. Ya gerçek istatistiksel aralık (Prophet CI, HW prediction interval) ya da hiç aralık + dürüst disclaimers.
5. **Sayı uydurma YASAK.** LLM çıktısındaki her sayı motorun hesapladığı değerle doğrulanmalı (`api/ai_guardrails.py`). Guardrail'siz LLM çağrısı eklenemez — Streamlit dahil.
6. **Runway açılış nakdine sabitlenemez.** Gözlem dönemi net akışı dahil edilmeli (`cashflow_engine.py:266` hatası).

## Türkiye-Spesifik Zorunluluklar

- Faiz maliyetinde **BSMV (%15)** ve uygunsa **KKDF** hesaba katılmalı; brüt faizle DSCR/faiz karşılama iyimser çıkar.
- "Net Borç/FAVÖK" deniyorsa nakit GERÇEKTEN netlenmeli (`debt_engine.py:240-244` yanlış etiket).
- FX cinsinden borç `para_birimi` ile ayrıştırılmalı; TRY borçla karıştırılmamalı, kur farkı modellemesi düşünülebilir.
- Tahmin/bütçe projeksiyonunda **Ramazan/Bayram regressörleri** (Prophet holidays TR takvimini kullan).
- Yüksek enflasyonda nominal trend ≈ fiyat; reel görünüm (deflatör) sunulmalı veya nominal olduğu açıkça etiketlenmeli.
- Statik benchmark değerleri TL ise **enflasyon endeksleme kancası** (örn. `kalibrasyon_tarihi` + CPI çarpanı) bulundur.

## Skorlama Disiplini

- Bileşik skorda bir faktör iki kez sayılamaz (gider oranı ≡ kâr marjı — çift sayım hatası).
- Net kâr "nakit" diye etiketlenemez; tahakkuk/nakit ayrımı yapılmalı.
- Eksik veri → sessizce 0 veya nötr skor DEĞİL; `durum="eksik_veri"` + eksik alan listesi (api standardı: `MetrikSonucu`).
- Her skor bileşeninin ağırlığı ve eşiği kodda tek yerden, sürüm numarasıyla yönetilmeli.

## Müşteri/CAC/LTV

- Değişken maliyeti gelire oransal dağıtmak tüm müşterilere eşit marj verir — bu "kârlılık analizi" OLMAZ (`customer_engine.py:123-136` hatası).
- Gerçek CAC/LTV için minimum veri: pazarlama/satış gideri, müşteri kazanım tarihi, cohort tanımı. Veri yoksa özellik sunulmaz, UI'da vaat edilmez.

## Kabul Kriteri

Her finansal değişiklikte: formül kaynağı (file:line), test (elle hesaplanmış beklenen değerle), ve varsa metodoloji uyarısı kontrol edilmeli. Şüphede → bu dosyadaki yasağa göre davran ve kullanıcıyı uyar.

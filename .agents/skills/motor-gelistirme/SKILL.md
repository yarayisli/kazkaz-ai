---
name: motor-gelistirme
description: KazKaz AI'da yeni finansal motor (*_engine.py) ekleme veya mevcut motoru standartlara çekme rehberi. MetrikSonucu kanıt zinciri, sürüm versiyonlu formüller, eksik-veri reddi, zorunlu testler. Tetikleyiciler yeni motor, yeni metrik, engine refactor, test ekleme.
---

# Motor Geliştirme Standardı

## Altın Standart: `api/financial_metrics.py`

Yeni finansal hesaplama eklerken BU deseni izle (Streamlit kök motorlarındaki gevşek desen değil):

```python
FORMUL_SURUMU = "2026.08-v1"

@dataclass
class MetrikSonucu:
    formula_id: str          # örn. "dscr_v1"
    formul: str              # okunabilir formül stringi
    girisler: dict           # kullanılan ham değerler
    kaynak_alanlar: list     # hangi alanlardan geldi
    guven: str               # "yüksek" | "orta" | "düşük"
    durum: str               # "tamam" | "eksik_veri"
    eksik_alanlar: list      # durum=eksik_veri ise zorunlu
    deger: float | None
```

Kurallar:
- Eksik veri → hesaplama REDDEDİLİR, varsayılan 0 / nötr 50 puan YOK.
- Her metriğin sürümü var; davranış değişirse sürüm artar.
- Formül stringi raporlarda kullanıcıya gösterilebilir olmalı.

## Mimari Kurallar

1. **Engine/UI ayrımı:** `*_engine.py` içinde Streamlit importu YASAK. Tüm kullanıcı-facing metin Türkçe.
2. **Tek doğruluk kaynağı:** Aynı metriğin iki tanımı olamaz. Yeni hesap `api/services.py` veya kök motorlardan zaten var mı kontrol et (grep: fonksiyon adı + İngilizce/Türkçe eşanlamlılar). Varsa yeniden kullan; sapma gerekiyor ise eskisini deprecate et.
3. **Veri alanları:** Kök = nakit defteri (`Tarih/Kategori/Gelir/Gider`); API = mizan + `FinansalGorunum`. Hangi domainde çalıştığını belgele.
4. **Magic number yok:** Ağırlık/eşik/tolerans modül başında adlandırılmış sabit + yorumda gerekçe + kalibrasyon tarihi.
5. **Türkiye varsayımları:** BSMV/KKDF, bayram etkisi, enflasyon — bkz. `/finans-metodoloji` skill'i.

## Zorunlu Testler

Yeni hesaplamada en az:
- [ ] Elle hesaplanmış bilinen değer testi (Excel/finansal hesap makinesi karşılaştırması)
- [ ] Eksik veri → `eksik_veri` durumu testi
- [ ] Sınır durumları (sıfır bölme, negatif, tek dönem)

Test yeri: kök motorlar → `test_engines.py`; API → `api/tests/test_*.py`.
DİKKAT: CI sadece `api/tests` çalıştırıyor — kök motor değişikliğinde `python -m pytest test_engines.py -v` lokal çalıştırılmalı ve CI'a kök testlerin eklenmesi için issue açılmalı.

## Kontrol Listesi

```
- [ ] Streamlit importu motor dosyasında yok
- [ ] MetrikSonucu benzeri kanıt yapısı var
- [ ] Eksik veri reddediliyor
- [ ] Magic numbers sabitlere alındı (+gerekçe+tarih)
- [ ] Mevcut metriklerle çift tanım yok
- [ ] test_engines.py veya api/tests'e test eklendi
- [ ] Lokal pytest geçti
```

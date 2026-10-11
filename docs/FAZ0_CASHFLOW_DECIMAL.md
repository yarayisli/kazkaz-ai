# Faz 0 — Nakit hassasiyeti uygulama dilimi

11 Ekim 2026. Bu değişiklik #36'nın sonlu girdi kontrolünün devamıdır.
Durum: owner incelemesi için hazırlanmış finansal davranış değişikliği.
Bu belge onaylı risk politikası, golden fixture veya invariant sözleşmesi değildir.

## Yapılan değişiklik

Aylık net/toplam/kapanış, pandas dönem gruplaması, 13 haftalık pencere
açılışı/kapanışı ve nakit köprüsü ortak Decimal aritmetiğini kullanır.
Float girdiler, API'nin aldığı sayının `str` temsili üzerinden ondalığa
çevrilir. Önceden istemcide veya importta kaybolmuş basamaklar geri gelmez.
Ara toplamlar yuvarlanmaz; görüntülenen para sonuçları iki basamakta
HALF_EVEN ile yuvarlanır. Aylık ham net hareket mevcut davranışa uygun
olarak kuruşa yuvarlanmaz. Runway bir, verimlilik oranı üç basamak kullanır.

Yerel Decimal bağlamı girdi basamaklarına göre hesaplanır; iptal olan
büyük tutarların yanında küçük ondalık hareketler korunur. Global Decimal
bağlamına dokunulmaz. API'de float/number biçimi korunur; sonlu sayı
aralığına sığmayan parasal sonuç, oran veya projeksiyon açık hata verir.
Nakit hesabına ait hata API'de `422 / nakit_hesaplama_araligi` döner;
NaN/Infinity sıfıra veya başarılı sonuçta null'a dönüştürülmez.

## Davranış farkları

- `1e16 + 1 - 1e16`: eski toplam 0, yeni toplam 1.
- `100.10 + 200.20`: sonuç 300.30 tutarında; JSON number biçiminde 300.3
  olabilir, iki basamaklı metin temsili API değişikliği değildir.
- 2.675 için eski float yuvarlama 2.67, ondalık HALF_EVEN 2.68.
- `[1e308, 1e308]` toplamı: eski sonuç Infinity, yeni davranış açık hata.
- Haftalık eksik/tam/inceleme durumları, ilk tekrar satırını seçme davranışı,
  tarih boşluğu uyarıları ve nakit köprüsünün mevcut 1 TL toleransı korunur.
  Bunlar yeni onaylı finansal politikalar olarak kabul edilmez.

## Doğrulama

- Yeni dosyada 20 regresyon testi: kuruş kaybı, ara yuvarlama, tarihli
  pencere açılışı, gerçek API rota hatası, pandas gruplama, oran/projeksiyon
  taşması, çağıran verinin korunması ve Decimal bağlam izolasyonu.
- Tüm API paketi: 294 test başarılı, skip yok; mevcut frontend üretim
  derlemesi yapılarak statik dosya testi de çalıştırıldı.
- Kök motor paketi: 129 testten 128 başarılı. Mevcut Forecast MAPE testi
  bu ortamda Prophet ile 33.39 üretip `<10` beklentisinde başarısız oldu.
  Aynı test değiştirilmemiş #36 dalında aynı 33.39 ile başarısız oldu.
  Forecast kodu, mevcut assertion, tolerans veya skip değiştirilmedi.
- Kullanım takip paketi: 10 test başarılı.
- 30 aylık tam rapor karşılaştırması: kuruşa yuvarlanmış gösterimler aynı;
  225 ham sayısal alanda float farkı, en büyük mutlak fark
  1.4551915228366852e-11. Hata/NaN/Infinity yok. Bu sayı owner tarafından
  kabul edilmiş tolerans değildir; ölçülen farkın kaydıdır.
- Aynı makinede 12 dönemlik aylık tam rapor ortalama süreleri: eski 1.74 ms,
  yeni 3.34 ms. Küçük yerel örneklem; üretim performans garantisi değildir.
- 30 haftalık tam raporun bütün alanları eski motorla birebir aynı.

## İnceleme ve sonraki dilimler

Risk HIGH: finansal yuvarlama ve hata davranışı değişiyor. HALF_EVEN ve
API davranışı merge öncesinde owner tarafından incelenmeli. Mevcut testler,
golden/invariant fixture'lar, bağımlılıklar ve korumalı dosyalar değiştirilmedi.
Finansal çıktı değişikliği üretimde etkinleştirilmedi.

Bu dilim tam Faz 0 veya tüm Cashflow Safety Pack değildir. Backend kanonik
sonucunun frontend/rapor/exportta tüketilmesi, aynı tarihli çelişkili
haftaların kesin kabul davranışı, gelir/giderin gerçek tahsilat/ödeme olarak
etiketlenmesi ve owner onaylı golden/invariant katmanı kalan işlerdir.
API number çıktısı çok büyük tutarlarda tüm kuruşları temsil edemez;
Decimal string/kuruş tamsayısı için sürümlü geçiş ayrıca değerlendirilmelidir.

#37 bağımlılık düzeltmesi ayrı PR'dır. Bu dal mevcut #36 kilidini kullanır;
#37 merge edilip taban güncellenmeden GitHub production npm audit kapısının
mevcut gRPC açığı nedeniyle geçmesi beklenmez. Kontrol kapısı kapatılmadı.
Docker runtime'daki mevcut eksik motor dosyaları da ayrı owner işidir.

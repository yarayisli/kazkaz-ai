# KazKaz AI V1 pilot kabul kapısı

Bu belge Kaizen çevrimlerinde her değişikliğin ölçülebilir bir kapıdan geçmesini
sağlar. Teknik testlerin geçmesi tek başına canlı yayın, KVKK veya finansal uzman
onayı anlamına gelmez.

## Otomatik teknik kapı

`./scripts/run_acceptance.sh` aşağıdakilerin tamamında başarılı olmalıdır:

- API, yetkilendirme, finansal metrik, ajan ve veri yaşam döngüsü testleri
- Eski finans motoru regresyon testleri
- Frontend TypeScript kontrolü ve production build
- Yüksek önem NPM bağımlılık denetimi
- Depoda gerçek API anahtarı/private key taraması

## Firebase güvenlik kapısı

- Emulator Suite üzerinde `company-a` kullanıcısı `company-b` verisini okuyamaz,
  yazamaz, dışa aktaramaz ve silemez.
- Viewer yazamaz/silemez; Analyst kaydedebilir ancak silemez; Admin ve CFO silebilir.
- Token iptali sonrasında korumalı bütün API uçları 401 döndürür.
- Başarılı test tarihi `TENANT_ISOLATION_TEST_PASSED=true` yapılmadan önce kanıtıyla kaydedilir.
- `firestore.rules` canlıya dağıtıldıktan sonra `FIRESTORE_RULES_DEPLOYED=true` yapılır.

## Finans ve AI kapısı

- CFO/SMMM golden dosyalardaki FAVÖK, net kâr, bilanço, nakit köprüsü ve DSCR
  sonuçlarını imzalı kontrol listesiyle onaylar.
- Kaynaksız sayı içeren AI cevabı kullanıcıya gösterilmez.
- Baş denetçi kritik mutabakat farkında AI çağrısını durdurur.
- `FINANCIAL_METHODOLOGY_APPROVED=true` yalnız uzman onayından sonra ayarlanır.

## Veri ve KVKK kapısı

- Çalışma alanı dışa aktarma ve aktif veri silme başarılıdır.
- Firestore TTL `retentionUntil` alanında etkinleştirilmiştir.
- Yedek saklama süresi aktif veri saklama politikasıyla uyumludur.
- NVIDIA/Groq/Gemini veri işleme ve yurtdışı aktarım şartları hukukçu tarafından incelenir.
- `KVKK_REVIEW_APPROVED=true` yalnız aydınlatma, saklama, imha ve veri işleyen
  sözleşmeleri onaylandıktan sonra ayarlanır.

## Operasyon kapısı

- Sentry 5xx alarmı kontrollü test hatasıyla doğrulanır.
- Firestore günlük yedeği oluşur.
- Ayrı test projesinde geri yükleme tatbikatı tamamlanır ve tarih
  `BACKUP_RESTORE_TESTED_AT` olarak kaydedilir.
- Alan adı üzerinde HTTPS giriş, Excel yükleme, analiz, AI CFO, rapor indirme,
  dışa aktarma, silme ve çıkış smoke testi tamamlanır.

## Pilot sonucu

Genel kullanıcı açılışı için kritik ve yüksek önem hata sıfır olmalı; en az üç
izinli/anonim pilot şirket uçtan uca akışı tamamlamalıdır. Başarısız her bulgu
yeni bir Kaizen maddesi olarak kayıt altına alınır, küçük değişiklikle düzeltilir
ve bütün kabul turu yeniden çalıştırılır.

## Ticari ve entegrasyon kapısı

- Ödeme sağlayıcısı, webhook doğrulaması, paket fiyatı ve sürümlü satış/iade koşulları birlikte hazır değilse canlı fiyat yayınlanmaz.
- 30 günlük iade uygunluğu sınır günleriyle test edilir; son karar yetkili insan onayındadır.
- Logo salt okunur bağlantısı gerçek lisanslı test hesabında çalıştırılır ve kaynak toplamlarıyla mutabakat raporu alınır.
- Mikro/Netsis hazır değilse kullanıcı arayüzünde yol haritası olarak kalır.

## ESG, TFRS ve müşteri kanıtı kapısı

- ESG ve TFRS hazırlık modülleri eksik veride uyum veya performans skoru üretmez.
- Uygulanabilir standart seçimi ve uzman onayı ayrı kayıtlardır; sistem onayı insan görüşü gibi sunmaz.
- ROI sonucu beklenen/gerçekleşen değer ve uygulama maliyetiyle yeniden hesaplanır.
- Anonim vaka, logo, yorum veya sonuç yalnız açık yayın izniyle dışarı çıkar.

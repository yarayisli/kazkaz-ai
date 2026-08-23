# KazKaz AI KVKK uyum paketi — hukuk incelemesi taslağı

Bu belge teknik hazırlık kaydıdır; hukuk görüşü veya “KVKK uyumludur” beyanı
değildir. `KVKK_REVIEW_APPROVED=true` yalnız yetkili hukuk incelemesi, metinlerin
yayını ve veri işleyen sözleşmelerinin tamamlanmasından sonra kullanılmalıdır.

## 1. Roller ve kapsam

- Veri sorumlusu: Canlı hizmeti sunacak KazKaz AI tüzel kişiliği — **ticari unvan,
  adres, MERSİS ve iletişim bilgileri doldurulacak.**
- Veri işleyenler: Firebase/Google Cloud, canlı barındırma sağlayıcısı, hata izleme,
  e-posta, ödeme ve seçilen AI sağlayıcıları — **sözleşme ve veri bölgesi bazında
  kesinleştirilecek.**
- İlgili kişiler: Şirket yöneticileri, finans çalışanları, davetli kullanıcılar ve
  destek talebi sahipleri.
- Veri sahibi şirket: Yüklenen mali kayıtların sahipliği kullanıcı şirkette kalır.

## 2. Veri envanteri

| Veri grubu | Amaç | Hukuki sebep adayı | Saklama | Bugünkü teknik durum |
|---|---|---|---|---|
| Kimlik ve oturum | Hesap güvenliği | Sözleşmenin kurulması/ifası | Hesap süresi + onaylı dönem | Firebase token doğrulaması, iptal kontrolü |
| Şirket üyeliği ve rol | Yetkilendirme | Sözleşmenin ifası, meşru menfaat | Üyelik + denetim süresi | Admin/CFO/analist/izleyici rolleri |
| Finansal çalışma alanı | Analiz ve raporlama | Sözleşmenin ifası | `DATA_RETENTION_DAYS` | Şirket altında backend-only kayıt |
| Rapor arşivi | Sürümlü rapor | Sözleşmenin ifası | `REPORT_RETENTION_DAYS` | Şirket izolasyonu ve yetki kontrolü |
| AI istemi ve yanıtı | Yönetici açıklaması | Sözleşmenin ifası | **Sağlayıcı sözleşmesine göre belirlenecek** | Finans motoru sonucu gönderilir; anahtarlar gizli |
| Geri bildirim | Destek ve iyileştirme | Meşru menfaat / iletişim izni | **Belirlenecek** | Şirket altında backend-only kayıt |
| Operasyon telemetrisi | Hız ve hata ölçümü | Meşru menfaat | Süreç içi 5.000 örnek | Kullanıcı, şirket, dosya adı ve finansal değer yok |

Hukukçu her satır için hukuki sebebi, zorunlu/isteğe bağlı alanı, yurtdışı aktarım
durumunu ve kesin saklama süresini onaylamalıdır.

## 3. İlgili kişi hakları iş akışı

1. Talep kimliği doğrulanır; e-posta tek başına yeterli kabul edilmez.
2. Şirket ve kullanıcı kapsamı belirlenir; başka tenant verisi aranmaz.
3. Erişim/dışa aktarma için çalışma alanı export ucu kullanılır.
4. Düzeltme talebi kaynak finans dosyasında ve yeni rapor sürümünde uygulanır.
5. Silme talebi aktif çalışma alanı, rapor, geri bildirim, yedek ve sağlayıcı
   kapsamlarıyla ayrı ayrı kayda alınır.
6. Hukuki saklama zorunluluğu varsa veri erişime kapatılır ve gerekçe bildirilir.
7. Yanıt tarihi, işlemi yapan yetkili ve sonuç denetim kaydına yazılır.

## 4. Yayından önce tamamlanacak metinler

- [ ] Veri sorumlusu bilgileri tamamlandı.
- [ ] Aydınlatma metni kayıt ve veri yükleme öncesinde gösteriliyor.
- [ ] Zorunlu sözleşme işlemleri ile isteğe bağlı iletişim izni ayrıldı.
- [ ] Çerez/analitik tercih ekranı gerçek kullanılan araçlarla eşleşiyor.
- [ ] Alt veri işleyen listesi, ülke ve amaçlarıyla yayınlandı.
- [ ] Yurtdışı aktarım mekanizması hukukçu tarafından onaylandı.
- [ ] Saklama ve imha süreleri Firestore TTL/yedek yaşam döngüsüyle eşleşiyor.
- [ ] İlgili kişi başvuru kanalı ve kimlik doğrulama prosedürü çalışıyor.
- [ ] Veri ihlali bildirim sorumluları ve süreleri onaylandı.
- [ ] Tarih, sürüm ve hukukçu onayı kaydedildi.

## 5. Ürün metni yayın kuralı

Hukuk onayından önce: **“KVKK teknik hazırlıkları sürüyor.”**

Hukuk onayı ve canlı doğrulama sonrasında dahi genel “KVKK sertifikalı” ifadesi
kullanılmaz. Kapsamı belirten ifade tercih edilir: **“KVKK yükümlülüklerini
destekleyen erişim, dışa aktarma ve silme kontrolleri uygulanmaktadır.”**

# Veri saklama ve imha politikası — onay taslağı

Bu taslak hukuk, güvenlik ve iş birimi tarafından süreleri onaylanmadan yürürlüğe
girmez.

## İlkeler

- Amaç için gereken en az veri tutulur.
- Tenant verisi başka şirketin kaydına taşınmaz.
- Aktif veri, rapor, log, yedek ve üçüncü taraf kopyaları ayrı değerlendirilir.
- Silme talebi geri döndürülemez işlem öncesi kimlik ve yetki doğrulaması ister.
- Yedeklerdeki silme, yaşam döngüsü sonunda gerçekleşir; bu gecikme kullanıcıya açıklanır.

## Teknik süreler

- Aktif finans çalışma alanı: `DATA_RETENTION_DAYS` — öneri 365 gün, hukuk onayı bekler.
- Rapor arşivi: `REPORT_RETENTION_DAYS` — öneri 365 gün, hukuk onayı bekler.
- Operasyon telemetrisi: en fazla `PERFORMANCE_WINDOW_SIZE` anonim ölçüm; kalıcı
  kullanıcı/şirket kimliği tutulmaz.
- Güvenlik denetim kayıtları: **süre belirlenecek.**
- Geri bildirim kayıtları: **süre belirlenecek.**
- Firestore export yedekleri: **bucket yaşam döngüsüyle belirlenecek.**
- AI sağlayıcısı kayıtları: **seçilen sağlayıcı sözleşmesiyle doğrulanacak.**

## İmha akışı

1. Yetkili kullanıcı talebi ve tenant kimliği doğrulanır.
2. Aktif çalışma alanı ve rapor arşivi uygulama servisleri üzerinden silinir.
3. İşlem, finansal içeriği tekrar etmeyen denetim kaydına yazılır.
4. Üçüncü taraf silme/kapatma işlemleri takip kaydına bağlanır.
5. Yedek yaşam döngüsü bitiş tarihi kullanıcı talebine eklenir.
6. Geri yükleme tatbikatında süresi dolmuş verinin yeniden aktifleşmediği kontrol edilir.

## Kanıtlar

- Firestore TTL ekran görüntüsü/çıktısı
- Bucket lifecycle yapılandırması
- Başarılı dışa aktarma ve silme testleri
- Ayrı projeye geri yükleme tatbikatı kaydı
- Onaylayan hukukçu ve güvenlik sorumlusu
- Politika sürümü ve yürürlük tarihi

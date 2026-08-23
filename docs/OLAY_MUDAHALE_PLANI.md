# Güvenlik ve hizmet olayı müdahale planı

## Seviyeler

- **SEV-1:** Şirketler arası veri görünmesi, aktif anahtar sızıntısı, geniş hizmet
  kesintisi veya finansal veri bütünlüğü kaybı.
- **SEV-2:** Tek tenant erişim sorunu, rapor bütünlüğü şüphesi, sürekli 5xx veya
  p95 gecikme eşiği aşımı.
- **SEV-3:** Sınırlı UI hatası, geçici sağlayıcı yavaşlığı veya düşük etkili uyarı.

## İlk müdahale

1. Request ID, zaman, ortam ve etkilenen işlev kaydedilir; finansal veri kopyalanmaz.
2. SEV-1’de ilgili özellik veya dağıtım güvenli biçimde durdurulur; erişim anahtarı
   şüphesinde anahtar hemen döndürülür.
3. Tenant kapsamı backend yolları ve denetim kayıtlarıyla doğrulanır.
4. Veri bütünlüğü şüphesinde yeni rapor/AI önerisi üretimi geçici olarak kapatılır.
5. Hukuk ve güvenlik sorumlusu kişisel veri ihlali değerlendirmesini başlatır.

## Hedefler — yönetim onayı bekler

- SEV-1 ilk yanıt: 15 dakika; durum güncellemesi: 30 dakika.
- SEV-2 ilk yanıt: 1 saat; durum güncellemesi: 2 saat.
- SEV-3 ilk yanıt: 1 iş günü.
- RPO/RTO: canlı mimari ve geri yükleme tatbikatından sonra kesinleştirilecek.

## Kapanış kanıtı

- Kök neden ve zaman çizelgesi
- Etkilenen tenant/veri kapsamı
- Alınan sınırlama ve kalıcı düzeltme
- Geri yükleme ve bütünlük testi
- Kullanıcı/hukuk bildirim kararı
- Tekrarı önleyen test veya kontrol
- Olayı kapatan yetkilinin adı ve tarih

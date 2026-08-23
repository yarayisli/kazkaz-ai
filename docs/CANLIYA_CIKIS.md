# KazKaz AI V1 canlıya çıkış kapısı

Bu liste tamamlanmadan ürün “genel kullanıma hazır”, “KVKK uyumlu”, “ISO 27001”
veya “Türkiye’de barındırılıyor” şeklinde tanıtılmaz. Teknik kontroller uygunluğu
destekler; hukukçu, mali müşavir/CFO ve güvenlik uzmanı onayının yerine geçmez.

## 1. Render ve alan adı

1. Render’da bu depodan Blueprint oluşturun; `render.yaml` tek Docker servisi kurar.
2. `sync: false` secret değerlerini Render panelinde tanımlayın.
3. İlk dağıtımdan sonra Render Custom Domains ekranına `supermantarik.com` ve
   `www.supermantarik.com` ekleyin; Render’ın verdiği DNS kayıtlarını alan adı
   sağlayıcısına girin.
4. `/api/health` 200, `/api/readiness` ise `durum: hazir` dönmeden pilot açmayın.
5. HTTPS üzerinden giriş, Excel yükleme, rapor indirme ve çıkış smoke testini yapın.

## 2. Firebase

- Email/Password ve Google giriş sağlayıcılarını bilinçli olarak etkinleştirin.
- Authorized Domains listesine iki canlı alan adını ekleyin.
- `firestore.rules` dosyasını canlı projeye dağıtın; Emulator Suite ile iki şirket
  arasında okuma/yazma izolasyonunu ayrıca çalıştırın.
- Servis hesabı JSON dosyasını depoya koymayın; Render secret olarak tek satır JSON kullanın.
- Google Sheets için Firebase’den ayrı servis hesabı kullanın ve yalnızca hedef
  belgeye Görüntüleyici erişimi verin.

## 3. Yedekleme ve geri yükleme

- Hukuk/KVKK onaylı aktif çalışma alanı süresini `DATA_RETENTION_DAYS` olarak tanımlayın.
- Firestore TTL politikasını `companies/*/workspaces/*` belgelerindeki `retentionUntil`
  alanı için etkinleştirin; TTL silmesinin gecikmeli olabileceğini kullanıcı metninde açıklayın.
- Ayrı, sürümlemeli bir Cloud Storage bucket oluşturup adını
  `FIRESTORE_BACKUP_BUCKET` olarak tanımlayın.
- Günlük zamanlanmış işte `gcloud firestore export gs://BUCKET/kazkaz-YYYY-MM-DD`
  çalıştırın; servis hesabına yalnız gerekli Firestore export ve bucket yazma rollerini verin.
- Ayda bir ayrı test projesine `gcloud firestore import gs://BUCKET/YEDEK` ile geri
  yükleme tatbikatı yapın. Tarih, süre, kayıt adedi ve sonucu denetim kaydına yazın.
- Yedek yaşam döngüsü ve silme süresi KVKK saklama politikasıyla aynı olmalıdır.

## 4. İzleme ve olay yönetimi

- Sentry projesi oluşturup `SENTRY_DSN` secretını tanımlayın; finansal veri ve token
  içeren request body’lerini olay kaydına eklemeyin.
- Render health alarmı, 5xx oranı, p95 gecikme ve Firebase hata oranı için uyarı kurun.
- Olay sorumlusu, bildirim kanalı, ilk yanıt hedefi ve kullanıcı bilgilendirme metni yazılı olsun.

## 5. Pilot kapısı

- Muhasebeci/CFO: FAVÖK, net kâr, nakit köprüsü, DSCR ve mizan eşleme golden dosyalarını onaylar.
- Güvenlik: tenant izolasyonu, silme/dışa aktarma, token iptali ve rate-limit testlerini onaylar.
- Hukuk/KVKK: aydınlatma metni, açık rıza gerektiren alanlar, veri işleyen sözleşmeleri,
  saklama/silme süreleri ve yurtdışı aktarım durumunu onaylar.
- En az 3 anonim pilot şirket; yükleme, analiz, rapor, AI CFO ve destek akışını tamamlar.
- Kritik hata sıfır, yüksek önem hata sıfır ve geri yükleme tatbikatı başarılı olmadan genel açılış yapılmaz.

## 6. Ticari paket ve iade kapısı

- Ödeme sağlayıcısı hesabı, canlı API anahtarı, webhook sırrı ve paket fiyatı tanımlanır.
- Mesafeli satış koşulları ile iade politikası hukuk tarafından sürümlü olarak onaylanır.
- Başarılı/başarısız ödeme, mükerrer webhook, paket yükseltme/düşürme ve 30. gün sınırındaki iade akışı test edilir.
- Bu kapı tamamlanmadan fiyat veya “30 gün iade garantisi” ana sayfada yayınlanmaz.

## 7. ERP entegrasyonu kapısı

- Logo Cloud ERP API/NetOpenX lisansı ve salt okunur müşteri test hesabı temin edilir.
- OAuth2 token yenileme, zaman aşımı, aynı kaynak alan adı kısıtı ve hata kayıtları doğrulanır.
- Aktarılan cari, fatura ve mizan kayıtları kaynak ERP toplamlarıyla mutabık olmadan “Logo entegrasyonu hazır” denmez.
- Mikro ve Netsis için ayrı sağlayıcı sözleşmesi ve test adaptörü tamamlanmadan bu adlar hazır entegrasyon olarak yayınlanmaz.

## 8. ESG ve TFRS hazırlık kapısı

- ESG ekranı yalnız veri kapsamını ölçer; performans skoru veya GRI/SASB uyum görüşü üretmez.
- TFRS ekranı yalnız uygulanabilir standart konularındaki belge eksiklerini gösterir; denetim görüşü üretmez.
- Gösterge kaynakları, dönem kapsamı, metodoloji sürümü ve yetkili uzman onayı kayıt altına alınır.
- Standart metinlerinin ticari üründe kullanımı için KGK/IFRS telif ve lisans koşulları ayrıca doğrulanır.

## 9. Kamuya açık kanıt kapısı

- Kullanıcı/ziyaretçi sayısı yalnız bot filtreli, tarih aralığı belli üretim ölçümünden yayınlanır.
- Analiz süresi en az 30 başarılı örneğin p50/p95 değerleriyle gösterilir.
- ROI veya tasarruf sonucu; beklenen etki, gerçekleşen etki, uygulama maliyeti, ölçüm dönemi ve müşteri onayı olmadan yayınlanmaz.
- Logo, yorum veya anonim vaka paylaşımı için sürümlü açık yayın izni saklanır; izin geri çekilirse içerik kaldırılır.

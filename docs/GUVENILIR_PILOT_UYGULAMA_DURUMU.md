# Güvenilir Pilot Uygulama Durumu — 11 Eylül 2026

Bu kayıt, `codex/guvenilir-pilot` dalında uygulanan yol haritası adımlarını ve doğrulama sınırlarını gösterir.

## Aşama 0 — Sürüm ve ortam eşleştirmesi

- İnceleme tabanı: `cbeabeebe2ea416a5880afce48da073bd866d1a8`.
- Kaynak dalın GitHub CI çalışması başarılıydı.
- Henüz bağlı bir canlı veya test adresi yoktur. Geçmiş alan adı varsayımı dağıtım
  yapılandırmasından kaldırıldı; ilk Render dağıtımının verdiği gerçek adres
  `CORS_ORIGINS` olarak tanımlanmadan canlı sürüm eşleştirmesi tamamlanmış sayılamaz.

## Aşama 1 — Oturum, yetki ve eşzamanlı veri güvenliği

- Kullanıcı veya şirket kimliği değiştiğinde React çalışma alanı tamamen yeniden kurulur; eski şirketin bellekteki verisi yeni oturuma taşınmaz.
- Geç gelen yükleme ve kayıt yanıtları yeni oturumun durumunu değiştiremez.
- Her kayıt zorunlu taban revizyonu ister. Çakışan kayıt `409` ile reddedilir ve kullanıcı en son sürümü yüklemeye yönlendirilir.
- Silme işlemi de revizyona bağlıdır. Eski ekran yeni veriyi silemez; silinen finans içeriğinin yerine yalnızca artan revizyon mezar taşı bırakılır.
- Şirketin güncel durumu güvenilir kaynaktan okunamazsa finans uçları `503` ile kapalı kalır; eski token erişim açamaz.
- Bekleyen claim işi geçmiş rolü geri veremez. Güncel üyelik/profil yoksa kuyruk işi iptal edilir; üye çıkarılırken bekleyen iş de silinir.
- Eski boolean rol claim'leri yeni tekil rol yazılırken temizlenir.

## Aşama 2 — Sessiz veri bozulmasını önleme

- `TL`, `Bin TL` ve `Milyon TL` başlıkları açıkça tanınır; açık ölçek TL'ye normalize edilir.
- Gelir ve gider ölçekleri karışıksa aktarım durdurulur.
- KDV dahil/hariç bazları karışıksa aktarım durdurulur; KDV oranı veya baz dönüşümü tahmin edilmez.
- `01/02/2026` gibi gün/ay açısından belirsiz tarihler görünür uyarı üretir.
- Ara/genel toplam satırları çift sayımı önlemek için reddedilir.
- Kimlikli mükerrer kayıtlar reddedilir; aynı görünen işlemler otomatik silinmeden kullanıcı kontrolüne sunulur.
- Reddedilen satır veya kesin finansal tutarsızlık varsa çalışma alanına aktarım kapatılır.
- Uyarılı dosyada kullanıcı ölçek, KDV, tarih ve mükerrer risklerini gördüğünü işaretlemeden analiz başlatılamaz.
- İndirilebilir KazKaz şablonu TL ve KDV bazını açıkça belirten başlıklar üretir.

## Aşama 3 — Kritik arayüz ve destek davranışları

- React birim/davranış test altyapısı CI kapısına eklendi.
- Oturum değişimi, geç yanıt, kayıt/silme çakışması ve yükleme öncesi kayıt senaryoları test edildi.
- Kesin veri hatasında aktarımın kapanması ve uyarıların kullanıcı onayı olmadan geçilememesi test edildi.
- Admin panelinde A şirketinin geç ayrıntı yanıtının B şirketini ezmediği test edildi.
- Destek talep numarası, çözüm yanıtı ve müşteri memnuniyeti akışı tarayıcı bileşeninde test edildi.

## Aşama 4 — Değişmez rapor arşivi

- Yeni PDF ve Excel raporları yalnız finansal girdilerle değil, kullanıcıya teslim edilen özgün dosya baytlarıyla arşivlenir.
- Her dosyanın SHA-256 bütünlük özeti ve boyutu kayıt altına alınır; indirme sırasında ikisi de doğrulanır. Değişmiş veya eksik dosya kullanıcıya sunulmaz.
- Depo yolu şirket ve rapor kapsamıyla doğrulanır; bozulmuş bir kayıt başka şirketin nesnesini okutamaz.
- Aynı depo nesnesinin üzerine yazmayı engelleyen oluşturma önkoşulu kullanılır.
- Rapor motoru sonradan değişse bile yeni arşiv kayıtları üretim anındaki özgün çıktıyı döndürür.
- Önceki sürümlerden kalan, özgün dosya içermeyen kayıtlar açıkça “Eski arşiv kaydı” olarak gösterilir ve uyumluluk için saklı girdiden yeniden üretilir.
- Dosya silinemediğinde Firestore kaydı korunur; böylece yetim ve görünmez finans dosyası oluşmaz.
- Canlı hazırlık kapısı hem Storage bucket yapılandırmasını hem de saklama süresiyle uyumlu yaşam döngüsü kuralının doğrulandığını arar.

## Aşama 5 — Yedekleme ve geri yükleme kanıtı

- Yedek betiği tamamlanmış Firestore export metadata dosyasını doğrular; komutun yalnızca başlamasını başarı saymaz.
- Sabit doğrulama belgesinin içeriği kanıt dosyasına yazılmaz; kaynakta SHA-256 parmak izi alınır.
- Geri yükleme yalnız açıkça ayrı ve silinebilir olduğu belirtilen test projesine yapılabilir; kaynak proje hedef olarak reddedilir.
- Import sonrasında aynı belgenin parmak izi yeniden hesaplanır. Kaynak ve hedef eşleşmeden tatbikat başarılı sayılmaz.
- Yedek süresi, yedek yaşı ve geri yükleme süresi makinece okunabilir kanıt dosyalarına yazılır.
- Ardışık iki başarılı yedek arasındaki gerçek süre RPO hedefiyle; geri yükleme süresi RTO hedefiyle karşılaştırılır.
- Yönetim hazırlık paneli 35 günden eski tatbikatı ve aşılmış RPO/RTO hedefini hazır saymaz.
- Betikler sahte `gcloud` ve parmak izi uçlarıyla uçtan uca çalıştırıldı. Bu yalnız akış doğrulamasıdır; gerçek bulut tatbikatı değildir.

## Doğrulama kanıtı

- API, yetkilendirme, veri kalite ve işletim kanıtı testleri: **264 geçti**.
- Kök finans motorları ve kullanım sayacı: **139 geçti**.
- React davranış testleri: **12 geçti**.
- Masaüstü/mobil Playwright kabul senaryoları: **6 geçti**.
- TypeScript tip kontrolü: geçti.
- Vite üretim derlemesi: geçti.
- npm bağımlılık taraması: **0 açık**.
- Python sözdizimi ve diff biçim kontrolü: geçti.
- Docker komutu bu bilgisayarda kurulu olmadığı için yerel imaj üretimi çalıştırılamadı; CI'daki Docker kapısı korunuyor.

## Aşama 6 — Pilot müşteri kanıtı

- Platform yöneticisi paneli aktif pilot şirket sayısını, 28 günü tamamlayanları,
  uçtan uca görev oranını, destek çözüm sürelerini, memnuniyeti, bildirilen hata
  oranını ve devam niyetini tek özette gösterir.
- Görev başarısı dosya doğrulama, çalışma alanı kaydı, finansal analiz ve değişmez
  rapor arşivi denetim kayıtlarından ölçülür.
- Müşteri tarafından bildirilen hata teknik 5xx oranından açıkça ayrılır; örnek
  sayısı olmayan oran gösterilmez.
- Pilotun son haftasında yalnız şirket admini veya CFO'su devam ve ücretli devam
  niyetini kaydedebilir.
- Yönetim özeti finansal tutar, dosya adı, destek mesajı veya kullanıcı kimliği
  taşımaz.
- Üç ila beş şirket, en az üç tamamlanmış 28 günlük dönem, üç tam yolculuk ve üç
  yönetici yanıtı oluşmadan sistem “asgari kanıt hazır” demez.

## Sıradaki işler

1. Güncel canlı/test adresini doğrula; aynı commit'i sağlık, oturum, askı, kayıt çakışması ve geri yükleme senaryolarıyla sınayarak Aşama 0'ı kapat.
2. Firebase Storage bucket yaşam döngüsünü `REPORT_RETENTION_DAYS` ile uyumlu kurup `REPORT_STORAGE_LIFECYCLE_CONFIGURED=true` ile doğrula.
3. Gerçek Google Cloud kimliğiyle iki ardışık yedeği ve ayrı test projesi geri yüklemesini çalıştır; üretilen RPO/RTO kanıtını canlı ayarlara kaydet.
4. Üç ila beş müşteriyle gerçek dört haftalık ücretli pilotu yürüt; paneldeki görev,
   destek, hata ve devam niyeti sonuçlarını ürün kararı için değerlendir.

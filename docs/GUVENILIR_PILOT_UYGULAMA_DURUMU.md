# Güvenilir Pilot Uygulama Durumu — 11 Eylül 2026

Bu kayıt, `codex/guvenilir-pilot` dalında uygulanan yol haritası adımlarını ve doğrulama sınırlarını gösterir.

## Aşama 0 — Sürüm ve ortam eşleştirmesi

- İnceleme tabanı: `cbeabeebe2ea416a5880afce48da073bd866d1a8`.
- Kaynak dalın GitHub CI çalışması başarılıydı.
- Yapılandırmada görülen `https://supermantarik.com/api/health` adresi bu çalışma ortamında DNS üzerinden çözülemedi. Güncel canlı/test adresi bilinmeden canlı sürüm eşleştirmesi ve geri yükleme tatbikatı tamamlanmış sayılamaz.

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

## Doğrulama kanıtı

- API, yetkilendirme ve veri kalite testleri: **248 geçti**.
- Kök finans motorları ve kullanım sayacı: **139 geçti**.
- React davranış testleri: **11 geçti**.
- Masaüstü/mobil Playwright kabul senaryoları: **6 geçti**.
- TypeScript tip kontrolü: geçti.
- Vite üretim derlemesi: geçti.
- npm bağımlılık taraması: **0 açık**.
- Python sözdizimi ve diff biçim kontrolü: geçti.
- Docker komutu bu bilgisayarda kurulu olmadığı için yerel imaj üretimi çalıştırılamadı; CI'daki Docker kapısı korunuyor.

## Sıradaki işler

1. Güncel canlı/test adresini doğrula; aynı commit'i sağlık, oturum, askı, kayıt çakışması ve geri yükleme senaryolarıyla sınayarak Aşama 0'ı kapat.
2. Firebase Storage bucket yaşam döngüsünü `REPORT_RETENTION_DAYS` ile uyumlu kurup `REPORT_STORAGE_LIFECYCLE_CONFIGURED=true` ile doğrula.
3. Yedekleme ve geri yükleme tatbikatını ölç; RPO/RTO kanıtını kaydet.
4. Üç ila beş müşteriyle dört haftalık ücretli pilotta görev tamamlama, destek çözüm süresi, hata oranı ve devam niyetini ölç.

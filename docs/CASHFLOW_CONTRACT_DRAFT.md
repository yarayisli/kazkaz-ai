# Cashflow Safety Pack — hesap sözleşmesi taslağı

Tarih: 8 Ekim 2026. Kaynak: `main/e6878ca` ve `CURRENT_REPO_ASSESSMENT.md`.

**Durum: Owner incelemesi bekleyen taslak.** Bu belge golden/invariant
beklenen sonuçlarını onaylamaz ve korumalı test/politika dosyası oluşturmaz.
Mevcut hesapların hassasiyeti veya çıktısı bu ilk PR'da değiştirilmez.

## 1. Bu PR'ın tamamladığı ilk dilim

- Aylık `CashFlowInput`, giriş/çıkış, açılış ve likidite tutarlarında NaN ve
  ±Infinity gibi sonlu olmayan değerleri açık `ValueError` ile reddeder.
- Finansal Pydantic modelleri `allow_inf_nan=False` kullanır. İstek
  doğrulaması geçersiz değerleri hesap servisine ulaşmadan durdurur.
- JSON içindeki `1e400`, string `NaN`/`Infinity` ve iç içe haftalık tutar
  girdileri yeni regresyon testlerinde kapsanır.
- Hata yanıtı içinde sonlu olmayan girdi JSON'a yazılamadığı için 500
  oluşmasını önleyen handler eklenir. Gerçek FastAPI route'una gönderilen
  geçersiz girdiler 422 döner ve finans hesap servisi çağrılmaz.
- Geçerli istek şekli, negatif net kâr, opsiyonel `None` alanları ve aylık
  motorun mevcut iade/negatif bakiye davranışı korunur.
- Yeni dependency eklenmez; mevcut test, golden ve invariant dosyaları
  değiştirilmez. Yeni dosya girdi reddi/regresyon testlerini içerir.

**Bu dilim bütün Safety Pack değildir.** Sonlu girdilerin matematiksel
taşma üretmesi, işlem sırasına bağlı float toplamı, derived net/bakiye
mutabakatı ve frontend'deki ikinci hesap yolu sonraki dilimlerde ele alınır.
`model_construct`/`model_copy(update=...)` gibi doğrulamayı atlayan dahili
Pydantic kullanımları bu PR ile doğrulamalı hale getirilmez.

## 2. Kanonik nakit yolları

1. Aylık gerçekleşmiş nakit: açılış + tahsilatlar − ödemeler.
2. 13 haftalık plan: her haftanın açılışı önceki haftanın kapanışıdır.
   Rapor penceresi açılışı ile tüm veri kümesinin açılışı ayrılır.
3. Finansal tablo köprüsü: açılış + CFO + CFI + CFF = kapanış.
4. Ekran/rapor/export aynı kanonik backend sonucunu göstermelidir.

Gelir/gider, tahsilat/ödeme olduğu doğrulanmadıkça **gerçek nakit** olarak
etiketlenmemelidir. Mevcut `from_financial_engine` varsayımını kaldırmak
veya yeniden etiketlemek ayrı davranış değişikliğidir; bu ilk dilime dahil
değildir.

## 3. Owner'a önerilen hassasiyet kararı

- Deterministik muhasebe toplamlarında ondalık aritmetik kullanılsın.
  Hesap yolunda binary float'a erken dönüşüm yapılmasın.
- Para birimi ve tutarın birimi açık olsun; farklı para birimleri kur
  tarihi/kaynak olmadan birbirine eklenmesin.
- Kuruş yuvarlaması, import sırasında satır başına mı yoksa toplam
  sonuçta mı uygulanacağı belirtilerek onaylansın.
- Öneri: ara toplamların hassasiyetini koruyup son parasal çıktıyı ilgili
  para biriminin ölçeğinde `ROUND_HALF_EVEN` ile üretmek. Bu bir taslaktır.
  Örneğin `2.675` için mevcut float ve ondalık yuvarlama aynı sonucu
  vermeyebilir; değişiklik sessiz refactor gibi sunulmamalıdır.
- API'de ondalık string/cent-integer çıktısına geçiş gerekiyorsa mevcut
  `number` istemcileri için sürümlü geçiş ve compatibility planı oluşturulsun.
- Kabul edilen azami tutar, ondalık basamak ve işlem sayısı tanımlansın.
  Yeni limitler bu PR'da keyfi olarak konulmadı.

## 4. Owner'a önerilen veri davranışı

- En az bir dönem ama sıfır hareket varsa açılış korunmalı.
- Hiç dönem yoksa mevcut aylık motorun açıklayıcı hata sözleşmesi
  korunmalı; boş veri gerçek sıfır nakit gibi sunulmamalı.
- API türetilmiş `net_nakit`/`kumulatif_nakit` alanı alıyorsa temel
  hareketlerle karşılaştırmalı veya kanonik hesapla yeniden üretmeli.
  Hangi davranışın uygulanacağı ve tolerans owner tarafından onaylanmalı.
- Tekrarlı haftalarda backend'in ilk satırı seçmesiyle frontend'in tüm
  satırları toplaması uzlaştırılmalı. Öneri: geçersiz planı açıkça işaretleyip
  onaysız kesin sonuç üretmemek; otomatik birleştirme politikası varsayılmamalı.
- Haftalık tarih boşlukları bilinmeyen hareketi sıfır olarak doldurmamalı.
- İadeler/ters kayıtlar için negatif tutarların hangi yolda kabul edildiği
  açıkça tanımlanmalı; API ve kök dataclass bugün aynı işaret kuralında değil.

## 5. Sonraki paketlerin onaylı kabul örnekleri

Bu örnekler owner incelemesi için öneridir; bir golden fixture değildir:

- Açılış 100, giriş 1000, çıkış 1000 → kapanış 100.
- Açılış 100, sıfır hareket → kapanış 100.
- `100.10 + 200.20` → `300.30`, onaylı parasal temsil ile.
- Aynı işlemlerin farklı sırası toplam kapanışı değiştirmez. Tarihe bağlı
  ara bakiyelerin aynı olması beklenmez.
- NaN/±Infinity/taşan işlem sonucu hesaplanmış finansal değer gibi dönmez.
- Aynı girdi tekrar çalıştırıldığında aynı sonucu verir; caller verisi
  yerinde değiştirilmez.
- 13 haftalık pencere açılışı, önceki hareketler ve ekran/rapor sonucu
  aynı kaynak üzerinde mutabıktır.

Owner bu sözleşmeyi ve bağımsız beklenen sonuçları onayladıktan sonra
korumalı golden/invariant katmanı oluşturulmalıdır. Mevcut assertion
gevşetilmez, başarısız test silinmez veya skip ile gizlenmez.

## 6. Sonraki iş sırası

1. Owner hesap sözleşmesi ve golden/invariant beklenen çıktıları.
2. Aylık + haftalık + nakit köprüsü için ondalık hesap ve taşma koruması.
3. Backend/frontend/rapor mutabakatı ve derived alan doğrulaması.
4. Aynı veri üzerinde eski/yeni sonuç, fark ve süre karşılaştırması.
5. Owner review ve CI sonrası merge; doğrudan production değişikliği yapılmaz.

Risk: Finansal girdi kabulü değiştiği için bu PR **HIGH** olarak owner
review'a sunulur. Geçersiz verinin daha önce hesap yoluna alınması, yeni
reddi bir breaking davranış değişikliği olarak görünür kılmayı gerektirir.

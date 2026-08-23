# KazKaz AI

Türkiye'deki KOBİ'ler için finansal analiz ve AI CFO karar destek platformu.

V1 iki katmandan oluşur:

- `web/`: React, TypeScript ve Vite kullanıcı arayüzü
- `api/`: FastAPI güvenlik/API katmanı ve mevcut Python finans motorları

Streamlit uygulaması geçiş sürecinde `app.py` üzerinden çalışmaya devam eder.

## V1'i yerel çalıştırma

Backend:

```bash
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
KAZKAZ_AUTH_DISABLED=true APP_ENV=development uvicorn api.main:uygulama --reload --port 8000
```

Frontend:

```bash
cd web
npm install
cp .env.example .env
npm run dev
```

React geliştirme sunucusu `/api` isteklerini `http://127.0.0.1:8000` adresine
yönlendirir.

## Kontroller

```bash
.venv/bin/python -m unittest test_engines api.tests.test_services api.tests.test_api api.tests.test_ai_orchestrator api.tests.test_cfo_agent_v1 api.tests.test_advanced_agents api.tests.test_authz -v
cd web && npm run lint && npm run build
```

## Güvenlik

Korumalı API uçları Firebase ID token içindeki güvenilir `company_id` ve rol
claim'lerini ister. `KAZKAZ_AUTH_DISABLED=true` yalnızca yerel geliştirme içindir
ve `APP_ENV=production` ortamında etkisizdir. Firestore kuralları finans kayıtlarını
`companies/{companyId}` altında şirket üyeliği ve role göre izole eder. Yeni hesap
varsayılan olarak `member` açılır; CFO/admin ataması yalnızca güvenilir backend ile
yapılmalıdır.

API varsayılan olarak 5 MB istek gövdesi ve kimlik/IP başına dakikada 120 istek
sınırı uygular. `MAX_REQUEST_BYTES` ve `API_RATE_LIMIT_PER_MINUTE` ortam
değişkenleriyle değiştirilebilir. Canlıda bunlara ek olarak ters proxy/WAF üzerinde
gövde boyutu, hız, eşzamanlılık ve zaman aşımı sınırları tanımlanmalıdır.

## AI CFO mimarisi

V1'de dil modeli finansal hesaplama yapmaz. Hesaplamalar deterministik finans
motorundan gelir; AI yalnızca doğrulanmış metrikleri yönetici dilinde açıklar.

- `veri_kalitesi_ajani`: Eksik ve çelişkili girdileri belirler; yetersiz veride AI çağrısını engeller.
- `finansal_denetim_ajani`: Brüt kâr, marj, likidite ve işletme sermayesini hesaplar.
- `ai_anlatim_ajani`: Doğrulanmış çıktıyı açıklar; yeni finansal değer üretmemesi istenir.
- `insan_onayi_koruyucusu`: Ödeme, kredi, yatırım ve muhasebe aksiyonlarını otomatik çalıştırmaz.

Sağlayıcılar paralel kullanılmaz. Varsayılan sıra NVIDIA NIM → Groq → Gemini'dir;
sonraki sağlayıcı yalnızca öncekiler cevap veremezse denenir. NVIDIA tarafında
varsayılan model düşük gecikmeli V1 profili için `openai/gpt-oss-20b` ve resmi OpenAI uyumlu uç noktadır:

```bash
AI_PROVIDER_ORDER=nvidia,groq,gemini
NVIDIA_API_KEY=
NVIDIA_MODEL=openai/gpt-oss-20b
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
GROQ_API_KEY=
GEMINI_API_KEY=
```

Hiçbir anahtar yoksa veya veri yetersizse CFO sohbeti kurallı finans motoruyla
çalışmaya devam eder. Hazırlık durumu, anahtarları açığa çıkarmayan korumalı
`GET /api/v1/ai/durum` ucundan görülebilir.

Eski CFO araçları V1'e doğrudan değil, güvenli adaptör üzerinden bağlanır:

- `POST /api/v1/cfo/ajan-analizi`: Finans, nakit, borç, yatırım hazırlığı ve rapor araçlarını çalıştırır.
- Kaynaksız yatırım tutarı veya ROI üretmez.
- Faiz bilinmiyorsa varsayılan faiz kullanmaz.
- DSCR, operasyonel nakit ve gerçek borç servisi olmadan hesaplanmaz.
- Metodoloji ve aksiyonlar muhasebeci/CFO veya yetkili yönetici onayı beklediğini açıkça gösterir.

## Gelişmiş finans ajanları

`POST /api/v1/cfo/gelismis-ajanlar` aşağıdaki deterministik kontrolleri tek veri
sözleşmesiyle çalıştırır:

- Mizan eşleme, borç/alacak denkliği ve bilanço eşitliği
- 13 haftalık nakit tahmini, minimum nakit eşiği ve ilk açık tarihi
- Fatura bazlı açık alacak, yaşlandırma ve müşteri yoğunlaşması
- Anapara/faiz ayrımlı borç servisi, para birimi kontrolü ve doğrulanabilir DSCR
- Aylık bütçe/gerçekleşen, yıl sonu tahmini ve geçmiş tahmin hatası
- Veri anomalileri ile SHA-256 tabanlı denetim izi

Arayüzde **AI CFO → Gelişmiş ajanlar → Ajan verisi yükle** yoluyla JSON veri
dosyası yüklenebilir. Başlangıç şablonu
`web/public/ornek-gelismis-ajan-verisi.json` dosyasındadır. Bir ajan için zorunlu
alanlar eksikse sistem sonuç uydurmaz; `veri_bekliyor` durumuyla eksikleri döndürür.
Doğrulanan haftalık nakit, borç servisi, açık fatura ve bütçe satırları aynı
oturumdaki Nakit & Borç, Müşteri ve Bütçe ekranlarına da aktarılır. Kullanıcı yalnız
finansal özet girerse bağımlı örnek tablolar temizlenir; eksik geçmiş veri yapay
olarak üretilmez.

## Sürümlü kurumsal finans metrikleri

`POST /api/v1/finans/denetim` temel metriklere ek olarak kaynak gösterilebilir
bir `metrik_kaydi` döndürür. Her kayıtta değer, birim, formül kimliği, formül
sürümü, kullanılan girdiler, kaynak alanlar, güven seviyesi ve eksik alanlar
bulunur. İlk paket şunları kapsar:

- Özel imalat şirketleri için Altman Z'
- Üç aşamalı DuPont ROE
- NOPAT tabanlı ROIC
- Operasyonel nakit akışı eksi CapEx ile serbest nakit akışı
- DSO + DIO - DPO ile tam nakit dönüşüm döngüsü
- Müşteri cirosu Herfindahl-Hirschman yoğunlaşma endeksi

Metrik için gereken bir alan yoksa API sayı tahmin etmez; `eksik_veri` durumu ve
gereken alanları döndürür. Excel şablonundaki `Finansal_Gorunum` sayfası bu
metrikler için dönen/toplam varlık, toplam yükümlülük, dağıtılmamış kâr,
operasyonel nakit akışı, dönem gün sayısı ve etkin vergi oranı alanlarını içerir.

## Ortak finansal tablolar ve mutabakat

Gelişmiş ajan API'sindeki `finansal_tablo_mutabakat_ajani`, eşlenmiş mizandan her
dönem için gelir tablosu ve bilanço üretir. Borç/alacak mizan eşitliğini, aktif =
yükümlülük + özkaynak denklemini, hesaplanan dönem kârını ve son dönemin
`Finansal_Gorunum` değerleriyle mutabakatını ayrı ayrı raporlar. Kapanmamış mizan
yüklenirse hesaplanan net kâr yalnızca ayrı bir dönem kârı hesabı bulunmadığında
özkaynağa eklenir; mükerrer kâr yazılmaz.

Excel şablonu dönem başı nakit, operasyonel nakit akışı (CFO), yatırım nakit
akışı (CFI) ve finansman nakit akışı (CFF) alanlarını da içerir. Bu dört kalem
tamamlanmadan dönem sonu nakit için varsayım üretilmez. Formüller ve sonuçlar
`2026.08-v1` sürüm etiketiyle döndürülür.

## Pilot ve üretim sınırı

React ana sayfası ürünü **pilot sürüm** olarak tanımlar. ISO 27001, KVKK uyumu,
barındırma bölgesi, kullanıcı sayısı ve iade garantisi ancak belge ve iş süreçleri
tamamlandıktan sonra ürün iddiası olarak kullanılabilir. `landing/` altındaki segment
ve tasarım referansları `noindex` işaretlidir ve aktif ürün taahhüdü değildir.

Üretimde şirket oluşturma, üyelik ve rol claim'leri güvenilir Admin SDK/backend
akışıyla atanmalıdır. İstemci yeni kullanıcıyı yalnızca `member` olarak oluşturur;
şirketi olmayan veya rol atanmamış hesaplar finans API uçlarına erişemez.

## V1'e eklenen ürünleşme katmanları

- Şirket oluşturma, Admin rolü, 14 günlük deneme planı ve şirket kapsamlı kalıcı çalışma alanı
- Sunucuda yeniden hesaplanan PDF/Excel yönetici raporları
- Ayrı servis hesabıyla salt-okunur Google Sheets doğrulaması
- Kaynak ve efektif tarih kaydı içeren tarihsel TCMB döviz alış kuru
- AI CFO aksiyonlarının metrik/formül dayanaklı insan onay kuyruğu
- Canlı ortamda sunucu tarafında çalışan Free/Trial/Pro/Uzman özellik kapıları
- Şirket kapsamlı geri bildirim, global hata kurtarma ekranı ve güvenli HTTP başlıkları
- Tek servis Docker/Render dağıtımı ve gizli değer göstermeyen `/api/readiness` kontrolü

Canlıya çıkış, DNS, Firebase, Sentry, yedekleme, KVKK ve pilot onay adımları
[`docs/CANLIYA_CIKIS.md`](docs/CANLIYA_CIKIS.md) dosyasında tutulur. Bu adımlar
harici hesap ve uzman onayı gerektirdiği için yalnızca kodun bulunması tamamlandıkları
anlamına gelmez.

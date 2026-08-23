import React, { useEffect, useRef, useState } from 'react';
import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  Bot,
  CalendarClock,
  Calculator,
  Check,
  CheckCircle2,
  ChevronDown,
  ClipboardCheck,
  Database,
  Eye,
  FileCheck2,
  FileSpreadsheet,
  Gauge,
  HandCoins,
  Landmark,
  Layers3,
  LineChart,
  LockKeyhole,
  ReceiptText,
  ScanLine,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  TimerReset,
  TrendingUp,
  Upload,
  UsersRound,
  WalletCards,
  Workflow,
} from 'lucide-react';
import { KamuyaAcikPerformans, kamuyaAcikPerformansiGetir } from '../lib/api';

interface LandingPageProps {
  onNavigateTab: (tabId: string) => void;
  onOpenAuth: () => void;
  onSelectDemo: (demoId: string) => Promise<void> | void;
}

const sectors = ['E-ticaret', 'Üretim', 'Hizmet', 'Yazılım', 'Perakende'];

const sectorMessages: Record<string, { title: string; signal: string; detail: string }> = {
  'E-ticaret': {
    title: 'Stok, tahsilat ve marj baskısını aynı anda görün.',
    signal: 'Stok ve nakit döngüsü',
    detail: 'Satış büyürken stok ve tahsilatın nakit üzerindeki etkisini birlikte inceleyin.',
  },
  Üretim: {
    title: 'Maliyet değişiminin kârlılığa etkisini açıklayın.',
    signal: 'Brüt kâr ve işletme sermayesi',
    detail: 'SMM, stok ve kısa vadeli borcun karar sırasındaki yerini görün.',
  },
  Hizmet: {
    title: 'Proje kârlılığı ile gerçek nakdi birbirinden ayırın.',
    signal: 'Marj ve tahsilat görünümü',
    detail: 'Kârlı görünen dönemde tahsilat ve ödeme yükünün yarattığı farkı izleyin.',
  },
  Yazılım: {
    title: 'Büyüme hızını nakit dayanıklılığıyla birlikte değerlendirin.',
    signal: 'Runway ve faaliyet giderleri',
    detail: 'Gelir, gider ve nakit eğilimini aynı finansal bağlam içinde açıklayın.',
  },
  Perakende: {
    title: 'Ciro artışının kasaya ne kadar yansıdığını görün.',
    signal: 'Marj, stok ve ödeme dengesi',
    detail: 'Satış, maliyet ve kısa vadeli yükümlülükleri tek karar görünümünde birleştirin.',
  },
};

const analysisAreas = [
  {
    icon: WalletCards,
    label: 'Nakit dayanıklılığı',
    value: '13 haftalık görünüm',
    description: 'Minimum nakit eşiği, yaklaşan ödeme yükü ve açık tarihini birlikte izleyin.',
    tone: 'emerald',
  },
  {
    icon: Calculator,
    label: 'Finansal doğruluk',
    value: 'Kaynak metrik görünür',
    description: 'Net kâr, FAVÖK ve nakit akışını veri yeterliliğine göre birbirinden ayırın.',
    tone: 'violet',
  },
  {
    icon: BarChart3,
    label: 'Karar sırası',
    value: 'Risk → etki → aksiyon',
    description: 'Rapor kalabalığı yerine önce incelenmesi gereken finansal sinyali görün.',
    tone: 'amber',
  },
];

const agentFlow = [
  {
    icon: Database,
    step: '01',
    title: 'Veri kalitesi ajanı',
    description: 'Eksik ve çelişkili alanları belirler; yetersiz veride kesin öneriyi durdurur.',
  },
  {
    icon: Calculator,
    step: '02',
    title: 'Finans motoru',
    description: 'Metrikleri yapay zekâdan bağımsız, test edilebilir kurallarla hesaplar.',
  },
  {
    icon: Workflow,
    step: '03',
    title: 'Kontrollü CFO araçları',
    description: 'Nakit, borç, yatırım hazırlığı ve rapor araçlarını kanıtlarıyla çalıştırır.',
  },
  {
    icon: Bot,
    step: '04',
    title: 'AI açıklama katmanı',
    description: 'Doğrulanmış sonucu yönetici dilinde açıklar; yeni finansal değer üretmez.',
  },
];

const trustItems = [
  {
    icon: ShieldCheck,
    title: 'Hesaplama AI’dan bağımsız',
    text: 'Dil modeli değişse bile finans motorunun sonucu aynı kalır.',
  },
  {
    icon: Eye,
    title: 'Kaynak ve güven seviyesi görünür',
    text: 'Yanıtta kullanılan sağlayıcı, veri kalitesi ve yedek geçişi kullanıcıya gösterilir.',
  },
  {
    icon: LockKeyhole,
    title: 'Aksiyonlar insan onayında',
    text: 'Ödeme, kredi, yatırım ve muhasebe kaydı otomatik olarak başlatılmaz.',
  },
];

type ClaimProgramStatus = 'technical' | 'verification' | 'planned';

const claimProgramStatuses: Record<ClaimProgramStatus, { label: string; className: string }> = {
  technical: {
    label: 'Teknik temel var',
    className: 'border-sky-200 bg-sky-50 text-sky-800',
  },
  verification: {
    label: 'Doğrulama gerekiyor',
    className: 'border-amber-200 bg-amber-50 text-amber-800',
  },
  planned: {
    label: 'Ürün yol haritası',
    className: 'border-slate-200 bg-slate-100 text-slate-700',
  },
};

const claimPrograms: Array<{
  icon: React.ElementType;
  title: string;
  promise: string;
  status: ClaimProgramStatus;
  current: string;
  proof: string;
}> = [
  {
    icon: UsersRound,
    title: 'Gerçek kullanıcı ve canlı kullanım kanıtı',
    promise: 'Kullanıcı, ziyaretçi ve analiz sayıları yalnız doğrulanmış üretim telemetrisinden yayınlanacak.',
    status: 'planned',
    current: 'Pilot kullanıcı kabulü ve anonim ölçüm politikası hazırlanacak.',
    proof: 'Onaylı analitik kaydı, bot filtresi, tarih aralığı ve açık hesaplama yöntemi.',
  },
  {
    icon: TimerReset,
    title: 'Ölçülmüş analiz süresi',
    promise: '“30 saniyede analiz” yerine dosya boyutu ve veri kapsamına göre ölçülmüş süre aralığı gösterilecek.',
    status: 'technical',
    current: 'Analiz akışı çalışıyor; üretim performans testi ve yüzdelik süre ölçümü eksik.',
    proof: 'p50/p95 süreleri, örnek dosya boyutları ve tekrarlanabilir performans testi.',
  },
  {
    icon: ShieldCheck,
    title: 'ISO 27001 programı',
    promise: 'Sertifika alınmadan ISO 27001 sertifikalı ifadesi kullanılmayacak; hazırlık programı görünür olacak.',
    status: 'technical',
    current: 'Rol yönetimi, denetim izi, olay müdahale planı ve kontrol matrisi teknik hazırlık olarak bulunuyor.',
    proof: 'Belgelendirme kuruluşu, kapsam, geçerli sertifika numarası ve doğrulama bağlantısı.',
  },
  {
    icon: FileCheck2,
    title: 'KVKK uyum programı',
    promise: 'Teknik gizlilik kontrolleri ile hukuki uyum beyanı birbirinden ayrılacak.',
    status: 'verification',
    current: 'Şirket izolasyonu, rol kontrolü, dışa aktarma/silme, saklama-imha ve KVKK çalışma taslakları mevcut.',
    proof: 'Veri envanteri, aydınlatma metni, saklama-imha politikası ve hukuk onayı.',
  },
  {
    icon: Landmark,
    title: 'Türkiye’de veri barındırma',
    promise: 'Canlı veri bölgesi seçilince sağlayıcı ve kapsam açıkça belirtilecek.',
    status: 'planned',
    current: 'Yerel geliştirme ortamı üretim barındırma kanıtı sayılmaz.',
    proof: 'Bulut sözleşmesi, veri merkezi bölgesi ve yedeklerin bulunduğu ülke kaydı.',
  },
  {
    icon: LockKeyhole,
    title: 'HTTPS ve aktarım güvenliği',
    promise: 'Pazarlama amaçlı “256-bit SSL” yerine doğrulanabilir TLS yapılandırması ve test tarihi yayınlanacak.',
    status: 'verification',
    current: 'Yerel ortam HTTP kullanıyor; canlı alan adı testi dağıtımdan sonra yapılmalı.',
    proof: 'TLS sürümü, sertifika zinciri, HSTS ve bağımsız HTTPS güvenlik testi.',
  },
  {
    icon: ReceiptText,
    title: '30 gün iade güvencesi',
    promise: 'İade taahhüdü paket, ödeme sağlayıcısı ve koşulları kesinleştiğinde açık sözleşmeyle sunulacak.',
    status: 'technical',
    current: '30 günlük uygunluk hesabı ve kanıt kapısı hazır; canlı ödeme sağlayıcısı ve sözleşme onayı henüz yok.',
    proof: 'Mesafeli satış koşulları, istisnalar, başvuru kanalı ve gerçek iade iş akışı.',
  },
  {
    icon: Activity,
    title: 'GRI/SASB ESG çalışma alanı',
    promise: 'ESG ekranı yalnız doğrulanmış veri sözlüğü ve metodoloji tamamlandığında ürün özelliği olacak.',
    status: 'technical',
    current: 'ESG veri hazırlık motoru ve paneli aktif; performans skoru veya GRI/SASB uyum görüşü üretmiyor.',
    proof: 'Gösterge veri sözlüğü, kaynak kayıtları, kapsam sınırı ve uzman metodoloji onayı.',
  },
  {
    icon: ClipboardCheck,
    title: 'IFRS/TFRS hazırlık kontrolü',
    promise: 'Tam uyum görüşü vermek yerine standart bazlı hazırlık ve eksik veri kontrolü geliştirilecek.',
    status: 'technical',
    current: 'Uygulanabilir TFRS başlıkları, belge eksikleri ve muhasebe uzmanı onayı ayrı olarak denetleniyor.',
    proof: 'Standart sürümü, muhasebe politikaları, mutabakat testleri ve yetkili uzman onayı.',
  },
  {
    icon: TrendingUp,
    title: 'ROI ve tasarruf metodolojisi',
    promise: 'Her ROI sonucu girdileri, varsayımları, senaryosu ve güven aralığıyla gösterilecek.',
    status: 'technical',
    current: 'Beklenen/gerçekleşen etki, uygulama maliyeti, net etki, gerçek ROI ve yayın izni ayrı kaydediliyor.',
    proof: 'Formül sürümü, beklenen-gerçekleşen karşılaştırması ve müşteri tarafından onaylı sonuç.',
  },
  {
    icon: Workflow,
    title: 'Logo, Mikro ve Netsis entegrasyonları',
    promise: 'Entegrasyon adı ancak gerçek bağlantı, hata yönetimi ve veri mutabakatı tamamlanınca “hazır” olacak.',
    status: 'technical',
    current: 'Logo için salt okunur OAuth2 bağlantı katmanı ve hazırlık kontrolü var; gerçek müşteri lisansı/anahtarıyla doğrulama bekliyor. Mikro ve Netsis yol haritasında.',
    proof: 'Sağlayıcı erişimi, örnek şirket testi, yeniden deneme, kayıt eşleme ve mutabakat raporu.',
  },
  {
    icon: Eye,
    title: 'Müşteri logoları, yorumlar ve vaka sonuçları',
    promise: 'Sosyal kanıt yalnız açık müşteri izni ve doğrulanabilir sonuçla yayınlanacak.',
    status: 'technical',
    current: 'Kurgusal örnekler etiketli; anonim vaka yayını için kullanıcı, zaman ve sürüm kayıtlı açık izin akışı hazır.',
    proof: 'Yazılı yayın izni, ölçüm başlangıç-bitiş dönemi ve sonucu onaylayan müşteri kaydı.',
  },
];

const heroInsights = [
  {
    id: 'nakit', label: 'Nakit', eyebrow: '13 haftalık görünüm',
    title: 'Tahsilat ile kısa vadeli ödeme yükünü birlikte doğrulayın.',
    metric: '₺1,24M', metricLabel: 'örnek dönem sonu nakit', progress: 72,
    note: 'Minimum eşik girildiğinde açık tarihi hesaplanır.', tone: 'emerald',
  },
  {
    id: 'kar', label: 'Kârlılık', eyebrow: 'Mizan mutabakatı',
    title: 'Net kâr, FAVÖK ve nakit akışının neden farklı olduğunu görün.',
    metric: '%23,0', metricLabel: 'örnek net kâr marjı', progress: 84,
    note: 'Formül, kaynak alanlar ve güven seviyesi görünür.', tone: 'violet',
  },
  {
    id: 'risk', label: 'Risk', eyebrow: 'Kontrollü ajanlar',
    title: 'Alacak, borç ve bütçe sinyallerini tek karar sırasına alın.',
    metric: '7 ajan', metricLabel: 'deterministik kontrol', progress: 91,
    note: 'Aksiyonlar uygulanmaz; yetkili insan onayına bırakılır.', tone: 'amber',
  },
];

const productModules = [
  { icon: Gauge, title: 'Finansal sağlık', text: 'Kârlılık, likidite, borçluluk ve çalışma sermayesini açıklanabilir metriklerle izleyin.', tag: 'Sürümlü formüller' },
  { icon: FileCheck2, title: 'Mizan ve tablolar', text: 'Mizandan gelir tablosu ve bilanço üretin; dönem kârı ile bilanço eşitliğini uzlaştırın.', tag: 'Mutabakat' },
  { icon: CalendarClock, title: '13 haftalık nakit', text: 'Tahsilat, ödeme ve minimum nakit eşiğine göre ilk finansman ihtiyacı tarihini görün.', tag: 'Haftalık görünüm' },
  { icon: ReceiptText, title: 'Alacak riski', text: 'Fatura bazlı açık alacakları 0–30, 31–60, 61–90 ve 90+ gün olarak yaşlandırın.', tag: 'Tahsilat odağı' },
  { icon: HandCoins, title: 'Borç servisi', text: 'Anapara, faiz, para birimi ve operasyonel nakit üzerinden borç karşılama kapasitesini inceleyin.', tag: 'DSCR kontrolü' },
  { icon: LineChart, title: 'Bütçe ve tahmin', text: 'Bütçe–gerçekleşen sapmasını, yıl sonu görünümünü ve geçmiş tahmin hatasını karşılaştırın.', tag: 'Senaryo' },
  { icon: Bot, title: 'AI CFO', text: 'Finans motorunun doğruladığı sonuçları yönetici dilinde açıklayın; eksik veride kesin öneriyi durdurun.', tag: 'İnsan onaylı' },
];

const dataJourney = [
  { step: '01', icon: FileSpreadsheet, title: 'Verinizi getirin', text: 'Excel/CSV şablonu veya kontrollü manuel giriş kullanın.' },
  { step: '02', icon: ClipboardCheck, title: 'Kaliteyi doğrulayın', text: 'Eksik alanlar, hatalı satırlar ve eşlenmeyen hesaplar işaretlenir.' },
  { step: '03', icon: Calculator, title: 'Motor hesaplasın', text: 'Finansal tablolar, oranlar ve ajan kontrolleri AI’dan bağımsız çalışır.' },
  { step: '04', icon: Layers3, title: 'Karar sırasını görün', text: 'Risk, finansal etki, kaynak ve gereken insan onayı birlikte sunulur.' },
];

const pilotOptions = [
  {
    id: 'quick', icon: Eye, title: 'Hızlı yönetici turu', badge: 'Önerilen',
    description: 'Dengeli büyüyen kurgusal bir KOBİ üzerinden karar merkezini 3 dakikada keşfedin.',
    signal: 'Genel görünüm · AI bulguları · karar sırası', agents: '3 temel kontrol', duration: '3 dakika',
    action: 'Turu başlat', layout: 'lg:col-span-7', featured: true,
  },
  {
    id: 'own-data', icon: Upload, title: 'Kendi verimle başla', badge: 'Şirketinize özel',
    description: 'Excel, CSV, Google Sheets veya manuel girişle kendi çalışma alanınızı oluşturun.',
    signal: 'Doğrulama · eksik alanlar · güvenli kayıt', agents: 'Veriye göre', duration: '5–15 dakika',
    action: 'Veri ekranını aç', layout: 'lg:col-span-5', featured: false,
  },
  {
    id: 'cash-pressure', icon: WalletCards, title: 'Nakit baskısı', badge: 'Risk senaryosu',
    description: 'Tahsilat gecikmesi, kısa vadeli ödeme yükü ve negatif nakit dönemini birlikte inceleyin.',
    signal: 'Likidite · tahsilat · borç servisi', agents: '5 ajan görünümü', duration: '4 dakika',
    action: 'Nakit senaryosunu aç', layout: 'lg:col-span-4', featured: false,
  },
  {
    id: 'profit-pressure', icon: Calculator, title: 'Kârlılık düşüşü', badge: 'Marj senaryosu',
    description: 'Ciro büyürken maliyet artışının FAVÖK ve net kâr üzerindeki etkisini görün.',
    signal: 'Gelir tablosu · bütçe · sapma', agents: '4 kontrol', duration: '4 dakika',
    action: 'Kârlılık senaryosunu aç', layout: 'lg:col-span-4', featured: false,
  },
  {
    id: 'full-company', icon: Bot, title: 'Tam kapsamlı şirket', badge: '7 ajan',
    description: 'Mizan, 13 haftalık nakit, alacak, borç servisi ve bütçe verileriyle tüm sistemi zorlayın.',
    signal: 'Baş denetçi · uzman ajanlar · AI CFO', agents: '7 ajan veri seti', duration: '7 dakika',
    action: 'Tam sistemi incele', layout: 'lg:col-span-4', featured: false,
  },
];

const demoStages = [
  { label: 'Örnek veri hazırlanıyor', detail: 'Şirket profili ve dönem verileri yükleniyor' },
  { label: 'Finans motoru çalışıyor', detail: 'Metrikler ve mutabakat kontrolleri hesaplanıyor' },
  { label: 'Riskler önceliklendiriliyor', detail: 'Ajan bulguları karar sırasına alınıyor' },
  { label: 'Çalışma alanı açılıyor', detail: 'Seçtiğiniz görünüme yönlendiriliyorsunuz' },
];

const faqs = [
  { q: 'KazKaz muhasebecimin veya CFO’nun yerine geçer mi?', a: 'Hayır. KazKaz finansal karar desteği sağlar; muhasebe kaydı, bağımsız denetim görüşü veya yetkili kişi onayı üretmez. Uzmanınızın daha hızlı ve izlenebilir çalışmasına yardımcı olur.' },
  { q: 'Hangi verileri yükleyebilirim?', a: 'V1, Excel ve CSV üzerinden finansal görünüm, işlem satırları, mizan, 13 haftalık nakit planı, alacak faturaları, borç servisi ve bütçe verilerini doğrular.' },
  { q: 'Eksik veya hatalı veri yüklersem ne olur?', a: 'Sistem sonuç uydurmaz. Eksik alanı, hatalı satırı veya eşlenmeyen hesabı gösterir; ilgili metriği “veri gerekli” durumunda tutar.' },
  { q: 'AI finansal hesaplamaları değiştirir mi?', a: 'Hayır. Temel hesaplamalar sürümlü ve test edilebilir finans motorunda yapılır. AI yalnızca doğrulanmış sonucu açıklamak için kullanılır.' },
  { q: 'KVKK, ISO 27001 ve Türkiye’de barındırma tamamlandı mı?', a: 'Bu başlıklar belge ve canlı altyapı doğrulaması gerektirir. Tamamlanmayan uyum veya sertifika iddiaları üründe kazanılmış statü gibi gösterilmez.' },
  { q: 'Neden kullanıcı sayısı, müşteri logosu veya tasarruf rakamı göstermiyorsunuz?', a: 'Bu rakamlar üretim telemetrisi, yazılı müşteri izni ve ölçüm kaydı oluştuğunda yayınlanır. Kurgusal demo verisi sosyal kanıt olarak kullanılmaz.' },
  { q: 'Logo, Mikro ve Netsis entegrasyonları hazır mı?', a: 'Hayır. V1 bugün Excel/CSV, Google Sheets doğrulama ve manuel veri girişini destekler. ERP bağlantıları gerçek mutabakat ve hata senaryoları tamamlandıktan sonra hazır olarak işaretlenecektir.' },
];

export const LandingPage: React.FC<LandingPageProps> = ({ onNavigateTab, onOpenAuth, onSelectDemo }) => {
  const [selectedSector, setSelectedSector] = useState('E-ticaret');
  const [activeInsight, setActiveInsight] = useState(0);
  const [openFaq, setOpenFaq] = useState<number | null>(0);
  const [activeDemo, setActiveDemo] = useState<(typeof pilotOptions)[number] | null>(null);
  const [demoStage, setDemoStage] = useState(0);
  const [publicPerformance, setPublicPerformance] = useState<KamuyaAcikPerformans | null>(null);
  const demoRun = useRef(0);
  const sectorMessage = sectorMessages[selectedSector];
  const heroInsight = heroInsights[activeInsight];

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined;
    const timer = window.setInterval(() => {
      setActiveInsight((current) => (current + 1) % heroInsights.length);
    }, 5200);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    let active = true;
    void kamuyaAcikPerformansiGetir()
      .then((summary) => { if (active) setPublicPerformance(summary); })
      .catch(() => { /* Güven alanı API ulaşılamadığında statik ve ihtiyatlı kalır. */ });
    return () => { active = false; };
  }, []);

  const wait = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

  const startDemo = async (option: (typeof pilotOptions)[number]) => {
    if (option.id === 'own-data') {
      onOpenAuth();
      return;
    }
    const runId = ++demoRun.current;
    setActiveDemo(option);
    setDemoStage(0);
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    for (let index = 0; index < demoStages.length; index += 1) {
      if (demoRun.current !== runId) return;
      setDemoStage(index);
      await wait(reducedMotion ? 80 : 620);
    }
    if (demoRun.current !== runId) return;
    await onSelectDemo(option.id);
  };

  const cancelDemo = () => {
    demoRun.current += 1;
    setActiveDemo(null);
    setDemoStage(0);
  };

  const showDemoOptions = () => {
    document.getElementById('pilot-secenekleri')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="landing-page overflow-hidden bg-[#f7f8fc] text-[#0a1628]">
      <main>
        <section id="urun" className="relative isolate overflow-hidden border-b border-slate-200/80">
          <div className="landing-grid absolute inset-0 -z-30" />
          <div className="landing-orb landing-orb-violet -z-20" />
          <div className="landing-orb landing-orb-orange -z-20" />
          <div className="landing-orb landing-orb-blue -z-20" />

          <div className="mx-auto grid min-h-[760px] max-w-7xl items-center gap-14 px-5 py-16 sm:px-8 lg:grid-cols-[1.03fr_.97fr] lg:px-10 lg:py-20">
            <div className="relative max-w-2xl">
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-violet-200 bg-white/80 px-3.5 py-2 text-xs font-bold text-violet-800 shadow-sm backdrop-blur-xl">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-violet-400 opacity-50" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-violet-600" />
                </span>
                Kontrollü AI CFO · Pilot sürüm
              </div>

              <p className="mb-4 text-xs font-extrabold uppercase tracking-[0.18em] text-slate-500">
                Finansal veriniz size ne anlatıyor?
              </p>
              <h1 className="landing-title max-w-3xl text-[2.85rem] font-black leading-[1.03] tracking-[-0.052em] text-[#09162d] sm:text-6xl lg:text-[4.5rem]">
                Rakamları değil,{' '}
                <span className="landing-gradient-text">almanız gereken kararı</span> görün.
              </h1>

              <p className="mt-6 max-w-xl text-base leading-7 text-slate-600 sm:text-lg sm:leading-8">
                KazKaz; gelir tablosu, bilanço, nakit ve borç verilerinizi açıklanabilir bir karar sırasına dönüştürür. Hesabı finans motoru yapar, AI sonucu anlaşılır hale getirir.
              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <button
                  type="button"
                  onClick={onOpenAuth}
                  className="landing-primary-button group inline-flex min-h-13 items-center justify-center gap-2.5 rounded-xl bg-[#0f2252] px-6 py-3.5 text-sm font-extrabold text-white shadow-[0_16px_36px_rgba(15,34,82,.22)] transition hover:-translate-y-1 hover:bg-[#1c3674] focus-visible:ring-2 focus-visible:ring-violet-400"
                >
                  Ücretsiz finansal görünüm oluştur
                  <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
                </button>
                <button
                  type="button"
                  onClick={showDemoOptions}
                  className="inline-flex min-h-13 items-center justify-center gap-2.5 rounded-xl border border-slate-300 bg-white/80 px-6 py-3.5 text-sm font-bold text-slate-800 shadow-sm backdrop-blur-xl transition hover:-translate-y-0.5 hover:border-violet-300 hover:bg-white"
                >
                  <Activity className="h-4 w-4 text-violet-600" />
                  Örnek şirketi incele
                </button>
              </div>

              <div className="mt-7 flex flex-wrap gap-x-5 gap-y-3 text-xs font-semibold text-slate-500">
                {['Kredi kartı gerekmez', 'Örnek veriyle keşfedin', 'AI kaynağı görünür'].map((item) => (
                  <span key={item} className="flex items-center gap-1.5">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600" /> {item}
                  </span>
                ))}
              </div>
            </div>

            <div className="relative mx-auto w-full max-w-[620px] lg:translate-x-3">
              <div className="landing-dashboard-glow absolute -inset-10 -z-10 rounded-full blur-3xl" />
              <div className="landing-dashboard overflow-hidden rounded-[1.6rem] border border-white/80 bg-white/90 shadow-[0_35px_100px_rgba(15,34,82,.18)] backdrop-blur-2xl">
                <div className="flex items-center justify-between border-b border-slate-200/80 px-5 py-4 sm:px-6">
                  <div className="flex items-center gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#0f2252] text-white shadow-lg shadow-blue-950/15">
                      <ScanLine className="h-5 w-5" />
                    </span>
                    <div>
                      <p className="text-sm font-extrabold text-slate-900">Finansal karar merkezi</p>
                      <p className="mt-0.5 text-[11px] text-slate-500">Anadolu Teknoloji · örnek veri</p>
                    </div>
                  </div>
                  <span className="flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[10px] font-extrabold text-emerald-700">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Motor aktif
                  </span>
                </div>

                <div className="relative p-4 sm:p-6">
                  <div className="landing-scan-line" />
                  <div className="mb-4 grid grid-cols-3 rounded-xl border border-slate-200 bg-slate-100/80 p-1" role="tablist" aria-label="Örnek karar görünümü">
                    {heroInsights.map((insight, index) => (
                      <button
                        key={insight.id}
                        type="button"
                        role="tab"
                        aria-selected={activeInsight === index}
                        onClick={() => setActiveInsight(index)}
                        className={`rounded-lg px-2 py-2 text-[10px] font-extrabold transition sm:text-[11px] ${activeInsight === index ? 'bg-white text-[#0f2252] shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}
                      >
                        {insight.label}
                      </button>
                    ))}
                  </div>
                  <div className="rounded-2xl bg-[#0b1733] p-5 text-white shadow-xl shadow-slate-900/10">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-violet-300">{heroInsight.eyebrow}</p>
                        <p className="mt-2 max-w-md text-sm font-semibold leading-6 text-white">
                          {heroInsight.title}
                        </p>
                      </div>
                      <span className="rounded-lg bg-amber-400/15 px-2 py-1 text-[10px] font-bold text-amber-300">İnsan onayı</span>
                    </div>
                    <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-white/10">
                      <div className="landing-progress h-full rounded-full bg-gradient-to-r from-violet-400 via-fuchsia-400 to-orange-400 transition-[width] duration-700" style={{ width: `${heroInsight.progress}%` }} />
                    </div>
                    <div className="mt-2 flex justify-between text-[10px] text-slate-400">
                      <span>Örnek veri kapsamı</span><span>%{heroInsight.progress} · açıklanabilir</span>
                    </div>
                  </div>

                  <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
                    {[
                      ['Net kâr marjı', '%23,0', 'Hesaplandı', 'text-emerald-700'],
                      ['Cari oran', '2,50x', 'Hesaplandı', 'text-violet-700'],
                      ['FAVÖK', 'Veri gerekli', 'Amortisman eksik', 'text-amber-700'],
                    ].map(([label, value, note, tone], index) => (
                      <div key={label} className={`rounded-xl border border-slate-200 bg-white p-4 ${index === 2 ? 'col-span-2 sm:col-span-1' : ''}`}>
                        <p className="text-[10px] font-semibold text-slate-500">{label}</p>
                        <p className={`mt-2 text-lg font-black tracking-tight ${tone}`}>{value}</p>
                        <p className="mt-1 text-[9px] text-slate-400">{note}</p>
                      </div>
                    ))}
                  </div>

                  <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50/80 p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs font-extrabold text-slate-800">{heroInsight.metric}</p>
                        <p className="mt-0.5 text-[10px] text-slate-500">{heroInsight.metricLabel}</p>
                      </div>
                      <span className="rounded-md bg-white px-2 py-1 text-[9px] font-bold text-slate-500 shadow-sm">Örnek veri</span>
                    </div>
                    <div className="mt-4 flex h-20 items-end gap-2" aria-label="Örnek nakit eğilimi">
                      {[44, 58, 38, 71, 64, 86, 78, 96].map((height, index) => (
                        <div key={height + index} className="flex h-full flex-1 items-end">
                          <div
                            className={`w-full rounded-t-md transition-all duration-500 ${index === 7 ? 'bg-gradient-to-t from-violet-700 to-violet-400' : 'bg-slate-300'}`}
                            style={{ height: `${height}%` }}
                          />
                        </div>
                      ))}
                    </div>
                    <p className="mt-3 border-t border-slate-200 pt-3 text-[10px] leading-4 text-slate-500">{heroInsight.note}</p>
                  </div>
                </div>
              </div>

              <div className="landing-float-delayed absolute -bottom-7 -left-5 hidden rounded-2xl border border-white bg-white/95 p-3.5 shadow-[0_18px_50px_rgba(15,34,82,.16)] backdrop-blur-xl sm:flex sm:items-center sm:gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-violet-100 text-violet-700"><Bot className="h-4 w-4" /></span>
                <div><p className="text-[10px] font-extrabold text-slate-800">AI açıklaması hazır</p><p className="mt-0.5 text-[9px] text-slate-500">Kaynak: finans motoru</p></div>
              </div>
            </div>
          </div>

          <div className="border-t border-slate-200/80 bg-white/65 backdrop-blur-xl">
            <div className="mx-auto grid max-w-7xl gap-px px-5 sm:grid-cols-3 sm:px-8 lg:px-10">
              {[
                ['Finans motoru', 'AI’dan bağımsız hesaplama'],
                ['Kontrollü ajanlar', 'Nakit · borç · yatırım hazırlığı'],
                ['Güvenli geri dönüş', 'AI yoksa kurallı analiz'],
              ].map(([title, detail]) => (
                <div key={title} className="border-slate-200 px-4 py-5 sm:border-r sm:last:border-r-0">
                  <p className="text-xs font-extrabold text-slate-900">{title}</p>
                  <p className="mt-1 text-[11px] text-slate-500">{detail}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="moduller" className="bg-white py-20 sm:py-24">
          <div className="mx-auto max-w-7xl px-5 sm:px-8 lg:px-10">
            <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
              <div className="max-w-3xl">
                <p className="landing-kicker">Tek çalışma alanı</p>
                <h2 className="mt-4 text-3xl font-black tracking-[-0.04em] text-[#0a1628] sm:text-5xl">Finansın kritik parçaları birbirinden kopuk kalmasın.</h2>
                <p className="mt-5 max-w-2xl text-base leading-7 text-slate-600">Özet oranlardan mizana, nakit planından AI CFO’ya kadar her modül aynı doğrulanmış veri sözleşmesini kullanır.</p>
              </div>
              <button type="button" onClick={onOpenAuth} className="inline-flex shrink-0 items-center gap-2 self-start rounded-xl border border-violet-200 bg-violet-50 px-4 py-3 text-sm font-extrabold text-violet-800 transition hover:-translate-y-0.5 hover:bg-violet-100 lg:self-auto">
                Verimi hazırlamaya başla <ArrowUpRight className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {productModules.map((module, index) => {
                const Icon = module.icon;
                return (
                  <article key={module.title} className={`landing-module-card group rounded-2xl border border-slate-200 bg-[#f9fafc] p-5 transition ${index === 0 ? 'lg:col-span-2 lg:grid lg:grid-cols-[auto_1fr] lg:gap-5' : ''}`}>
                    <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-violet-100 bg-white text-violet-700 shadow-sm transition group-hover:-rotate-3 group-hover:scale-105"><Icon className="h-5 w-5" /></span>
                    <div className={index === 0 ? '' : 'mt-5'}>
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <h3 className="text-base font-extrabold text-slate-900">{module.title}</h3>
                        <span className="rounded-full bg-slate-100 px-2 py-1 text-[9px] font-bold text-slate-500">{module.tag}</span>
                      </div>
                      <p className="mt-3 text-sm leading-6 text-slate-600">{module.text}</p>
                    </div>
                  </article>
                );
              })}
              <button type="button" onClick={showDemoOptions} className="group flex min-h-52 flex-col justify-between rounded-2xl bg-[#0f2252] p-5 text-left text-white shadow-[0_18px_45px_rgba(15,34,82,.16)] transition hover:-translate-y-1 hover:bg-[#1a3470]">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-white/10"><ArrowUpRight className="h-5 w-5 transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5" /></span>
                <span><strong className="block text-lg">Çalışan ürünü görün</strong><span className="mt-2 block text-sm leading-6 text-blue-100/75">Örnek veriyi açıp metriklerin kaynaklarını inceleyin.</span></span>
              </button>
            </div>
          </div>
        </section>

        <section id="veri-yolculugu" className="border-y border-slate-200 bg-[#f7f8fc] py-20 sm:py-24">
          <div className="mx-auto max-w-7xl px-5 sm:px-8 lg:px-10">
            <div className="mx-auto max-w-3xl text-center">
              <p className="landing-kicker">Veriden karara</p>
              <h2 className="mt-4 text-3xl font-black tracking-[-0.04em] text-[#0a1628] sm:text-5xl">Dört adımda, kontrolü kaybetmeden.</h2>
              <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-slate-600">Her aşamada neyin hesaplandığını, neyin eksik olduğunu ve hangi kararın insan onayı istediğini görün.</p>
            </div>

            <div className="relative mt-12 grid gap-4 md:grid-cols-4">
              <div className="absolute left-[12%] right-[12%] top-7 hidden h-px bg-gradient-to-r from-violet-200 via-blue-200 to-orange-200 md:block" />
              {dataJourney.map((item) => {
                const Icon = item.icon;
                return (
                  <article key={item.step} className="relative rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                    <div className="flex items-center justify-between">
                      <span className="relative z-10 flex h-14 w-14 items-center justify-center rounded-2xl border border-violet-200 bg-violet-50 text-violet-700 shadow-[0_0_0_7px_#f7f8fc]"><Icon className="h-6 w-6" /></span>
                      <span className="font-mono text-[10px] font-extrabold text-slate-400">{item.step}</span>
                    </div>
                    <h3 className="mt-6 text-base font-extrabold text-slate-900">{item.title}</h3>
                    <p className="mt-3 text-sm leading-6 text-slate-600">{item.text}</p>
                  </article>
                );
              })}
            </div>

            <div className="mt-8 flex flex-col items-start justify-between gap-4 rounded-2xl border border-blue-200 bg-blue-50/70 p-5 sm:flex-row sm:items-center">
              <div className="flex items-start gap-3"><Upload className="mt-0.5 h-5 w-5 shrink-0 text-blue-700" /><div><p className="text-sm font-extrabold text-blue-950">Hazır şablonla başlayabilirsiniz</p><p className="mt-1 text-xs leading-5 text-blue-800">Excel şablonu, gerekli sayfaları ve alanları doğrudan çalışma alanında sunar.</p></div></div>
              <button type="button" onClick={onOpenAuth} className="shrink-0 rounded-lg bg-blue-950 px-4 py-2.5 text-xs font-extrabold text-white transition hover:bg-blue-900">Veri ekranını aç</button>
            </div>
          </div>
        </section>

        <section className="bg-white py-20 sm:py-24">
          <div className="mx-auto max-w-7xl px-5 sm:px-8 lg:px-10">
            <div className="mx-auto max-w-3xl text-center">
              <p className="landing-kicker">Sektörünüzde önce neye bakmalı?</p>
              <h2 className="mt-4 text-3xl font-black tracking-[-0.04em] text-[#0a1628] sm:text-5xl">Tek ekran, şirketinize göre değişen karar odağı.</h2>
              <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-slate-600">Sektörü seçin; KazKaz’ın önce hangi finansal sinyali açıklayacağını görün.</p>
            </div>

            <div className="mt-9 flex flex-wrap justify-center gap-2">
              {sectors.map((sector) => (
                <button
                  type="button"
                  key={sector}
                  onClick={() => setSelectedSector(sector)}
                  className={`rounded-full border px-4 py-2 text-xs font-extrabold transition ${selectedSector === sector ? 'border-[#0f2252] bg-[#0f2252] text-white shadow-lg shadow-blue-950/15' : 'border-slate-200 bg-slate-50 text-slate-600 hover:border-violet-300 hover:bg-violet-50 hover:text-violet-800'}`}
                >
                  {sector}
                </button>
              ))}
            </div>

            <div className="landing-reveal mt-10 grid overflow-hidden rounded-[2rem] bg-[#0b1733] shadow-[0_30px_80px_rgba(15,34,82,.18)] lg:grid-cols-[1.05fr_.95fr]">
              <div className="relative overflow-hidden p-7 sm:p-10 lg:p-12">
                <div className="absolute -left-20 top-0 h-64 w-64 rounded-full bg-violet-600/25 blur-3xl" />
                <div className="relative">
                  <span className="inline-flex items-center gap-2 rounded-full border border-violet-300/20 bg-violet-400/10 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.14em] text-violet-200">
                    <Sparkles className="h-3.5 w-3.5" /> {selectedSector} görünümü
                  </span>
                  <h3 className="mt-6 max-w-xl text-3xl font-black tracking-[-0.035em] text-white sm:text-4xl">{sectorMessage.title}</h3>
                  <p className="mt-5 max-w-xl text-sm leading-7 text-slate-300">{sectorMessage.detail}</p>
                  <button type="button" onClick={onOpenAuth} className="mt-8 inline-flex items-center gap-2 text-sm font-extrabold text-orange-300 transition hover:text-orange-200">
                    Kendi verinizle görün <ArrowRight className="h-4 w-4" />
                  </button>
                </div>
              </div>

              <div className="border-t border-white/10 bg-white/[0.045] p-7 sm:p-10 lg:border-l lg:border-t-0">
                <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">İlk incelenecek sinyal</p>
                <p className="mt-3 text-xl font-black text-white">{sectorMessage.signal}</p>
                <div className="mt-7 space-y-3">
                  {analysisAreas.map((area) => {
                    const Icon = area.icon;
                    return (
                      <div key={area.label} className="group flex gap-4 rounded-xl border border-white/10 bg-white/[0.045] p-4 transition hover:-translate-y-0.5 hover:border-violet-300/30 hover:bg-white/[0.07]">
                        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/10 text-violet-200"><Icon className="h-4.5 w-4.5" /></span>
                        <div><p className="text-xs font-extrabold text-white">{area.label}</p><p className="mt-1 text-[11px] leading-5 text-slate-400">{area.value}</p></div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="nasil-calisir" className="border-y border-slate-200 bg-[#f7f8fc] py-20 sm:py-24">
          <div className="mx-auto max-w-7xl px-5 sm:px-8 lg:px-10">
            <div className="grid gap-10 lg:grid-cols-[.72fr_1.28fr] lg:gap-16">
              <div className="lg:sticky lg:top-28 lg:self-start">
                <p className="landing-kicker">Dört kontrollü katman</p>
                <h2 className="mt-4 text-3xl font-black tracking-[-0.04em] text-[#0a1628] sm:text-5xl">AI karar vermez. Kararı açıklanabilir hale getirir.</h2>
                <p className="mt-5 text-base leading-7 text-slate-600">Her aşama bir öncekinin doğrulanmış çıktısını kullanır. Veri yetersizse zincir güvenli biçimde durur.</p>
                <button type="button" onClick={() => onNavigateTab('cfo-agent')} className="mt-7 inline-flex items-center gap-2 text-sm font-extrabold text-violet-700 transition hover:text-violet-900">
                  Kontrollü ajanları aç <ArrowRight className="h-4 w-4" />
                </button>
              </div>

              <div className="relative space-y-4 before:absolute before:bottom-10 before:left-[1.65rem] before:top-10 before:w-px before:bg-gradient-to-b before:from-violet-300 before:via-slate-200 before:to-orange-300 sm:before:left-[2.15rem]">
                {agentFlow.map((agent) => {
                  const Icon = agent.icon;
                  return (
                    <article key={agent.step} className="landing-agent-card relative flex gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition sm:gap-6 sm:p-6">
                      <span className="relative z-10 flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-violet-200 bg-violet-50 text-violet-700 shadow-[0_0_0_6px_#f7f8fc] sm:h-12 sm:w-12"><Icon className="h-5 w-5" /></span>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between gap-4"><p className="text-base font-extrabold text-slate-900">{agent.title}</p><span className="font-mono text-[10px] font-bold text-slate-400">{agent.step}</span></div>
                        <p className="mt-2 text-sm leading-6 text-slate-600">{agent.description}</p>
                      </div>
                    </article>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

        <section id="guvenlik" className="bg-white py-20 sm:py-24">
          <div className="mx-auto max-w-7xl px-5 sm:px-8 lg:px-10">
            <div className="mx-auto max-w-3xl text-center">
              <span className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl border border-emerald-200 bg-emerald-50 text-emerald-700"><ShieldCheck className="h-6 w-6" /></span>
              <p className="landing-kicker mt-5">Güven iddiayla değil, kanıtla</p>
              <h2 className="mt-4 text-3xl font-black tracking-[-0.04em] text-[#0a1628] sm:text-5xl">Sistemin bildiği kadar, bilmediği de görünür.</h2>
            </div>

            <div className="mt-12 grid gap-4 lg:grid-cols-3">
              {trustItems.map((item) => {
                const Icon = item.icon;
                return (
                  <article key={item.title} className="landing-trust-card rounded-2xl border border-slate-200 bg-[#f9fafc] p-6 transition">
                    <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-white text-emerald-700 shadow-sm"><Icon className="h-5 w-5" /></span>
                    <h3 className="mt-6 text-base font-extrabold text-slate-900">{item.title}</h3>
                    <p className="mt-3 text-sm leading-6 text-slate-600">{item.text}</p>
                  </article>
                );
              })}
            </div>

            <div className="mt-12 overflow-hidden rounded-[1.75rem] border border-slate-200 bg-[#0b1733] shadow-[0_30px_80px_rgba(15,34,82,.14)]">
              <div className="relative overflow-hidden border-b border-white/10 px-6 py-8 text-white sm:px-8 lg:flex lg:items-end lg:justify-between lg:gap-10">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_12%_0%,rgba(124,58,237,.28),transparent_34%),radial-gradient(circle_at_92%_100%,rgba(37,99,235,.18),transparent_32%)]" />
                <div className="relative max-w-3xl">
                  <p className="text-[10px] font-extrabold uppercase tracking-[0.17em] text-violet-200">Doğrulanabilir güven programı</p>
                  <h3 className="mt-3 text-2xl font-black tracking-[-0.035em] sm:text-3xl">Büyük vaatler, yayınlanabilir kanıta dönüşsün.</h3>
                  <p className="mt-3 text-sm leading-6 text-slate-300">Sertifika, hız, kullanıcı sayısı, müşteri sonucu ve entegrasyon iddiaları aynı kanıt kapısından geçer. Durum değiştiğinde metin değil, dayanağıyla birlikte statü güncellenir.</p>
                </div>
                <div className="relative mt-6 grid shrink-0 grid-cols-3 gap-2 text-center lg:mt-0">
                  {([
                    ['2', 'teknik temel'],
                    ['2', 'doğrulama'],
                    ['8', 'yol haritası'],
                  ] as const).map(([value, label]) => (
                    <div key={label} className="rounded-xl border border-white/10 bg-white/[0.06] px-3 py-2.5 backdrop-blur-sm">
                      <p className="text-lg font-black text-white">{value}</p>
                      <p className="mt-0.5 text-[9px] font-bold uppercase tracking-wide text-slate-400">{label}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid gap-px bg-white/10 md:grid-cols-2 xl:grid-cols-3">
                {claimPrograms.map((program) => {
                  const isPerformance = program.title === 'Ölçülmüş analiz süresi';
                  const publishedPerformance = isPerformance && publicPerformance?.durum === 'yayina_hazir';
                  const displayedProgram = publishedPerformance
                    ? {
                        ...program,
                        current: `Son doğrulanmış p50 ${Math.round(publicPerformance.p50_ms || 0)} ms · p95 ${Math.round(publicPerformance.p95_ms || 0)} ms · başarı %${publicPerformance.basari_orani?.toLocaleString('tr-TR')}.`,
                        proof: `${publicPerformance.orneklem} anonim üretim örneği · kişisel ve finansal veri toplanmaz.`,
                      }
                    : isPerformance && publicPerformance?.durum === 'yetersiz_veri'
                      ? { ...program, current: publicPerformance.mesaj || program.current }
                      : program;
                  const Icon = displayedProgram.icon;
                  const status = claimProgramStatuses[displayedProgram.status];
                  return (
                    <article key={displayedProgram.title} className="group bg-[#0b1733] p-6 transition hover:bg-[#101f40]">
                      <div className="flex items-start justify-between gap-3">
                        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-white/10 bg-white/[0.07] text-violet-200 transition group-hover:border-violet-300/30 group-hover:bg-violet-400/10"><Icon className="h-5 w-5" /></span>
                        <span className={`rounded-full border px-2.5 py-1 text-[9px] font-extrabold uppercase tracking-wide ${status.className}`}>{status.label}</span>
                      </div>
                      <h4 className="mt-5 text-sm font-extrabold leading-5 text-white">{displayedProgram.title}</h4>
                      <p className="mt-2 text-xs leading-5 text-slate-300">{displayedProgram.promise}</p>
                      <div className="mt-5 space-y-3 border-t border-white/10 pt-4 text-[10px] leading-4">
                        <div><span className="font-extrabold uppercase tracking-[0.11em] text-slate-500">Bugün</span><p className="mt-1 text-slate-300">{displayedProgram.current}</p></div>
                        <div><span className="font-extrabold uppercase tracking-[0.11em] text-violet-300">Yayın kanıtı</span><p className="mt-1 text-slate-400">{displayedProgram.proof}</p></div>
                      </div>
                    </article>
                  );
                })}
              </div>

              <div className="flex flex-col gap-3 border-t border-white/10 bg-[#08142e] px-6 py-5 text-[11px] leading-5 text-slate-300 sm:flex-row sm:items-center sm:justify-between sm:px-8">
                <p><strong className="text-white">Yayın kuralı:</strong> Kanıtı olmayan sayı, sertifika, garanti veya müşteri sonucu kazanılmış özellik olarak gösterilmez.</p>
                <span className="shrink-0 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1.5 font-extrabold uppercase tracking-wide text-emerald-300">Kanıt kapısı açık</span>
              </div>
            </div>

            <div className="mt-6 flex flex-col items-start justify-between gap-5 rounded-2xl border border-amber-200 bg-amber-50/70 p-6 sm:flex-row sm:items-center">
              <div className="flex gap-4">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-100 text-amber-700"><FileCheck2 className="h-5 w-5" /></span>
                <div><p className="text-sm font-extrabold text-amber-950">Metodoloji onayları şeffaf tutulur</p><p className="mt-1 text-xs leading-5 text-amber-800">FAVÖK, yatırım limiti ve borç politikası gibi başlıklar uzman onayı tamamlanmadan kesin öneri olarak gösterilmez.</p></div>
              </div>
              <span className="shrink-0 rounded-full border border-amber-300 bg-white px-3 py-1.5 text-[10px] font-extrabold uppercase tracking-wide text-amber-800">Onay kapısı aktif</span>
            </div>
          </div>
        </section>

        <section id="pilot-secenekleri" className="border-y border-slate-200 bg-[#f7f8fc] py-20 sm:py-24">
          <div className="mx-auto max-w-7xl px-5 sm:px-8 lg:px-10">
            <div className="mx-auto max-w-3xl text-center">
              <p className="landing-kicker">V1 erişim seçenekleri</p>
              <h2 className="mt-4 text-3xl font-black tracking-[-0.04em] text-[#0a1628] sm:text-5xl">Önce görün, sonra kendi verinizle doğrulayın.</h2>
              <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-slate-600">Canlı ödeme ve ticari taahhütler tamamlanana kadar erişim pilot kapsamındadır. Kanıtlanmamış indirim veya garanti kullanılmaz.</p>
            </div>

            <div className="mt-12 grid gap-5 lg:grid-cols-12">
              {pilotOptions.map((option, index) => {
                const Icon = option.icon;
                return (
                  <article key={option.id} style={{ animationDelay: `${index * 90}ms` }} className={`landing-sample-card group relative flex min-h-[270px] flex-col overflow-hidden rounded-[1.5rem] border p-6 ${option.layout} ${option.featured ? 'border-violet-400 bg-[#0b1733] text-white shadow-[0_28px_70px_rgba(15,34,82,.2)]' : 'border-slate-200 bg-white text-slate-900 shadow-sm'}`}>
                    <div className="flex items-start justify-between gap-4">
                      <span className={`landing-sample-icon grid h-11 w-11 place-items-center rounded-xl ${option.featured ? 'bg-white/10 text-violet-200' : 'bg-violet-50 text-violet-700'}`}><Icon className="h-5 w-5" /></span>
                      <span className={`rounded-full px-2.5 py-1 text-[9px] font-extrabold uppercase tracking-wide ${option.featured ? 'bg-violet-400/15 text-violet-200' : 'bg-slate-100 text-slate-500'}`}>{option.badge}</span>
                    </div>
                    <h3 className="mt-5 text-xl font-black sm:text-2xl">{option.title}</h3>
                    <p className={`mt-3 text-sm leading-6 ${option.featured ? 'text-slate-300' : 'text-slate-600'}`}>{option.description}</p>
                    <div className={`mt-5 flex flex-wrap gap-2 text-[10px] font-bold ${option.featured ? 'text-slate-200' : 'text-slate-600'}`}>
                      <span className={`rounded-lg px-2.5 py-1.5 ${option.featured ? 'bg-white/[0.07]' : 'bg-slate-50'}`}>{option.agents}</span>
                      <span className={`rounded-lg px-2.5 py-1.5 ${option.featured ? 'bg-white/[0.07]' : 'bg-slate-50'}`}>{option.duration}</span>
                    </div>
                    <p className={`mt-4 text-[10px] font-semibold uppercase tracking-[0.1em] ${option.featured ? 'text-violet-200' : 'text-violet-700'}`}>{option.signal}</p>
                    <button type="button" onClick={() => void startDemo(option)} className={`mt-auto inline-flex min-h-11 items-center justify-center gap-2 rounded-xl px-4 pt-0 text-sm font-extrabold transition ${option.featured ? 'bg-white text-[#0f2252] hover:-translate-y-0.5' : 'border border-slate-300 bg-white text-slate-800 hover:border-violet-300 hover:text-violet-800'}`}>
                      {option.action} <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
                    </button>
                    <div className="landing-sample-signal" aria-hidden="true"><span /><span /><span /></div>
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        {activeDemo && (
          <div className="landing-demo-overlay fixed inset-0 z-[70] grid place-items-center bg-[#071126]/70 px-4 backdrop-blur-md" role="dialog" aria-modal="true" aria-labelledby="demo-loading-title">
            <div className="landing-demo-dialog w-full max-w-xl overflow-hidden rounded-[1.5rem] border border-white/15 bg-white shadow-[0_35px_100px_rgba(7,17,38,.35)]">
              <div className="relative overflow-hidden bg-[#0b1733] px-6 py-7 text-white sm:px-8">
                <div className="landing-demo-orbit" aria-hidden="true"><span /><span /><span /></div>
                <div className="relative z-10 flex items-start gap-4">
                  <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-white/10 text-violet-200"><activeDemo.icon className="h-6 w-6" /></span>
                  <div><p className="text-[10px] font-extrabold uppercase tracking-[0.15em] text-violet-200">Örnek çalışma alanı hazırlanıyor</p><h3 id="demo-loading-title" className="mt-2 text-2xl font-black">{activeDemo.title}</h3><p className="mt-2 text-sm text-slate-300">{activeDemo.signal}</p></div>
                </div>
              </div>
              <div className="p-6 sm:p-8" aria-live="polite">
                <div className="mb-6 h-1.5 overflow-hidden rounded-full bg-slate-100"><span className="landing-demo-progress block h-full rounded-full bg-gradient-to-r from-[#0f2252] to-[#7c3aed]" style={{ width: `${((demoStage + 1) / demoStages.length) * 100}%` }} /></div>
                <div className="space-y-3">
                  {demoStages.map((stage, index) => {
                    const complete = index < demoStage;
                    const current = index === demoStage;
                    return (
                      <div key={stage.label} className={`flex items-start gap-3 rounded-xl border px-4 py-3 transition ${current ? 'landing-demo-current border-violet-200 bg-violet-50' : complete ? 'border-emerald-100 bg-emerald-50/60' : 'border-slate-100 bg-slate-50 opacity-55'}`}>
                        <span className={`mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full text-[10px] font-black ${complete ? 'bg-emerald-600 text-white' : current ? 'bg-violet-700 text-white' : 'bg-slate-200 text-slate-500'}`}>{complete ? <Check className="h-3.5 w-3.5" /> : index + 1}</span>
                        <div><p className="text-xs font-extrabold text-slate-900">{stage.label}</p><p className="mt-1 text-[10px] leading-4 text-slate-500">{stage.detail}</p></div>
                        {current && <ScanLine className="ml-auto h-4 w-4 animate-pulse text-violet-700" />}
                      </div>
                    );
                  })}
                </div>
                <button type="button" onClick={cancelDemo} className="mt-5 w-full text-center text-xs font-bold text-slate-500 transition hover:text-slate-900">Vazgeç</button>
              </div>
            </div>
          </div>
        )}

        <section id="sss" className="bg-white py-20 sm:py-24">
          <div className="mx-auto grid max-w-7xl gap-12 px-5 sm:px-8 lg:grid-cols-[.72fr_1.28fr] lg:px-10">
            <div>
              <p className="landing-kicker">Sık sorulan sorular</p>
              <h2 className="mt-4 text-3xl font-black tracking-[-0.04em] text-[#0a1628] sm:text-5xl">Aklınızda soru işareti kalmasın.</h2>
              <p className="mt-5 max-w-md text-base leading-7 text-slate-600">Ürünün yapabildikleri kadar sınırlarını da açıkça anlatıyoruz.</p>
              <div className="mt-8 rounded-2xl border border-slate-200 bg-slate-50 p-5">
                <div className="flex gap-3"><ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-amber-700" /><div><p className="text-sm font-extrabold text-slate-900">Pilot kullanım notu</p><p className="mt-2 text-xs leading-5 text-slate-600">Finansal sonuçlar karar desteğidir. Ödeme, yatırım, kredi ve muhasebe aksiyonları yetkili uzman onayı gerektirir.</p></div></div>
              </div>
            </div>

            <div className="divide-y divide-slate-200 rounded-2xl border border-slate-200 bg-[#f9fafc] px-5 sm:px-7">
              {faqs.map((faq, index) => {
                const isOpen = openFaq === index;
                return (
                  <article key={faq.q}>
                    <h3>
                      <button type="button" aria-expanded={isOpen} onClick={() => setOpenFaq(isOpen ? null : index)} className="flex w-full items-center justify-between gap-4 py-5 text-left text-sm font-extrabold text-slate-900 sm:text-base">
                        {faq.q}<ChevronDown className={`h-4 w-4 shrink-0 text-violet-700 transition ${isOpen ? 'rotate-180' : ''}`} />
                      </button>
                    </h3>
                    {isOpen && <p className="landing-reveal pb-6 pr-8 text-sm leading-7 text-slate-600">{faq.a}</p>}
                  </article>
                );
              })}
            </div>
          </div>
        </section>

        <section id="pilot" className="relative overflow-hidden bg-[#08142e] py-20 text-white sm:py-24">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_25%_0%,rgba(124,58,237,.25),transparent_34%),radial-gradient(circle_at_80%_100%,rgba(255,77,0,.17),transparent_32%)]" />
          <div className="landing-grid-dark absolute inset-0 opacity-30" />
          <div className="relative mx-auto max-w-4xl px-5 text-center sm:px-8">
            <Landmark className="mx-auto h-7 w-7 text-violet-300" />
            <h2 className="mt-5 text-3xl font-black tracking-[-0.04em] sm:text-5xl">İlk finansal karar görünümünüzü oluşturun.</h2>
            <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-slate-300">Önce örnek şirketi keşfedin. Hazır olduğunuzda kendi verinizi girip hangi alanların doğrulama istediğini görün.</p>
            <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
              <button type="button" onClick={onOpenAuth} className="group inline-flex min-h-13 items-center justify-center gap-2 rounded-xl bg-white px-6 py-3.5 text-sm font-extrabold text-[#0f2252] shadow-xl transition hover:-translate-y-1">
                <Upload className="h-4 w-4" /> Pilot analizimi oluştur <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
              </button>
              <button type="button" onClick={showDemoOptions} className="inline-flex min-h-13 items-center justify-center gap-2 rounded-xl border border-white/20 bg-white/[0.06] px-6 py-3.5 text-sm font-bold text-white backdrop-blur-xl transition hover:bg-white/[0.11]">
                <TrendingUp className="h-4 w-4" /> Örnek analizi aç
              </button>
            </div>
          </div>
        </section>

        <footer className="border-t border-white/10 bg-[#050b1b] py-12 text-white">
          <div className="mx-auto max-w-7xl px-5 sm:px-8 lg:px-10">
            <div className="grid gap-10 lg:grid-cols-[1.25fr_.75fr_.75fr]">
              <div className="max-w-md">
                <div className="flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-[#1f3c79] to-violet-600 font-black">✦</span><div><p className="text-lg font-black">KazKaz AI</p><p className="text-[11px] text-slate-500">Açıklanabilir dijital CFO çalışma alanı</p></div></div>
                <p className="mt-5 text-sm leading-6 text-slate-400">KOBİ ve finans ekipleri için veri kalitesi, finans motoru ve kontrollü AI açıklamasını tek karar akışında birleştirir.</p>
              </div>
              <div><p className="text-xs font-extrabold uppercase tracking-[.14em] text-slate-500">Ürün</p><nav className="mt-4 grid gap-3 text-sm text-slate-300" aria-label="Alt ürün menüsü"><a href="#moduller" className="hover:text-white">Modüller</a><a href="#veri-yolculugu" className="hover:text-white">Nasıl çalışır?</a><a href="#pilot-secenekleri" className="hover:text-white">Pilot erişim</a><a href="#sss" className="hover:text-white">Sık sorulanlar</a></nav></div>
              <div><p className="text-xs font-extrabold uppercase tracking-[.14em] text-slate-500">Güven ve sınırlar</p><nav className="mt-4 grid gap-3 text-sm text-slate-300" aria-label="Alt güven menüsü"><a href="#guvenlik" className="hover:text-white">Güven yaklaşımı</a><span>İnsan onayı gereklidir</span><span>Sertifika iddiası yoktur</span><span>Canlı ödeme henüz yoktur</span></nav></div>
            </div>
            <div className="mt-10 flex flex-col gap-3 border-t border-white/10 pt-6 text-[11px] text-slate-500 sm:flex-row sm:items-center sm:justify-between"><span>© 2026 KazKaz AI · Pilot V1</span><span>Karar desteği sağlar; muhasebe kaydı veya bağımsız denetim görüşü değildir.</span></div>
          </div>
        </footer>
      </main>
    </div>
  );
};

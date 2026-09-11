import React, { useEffect, useState } from 'react';
import { FinancialData } from '../types';
import type { FinansalDenetim, GelismisAjanGirdisi, KendiTrendi } from '../lib/api';
import { gelismisAjanAnalizi } from '../lib/api';
import { finansalMetrikler, paraBicimlendirici } from '../lib/metrikler';
import { KendiTrendin } from './KendiTrendin';
import {
  BarChart2,
  TrendingUp,
  Award,
  AlertTriangle,
  CheckCircle2,
  Building2,
  Target,
  Zap,
  Compass,
  ArrowUpRight,
  ArrowDownRight,
  ShieldAlert,
  HelpCircle
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';

interface BenchmarkingTabProps {
  financialData: FinancialData;
  /** Doğrulanmış metrikler; verilirse yerel hesap yerine bunlar kullanılır. */
  audit?: FinansalDenetim | null;
  /** Yüklenen mizan; çok dönemliyse kendi trendi hesaplanır. */
  advancedData?: GelismisAjanGirdisi;
  onNavigateTab?: (tabId: string) => void;
}

interface SectorMetrics {
  grossProfitMargin: number; // %
  netProfitMargin: number;   // %
  debtToEquity: number;      // ratio
  dsoDays: number;           // DSO (Days Sales Outstanding)
  currentRatio: number;      // Liquidity
  inventoryTurnover: number; // times/yr
}

const SECTOR_BENCHMARKS: Record<string, { name: string; avg: SectorMetrics; top10: SectorMetrics; description: string }> = {
  'Teknoloji & Yazılım': {
    name: 'Teknoloji, Yazılım & Bilişim',
    avg: { grossProfitMargin: 48, netProfitMargin: 18, debtToEquity: 0.55, dsoDays: 42, currentRatio: 1.85, inventoryTurnover: 12 },
    top10: { grossProfitMargin: 62, netProfitMargin: 28, debtToEquity: 0.30, dsoDays: 25, currentRatio: 2.40, inventoryTurnover: 18 },
    description: 'Yüksek katma değerli, düşük stok maliyetli, insan kaynağı ağırlıklı KOBİ segmenti.'
  },
  'İmalat & Otomotiv': {
    name: 'İmalat, Otomotiv Yan Sanayi & Sanayi',
    avg: { grossProfitMargin: 24, netProfitMargin: 8, debtToEquity: 1.20, dsoDays: 68, currentRatio: 1.25, inventoryTurnover: 5.2 },
    top10: { grossProfitMargin: 34, netProfitMargin: 15, debtToEquity: 0.70, dsoDays: 45, currentRatio: 1.65, inventoryTurnover: 8.5 },
    description: 'Yüksek makine yatırımı, hammadde stoğu ve uzun vade çek/senet döngüsüne sahip sanayi sektörü.'
  },
  'Perakende & Gıda': {
    name: 'Perakende, FMCG & Gıda Ticareti',
    avg: { grossProfitMargin: 22, netProfitMargin: 5.5, debtToEquity: 0.95, dsoDays: 28, currentRatio: 1.15, inventoryTurnover: 9.8 },
    top10: { grossProfitMargin: 31, netProfitMargin: 10, debtToEquity: 0.50, dsoDays: 14, currentRatio: 1.50, inventoryTurnover: 15.0 },
    description: 'Hızlı stok devir hızı, peşin veya kısa vadeli satış yapısıyla nakit döngüsü güçlü sektör.'
  },
  'Tekstil & Konfeksiyon': {
    name: 'Tekstil, Hazır Giyim & Moda',
    avg: { grossProfitMargin: 28, netProfitMargin: 9, debtToEquity: 1.10, dsoDays: 55, currentRatio: 1.30, inventoryTurnover: 4.8 },
    top10: { grossProfitMargin: 38, netProfitMargin: 17, debtToEquity: 0.60, dsoDays: 35, currentRatio: 1.75, inventoryTurnover: 7.2 },
    description: 'Sezonsallık, ihracat kur riski ve hammadde stok yönetimi kritik olan tekstil KOBİ’leri.'
  },
  'Lojistik & Taşımacılık': {
    name: 'Lojistik, Depolama & Taşımacılık',
    avg: { grossProfitMargin: 19, netProfitMargin: 6.8, debtToEquity: 1.45, dsoDays: 50, currentRatio: 1.10, inventoryTurnover: 14 },
    top10: { grossProfitMargin: 27, netProfitMargin: 12, debtToEquity: 0.85, dsoDays: 30, currentRatio: 1.45, inventoryTurnover: 22 },
    description: 'Yakıt ve araç leasing yükü yüksek, ciro hacmi geniş fakat marj baskılı taşımacılık sektörü.'
  }
};

export const BenchmarkingTab: React.FC<BenchmarkingTabProps> = ({ financialData, audit, advancedData, onNavigateTab }) => {
  const [selectedSectorKey, setSelectedSectorKey] = useState<string>('Teknoloji & Yazılım');

  useEffect(() => {
    const sektor = financialData.sector.toLocaleLowerCase('tr-TR');
    if (sektor.includes('imalat') || sektor.includes('üretim') || sektor.includes('otomotiv')) setSelectedSectorKey('İmalat & Otomotiv');
    else if (sektor.includes('perakende') || sektor.includes('gıda')) setSelectedSectorKey('Perakende & Gıda');
    else if (sektor.includes('tekstil')) setSelectedSectorKey('Tekstil & Konfeksiyon');
    else if (sektor.includes('lojistik') || sektor.includes('taşım')) setSelectedSectorKey('Lojistik & Taşımacılık');
    else if (sektor.includes('yazılım') || sektor.includes('teknoloji') || sektor.includes('bilişim')) setSelectedSectorKey('Teknoloji & Yazılım');
  }, [financialData.sector]);

  const sectorInfo = SECTOR_BENCHMARKS[selectedSectorKey] || SECTOR_BENCHMARKS['Teknoloji & Yazılım'];

  // Metrikler tek kaynaktan gelir (lib/metrikler.ts → api/financial_metrics.py).
  // Ekran içinde aritmetik yapılmaz; aynı metriğin iki farklı sonuç
  // vermesi böyle önlenir.
  const metrikler = finansalMetrikler(financialData, audit);
  const paraBicimle = paraBicimlendirici(financialData.currency);

  // Şirketin kendi geçmişi — mizan çok dönemliyse dolar. Sektör
  // ortalaması "normal miyim?" der; bu "ne değişti?" der ve karar üretir.
  const [kendiTrendi, setKendiTrendi] = useState<KendiTrendi | null>(null);
  const mizanSatirSayisi = advancedData?.mizan?.length ?? 0;

  useEffect(() => {
    if (mizanSatirSayisi === 0 || !advancedData) {
      setKendiTrendi(null);
      return undefined;
    }
    let aktif = true;
    gelismisAjanAnalizi(financialData, advancedData)
      .then((sonuc) => {
        if (aktif) setKendiTrendi(sonuc.ajanlar?.finansal_tablo_mutabakat_ajani?.kendi_trendi ?? null);
      })
      .catch(() => { if (aktif) setKendiTrendi(null); });
    return () => { aktif = false; };
  }, [advancedData, financialData, mizanSatirSayisi]);

  const companyGrossMargin = metrikler.brutKarMarji.deger ?? 0;
  const companyNetMargin = metrikler.netKarMarji.deger ?? 0;
  const companyTotalDebt = financialData.shortTermDebt + financialData.longTermDebt;
  const fullBalanceAvailable = [financialData.currentAssets, financialData.totalAssets, financialData.totalLiabilities]
    .every((value) => value != null);
  const companyDebtToEquity = fullBalanceAvailable ? metrikler.borcOzkaynak.deger : null;
  const companyCurrentRatio = metrikler.cariOran.deger;
  const companyDso = metrikler.alacakDevirGunu.deger == null
    ? null
    : Math.round(metrikler.alacakDevirGunu.deger);

  // DSO 10 gün kısalırsa serbest kalan tutar. Günlük ciro dönem gün
  // sayısından gelir; 365 varsayılmaz.
  const dsoKisaltmaEtkisi = metrikler.gunlukCiro.deger == null
    ? null
    : metrikler.gunlukCiro.deger * 10;

  // Kârlılık yorumu hesaplanan sonuca bağlıdır; her durumda "güçlü" denmez.
  const netMarjFarki = companyNetMargin - sectorInfo.avg.netProfitMargin;
  const karlilikDurumu = companyNetMargin < 0
    ? 'zarar'
    : netMarjFarki >= 0
      ? 'guclu'
      : 'geride';

  // Recharts Data Structure
  const comparisonData = [
    {
      metric: 'Brüt Kâr Marjı (%)',
      Sirketiniz: Number(companyGrossMargin.toFixed(1)),
      SektorOrtalamasi: sectorInfo.avg.grossProfitMargin,
      SektorLiderleri: sectorInfo.top10.grossProfitMargin,
    },
    {
      metric: 'Net Kâr Marjı (%)',
      Sirketiniz: Number(companyNetMargin.toFixed(1)),
      SektorOrtalamasi: sectorInfo.avg.netProfitMargin,
      SektorLiderleri: sectorInfo.top10.netProfitMargin,
    },
    ...(companyCurrentRatio == null ? [] : [{
      metric: 'Cari Oran (Likidite)',
      Sirketiniz: Number((companyCurrentRatio * 10).toFixed(1)), // Scaled x10 for chart readability
      SektorOrtalamasi: Number((sectorInfo.avg.currentRatio * 10).toFixed(1)),
      SektorLiderleri: Number((sectorInfo.top10.currentRatio * 10).toFixed(1)),
      actualCompany: Number(companyCurrentRatio.toFixed(2)),
      actualAvg: Number(sectorInfo.avg.currentRatio.toFixed(2)),
      actualTop: Number(sectorInfo.top10.currentRatio.toFixed(2)),
    }]),
  ];

  // Radar chart normalized metrics (0-100 scale)
  const radarData = [
    {
      subject: 'Kârlılık',
      Sirketiniz: Math.min(100, Math.round((companyNetMargin / sectorInfo.top10.netProfitMargin) * 80)),
      SektorOrtalamasi: 50,
      SektorLideri: 90,
    },
    ...(companyCurrentRatio == null ? [] : [{
      subject: 'Likidite (Cari Oran)',
      Sirketiniz: Math.min(100, Math.round((companyCurrentRatio / sectorInfo.top10.currentRatio) * 80)),
      SektorOrtalamasi: 50,
      SektorLideri: 90,
    }]),
    ...(companyDebtToEquity == null ? [] : [{
      subject: 'Borç Yönetimi',
      Sirketiniz: Math.min(100, Math.round((sectorInfo.avg.debtToEquity / (companyDebtToEquity || 0.1)) * 50)),
      SektorOrtalamasi: 50,
      SektorLideri: 85,
    }]),
    ...(companyDso == null ? [] : [{
      subject: 'Tahsilat Hızı (DSO)',
      Sirketiniz: Math.min(100, Math.round((sectorInfo.avg.dsoDays / (companyDso || 1)) * 60)),
      SektorOrtalamasi: 50,
      SektorLideri: 85,
    }]),
    {
      subject: 'Sermaye Gücü',
      Sirketiniz: Math.min(100, Math.round((financialData.equity / (financialData.revenue * 0.8 || 1)) * 100)),
      SektorOrtalamasi: 55,
      SektorLideri: 88,
    },
  ];

  // Overall Score Calculation
  const scoreRatios = [
    companyGrossMargin / sectorInfo.avg.grossProfitMargin,
    companyNetMargin / sectorInfo.avg.netProfitMargin,
    ...(companyCurrentRatio == null ? [] : [companyCurrentRatio / sectorInfo.avg.currentRatio]),
    ...(companyDso == null ? [] : [sectorInfo.avg.dsoDays / Math.max(companyDso, 1)]),
  ];
  const scoreIsReady = scoreRatios.length >= 3;
  const score = scoreIsReady
    ? Math.round(scoreRatios.reduce((sum, ratio) => sum + ratio, 0) / scoreRatios.length * 100)
    : null;
  const normalizedScore = score == null ? null : Math.min(100, Math.max(0, score));

  return (
    <div className="space-y-6">
      {/* Kendi geçmişiyle karşılaştırma — sektör kartlarından önce gelir. */}
      <KendiTrendin
        trend={kendiTrendi}
        paraBirimi={financialData.currency}
        onNavigateTab={onNavigateTab ?? (() => {})}
      />

      {/* Page Header */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="bg-purple-100 text-purple-800 text-[10px] font-extrabold px-2 py-0.5 rounded uppercase">
              Referans Benchmark
            </span>
            <h2 className="text-lg font-bold text-slate-900">Piyasa Karşılaştırma ve Rekabet Analizi</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Şirketinizin kârlılık, borçluluk ve likidite performansını ürün içi referans eşikleriyle karşılaştırın.
          </p>
        </div>

        {/* Sector Selector Controls */}
          <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 p-1.5 rounded-xl text-xs">
            <Building2 className="w-4 h-4 text-slate-500 ml-1" />
            <select
              value={selectedSectorKey}
              onChange={(e) => setSelectedSectorKey(e.target.value)}
              className="bg-transparent font-bold text-slate-800 outline-none cursor-pointer pr-2"
            >
              {Object.keys(SECTOR_BENCHMARKS).map((key) => (
                <option key={key} value={key}>{key}</option>
              ))}
            </select>
          </div>

            <span className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-[10px] font-bold text-slate-500">Pilot sektör profili · ölçek filtresi yok</span>
          </div>
      </div>

      <div className="flex items-start gap-3 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
        <HelpCircle className="mt-0.5 h-4 w-4 shrink-0 text-amber-700" />
        <p>
          <strong>Bu eşikler ürün içi başlangıç referansıdır.</strong> Bağımsız bir kaynaktan
          gelmez; yayın tarihi, örneklem büyüklüğü ve şirket ölçeği bilgisi yoktur, bu yüzden
          "sektör ortalaması" değildir. Asıl karşılaştırma yukarıdaki kendi trendinizdir —
          geçmiş dönem yüklendikçe bu eşiklere ihtiyaç azalır.
        </p>
      </div>

      {/* Sector Summary Card & Competitive Score */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Competitive Score Card */}
        <div className="bg-slate-900 text-white p-5 rounded-xl shadow-sm relative overflow-hidden flex flex-col justify-between">
          <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-2xl pointer-events-none"></div>

          <div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-extrabold uppercase tracking-wider text-blue-400 bg-blue-950/80 px-2.5 py-1 rounded-md border border-blue-800">
                Referans Uyum Skoru
              </span>
              <Award className="w-5 h-5 text-amber-400" />
            </div>

            <div className="mt-4 flex items-baseline gap-3">
              <span className="text-4xl font-extrabold tracking-tight">{normalizedScore ?? '—'}</span>
              <span className="text-xs text-slate-400 font-medium">{normalizedScore == null ? 'veri gerekli' : '/ 100 Puan'}</span>
            </div>

            <p className="text-xs text-slate-300 mt-2 font-medium">
              {normalizedScore == null ? (
                <span className="text-amber-300 font-bold"> Skor için en az üç doğrulanmış karşılaştırma metriği gerekli.</span>
              ) : normalizedScore >= 75 ? (
                <span className="text-emerald-400 font-bold"> Pilot referans eşiklerinin üzerinde görünüyorsunuz.</span>
              ) : normalizedScore >= 55 ? (
                <span className="text-blue-400 font-bold"> Ürün içi referans eşiğinin üzerinde.</span>
              ) : (
                <span className="text-amber-400 font-bold"> Ürün içi referans eşiğinin altında.</span>
              )}
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800/80 text-[11px] text-slate-400 space-y-1">
            <div className="flex justify-between">
              <span>Seçili Sektör:</span>
              <span className="text-white font-semibold">{sectorInfo.name}</span>
            </div>
            <div className="flex justify-between">
              <span>Şirket Verisi:</span>
              <span className="text-emerald-400 font-semibold">{financialData.companyName}</span>
            </div>
          </div>
        </div>

        {/* Sector Description & Key Averages */}
        <div className="lg:col-span-2 bg-white p-5 rounded-xl border border-slate-200 shadow-xs flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Compass className="w-4 h-4 text-blue-600" />
              <h3 className="text-sm font-bold text-slate-900">Referans Profil ve Karşılaştırma Özeti</h3>
            </div>
            <p className="text-xs text-slate-500">{sectorInfo.description}</p>
          </div>

          {/* Quick Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
              <span className="text-[10px] font-bold text-slate-400 uppercase block">Brüt Kâr Marjı</span>
              <div className="flex items-baseline gap-1 mt-1">
                <span className="text-sm font-extrabold text-slate-900">%{companyGrossMargin.toFixed(1)}</span>
                <span className="text-[10px] text-slate-500">vs %{sectorInfo.avg.grossProfitMargin} referans</span>
              </div>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
              <span className="text-[10px] font-bold text-slate-400 uppercase block">Net Kâr Marjı</span>
              <div className="flex items-baseline gap-1 mt-1">
                <span className="text-sm font-extrabold text-slate-900">%{companyNetMargin.toFixed(1)}</span>
                <span className="text-[10px] text-slate-500">vs %{sectorInfo.avg.netProfitMargin} referans</span>
              </div>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
              <span className="text-[10px] font-bold text-slate-400 uppercase block">Tahsilat Süresi (DSO)</span>
              <div className="flex items-baseline gap-1 mt-1">
                <span className={`text-sm font-extrabold ${companyDso != null && companyDso <= sectorInfo.avg.dsoDays ? 'text-emerald-700' : 'text-amber-700'}`}>
                  {companyDso == null ? 'Veri gerekli' : `${companyDso} Gün`}
                </span>
                <span className="text-[10px] text-slate-500">vs {sectorInfo.avg.dsoDays} Gün</span>
              </div>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
              <span className="text-[10px] font-bold text-slate-400 uppercase block">Cari Oran</span>
              <div className="flex items-baseline gap-1 mt-1">
                <span className="text-sm font-extrabold text-slate-900">{companyCurrentRatio == null ? 'Veri gerekli' : `${companyCurrentRatio.toFixed(2)}x`}</span>
                <span className="text-[10px] text-slate-500">vs {sectorInfo.avg.currentRatio}x</span>
              </div>
            </div>
          </div>

          <div className="p-2.5 bg-blue-50 border border-blue-100 rounded-lg text-xs text-blue-900 flex items-center gap-2">
            <Zap className="w-4 h-4 text-blue-600 shrink-0" />
            <span><strong>CFO Notu:</strong> Net kâr marjınız seçili referans ortalamasıyla karşılaştırılmıştır. Sonucu veri kalitesi ve şirketinizin dönemsel koşullarıyla birlikte değerlendirin.</span>
          </div>
        </div>
      </div>

      {/* Visual Benchmarking Charts: Bar Chart & Radar Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

        {/* Bar Chart: Metric Comparison */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-blue-600" />
                Şirketiniz vs referans ortalama vs güçlü performans eşiği
              </h3>
              <p className="text-xs text-slate-500">Temel finansal rasyoların sektörel normlar ile kıyası</p>
            </div>
          </div>

          <div className="h-64 w-full pt-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparisonData} margin={{ top: 10, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                <XAxis dataKey="metric" tick={{ fontSize: 11, fill: '#64748B' }} />
                <YAxis tick={{ fontSize: 11, fill: '#64748B' }} />
                <Tooltip
                  formatter={(val: any, name: any) => [`${val}`, name === 'Sirketiniz' ? 'Şirketiniz' : name === 'SektorOrtalamasi' ? 'Referans ortalama' : 'Güçlü performans eşiği']}
                  contentStyle={{ borderRadius: '12px', fontSize: '12px', border: '1px solid #E2E8F0' }}
                />
                <Legend
                  formatter={(value) => {
                    const map: Record<string, string> = {
                      Sirketiniz: 'Şirketiniz',
                      SektorOrtalamasi: 'Referans ortalama',
                      SektorLiderleri: 'Güçlü performans eşiği'
                    };
                    return <span className="text-xs font-semibold text-slate-700">{map[value] || value}</span>;
                  }}
                />
                <Bar dataKey="Sirketiniz" fill="#2563EB" radius={[4, 4, 0, 0]} />
                <Bar dataKey="SektorOrtalamasi" fill="#94A3B8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="SektorLiderleri" fill="#10B981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Radar Chart: Multidimensional Competitive Profile */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Target className="w-4 h-4 text-purple-600" />
                Çok Boyutlu Finansal Sağlık Radarı
              </h3>
              <p className="text-xs text-slate-500">Yalnızca hesaplanabilen finansal boyutlarda güç ve zayıflık haritası</p>
            </div>
          </div>

          <div className="h-64 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                <PolarGrid stroke="#E2E8F0" />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: '#475569', fontWeight: 600 }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} />
                <Radar name="Şirketiniz" dataKey="Sirketiniz" stroke="#2563EB" fill="#2563EB" fillOpacity={0.4} />
                <Radar name="Referans ortalama" dataKey="SektorOrtalamasi" stroke="#94A3B8" fill="#94A3B8" fillOpacity={0.2} />
                <Radar name="Güçlü performans eşiği" dataKey="SektorLideri" stroke="#10B981" fill="#10B981" fillOpacity={0.15} />
                <Legend
                  formatter={(value) => <span className="text-xs font-semibold text-slate-700">{value}</span>}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

      {/* Strategic Benchmarking Gap Analysis & Actions */}
      <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-emerald-600" />
          Referans Fark Analizi ve İncelenecek Aksiyonlar
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Item 1 */}
          <div className={`p-4 border rounded-xl space-y-2 ${
            karlilikDurumu === 'guclu'
              ? 'bg-emerald-50/60 border-emerald-200'
              : karlilikDurumu === 'geride'
                ? 'bg-amber-50/60 border-amber-200'
                : 'bg-red-50/60 border-red-200'
          }`}>
            <div className={`flex items-center gap-2 font-bold text-xs ${
              karlilikDurumu === 'guclu'
                ? 'text-emerald-800'
                : karlilikDurumu === 'geride' ? 'text-amber-900' : 'text-red-900'
            }`}>
              {karlilikDurumu === 'guclu'
                ? <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                : <AlertTriangle className={`w-4 h-4 shrink-0 ${karlilikDurumu === 'geride' ? 'text-amber-600' : 'text-red-600'}`} />}
              <span>
                {karlilikDurumu === 'guclu'
                  ? 'Güçlü Alan: Net Kâr Marjı'
                  : karlilikDurumu === 'geride'
                    ? 'Gelişime Açık: Net Kâr Marjı'
                    : 'Kritik: Dönem Zararı'}
              </span>
            </div>
            <p className="text-xs text-slate-700">
              {karlilikDurumu === 'zarar' ? (
                <>Şirketiniz incelenen dönemde <strong>%{Math.abs(companyNetMargin).toFixed(1)}</strong> oranında zarar etti. Referans değerle karşılaştırma yapılmadan önce negatif katkı marjlı ürün ve gider kalemlerini ayırın.</>
              ) : karlilikDurumu === 'geride' ? (
                <>Net Kâr Marjınız (<strong>%{companyNetMargin.toFixed(1)}</strong>), seçili referans değerin (<strong>%{sectorInfo.avg.netProfitMargin}</strong>) <strong>{Math.abs(netMarjFarki).toFixed(1)} puan</strong> altında. Fiyatlama ve gider kalemlerini dönemsel etkilerle birlikte gözden geçirin.</>
              ) : (
                <>Net Kâr Marjınız (<strong>%{companyNetMargin.toFixed(1)}</strong>), seçili referans değerin (<strong>%{sectorInfo.avg.netProfitMargin}</strong>) <strong>{netMarjFarki.toFixed(1)} puan</strong> üzerinde. Gider kalemlerini dönemsel etkilerle birlikte doğrulayın.</>
              )}
            </p>
          </div>

          {/* Item 2 */}
          <div className="p-4 bg-amber-50/60 border border-amber-200 rounded-xl space-y-2">
            <div className="flex items-center gap-2 text-amber-900 font-bold text-xs">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
              <span>Gelişime Açık: Tahsilat Süresi (DSO)</span>
            </div>
            <p className="text-xs text-slate-700">
              {companyDso == null
                ? 'Bilanço ve ticari alacak verisi olmadan tahsilat karşılaştırması yapılmaz.'
                : <>Alacak tahsilat süreniz <strong>{companyDso} gün</strong>. Referans değer <strong>{sectorInfo.avg.dsoDays} gün</strong>.{dsoKisaltmaEtkisi != null && <> DSO süresi 10 gün kısalırsa yaklaşık <strong>{paraBicimle(dsoKisaltmaEtkisi)}</strong> likidite etkisi oluşabilir ({financialData.periodDays} günlük dönem üzerinden).</>}</>}
            </p>
          </div>

          {/* Item 3 */}
          <div className="p-4 bg-blue-50/60 border border-blue-200 rounded-xl space-y-2">
            <div className="flex items-center gap-2 text-blue-900 font-bold text-xs">
              <Zap className="w-4 h-4 text-blue-600 shrink-0" />
              <span>Stratejik Hedef: Borç Yapısı</span>
            </div>
            <p className="text-xs text-slate-700">
              {companyDebtToEquity == null
                ? 'Borç ve özkaynak kalemleri doğrulanmadan sermaye yapısı karşılaştırması yapılmaz.'
                : <>Borç / Özkaynak oranınız <strong>{companyDebtToEquity.toFixed(2)}x</strong>, referans eşik <strong>{sectorInfo.top10.debtToEquity}x</strong>. Bu oranı yalnızca borcu azaltmak veya özkaynağı güçlendirmek değiştirir; kısa vadeli borcu uzun vadeye yaymak toplam borcu değiştirmediği için oranı da değiştirmez. Vade uzatma likiditeyi ve ödeme takvimini rahatlatır — etkisini cari oran{companyCurrentRatio != null && <> (<strong>{companyCurrentRatio.toFixed(2)}x</strong>)</>} ve borç servis kapasitesi üzerinden değerlendirin.</>}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

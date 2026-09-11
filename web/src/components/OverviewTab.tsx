import React, { useEffect, useMemo, useState } from 'react';
import {
  ArrowRight,
  Bot,
  Calculator,
  CheckCircle2,
  CircleAlert,
  Database,
  FileCheck2,
  FileSpreadsheet,
  Gauge,
  Landmark,
  Layers3,
  ShieldCheck,
  TrendingUp,
  WalletCards,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { FinansalDenetim, SaglikSkoru } from '../lib/api';
import { CashFlowItem, CustomerRisk, FinancialData } from '../types';
import { DurumOzeti } from './DurumOzeti';

interface OverviewTabProps {
  data: FinancialData;
  cashFlow: CashFlowItem[];
  customers: CustomerRisk[];
  audit?: FinansalDenetim | null;
  /** Zaman serisinden hesaplanan sağlık skoru; yoksa kart gösterilmez. */
  healthScore?: SaglikSkoru | null;
  isSampleData?: boolean;
  onNavigateTab: (tab: string) => void;
}

const formatMoney = (value: number, currency: string) => new Intl.NumberFormat('tr-TR', {
  style: 'currency',
  currency: currency === '₺' ? 'TRY' : currency,
  maximumFractionDigits: 0,
}).format(value);

const formatPercent = (value: number | null) => value == null
  ? 'Veri gerekli'
  : `%${value.toLocaleString('tr-TR', { maximumFractionDigits: 1 })}`;

const formatMultiple = (value: number | null) => value == null
  ? 'Veri gerekli'
  : `${value.toLocaleString('tr-TR', { maximumFractionDigits: 2 })}x`;

const AnimatedMetric: React.FC<{
  value: number | null;
  formatter: (value: number) => string;
  fallback: string;
}> = ({ value, formatter, fallback }) => {
  const [display, setDisplay] = useState(value == null ? fallback : formatter(0));

  useEffect(() => {
    if (value == null) {
      setDisplay(fallback);
      return undefined;
    }
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setDisplay(formatter(value));
      return undefined;
    }

    let frame = 0;
    const startedAt = performance.now();
    const duration = 900;
    const tick = (now: number) => {
      const progress = Math.min(1, (now - startedAt) / duration);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(formatter(value * eased));
      if (progress < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [fallback, formatter, value]);

  return <>{display}</>;
};

const kurumsalEtiketler: Record<string, { etiket: string; aciklama: string }> = {
  altman_z_prime: { etiket: "Altman Z'", aciklama: 'Özel imalat şirketleri için finansal sıkıntı göstergesi' },
  dupont_roe: { etiket: 'DuPont ROE', aciklama: 'Kârlılık, varlık devri ve kaldıraç ayrıştırması' },
  roic: { etiket: 'ROIC', aciklama: 'Yatırılan sermayenin vergi sonrası operasyonel getirisi' },
  serbest_nakit_akisi: { etiket: 'Serbest Nakit Akışı', aciklama: 'Operasyonel nakit akışı eksi yatırım harcamaları' },
  nakit_donusum_dongusu: { etiket: 'Nakit Dönüşüm Döngüsü', aciklama: 'DSO + DIO − DPO ile çalışma sermayesi süresi' },
  musteri_hhi: { etiket: 'Müşteri HHI', aciklama: 'Müşteri cirosunun yoğunlaşma göstergesi' },
};

const alanEtiketleri: Record<string, string> = {
  donen_varliklar: 'Dönen varlıklar',
  toplam_varliklar: 'Toplam varlıklar',
  toplam_yukumlulukler: 'Toplam yükümlülükler',
  dagitilmamis_karlar: 'Dağıtılmamış kârlar',
  ebit: 'Faiz ve vergi öncesi kâr',
  etkin_vergi_orani: 'Etkin vergi oranı',
  yatirilan_sermaye: 'Yatırılan sermaye bileşenleri',
  operasyonel_nakit_akisi: 'Operasyonel nakit akışı',
  capex: 'CapEx',
  donem_gun_sayisi: 'Dönem gün sayısı',
  ciro: 'Ciro',
  satis_maliyeti: 'Satış maliyeti',
  musteri_sayisi: 'Müşteri bazlı ciro',
  toplam_musteri_cirosu: 'Toplam müşteri cirosu',
};

export const OverviewTab: React.FC<OverviewTabProps> = ({
  data,
  cashFlow,
  customers,
  audit,
  healthScore,
  isSampleData = false,
  onNavigateTab,
}) => {
  const [timeRange, setTimeRange] = useState<'6m' | '12m'>('12m');
  const formatTRY = (value: number) => formatMoney(value, data.currency);

  const grossMargin = data.revenue > 0 ? data.grossProfit / data.revenue * 100 : null;
  const netMargin = data.revenue > 0 ? data.netProfit / data.revenue * 100 : null;
  const ebitdaAvailable = data.dataQuality?.ebitdaAvailable !== false;
  const fullBalanceAvailable = [data.currentAssets, data.totalAssets, data.totalLiabilities]
    .every((value) => value != null);

  const currentRatio = audit?.metrikler.cari_oran
    ?? (data.currentAssets != null && data.shortTermDebt > 0
      ? data.currentAssets / data.shortTermDebt
      : null);
  const narrowLiquidity = currentRatio == null && data.shortTermDebt > 0
    ? (data.cashInHand + data.receivables) / data.shortTermDebt
    : null;
  const debtToEquity = audit?.metrikler.borc_ozkaynak_orani
    ?? (data.equity > 0 ? (data.shortTermDebt + data.longTermDebt) / data.equity : null);
  const dsoDays = data.periodDays && data.revenue > 0
    ? data.receivables / data.revenue * data.periodDays
    : null;

  const calculatedNetProfit = ebitdaAvailable
    ? data.ebitda - data.depreciation - data.interestExpense - data.taxExpense
    : null;
  const reconciliationDifference = calculatedNetProfit == null
    ? null
    : data.netProfit - calculatedNetProfit;
  const reconciliationTolerance = Math.max(Math.abs(data.netProfit) * 0.001, 1);
  const reconciles = reconciliationDifference != null
    && Math.abs(reconciliationDifference) <= reconciliationTolerance;

  const leadingCustomer = [...customers].sort((a, b) => b.sharePercentage - a.sharePercentage)[0];
  const negativeCashPeriod = [...cashFlow].reverse().find((item) => item.netCash < 0);

  const readinessAreas = [
    { name: 'Gelir tablosu', ready: data.revenue > 0 && data.costOfGoods >= 0, detail: 'Ciro, satış maliyeti ve net kâr' },
    { name: 'Bilanço', ready: fullBalanceAvailable, detail: 'Dönen/toplam varlık ve yükümlülük' },
    { name: 'Nakit hareketi', ready: cashFlow.length > 0, detail: 'Dönemsel giriş, çıkış ve net nakit' },
    { name: 'Müşteri ve alacak', ready: customers.length > 0 || Boolean(data.customerRevenues?.length), detail: 'Müşteri bazlı tutar ve ödeme bilgisi' },
    {
      name: 'Nakit köprüsü',
      ready: [data.beginningCash, data.operatingCashFlow, data.investingCashFlow, data.financingCashFlow]
        .every((value) => value != null),
      detail: 'Başlangıç, faaliyet, yatırım ve finansman',
    },
    { name: 'Sürümlü formüller', ready: Boolean(audit?.metrik_kaydi), detail: 'Formül kimliği, girdi ve güven kaydı' },
  ];
  const readyCount = readinessAreas.filter((area) => area.ready).length;
  const readinessScore = Math.round(readyCount / readinessAreas.length * 100);

  const missingInputs = useMemo(() => {
    const fields: string[] = [];
    if (data.currentAssets == null) fields.push('Dönen varlıklar');
    if (data.totalAssets == null) fields.push('Toplam varlıklar');
    if (data.totalLiabilities == null) fields.push('Toplam yükümlülükler');
    if (data.periodDays == null) fields.push('Dönem gün sayısı');
    if (data.operatingCashFlow == null) fields.push('Operasyonel nakit akışı');
    if (!data.customerRevenues?.length) fields.push('Müşteri bazlı ciro');
    if (!cashFlow.length) fields.push('Dönemsel nakit hareketi');
    return fields;
  }, [cashFlow.length, data]);

  const pnlChartData = [
    { name: 'Ciro', value: data.revenue / 1_000_000 },
    { name: 'Brüt Kâr', value: data.grossProfit / 1_000_000 },
    ...(ebitdaAvailable ? [{ name: 'FAVÖK', value: data.ebitda / 1_000_000 }] : []),
    { name: 'Net Kâr', value: data.netProfit / 1_000_000 },
  ];

  const cashTrendData = (timeRange === '6m' ? cashFlow.slice(-6) : cashFlow.slice(-12)).map((item) => ({
    ay: item.month,
    giris: item.inflow / 1_000_000,
    cikis: item.outflow / 1_000_000,
    net: item.netCash / 1_000_000,
  }));

  const metricRecords = audit?.metrik_kaydi
    ? Object.entries(audit.metrik_kaydi).filter(([name]) => kurumsalEtiketler[name])
    : [];
  const missingCorporateFields = [...new Set(
    metricRecords.flatMap(([, metric]) => metric.durum === 'eksik_veri' ? metric.eksik_alanlar : []),
  )];

  const corporateValue = (value: number, unit: string) => {
    if (unit === 'TRY') return formatTRY(value);
    if (unit === '%') return formatPercent(value);
    if (unit === 'gün') return `${value.toLocaleString('tr-TR', { maximumFractionDigits: 1 })} gün`;
    return value.toLocaleString('tr-TR', { maximumFractionDigits: 2 });
  };

  const decisionQueue = [
    {
      title: 'Kâr mutabakatı',
      status: calculatedNetProfit == null ? 'Veri gerekli' : reconciles ? 'Mutabık' : 'İnceleme',
      description: calculatedNetProfit == null
        ? 'FAVÖK ayrıştırılmadığı için net kâr köprüsü kurulamadı.'
        : reconciles
          ? `Girilen net kâr ile hesaplanan net kâr arasındaki fark ${formatTRY(reconciliationDifference ?? 0)}.`
          : `Girilen ve hesaplanan net kâr arasında ${formatTRY(Math.abs(reconciliationDifference ?? 0))} fark var.`,
      tone: calculatedNetProfit != null && reconciles ? 'emerald' : 'amber',
      tab: 'data-entry',
    },
    {
      title: 'Likidite hesabı',
      status: currentRatio != null ? 'Cari oran' : narrowLiquidity != null ? 'Dar görünüm' : 'Veri gerekli',
      description: currentRatio != null
        ? `Dönen varlıklar / kısa vadeli borç: ${formatMultiple(currentRatio)}.`
        : narrowLiquidity != null
          ? `(Nakit + alacak) / kısa vadeli borç: ${formatMultiple(narrowLiquidity)}. Bu değer cari oran değildir.`
          : 'Likidite oranı için bilanço kalemleri tamamlanmalı.',
      tone: 'blue',
      tab: 'cashflow',
    },
    {
      title: 'Nakit dönemleri',
      status: cashFlow.length ? `${cashFlow.length} dönem` : 'Veri gerekli',
      description: negativeCashPeriod
        ? `${negativeCashPeriod.month} döneminde net nakit ${formatTRY(negativeCashPeriod.netCash)} olarak gözlendi.`
        : cashFlow.length
          ? 'Yüklenen dönemlerde negatif net nakit gözlenmedi.'
          : 'Nakit giriş ve çıkış serisi yüklenmedi.',
      tone: negativeCashPeriod ? 'amber' : 'emerald',
      tab: 'cashflow',
    },
    {
      title: 'Müşteri görünümü',
      status: leadingCustomer ? 'Gözlem hazır' : 'Veri gerekli',
      description: leadingCustomer
        ? `${leadingCustomer.name}, yüklenen müşteri tutarlarının %${leadingCustomer.sharePercentage.toLocaleString('tr-TR', { maximumFractionDigits: 1 })}'ini oluşturuyor.`
        : 'Yoğunlaşma analizi için müşteri/fatura bazlı veri gerekli.',
      tone: 'violet',
      tab: 'customer',
    },
  ];

  const kpis = [
    { label: 'Dönem cirosu', value: data.revenue, formatter: formatTRY, fallback: formatTRY(data.revenue), note: `${data.period} · girilen değer`, icon: TrendingUp },
    { label: 'Net kâr', value: data.netProfit, formatter: formatTRY, fallback: formatTRY(data.netProfit), note: `Net marj ${formatPercent(netMargin)}`, icon: Calculator },
    {
      label: currentRatio != null ? 'Cari oran' : 'Dar likidite',
      value: currentRatio ?? narrowLiquidity,
      formatter: (value: number) => formatMultiple(value),
      fallback: formatMultiple(currentRatio ?? narrowLiquidity),
      note: currentRatio != null ? 'Dönen varlık / kısa vadeli borç' : 'Nakit + alacak / kısa vadeli borç',
      icon: Gauge,
    },
    { label: 'Nakit mevcudu', value: data.cashInHand, formatter: formatTRY, fallback: formatTRY(data.cashInHand), note: `Kısa vadeli borç ${formatTRY(data.shortTermDebt)}`, icon: WalletCards },
  ];

  return (
    <div className="overview-panel space-y-5 pb-8">
      <section className="flex flex-col gap-3 rounded-xl border border-violet-200 bg-gradient-to-r from-[#eef2ff] to-[#f5f3ff] px-4 py-3 shadow-sm sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-[#0f2252] to-[#7c3aed] text-sm text-white">✓</span>
          <div>
            <p className="text-sm font-bold text-[#0f2252]">Finansal çalışma alanı hazır</p>
            <p className="mt-0.5 text-[11px] text-slate-500">{readyCount}/{readinessAreas.length} veri alanı analiz için kullanılabilir · sonuçlar yalnızca yüklenen girdilere dayanır.</p>
          </div>
        </div>
        <button type="button" onClick={() => onNavigateTab('cfo-agent')} className="inline-flex items-center gap-2 text-xs font-extrabold text-violet-700 transition hover:text-violet-900">AI bulgularını aç <ArrowRight className="h-3.5 w-3.5" /></button>
      </section>

      {/* Motorun ürettiği risk ve aksiyonlar — detay bölümlerinden önce gelir. */}
      <DurumOzeti audit={audit} healthScore={healthScore} onNavigateTab={onNavigateTab} />

      <section className="panel-card p-5 sm:p-6">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
          <div className="max-w-3xl">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span className="panel-kicker">Finansal karar merkezi</span>
              <span className={`rounded-full border px-2.5 py-1 text-[9px] font-black uppercase tracking-[0.14em] ${isSampleData ? 'border-amber-200 bg-amber-50 text-amber-700' : 'border-emerald-200 bg-emerald-50 text-emerald-700'}`}>{isSampleData ? 'Örnek veri' : 'Şirket verisi'}</span>
            </div>
            <h1 className="text-2xl font-black tracking-[-0.035em] text-[#0a1628] sm:text-3xl">{data.companyName}</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Rakamlar, veri kapsamı ve kontrol durumu aynı ekranda. Eksik girdiler kesin öneriye dönüştürülmez.</p>
            <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-xs font-medium text-slate-500">
              <span className="flex items-center gap-2"><Landmark className="h-4 w-4 text-violet-600" />{data.sector}</span>
              <span className="flex items-center gap-2"><Layers3 className="h-4 w-4 text-indigo-600" />{data.period}</span>
              <span className="flex items-center gap-2"><Database className="h-4 w-4 text-blue-600" />{data.currency}</span>
            </div>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <button type="button" onClick={() => onNavigateTab('data-entry')} className="panel-secondary-button"><FileSpreadsheet className="h-4 w-4" /> Veriyi güncelle</button>
            <button type="button" onClick={() => onNavigateTab('cfo-agent')} className="panel-primary-button"><Bot className="h-4 w-4" /> AI CFO'ya sor</button>
          </div>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {kpis.map((kpi, index) => {
          const Icon = kpi.icon;
          const accent = ['#0f2252', '#7c3aed', '#2563eb', '#059669'][index];
          return (
            <article key={kpi.label} className="panel-card panel-kpi-card relative overflow-hidden p-5 transition duration-200 hover:-translate-y-0.5 hover:shadow-[0_12px_28px_rgba(15,34,82,.09)]">
              <span className="absolute inset-y-0 left-0 w-1" style={{ backgroundColor: accent }} />
              <div className="flex items-center justify-between gap-3">
                <p className="text-[10px] font-extrabold uppercase tracking-[0.13em] text-slate-500">{kpi.label}</p>
                <span className="rounded-lg bg-slate-100 p-2 text-violet-700"><Icon className="h-4 w-4" /></span>
              </div>
              <p className="mt-4 break-words text-2xl font-black tracking-[-0.025em] text-[#0a1628]"><AnimatedMetric value={kpi.value} formatter={kpi.formatter} fallback={kpi.fallback} /></p>
              <p className="mt-2 text-[11px] leading-4 text-slate-500">{kpi.note}</p>
            </article>
          );
        })}
      </section>

      <section className="grid gap-5 xl:grid-cols-[1.45fr_.85fr]">
        <article className="panel-card p-5">
          <div className="flex flex-col gap-2 border-b border-slate-200 pb-4 sm:flex-row sm:items-end sm:justify-between">
            <div><p className="panel-kicker">Gelir tablosu</p><h2 className="mt-2 text-lg font-bold text-[#0a1628]">Kârlılık yapısı</h2><p className="mt-1 text-xs text-slate-500">Tek dönem kalemleri · milyon {data.currency}</p></div>
            <span className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-bold text-slate-600">{data.period}</span>
          </div>
          <div className="mt-5 h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={pnlChartData} margin={{ top: 10, right: 8, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8eaf0" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} unit="M" />
                <Tooltip formatter={(value) => [`${Number(value).toLocaleString('tr-TR', { maximumFractionDigits: 2 })} M ${data.currency}`, 'Tutar']} contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px', fontSize: '12px', color: '#0f172a', boxShadow: '0 12px 28px rgba(15,34,82,.12)' }} />
                <Bar dataKey="value" fill="#7c3aed" radius={[7, 7, 0, 0]} isAnimationActive animationBegin={180} animationDuration={900} animationEasing="ease-out" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-3 flex items-start gap-2 rounded-xl border border-blue-100 bg-blue-50 p-3 text-[11px] leading-5 text-blue-800"><CircleAlert className="mt-0.5 h-4 w-4 shrink-0 text-blue-600" />Bu grafik büyüme trendi değildir. Yalnızca {data.period} döneminde girilen gelir tablosu kalemlerini karşılaştırır.</p>
        </article>

        <article className="panel-card p-5">
          <div className="flex items-center justify-between border-b border-slate-200 pb-4">
            <div><p className="panel-kicker">AI destekli kontrol</p><h2 className="mt-2 text-lg font-bold text-[#0a1628]">Öncelikli bulgular</h2></div>
            <span className="panel-ai-pulse grid h-9 w-9 place-items-center rounded-lg bg-[#0f2252] text-white"><Bot className="h-4 w-4" /></span>
          </div>
          <div className="divide-y divide-slate-100">
            {decisionQueue.slice(0, 3).map((item) => (
              <button key={item.title} type="button" onClick={() => onNavigateTab(item.tab)} className="panel-ai-finding group block w-full py-4 text-left">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-bold text-slate-800">{item.title}</p>
                  <span className={`rounded-full px-2 py-1 text-[9px] font-extrabold uppercase tracking-wide ${item.tone === 'emerald' ? 'bg-emerald-50 text-emerald-700' : item.tone === 'blue' ? 'bg-blue-50 text-blue-700' : item.tone === 'violet' ? 'bg-violet-50 text-violet-700' : 'bg-amber-50 text-amber-700'}`}>{item.status}</span>
                </div>
                <p className="mt-2 text-[11px] leading-5 text-slate-500">{item.description}</p>
                <span className="mt-2 inline-flex items-center gap-1 text-[10px] font-bold text-violet-700 opacity-0 transition group-hover:opacity-100">Detayı aç <ArrowRight className="h-3 w-3" /></span>
              </button>
            ))}
          </div>
          <button type="button" onClick={() => onNavigateTab('cfo-agent')} className="mt-2 w-full rounded-xl bg-[#0f2252] px-4 py-3 text-xs font-extrabold text-white transition hover:bg-[#1b3a6b]">Tüm bulguları açıklat</button>
        </article>
      </section>

      <section className="grid gap-5 xl:grid-cols-[.9fr_1.1fr]">
        <article className="panel-card p-5">
          <div className="flex items-start justify-between gap-5">
            <div><p className="panel-kicker">Veri kapsamı</p><h2 className="mt-2 text-lg font-bold text-[#0a1628]">Analiz hazırlığı</h2><p className="mt-2 text-xs leading-5 text-slate-500">Bu bir finansal sağlık puanı değildir; hazır veri alanlarının oranıdır.</p></div>
            <div className="grid h-20 w-20 shrink-0 place-items-center rounded-full p-2" style={{ background: `conic-gradient(#7c3aed ${readinessScore}%, #eef0f4 0)` }}><div className="grid h-full w-full place-items-center rounded-full bg-white text-center"><div><span className="text-xl font-black text-[#0a1628]">%{readinessScore}</span><span className="block text-[8px] uppercase tracking-wider text-slate-400">hazır</span></div></div></div>
          </div>
          <div className="mt-5 grid gap-2 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
            {readinessAreas.map((area) => <div key={area.name} className="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50/70 px-3 py-2.5">{area.ready ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" /> : <CircleAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />}<div className="min-w-0"><p className="text-xs font-bold text-slate-700">{area.name}</p><p className="mt-0.5 text-[10px] leading-4 text-slate-500">{area.detail}</p></div></div>)}
          </div>
        </article>

        <article className="panel-card p-5">
          <div className="flex items-center justify-between border-b border-slate-200 pb-4"><div><p className="panel-kicker">Kontrol hesabı</p><h2 className="mt-2 text-lg font-bold text-[#0a1628]">Net kâr köprüsü</h2></div><Calculator className="h-5 w-5 text-violet-700" /></div>
          <div className="mt-5 space-y-3 text-sm">
            <div className="flex items-center justify-between gap-3"><span className="text-slate-500">FAVÖK</span><span className="font-bold text-slate-800">{ebitdaAvailable ? formatTRY(data.ebitda) : 'Veri gerekli'}</span></div>
            <div className="flex items-center justify-between gap-3"><span className="text-slate-500">− Amortisman</span><span className="font-bold text-slate-700">{formatTRY(data.depreciation)}</span></div>
            <div className="flex items-center justify-between gap-3"><span className="text-slate-500">− Faiz</span><span className="font-bold text-slate-700">{formatTRY(data.interestExpense)}</span></div>
            <div className="flex items-center justify-between gap-3"><span className="text-slate-500">− Vergi</span><span className="font-bold text-slate-700">{formatTRY(data.taxExpense)}</span></div>
            <div className="border-t border-slate-200 pt-3"><div className="flex items-center justify-between gap-3"><span className="font-bold text-slate-800">Hesaplanan net kâr</span><span className="font-black text-[#0a1628]">{calculatedNetProfit == null ? '—' : formatTRY(calculatedNetProfit)}</span></div></div>
            <div className="flex items-center justify-between gap-3"><span className="text-slate-500">Girilen net kâr</span><span className="font-bold text-slate-800">{formatTRY(data.netProfit)}</span></div>
          </div>
          <div className={`mt-5 rounded-xl border p-3 ${calculatedNetProfit == null ? 'border-amber-200 bg-amber-50' : reconciles ? 'border-emerald-200 bg-emerald-50' : 'border-amber-200 bg-amber-50'}`}><div className="flex items-center gap-2 text-xs font-bold text-slate-800">{calculatedNetProfit != null && reconciles ? <CheckCircle2 className="h-4 w-4 text-emerald-600" /> : <CircleAlert className="h-4 w-4 text-amber-500" />}{calculatedNetProfit == null ? 'Köprü kurulamadı' : reconciles ? 'Net kâr mutabık' : 'Mutabakat farkı var'}</div><p className="mt-1.5 text-[11px] leading-4 text-slate-600">{calculatedNetProfit == null ? 'Faiz, vergi ve amortisman ayrımı doğrulanmalıdır.' : `Fark: ${formatTRY(reconciliationDifference ?? 0)} · tolerans ${formatTRY(reconciliationTolerance)}`}</p></div>
        </article>
      </section>

      <section className="panel-card p-5">
        <div className="flex flex-col gap-3 border-b border-slate-200 pb-4 sm:flex-row sm:items-center sm:justify-between">
          <div><p className="panel-kicker">Nakit hareketi</p><h2 className="mt-2 text-lg font-bold text-[#0a1628]">Giriş, çıkış ve net nakit</h2><p className="mt-1 text-xs text-slate-500">Gelir tablosu giderleriyle karıştırılmayan dönemsel nakit serisi</p></div>
          {cashFlow.length > 6 && <div className="flex rounded-xl border border-slate-200 bg-slate-100 p-1 text-xs font-bold"><button type="button" onClick={() => setTimeRange('6m')} className={`rounded-lg px-3 py-2 ${timeRange === '6m' ? 'bg-white text-[#0f2252] shadow-sm' : 'text-slate-500'}`}>6 dönem</button><button type="button" onClick={() => setTimeRange('12m')} className={`rounded-lg px-3 py-2 ${timeRange === '12m' ? 'bg-white text-[#0f2252] shadow-sm' : 'text-slate-500'}`}>12 dönem</button></div>}
        </div>
        {cashTrendData.length ? <div className="mt-5 h-72 w-full"><ResponsiveContainer width="100%" height="100%"><LineChart data={cashTrendData} margin={{ top: 10, right: 18, left: -8, bottom: 0 }}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8eaf0" /><XAxis dataKey="ay" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} /><YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} unit="M" /><Tooltip formatter={(value, name) => { const labels: Record<string, string> = { giris: 'Nakit girişi', cikis: 'Nakit çıkışı', net: 'Net nakit' }; return [`${Number(value).toLocaleString('tr-TR', { maximumFractionDigits: 2 })} M ${data.currency}`, labels[String(name)] ?? String(name)]; }} contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px', fontSize: '12px', color: '#0f172a' }} /><Legend formatter={(value) => { const labels: Record<string, string> = { giris: 'Nakit girişi', cikis: 'Nakit çıkışı', net: 'Net nakit' }; return labels[String(value)] ?? String(value); }} /><Line type="monotone" dataKey="giris" stroke="#2563eb" strokeWidth={2.5} dot={{ r: 3 }} isAnimationActive animationBegin={120} animationDuration={850} /><Line type="monotone" dataKey="cikis" stroke="#d97706" strokeWidth={2.5} dot={{ r: 3 }} isAnimationActive animationBegin={220} animationDuration={850} /><Line type="monotone" dataKey="net" stroke="#7c3aed" strokeWidth={3} dot={{ r: 4 }} isAnimationActive animationBegin={320} animationDuration={850} /></LineChart></ResponsiveContainer></div> : <div className="mt-5 grid min-h-60 place-items-center rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center"><div><Database className="mx-auto h-8 w-8 text-slate-400" /><h3 className="mt-3 text-sm font-bold text-slate-800">Nakit serisi yüklenmedi</h3><p className="mx-auto mt-2 max-w-md text-xs leading-5 text-slate-500">Trend göstermek için en az iki dönem nakit girişi, nakit çıkışı ve net nakit verisi gerekir.</p><button type="button" onClick={() => onNavigateTab('data-entry')} className="mt-4 text-xs font-bold text-violet-700">Veri yüklemeye git →</button></div></div>}
      </section>

      <section className="panel-card p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between"><div><p className="panel-kicker">Denetlenebilir finans çekirdeği</p><h2 className="mt-2 text-lg font-bold text-[#0a1628]">Formül kayıtları</h2><p className="mt-1 max-w-3xl text-xs leading-5 text-slate-500">Kurumsal metrikler; formül kimliği, sürüm, girdi alanları ve güven kaydıyla gösterilir. Eksik veride sonuç uydurulmaz.</p></div><button type="button" onClick={() => onNavigateTab('data-entry')} className="panel-secondary-button shrink-0">Verileri tamamla</button></div>
        {!audit?.metrik_kaydi ? <div className="mt-5 flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4"><CircleAlert className="mt-0.5 h-5 w-5 shrink-0 text-amber-500" /><div><p className="text-sm font-bold text-amber-900">Formül kaydı henüz oluşmadı</p><p className="mt-1 text-xs leading-5 text-amber-800/70">Finansal dosyayı yeniden aktarın veya alanları kaydedin; motor hesaplanabilen metrikler için denetim kaydı oluşturacaktır.</p></div></div> : <><div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{metricRecords.map(([name, metric]) => { const info = kurumsalEtiketler[name]; const calculated = metric.durum === 'hesaplandi' && metric.deger != null; return <article key={name} className="rounded-xl border border-slate-200 bg-slate-50/60 p-4"><div className="flex items-start justify-between gap-3"><div><h3 className="text-sm font-bold text-slate-800">{info.etiket}</h3><p className="mt-1 text-[10px] leading-4 text-slate-500">{info.aciklama}</p></div><span className={`shrink-0 rounded-full px-2 py-1 text-[9px] font-bold uppercase ${calculated ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}>{calculated ? `${metric.guven} güven` : 'Veri gerekli'}</span></div><p className={`mt-5 text-2xl font-black ${calculated ? 'text-[#0a1628]' : 'text-slate-400'}`}>{calculated ? corporateValue(metric.deger as number, metric.birim) : 'Hesaplanmadı'}</p><div className="mt-4 border-t border-slate-200 pt-3 text-[10px] leading-4 text-slate-500"><p className="font-mono text-slate-600">{metric.formula_id} · {metric.formul_surumu}</p><p className="mt-1">{metric.metodoloji_notu}</p></div></article>; })}</div>{missingCorporateFields.length > 0 && <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4"><p className="text-xs font-bold text-amber-900">Kurumsal metrikler için eksik girdiler</p><div className="mt-3 flex flex-wrap gap-2">{missingCorporateFields.map((field) => <span key={field} className="rounded-full border border-amber-200 bg-white px-2.5 py-1 text-[10px] text-amber-800">{alanEtiketleri[field] ?? field.replaceAll('_', ' ')}</span>)}</div></div>}</>}
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        <article className="panel-card p-5"><div className="flex items-center gap-3"><span className="rounded-lg bg-amber-50 p-2 text-amber-600"><FileCheck2 className="h-5 w-5" /></span><div><p className="text-[10px] font-bold uppercase tracking-[0.16em] text-amber-700">Eksik veri</p><h2 className="text-lg font-bold text-[#0a1628]">Analizi güçlendirecek alanlar</h2></div></div>{missingInputs.length ? <div className="mt-4 flex flex-wrap gap-2">{missingInputs.map((field) => <span key={field} className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-[11px] text-slate-600">{field}</span>)}</div> : <p className="mt-4 text-sm text-emerald-700">Temel analiz girdileri tamamlandı.</p>}<button type="button" onClick={() => onNavigateTab('data-entry')} className="mt-5 inline-flex items-center gap-2 text-xs font-bold text-violet-700">Excel veya form ile tamamla <ArrowRight className="h-3.5 w-3.5" /></button></article>
        <article className="rounded-2xl border border-violet-200 bg-gradient-to-br from-violet-50 to-indigo-50 p-5 shadow-sm"><div className="flex items-center gap-3"><span className="rounded-lg bg-violet-100 p-2 text-violet-700"><Bot className="h-5 w-5" /></span><div><p className="text-[10px] font-bold uppercase tracking-[0.16em] text-violet-700">AI CFO çalışma ilkesi</p><h2 className="text-lg font-bold text-[#0a1628]">Önce metrik, sonra yorum</h2></div></div><p className="mt-4 text-sm leading-6 text-slate-600">AI önerisi; dayandığı metriği, veri kapsamını ve güven seviyesini gösterir. Eksik veride kesin aksiyon üretmez; ödeme, yatırım ve borç kararlarında insan onayı ister.</p><button type="button" onClick={() => onNavigateTab('cfo-agent')} className="mt-5 inline-flex items-center gap-2 rounded-xl bg-[#0f2252] px-4 py-2.5 text-xs font-black text-white transition hover:bg-[#1b3a6b]">Açıklamalı analizi başlat <ArrowRight className="h-3.5 w-3.5" /></button></article>
      </section>

      <p className="px-2 text-center text-[10px] leading-5 text-slate-500">KazKaz AI karar desteği sağlar; muhasebe kaydı, bağımsız denetim görüşü veya yatırım tavsiyesi değildir. DSO hesabı için dönem gün sayısı; cari oran için dönen varlıklar zorunludur. Borç/özkaynak görünümü: {formatMultiple(debtToEquity)}. Brüt marj: {formatPercent(grossMargin)}. Tahsilat süresi: {dsoDays == null ? 'dönem gün sayısı gerekli' : `${dsoDays.toLocaleString('tr-TR', { maximumFractionDigits: 1 })} gün`}.</p>
    </div>
  );
};

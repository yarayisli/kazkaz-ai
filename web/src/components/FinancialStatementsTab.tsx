import React, { useEffect, useState } from 'react';
import { ArrowRight, CheckCircle2, CircleAlert, Landmark, Scale, TrendingUp } from 'lucide-react';
import { CashFlowItem, FinancialData } from '../types';
import { gelismisAjanAnalizi, GelismisAjanGirdisi, MizanDonemi } from '../lib/api';
import { MizanTablosu } from './MizanTablosu';

type StatementSection = 'income' | 'balance' | 'cash';

interface FinancialStatementsTabProps {
  data: FinancialData;
  cashFlow: CashFlowItem[];
  section: StatementSection;
  /** Yüklenen mizan burada taşınır; varsa tablolar ondan türetilir. */
  advancedData?: GelismisAjanGirdisi;
  onNavigateTab: (tab: string) => void;
}

const formatMoney = (value: number, currency: string) => new Intl.NumberFormat('tr-TR', {
  style: 'currency',
  currency: currency === '₺' ? 'TRY' : currency,
  maximumFractionDigits: 0,
}).format(value);

export const FinancialStatementsTab: React.FC<FinancialStatementsTabProps> = ({
  data,
  cashFlow,
  section,
  advancedData,
  onNavigateTab,
}) => {
  // Mizan yüklüyse tablolar hesap bakiyelerinden türetilir. İstek yalnızca
  // mizan varken ve bu sekme açıldığında yapılır; başarısız olursa ekran
  // elle girilen görünümle çalışmaya devam eder.
  const [mizanDonemi, setMizanDonemi] = useState<MizanDonemi | null>(null);
  const [tabloSurumu, setTabloSurumu] = useState<string | undefined>();
  const [yansitma, setYansitma] = useState<string[]>([]);
  const [eslesmeyen, setEslesmeyen] = useState<string[]>([]);

  const mizanSatirSayisi = advancedData?.mizan?.length ?? 0;

  useEffect(() => {
    if (mizanSatirSayisi === 0 || !advancedData) {
      setMizanDonemi(null);
      return undefined;
    }
    let aktif = true;
    gelismisAjanAnalizi(data, advancedData)
      .then((sonuc) => {
        if (!aktif) return;
        const ajan = sonuc.ajanlar?.finansal_tablo_mutabakat_ajani;
        setMizanDonemi(ajan?.son_donem ?? null);
        setTabloSurumu(ajan?.tablo_surumu);
        setYansitma(ajan?.yansitma_hesaplari ?? []);
        setEslesmeyen(ajan?.eslesmeyen_hesaplar ?? []);
      })
      .catch(() => {
        if (aktif) setMizanDonemi(null);
      });
    return () => { aktif = false; };
  }, [advancedData, data, mizanSatirSayisi]);

  const money = (value: number) => formatMoney(value, data.currency);
  const calculatedNetProfit = data.ebitda - data.depreciation - data.interestExpense - data.taxExpense;
  const profitDifference = data.netProfit - calculatedNetProfit;
  const totalLiabilities = data.totalLiabilities ?? data.shortTermDebt + data.longTermDebt + data.payables;
  const totalAssets = data.totalAssets;
  const balanceDifference = totalAssets == null ? null : totalAssets - (totalLiabilities + data.equity);
  const cashBridgeReady = [data.beginningCash, data.operatingCashFlow, data.investingCashFlow, data.financingCashFlow]
    .every((value) => value != null);
  const calculatedClosingCash = cashBridgeReady
    ? (data.beginningCash || 0) + (data.operatingCashFlow || 0) + (data.investingCashFlow || 0) + (data.financingCashFlow || 0)
    : null;

  const tabs = [
    { id: 'income-statement', label: 'Gelir Tablosu', section: 'income' as const, icon: TrendingUp },
    { id: 'balance-sheet', label: 'Bilanço', section: 'balance' as const, icon: Scale },
    { id: 'cash-statement', label: 'Nakit Akışı', section: 'cash' as const, icon: Landmark },
  ];

  const incomeRows: Array<[string, number | undefined]> = [
    ['Net satışlar', data.revenue],
    ['Satışların maliyeti', -data.costOfGoods],
    ['Brüt kâr', data.grossProfit],
    ['Faaliyet giderleri', -data.operatingExpenses],
    ['FAVÖK', data.ebitda],
    ['Amortisman', -data.depreciation],
    ['Faiz gideri', -data.interestExpense],
    ['Vergi gideri', -data.taxExpense],
    ['Net kâr', data.netProfit],
  ];

  const balanceRows: Array<[string, number | undefined]> = [
    ['Dönen varlıklar', data.currentAssets],
    ['Nakit', data.cashInHand],
    ['Ticari alacaklar', data.receivables],
    ['Stoklar', data.inventory],
    ['Toplam varlıklar', data.totalAssets],
    ['Kısa vadeli borç', data.shortTermDebt],
    ['Uzun vadeli borç', data.longTermDebt],
    ['Ticari borçlar', data.payables],
    ['Toplam yükümlülükler', totalLiabilities],
    ['Özkaynak', data.equity],
  ];

  const cashRows: Array<[string, number | undefined | null]> = cashBridgeReady ? [
    ['Dönem başı nakit', data.beginningCash],
    ['Faaliyetlerden nakit akışı', data.operatingCashFlow],
    ['Yatırım faaliyetleri nakit akışı', data.investingCashFlow],
    ['Finansman faaliyetleri nakit akışı', data.financingCashFlow],
    ['Hesaplanan dönem sonu nakit', calculatedClosingCash],
    ['Girilen dönem sonu nakit', data.cashInHand],
  ] : [];

  const rows = section === 'income' ? incomeRows : section === 'balance' ? balanceRows : cashRows;
  const title = section === 'income' ? 'Gelir Tablosu' : section === 'balance' ? 'Bilanço' : 'Nakit Akış Tablosu';
  const description = section === 'income'
    ? 'Kârlılık kalemleri FAVÖK’ten net kâra kadar ayrı gösterilir.'
    : section === 'balance'
      ? 'Varlıklar ile yükümlülük ve özkaynak dengesi kontrol edilir.'
      : 'Dönem başı nakit, faaliyet, yatırım ve finansman hareketleriyle mutabıklaştırılır.';

  const control = section === 'income'
    ? { ready: Math.abs(profitDifference) <= Math.max(Math.abs(data.netProfit) * 0.001, 1), label: `Net kâr mutabakat farkı: ${money(profitDifference)}` }
    : section === 'balance'
      ? { ready: balanceDifference != null && Math.abs(balanceDifference) <= 1, label: balanceDifference == null ? 'Toplam varlıklar verisi gerekli' : `Bilanço eşitlik farkı: ${money(balanceDifference)}` }
      : { ready: calculatedClosingCash != null && Math.abs(calculatedClosingCash - data.cashInHand) <= 1, label: calculatedClosingCash == null ? 'Nakit köprüsü için dört bileşen gerekli' : `Nakit köprüsü farkı: ${money(calculatedClosingCash - data.cashInHand)}` };

  const mizanBolumu = section === 'income' || section === 'balance' ? section : null;

  return (
    <div className="space-y-5 pb-8">
      <section className="panel-card p-5 sm:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <span className="panel-kicker">Finans</span>
            <h1 className="mt-2 text-2xl font-black tracking-[-0.03em] text-[#0a1628]">{title}</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">{description}</p>
          </div>
          <button type="button" onClick={() => onNavigateTab('data-entry')} className="panel-secondary-button">Veriyi güncelle <ArrowRight className="h-4 w-4" /></button>
        </div>
        <div className="mt-5 grid gap-2 rounded-xl border border-slate-200 bg-slate-100 p-1 sm:grid-cols-3" role="tablist" aria-label="Finansal tablolar">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const active = section === tab.section;
            return <button key={tab.id} type="button" role="tab" aria-selected={active} onClick={() => onNavigateTab(tab.id)} className={`flex min-h-11 items-center justify-center gap-2 rounded-lg px-3 text-xs font-extrabold transition ${active ? 'bg-white text-[#0f2252] shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}><Icon className={`h-4 w-4 ${active ? 'text-violet-700' : ''}`} />{tab.label}</button>;
          })}
        </div>
      </section>

      {mizanDonemi && mizanBolumu && (
        <MizanTablosu
          donem={mizanDonemi}
          bolum={mizanBolumu}
          paraBirimi={data.currency}
          tabloSurumu={tabloSurumu}
          yansitmaHesaplari={yansitma}
          eslesmeyenHesaplar={eslesmeyen}
        />
      )}

      <section className={`flex items-start gap-3 rounded-xl border px-4 py-3 ${control.ready ? 'border-emerald-200 bg-emerald-50 text-emerald-900' : 'border-amber-200 bg-amber-50 text-amber-900'}`}>
        {control.ready ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-700" /> : <CircleAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-700" />}
        <div><p className="text-xs font-extrabold">{control.ready ? 'Kontrol başarılı' : 'İnceleme veya ek veri gerekli'}</p><p className="mt-1 text-[11px]">{control.label}</p></div>
      </section>

      <section className="panel-card overflow-hidden">
        <div className="border-b border-slate-200 px-5 py-4">
          <h2 className="text-sm font-extrabold text-slate-900">{data.companyName} · {data.period}</h2>
          <p className="mt-1 text-[11px] text-slate-500">
            {mizanDonemi && mizanBolumu ? 'Girilen özet veriden · ' : ''}Raporlama para birimi: {data.currency}
          </p>
        </div>
        {section === 'cash' && !cashBridgeReady ? (
          <div className="p-6 text-sm text-slate-600"><strong className="text-slate-900">Nakit köprüsü henüz kurulamadı.</strong><p className="mt-2 text-xs leading-5">Dönem başı nakit, operasyonel nakit akışı, yatırım nakit akışı ve finansman nakit akışı alanlarını tamamlayın. Aylık nakit hareketleri ayrı olarak Nakit &amp; Borç ekranında incelenebilir.</p></div>
        ) : (
          <div className="divide-y divide-slate-100">
            {rows.map(([label, value], index) => (
              <div key={label} className={`flex items-center justify-between gap-4 px-5 py-3 text-sm ${index === rows.length - 1 || label.includes('Toplam') || label.includes('Brüt kâr') || label.includes('FAVÖK') ? 'bg-slate-50 font-extrabold text-slate-900' : 'text-slate-600'}`}>
                <span>{label}</span><span className={typeof value === 'number' && value < 0 ? 'text-red-700' : 'text-slate-900'}>{value == null ? 'Veri gerekli' : money(value)}</span>
              </div>
            ))}
          </div>
        )}
      </section>

      {section === 'cash' && cashFlow.length > 0 && <button type="button" onClick={() => onNavigateTab('cashflow')} className="panel-primary-button">Aylık nakit ve borç detayına git <ArrowRight className="h-4 w-4" /></button>}
    </div>
  );
};

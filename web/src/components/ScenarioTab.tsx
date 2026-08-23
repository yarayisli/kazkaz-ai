import React, { useState } from 'react';
import { FinancialData, TransactionAnalytics } from '../types';
import { Sliders, TrendingUp, DollarSign, Activity, RotateCcw, Calculator, ShieldCheck } from 'lucide-react';

interface ScenarioTabProps {
  baseData: FinancialData;
  analytics?: TransactionAnalytics;
}

export const ScenarioTab: React.FC<ScenarioTabProps> = ({ baseData, analytics }) => {
  const [revenueChange, setRevenueChange] = useState<number>(0); // %
  const [costInflation, setCostInflation] = useState<number>(0); // %
  const [collectionDelay, setCollectionDelay] = useState<number>(0); // days
  const [investmentCost, setInvestmentCost] = useState<number>(0);
  const [discountRate, setDiscountRate] = useState<number>(0);
  const [cashFlows, setCashFlows] = useState<string>('');

  const formatTRY = (val: number) => {
    return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(val);
  };

  // Scenario Calculation
  const simulatedRevenue = baseData.revenue * (1 + revenueChange / 100);
  const simulatedCost = baseData.costOfGoods * (1 + costInflation / 100);
  const simulatedGrossProfit = baseData.grossProfit + (simulatedRevenue - baseData.revenue) - (simulatedCost - baseData.costOfGoods);
  const baseProfitBeforeTax = baseData.netProfit + baseData.taxExpense;
  const effectiveTaxRate = baseProfitBeforeTax > 0
    ? baseData.taxExpense / baseProfitBeforeTax
    : baseData.effectiveTaxRate != null
      ? baseData.effectiveTaxRate / 100
      : 0;
  const grossProfitChange = simulatedGrossProfit - baseData.grossProfit;
  const simulatedProfitBeforeTax = baseProfitBeforeTax + grossProfitChange;
  const simulatedTax = simulatedProfitBeforeTax > 0 ? simulatedProfitBeforeTax * effectiveTaxRate : 0;
  const simulatedNetProfit = simulatedProfitBeforeTax - simulatedTax;
  const collectionCashImpact = baseData.periodDays && baseData.periodDays > 0
    ? (baseData.revenue / baseData.periodDays) * collectionDelay
    : null;

  const profitDiff = simulatedNetProfit - baseData.netProfit;
  const parsedCashFlows = cashFlows.split(',').map((value) => value.trim()).filter(Boolean).map(Number).filter(Number.isFinite);
  const investmentReady = investmentCost > 0 && parsedCashFlows.length > 0;
  const investmentNpv = parsedCashFlows.reduce(
    (sum, value, index) => sum + value / Math.pow(1 + discountRate / 100, index + 1),
    -investmentCost,
  );
  const investmentRoi = investmentCost > 0
    ? (parsedCashFlows.reduce((sum, value) => sum + value, 0) - investmentCost) / investmentCost * 100
    : 0;
  let runningCash = -investmentCost;
  const paybackIndex = parsedCashFlows.findIndex((value) => {
    runningCash += value;
    return runningCash >= 0;
  });

  const handleReset = () => {
    setRevenueChange(0);
    setCostInflation(0);
    setCollectionDelay(0);
    setInvestmentCost(0);
    setDiscountRate(0);
    setCashFlows('');
  };

  const signed = (value: number, unit: string) => `${value > 0 ? '+' : ''}${value}${unit}`;

  return (
    <div className="space-y-6">
      {/* Intro Banner */}
      <div className="bg-slate-900 text-white p-5 rounded-2xl shadow-sm flex items-center justify-between">
        <div>
          <h2 className="text-base font-bold flex items-center gap-2">
            <Sliders className="w-5 h-5 text-blue-400" />
            <span>Finansal Senaryo & Stress Testi Simülatörü</span>
          </h2>
          <p className="text-xs text-slate-300 mt-1">
            Enflasyon, satış büyümesi ve tahsilat sürelerindeki olası değişikliklerin şirketinizin net kârına ve nakit akışına etkisini test edin.
          </p>
        </div>
        <button
          onClick={handleReset}
          className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold px-3 py-2 rounded-lg flex items-center gap-1.5 transition-colors cursor-pointer"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Sıfırla</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sliders Panel */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-5">
          <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-3">Senaryo Parametreleri</h3>

          {/* Revenue Growth Slider */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-slate-700">Satış Büyüme Değişimi:</span>
              <span className="font-bold text-blue-600">{signed(revenueChange, '%')}</span>
            </div>
            <input
              type="range"
              min="-30"
              max="50"
              value={revenueChange}
              onChange={(e) => setRevenueChange(Number(e.target.value))}
              className="w-full accent-blue-600 cursor-pointer"
            />
          </div>

          {/* Cost Inflation Slider */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-slate-700">Maliyet Enflasyon Değişimi:</span>
              <span className="font-bold text-amber-600">{signed(costInflation, '%')}</span>
            </div>
            <input
              type="range"
              min="0"
              max="60"
              value={costInflation}
              onChange={(e) => setCostInflation(Number(e.target.value))}
              className="w-full accent-amber-600 cursor-pointer"
            />
          </div>

          {/* Collection Delay Slider */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-slate-700">Tahsilat Vade Gecikmesi:</span>
              <span className="font-bold text-red-600">{signed(collectionDelay, ' Gün')}</span>
            </div>
            <input
              type="range"
              min="0"
              max="60"
              value={collectionDelay}
              onChange={(e) => setCollectionDelay(Number(e.target.value))}
              className="w-full accent-red-600 cursor-pointer"
            />
          </div>
        </div>

        {/* Comparison Output */}
        <div className="lg:col-span-2 bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-3">
            Mevcut Durum vs Simülasyon Sonucu
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Revenue comparison */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-xs text-slate-500 font-semibold uppercase">Simüle Edilen Ciro</span>
              <div className="text-xl font-extrabold text-slate-900">{formatTRY(simulatedRevenue)}</div>
              <p className="text-xs text-slate-500">Mevcut: {formatTRY(baseData.revenue)}</p>
            </div>

            {/* Net profit comparison */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-xs text-slate-500 font-semibold uppercase">Simüle Edilen Net Kâr</span>
              <div className="text-xl font-extrabold text-slate-900">{formatTRY(simulatedNetProfit)}</div>
              <p className={`text-xs font-bold ${profitDiff >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                Fark: {profitDiff >= 0 ? '+' : ''}{formatTRY(profitDiff)}
              </p>
            </div>
          </div>

          {/* Executive Takeaway */}
          <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 text-xs text-blue-900 space-y-1">
            <span className="font-bold block">Simülasyon Değerlendirmesi</span>
            <p>
              Belirlediğiniz parametrelerle şirketinizin Net Kâr Marjı %
              {simulatedRevenue > 0 ? ((simulatedNetProfit / simulatedRevenue) * 100).toFixed(1) : '0,0'} seviyesine değişmektedir. Vergi, simüle edilen vergi öncesi kâr ve %{(effectiveTaxRate * 100).toFixed(1)} etkin oran üzerinden yeniden hesaplanır.{' '}
              {collectionCashImpact == null
                ? 'Tahsilat gecikmesinin nakit etkisi için dönem gün sayısı gereklidir.'
                : `${signed(collectionDelay, ' günlük')} değişimin yaklaşık nakit etkisi ${formatTRY(collectionCashImpact)} olarak hesaplanır.`}
            </p>
            <p className="mt-2 border-t border-blue-200 pt-2 text-[10px] text-blue-700">Tahsilat etkisi formülü: dönem cirosu / dönem gün sayısı × gecikme günü. Kredili satış oranı ayrıca sağlanırsa yalnızca kredili satış tutarı kullanılmalıdır.</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="mb-4 flex items-start justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="flex items-center gap-2 text-sm font-bold text-slate-900">
                <TrendingUp className="h-4 w-4 text-blue-600" /> Gelir Tahmini ve Geri Test
              </h3>
              <p className="text-xs text-slate-500">Yüklenen aylık işlem serisinden üretilir.</p>
            </div>
            {analytics?.tahmin.guven && <span className="rounded-full bg-amber-50 px-2 py-1 text-[10px] font-bold uppercase text-amber-700">{analytics.tahmin.guven} güven</span>}
          </div>
          {analytics?.tahmin.durum === 'hazir' ? (
            <div className="space-y-3">
              <div className="grid grid-cols-3 gap-2">
                {analytics.tahmin.noktalar.map((point) => (
                  <div key={point.donem} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <p className="text-[10px] font-bold text-slate-500">{point.donem}</p>
                    <p className="mt-1 text-sm font-extrabold text-slate-900">{formatTRY(point.tahmin)}</p>
                    <p className="text-[10px] text-slate-500">{formatTRY(point.alt)} – {formatTRY(point.ust)}</p>
                  </div>
                ))}
              </div>
              <p className="text-xs text-slate-600">
                Geçmiş tahmin hatası (MAPE): <strong>{analytics.tahmin.gecmis_hata_mape ?? 'ölçülemedi'}{analytics.tahmin.gecmis_hata_mape != null ? '%' : ''}</strong> · {analytics.tahmin.yontem}
              </p>
              <p className="rounded-lg bg-amber-50 p-2 text-[11px] text-amber-800">{analytics.tahmin.uyari}</p>
            </div>
          ) : (
            <p className="rounded-xl bg-amber-50 p-4 text-xs text-amber-900">{analytics?.tahmin.gereken || 'Tahmin için aylık işlem verisi yükleyin.'}</p>
          )}
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="mb-4 border-b border-slate-100 pb-3">
            <h3 className="flex items-center gap-2 text-sm font-bold text-slate-900">
              <Calculator className="h-4 w-4 text-violet-600" /> Yatırım NPV / ROI Ön Değerlendirmesi
            </h3>
            <p className="text-xs text-slate-500">Oranlar kullanıcı tarafından girilir; sabit piyasa varsayımı kullanılmaz.</p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <label className="text-xs font-semibold text-slate-700">Başlangıç maliyeti
              <input type="number" min="0" value={investmentCost || ''} placeholder="Örn. 1000000" onChange={(e) => setInvestmentCost(Number(e.target.value))} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
            </label>
            <label className="text-xs font-semibold text-slate-700">İskonto oranı (%)
              <input type="number" min="0" max="300" value={discountRate || ''} placeholder="Örn. 35" onChange={(e) => setDiscountRate(Number(e.target.value))} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
            </label>
            <label className="col-span-2 text-xs font-semibold text-slate-700">Yıllık nakit akışları (virgülle)
              <input value={cashFlows} placeholder="Örn. 350000, 425000, 500000" onChange={(e) => setCashFlows(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2" />
            </label>
          </div>
          <div className="mt-4 grid grid-cols-3 gap-2">
            <div className="rounded-xl bg-slate-50 p-3"><p className="text-[10px] text-slate-500">NPV</p><p className={`text-sm font-extrabold ${!investmentReady ? 'text-slate-400' : investmentNpv >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>{investmentReady ? formatTRY(investmentNpv) : 'Veri gerekli'}</p></div>
            <div className="rounded-xl bg-slate-50 p-3"><p className="text-[10px] text-slate-500">Toplam ROI</p><p className="text-sm font-extrabold text-slate-900">{investmentReady ? `%${investmentRoi.toFixed(1)}` : 'Veri gerekli'}</p></div>
            <div className="rounded-xl bg-slate-50 p-3"><p className="text-[10px] text-slate-500">Basit geri ödeme</p><p className="text-sm font-extrabold text-slate-900">{investmentReady ? (paybackIndex >= 0 ? `${paybackIndex + 1}. yıl` : 'Ufuk dışında') : 'Veri gerekli'}</p></div>
          </div>
          <p className="mt-3 flex items-start gap-2 rounded-lg bg-blue-50 p-2 text-[11px] text-blue-900"><ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0" /> Vergi, enflasyon, finansman ve terminal değer ayrıca doğrulanmadan yatırım kararı verilmemelidir.</p>
        </div>
      </div>
    </div>
  );
};

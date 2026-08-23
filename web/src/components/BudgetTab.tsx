import React from 'react';
import { BudgetItem } from '../types';
import { PieChart, ShieldAlert, AlertCircle, Flame, Zap, ArrowUpRight, ArrowDownRight, RefreshCw } from 'lucide-react';
import { useAlerts } from '../context/AlertContext';

interface BudgetTabProps {
  budgetItems: BudgetItem[];
  onNavigateDataEntry: () => void;
}

export const BudgetTab: React.FC<BudgetTabProps> = ({ budgetItems, onNavigateDataEntry }) => {
  const { triggerBudgetTestAlert, runFullFinancialScan } = useAlerts();
  const showSimulationTools = import.meta.env.VITE_ENABLE_SIMULATION_TOOLS === 'true';

  const formatTRY = (val: number) => {
    return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(val);
  };

  const totalPlanned = budgetItems.reduce((acc, b) => acc + b.planned, 0);
  const totalActual = budgetItems.reduce((acc, b) => acc + b.actual, 0);
  const totalVariance = totalPlanned - totalActual;
  const isTotalOverBudget = totalVariance < 0;

  if (!budgetItems.length) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
        <strong>Bütçe verisi gerekli.</strong> Aylık bütçe ve gerçekleşen sayfasını yüklediğinizde sapma analizi burada oluşturulur.
        <button type="button" onClick={onNavigateDataEntry} className="mt-3 block text-xs font-extrabold text-violet-700">Bütçe verisi yükle →</button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Interactive Live Alert Trigger Banner */}
      {showSimulationTools && <div className="card-dark p-5 rounded-xs border border-[#FF4D00]/40 bg-gradient-to-r from-red-950/40 via-[#18181b] to-[#18181b] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-red-500/20 text-red-400 border border-red-500/40 rounded-xs">
            <ShieldAlert className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="bg-[#FF4D00]/20 text-[#FF4D00] text-[10px] font-mono font-bold px-2 py-0.5 rounded-xs uppercase tracking-wider border border-[#FF4D00]/30">
                OTOMATİK BÜTÇE KORUMA PROTOKOLÜ
              </span>
            </div>
            <h3 className="text-base font-display font-bold text-white mt-1">
              Bütçe Aşımı Otomatik İkaz & Bildirim Motoru
            </h3>
            <p className="text-xs font-mono text-slate-400 mt-0.5">
              Gider kalemleriniz belirlenen %5 tolerans sınırını aştığında anlık sesli ve görsel ikaz üretilir.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0 font-mono text-xs">
          <button
            onClick={() => triggerBudgetTestAlert('Danışmanlık & Hukuk', 240000)}
            className="bg-[#FF4D00] hover:bg-[#e04400] text-white font-bold px-4 py-2.5 rounded-xs transition-all flex items-center gap-2 cursor-pointer shadow-md"
          >
            <Flame className="w-4 h-4 text-white" />
            <span>🚨 Bütçe Aşım Uyarısı Tetikle (Sesli & Görsel)</span>
          </button>
        </div>
      </div>}

      {/* Header Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono">
        <div className="card-dark p-5 rounded-xs border border-white/10 space-y-1 bg-white/[0.03]">
          <span className="text-xs text-slate-400 font-bold uppercase">Planlanan Toplam Bütçe</span>
          <div className="text-2xl font-display font-extrabold text-white">{formatTRY(totalPlanned)}</div>
          <p className="text-[11px] text-slate-500">Q1 Hedeflenen Gider Limiti</p>
        </div>

        <div className="card-dark p-5 rounded-xs border border-white/10 space-y-1 bg-white/[0.03]">
          <span className="text-xs text-slate-400 font-bold uppercase">Gerçekleşen Harcama</span>
          <div className="text-2xl font-display font-extrabold text-white">{formatTRY(totalActual)}</div>
          <p className="text-[11px] text-slate-500">Gerçekleşen Operasyonel Harcama</p>
        </div>

        <div className={`card-dark p-5 rounded-xs border space-y-1 ${
          isTotalOverBudget ? 'border-red-500/50 bg-red-950/20' : 'border-emerald-500/50 bg-emerald-950/20'
        }`}>
          <span className="text-xs text-slate-400 font-bold uppercase">Net Bütçe Sapması</span>
          <div className={`text-2xl font-display font-extrabold ${isTotalOverBudget ? 'text-red-400' : 'text-emerald-400'}`}>
            {formatTRY(totalVariance)}
          </div>
          <p className={`text-[11px] font-bold ${isTotalOverBudget ? 'text-red-300' : 'text-emerald-300'}`}>
            {isTotalOverBudget ? '⚠️ Kritik Bütçe Aşımı Mevcut' : '✓ Bütçe Limitleri İçinde (Tasarruf)'}
          </p>
        </div>
      </div>

      {/* Detailed Budget Table */}
      <div className="card-dark p-5 rounded-xs border border-white/10 space-y-4 bg-white/[0.03]">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10 pb-3">
          <div>
            <h3 className="text-sm font-display font-bold text-white flex items-center gap-2">
              <PieChart className="w-4 h-4 text-[#FF4D00]" />
              <span>Gider Kalemleri & Sapma Analizi (Plan vs Gerçekleşen)</span>
            </h3>
            <p className="text-xs font-mono text-slate-400">Gider kategorilerine göre tolerans ve ikaz durumları</p>
          </div>

          {showSimulationTools && <button
            onClick={runFullFinancialScan}
            className="bg-white/5 hover:bg-white/10 text-slate-300 font-mono text-xs px-3 py-1.5 rounded-xs border border-white/10 flex items-center gap-1.5 self-start sm:self-auto cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5 text-[#FF4D00]" />
            <span>Tüm Toleransları Tara</span>
          </button>}
        </div>

        <div className="space-y-3">
          {budgetItems.map((item, idx) => {
            const isOverBudget = item.actual > item.planned;
            const percentageUsed = item.planned > 0 ? Math.min(Math.round((item.actual / item.planned) * 100), 100) : item.actual > 0 ? 100 : 0;

            return (
              <div
                key={idx}
                className={`p-4 rounded-xs border space-y-2.5 transition-all ${
                  isOverBudget
                    ? 'border-red-500/40 bg-red-950/15'
                    : 'border-white/10 bg-white/[0.02]'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs font-mono">
                  <div className="flex items-center gap-2">
                    {isOverBudget && (
                      <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
                    )}
                    <span className="font-bold text-white text-sm">{item.category}</span>
                  </div>

                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="text-slate-400">Plan: <strong className="text-white">{formatTRY(item.planned)}</strong></span>
                    <span className="text-slate-400">Gerçekleşen: <strong className="text-white">{formatTRY(item.actual)}</strong></span>
                    <span className={`px-2 py-0.5 rounded-xs text-[10px] font-bold ${
                      isOverBudget ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    }`}>
                      {isOverBudget ? `+%${Math.abs(item.variancePercent)} AŞIM` : `-%${Math.abs(item.variancePercent)} TASARRUF`}
                    </span>

                    {/* Quick Trigger Test for this category */}
                    {showSimulationTools && <button
                      onClick={() => triggerBudgetTestAlert(item.category, Math.round(item.planned * 0.25))}
                      className="bg-white/5 hover:bg-white/10 text-slate-300 text-[10px] px-2 py-0.5 rounded-xs border border-white/10 transition-colors cursor-pointer"
                      title="Bu kalem için bütçe aşım simülasyonu çalıştır"
                    >
                      ⚡ Test Et
                    </button>}
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-white/10 rounded-xs h-2 overflow-hidden">
                  <div
                    className={`h-2 rounded-xs transition-all ${
                      isOverBudget ? 'bg-red-500' : 'bg-emerald-500'
                    }`}
                    style={{ width: `${percentageUsed}%` }}
                  ></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

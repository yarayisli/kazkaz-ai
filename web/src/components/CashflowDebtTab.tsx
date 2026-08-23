import React from 'react';
import { CashFlowItem, DebtItem } from '../types';
import { Wallet, ShieldAlert, ArrowUpRight, ArrowDownRight, CreditCard, Flame, TrendingDown, RefreshCw } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useAlerts } from '../context/AlertContext';

interface CashflowDebtTabProps {
  cashFlow: CashFlowItem[];
  debts: DebtItem[];
  onNavigateDataEntry: () => void;
}

export const CashflowDebtTab: React.FC<CashflowDebtTabProps> = ({ cashFlow, debts, onNavigateDataEntry }) => {
  const { triggerCashflowTestAlert, runFullFinancialScan } = useAlerts();
  const showSimulationTools = import.meta.env.VITE_ENABLE_SIMULATION_TOOLS === 'true';

  const formatTRY = (val: number) => {
    return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(val);
  };

  const totalDebt = debts.reduce((acc, d) => acc + d.amount, 0);
  const criticalDebts = debts.filter((d) => d.status === 'critical' || d.status === 'warning');
  const averageInflow = cashFlow.length ? cashFlow.reduce((acc, c) => acc + c.inflow, 0) / cashFlow.length : 0;
  const averageOutflow = cashFlow.length ? cashFlow.reduce((acc, c) => acc + c.outflow, 0) / cashFlow.length : 0;

  if (!cashFlow.length && !debts.length) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
        <strong>Nakit ve borç verisi gerekli.</strong> 13 haftalık nakit ile borç servis sayfalarını içeren veri şablonunu yükleyin.
        <button type="button" onClick={onNavigateDataEntry} className="mt-3 block text-xs font-extrabold text-violet-700">Veri girişine git →</button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Live Cash Flow Alert Banner */}
      {showSimulationTools && <div className="card-dark p-5 rounded-xs border border-amber-500/40 bg-gradient-to-r from-amber-950/40 via-[#18181b] to-[#18181b] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-amber-500/20 text-amber-400 border border-amber-500/40 rounded-xs">
            <ShieldAlert className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="bg-amber-500/20 text-amber-400 text-[10px] font-mono font-bold px-2 py-0.5 rounded-xs uppercase tracking-wider border border-amber-500/30">
                LİKİDİTE & NAKİT DÜŞÜŞ KORUMASI
              </span>
            </div>
            <h3 className="text-base font-display font-bold text-white mt-1">
              Kritik Nakit Akış Düşüş Uyarısı
            </h3>
            <p className="text-xs font-mono text-slate-400 mt-0.5">
              Net nakit akışında ₺100.000 üzerindeki düşüşlerde otomatik sesli siren ikazı devreye girer.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0 font-mono text-xs">
          <button
            onClick={() => triggerCashflowTestAlert(450000)}
            className="bg-[#FF4D00] hover:bg-[#e04400] text-white font-bold px-4 py-2.5 rounded-xs transition-all flex items-center gap-2 cursor-pointer shadow-md"
          >
            <TrendingDown className="w-4 h-4 text-white" />
            <span>📉 Nakit Düşüş Uyarısı Tetikle (Sesli & Görsel)</span>
          </button>
        </div>
      </div>}

      {/* Overview Metric Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono">
        <div className="card-dark p-5 rounded-xs border border-white/10 space-y-1 bg-white/[0.03]">
          <div className="flex items-center justify-between text-xs text-slate-400 font-bold uppercase">
            <span>Aylık Ortalama Nakit Girişi</span>
            <ArrowUpRight className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-display font-extrabold text-white">
            {formatTRY(averageInflow)}
          </div>
          <p className="text-xs text-emerald-400 font-medium">{cashFlow.length ? `${cashFlow.length} dönemlik veri` : 'Veri bekleniyor'}</p>
        </div>

        <div className="card-dark p-5 rounded-xs border border-white/10 space-y-1 bg-white/[0.03]">
          <div className="flex items-center justify-between text-xs text-slate-400 font-bold uppercase">
            <span>Aylık Ortalama Nakit Çıkışı</span>
            <ArrowDownRight className="w-4 h-4 text-red-400" />
          </div>
          <div className="text-2xl font-display font-extrabold text-white">
            {formatTRY(averageOutflow)}
          </div>
          <p className="text-xs text-slate-400 font-medium">{cashFlow.length ? 'Yüklenen nakit planı' : 'Veri bekleniyor'}</p>
        </div>

        <div className="card-dark p-5 rounded-xs border border-white/10 space-y-1 bg-white/[0.03]">
          <div className="flex items-center justify-between text-xs text-slate-400 font-bold uppercase">
            <span>Toplam Ticari & Banka Borcu</span>
            <CreditCard className="w-4 h-4 text-[#FF4D00]" />
          </div>
          <div className="text-2xl font-display font-extrabold text-white">{formatTRY(totalDebt)}</div>
          <p className="text-xs text-amber-400 font-medium">{criticalDebts.length} yakın vadeli veya gecikmiş ödeme</p>
        </div>
      </div>

      {/* Cashflow Inflow vs Outflow Chart */}
      <div className="card-dark p-5 rounded-xs border border-white/10 space-y-4 bg-white/[0.03]">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div>
            <h3 className="text-sm font-display font-bold text-white flex items-center gap-2">
              <Wallet className="w-4 h-4 text-[#FF4D00]" />
              <span>Aylık Nakit Hareketleri (Giriş vs Çıkış)</span>
            </h3>
            <p className="text-xs font-mono text-slate-400">Aylık nakit hareketleri ve kumülatif rezerv</p>
          </div>

          {showSimulationTools && <button
            onClick={runFullFinancialScan}
            className="bg-white/5 hover:bg-white/10 text-slate-300 font-mono text-xs px-3 py-1.5 rounded-xs border border-white/10 flex items-center gap-1.5 cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5 text-[#FF4D00]" />
            <span>Nakit Taramasını Yenile</span>
          </button>}
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={cashFlow} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8eaf0" />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#a1a1aa' }} />
              <YAxis tick={{ fontSize: 11, fill: '#a1a1aa' }} unit="₺" tickFormatter={(v) => `${(v/1000000).toFixed(1)}M`} />
              <Tooltip formatter={(val: any) => [formatTRY(Number(val)), 'Tutar']} contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e5eb', borderRadius: '10px', color: '#0f1729', boxShadow: '0 10px 26px rgba(15,34,82,.12)' }} />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Bar dataKey="inflow" name="Nakit Girişi" fill="#10B981" radius={[2, 2, 0, 0]} />
              <Bar dataKey="outflow" name="Nakit Çıkışı" fill="#EF4444" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Debt Table & Risk Analysis */}
      <div className="card-dark p-5 rounded-xs border border-white/10 space-y-4 bg-white/[0.03]">
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div>
            <h3 className="text-sm font-display font-bold text-white flex items-center gap-2">
              <CreditCard className="w-4 h-4 text-slate-300" />
              <span>Kredi & Borç Yapılanması Tablosu</span>
            </h3>
            <p className="text-xs font-mono text-slate-400">Faiz oranları ve son ödeme vadeleri</p>
          </div>
          <span className="text-xs font-mono font-semibold bg-amber-500/20 text-amber-400 px-2.5 py-1 rounded-xs border border-amber-500/30">
            {criticalDebts.length} borç kalemi için ödeme planı incelemesi gerekli
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300 border-collapse font-mono">
            <thead>
              <tr className="bg-white/5 border-b border-white/10 text-slate-400 font-bold uppercase">
                <th className="p-3">Kredi / Alacaklı Firma</th>
                <th className="p-3">Tür</th>
                <th className="p-3 text-right">Anapara Tutarı</th>
                <th className="p-3 text-center">Faiz Tutarı / Yıllık Oran</th>
                <th className="p-3 text-center">Son Ödeme Tarihi</th>
                <th className="p-3 text-center">Durum / Risk</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/10">
              {debts.map((debt) => (
                <tr key={debt.id} className="hover:bg-white/5 transition-colors">
                  <td className="p-3 font-bold text-white">{debt.creditor}</td>
                  <td className="p-3 text-slate-400">{debt.type}</td>
                  <td className="p-3 text-right font-bold text-white">{formatTRY(debt.amount)}</td>
                  <td className="p-3 text-center font-bold text-amber-400">
                    {debt.interestAmount != null ? formatTRY(debt.interestAmount) : `%${debt.interestRate}`}
                  </td>
                  <td className="p-3 text-center text-slate-400">{debt.dueDate}</td>
                  <td className="p-3 text-center">
                    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-xs text-[10px] font-bold ${
                      debt.status === 'critical'
                        ? 'bg-red-500/20 text-red-400 border border-red-500/40'
                        : debt.status === 'warning'
                        ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                        : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                    }`}>
                      {debt.status === 'critical' && 'Yakın / geçmiş vade'}
                      {debt.status === 'warning' && 'Yaklaşan Vade'}
                      {debt.status === 'active' && 'Normal Vade'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="rounded-lg bg-amber-50 p-3 text-[11px] leading-5 text-amber-800">Yapılandırma önerisi üretmek için aylık anapara/faiz planı, para birimi, operasyonel nakit akışı ve DSCR hesabı doğrulanmalıdır. Bu tablo yalnızca vade riskini işaretler.</p>
      </div>
    </div>
  );
};

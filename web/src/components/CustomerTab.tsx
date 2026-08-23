import React from 'react';
import { CustomerRisk, TransactionAnalytics } from '../types';
import { Users, ShieldAlert, Clock, AlertTriangle, CheckCircle } from 'lucide-react';

interface CustomerTabProps {
  customers: CustomerRisk[];
  analytics?: TransactionAnalytics;
  onNavigateDataEntry: () => void;
}

export const CustomerTab: React.FC<CustomerTabProps> = ({ customers, analytics, onNavigateDataEntry }) => {
  const formatTRY = (val: number) => {
    return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(val);
  };

  const totalReceivables = customers.reduce((acc, c) => acc + c.receivableAmount, 0);
  const leadingCustomers = [...customers].sort((a, b) => b.sharePercentage - a.sharePercentage).slice(0, 2);
  const leadingShare = leadingCustomers.reduce((sum, customer) => sum + customer.sharePercentage, 0);
  const highestDelay = customers.reduce((days, customer) => Math.max(days, customer.avgPaymentDays), 0);

  if (!customers.length && !analytics?.musteriler.length) {
    return (
      <div className="rounded-xl border border-amber-300 bg-amber-50 p-5 text-sm text-amber-900">
        <strong>Fatura bazlı alacak verisi gerekli.</strong> Açık alacak sayfasını yüklediğinizde müşteri yoğunlaşması ve gecikme görünümü burada oluşur.
        <button type="button" onClick={onNavigateDataEntry} className="mt-3 block text-xs font-extrabold text-violet-700">Alacak verisi yükle →</button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {customers.length > 0 && <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
        <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div className="text-xs text-amber-900 space-y-1">
          <span className="font-bold block">Müşteri Yoğunlaşma & Tahsilat Riski Uyarısı</span>
          <p>
            En büyük {leadingCustomers.length} müşteri açık alacakların <strong>%{leadingShare.toFixed(1)}</strong>'ini oluşturuyor.
            En yüksek gecikme göstergesi {highestDelay} gün; bu sonuç yüklenen açık faturaların vade tarihine dayanır.
          </p>
        </div>
      </div>}

      {/* Customer Risk Matrix Table */}
      {customers.length > 0 && <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Users className="w-4 h-4 text-blue-600" />
              <span>Müşteri Konsantrasyonu & Alacak Yaşlandırma Tablosu</span>
            </h3>
            <p className="text-xs text-slate-500">Açık alacak payı, tutar ve vade gecikmesi</p>
          </div>
          <span className="text-xs font-semibold bg-slate-100 text-slate-700 px-3 py-1 rounded-md">
            Toplam Alacak: {formatTRY(totalReceivables)}
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700 border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase">
                <th className="p-3">Müşteri Unvanı</th>
                <th className="p-3 text-center">Açık Alacak Payı (%)</th>
                <th className="p-3 text-right">Açık Alacak Tutarı</th>
                <th className="p-3 text-center">Ağırlıklı Gecikme (Gün)</th>
                <th className="p-3 text-center">Risk Seviyesi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {customers.map((cust) => (
                <tr key={cust.id} className="hover:bg-slate-50 transition-colors">
                  <td className="p-3 font-semibold text-slate-900">{cust.name}</td>
                  <td className="p-3 text-center font-bold text-blue-700">%{cust.sharePercentage}</td>
                  <td className="p-3 text-right font-bold text-slate-900">{formatTRY(cust.receivableAmount)}</td>
                  <td className="p-3 text-center font-semibold text-slate-800">{cust.avgPaymentDays} gün</td>
                  <td className="p-3 text-center">
                    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold ${
                      cust.riskLevel === 'kritik'
                        ? 'bg-red-100 text-red-800'
                        : cust.riskLevel === 'yüksek'
                        ? 'bg-amber-100 text-amber-800'
                        : cust.riskLevel === 'orta'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-emerald-100 text-emerald-800'
                    }`}>
                      {cust.riskLevel.toUpperCase()}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>}

      {analytics && analytics.musteriler.length > 0 && (
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Users className="w-4 h-4 text-violet-600" />
              Satış Müşterileri · RFM Segmentasyonu
            </h3>
            <p className="text-xs text-slate-500">Son işlem, sıklık ve toplam gelirden hesaplanır; açık alacak riskiyle karıştırılmaz.</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead><tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase">
                <th className="p-3">Müşteri</th><th className="p-3 text-right">Gelir</th>
                <th className="p-3 text-center">Pay</th><th className="p-3 text-center">İşlem</th>
                <th className="p-3 text-center">RFM</th><th className="p-3">Segment</th>
              </tr></thead>
              <tbody className="divide-y divide-slate-100">
                {analytics.musteriler.slice(0, 20).map((musteri) => (
                  <tr key={musteri.id}>
                    <td className="p-3 font-bold text-slate-900">{musteri.ad}</td>
                    <td className="p-3 text-right font-semibold">{formatTRY(musteri.gelir)}</td>
                    <td className="p-3 text-center">%{musteri.gelir_payi}</td>
                    <td className="p-3 text-center">{musteri.islem_sayisi}</td>
                    <td className="p-3 text-center font-bold">{musteri.rfm_skoru}/15</td>
                    <td className="p-3"><span className="rounded-full bg-violet-50 px-2 py-1 font-semibold text-violet-700">{musteri.segment}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {analytics && analytics.urunler.length > 0 && (
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Ürün / Hizmet Gelir Dağılımı</h3>
            <p className="text-xs text-slate-500">Doğrudan ürün maliyeti bulunmadığı için kârlılık tahmini yapılmaz.</p>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {analytics.urunler.slice(0, 9).map((urun) => (
              <div key={urun.urun} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs font-bold text-slate-900">{urun.urun}</p>
                <p className="mt-2 text-lg font-extrabold text-slate-900">{formatTRY(urun.gelir)}</p>
                <p className="text-[11px] text-slate-500">Gelir payı %{urun.gelir_payi} · {urun.musteri_sayisi} müşteri</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

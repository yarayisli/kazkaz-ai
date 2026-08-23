import React, { useEffect, useState } from 'react';
import { Database, FileDown, FileSpreadsheet, FileText, GitCompare, History, RefreshCw, ShieldCheck, Trash2 } from 'lucide-react';
import { ArsivRaporu, arsivRaporuIndir, arsivRaporuSil, raporArsiviniGetir, raporIndir } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { FinancialData } from '../types';

interface ReportsTabProps {
  data: FinancialData;
  onNavigateDataEntry: () => void;
}

export const ReportsTab: React.FC<ReportsTabProps> = ({ data, onNavigateDataEntry }) => {
  const { currentUser, userProfile, isGuest } = useAuth();
  const [loading, setLoading] = useState<'pdf' | 'excel' | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [archive, setArchive] = useState<ArsivRaporu[]>([]);
  const [archiveLoading, setArchiveLoading] = useState(false);
  const [selectedReports, setSelectedReports] = useState<string[]>([]);
  const canDownload = Boolean(currentUser && userProfile?.companyId && !isGuest);
  const canDelete = canDownload && ['admin', 'cfo'].includes(userProfile?.role || '');

  const loadArchive = async () => {
    if (!canDownload) return;
    setArchiveLoading(true);
    try { setArchive((await raporArsiviniGetir()).raporlar); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Rapor arşivi yüklenemedi.'); }
    finally { setArchiveLoading(false); }
  };

  useEffect(() => { void loadArchive(); }, [canDownload]);

  const download = async (type: 'pdf' | 'excel') => {
    setLoading(type);
    setMessage(null);
    try {
      await raporIndir(type, data);
      setMessage(`${type.toUpperCase()} yönetici raporu indirildi.`);
      await loadArchive();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Rapor oluşturulamadı.');
    } finally {
      setLoading(null);
    }
  };

  const redownload = async (report: ArsivRaporu, type: 'pdf' | 'excel') => {
    setLoading(type); setMessage(null);
    try { await arsivRaporuIndir(report.rapor_id, type); setMessage(`${report.donem} · ${report.surum} raporu indirildi.`); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Arşiv raporu indirilemedi.'); }
    finally { setLoading(null); }
  };

  const removeReport = async (report: ArsivRaporu) => {
    if (!window.confirm(`${report.donem} dönemine ait ${report.surum} sürümü arşivden silinsin mi?`)) return;
    setArchiveLoading(true); setMessage(null);
    try { await arsivRaporuSil(report.rapor_id); setSelectedReports((current) => current.filter((id) => id !== report.rapor_id)); await loadArchive(); setMessage('Rapor sürümü arşivden silindi.'); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Rapor silinemedi.'); }
    finally { setArchiveLoading(false); }
  };

  const toggleCompare = (reportId: string) => setSelectedReports((current) => current.includes(reportId) ? current.filter((id) => id !== reportId) : current.length < 2 ? [...current, reportId] : [current[1], reportId]);
  const comparison = selectedReports.map((id) => archive.find((report) => report.rapor_id === id)).filter(Boolean) as ArsivRaporu[];
  const money = (value?: number) => value == null ? '—' : new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(value);

  return (
    <div className="space-y-5 pb-8">
      <section className="panel-card p-5 sm:p-6">
        <span className="panel-kicker">Rapor merkezi</span>
        <h1 className="mt-2 text-2xl font-black tracking-[-0.03em] text-[#0a1628]">Yönetici raporları</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">Doğrulanmış metrikleri, veri kalitesini, riskleri ve kontrollü aksiyonları paylaşılabilir dosyaya dönüştürün.</p>
      </section>

      {message && <div role="status" className="rounded-xl border border-violet-200 bg-violet-50 px-4 py-3 text-xs font-semibold text-violet-900">{message}</div>}

      <section className="grid gap-4 lg:grid-cols-2">
        <article className="panel-card p-5">
          <div className="flex items-start gap-3"><span className="grid h-10 w-10 place-items-center rounded-xl bg-violet-50 text-violet-700"><FileText className="h-5 w-5" /></span><div><h2 className="text-sm font-extrabold text-slate-900">PDF yönetici raporu</h2><p className="mt-1 text-xs leading-5 text-slate-500">Yönetim, banka veya danışman paylaşımı için sabit düzenli rapor.</p></div></div>
          <button type="button" disabled={!canDownload || loading !== null} onClick={() => void download('pdf')} className="panel-primary-button mt-5 w-full disabled:cursor-not-allowed disabled:opacity-50"><FileDown className="h-4 w-4" />{loading === 'pdf' ? 'Hazırlanıyor…' : 'PDF indir'}</button>
        </article>
        <article className="panel-card p-5">
          <div className="flex items-start gap-3"><span className="grid h-10 w-10 place-items-center rounded-xl bg-violet-50 text-violet-700"><FileSpreadsheet className="h-5 w-5" /></span><div><h2 className="text-sm font-extrabold text-slate-900">Excel analiz paketi</h2><p className="mt-1 text-xs leading-5 text-slate-500">Metrikler, riskler ve aksiyonları çalışma dosyası olarak indirin.</p></div></div>
          <button type="button" disabled={!canDownload || loading !== null} onClick={() => void download('excel')} className="panel-secondary-button mt-5 w-full disabled:cursor-not-allowed disabled:opacity-50"><FileDown className="h-4 w-4" />{loading === 'excel' ? 'Hazırlanıyor…' : 'Excel indir'}</button>
        </article>
      </section>

      {!canDownload && <section className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-amber-900"><ShieldCheck className="mt-0.5 h-4 w-4 shrink-0" /><p className="text-xs leading-5">Rapor indirme yalnızca doğrulanmış şirket çalışma alanında kullanılabilir. Önce giriş yapın ve şirket kurulumunu tamamlayın.</p></section>}

      <section className="grid gap-4 lg:grid-cols-2">
        <article className="panel-card p-5 lg:col-span-2">
          <div className="flex items-center justify-between gap-3"><div className="flex items-center gap-2"><History className="h-4 w-4 text-violet-700" /><h2 className="text-sm font-extrabold text-slate-900">Sürümlü rapor arşivi</h2></div>{canDownload && <button type="button" onClick={() => void loadArchive()} disabled={archiveLoading} className="panel-secondary-button"><RefreshCw className={`h-4 w-4 ${archiveLoading ? 'animate-spin' : ''}`} /> Yenile</button>}</div>
          <p className="mt-3 text-xs leading-5 text-slate-600">Her indirme şirket, dönem, sürüm ve özet metriklerle arşivlenir. İki sürüm seçerek temel finansal farkları karşılaştırabilirsiniz.</p>
          {!canDownload ? <div className="mt-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-center text-[11px] text-slate-500">Arşiv için doğrulanmış şirket oturumu gerekir.</div> : archive.length ? <div className="mt-4 space-y-2">{archive.map((report) => <article key={report.rapor_id} className={`flex flex-col gap-3 rounded-xl border p-3 sm:flex-row sm:items-center sm:justify-between ${selectedReports.includes(report.rapor_id) ? 'border-violet-300 bg-violet-50' : 'border-slate-200 bg-slate-50'}`}><label className="flex min-w-0 cursor-pointer items-start gap-3"><input type="checkbox" checked={selectedReports.includes(report.rapor_id)} onChange={() => toggleCompare(report.rapor_id)} className="mt-1 accent-violet-700" /><span className="min-w-0"><span className="block truncate text-xs font-extrabold text-slate-900">{report.donem} · {report.surum}</span><span className="mt-1 block text-[10px] text-slate-500">Ciro {money(report.ozet.revenue)} · Net kâr {money(report.ozet.netProfit)}</span></span></label><div className="flex flex-wrap items-center gap-2">{report.formatlar.map((type) => <button type="button" key={type} disabled={loading !== null} onClick={() => void redownload(report, type)} className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-[10px] font-extrabold uppercase text-slate-700 hover:border-violet-300">{type} indir</button>)}{canDelete && <button type="button" aria-label={`${report.donem} raporunu sil`} disabled={archiveLoading} onClick={() => void removeReport(report)} className="grid h-8 w-8 place-items-center rounded-lg border border-red-200 bg-white text-red-700 hover:bg-red-50"><Trash2 className="h-3.5 w-3.5" /></button>}</div></article>)}</div> : <div className="mt-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-center text-[11px] text-slate-500">Henüz arşivlenmiş rapor yok. İlk PDF veya Excel raporunu ürettiğinizde burada görünecek.</div>}
          {comparison.length === 2 && <div className="mt-5 rounded-xl border border-violet-200 bg-violet-50 p-4"><div className="flex items-center gap-2 text-xs font-extrabold text-violet-900"><GitCompare className="h-4 w-4" /> Seçili sürüm karşılaştırması</div><div className="mt-3 grid grid-cols-3 gap-2 text-[10px]"><span className="font-bold text-slate-500">Metrik</span><span className="font-bold text-slate-700">{comparison[0].donem}</span><span className="font-bold text-slate-700">{comparison[1].donem}</span>{[['Ciro','revenue'],['Net kâr','netProfit'],['Nakit','cash'],['Toplam borç','totalDebt']].map(([label,key]) => <React.Fragment key={key}><span className="text-slate-500">{label}</span><span className="font-bold text-slate-900">{money(comparison[0].ozet[key as keyof ArsivRaporu['ozet']] as number)}</span><span className="font-bold text-slate-900">{money(comparison[1].ozet[key as keyof ArsivRaporu['ozet']] as number)}</span></React.Fragment>)}</div></div>}
        </article>
        <article className="panel-card p-5">
          <div className="flex items-center gap-2"><Database className="h-4 w-4 text-violet-700" /><h2 className="text-sm font-extrabold text-slate-900">Rapor veri kaynağı</h2></div>
          <p className="mt-3 text-xs leading-5 text-slate-600">Aktif rapor <strong>{data.companyName}</strong> şirketinin <strong>{data.period}</strong> dönemine ve çalışma alanındaki son doğrulanmış verilere dayanır.</p>
          <button type="button" onClick={onNavigateDataEntry} className="panel-secondary-button mt-4"><Database className="h-4 w-4" /> Finansal veri girişine git</button>
        </article>
      </section>
    </div>
  );
};

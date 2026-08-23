import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity, Building2, CheckCircle2, ChevronRight,
  FileClock, Loader2, LockKeyhole, Mail, RefreshCw, Search, ShieldAlert,
  ShieldCheck, UserRound, Users, X,
} from 'lucide-react';
import {
  PlatformSirketDetayi, PlatformSirketListesi, platformGeriBildirimDurumunuGuncelle,
  platformSirketDetayiniGetir, platformSirketEylemi, platformSirketiniGuncelle,
  platformSirketleriniGetir,
} from '../lib/api';

type Company = PlatformSirketListesi['sirketler'][number];
type FeedbackStatus = 'new' | 'in_review' | 'resolved';

const statusLabels: Record<string, string> = { active: 'Aktif', pilot: 'Pilot', suspended: 'Askıda', closed: 'Kapalı' };
const healthLabels: Record<string, string> = { normal: 'Normal', dikkat: 'İlgilen', hareketsiz: 'Hareketsiz', engelli: 'Erişim kapalı' };
const actionLabels: Record<string, string> = {
  'workspace.save': 'Finansal çalışma alanını kaydetti', 'workspace.read': 'Çalışma alanını açtı',
  'workspace.export': 'Verisini dışa aktardı', 'workspace.delete': 'Çalışma alanını sildi',
  'report.archive': 'Yeni rapor oluşturdu', 'report.download': 'Rapor indirdi', 'report.delete': 'Rapor sildi',
  'member.invite': 'Kullanıcı davet etti', 'member.role_update': 'Kullanıcı rolünü değiştirdi', 'member.remove': 'Kullanıcı çıkardı',
  'analysis.financial_audit': 'Finansal denetim çalıştırdı', 'analysis.time_series': 'Zaman serisi analizi çalıştırdı',
  'analysis.esg_readiness': 'ESG hazırlığını kontrol etti', 'analysis.tfrs_readiness': 'TFRS hazırlığını kontrol etti',
  'data.file_validated': 'Finansal dosya doğruladı', 'ai.cfo_chat': 'AI CFO ile çalıştı',
  'ai.cfo_agent': 'CFO araçlarını çalıştırdı', 'ai.advanced_agents': '7 uzman ajanı çalıştırdı',
};

const formatDate = (value: string | null | undefined) => value
  ? new Intl.DateTimeFormat('tr-TR', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value))
  : 'Henüz aktivite yok';

const HealthBadge = ({ value }: { value: string }) => {
  const styles: Record<string, string> = {
    normal: 'bg-emerald-50 text-emerald-700', dikkat: 'bg-amber-50 text-amber-700',
    hareketsiz: 'bg-slate-100 text-slate-600', engelli: 'bg-red-50 text-red-700',
  };
  return <span className={`rounded-full px-2.5 py-1 text-[9px] font-black uppercase tracking-wide ${styles[value] || styles.hareketsiz}`}>{healthLabels[value] || value}</span>;
};

const Metric = ({ label, value, detail }: { label: string; value: string | number; detail: string }) => (
  <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
    <p className="text-[9px] font-black uppercase tracking-wider text-slate-400">{label}</p>
    <p className="mt-1.5 text-lg font-black text-[#0f2252]">{value}</p>
    <p className="mt-1 text-[10px] text-slate-500">{detail}</p>
  </div>
);

export const PlatformCompaniesPanel: React.FC = () => {
  const [companies, setCompanies] = useState<PlatformSirketListesi | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [healthFilter, setHealthFilter] = useState('all');
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<PlatformSirketDetayi | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [reason, setReason] = useState('');
  const [message, setMessage] = useState<string | null>(null);

  const loadCompanies = async () => {
    setLoading(true);
    try { setCompanies(await platformSirketleriniGetir(100)); }
    finally { setLoading(false); }
  };
  const loadDetail = async (companyId: string) => {
    setDetailLoading(true); setMessage(null);
    try { setDetail(await platformSirketDetayiniGetir(companyId)); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Şirket ayrıntısı alınamadı.'); }
    finally { setDetailLoading(false); }
  };

  useEffect(() => { void loadCompanies(); }, []);
  useEffect(() => { if (selectedId) void loadDetail(selectedId); else setDetail(null); }, [selectedId]);

  const filtered = useMemo(() => (companies?.sirketler || []).filter(company => {
    const query = search.trim().toLocaleLowerCase('tr-TR');
    const textMatch = !query || `${company.sirket_adi} ${company.sirket_id} ${company.sektor}`.toLocaleLowerCase('tr-TR').includes(query);
    return textMatch && (statusFilter === 'all' || company.durum === statusFilter)
      && (healthFilter === 'all' || company.operasyon_sagligi === healthFilter);
  }), [companies, healthFilter, search, statusFilter]);

  const updateCompany = async (change: { durum?: string; plan?: string }) => {
    if (!detail) return;
    const description = change.durum ? `durumu ${statusLabels[change.durum] || change.durum}` : `paketi ${change.plan?.toUpperCase()}`;
    if (!window.confirm(`${detail.sirket.sirket_adi} şirketinin ${description} olarak güncellensin mi?`)) return;
    setActionLoading(true); setMessage(null);
    try {
      await platformSirketiniGuncelle(detail.sirket.sirket_id, { ...change, ...(reason.trim().length >= 5 ? { gerekce: reason.trim() } : {}) });
      setMessage('Şirket ayarı güncellendi ve denetim kaydına yazıldı.');
      await Promise.all([loadCompanies(), loadDetail(detail.sirket.sirket_id)]);
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Şirket güncellenemedi.'); }
    finally { setActionLoading(false); }
  };

  const revokeSessions = async () => {
    if (!detail || reason.trim().length < 5) return;
    if (!window.confirm(`${detail.sirket.sirket_adi} şirketindeki tüm kullanıcı oturumları sonlandırılacak. Devam edilsin mi?`)) return;
    setActionLoading(true); setMessage(null);
    try {
      const result = await platformSirketEylemi(detail.sirket.sirket_id, 'oturumlari_sonlandir', reason.trim());
      setMessage(`${result.etkilenen_kullanici} kullanıcının oturumu sonlandırıldı${result.basarisiz_kullanici ? `; ${result.basarisiz_kullanici} işlem kontrol edilmeli` : ''}.`);
      setReason('');
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Oturumlar sonlandırılamadı.'); }
    finally { setActionLoading(false); }
  };

  const updateFeedback = async (feedbackId: string, nextStatus: FeedbackStatus) => {
    if (!detail) return;
    setActionLoading(true); setMessage(null);
    try {
      await platformGeriBildirimDurumunuGuncelle(detail.sirket.sirket_id, feedbackId, nextStatus, reason.trim().length >= 5 ? reason.trim() : undefined);
      setMessage('Geri bildirim iş akışı güncellendi.');
      await loadDetail(detail.sirket.sirket_id);
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Geri bildirim güncellenemedi.'); }
    finally { setActionLoading(false); }
  };

  return <div className="space-y-4">
    <section className="panel-card p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div><h2 className="font-black text-slate-900">Şirket kontrol merkezi</h2><p className="mt-1 text-xs leading-5 text-slate-500">Kullanım sinyallerini görün, destek ihtiyacını fark edin ve erişime güvenli biçimde müdahale edin.</p></div>
        <button onClick={() => void loadCompanies()} disabled={loading} className="panel-secondary-button"><RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Listeyi yenile</button>
      </div>
      <div className="mt-4 grid gap-3 lg:grid-cols-[minmax(240px,1fr)_180px_180px]">
        <label className="relative"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" /><input value={search} onChange={event => setSearch(event.target.value)} placeholder="Şirket adı, kimlik veya sektör ara" className="min-h-11 w-full rounded-xl border border-slate-300 bg-white pl-10 pr-3 text-xs font-semibold outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-100" /></label>
        <select aria-label="Şirket durumuna göre filtrele" value={statusFilter} onChange={event => setStatusFilter(event.target.value)} className="min-h-11 rounded-xl border border-slate-300 bg-white px-3 text-xs font-bold text-slate-600"><option value="all">Tüm durumlar</option><option value="active">Aktif</option><option value="pilot">Pilot</option><option value="suspended">Askıda</option><option value="closed">Kapalı</option></select>
        <select aria-label="Operasyon sağlığına göre filtrele" value={healthFilter} onChange={event => setHealthFilter(event.target.value)} className="min-h-11 rounded-xl border border-slate-300 bg-white px-3 text-xs font-bold text-slate-600"><option value="all">Tüm sinyaller</option><option value="normal">Normal</option><option value="dikkat">İlgilenilmeli</option><option value="hareketsiz">Hareketsiz</option><option value="engelli">Erişim kapalı</option></select>
      </div>
    </section>

    <div className={`grid gap-4 ${selectedId ? 'xl:grid-cols-[minmax(0,1fr)_minmax(420px,0.8fr)]' : ''}`}>
      <section className="panel-card overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4"><p className="text-xs font-extrabold text-slate-700">{filtered.length} şirket</p><p className="text-[10px] text-slate-400">Finansal değer gösterilmez</p></div>
        {loading ? <div className="grid min-h-64 place-items-center"><Loader2 className="h-6 w-6 animate-spin text-violet-600" /></div> : <div className="divide-y divide-slate-100">
          {filtered.map(company => <button key={company.sirket_id} onClick={() => setSelectedId(company.sirket_id)} className={`grid w-full gap-3 p-4 text-left transition hover:bg-slate-50 sm:grid-cols-[minmax(190px,1.3fr)_110px_110px_150px_28px] sm:items-center ${selectedId === company.sirket_id ? 'bg-violet-50/60' : ''}`}>
            <div><div className="flex flex-wrap items-center gap-2"><p className="truncate text-sm font-black text-slate-900">{company.sirket_adi}</p><HealthBadge value={company.operasyon_sagligi} /></div><p className="mt-1 text-[10px] text-slate-500">{company.sektor} · {company.uye_sayisi} üye · {company.bekleyen_davet} davet</p></div>
            <div><p className="text-[9px] font-bold uppercase text-slate-400">Durum</p><p className="mt-1 text-xs font-extrabold text-slate-700">{statusLabels[company.durum] || company.durum}</p></div>
            <div><p className="text-[9px] font-bold uppercase text-slate-400">Paket</p><p className="mt-1 text-xs font-extrabold uppercase text-violet-700">{company.plan}</p></div>
            <div><p className="text-[9px] font-bold uppercase text-slate-400">Son hareket</p><p className="mt-1 truncate text-[10px] font-semibold text-slate-600">{formatDate(company.son_aktivite)}</p><p className="mt-0.5 truncate text-[9px] text-slate-400">{actionLabels[company.son_aksiyon] || company.son_aksiyon.replaceAll('_', ' ')}</p></div>
            <ChevronRight className="hidden h-4 w-4 text-slate-400 sm:block" />
          </button>)}
          {!filtered.length && <div className="p-10 text-center"><Building2 className="mx-auto h-8 w-8 text-slate-300" /><p className="mt-3 text-sm font-bold text-slate-600">Filtreye uygun şirket bulunamadı</p><p className="mt-1 text-xs text-slate-400">Henüz canlı şirket yoksa ilk kayıt sonrası burada görünecek.</p></div>}
        </div>}
      </section>

      {selectedId && <aside className="panel-card overflow-hidden xl:sticky xl:top-20 xl:max-h-[calc(100vh-7rem)] xl:overflow-y-auto">
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-slate-100 bg-white px-5 py-4"><div><p className="text-[9px] font-black uppercase tracking-wider text-violet-600">Şirket ayrıntısı</p><p className="mt-1 text-sm font-black text-slate-900">{detail?.sirket.sirket_adi || 'Yükleniyor'}</p></div><button aria-label="Şirket ayrıntısını kapat" onClick={() => setSelectedId(null)} className="grid h-9 w-9 place-items-center rounded-xl bg-slate-100 text-slate-500 hover:bg-slate-200"><X className="h-4 w-4" /></button></div>
        {detailLoading && !detail ? <div className="grid min-h-72 place-items-center"><Loader2 className="h-6 w-6 animate-spin text-violet-600" /></div> : detail && <div className="space-y-5 p-5">
          {message && <p role="status" className="rounded-xl border border-sky-200 bg-sky-50 p-3 text-xs font-bold leading-5 text-sky-800">{message}</p>}
          <div className="grid grid-cols-2 gap-2"><Metric label="30 günlük hareket" value={detail.kullanim.aktivite_30_gun} detail={actionLabels[detail.kullanim.son_aksiyon] || detail.kullanim.son_aksiyon} /><Metric label="Arşivlenen rapor" value={detail.kullanim.rapor_arsivleme} detail={`${detail.kullanim.rapor_indirme} indirme`} /><Metric label="Çalışma alanı" value={detail.kullanim.veri_durumu === 'kayitli' ? 'Kayıtlı' : 'Veri yok'} detail={`${detail.kullanim.calisma_alani_kayit} kayıt işlemi`} /><Metric label="Ekip" value={detail.uyeler.length} detail={`${detail.bekleyen_davetler.length} bekleyen davet`} /></div>

          <section><div className="flex items-center gap-2"><Activity className="h-4 w-4 text-violet-600" /><h3 className="text-xs font-black text-slate-900">Şirket ne yapıyor?</h3></div><div className="mt-3 space-y-2">{detail.son_olaylar.slice(0, 8).map((event, index) => <div key={`${event.aktor}-${event.zaman}-${index}`} className="flex gap-3 rounded-xl border border-slate-200 p-3"><span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-violet-50"><FileClock className="h-3.5 w-3.5 text-violet-700" /></span><div className="min-w-0"><p className="truncate text-[11px] font-extrabold text-slate-700">{actionLabels[event.aksiyon] || event.aksiyon.replaceAll('_', ' ')}</p><p className="mt-1 text-[9px] text-slate-400">{event.aktor_rolu} · {event.aktor} · {formatDate(event.zaman)}</p></div></div>)}{!detail.son_olaylar.length && <p className="rounded-xl border border-dashed border-slate-300 p-4 text-center text-xs text-slate-400">Henüz denetlenebilir aktivite yok.</p>}</div></section>

          <section><div className="flex items-center gap-2"><Users className="h-4 w-4 text-violet-600" /><h3 className="text-xs font-black text-slate-900">Üyeler ve roller</h3></div><div className="mt-3 space-y-2">{detail.uyeler.map(member => <div key={member.kullanici_ozeti} className="flex items-center justify-between rounded-xl bg-slate-50 p-3"><div className="flex items-center gap-2"><UserRound className="h-4 w-4 text-slate-400" /><div><p className="text-[11px] font-extrabold text-slate-700">{member.eposta_maskeli}</p><p className="text-[9px] text-slate-400">{member.kullanici_ozeti}</p></div></div><span className="rounded-full bg-white px-2 py-1 text-[9px] font-black uppercase text-violet-700">{member.rol}</span></div>)}</div></section>

          <section><div className="flex items-center gap-2"><Mail className="h-4 w-4 text-violet-600" /><h3 className="text-xs font-black text-slate-900">Destek sinyalleri</h3></div><div className="mt-3 space-y-2">{detail.geri_bildirimler.slice(0, 8).map(item => <div key={item.geri_bildirim_id} className="rounded-xl border border-slate-200 p-3"><div className="flex items-start justify-between gap-3"><div><p className="text-[11px] font-extrabold text-slate-700">{item.kategori} · {item.sayfa}</p><p className="mt-1 text-[9px] text-slate-400">{formatDate(item.zaman)}{item.iletisim_izni ? ' · iletişim izni var' : ''}</p></div><select aria-label={`${item.kategori} geri bildirim durumu`} value={item.durum} disabled={actionLoading} onChange={event => void updateFeedback(item.geri_bildirim_id, event.target.value as FeedbackStatus)} className="min-h-8 rounded-lg border border-slate-300 bg-white px-2 text-[9px] font-bold"><option value="new">Yeni</option><option value="in_review">İnceleniyor</option><option value="resolved">Çözüldü</option></select></div></div>)}{!detail.geri_bildirimler.length && <p className="rounded-xl bg-emerald-50 p-3 text-xs font-bold text-emerald-700"><CheckCircle2 className="mr-2 inline h-4 w-4" />Açık destek sinyali yok.</p>}</div></section>

          <section className="rounded-2xl border border-amber-200 bg-amber-50/60 p-4"><div className="flex items-center gap-2"><ShieldAlert className="h-4 w-4 text-amber-700" /><h3 className="text-xs font-black text-amber-900">Kontrollü müdahale</h3></div><p className="mt-2 text-[10px] leading-5 text-amber-800">Her işlem denetim kaydına yazılır. Finansal veri görüntülenmez veya değiştirilmez.</p><textarea value={reason} onChange={event => setReason(event.target.value)} maxLength={300} placeholder="Müdahale gerekçesi (oturum kapatma için zorunlu)" className="mt-3 min-h-20 w-full resize-none rounded-xl border border-amber-200 bg-white p-3 text-xs outline-none focus:border-amber-400" />
            <div className="mt-3 grid grid-cols-2 gap-2"><select aria-label="Şirket durumunu değiştir" value={detail.sirket.durum} disabled={actionLoading} onChange={event => void updateCompany({ durum: event.target.value })} className="min-h-10 rounded-xl border border-slate-300 bg-white px-3 text-[10px] font-bold"><option value="active">Aktif</option><option value="pilot">Pilot</option><option value="suspended">Askıya al</option><option value="closed">Kapat</option></select><select aria-label="Şirket paketini değiştir" value={detail.sirket.plan} disabled={actionLoading} onChange={event => void updateCompany({ plan: event.target.value })} className="min-h-10 rounded-xl border border-slate-300 bg-white px-3 text-[10px] font-bold uppercase"><option value="free">Free</option><option value="trial">Trial</option><option value="pro">Pro</option><option value="uzman">Uzman</option></select></div>
            <button onClick={() => void revokeSessions()} disabled={actionLoading || reason.trim().length < 5} className="mt-2 inline-flex min-h-10 w-full items-center justify-center gap-2 rounded-xl bg-red-600 px-3 text-[10px] font-black text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-40">{actionLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <LockKeyhole className="h-4 w-4" />} Tüm oturumları sonlandır</button>
          </section>

          <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-[10px] leading-5 text-emerald-800"><ShieldCheck className="mr-2 inline h-4 w-4" />E-postalar maskeli, kullanıcı kimlikleri özetlidir. Müşteri dosyası, finansal rakam ve geri bildirim mesajı açılmaz.</div>
        </div>}
      </aside>}
    </div>
  </div>;
};

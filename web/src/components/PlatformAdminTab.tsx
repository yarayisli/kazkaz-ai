import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity, AlertTriangle, Bot, Building2, CheckCircle2, CreditCard, Database,
  EyeOff, Loader2, RefreshCw, ServerCog, ShieldCheck, Users,
} from 'lucide-react';
import { PlatformAdminOzet, PlatformOlayListesi, platformAdminOzetiniGetir, platformOlaylariniGetir } from '../lib/api';
import { PlatformCompaniesPanel } from './PlatformCompaniesPanel';

type Section = 'overview' | 'companies' | 'operations' | 'events';

const labelMap: Record<string, string> = {
  production_modu: 'Üretim modu', kimlik_bypass_kapali: 'Kimlik bypass kapalı', firebase_projesi: 'Firebase projesi',
  firebase_servis_hesabi: 'Firebase servis hesabı', canli_cors: 'Canlı CORS', izinli_hostlar: 'İzinli alan adları',
  https_zorunlu: 'HTTPS zorunlu', paket_kapilari: 'Paket kapıları', firebase_kurallari_dagitildi: 'Firebase kuralları',
  tenant_izolasyon_testi: 'Şirket izolasyon testi', veri_saklama_politikasi: 'Veri saklama politikası',
  rapor_saklama_politikasi: 'Rapor saklama politikası', finans_metodoloji_onayi: 'Finans uzman onayı',
  kvkk_hukuk_onayi: 'KVKK hukuk onayı', hata_izleme: 'Hata izleme', yedekleme_hedefi: 'Yedekleme hedefi',
  odeme_saglayicisi: 'Ödeme sağlayıcısı', google_sheets: 'Google Sheets', ai_saglayicisi: 'AI sağlayıcısı',
  ai_yedek_saglayicisi: 'AI yedek sağlayıcısı', geri_yukleme_tatbikati: 'Geri yükleme tatbikatı',
};

const StatusDot = ({ ok }: { ok: boolean }) => ok
  ? <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
  : <AlertTriangle className="h-4 w-4 shrink-0 text-amber-600" />;

const Kpi = ({ icon: Icon, label, value, detail, tone = 'violet' }: { icon: React.ElementType; label: string; value: string | number; detail: string; tone?: 'violet' | 'emerald' | 'amber' | 'sky' }) => {
  const tones = { violet: 'bg-violet-50 text-violet-700', emerald: 'bg-emerald-50 text-emerald-700', amber: 'bg-amber-50 text-amber-700', sky: 'bg-sky-50 text-sky-700' };
  return <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"><div className="flex items-start justify-between"><div><p className="text-[10px] font-extrabold uppercase tracking-[.13em] text-slate-400">{label}</p><p className="mt-2 text-2xl font-black text-[#0f2252]">{value}</p></div><span className={`grid h-10 w-10 place-items-center rounded-xl ${tones[tone]}`}><Icon className="h-5 w-5" /></span></div><p className="mt-3 text-[11px] leading-5 text-slate-500">{detail}</p></article>;
};

export const PlatformAdminTab: React.FC = () => {
  const [section, setSection] = useState<Section>('overview');
  const [overview, setOverview] = useState<PlatformAdminOzet | null>(null);
  const [events, setEvents] = useState<PlatformOlayListesi | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true); setError(null);
    try {
      const [nextOverview, nextEvents] = await Promise.all([
        platformAdminOzetiniGetir(), platformOlaylariniGetir(),
      ]);
      setOverview(nextOverview); setEvents(nextEvents);
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Yönetim merkezi yüklenemedi.'); }
    finally { setLoading(false); }
  };

  useEffect(() => { void load(); }, []);
  const allChecks = useMemo(() => overview ? { ...overview.canli_hazirlik.kritik_kontroller, ...overview.canli_hazirlik.operasyon_kontrolleri } : {}, [overview]);
  const readyChecks = Object.values(allChecks).filter(Boolean).length;
  const totalChecks = Object.keys(allChecks).length;

  if (loading && !overview) return <div className="grid min-h-[480px] place-items-center"><div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-5 py-4 text-sm font-bold text-slate-600 shadow-sm"><Loader2 className="h-5 w-5 animate-spin text-violet-600" /> Sistem yönetimi hazırlanıyor…</div></div>;
  if (error && !overview) return <div className="rounded-2xl border border-red-200 bg-red-50 p-6"><h1 className="font-black text-red-900">Sistem yönetimi açılamadı</h1><p className="mt-2 text-sm text-red-700">{error}</p><button onClick={() => void load()} className="panel-secondary-button mt-4"><RefreshCw className="h-4 w-4" /> Yeniden dene</button></div>;
  if (!overview) return null;

  return <div className="space-y-5">
    <header className="overflow-hidden rounded-2xl bg-[#0f2252] p-6 text-white shadow-[0_18px_45px_rgba(15,34,82,.18)]">
      <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between"><div className="flex items-start gap-4"><span className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-white/10"><ServerCog className="h-6 w-6" /></span><div><p className="text-[10px] font-extrabold uppercase tracking-[.18em] text-violet-200">KazKaz işletim merkezi</p><h1 className="mt-1 text-2xl font-black">Platform yönetimi</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-slate-300">Şirketleri, AI sürekliliğini, operasyon kapılarını ve destek sinyallerini tek yerde yönetin.</p></div></div><button onClick={() => void load()} disabled={loading} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-white/20 bg-white/10 px-4 text-xs font-extrabold hover:bg-white/15 disabled:opacity-50"><RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Yenile</button></div>
      <div className="mt-5 flex items-center gap-2 rounded-xl border border-emerald-300/20 bg-emerald-300/10 p-3 text-xs text-emerald-100"><EyeOff className="h-4 w-4 shrink-0" /> Bu panel müşteri finansal rakamlarını, dosyalarını veya geri bildirim mesaj gövdelerini göstermez.</div>
    </header>

    <nav className="grid grid-cols-2 gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm md:grid-cols-4" aria-label="Sistem yönetimi bölümleri">
      {([['overview','Genel görünüm'],['companies','Şirketler'],['operations','Operasyon'],['events','Olaylar']] as Array<[Section,string]>).map(([id,label]) => <button key={id} onClick={() => setSection(id)} className={`min-h-11 rounded-xl text-xs font-extrabold transition ${section === id ? 'bg-violet-50 text-violet-800 shadow-sm' : 'text-slate-500 hover:bg-slate-50'}`}>{label}</button>)}
    </nav>

    {section === 'overview' && <>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5"><Kpi icon={Building2} label="Toplam şirket" value={overview.sayaclar.toplam_sirket} detail={`${overview.sayaclar.aktif_sirket} aktif · ${overview.sayaclar.pilot_sirket} pilot`} /><Kpi icon={Users} label="Toplam üye" value={overview.sayaclar.toplam_uye} detail="Şirket üyeliklerinin toplamı" tone="sky" /><Kpi icon={Activity} label="Teknik kapı" value={`${readyChecks}/${totalChecks}`} detail={overview.canli_hazirlik.durum === 'hazir' ? 'Canlı kapısı hazır' : 'Eksik kontroller var'} tone={overview.canli_hazirlik.durum === 'hazir' ? 'emerald' : 'amber'} /><Kpi icon={Bot} label="AI sürekliliği" value={`${overview.ai.saglayicilar.filter(item => item.hazir).length}/${overview.ai.saglayicilar.length}`} detail="Hazır sağlayıcı sayısı" tone="violet" /><Kpi icon={AlertTriangle} label="Yeni bildirim" value={overview.sayaclar.yeni_geri_bildirim} detail="Mesaj içeriği gizli tutulur" tone="amber" /></div>
      <div className="grid gap-5 lg:grid-cols-2"><section className="panel-card p-5"><div className="flex items-center gap-3"><ShieldCheck className="h-5 w-5 text-violet-700" /><div><h2 className="font-black text-slate-900">Canlıya çıkış kapıları</h2><p className="mt-1 text-xs text-slate-500">Kritik ve operasyonel hazırlık</p></div></div><div className="mt-4 grid gap-2 sm:grid-cols-2">{Object.entries(allChecks).map(([key,ok]) => <div key={key} className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs font-bold text-slate-700"><StatusDot ok={ok} />{labelMap[key] || key}</div>)}</div></section><section className="panel-card p-5"><div className="flex items-center gap-3"><Bot className="h-5 w-5 text-violet-700" /><div><h2 className="font-black text-slate-900">AI sağlayıcı zinciri</h2><p className="mt-1 text-xs text-slate-500">Finans motoru her zaman doğruluk kaynağıdır</p></div></div><div className="mt-4 space-y-2">{overview.ai.saglayicilar.map(provider => <div key={provider.ad} className="flex items-center justify-between rounded-xl border border-slate-200 p-3"><div className="flex items-center gap-2"><StatusDot ok={provider.hazir} /><span className="text-sm font-extrabold capitalize text-slate-800">{provider.ad}</span></div><span className="rounded-full bg-slate-100 px-2.5 py-1 text-[9px] font-bold uppercase text-slate-500">{provider.rol}</span></div>)}</div><div className="mt-4 rounded-xl bg-violet-50 p-3 text-xs leading-5 text-violet-900">{overview.ai.politika}</div></section></div>
    </>}

    {section === 'companies' && <PlatformCompaniesPanel />}

    {section === 'operations' && <div className="grid gap-5 lg:grid-cols-2"><section className="panel-card p-5"><div className="flex items-center gap-3"><Activity className="h-5 w-5 text-violet-700" /><h2 className="font-black text-slate-900">Performans ölçümleri</h2></div><div className="mt-4 grid grid-cols-3 gap-3"><div className="rounded-xl bg-slate-50 p-3"><p className="text-[9px] font-bold uppercase text-slate-400">Örneklem</p><p className="mt-2 text-lg font-black">{overview.performans.genel?.orneklem ?? 0}</p></div><div className="rounded-xl bg-slate-50 p-3"><p className="text-[9px] font-bold uppercase text-slate-400">p50</p><p className="mt-2 text-lg font-black">{overview.performans.genel?.p50_ms ?? 0} ms</p></div><div className="rounded-xl bg-slate-50 p-3"><p className="text-[9px] font-bold uppercase text-slate-400">p95</p><p className="mt-2 text-lg font-black">{overview.performans.genel?.p95_ms ?? 0} ms</p></div></div><div className="mt-4 space-y-2">{Object.entries(overview.performans.operasyonlar || {}).map(([name,item]) => <div key={name} className="flex items-center justify-between rounded-xl border border-slate-200 p-3 text-xs"><span className="font-bold text-slate-700">{name.replaceAll('_',' ')}</span><span className="text-slate-500">{item.orneklem} çağrı · %{item.basari_orani} · p95 {item.p95_ms} ms</span></div>)}</div></section><div className="space-y-5"><section className="panel-card p-5"><div className="flex items-center gap-3"><CreditCard className="h-5 w-5 text-violet-700" /><h2 className="font-black text-slate-900">Ödeme hazırlığı</h2></div><p className="mt-4 text-sm font-extrabold text-slate-800">{overview.odeme.durum === 'hazir' ? 'Hazır' : 'Kurulum eksik'}</p><div className="mt-3 flex flex-wrap gap-2">{overview.odeme.eksikler?.map(item => <span key={item} className="rounded-full bg-amber-50 px-2.5 py-1 text-[9px] font-bold text-amber-700">{labelMap[item] || item.replaceAll('_',' ')}</span>)}</div></section><section className="panel-card p-5"><div className="flex items-center gap-3"><Database className="h-5 w-5 text-violet-700" /><h2 className="font-black text-slate-900">ERP bağlantıları</h2></div><div className="mt-4 space-y-2">{Object.entries(overview.erp.saglayicilar).map(([name,item]) => <div key={name} className="flex items-center justify-between rounded-xl border border-slate-200 p-3 text-xs"><span className="font-extrabold capitalize text-slate-800">{name}</span><span className="font-bold text-slate-500">{item.durum}</span></div>)}</div></section></div></div>}

    {section === 'events' && <section className="panel-card p-5"><div className="flex items-center gap-3"><Activity className="h-5 w-5 text-violet-700" /><div><h2 className="font-black text-slate-900">Destek ve denetim olayları</h2><p className="mt-1 text-xs text-slate-500">Mesaj gövdesi ve finansal değerler bu görünümde tutulmaz.</p></div></div><div className="mt-4 space-y-2">{events?.olaylar.map(event => <article key={`${event.tur}-${event.olay_id}`} className="flex flex-col gap-2 rounded-xl border border-slate-200 p-3 sm:flex-row sm:items-center sm:justify-between"><div><div className="flex items-center gap-2"><span className={`rounded-full px-2 py-1 text-[8px] font-black uppercase ${event.tur === 'geri_bildirim' ? 'bg-amber-50 text-amber-700' : 'bg-sky-50 text-sky-700'}`}>{event.tur}</span><p className="text-xs font-extrabold text-slate-800">{event.etiket}</p></div><p className="mt-1 text-[10px] text-slate-500">{event.sirket_adi}{event.sayfa ? ` · ${event.sayfa}` : ''}</p></div><div className="text-left sm:text-right"><p className="text-[9px] font-bold uppercase text-slate-500">{event.durum}</p><p className="mt-1 text-[9px] text-slate-400">{event.zaman?.slice(0,19).replace('T',' ') || '—'}</p></div></article>)}{!events?.olaylar.length && <p className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">Henüz destek veya denetim olayı yok.</p>}</div></section>}
  </div>;
};

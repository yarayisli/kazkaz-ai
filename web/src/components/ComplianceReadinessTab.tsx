import React, { useState } from 'react';
import { AlertTriangle, CheckCircle2, ClipboardCheck, FileCheck2, Leaf, Loader2, ShieldCheck } from 'lucide-react';
import {
  EsgHazirlikGirdisi,
  TfrsHazirlikGirdisi,
  UyumHazirlikSonucu,
  esgHazirliginiDegerlendir,
  tfrsHazirliginiDegerlendir,
} from '../lib/api';
import { useAuth } from '../context/AuthContext';

const esgInitial: EsgHazirlikGirdisi = {
  raporlama_yili: new Date().getFullYear(),
  organizasyon_kapsami_tanimli: false,
  onemli_konular_belirlendi: false,
  enerji_kwh: null,
  scope1_tco2e: null,
  scope2_tco2e: null,
  su_m3: null,
  atik_ton: null,
  calisan_sayisi: null,
  kadin_calisan_orani: null,
  kayip_gunlu_is_kazasi: null,
  etik_politikasi_var: false,
  yonetim_sorumlusu_atandi: false,
  veri_kaynaklari_belgeli: false,
  uzman_onayi: false,
};

const tfrsInitial: TfrsHazirlikGirdisi = {
  standart_seti: 'TFRS 2026',
  musteri_sozlesmeleri_var: false,
  hasilat_politikasi_belgeli: false,
  performans_yukumlulukleri_listeli: false,
  kiralama_sozlesmeleri_var: false,
  kiralama_envanteri_var: false,
  yabanci_para_islemleri_var: false,
  fonksiyonel_para_birimi_belgeli: false,
  stok_var: false,
  stok_degerleme_politikasi_belgeli: false,
  finansal_araclar_var: false,
  finansal_arac_siniflandirmasi_belgeli: false,
  iliskili_taraf_var: false,
  iliskili_taraf_listesi_var: false,
  nakit_akis_mutabakati_var: false,
  muhasebe_uzmani_onayi: false,
};

const Checkbox = ({ checked, onChange, label, detail }: { checked: boolean; onChange: (value: boolean) => void; label: string; detail?: string }) => (
  <label className="flex cursor-pointer gap-3 rounded-xl border border-slate-200 bg-white p-3 transition hover:border-violet-200 hover:bg-violet-50/30">
    <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} className="mt-1 h-4 w-4 rounded border-slate-300 accent-violet-600" />
    <span><span className="block text-sm font-bold text-slate-700">{label}</span>{detail && <span className="mt-0.5 block text-xs leading-5 text-slate-500">{detail}</span>}</span>
  </label>
);

const NumberField = ({ label, value, onChange, suffix }: { label: string; value: number | null; onChange: (value: number | null) => void; suffix: string }) => (
  <label className="grid gap-1.5 text-xs font-bold text-slate-600">
    {label}
    <div className="flex overflow-hidden rounded-xl border border-slate-200 bg-white focus-within:border-violet-400 focus-within:ring-2 focus-within:ring-violet-100">
      <input type="number" min="0" value={value ?? ''} onChange={(event) => onChange(event.target.value === '' ? null : Number(event.target.value))} className="min-w-0 flex-1 px-3 py-2.5 text-sm font-semibold text-slate-800 outline-none" />
      <span className="grid place-items-center border-l border-slate-200 bg-slate-50 px-3 text-[10px] text-slate-500">{suffix}</span>
    </div>
  </label>
);

const Result = ({ result }: { result: UyumHazirlikSonucu }) => {
  const completed = result.durum === 'hazirlik_tamamlandi';
  const expertPending = result.durum === 'uzman_onayi_bekliyor';
  return (
    <section aria-live="polite" className="mt-5 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="grid gap-4 border-b border-slate-100 p-5 sm:grid-cols-[auto_1fr] sm:items-center">
        <div className="grid h-20 w-20 place-items-center rounded-full bg-[conic-gradient(#7c3aed_var(--score),#e2e8f0_0)]" style={{ '--score': `${result.hazirlik_orani}%` } as React.CSSProperties}>
          <div className="grid h-16 w-16 place-items-center rounded-full bg-white text-lg font-black text-[#0f2252]">%{result.hazirlik_orani}</div>
        </div>
        <div>
          <div className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-wider ${completed ? 'bg-emerald-50 text-emerald-700' : expertPending ? 'bg-amber-50 text-amber-700' : 'bg-violet-50 text-violet-700'}`}>
            {completed ? <CheckCircle2 className="h-3.5 w-3.5" /> : <ClipboardCheck className="h-3.5 w-3.5" />}
            {completed ? 'Hazırlık tamamlandı' : expertPending ? 'Uzman onayı bekleniyor' : 'Veri hazırlığı sürüyor'}
          </div>
          <p className="mt-2 text-sm font-bold text-slate-700">{result.hazir_baslik}/{result.uygulanabilir_baslik} uygulanabilir başlık hazır</p>
          <p className="mt-1 text-xs leading-5 text-slate-500">{result.metodoloji}</p>
        </div>
      </div>
      <div className="grid gap-2 p-4 sm:grid-cols-2">
        {result.basliklar.filter((item) => item.uygulanabilir).map((item) => (
          <div key={item.kod} className={`flex gap-2.5 rounded-xl border p-3 ${item.hazir ? 'border-emerald-100 bg-emerald-50/60' : 'border-amber-100 bg-amber-50/60'}`}>
            {item.hazir ? <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" /> : <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />}
            <div><p className="text-xs font-extrabold text-slate-700">{item.ad}</p>{!item.hazir && <p className="mt-1 text-[11px] leading-4 text-slate-500">Gerekli: {item.gereken}</p>}</div>
          </div>
        ))}
      </div>
      <div className="border-t border-slate-100 bg-slate-50 px-4 py-3 text-xs leading-5 text-slate-600"><strong>Sınır:</strong> {result.uyari} {result.lisans_notu || ''}</div>
    </section>
  );
};

export const ComplianceReadinessTab: React.FC = () => {
  const { currentUser } = useAuth();
  const [mode, setMode] = useState<'esg' | 'tfrs'>('esg');
  const [esg, setEsg] = useState(esgInitial);
  const [tfrs, setTfrs] = useState(tfrsInitial);
  const [result, setResult] = useState<UyumHazirlikSonucu | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const localAuthDisabled = import.meta.env.DEV && import.meta.env.VITE_API_AUTH_DISABLED === 'true';
  const canEvaluate = Boolean(currentUser) || localAuthDisabled;

  const evaluate = async () => {
    if (!canEvaluate) return;
    setLoading(true); setError(null); setResult(null);
    try { setResult(mode === 'esg' ? await esgHazirliginiDegerlendir(esg) : await tfrsHazirliginiDegerlendir(tfrs)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Hazırlık kontrolü tamamlanamadı.'); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-5">
      <header className="overflow-hidden rounded-2xl bg-[#0f2252] p-6 text-white shadow-[0_18px_45px_rgba(15,34,82,.15)]">
        <div className="flex items-start gap-4"><div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-white/10"><ShieldCheck className="h-5 w-5" /></div><div><p className="text-[10px] font-extrabold uppercase tracking-[.18em] text-violet-200">Kanıt temelli hazırlık</p><h1 className="mt-1 text-2xl font-black">ESG ve TFRS hazırlık merkezi</h1><p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300">Eksik veri ve belgeleri görün; mevzuat uyumu veya performans skoru iddiası üretmeden uzman incelemesine hazırlan.</p></div></div>
      </header>

      <div className="grid grid-cols-2 gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm">
        <button type="button" onClick={() => { setMode('esg'); setResult(null); setError(null); }} className={`flex min-h-14 items-center justify-center gap-2 rounded-xl text-sm font-extrabold transition ${mode === 'esg' ? 'bg-violet-50 text-violet-800 shadow-sm' : 'text-slate-500 hover:bg-slate-50'}`}><Leaf className="h-4 w-4" /> ESG veri hazırlığı</button>
        <button type="button" onClick={() => { setMode('tfrs'); setResult(null); setError(null); }} className={`flex min-h-14 items-center justify-center gap-2 rounded-xl text-sm font-extrabold transition ${mode === 'tfrs' ? 'bg-violet-50 text-violet-800 shadow-sm' : 'text-slate-500 hover:bg-slate-50'}`}><FileCheck2 className="h-4 w-4" /> TFRS belge hazırlığı</button>
      </div>

      {mode === 'esg' ? (
        <section className="grid gap-5 rounded-2xl border border-slate-200 bg-slate-50 p-5 lg:grid-cols-2">
          <div className="space-y-3"><h2 className="text-sm font-black text-[#0f2252]">Kapsam ve yönetişim</h2><Checkbox checked={esg.organizasyon_kapsami_tanimli} onChange={(value) => setEsg({ ...esg, organizasyon_kapsami_tanimli: value })} label="Organizasyon kapsamı tanımlı" /><Checkbox checked={esg.onemli_konular_belirlendi} onChange={(value) => setEsg({ ...esg, onemli_konular_belirlendi: value })} label="Önemli konular belirlendi" /><Checkbox checked={esg.etik_politikasi_var} onChange={(value) => setEsg({ ...esg, etik_politikasi_var: value })} label="Etik politikası var" /><Checkbox checked={esg.yonetim_sorumlusu_atandi} onChange={(value) => setEsg({ ...esg, yonetim_sorumlusu_atandi: value })} label="ESG/veri sorumlusu atandı" /><Checkbox checked={esg.veri_kaynaklari_belgeli} onChange={(value) => setEsg({ ...esg, veri_kaynaklari_belgeli: value })} label="Gösterge kaynakları belgeli" /><Checkbox checked={esg.uzman_onayi} onChange={(value) => setEsg({ ...esg, uzman_onayi: value })} label="Sürdürülebilirlik uzmanı onayı var" detail="İşaretleme yalnız kayıtlı ve yetkili insan onayı mevcutsa yapılmalıdır." /></div>
          <div><h2 className="mb-3 text-sm font-black text-[#0f2252]">Ölçülebilir göstergeler</h2><div className="grid gap-3 sm:grid-cols-2"><NumberField label="Enerji" value={esg.enerji_kwh} onChange={(value) => setEsg({ ...esg, enerji_kwh: value })} suffix="kWh" /><NumberField label="Scope 1" value={esg.scope1_tco2e} onChange={(value) => setEsg({ ...esg, scope1_tco2e: value })} suffix="tCO₂e" /><NumberField label="Scope 2" value={esg.scope2_tco2e} onChange={(value) => setEsg({ ...esg, scope2_tco2e: value })} suffix="tCO₂e" /><NumberField label="Su" value={esg.su_m3} onChange={(value) => setEsg({ ...esg, su_m3: value })} suffix="m³" /><NumberField label="Atık" value={esg.atik_ton} onChange={(value) => setEsg({ ...esg, atik_ton: value })} suffix="ton" /><NumberField label="Çalışan" value={esg.calisan_sayisi} onChange={(value) => setEsg({ ...esg, calisan_sayisi: value })} suffix="kişi" /><NumberField label="Kadın çalışan oranı" value={esg.kadin_calisan_orani} onChange={(value) => setEsg({ ...esg, kadin_calisan_orani: value })} suffix="%" /><NumberField label="Kayıp günlü iş kazası" value={esg.kayip_gunlu_is_kazasi} onChange={(value) => setEsg({ ...esg, kayip_gunlu_is_kazasi: value })} suffix="adet" /></div></div>
        </section>
      ) : (
        <section className="rounded-2xl border border-slate-200 bg-slate-50 p-5"><div className="grid gap-5 lg:grid-cols-2"><div className="space-y-3"><h2 className="text-sm font-black text-[#0f2252]">Uygulanabilir işlemler</h2><Checkbox checked={tfrs.musteri_sozlesmeleri_var} onChange={(value) => setTfrs({ ...tfrs, musteri_sozlesmeleri_var: value })} label="Müşteri sözleşmeleri var" /><Checkbox checked={tfrs.kiralama_sozlesmeleri_var} onChange={(value) => setTfrs({ ...tfrs, kiralama_sozlesmeleri_var: value })} label="Kiralama sözleşmeleri var" /><Checkbox checked={tfrs.yabanci_para_islemleri_var} onChange={(value) => setTfrs({ ...tfrs, yabanci_para_islemleri_var: value })} label="Yabancı para işlemleri var" /><Checkbox checked={tfrs.stok_var} onChange={(value) => setTfrs({ ...tfrs, stok_var: value })} label="Stok var" /><Checkbox checked={tfrs.finansal_araclar_var} onChange={(value) => setTfrs({ ...tfrs, finansal_araclar_var: value })} label="Finansal araçlar var" /><Checkbox checked={tfrs.iliskili_taraf_var} onChange={(value) => setTfrs({ ...tfrs, iliskili_taraf_var: value })} label="İlişkili taraf var" /></div><div className="space-y-3"><h2 className="text-sm font-black text-[#0f2252]">Politika, envanter ve mutabakat</h2>{tfrs.musteri_sozlesmeleri_var && <><Checkbox checked={tfrs.hasilat_politikasi_belgeli} onChange={(value) => setTfrs({ ...tfrs, hasilat_politikasi_belgeli: value })} label="Hasılat politikası belgeli" /><Checkbox checked={tfrs.performans_yukumlulukleri_listeli} onChange={(value) => setTfrs({ ...tfrs, performans_yukumlulukleri_listeli: value })} label="Performans yükümlülükleri listeli" /></>}{tfrs.kiralama_sozlesmeleri_var && <Checkbox checked={tfrs.kiralama_envanteri_var} onChange={(value) => setTfrs({ ...tfrs, kiralama_envanteri_var: value })} label="Kiralama envanteri var" />}{tfrs.yabanci_para_islemleri_var && <Checkbox checked={tfrs.fonksiyonel_para_birimi_belgeli} onChange={(value) => setTfrs({ ...tfrs, fonksiyonel_para_birimi_belgeli: value })} label="Fonksiyonel para birimi belgeli" />}{tfrs.stok_var && <Checkbox checked={tfrs.stok_degerleme_politikasi_belgeli} onChange={(value) => setTfrs({ ...tfrs, stok_degerleme_politikasi_belgeli: value })} label="Stok değerleme politikası belgeli" />}{tfrs.finansal_araclar_var && <Checkbox checked={tfrs.finansal_arac_siniflandirmasi_belgeli} onChange={(value) => setTfrs({ ...tfrs, finansal_arac_siniflandirmasi_belgeli: value })} label="Finansal araç sınıflandırması belgeli" />}{tfrs.iliskili_taraf_var && <Checkbox checked={tfrs.iliskili_taraf_listesi_var} onChange={(value) => setTfrs({ ...tfrs, iliskili_taraf_listesi_var: value })} label="İlişkili taraf listesi var" />}<Checkbox checked={tfrs.nakit_akis_mutabakati_var} onChange={(value) => setTfrs({ ...tfrs, nakit_akis_mutabakati_var: value })} label="Nakit akış mutabakatı var" /><Checkbox checked={tfrs.muhasebe_uzmani_onayi} onChange={(value) => setTfrs({ ...tfrs, muhasebe_uzmani_onayi: value })} label="Muhasebe uzmanı/CFO onayı var" detail="Bu seçim uyum görüşü yerine geçmez; onay kaydını temsil eder." /></div></div></section>
      )}

      {!canEvaluate && <div className="rounded-xl border border-sky-200 bg-sky-50 p-4 text-sm text-sky-800"><strong>Değerlendirmeyi kaydetmek için giriş yapın.</strong> Kontrol listelerini giriş yapmadan inceleyebilirsiniz; şirket verisiyle sonuç üretme işlemi kimliği doğrulanmış çalışma alanında yapılır.</div>}
      <button type="button" onClick={evaluate} disabled={loading || !canEvaluate} className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-[#0f2252] px-5 text-sm font-extrabold text-white shadow-sm transition hover:bg-[#1c3674] disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto">{loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ClipboardCheck className="h-4 w-4" />} Hazırlığı değerlendir</button>
      {error && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm font-semibold text-red-700">{error}</div>}
      {result && <Result result={result} />}
    </div>
  );
};

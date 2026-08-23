import React, { useMemo, useState } from 'react';
import { ArrowLeft, ArrowRight, Building2, Check, CheckCircle2, Database, Loader2, MailCheck, ShieldCheck, Target } from 'lucide-react';
import { sirketDavetiniKabulEt, sirketOlustur, SirketTanimaProfili } from '../lib/api';
import { useAuth } from '../context/AuthContext';

type Secenek<T extends string> = { value: T; label: string; note?: string };

const sektorler: Secenek<SirketTanimaProfili['sektor']>[] = [
  { value: 'teknoloji', label: 'Teknoloji / SaaS' }, { value: 'uretim', label: 'Üretim / Sanayi' },
  { value: 'perakende', label: 'Perakende / E-ticaret' }, { value: 'hizmet', label: 'Hizmet / Danışmanlık' },
  { value: 'insaat', label: 'İnşaat / Gayrimenkul' }, { value: 'gida', label: 'Gıda / HoReCa' },
  { value: 'lojistik', label: 'Lojistik / Taşımacılık' }, { value: 'diger', label: 'Diğer' },
];
const olcekler: Secenek<SirketTanimaProfili['calisan_olcegi']>[] = [
  { value: '1-9', label: '1–9 kişi' }, { value: '10-49', label: '10–49 kişi' },
  { value: '50-249', label: '50–249 kişi' }, { value: '250+', label: '250+ kişi' },
];
const hedefler: Secenek<SirketTanimaProfili['ana_hedef']>[] = [
  { value: 'buyume', label: 'Büyümeyi yönetmek', note: 'Ciro, müşteri ve kapasite görünümü' },
  { value: 'karlilik', label: 'Kârlılığı artırmak', note: 'Marj, gider ve ürün kârlılığı' },
  { value: 'nakit', label: 'Nakit akışını yönetmek', note: '13 haftalık nakit ve tahsilat' },
  { value: 'finansman', label: 'Yatırım / finansman', note: 'Borç servisi ve kaynak ihtiyacı' },
  { value: 'maliyet', label: 'Maliyetleri kontrol etmek', note: 'Bütçe sapması ve gider kırılımı' },
];
const zorluklar: Secenek<SirketTanimaProfili['ana_zorluk']>[] = [
  { value: 'nakit', label: 'Nakit sıkışıklığı' }, { value: 'marj', label: 'Düşen marjlar' },
  { value: 'tahsilat', label: 'Tahsilat ve vadeler' }, { value: 'maliyet', label: 'Artan maliyetler' },
  { value: 'gorunurluk', label: 'Veri / görünürlük eksikliği' },
];
const kaynaklar: Secenek<SirketTanimaProfili['veri_kaynagi']>[] = [
  { value: 'excel', label: 'Excel / CSV' }, { value: 'logo', label: 'Logo' }, { value: 'mikro', label: 'Mikro' },
  { value: 'parasut', label: 'Paraşüt' }, { value: 'erp', label: 'ERP / özel yazılım' },
  { value: 'smmm', label: 'SMMM çıktısı' }, { value: 'diger', label: 'Diğer' },
];
const veriAlanlari: Secenek<SirketTanimaProfili['veri_kapsami'][number]>[] = [
  { value: 'gelir_tablosu', label: 'Gelir tablosu' }, { value: 'bilanco', label: 'Bilanço' },
  { value: 'mizan', label: 'Mizan' }, { value: 'nakit', label: 'Nakit planı' },
  { value: 'alacak', label: 'Alacak / faturalar' }, { value: 'borc', label: 'Borç / taksitler' },
  { value: 'butce', label: 'Bütçe / gerçekleşen' },
];
const aylar = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];
const etiket = <T extends string>(secenekler: Secenek<T>[], value: T) => secenekler.find((secenek) => secenek.value === value)?.label || value;

export const CompanySetup: React.FC = () => {
  const { currentUser, refreshProfile } = useAuth();
  const [step, setStep] = useState(0);
  const [companyName, setCompanyName] = useState('');
  const [sector, setSector] = useState<SirketTanimaProfili['sektor'] | ''>('');
  const [employeeScale, setEmployeeScale] = useState<SirketTanimaProfili['calisan_olcegi'] | ''>('');
  const [primaryGoal, setPrimaryGoal] = useState<SirketTanimaProfili['ana_hedef'] | ''>('');
  const [primaryChallenge, setPrimaryChallenge] = useState<SirketTanimaProfili['ana_zorluk'] | ''>('');
  const [dataSource, setDataSource] = useState<SirketTanimaProfili['veri_kaynagi'] | ''>('');
  const [availableData, setAvailableData] = useState<SirketTanimaProfili['veri_kapsami']>([]);
  const [currency, setCurrency] = useState<SirketTanimaProfili['para_birimi']>('TRY');
  const [fiscalMonth, setFiscalMonth] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [checkingInvite, setCheckingInvite] = useState(false);

  const stepReady = [companyName.trim().length >= 2 && Boolean(sector) && Boolean(employeeScale), Boolean(primaryGoal) && Boolean(primaryChallenge), Boolean(dataSource), true][step];
  const recommendation = useMemo(() => {
    if (primaryGoal === 'nakit' || primaryChallenge === 'nakit') return 'İlk sırada 13 haftalık nakit, tahsilat ve ödeme verilerini doğrulayacağız.';
    if (primaryGoal === 'karlilik' || primaryChallenge === 'marj') return 'İlk sırada gelir tablosu, brüt marj ve gider kırılımını doğrulayacağız.';
    if (primaryChallenge === 'tahsilat') return 'İlk sırada fatura bazlı alacak yaşlandırması ve müşteri yoğunlaşmasını kuracağız.';
    if (primaryGoal === 'finansman') return 'İlk sırada borç servis planını, DSCR girdilerini ve nakit ihtiyacını doğrulayacağız.';
    if (primaryGoal === 'maliyet' || primaryChallenge === 'maliyet') return 'İlk sırada bütçe–gerçekleşen sapması ve maliyet kırılımını inceleyeceğiz.';
    return 'İlk sırada büyümeyi taşıyan müşteri, marj ve nakit sinyallerini doğrulayacağız.';
  }, [primaryChallenge, primaryGoal]);

  const toggleData = (value: SirketTanimaProfili['veri_kapsami'][number]) => setAvailableData((current) => current.includes(value) ? current.filter((item) => item !== value) : [...current, value]);
  const optionClass = (selected: boolean) => `min-h-11 rounded-xl border px-3.5 py-2.5 text-left text-xs font-bold transition ${selected ? 'border-violet-400 bg-violet-400/15 text-violet-100 ring-1 ring-violet-400/30' : 'border-white/10 bg-white/[0.035] text-slate-300 hover:border-white/25 hover:bg-white/[0.065]'}`;

  const submit = async () => {
    if (!currentUser || !sector || !employeeScale || !primaryGoal || !primaryChallenge || !dataSource) return;
    setError(null); setSubmitting(true);
    try {
      const result = await sirketOlustur({ sirket_adi: companyName.trim(), sektor: sector, calisan_olcegi: employeeScale, ana_hedef: primaryGoal, ana_zorluk: primaryChallenge, veri_kaynagi: dataSource, veri_kapsami: availableData, para_birimi: currency, mali_yil_baslangic_ayi: fiscalMonth });
      if (result.token_yenile) await currentUser.getIdToken(true);
      await refreshProfile();
    } catch (err) { setError(err instanceof Error ? err.message : 'Şirket çalışma alanı oluşturulamadı.'); }
    finally { setSubmitting(false); }
  };

  const acceptInvite = async () => {
    if (!currentUser) return;
    setError(null); setCheckingInvite(true);
    try {
      const result = await sirketDavetiniKabulEt();
      if (result.token_yenile) await currentUser.getIdToken(true);
      await refreshProfile();
    } catch (err) { setError(err instanceof Error ? err.message : 'Şirket daveti doğrulanamadı.'); }
    finally { setCheckingInvite(false); }
  };

  const stepNames = ['Şirket bilgileri', 'Önceliğiniz nedir?', 'Veriniz bugün nerede?', 'Başlangıç planınız hazır'];
  const journey = [
    ['Şirket kimliği', 'Sektör ve işletme ölçeği'], ['Karar önceliği', 'Hedef ve mevcut zorluk'],
    ['Veri hazırlığı', 'Kaynak ve mevcut veri alanları'], ['Kontrollü başlangıç', 'Özet ve çalışma alanı'],
  ];

  return (
    <main className="mx-auto grid min-h-[calc(100vh-68px)] max-w-6xl place-items-center px-4 py-8 sm:py-12">
      <div className="grid w-full overflow-hidden rounded-3xl border border-white/10 bg-[#070b18] shadow-2xl shadow-black/20 lg:grid-cols-[0.72fr_1.28fr]">
        <section className="border-b border-white/10 bg-[radial-gradient(circle_at_top_left,rgba(124,58,237,.2),transparent_48%),#0b1020] p-7 sm:p-9 lg:border-b-0 lg:border-r">
          <span className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-orange-500/15 text-orange-300"><ShieldCheck className="h-6 w-6" /></span>
          <p className="mt-7 text-[10px] font-black uppercase tracking-[0.2em] text-violet-300">Kontrollü başlangıç</p>
          <h1 className="mt-3 text-2xl font-extrabold text-white sm:text-3xl">Önce şirketinizi tanıyalım.</h1>
          <p className="mt-4 text-sm leading-6 text-slate-400">Cevaplarınız panel sırasını ve veri hazırlık listesini kişiselleştirir. Finansal sonuçlar yalnızca yüklediğiniz doğrulanmış rakamlardan hesaplanır.</p>
          <div className="mt-8 space-y-4">{journey.map(([title, note], index) => <div key={title} className={`flex items-start gap-3 transition ${index <= step ? 'opacity-100' : 'opacity-45'}`}><span className={`grid h-8 w-8 shrink-0 place-items-center rounded-full text-xs font-black ${index < step ? 'bg-emerald-500 text-white' : index === step ? 'bg-violet-600 text-white' : 'bg-white/5 text-slate-500'}`}>{index < step ? <Check className="h-4 w-4" /> : index + 1}</span><div><p className="text-sm font-bold text-white">{title}</p><p className="mt-0.5 text-xs text-slate-500">{note}</p></div></div>)}</div>
        </section>

        <section className="p-6 sm:p-9 lg:p-11">
          <div className="mb-6 flex flex-col gap-3 rounded-2xl border border-sky-400/20 bg-sky-400/[0.07] p-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-start gap-3"><MailCheck className="mt-0.5 h-5 w-5 shrink-0 text-sky-300" /><div><p className="text-sm font-bold text-white">Şirketiniz sizi davet etti mi?</p><p className="mt-1 text-xs leading-5 text-slate-400">Doğrulanmış e-posta adresinize açık bir davet varsa yeni şirket oluşturmadan mevcut çalışma alanına katılın.</p></div></div>
            <button type="button" onClick={() => void acceptInvite()} disabled={checkingInvite || submitting} className="inline-flex min-h-10 shrink-0 items-center justify-center gap-2 rounded-xl border border-sky-300/30 bg-sky-300/10 px-4 text-xs font-extrabold text-sky-100 hover:bg-sky-300/20 disabled:opacity-50">{checkingInvite && <Loader2 className="h-4 w-4 animate-spin" />} Davetimi kontrol et</button>
          </div>
          <div className="mb-7 flex items-center justify-between gap-4"><div><p className="text-[10px] font-black uppercase tracking-[0.18em] text-slate-500">Adım {step + 1} / 4</p><h2 className="mt-2 text-xl font-bold text-white">{stepNames[step]}</h2></div><div className="flex gap-1.5" aria-label={`Adım ${step + 1} / 4`}>{[0, 1, 2, 3].map((index) => <span key={index} className={`h-2 rounded-full transition-all duration-300 ${index === step ? 'w-7 bg-violet-500' : index < step ? 'w-2 bg-emerald-500' : 'w-2 bg-white/10'}`} />)}</div></div>

          <div key={step} className="landing-reveal">
            {step === 0 && <div className="space-y-6">
              <div><label className="block text-xs font-bold text-slate-300" htmlFor="company-name">Şirketin resmi veya kullanılan adı</label><input id="company-name" value={companyName} onChange={(event) => setCompanyName(event.target.value)} minLength={2} maxLength={160} autoComplete="organization" placeholder="Örnek Teknoloji A.Ş." className="mt-2 w-full rounded-xl border border-white/15 bg-white/[0.055] px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-orange-400 focus:ring-2 focus:ring-orange-400/20" /></div>
              <ChoiceGrid title="Sektör" columns="sm:grid-cols-2 xl:grid-cols-3">{sektorler.map((item) => <ChoiceButton key={item.value} selected={sector === item.value} label={item.label} onClick={() => setSector(item.value)} className={optionClass(sector === item.value)} />)}</ChoiceGrid>
              <ChoiceGrid title="Çalışan ölçeği" columns="grid-cols-2 sm:grid-cols-4">{olcekler.map((item) => <ChoiceButton key={item.value} selected={employeeScale === item.value} label={item.label} onClick={() => setEmployeeScale(item.value)} className={optionClass(employeeScale === item.value)} />)}</ChoiceGrid>
            </div>}

            {step === 1 && <div className="space-y-7">
              <ChoiceGrid title="Önümüzdeki dönemde ana hedefiniz" icon={<Target className="h-4 w-4 text-orange-300" />} columns="sm:grid-cols-2">{hedefler.map((item) => <ChoiceButton key={item.value} selected={primaryGoal === item.value} label={item.label} note={item.note} onClick={() => setPrimaryGoal(item.value)} className={optionClass(primaryGoal === item.value)} />)}</ChoiceGrid>
              <ChoiceGrid title="Bugün en çok zorlandığınız konu" columns="sm:grid-cols-2 xl:grid-cols-3">{zorluklar.map((item) => <ChoiceButton key={item.value} selected={primaryChallenge === item.value} label={item.label} onClick={() => setPrimaryChallenge(item.value)} className={optionClass(primaryChallenge === item.value)} />)}</ChoiceGrid>
            </div>}

            {step === 2 && <div className="space-y-7">
              <ChoiceGrid title="Finans verinizi ağırlıklı olarak nerede tutuyorsunuz?" icon={<Database className="h-4 w-4 text-sky-300" />} columns="sm:grid-cols-2 xl:grid-cols-3">{kaynaklar.map((item) => <ChoiceButton key={item.value} selected={dataSource === item.value} label={item.label} onClick={() => setDataSource(item.value)} className={optionClass(dataSource === item.value)} />)}</ChoiceGrid>
              <div><div className="mb-3 flex items-end justify-between gap-3"><p className="text-xs font-bold text-slate-300">Şu anda elinizde olanlar</p><span className="text-[10px] text-slate-500">Birden çok seçin · bilmiyorsanız boş bırakın</span></div><div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">{veriAlanlari.map((item) => <ChoiceButton key={item.value} selected={availableData.includes(item.value)} label={item.label} onClick={() => toggleData(item.value)} className={optionClass(availableData.includes(item.value))} />)}</div></div>
              <div className="grid gap-4 sm:grid-cols-2"><SelectField label="Raporlama para birimi" value={currency} onChange={(value) => setCurrency(value as SirketTanimaProfili['para_birimi'])} options={['TRY', 'USD', 'EUR', 'GBP', 'CHF']} /><SelectField label="Mali yıl başlangıcı" value={String(fiscalMonth)} onChange={(value) => setFiscalMonth(Number(value))} options={aylar.map((label, index) => ({ label, value: String(index + 1) }))} /></div>
            </div>}

            {step === 3 && sector && employeeScale && primaryGoal && primaryChallenge && dataSource && <div className="space-y-5">
              <div className="rounded-2xl border border-violet-400/20 bg-[linear-gradient(135deg,rgba(124,58,237,.16),rgba(59,130,246,.07))] p-5"><div className="flex items-start gap-3"><span className="rounded-xl bg-violet-400/15 p-2 text-violet-200"><CheckCircle2 className="h-5 w-5" /></span><div><p className="text-xs font-black uppercase tracking-[0.16em] text-violet-300">Kişiselleştirilmiş başlangıç</p><p className="mt-2 text-sm leading-6 text-slate-200">{recommendation}</p></div></div></div>
              <div className="grid gap-3 sm:grid-cols-2"><Summary label="Şirket" value={companyName.trim()} note={`${etiket(sektorler, sector)} · ${etiket(olcekler, employeeScale)}`} /><Summary label="Karar odağı" value={etiket(hedefler, primaryGoal)} note={etiket(zorluklar, primaryChallenge)} /><Summary label="Veri kaynağı" value={etiket(kaynaklar, dataSource)} note={availableData.length ? `${availableData.length}/7 veri alanı mevcut` : 'Mevcut alanlar henüz belirtilmedi'} /><Summary label="Raporlama" value={currency} note={`Mali yıl başlangıcı: ${aylar[fiscalMonth - 1]}`} /></div>
              <p className="text-xs leading-5 text-slate-500">Bu profil kullanıcı beyanıdır. Finansal sağlık puanı veya doğrulanmış mali sonuç olarak kullanılmaz.</p>
            </div>}
          </div>

          {error && <p className="mt-6 rounded-xl border border-red-400/20 bg-red-400/10 px-4 py-3 text-sm text-red-200">{error}</p>}
          <div className="mt-8 flex items-center justify-between border-t border-white/10 pt-6"><button type="button" onClick={() => setStep((current) => Math.max(0, current - 1))} disabled={step === 0 || submitting} className="inline-flex min-h-11 items-center gap-2 rounded-xl px-3 text-sm font-bold text-slate-400 transition hover:bg-white/5 hover:text-white disabled:invisible"><ArrowLeft className="h-4 w-4" /> Geri</button>{step < 3 ? <button type="button" onClick={() => stepReady && setStep((current) => Math.min(3, current + 1))} disabled={!stepReady} className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-[#ff4d00] px-5 text-sm font-extrabold text-white transition hover:-translate-y-0.5 hover:bg-[#ff6328] disabled:cursor-not-allowed disabled:opacity-40">Devam et <ArrowRight className="h-4 w-4" /></button> : <button type="button" onClick={() => void submit()} disabled={submitting} className="inline-flex min-h-12 items-center gap-2 rounded-xl bg-[#ff4d00] px-5 text-sm font-extrabold text-white transition hover:-translate-y-0.5 hover:bg-[#ff6328] disabled:cursor-not-allowed disabled:opacity-50">{submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Building2 className="h-4 w-4" />} Çalışma alanını oluştur</button>}</div>
        </section>
      </div>
    </main>
  );
};

const ChoiceGrid: React.FC<{ title: string; columns: string; icon?: React.ReactNode; children: React.ReactNode }> = ({ title, columns, icon, children }) => <div><p className="mb-2.5 flex items-center gap-2 text-xs font-bold text-slate-300">{icon}{title}</p><div className={`grid gap-2 ${columns}`}>{children}</div></div>;
const ChoiceButton: React.FC<{ selected: boolean; label: string; note?: string; onClick: () => void; className: string }> = ({ selected, label, note, onClick, className }) => <button type="button" aria-pressed={selected} onClick={onClick} className={className}><span className="block">{label}</span>{note && <span className="mt-1 block text-[10px] font-medium text-slate-500">{note}</span>}</button>;
const Summary: React.FC<{ label: string; value: string; note: string }> = ({ label, value, note }) => <article className="rounded-xl border border-white/10 bg-white/[0.035] p-4"><p className="text-[10px] font-bold uppercase tracking-wider text-slate-500">{label}</p><p className="mt-2 font-bold text-white">{value}</p><p className="mt-1 text-xs text-slate-400">{note}</p></article>;
const SelectField: React.FC<{ label: string; value: string; onChange: (value: string) => void; options: Array<string | { label: string; value: string }> }> = ({ label, value, onChange, options }) => <label className="text-xs font-bold text-slate-300">{label}<select value={value} onChange={(event) => onChange(event.target.value)} className="mt-2 min-h-11 w-full rounded-xl border border-white/15 bg-[#101627] px-3 text-sm text-white outline-none focus:border-orange-400">{options.map((item) => { const option = typeof item === 'string' ? { label: item, value: item } : item; return <option key={option.value} value={option.value}>{option.label}</option>; })}</select></label>;

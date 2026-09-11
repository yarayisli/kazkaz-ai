import React, { useState } from 'react';
import { CheckCircle2, Clock3, MessageSquareText, Send, ThumbsDown, ThumbsUp, X } from 'lucide-react';
import { DestekTalebi, destekTalebiMemnuniyeti, destekTaleplerim, geriBildirimGonder, pilotNiyetDurumu, pilotNiyetKaydet } from '../lib/api';

type Category = 'hata' | 'oneri' | 'kullanilabilirlik' | 'finansal_sonuc';

const durumEtiketi: Record<DestekTalebi['durum'], { ad: string; renk: string }> = {
  new: { ad: 'Alındı', renk: 'bg-sky-500/20 text-sky-200 border-sky-400/30' },
  in_review: { ad: 'İnceleniyor', renk: 'bg-amber-500/20 text-amber-200 border-amber-400/30' },
  resolved: { ad: 'Çözüldü', renk: 'bg-emerald-500/20 text-emerald-200 border-emerald-400/30' },
};

export const FeedbackWidget: React.FC<{ activePage: string }> = ({ activePage }) => {
  const [open, setOpen] = useState(false);
  const [view, setView] = useState<'gonder' | 'talepler' | 'pilot'>('gonder');
  const [category, setCategory] = useState<Category>('kullanilabilirlik');
  const [message, setMessage] = useState('');
  const [contactAllowed, setContactAllowed] = useState(false);
  const [status, setStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');
  const [talepNo, setTalepNo] = useState<string | null>(null);
  const [talepler, setTalepler] = useState<DestekTalebi[] | null>(null);
  const [talepLoading, setTalepLoading] = useState(false);
  const [pilotStatus, setPilotStatus] = useState<{ uygun: boolean; yanitlandi: boolean; asgari_gun?: number } | null>(null);
  const [intent, setIntent] = useState<'kesinlikle' | 'muhtemelen' | 'kararsiz' | 'muhtemelen_hayir' | 'kesinlikle_hayir'>('muhtemelen');
  const [paidContinuation, setPaidContinuation] = useState<boolean | null>(null);
  const [pilotSending, setPilotSending] = useState(false);
  const [pilotError, setPilotError] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (message.trim().length < 10) return;
    setStatus('sending');
    try {
      const sonuc = await geriBildirimGonder(category, message.trim(), activePage, contactAllowed);
      setTalepNo(sonuc.talep_no);
      setStatus('sent');
      setMessage('');
    } catch {
      setStatus('error');
    }
  };

  const talepleriYukle = async () => {
    setTalepLoading(true);
    try { setTalepler((await destekTaleplerim()).talepler); }
    catch { setTalepler([]); }
    finally { setTalepLoading(false); }
  };

  const gecisYap = (hedef: 'gonder' | 'talepler' | 'pilot') => {
    setView(hedef);
    if (hedef === 'talepler') void talepleriYukle();
    if (hedef === 'pilot') void pilotNiyetDurumu().then(setPilotStatus).catch(() => setPilotStatus({ uygun: false, yanitlandi: false }));
  };

  const pilotGonder = async () => {
    if (paidContinuation === null) return;
    setPilotSending(true); setPilotError(null);
    try {
      await pilotNiyetKaydet(intent, paidContinuation);
      setPilotStatus({ uygun: true, yanitlandi: true });
    } catch (error) {
      setPilotError(error instanceof Error ? error.message : 'Pilot değerlendirmesi kaydedilemedi.');
    } finally { setPilotSending(false); }
  };

  const memnuniyetVer = async (talep: DestekTalebi, memnun: boolean) => {
    try {
      await destekTalebiMemnuniyeti(talep.geri_bildirim_id, memnun);
      setTalepler((mevcut) => (mevcut || []).map((t) => t.geri_bildirim_id === talep.geri_bildirim_id ? { ...t, memnun } : t));
    } catch {
      // Sessiz geç; kullanıcı tekrar deneyebilir.
    }
  };

  return <div className="fixed bottom-5 right-5 z-50">
    {open && <div className="mb-3 w-[min(380px,calc(100vw-2rem))] rounded-2xl border border-white/10 bg-[#10172b] p-4 text-white shadow-2xl">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold">Destek</h2>
        <button type="button" onClick={() => setOpen(false)} aria-label="Kapat"><X className="h-4 w-4 text-slate-400" /></button>
      </div>

      <div className="mt-3 grid grid-cols-3 gap-1 rounded-lg bg-white/5 p-1" role="tablist" aria-label="Destek görünümü">
        <button type="button" role="tab" aria-selected={view === 'gonder'} onClick={() => gecisYap('gonder')} className={`rounded-md py-1.5 text-[11px] font-bold ${view === 'gonder' ? 'bg-white/10 text-white' : 'text-slate-400'}`}>Yeni talep</button>
        <button type="button" role="tab" aria-selected={view === 'talepler'} onClick={() => gecisYap('talepler')} className={`rounded-md py-1.5 text-[11px] font-bold ${view === 'talepler' ? 'bg-white/10 text-white' : 'text-slate-400'}`}>Taleplerim</button>
        <button type="button" role="tab" aria-selected={view === 'pilot'} onClick={() => gecisYap('pilot')} className={`rounded-md py-1.5 text-[11px] font-bold ${view === 'pilot' ? 'bg-white/10 text-white' : 'text-slate-400'}`}>Pilot</button>
      </div>

      {view === 'gonder' && <form onSubmit={submit} className="mt-3">
        <p className="text-[10px] leading-4 text-slate-400">Finansal veri, kimlik numarası veya parola eklemeyin.</p>
        <select value={category} onChange={(event) => setCategory(event.target.value as Category)} aria-label="Kategori" className="mt-3 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs"><option value="kullanilabilirlik">Kullanım kolaylığı</option><option value="hata">Hata</option><option value="finansal_sonuc">Finansal sonuç</option><option value="oneri">Öneri</option></select>
        <textarea value={message} onChange={(event) => setMessage(event.target.value)} minLength={10} maxLength={2000} required rows={5} placeholder="Ne oldu, hangi sonucu bekliyordunuz?" className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs outline-none focus:ring-2 focus:ring-orange-500" />
        <label className="mt-2 flex items-start gap-2 text-[10px] text-slate-300"><input type="checkbox" checked={contactAllowed} onChange={(event) => setContactAllowed(event.target.checked)} /> Bu geri bildirim için benimle iletişime geçilebilir.</label>
        {status === 'sent' && <div className="mt-2 rounded-lg border border-emerald-400/30 bg-emerald-500/10 p-2.5 text-[11px] text-emerald-200">
          <p className="font-bold">Talebiniz alındı. Talep no: <span className="tabular-nums">{talepNo}</span></p>
          <p className="mt-0.5 text-emerald-300/80">Durumu “Taleplerim” sekmesinden izleyebilirsiniz.</p>
        </div>}
        {status === 'error' && <p className="mt-2 text-[10px] text-red-300">Gönderilemedi; lütfen oturumunuzu kontrol edip yeniden deneyin.</p>}
        <button type="submit" disabled={status === 'sending' || message.trim().length < 10} className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg bg-orange-600 px-3 py-2 text-xs font-bold disabled:opacity-50"><Send className="h-3.5 w-3.5" /> {status === 'sending' ? 'Gönderiliyor…' : 'Gönder'}</button>
      </form>}

      {view === 'talepler' && <div className="mt-3 max-h-[60vh] space-y-2 overflow-auto">
        {talepLoading && <p className="py-6 text-center text-[11px] text-slate-400">Talepleriniz yükleniyor…</p>}
        {!talepLoading && talepler && talepler.length === 0 && <p className="py-6 text-center text-[11px] text-slate-400">Henüz açtığınız bir talep yok.</p>}
        {!talepLoading && talepler && talepler.map((talep) => {
          const etiket = durumEtiketi[talep.durum];
          return <article key={talep.geri_bildirim_id} className="rounded-xl border border-white/10 bg-white/5 p-3">
            <div className="flex items-center justify-between gap-2">
              <span className="text-[11px] font-bold tabular-nums text-slate-200">{talep.talep_no}</span>
              <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[9px] font-bold ${etiket.renk}`}>
                {talep.durum === 'resolved' ? <CheckCircle2 className="h-3 w-3" /> : <Clock3 className="h-3 w-3" />}{etiket.ad}
              </span>
            </div>
            <p className="mt-1.5 line-clamp-2 text-[11px] leading-4 text-slate-300">{talep.mesaj}</p>
            {talep.yanit && <div className="mt-2 rounded-lg border border-white/10 bg-white/5 p-2">
              <p className="text-[9px] font-bold uppercase tracking-wide text-slate-400">KazKaz yanıtı</p>
              <p className="mt-0.5 text-[11px] leading-4 text-slate-200">{talep.yanit}</p>
            </div>}
            {talep.durum === 'resolved' && (talep.memnun == null ? <div className="mt-2 flex items-center gap-2">
              <span className="text-[10px] text-slate-400">Sorununuz çözüldü mü?</span>
              <button type="button" onClick={() => void memnuniyetVer(talep, true)} aria-label="Memnunum" className="grid h-7 w-7 place-items-center rounded-lg border border-emerald-400/30 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20"><ThumbsUp className="h-3.5 w-3.5" /></button>
              <button type="button" onClick={() => void memnuniyetVer(talep, false)} aria-label="Çözülmedi" className="grid h-7 w-7 place-items-center rounded-lg border border-red-400/30 bg-red-500/10 text-red-300 hover:bg-red-500/20"><ThumbsDown className="h-3.5 w-3.5" /></button>
            </div> : <p className="mt-2 text-[10px] text-slate-400">{talep.memnun ? '👍 Memnuniyetiniz kaydedildi.' : '👎 Geri bildiriminiz kaydedildi; talebi yeniden açabiliriz.'}</p>)}
          </article>;
        })}
      </div>}
      {view === 'pilot' && <div className="mt-3 rounded-xl border border-white/10 bg-white/5 p-3">
        {!pilotStatus && <p className="py-4 text-center text-[11px] text-slate-400">Pilot değerlendirmesi kontrol ediliyor…</p>}
        {pilotStatus && !pilotStatus.uygun && <p className="text-[11px] leading-5 text-slate-300">Pilot devam değerlendirmesi ölçüm döneminin son haftasında şirket yöneticisine açılır.</p>}
        {pilotStatus?.yanitlandi && <p className="text-[11px] font-bold leading-5 text-emerald-300">Pilot değerlendirmeniz kaydedildi. Teşekkürler.</p>}
        {pilotStatus?.uygun && !pilotStatus.yanitlandi && <div>
          <p className="text-[11px] leading-5 text-slate-300">KazKaz’ı pilot sonrasında kullanmaya devam etme niyetiniz nedir?</p>
          <select aria-label="Devam niyeti" value={intent} onChange={(event) => setIntent(event.target.value as typeof intent)} className="mt-2 w-full rounded-lg border border-white/10 bg-[#10172b] px-3 py-2 text-xs">
            <option value="kesinlikle">Kesinlikle devam ederiz</option><option value="muhtemelen">Muhtemelen devam ederiz</option><option value="kararsiz">Kararsızız</option><option value="muhtemelen_hayir">Muhtemelen devam etmeyiz</option><option value="kesinlikle_hayir">Devam etmeyiz</option>
          </select>
          <label className="mt-3 block text-[10px] text-slate-300">Ücretli planda devam etmeyi değerlendirir misiniz?<select aria-label="Ücretli devam niyeti" value={paidContinuation === null ? '' : paidContinuation ? 'evet' : 'hayir'} onChange={(event) => setPaidContinuation(event.target.value === '' ? null : event.target.value === 'evet')} className="mt-1.5 w-full rounded-lg border border-white/10 bg-[#10172b] px-3 py-2 text-xs"><option value="">Seçiniz</option><option value="evet">Evet</option><option value="hayir">Hayır</option></select></label>
          {pilotError && <p role="alert" className="mt-2 text-[10px] text-red-300">{pilotError}</p>}
          <button type="button" disabled={pilotSending || paidContinuation === null} onClick={() => void pilotGonder()} className="mt-3 w-full rounded-lg bg-orange-600 px-3 py-2 text-xs font-bold disabled:opacity-50">{pilotSending ? 'Kaydediliyor…' : 'Değerlendirmeyi kaydet'}</button>
        </div>}
      </div>}
    </div>}
    <button type="button" onClick={() => setOpen((value) => !value)} className="flex items-center gap-2 rounded-full bg-orange-600 px-4 py-3 text-xs font-bold text-white shadow-xl shadow-orange-950/30"><MessageSquareText className="h-4 w-4" /> Destek</button>
  </div>;
};

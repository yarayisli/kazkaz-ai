import React, { useState } from 'react';
import { MessageSquareText, Send, X } from 'lucide-react';
import { geriBildirimGonder } from '../lib/api';

type Category = 'hata' | 'oneri' | 'kullanilabilirlik' | 'finansal_sonuc';

export const FeedbackWidget: React.FC<{ activePage: string }> = ({ activePage }) => {
  const [open, setOpen] = useState(false);
  const [category, setCategory] = useState<Category>('kullanilabilirlik');
  const [message, setMessage] = useState('');
  const [contactAllowed, setContactAllowed] = useState(false);
  const [status, setStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (message.trim().length < 10) return;
    setStatus('sending');
    try {
      await geriBildirimGonder(category, message.trim(), activePage, contactAllowed);
      setStatus('sent');
      setMessage('');
    } catch {
      setStatus('error');
    }
  };

  return <div className="fixed bottom-5 right-5 z-50">
    {open && <form onSubmit={submit} className="mb-3 w-[min(360px,calc(100vw-2rem))] rounded-2xl border border-white/10 bg-[#10172b] p-4 text-white shadow-2xl">
      <div className="flex items-center justify-between"><h2 className="text-sm font-bold">Geri bildirim gönder</h2><button type="button" onClick={() => setOpen(false)} aria-label="Kapat"><X className="h-4 w-4 text-slate-400" /></button></div>
      <p className="mt-1 text-[10px] leading-4 text-slate-400">Finansal veri, kimlik numarası veya parola eklemeyin.</p>
      <select value={category} onChange={(event) => setCategory(event.target.value as Category)} className="mt-3 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs"><option value="kullanilabilirlik">Kullanım kolaylığı</option><option value="hata">Hata</option><option value="finansal_sonuc">Finansal sonuç</option><option value="oneri">Öneri</option></select>
      <textarea value={message} onChange={(event) => setMessage(event.target.value)} minLength={10} maxLength={2000} required rows={5} placeholder="Ne oldu, hangi sonucu bekliyordunuz?" className="mt-2 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs outline-none focus:ring-2 focus:ring-orange-500" />
      <label className="mt-2 flex items-start gap-2 text-[10px] text-slate-300"><input type="checkbox" checked={contactAllowed} onChange={(event) => setContactAllowed(event.target.checked)} /> Bu geri bildirim için benimle iletişime geçilebilir.</label>
      {status === 'sent' && <p className="mt-2 text-[10px] text-emerald-300">Teşekkürler, geri bildiriminiz kaydedildi.</p>}
      {status === 'error' && <p className="mt-2 text-[10px] text-red-300">Gönderilemedi; lütfen oturumunuzu kontrol edip yeniden deneyin.</p>}
      <button type="submit" disabled={status === 'sending' || message.trim().length < 10} className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg bg-orange-600 px-3 py-2 text-xs font-bold disabled:opacity-50"><Send className="h-3.5 w-3.5" /> {status === 'sending' ? 'Gönderiliyor…' : 'Gönder'}</button>
    </form>}
    <button type="button" onClick={() => setOpen((value) => !value)} className="flex items-center gap-2 rounded-full bg-orange-600 px-4 py-3 text-xs font-bold text-white shadow-xl shadow-orange-950/30"><MessageSquareText className="h-4 w-4" /> Geri bildirim</button>
  </div>;
};

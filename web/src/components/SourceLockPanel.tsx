import React from 'react';
import { Check, ShieldCheck, X } from 'lucide-react';
import type { CfoSohbetYaniti } from '../lib/api';

interface SourceLockPanelProps {
  dogrulama: CfoSohbetYaniti['ai_dogrulama'];
}

/**
 * Kaynak kilidi paneli.
 *
 * AI cevabındaki her sayının hangi finansal kalemden geldiğini gösterir.
 * Kaynağı bulunamayan sayı varsa cevap zaten yayınlanmamıştır; panel
 * bunu da nedeniyle birlikte söyler.
 */
export const SourceLockPanel: React.FC<SourceLockPanelProps> = ({ dogrulama }) => {
  if (!dogrulama) return null;

  const eslesmeler = dogrulama.kaynak_eslesmeleri || [];
  const reddedilen = dogrulama.reddedilen_sayilar || [];
  if (eslesmeler.length === 0 && reddedilen.length === 0) return null;

  const engellendi = reddedilen.length > 0;

  return (
    <section className="panel-card p-4">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="panel-kicker">Kaynak Kilidi</p>
          <p className="mt-1 text-sm font-extrabold text-[#0f1729]">Cevaptaki her sayı</p>
        </div>
        <span
          className={`shrink-0 rounded-full border px-2.5 py-1 text-[10px] font-bold ${
            engellendi
              ? 'border-red-200 bg-red-50 text-red-700'
              : 'border-emerald-200 bg-emerald-50 text-emerald-700'
          }`}
        >
          {engellendi
            ? `${reddedilen.length} rakam kaynaksız`
            : `${eslesmeler.length} rakam · hepsi bağlı`}
        </span>
      </div>

      <ul className="space-y-1.5">
        {eslesmeler.map((eslesme, index) => (
          <li
            key={`kabul-${eslesme.ham}-${index}`}
            className="flex items-center gap-2.5 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2"
          >
            <Check className="h-3.5 w-3.5 shrink-0 text-emerald-600" strokeWidth={3} />
            <span className="shrink-0 text-[11px] font-extrabold tabular-nums text-[#0f1729]">{eslesme.ham}</span>
            <span className="min-w-0 flex-1 truncate text-right text-[11px] text-slate-500">{eslesme.kaynak}</span>
          </li>
        ))}

        {reddedilen.map((ham, index) => (
          <li
            key={`ret-${ham}-${index}`}
            className="flex items-center gap-2.5 rounded-lg border border-red-200 bg-red-50 px-3 py-2"
          >
            <X className="h-3.5 w-3.5 shrink-0 text-red-600" strokeWidth={3} />
            <span className="shrink-0 text-[11px] font-extrabold tabular-nums text-red-700">{ham}</span>
            <span className="min-w-0 flex-1 truncate text-right text-[11px] font-semibold text-red-600">
              Kaynak bulunamadı
            </span>
          </li>
        ))}
      </ul>

      <p className="mt-3 flex items-start gap-2 border-t border-slate-100 pt-3 text-[11px] leading-4 text-slate-500">
        <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-violet-600" />
        {engellendi
          ? 'Kaynağı olmayan sayı bulunduğu için AI yanıtı yayınlanmadı; yerine kurallı finans özeti gösterildi.'
          : 'Bir cevaptaki tek bir sayı bile veriye bağlanamazsa cevabın tamamı yayınlanmaz.'}
      </p>
    </section>
  );
};

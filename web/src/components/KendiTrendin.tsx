import React from 'react';
import { ArrowDownRight, ArrowUpRight, CircleAlert, Clock3, Minus } from 'lucide-react';
import type { KendiTrendi, TrendDegisimi } from '../lib/api';
import { paraBicimlendirici } from '../lib/metrikler';

interface KendiTrendinProps {
  trend: KendiTrendi | null | undefined;
  paraBirimi: string;
  onNavigateTab: (tabId: string) => void;
}

const bicimle = (deger: number, birim: TrendDegisimi['birim'], para: (d: number) => string) => {
  switch (birim) {
    case 'tutar': return para(deger);
    case 'yuzde': return `%${deger.toLocaleString('tr-TR', { maximumFractionDigits: 1 })}`;
    case 'gun': return `${deger.toLocaleString('tr-TR', { maximumFractionDigits: 0 })} gün`;
    case 'kat': return `${deger.toLocaleString('tr-TR', { maximumFractionDigits: 2 })}x`;
    default: return String(deger);
  }
};

const TrendSatiri: React.FC<{ d: TrendDegisimi; para: (n: number) => string }> = ({ d, para }) => {
  const iyi = d.deger_yargisi === 'iyi';
  const kotu = d.deger_yargisi === 'kotu';
  const Ikon = d.yon === 'sabit' ? Minus : d.yon === 'artti' ? ArrowUpRight : ArrowDownRight;

  return (
    <li className={`flex flex-col gap-2 rounded-xl border p-3.5 sm:flex-row sm:items-center sm:gap-4 ${
      kotu ? 'border-red-200 bg-red-50/60' : iyi ? 'border-emerald-200 bg-emerald-50/60' : 'border-slate-200 bg-white'
    }`}>
      <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-white ${
        kotu ? 'text-red-600' : iyi ? 'text-emerald-600' : 'text-slate-400'
      }`}>
        <Ikon className="h-4 w-4" />
      </span>

      <div className="min-w-0 flex-1">
        <p className="text-xs font-bold text-[#0a1628]">{d.etiket}</p>
        <p className="mt-1 text-[11px] tabular-nums text-slate-600">
          {bicimle(d.onceki, d.birim, para)} <span className="text-slate-400">→</span>{' '}
          <strong className="text-slate-900">{bicimle(d.son, d.birim, para)}</strong>
          {d.goreli_degisim_yuzde != null && (
            <span className={kotu ? 'text-red-700' : iyi ? 'text-emerald-700' : 'text-slate-500'}>
              {' '}({d.goreli_degisim_yuzde > 0 ? '+' : ''}
              {d.goreli_degisim_yuzde.toLocaleString('tr-TR', { maximumFractionDigits: 1 })}%)
            </span>
          )}
        </p>
      </div>

      {d.nakit_etkisi != null && d.nakit_etkisi !== 0 && (
        <div className={`shrink-0 rounded-lg px-3 py-2 text-right ${d.nakit_etkisi > 0 ? 'bg-red-100/70' : 'bg-emerald-100/70'}`}>
          <p className={`text-[9px] font-black uppercase tracking-wide ${d.nakit_etkisi > 0 ? 'text-red-700' : 'text-emerald-700'}`}>
            {d.nakit_etkisi > 0 ? 'Bağlanan para' : 'Serbest kalan'}
          </p>
          <p className={`text-xs font-extrabold tabular-nums ${d.nakit_etkisi > 0 ? 'text-red-800' : 'text-emerald-800'}`}>
            {para(Math.abs(d.nakit_etkisi))}
          </p>
        </div>
      )}
    </li>
  );
};

/**
 * Şirketi sektör ortalamasıyla değil kendi geçmişiyle karşılaştırır.
 *
 * Sektör ortalaması "normal miyim?" sorusuna cevap verir ve karar
 * üretmez. Kendi trendi "ne değişti, ne yapmalıyım?" sorusuna cevap
 * verir — tahsilat süresi uzadığında kaç lira bağlandığını söyler.
 */
export const KendiTrendin: React.FC<KendiTrendinProps> = ({ trend, paraBirimi, onNavigateTab }) => {
  const para = paraBicimlendirici(paraBirimi);

  if (!trend || trend.durum === 'gecmis_yok') {
    return (
      <section className="panel-card p-5">
        <p className="panel-kicker">Kendi Trendin</p>
        <h2 className="mt-2 text-lg font-bold text-[#0a1628]">Karşılaştırma için geçmiş gerekiyor</h2>
        <div className="mt-4 flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <Clock3 className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
          <p className="text-xs leading-5 text-slate-600">
            Şirketinizin kendi geçmişiyle karşılaştırılması, en az iki dönemlik mizan
            yüklendiğinde başlar. Şu an{' '}
            <strong className="text-slate-800">{trend?.donem_sayisi ?? 0} dönem</strong> var.{' '}
            <button type="button" onClick={() => onNavigateTab('data-entry')} className="font-bold text-violet-700 underline decoration-violet-300 underline-offset-2">
              Geçmiş dönem mizanı yükleyin
            </button>
            .
          </p>
        </div>
      </section>
    );
  }

  const onemliler = trend.degisimler.filter((d) => d.onemli);
  const kotuler = onemliler.filter((d) => d.deger_yargisi === 'kotu');

  return (
    <section className="panel-card p-5">
      <div className="flex flex-col gap-3 border-b border-slate-200 pb-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="panel-kicker">Kendi Trendin</p>
          <h2 className="mt-2 text-lg font-bold text-[#0a1628]">Geçen döneme göre ne değişti?</h2>
          <p className="mt-1 text-xs text-slate-500">
            {trend.onceki_donem} → {trend.son_donem} · sektör ortalamasıyla değil, kendi geçmişinizle
          </p>
        </div>
        <span className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-bold ${
          kotuler.length > 0
            ? 'border-red-200 bg-red-50 text-red-700'
            : 'border-emerald-200 bg-emerald-50 text-emerald-700'
        }`}>
          {kotuler.length > 0 && <CircleAlert className="h-3 w-3" />}
          {kotuler.length > 0 ? `${kotuler.length} kalem kötüleşti` : 'Kötüleşen kalem yok'}
        </span>
      </div>

      {onemliler.length === 0 ? (
        <p className="pt-4 text-xs leading-5 text-slate-500">
          Hiçbir kalemde %5'i aşan değişim yok; dönem büyük ölçüde önceki dönemle aynı seyretti.
        </p>
      ) : (
        <ul className="mt-4 space-y-2">
          {onemliler.map((d) => <TrendSatiri key={d.metrik} d={d} para={para} />)}
        </ul>
      )}

      <p className="mt-4 border-t border-slate-100 pt-3 text-[10px] leading-4 text-slate-400">
        %5 altındaki oynamalar gürültü sayılır ve listelenmez. Tahsilat süresindeki değişimin
        nakit etkisi, farkın günlük ciroyla çarpımıdır. Gün bazlı kalemler dönem gün sayısını
        ister; verilmemişse hesaplanmaz.
      </p>
    </section>
  );
};

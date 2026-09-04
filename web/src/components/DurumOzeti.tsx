import React from 'react';
import { AlertTriangle, ArrowRight, CheckCircle2, Info } from 'lucide-react';
import type { FinansalDenetim } from '../lib/api';

interface DurumOzetiProps {
  audit: FinansalDenetim | null | undefined;
  onNavigateTab: (tabId: string) => void;
}

/**
 * "Şirketim nasıl?" sorusunun ilk ekranda gördüğü cevabı.
 *
 * İçeriği tamamen motorun ürettiği riskler ve aksiyonlardan gelir
 * (api/services.py · finansal_denetim). Bunlar Altman Z', müşteri HHI,
 * cari oran ve kâr marjı eşikleriyle hesaplanır; burada yeniden
 * yorumlanmaz, sadece gösterilir.
 */
export const DurumOzeti: React.FC<DurumOzetiProps> = ({ audit, onNavigateTab }) => {
  if (!audit) return null;

  const riskler = audit.riskler || [];
  const aksiyonlar = audit.aksiyonlar || [];
  if (riskler.length === 0 && aksiyonlar.length === 0) return null;

  const temiz = riskler.length === 0;

  return (
    <section className="grid gap-5 xl:grid-cols-[1.15fr_.85fr]">
      {/* Şimdi bakılması gerekenler */}
      <article className="panel-card p-5">
        <div className="flex items-start justify-between gap-3 border-b border-slate-200 pb-4">
          <div>
            <p className="panel-kicker">Şimdi bakılması gerekenler</p>
            <h2 className="mt-2 text-lg font-bold text-[#0a1628]">
              {temiz ? 'Tanımlı eşiklerde ihlal yok' : `${riskler.length} bulgu`}
            </h2>
          </div>
          <span
            className={`mt-1 grid h-9 w-9 shrink-0 place-items-center rounded-lg ${
              temiz ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-600'
            }`}
          >
            {temiz ? <CheckCircle2 className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
          </span>
        </div>

        {temiz ? (
          <p className="pt-4 text-xs leading-5 text-slate-500">
            Kâr marjı, likidite, alacak dengesi, Altman Z' ve müşteri yoğunlaşması eşiklerinin
            hiçbiri aşılmadı.
          </p>
        ) : (
          <ul className="divide-y divide-slate-100">
            {riskler.map((risk, index) => (
              <li key={`${index}-${risk.slice(0, 24)}`} className="flex gap-3 py-3.5">
                <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-md bg-red-50 text-[10px] font-black text-red-600">
                  {index + 1}
                </span>
                <p className="text-xs leading-5 text-slate-700">{risk}</p>
              </li>
            ))}
          </ul>
        )}
      </article>

      {/* Bu ay ne yapmalıyım */}
      <article className="panel-card flex flex-col p-5">
        <div className="border-b border-slate-200 pb-4">
          <p className="panel-kicker">Bu ay</p>
          <h2 className="mt-2 text-lg font-bold text-[#0a1628]">Ne yapmalıyım?</h2>
        </div>

        <ol className="flex-1 divide-y divide-slate-100">
          {aksiyonlar.map((aksiyon, index) => (
            <li key={`${index}-${aksiyon.slice(0, 24)}`} className="flex gap-3 py-3.5">
              <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-md bg-[#0f2252] text-[10px] font-black text-white">
                {index + 1}
              </span>
              <p className="text-xs leading-5 text-slate-700">{aksiyon}</p>
            </li>
          ))}
        </ol>

        <button
          type="button"
          onClick={() => onNavigateTab('cfo-agent')}
          className="panel-primary-button mt-4 w-full"
        >
          CFO'ya sor <ArrowRight className="h-3.5 w-3.5" />
        </button>

        <p className="mt-3 flex items-start gap-2 text-[10px] leading-4 text-slate-400">
          <Info className="mt-px h-3 w-3 shrink-0" />
          Bu adımlar kurallı finans motorundan gelir; uygulanmadan önce insan onayı gerektirir.
        </p>
      </article>
    </section>
  );
};

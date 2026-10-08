import React from 'react';
import { AlertTriangle, ArrowRight, CheckCircle2, Info } from 'lucide-react';
import type { FinansalDenetim, SaglikSkoru } from '../lib/api';

interface DurumOzetiProps {
  audit: FinansalDenetim | null | undefined;
  /** Zaman serisinden hesaplanan skor; yoksa kart çizilmez. */
  healthScore?: SaglikSkoru | null;
  onNavigateTab: (tabId: string) => void;
}

const BOYUT_ETIKETLERI: Record<string, string> = {
  karlilik: 'Kârlılık',
  buyume: 'Büyüme',
  gider_kontrolu: 'Gider kontrolü',
  nakit: 'Nakit',
  konsantrasyon: 'Müşteri yoğunluğu',
};

/** 60 altı turuncu, üstü lacivert — Durum ekranının uyarı dili. */
const boyutRengi = (deger: number) => (deger < 60 ? '#b54708' : '#0f2252');

const SaglikSkoruKarti: React.FC<{ skor: SaglikSkoru }> = ({ skor }) => {
  const boyutlar = Object.entries(skor.alt_skorlar);
  const boyutSayisi = Number(skor.metodoloji?.boyut_sayisi) || boyutlar.length;

  return (
    <article className="financial-health-card md:col-span-2" aria-label="Finansal sağlık">
      <div className="financial-health-layout">
        <div className="financial-health-summary">
          <h2 className="text-lg font-bold text-[#0f2252]">Finansal sağlık</h2>

          <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2">
            <div className="flex items-baseline gap-2">
              <span className="font-display text-[56px] font-semibold leading-none tracking-tight tabular-nums text-[#0f2252]">
                {skor.skor.toLocaleString('tr-TR', { maximumFractionDigits: 1 })}
              </span>
              <span className="text-sm font-medium text-slate-500">/ 100</span>
              </div>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                {skor.kategori}
              </span>
          </div>
          <p className="mt-3 max-w-sm text-sm leading-6 text-slate-600">{skor.aciklama}</p>
        </div>

        <dl className="financial-health-dimensions">
          {boyutlar.map(([ad, deger]) => (
            <div key={ad} className="financial-health-row">
              <dt className="min-w-0 text-sm font-medium text-slate-700">{BOYUT_ETIKETLERI[ad] ?? ad}</dt>
              <dd className="financial-health-value">
                <div className="financial-health-track" aria-hidden="true">
                  <div
                    className="h-full rounded-full"
                    style={{ width: `${Math.min(100, Math.max(0, deger))}%`, background: boyutRengi(deger) }}
                  />
                </div>
                <span className="text-right text-sm font-semibold tabular-nums" style={{ color: boyutRengi(deger) }}>
                  {deger.toLocaleString('tr-TR', { maximumFractionDigits: 1 })}
                  <span className="sr-only"> / 100</span>
                </span>
              </dd>
            </div>
          ))}
        </dl>
      </div>

      <p className="mt-5 flex items-start gap-2 border-t border-slate-200/70 pt-4 text-xs leading-5 text-slate-500">
        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
        <span>
          {boyutSayisi} boyutlu ağırlıklı skor.{' '}
          {boyutSayisi < 5
            ? 'Müşteri sütununu yüklerseniz konsantrasyon riski de skorlanır.'
            : 'Müşteri konsantrasyon riski dahil.'}{' '}
          Nominal değerlere dayanır; enflasyon düzeltmesi uygulanmaz.
        </span>
      </p>
    </article>
  );
};

/**
 * "Şirketim nasıl?" sorusunun ilk ekranda gördüğü cevabı.
 *
 * İçeriği tamamen motorun ürettiği riskler ve aksiyonlardan gelir
 * (api/services.py · finansal_denetim). Bunlar Altman Z', müşteri HHI,
 * cari oran ve kâr marjı eşikleriyle hesaplanır; burada yeniden
 * yorumlanmaz, sadece gösterilir.
 */
export const DurumOzeti: React.FC<DurumOzetiProps> = ({ audit, healthScore, onNavigateTab }) => {
  if (!audit) return null;

  const riskler = audit.riskler || [];
  const aksiyonlar = audit.aksiyonlar || [];
  if (riskler.length === 0 && aksiyonlar.length === 0) return null;

  const temiz = riskler.length === 0;

  return (
    <section
      className={`grid gap-5 ${healthScore ? 'md:grid-cols-2' : 'xl:grid-cols-[1.15fr_.85fr]'}`}
    >
      {healthScore && <SaglikSkoruKarti skor={healthScore} />}

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
                <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-md bg-red-50 text-xs font-black text-red-600">
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
              <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-md bg-[#0f2252] text-xs font-black text-white">
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

        <p className="mt-3 flex items-start gap-2 text-xs leading-4 text-slate-400">
          <Info className="mt-px h-3 w-3 shrink-0" />
          Bu adımlar kurallı finans motorundan gelir; uygulanmadan önce insan onayı gerektirir.
        </p>
      </article>
    </section>
  );
};

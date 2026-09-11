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
const boyutRengi = (deger: number) => (deger < 60 ? '#FF4D00' : '#0f2252');

const SaglikSkoruKarti: React.FC<{ skor: SaglikSkoru }> = ({ skor }) => {
  const boyutlar = Object.entries(skor.alt_skorlar);
  const boyutSayisi = Number(skor.metodoloji?.boyut_sayisi) || boyutlar.length;

  return (
    <article className="panel-card p-5">
      <p className="panel-kicker">Finansal sağlık</p>

      <div className="mt-3 flex items-baseline gap-2">
        <span className="font-display text-[52px] font-bold leading-none text-[#0f2252]">
          {skor.skor.toLocaleString('tr-TR', { maximumFractionDigits: 1 })}
        </span>
        <span className="text-[15px] font-semibold text-slate-400">/ 100</span>
        <span className="ml-auto rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-bold text-slate-600">
          {skor.kategori}
        </span>
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-500">{skor.aciklama}</p>

      <div className="mt-5 flex flex-col gap-3">
        {boyutlar.map(([ad, deger]) => (
          <div key={ad} className="flex flex-col gap-1.5">
            <div className="flex justify-between text-xs">
              <span className="font-semibold text-slate-700">{BOYUT_ETIKETLERI[ad] ?? ad}</span>
              <span className="font-bold tabular-nums" style={{ color: boyutRengi(deger) }}>
                {deger.toLocaleString('tr-TR', { maximumFractionDigits: 1 })}
              </span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full"
                style={{ width: `${Math.min(100, Math.max(0, deger))}%`, background: boyutRengi(deger) }}
              />
            </div>
          </div>
        ))}
      </div>

      <p className="mt-4 border-t border-slate-100 pt-3 text-[10px] leading-4 text-slate-400">
        {boyutSayisi} boyutlu ağırlıklı skor.{' '}
        {boyutSayisi < 5
          ? 'Müşteri sütununu yüklerseniz konsantrasyon riski de skorlanır.'
          : 'Müşteri konsantrasyon riski dahil.'}{' '}
        Nominal değerlere dayanır; enflasyon düzeltmesi uygulanmaz.
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
      className={`grid gap-5 ${healthScore ? 'xl:grid-cols-[.8fr_1.1fr_.85fr]' : 'xl:grid-cols-[1.15fr_.85fr]'}`}
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

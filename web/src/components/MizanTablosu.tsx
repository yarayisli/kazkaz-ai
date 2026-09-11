import React from 'react';
import { CheckCircle2, CircleAlert, FileSpreadsheet, Info } from 'lucide-react';
import type { MizanDonemi } from '../lib/api';

interface MizanTablosuProps {
  donem: MizanDonemi;
  bolum: 'income' | 'balance';
  paraBirimi: string;
  tabloSurumu?: string;
  /** 7'li maliyet hesapları — yansıtıldığı için toplanmaz. */
  yansitmaHesaplari?: string[];
  eslesmeyenHesaplar?: string[];
}

type Satir = {
  etiket: string;
  deger: number;
  /** Ara toplam satırları kalın ve çizgili gösterilir. */
  toplam?: boolean;
  /** Gider satırları eksi işaretiyle okunur. */
  negatif?: boolean;
};

const paraBicimle = (deger: number, paraBirimi: string) =>
  new Intl.NumberFormat('tr-TR', {
    style: 'currency',
    currency: paraBirimi === '₺' ? 'TRY' : paraBirimi,
    maximumFractionDigits: 0,
  }).format(deger);

const gelirSatirlari = (d: MizanDonemi): Satir[] => {
  const g = d.gelir_tablosu;
  return [
    { etiket: 'Net satışlar', deger: g.ciro },
    { etiket: 'Satışların maliyeti', deger: g.satis_maliyeti, negatif: true },
    { etiket: 'Brüt kâr', deger: g.brut_kar, toplam: true },
    { etiket: 'Faaliyet giderleri', deger: g.faaliyet_giderleri, negatif: true },
    { etiket: 'Amortisman', deger: g.amortisman, negatif: true },
    { etiket: 'Faaliyet kârı', deger: g.faaliyet_kari, toplam: true },
    { etiket: 'Faiz gideri', deger: g.faiz_gideri, negatif: true },
    { etiket: 'Vergi öncesi kâr', deger: g.vergi_oncesi_kar, toplam: true },
    { etiket: 'Vergi gideri', deger: g.vergi_gideri, negatif: true },
    { etiket: 'Net kâr', deger: g.net_kar, toplam: true },
  ];
};

const bilancoSatirlari = (d: MizanDonemi): Satir[] => {
  const b = d.bilanco;
  return [
    { etiket: 'Nakit ve benzerleri', deger: b.nakit },
    { etiket: 'Ticari alacaklar', deger: b.alacaklar },
    { etiket: 'Stoklar', deger: b.stoklar },
    { etiket: 'Diğer dönen varlıklar', deger: b.diger_donen_varliklar },
    { etiket: 'Dönen varlıklar', deger: b.donen_varliklar, toplam: true },
    { etiket: 'Duran varlıklar', deger: b.duran_varliklar },
    { etiket: 'Toplam varlıklar', deger: b.toplam_varliklar, toplam: true },
    { etiket: 'Ticari borçlar', deger: b.ticari_borc },
    { etiket: 'Kısa vadeli borçlar', deger: b.kisa_vadeli_borc },
    { etiket: 'Karşılıklar', deger: b.karsiliklar },
    { etiket: 'Uzun vadeli borçlar', deger: b.uzun_vadeli_borc },
    { etiket: 'Toplam yükümlülükler', deger: b.toplam_yukumlulukler, toplam: true },
    { etiket: 'Kayıtlı özkaynak', deger: b.kayitli_ozkaynak },
    { etiket: 'Dönem net kârı', deger: b.donem_net_kari },
    { etiket: 'Toplam özkaynak', deger: b.toplam_ozkaynak, toplam: true },
  ];
};

/**
 * Muhasebe mizanından türetilmiş gelir tablosu ve bilanço.
 *
 * Rakamlar elle girilen tek dönemlik görünümden değil, yüklenen mizanın
 * hesap bakiyelerinden gelir (api/financial_statements.py). Hesap kodları
 * Tekdüzen Hesap Planı'na göre otomatik eşlenir.
 */
export const MizanTablosu: React.FC<MizanTablosuProps> = ({
  donem,
  bolum,
  paraBirimi,
  tabloSurumu,
  yansitmaHesaplari = [],
  eslesmeyenHesaplar = [],
}) => {
  const satirlar = bolum === 'income' ? gelirSatirlari(donem) : bilancoSatirlari(donem);
  const para = (deger: number) => paraBicimle(deger, paraBirimi);
  const denk = bolum === 'balance' ? donem.bilanco.denk : donem.mizan_denk;
  const fark = bolum === 'balance' ? donem.bilanco.bilanco_farki : donem.mizan_farki;

  return (
    <section className="panel-card p-5">
      <div className="flex flex-col gap-3 border-b border-slate-200 pb-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-violet-50 text-violet-700">
            <FileSpreadsheet className="h-4 w-4" />
          </span>
          <div>
            <p className="panel-kicker">Mizandan türetildi</p>
            <h2 className="mt-1.5 text-lg font-bold text-[#0a1628]">
              {bolum === 'income' ? 'Gelir tablosu' : 'Bilanço'}
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              {donem.donem} dönemi · hesap bakiyelerinden hesaplandı
            </p>
          </div>
        </div>
        <span
          className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-bold ${
            denk
              ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
              : 'border-amber-200 bg-amber-50 text-amber-800'
          }`}
        >
          {denk ? <CheckCircle2 className="h-3 w-3" /> : <CircleAlert className="h-3 w-3" />}
          {denk
            ? bolum === 'balance' ? 'Bilanço denk' : 'Mizan denk'
            : `${para(Math.abs(fark))} fark`}
        </span>
      </div>

      <dl className="mt-4">
        {satirlar.map((satir) => (
          <div
            key={satir.etiket}
            className={`flex items-baseline justify-between gap-4 py-2.5 ${
              satir.toplam ? 'border-t border-slate-200' : ''
            }`}
          >
            <dt className={`text-xs ${satir.toplam ? 'font-extrabold text-[#0a1628]' : 'text-slate-600'}`}>
              {satir.etiket}
            </dt>
            <dd
              className={`shrink-0 text-right tabular-nums ${
                satir.toplam
                  ? 'text-sm font-extrabold text-[#0a1628]'
                  : satir.negatif
                    ? 'text-xs font-semibold text-slate-500'
                    : 'text-xs font-semibold text-slate-700'
              }`}
            >
              {satir.negatif && satir.deger !== 0 ? '−' : ''}
              {para(Math.abs(satir.deger))}
            </dd>
          </div>
        ))}
      </dl>

      {(yansitmaHesaplari.length > 0 || eslesmeyenHesaplar.length > 0) && (
        <div className="mt-4 space-y-2 border-t border-slate-100 pt-4">
          {yansitmaHesaplari.length > 0 && (
            <p className="flex items-start gap-2 text-[11px] leading-4 text-slate-500">
              <Info className="mt-px h-3 w-3 shrink-0 text-slate-400" />
              <span>
                <strong className="text-slate-700">{yansitmaHesaplari.length} maliyet hesabı</strong> toplama
                dahil edilmedi ({yansitmaHesaplari.slice(0, 6).join(', ')}
                {yansitmaHesaplari.length > 6 ? '…' : ''}). 7'li hesaplar 6'lı gruba yansıtıldığı için
                ikisini birden saymak gideri iki kez gösterirdi.
              </span>
            </p>
          )}
          {eslesmeyenHesaplar.length > 0 && (
            <p className="flex items-start gap-2 text-[11px] leading-4 text-amber-800">
              <CircleAlert className="mt-px h-3 w-3 shrink-0 text-amber-600" />
              <span>
                <strong>{eslesmeyenHesaplar.length} hesap eşleşmedi</strong> (
                {eslesmeyenHesaplar.slice(0, 6).join(', ')}
                {eslesmeyenHesaplar.length > 6 ? '…' : ''}). Mizandaki Eşleme sütununu doldurarak
                bu hesapları elle sınıflandırabilirsiniz.
              </span>
            </p>
          )}
        </div>
      )}

      <p className="mt-3 text-[10px] leading-4 text-slate-400">
        Hesap kodları Tekdüzen Hesap Planı'na göre otomatik eşlenir; mizandaki Eşleme sütunu
        doldurulmuşsa o önceliklidir.
        {tabloSurumu && <> Tablo sürümü {tabloSurumu}.</>}
      </p>
    </section>
  );
};

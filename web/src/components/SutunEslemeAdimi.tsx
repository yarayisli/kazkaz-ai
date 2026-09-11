import React, { useMemo, useState } from 'react';
import { Columns3, Save, AlertTriangle, ArrowRight } from 'lucide-react';
import type { EslesmeGerekliSonucu } from '../lib/api';

interface SutunEslemeAdimiProps {
  sonuc: EslesmeGerekliSonucu;
  /** Daha önce kaydedilmiş eşleme (normalize başlık → kanonik alan). */
  mevcutEsleme: Record<string, string>;
  /** Kullanıcı eşlemeyi kaydettiğinde birleşik eşleme ile döner. */
  onKaydet: (birlesikEsleme: Record<string, string>) => void;
  yukleniyor?: boolean;
}

/** Kanonik alan → kullanıcıya görünen okunabilir etiket. */
const ALAN_ETIKETLERI: Record<string, string> = {
  tarih: 'Tarih',
  kategori: 'Kategori / Açıklama',
  gelir: 'Gelir (Tahsilat)',
  gider: 'Gider (Ödeme)',
  musteri: 'Müşteri',
  urun: 'Ürün',
  gider_tipi: 'Gider tipi (sabit/değişken)',
  vade_tarihi: 'Vade tarihi',
};

const alanEtiketi = (alan: string) => ALAN_ETIKETLERI[alan] ?? alan.replace(/_/g, ' ');

/**
 * Standart dışı başlıklı sütunları kanonik alanlara eşletir.
 *
 * Şirket "Ciro" yazdığında yerleşik liste bunu "gelir" olarak yakalayamaz;
 * kullanıcı bir kez elle eşler, eşleme şirket bazında kaydedilir ve sonraki
 * yüklemelerde tekrar sorulmaz. Eşlemesiz bırakılan sütunlar yok sayılır.
 */
export const SutunEslemeAdimi: React.FC<SutunEslemeAdimiProps> = ({
  sonuc,
  mevcutEsleme,
  onKaydet,
  yukleniyor = false,
}) => {
  const cozulemeyenler = sonuc.sutun_eslemesi.cozulemeyen_sutunlar;
  const taninanlar = sonuc.sutun_eslemesi.taninan_sutunlar;
  const zorunluEksik = sonuc.sutun_eslemesi.zorunlu_eksik ?? [];

  // Her çözülemeyen sütun için kullanıcının seçtiği kanonik alan.
  // Anahtar normalize başlıktır; boş string "eşleme yok" demektir.
  const [secimler, setSecimler] = useState<Record<string, string>>({});

  const secim = (normalize: string) => secimler[normalize] ?? '';

  // En az bir sütun bir alana eşlendi mi? Aksi halde kaydetmek anlamsız.
  const kaydedilebilir = useMemo(
    () => Object.values(secimler).some((alan) => alan !== ''),
    [secimler],
  );

  const kaydet = () => {
    // Mevcut eşlemeyi koru, yeni seçimleri üstüne ekle. Boş seçimler atlanır.
    const birlesik: Record<string, string> = { ...mevcutEsleme };
    for (const [normalize, alan] of Object.entries(secimler)) {
      if (alan) birlesik[normalize] = alan;
    }
    onKaydet(birlesik);
  };

  return (
    <section className="mt-5 space-y-4 rounded-2xl border border-amber-200 bg-amber-50/60 p-5">
      <div className="flex items-start gap-3">
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-amber-100 text-amber-700">
          <Columns3 className="h-5 w-5" />
        </span>
        <div className="min-w-0">
          <h3 className="text-sm font-bold text-amber-950">Bazı sütunlar tanınamadı</h3>
          <p className="mt-1 text-xs leading-5 text-amber-900/80">{sonuc.mesaj}</p>
          {zorunluEksik.length > 0 && (
            <p className="mt-2 flex items-center gap-1.5 text-[11px] font-bold text-amber-900">
              <AlertTriangle className="h-3.5 w-3.5" />
              Zorunlu alanlar eksik: {zorunluEksik.map((a) => alanEtiketi(a)).join(', ')}
            </p>
          )}
        </div>
      </div>

      {taninanlar.length > 0 && (
        <div className="rounded-xl border border-emerald-200 bg-white p-3">
          <p className="text-[10px] font-bold uppercase tracking-wide text-emerald-700">
            Otomatik tanınan sütunlar
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {taninanlar.map((s) => (
              <span
                key={s.indeks}
                className="inline-flex items-center gap-1 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-800"
              >
                {s.baslik} <ArrowRight className="h-3 w-3 text-emerald-400" /> {alanEtiketi(s.alan)}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-2">
        <p className="text-[11px] font-bold text-amber-950">
          Aşağıdaki sütunları eşleyin ({cozulemeyenler.length} sütun)
        </p>
        <ul className="space-y-2">
          {cozulemeyenler.map((s) => (
            <li
              key={s.indeks}
              className="flex flex-col gap-2 rounded-xl border border-slate-200 bg-white p-3 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="min-w-0">
                <p className="truncate text-xs font-bold text-slate-900">{s.baslik}</p>
                <p className="text-[10px] text-slate-400">Sütun {s.indeks + 1}</p>
              </div>
              <label className="flex items-center gap-2">
                <span className="sr-only">{s.baslik} sütununun eşleneceği alan</span>
                <select
                  value={secim(s.normalize)}
                  onChange={(e) =>
                    setSecimler((prev) => ({ ...prev, [s.normalize]: e.target.value }))
                  }
                  className="min-h-10 min-w-52 rounded-lg border border-slate-300 bg-white px-3 text-xs font-semibold text-slate-900 outline-none focus:ring-2 focus:ring-amber-500"
                >
                  <option value="">— Eşleme yok (yok say) —</option>
                  {sonuc.eslenebilir_alanlar.map((alan) => (
                    <option key={alan} value={alan}>
                      {alanEtiketi(alan)}
                    </option>
                  ))}
                </select>
              </label>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex flex-col gap-3 border-t border-amber-200 pt-4 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-[10px] leading-4 text-amber-900/70">
          Eşleme şirketiniz için kaydedilir; aynı başlıklı dosyalarda tekrar sorulmaz.
          Eşlemesiz bıraktığınız sütunlar dosyadan okunmaz.
        </p>
        <button
          type="button"
          onClick={kaydet}
          disabled={!kaydedilebilir || yukleniyor}
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-amber-600 px-4 py-2.5 text-xs font-bold text-white hover:bg-amber-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Save className="h-4 w-4" />
          {yukleniyor ? 'Kaydediliyor ve yeniden doğrulanıyor…' : 'Eşlemeyi kaydet ve yeniden dene'}
        </button>
      </div>
    </section>
  );
};

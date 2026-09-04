import React from 'react';
import { AlertTriangle, CheckCircle2, FileWarning, ShieldAlert } from 'lucide-react';
import type { VeriIceriAktarmaSonucu, VeriKalitesiBulgusu } from '../lib/api';

interface DataQualityFindingsProps {
  kalite: VeriIceriAktarmaSonucu['veri_kalitesi'];
  dosya: VeriIceriAktarmaSonucu['dosya'];
}

const sayiBicimle = (deger?: number) =>
  typeof deger === 'number' ? deger.toLocaleString('tr-TR', { maximumFractionDigits: 2 }) : null;

const BulguSatiri: React.FC<{ bulgu: VeriKalitesiBulgusu }> = ({ bulgu }) => {
  const hata = bulgu.seviye === 'hata';
  const beklenen = sayiBicimle(bulgu.beklenen);
  const gozlemlenen = sayiBicimle(bulgu.gozlemlenen);
  const sapma = sayiBicimle(bulgu.sapma_yuzde);

  return (
    <li
      className={`flex gap-3 rounded-xl border p-3 ${
        hata ? 'border-red-200 bg-red-50' : 'border-amber-200 bg-amber-50'
      }`}
    >
      <span
        className={`grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-white ${
          hata ? 'text-red-600' : 'text-amber-600'
        }`}
      >
        <AlertTriangle className="h-3.5 w-3.5" />
      </span>
      <div className="min-w-0">
        <p className={`text-xs font-bold ${hata ? 'text-red-900' : 'text-amber-900'}`}>{bulgu.mesaj}</p>
        {(beklenen !== null || gozlemlenen !== null) && (
          <p className={`mt-1 text-[11px] tabular-nums ${hata ? 'text-red-700' : 'text-amber-800'}`}>
            {beklenen !== null && <>Beklenen {beklenen}</>}
            {beklenen !== null && gozlemlenen !== null && ' ≠ '}
            {gozlemlenen !== null && <>Verilen {gozlemlenen}</>}
            {sapma !== null && <> · %{sapma} sapma</>}
          </p>
        )}
        {/* Alan adı büyük harfe çevrilmez: Türkçe yerelde ASCII "i" → "İ" olur
            ve toplam_varliklar → TOPLAM_VARLİKLAR gibi yanlış okunur. */}
        <p className="mt-1 text-[10px] font-semibold text-slate-400">Alan: {bulgu.alan.replace(/_/g, ' ')}</p>
      </div>
    </li>
  );
};

/**
 * Excel yüklendikten sonra çalışan iç denetim kurallarının sonucu.
 *
 * Bulgular içe aktarmayı engellemez — kullanıcı "çalışma alanına aktar"
 * demeden önce neyin tutmadığını görsün diye gösterilir.
 */
export const DataQualityFindings: React.FC<DataQualityFindingsProps> = ({ kalite, dosya }) => {
  const tutarlilik = kalite.tutarlilik_bulgulari || [];
  const anomali = kalite.anomali_bulgulari || [];
  const bulgular = [...tutarlilik, ...anomali];
  const atlanan = dosya.atlanan_sayfalar || [];
  const taninan = dosya['tanınan_sayfalar'] || [];

  // Arka uç bu alanları göndermiyorsa (eski sürüm) hiç render etme.
  if (kalite.semantik_durum === undefined && bulgular.length === 0 && atlanan.length === 0) return null;

  const hataSayisi = kalite.semantik_hata_sayisi ?? bulgular.filter((b) => b.seviye === 'hata').length;
  const uyariSayisi = kalite.semantik_uyari_sayisi ?? bulgular.filter((b) => b.seviye === 'uyari').length;
  const temiz = bulgular.length === 0;

  return (
    <section className={`rounded-xl border p-4 ${temiz ? 'border-emerald-200 bg-emerald-50/60' : 'border-slate-200 bg-white'}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          {temiz ? (
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
          ) : (
            <ShieldAlert className={`h-4 w-4 shrink-0 ${hataSayisi > 0 ? 'text-red-600' : 'text-amber-600'}`} />
          )}
          <div>
            <p className="text-xs font-bold text-slate-900">İç denetim kontrolleri</p>
            <p className="mt-0.5 text-[11px] text-slate-500">
              {temiz
                ? 'Bilanço, nakit akışı ve kâr tanımı tutarlı.'
                : 'Yapay zekâ yorum yapmadan önce tablo sorgulanır.'}
            </p>
          </div>
        </div>
        <span
          className={`shrink-0 rounded-full border px-2.5 py-1 text-[10px] font-bold ${
            temiz
              ? 'border-emerald-200 bg-white text-emerald-700'
              : hataSayisi > 0
                ? 'border-red-200 bg-red-50 text-red-700'
                : 'border-amber-200 bg-amber-50 text-amber-800'
          }`}
        >
          {temiz
            ? 'Temiz'
            : [hataSayisi > 0 ? `${hataSayisi} hata` : null, uyariSayisi > 0 ? `${uyariSayisi} uyarı` : null]
                .filter(Boolean)
                .join(' · ')}
        </span>
      </div>

      {bulgular.length > 0 && (
        <ul className="mt-3 space-y-2">
          {bulgular.map((bulgu, index) => (
            <BulguSatiri key={`${bulgu.kod}-${index}`} bulgu={bulgu} />
          ))}
        </ul>
      )}

      {atlanan.length > 0 && (
        <div className="mt-3 flex gap-2.5 rounded-xl border border-slate-200 bg-slate-50 p-3">
          <FileWarning className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-400" />
          <p className="text-[11px] leading-4 text-slate-600">
            <strong className="text-slate-800">{atlanan.length} sayfa okunmadı:</strong> {atlanan.join(', ')}.
            {taninan.length > 0 && <> Analiz {taninan.length} sayfadan yapıldı ({taninan.join(', ')}).</>}
          </p>
        </div>
      )}

      {hataSayisi > 0 && (
        <p className="mt-3 border-t border-slate-100 pt-3 text-[11px] leading-4 text-slate-500">
          Bulgular içe aktarmayı engellemez, ancak düzeltilmeden yapılan analiz yanıltıcı olabilir.
          Excel dosyanızı düzeltip yeniden yüklemeniz önerilir.
        </p>
      )}
    </section>
  );
};

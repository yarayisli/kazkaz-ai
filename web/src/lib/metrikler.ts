/**
 * Finansal metriklerin arayüz tarafındaki tek erişim noktası.
 *
 * Hesaplama motoru API'dedir (`api/financial_metrics.py`): her metrik
 * formül kimliği, sürümü ve güven seviyesiyle üretilir. Ekranlar bu
 * modülü kullanır; JSX içinde aritmetik yapmaz.
 *
 * Neden: BenchmarkingTab tahsilat süresini kendi hesaplarken günlük
 * ciroyu sabit 365'e bölüyordu ve çeyreklik veride sonuç dört kat
 * sapıyordu. Aynı metriğin iki yerde iki farklı sonuç vermesi, tek
 * hata değil bir hata sınıfıdır.
 *
 * Denetim yoksa (kullanıcı henüz veri doğrulamamışsa) yerel yedek
 * hesap devreye girer ama `kaynak` alanı bunu açıkça bildirir; ekran
 * isterse "doğrulanmamış" diye işaretleyebilir.
 */

import type { FinansalDenetim } from './api';
import type { FinancialData } from '../types';

/** Bir metriğin değeri ve nereden geldiği. */
export interface MetrikDegeri {
  deger: number | null;
  /** `motor`: API'nin sürümlü hesabı · `yerel`: doğrulanmamış yedek · `yok`: hesaplanamadı. */
  kaynak: 'motor' | 'yerel' | 'yok';
}

const motordan = (deger: number | null | undefined): MetrikDegeri =>
  deger == null ? { deger: null, kaynak: 'yok' } : { deger, kaynak: 'motor' };

const yerelden = (deger: number | null): MetrikDegeri =>
  deger == null ? { deger: null, kaynak: 'yok' } : { deger, kaynak: 'yerel' };

/** Önce motorun sonucunu dener; yoksa yerel yedeğe düşer. */
function tercih(motorDegeri: number | null | undefined, yerelHesap: () => number | null): MetrikDegeri {
  if (motorDegeri != null) return motordan(motorDegeri);
  return yerelden(yerelHesap());
}

export interface FinansalMetrikler {
  netKarMarji: MetrikDegeri;
  brutKarMarji: MetrikDegeri;
  cariOran: MetrikDegeri;
  borcOzkaynak: MetrikDegeri;
  /** DSO — tahsilat süresi (gün). */
  alacakDevirGunu: MetrikDegeri;
  stokDevirGunu: MetrikDegeri;
  borcDevirGunu: MetrikDegeri;
  nakitDonusumDongusu: MetrikDegeri;
  /** Günlük ciro — dönem gün sayısından; 365 varsayılmaz. */
  gunlukCiro: MetrikDegeri;
}

export function finansalMetrikler(
  data: FinancialData,
  audit?: FinansalDenetim | null,
): FinansalMetrikler {
  const m = audit?.metrikler;
  const ciro = data.revenue;
  const gun = data.periodDays;

  return {
    netKarMarji: tercih(
      m?.net_kar_marji,
      () => (ciro > 0 ? (data.netProfit / ciro) * 100 : null),
    ),
    brutKarMarji: tercih(
      // Motor brüt kârı tutar olarak verir; marja burada çevrilir.
      m?.brut_kar != null && ciro > 0 ? (m.brut_kar / ciro) * 100 : null,
      () => (ciro > 0 ? (data.grossProfit / ciro) * 100 : null),
    ),
    cariOran: tercih(
      m?.cari_oran,
      () => (data.currentAssets != null && data.shortTermDebt > 0
        ? data.currentAssets / data.shortTermDebt
        : null),
    ),
    borcOzkaynak: tercih(
      m?.borc_ozkaynak_orani,
      () => (data.equity > 0 ? (data.shortTermDebt + data.longTermDebt) / data.equity : null),
    ),
    alacakDevirGunu: tercih(
      m?.alacak_devir_gunu,
      () => (gun != null && gun > 0 && ciro > 0 ? (data.receivables / ciro) * gun : null),
    ),
    stokDevirGunu: tercih(
      m?.stok_devir_gunu,
      () => (gun != null && gun > 0 && data.costOfGoods > 0
        ? (data.inventory / data.costOfGoods) * gun
        : null),
    ),
    borcDevirGunu: tercih(
      m?.borc_devir_gunu,
      () => (gun != null && gun > 0 && data.costOfGoods > 0
        ? (data.payables / data.costOfGoods) * gun
        : null),
    ),
    nakitDonusumDongusu: motordan(m?.nakit_donusum_dongusu),
    // Günlük ciro motorda ayrı bir metrik değil; dönem gün sayısından
    // türetilir. Gün sayısı yoksa hesaplanmaz — 365 varsayılmaz.
    gunlukCiro: yerelden(gun != null && gun > 0 ? ciro / gun : null),
  };
}

/** Para birimini kayıttan alan biçimlendirici; ₺ sabitlenmez. */
export function paraBicimlendirici(paraBirimi: string) {
  const kod = paraBirimi === '₺' ? 'TRY' : paraBirimi;
  return (deger: number) =>
    new Intl.NumberFormat('tr-TR', { style: 'currency', currency: kod, maximumFractionDigits: 0 })
      .format(deger);
}

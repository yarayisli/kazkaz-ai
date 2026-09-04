import { auth } from './firebase';
import { CashFlowItem, DebtItem, FinancialData, TransactionAnalytics } from '../types';

export interface FinansalDenetim {
  sirket_adi: string;
  donem: string;
  metrikler: {
    brut_kar: number;
    favok: number | null;
    favok_durumu: 'hesaplandi' | 'eksik_veri';
    net_kar_marji: number;
    cari_oran: number | null;
    borc_ozkaynak_orani: number | null;
    net_isletme_sermayesi: number;
    altman_z_prime: number | null;
    dupont_roe: number | null;
    roic: number | null;
    serbest_nakit_akisi: number | null;
    nakit_donusum_dongusu: number | null;
    musteri_hhi: number | null;
  };
  metrik_kaydi: Record<string, {
    deger: number | null;
    birim: string;
    durum: 'hesaplandi' | 'eksik_veri';
    formula_id: string;
    formula: string;
    girdiler: Record<string, number | null>;
    kaynak_alanlar: string[];
    guven: 'yuksek' | 'orta' | 'hesaplanamadi';
    metodoloji_notu: string;
    eksik_alanlar: string[];
    formul_surumu: string;
  }>;
  riskler: string[];
  aksiyonlar: string[];
  veri_kalitesi: {
    seviye: 'iyi' | 'sinirli' | 'yetersiz';
    skor: number;
    eksikler: string[];
    uyarilar: string[];
  };
  uyari: string;
}

export interface CfoSohbetYaniti {
  yanit: string;
  kaynak: string;
  model: string;
  guven: 'dusuk' | 'orta' | 'yuksek';
  yedek_kullanildi: boolean;
  ai_dogrulama?: {
    durum: 'dogrulandi' | 'kuralli_yedek' | 'ajan_engeli' | 'veri_engeli';
    kontrol_edilen_sayi: number;
    reddedilen_sayilar: string[];
    /** Kabul edilen her sayı ve hangi kalemden geldiği. */
    kaynak_eslesmeleri?: { ham: string; kaynak: string }[];
  };
  veri_kalitesi: FinansalDenetim['veri_kalitesi'];
  ajanlar: string[];
  insan_onayi_gerekli: boolean;
  denetim: FinansalDenetim;
}

export interface CfoAjanAnalizi {
  durum: 'aktif_kontrollu';
  araclar: string[];
  uyarilar: Array<{
    seviye: string;
    baslik: string;
    mesaj: string;
    oneri: string;
    arac: string;
    deger: number;
    insan_onayi_gerekli: boolean;
  }>;
  nakit: Record<string, unknown>;
  yatirim: {
    risk_profili: string;
    hesaplanabilir: boolean;
    insan_onayi_gerekli: boolean;
    eksik_veriler: string[];
  };
  borc: {
    mevcut_borc: number;
    faiz_orani_pct: number | null;
    borc_gelir_orani: number | null;
    dscr: number | null;
    insan_onayi_gerekli: boolean;
  };
  rapor: string;
  metodoloji_onaylari: Array<{
    alan: string;
    teknik_test: string;
    uzman_onayi: string;
    kullanim: string;
  }>;
  sinirlar: string[];
}

export interface GelismisAjanAnalizi {
  durum: 'aktif';
  veri_ufku: {
    mizan: { donem_sayisi: number; donemler: string[]; karsilastirma_hazir: boolean };
    nakit: { kayit_sayisi: number; ilk: string | null; son: string | null; tam_13_hafta_penceresi: boolean };
    alacak: { kayit_sayisi: number; ilk: string | null; son: string | null };
    borc_servisi: { kayit_sayisi: number; ilk: string | null; son: string | null };
    butce: { kayit_sayisi: number; ilk: string | null; son: string | null; temel_tahmin_hazir: boolean };
  };
  bas_denetim: {
    denetci: 'bas_denetci';
    durum: 'onaylandi' | 'inceleme_gerekli' | 'engellendi';
    ai_kullanilabilir: boolean;
    ai_kapsami: 'tam' | 'sinirli' | 'temel_finansal_gorunum' | 'engelli';
    kritik_sorun_sayisi: number;
    uyari_sayisi: number;
    veri_bekleyen_ajanlar: string[];
    kontroller: Array<{
      kontrol_id: string;
      durum: 'gecti' | 'uyari' | 'kritik';
      mesaj: string;
      kaynak_ajanlar: string[];
    }>;
    kritikler: Array<{ kontrol_id: string; durum: string; mesaj: string; kaynak_ajanlar: string[] }>;
    uyarilar: Array<{ kontrol_id: string; durum: string; mesaj: string; kaynak_ajanlar: string[] }>;
    metodoloji: string;
  };
  ozet: {
    toplam: number;
    tamamlanan: number;
    inceleme_gerekli: number;
    veri_bekliyor: number;
  };
  ajanlar: Record<string, {
    ajan: string;
    durum: 'tamamlandi' | 'sinirli' | 'inceleme_gerekli' | 'veri_bekliyor';
    guven: string;
    gerekenler?: string[];
    bulgular: string[];
    tablo_surumu?: string;
    son_donem?: {
      donem: string;
      gelir_tablosu: { ciro: number; brut_kar: number; faaliyet_kari: number; net_kar: number };
      bilanco: {
        toplam_varliklar: number; toplam_yukumlulukler: number; toplam_ozkaynak: number;
        bilanco_farki: number; denk: boolean;
      };
    };
    finansal_gorunum_mutabakati?: { durum: string; uyusmayan_alanlar: string[] };
    nakit_koprusu?: { durum: string; fark?: number; eksik_alanlar?: string[] };
  }>;
}

export interface GelismisAjanGirdisi {
  rapor_tarihi?: string;
  baslangic_nakdi?: number;
  minimum_nakit_esigi?: number;
  operasyonel_nakit_akisi?: number;
  mizan?: Array<{
    donem: string;
    hesap_kodu: string;
    hesap_adi: string;
    borc: number;
    alacak: number;
    esleme?: string | null;
  }>;
  haftalik_nakit?: Array<{
    hafta: string;
    tahsilat?: number;
    nakit_satis?: number;
    diger_giris?: number;
    tedarikci?: number;
    personel?: number;
    vergi?: number;
    borc_servisi?: number;
    diger_cikis?: number;
  }>;
  alacak_faturalari?: Array<{
    fatura_id: string;
    musteri_id: string;
    musteri_adi: string;
    fatura_tarihi: string;
    vade_tarihi: string;
    tutar: number;
    odenen?: number;
  }>;
  borc_servisi?: Array<{
    borc_id: string;
    alacakli: string;
    odeme_tarihi: string;
    anapara?: number;
    faiz?: number;
    para_birimi?: string;
  }>;
  butce?: Array<{
    ay: string;
    kategori: string;
    departman?: string;
    proje?: string;
    butce?: number;
    gerceklesen?: number;
    onceki_tahmin?: number | null;
  }>;
}

export interface UyumHazirlikSonucu {
  durum: 'veri_hazirligi' | 'uzman_onayi_bekliyor' | 'hazirlik_tamamlandi';
  hazirlik_orani: number;
  hazir_baslik: number;
  uygulanabilir_baslik: number;
  basliklar: Array<{ kod: string; ad: string; uygulanabilir: boolean; hazir: boolean; gereken: string }>;
  eksikler: string[];
  metodoloji: string;
  uyari: string;
  standart_seti?: string;
  lisans_notu?: string;
}

export interface EsgHazirlikGirdisi {
  raporlama_yili: number;
  organizasyon_kapsami_tanimli: boolean;
  onemli_konular_belirlendi: boolean;
  enerji_kwh: number | null;
  scope1_tco2e: number | null;
  scope2_tco2e: number | null;
  su_m3: number | null;
  atik_ton: number | null;
  calisan_sayisi: number | null;
  kadin_calisan_orani: number | null;
  kayip_gunlu_is_kazasi: number | null;
  etik_politikasi_var: boolean;
  yonetim_sorumlusu_atandi: boolean;
  veri_kaynaklari_belgeli: boolean;
  uzman_onayi: boolean;
}

export interface TfrsHazirlikGirdisi {
  standart_seti: string;
  musteri_sozlesmeleri_var: boolean;
  hasilat_politikasi_belgeli: boolean;
  performans_yukumlulukleri_listeli: boolean;
  kiralama_sozlesmeleri_var: boolean;
  kiralama_envanteri_var: boolean;
  yabanci_para_islemleri_var: boolean;
  fonksiyonel_para_birimi_belgeli: boolean;
  stok_var: boolean;
  stok_degerleme_politikasi_belgeli: boolean;
  finansal_araclar_var: boolean;
  finansal_arac_siniflandirmasi_belgeli: boolean;
  iliskili_taraf_var: boolean;
  iliskili_taraf_listesi_var: boolean;
  nakit_akis_mutabakati_var: boolean;
  muhasebe_uzmani_onayi: boolean;
}

export interface VeriIceriAktarmaSonucu {
  durum: 'hazir' | 'uyarili';
  dosya: {
    ad: string; tur: string; boyut: number; sayfalar: string[];
    /** Finansal olarak yorumlanabilen sayfalar (Python tarafında 'tanınan_sayfalar'). */
    'tanınan_sayfalar'?: string[];
    atlanan_sayfalar?: string[];
  };
  ozet: {
    gecerli_satirlar: number;
    uyarili_satirlar: number;
    reddedilen_satirlar: number;
    toplam_gelir: number;
    toplam_gider: number;
    islem_satirlari: number;
  };
  finansal_veri: {
    sirket_adi: string; sektor: string; donem: string; ciro: number;
    satis_maliyeti: number; faaliyet_giderleri: number; net_kar: number;
    nakit: number; kisa_vadeli_borc: number; uzun_vadeli_borc: number;
    alacaklar: number; borclar: number; stoklar: number; ozkaynak: number;
    faiz_gideri?: number; vergi_gideri?: number; amortisman?: number; capex?: number;
    donen_varliklar?: number; toplam_varliklar?: number; toplam_yukumlulukler?: number;
    dagitilmamis_karlar?: number; operasyonel_nakit_akisi?: number;
    donem_basi_nakit?: number; yatirim_nakit_akisi?: number; finansman_nakit_akisi?: number;
    donem_gun_sayisi?: number; etkin_vergi_orani?: number;
    musteri_cirolari?: Array<{ musteri_id: string; musteri_adi: string; ciro: number }>;
  };
  veri_kalitesi: {
    kaynak: 'finansal_gorunum' | 'islem_ozeti';
    bilanco_mevcut: boolean;
    favok_hesaplanabilir: boolean;
    kurumsal_metrikler_hazir?: boolean;
    eksikler: string[];
    /** Muhasebe kimlikleri arası tutarlılık bulguları (api/data_quality.py). */
    tutarlilik_bulgulari?: VeriKalitesiBulgusu[];
    /** İstatistiksel anomali bulguları. */
    anomali_bulgulari?: VeriKalitesiBulgusu[];
    semantik_durum?: 'temiz' | 'uyarili' | 'hatali';
    semantik_hata_sayisi?: number;
    semantik_uyari_sayisi?: number;
  };
  gelismis_veri: GelismisAjanGirdisi;
  zaman_serisi: Array<Record<string, string | number>>;
  analizler: TransactionAnalytics;
  onizleme: Array<Record<string, unknown>>;
  hatalar: Array<{
    sayfa: string; satir: number; alan: string; kod: string; mesaj: string;
    seviye: 'hata' | 'uyari';
  }>;
  metodoloji: Record<string, string>;
}

/** api/data_quality.py'nin ürettiği tek bir kalite bulgusu. */
export interface VeriKalitesiBulgusu {
  kod: string;
  alan: string;
  mesaj: string;
  seviye: 'hata' | 'uyari';
  beklenen?: number;
  gozlemlenen?: number;
  sapma_yuzde?: number;
}

export interface SirketOlusturmaSonucu {
  durum: 'olusturuldu' | 'mevcut';
  sirket_id: string;
  sirket_adi: string;
  rol: 'admin' | 'cfo' | 'analyst' | 'viewer';
  token_yenile: boolean;
}

export interface SirketTanimaProfili {
  sirket_adi: string;
  sektor: 'teknoloji' | 'uretim' | 'perakende' | 'hizmet' | 'insaat' | 'gida' | 'lojistik' | 'diger';
  calisan_olcegi: '1-9' | '10-49' | '50-249' | '250+';
  ana_hedef: 'buyume' | 'karlilik' | 'nakit' | 'finansman' | 'maliyet';
  ana_zorluk: 'nakit' | 'marj' | 'tahsilat' | 'maliyet' | 'gorunurluk';
  veri_kaynagi: 'excel' | 'logo' | 'mikro' | 'parasut' | 'erp' | 'smmm' | 'diger';
  veri_kapsami: Array<'gelir_tablosu' | 'bilanco' | 'mizan' | 'nakit' | 'alacak' | 'borc' | 'butce'>;
  para_birimi: 'TRY' | 'USD' | 'EUR' | 'GBP' | 'CHF';
  mali_yil_baslangic_ayi: number;
}

export interface GoogleSheetsDurumu {
  yapilandirildi: boolean;
  servis_hesabi_epostasi: string | null;
  yetki: 'salt_okunur';
}

export interface PlatformAdminOzet {
  sayaclar: {
    olusturulma_zamani: string; veri_kaynagi: 'hazir' | 'sinirli'; toplam_sirket: number;
    aktif_sirket: number; pilot_sirket: number; toplam_uye: number; yeni_geri_bildirim: number;
    finansal_veri_gosterilir: false;
  };
  canli_hazirlik: {
    durum: 'hazir' | 'eksik'; kritik_kontroller: Record<string, boolean>;
    operasyon_kontrolleri: Record<string, boolean>; kritik_eksikler: string[]; operasyon_eksikleri: string[];
  };
  ai: { mod: string; politika: string; finans_motoru: string; saglayicilar: Array<{ ad: string; rol: string; hazir: boolean }>; aktif_ajanlar: string[] };
  performans: { durum: string; genel?: { orneklem: number; basari_orani: number; p50_ms: number; p95_ms: number }; operasyonlar?: Record<string, { orneklem: number; basari_orani: number; p50_ms: number; p95_ms: number }> };
  odeme: { durum: string; odeme_saglayicisi: string; eksikler: string[] };
  erp: { durum: string; saglayicilar: Record<string, { durum: string; yetki?: string }> };
  gizlilik: { finansal_veri_gosterilir: false; geri_bildirim_mesaji_gosterilir: false; kapsam: string };
}

export interface PlatformSirketListesi {
  durum: string; finansal_veri_gosterilir: false;
  sirketler: Array<{
    sirket_id: string; sirket_adi: string; plan: string; durum: string; uye_sayisi: number;
    bekleyen_davet: number; yeni_geri_bildirim: number; olusturulma: string | null; deneme_bitis: string | null;
    sektor: string; calisan_olcegi: string; veri_kaynagi: string; son_aktivite: string | null;
    son_aksiyon: string; aktivite_30_gun: number; rapor_arsivleme: number;
    veri_durumu: 'kayitli' | 'silindi' | 'veri_yok'; operasyon_sagligi: 'normal' | 'dikkat' | 'hareketsiz' | 'engelli';
  }>;
}

export interface PlatformSirketDetayi {
  durum: 'hazir';
  sirket: {
    sirket_id: string; sirket_adi: string; durum: string; plan: string; olusturulma: string | null; deneme_bitis: string | null;
    profil: { sektor: string; calisan_olcegi: string; ana_hedef: string; ana_zorluk: string; veri_kaynagi: string; veri_kapsami: string[] };
  };
  kullanim: {
    son_aktivite: string | null; son_aksiyon: string; aktivite_30_gun: number; rapor_arsivleme: number;
    rapor_indirme: number; calisma_alani_kayit: number; calisma_alani_okuma: number;
    calisma_alani_disari_aktarma: number; uyelik_islemi: number; veri_durumu: string;
    aksiyon_dagilimi: Record<string, number>;
  };
  uyeler: Array<{ kullanici_ozeti: string; eposta_maskeli: string; rol: string; eklenme: string | null }>;
  bekleyen_davetler: Array<{ davet_ozeti: string; eposta_maskeli: string; rol: string; son_gecerlilik: string | null }>;
  geri_bildirimler: Array<{ geri_bildirim_id: string; kategori: string; sayfa: string; durum: 'new' | 'in_review' | 'resolved'; iletisim_izni: boolean; zaman: string | null }>;
  son_olaylar: Array<{ aksiyon: string; kaynak: string | null; aktor: string; aktor_rolu: string; zaman: string | null }>;
  gizlilik: { finansal_veri_gosterilir: false; geri_bildirim_mesaji_gosterilir: false; epostalar_maskeli: true; kullanici_kimlikleri_ozetlenmis: true };
}

export interface PlatformOlayListesi {
  durum: string; mesaj_icerigi_gosterilir: false;
  olaylar: Array<{ olay_id: string; tur: 'geri_bildirim' | 'denetim'; sirket_id: string; sirket_adi: string; etiket: string; sayfa: string | null; durum: string; zaman: string | null }>;
}

async function apiGetIstegi<T>(yol: string): Promise<T> {
  const kullanici = auth.currentUser;
  const yerelKimlikDogrulamaKapali = import.meta.env.DEV
    && import.meta.env.VITE_API_AUTH_DISABLED === 'true';
  if (!kullanici && !yerelKimlikDogrulamaKapali) {
    throw new Error('Bu işlem için giriş yapmanız gerekiyor.');
  }
  const token = kullanici ? await kullanici.getIdToken() : null;
  const yanit = await fetch(yol, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!yanit.ok) {
    const hata = await yanit.json().catch(() => null);
    throw new Error(hata?.detail || 'KazKaz API isteği tamamlanamadı.');
  }
  return yanit.json() as Promise<T>;
}

export async function platformAdminErisiminiGetir(): Promise<boolean> {
  const kullanici = auth.currentUser;
  const token = kullanici ? await kullanici.getIdToken() : null;
  const yanit = await fetch('/api/v1/platform-admin/erisim', {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  return yanit.ok;
}

async function platformAdminGet<T>(yol: string): Promise<T> {
  const kullanici = auth.currentUser;
  const token = kullanici ? await kullanici.getIdToken() : null;
  const yanit = await fetch(yol, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
  if (!yanit.ok) {
    const hata = await yanit.json().catch(() => null);
    throw new Error(hata?.detail || 'Sistem yönetimi verisi alınamadı.');
  }
  return yanit.json() as Promise<T>;
}

async function platformAdminPost<T>(yol: string, govde: unknown): Promise<T> {
  const kullanici = auth.currentUser;
  const token = kullanici ? await kullanici.getIdToken() : null;
  const yanit = await fetch(yol, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: JSON.stringify(govde),
  });
  if (!yanit.ok) {
    const hata = await yanit.json().catch(() => null);
    throw new Error(hata?.detail || 'Sistem yönetimi işlemi tamamlanamadı.');
  }
  return yanit.json() as Promise<T>;
}

export function platformAdminOzetiniGetir() {
  return platformAdminGet<PlatformAdminOzet>('/api/v1/platform-admin/ozet');
}

export function platformSirketleriniGetir(limit = 50) {
  return platformAdminGet<PlatformSirketListesi>(`/api/v1/platform-admin/sirketler?limit=${limit}`);
}

export function platformOlaylariniGetir(limit = 50) {
  return platformAdminGet<PlatformOlayListesi>(`/api/v1/platform-admin/olaylar?limit=${limit}`);
}

export function platformSirketiniGuncelle(sirketId: string, degisiklik: { durum?: string; plan?: string; gerekce?: string }) {
  return platformAdminPost<{ durum: 'guncellendi' | 'kismen_guncellendi'; sirket_id: string; degisiklikler: Record<string, string>; oturum_yenileme_uyarisi: number }>(
    '/api/v1/platform-admin/sirket-guncelle',
    { sirket_id: sirketId, ...degisiklik },
  );
}

export function platformSirketDetayiniGetir(sirketId: string) {
  return platformAdminGet<PlatformSirketDetayi>(`/api/v1/platform-admin/sirket/${encodeURIComponent(sirketId)}`);
}

export function platformSirketEylemi(sirketId: string, eylem: 'oturumlari_sonlandir', gerekce: string) {
  return platformAdminPost<{ durum: string; sirket_id: string; eylem: string; etkilenen_kullanici: number; basarisiz_kullanici: number }>(
    '/api/v1/platform-admin/sirket-eylemi',
    { sirket_id: sirketId, eylem, gerekce },
  );
}

export function platformGeriBildirimDurumunuGuncelle(sirketId: string, geriBildirimId: string, durum: 'new' | 'in_review' | 'resolved', gerekce?: string) {
  return platformAdminPost<{ durum: string; sirket_id: string; geri_bildirim_id: string; geri_bildirim_durumu: string }>(
    '/api/v1/platform-admin/geri-bildirim-durumu',
    { sirket_id: sirketId, geri_bildirim_id: geriBildirimId, durum, ...(gerekce ? { gerekce } : {}) },
  );
}

export interface CalismaAlaniSonucu<T> {
  durum: 'hazir' | 'bos';
  schema_version?: number;
  snapshot: T | null;
}

export function calismaAlaniYukle<T>() {
  return apiGetIstegi<CalismaAlaniSonucu<T>>('/api/v1/veri/calisma-alani');
}

export function calismaAlaniKaydet<T>(snapshot: T) {
  return apiIstegi<{ durum: 'kaydedildi'; schema_version: number; boyut: number; saklama_gunu: number }>(
    '/api/v1/veri/calisma-alani/kaydet',
    { schema_version: 2, snapshot },
  );
}

export function calismaAlaniSil() {
  return apiIstegi<{ durum: 'silindi'; kapsam: string }>('/api/v1/veri/calisma-alani/sil', {});
}

export async function calismaAlaniDisaAktar(): Promise<void> {
  const kullanici = auth.currentUser;
  if (!kullanici) throw new Error('Veriyi dışa aktarmak için giriş yapmanız gerekiyor.');
  const token = await kullanici.getIdToken();
  const yanit = await fetch('/api/v1/veri/calisma-alani/disa-aktar', {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!yanit.ok) {
    const hata = await yanit.json().catch(() => null);
    throw new Error(hata?.detail || 'Çalışma alanı dışa aktarılamadı.');
  }
  const adres = URL.createObjectURL(await yanit.blob());
  const baglanti = document.createElement('a');
  baglanti.href = adres;
  baglanti.download = 'KazKaz_AI_Calisma_Alani.json';
  document.body.appendChild(baglanti);
  baglanti.click();
  baglanti.remove();
  URL.revokeObjectURL(adres);
}

function apiFinansalVeri(veri: FinancialData) {
  return {
    sirket_adi: veri.companyName,
    sektor: veri.sector,
    donem: veri.period,
    para_birimi: veri.currency === '₺' ? 'TRY' : veri.currency,
    ciro: veri.revenue,
    satis_maliyeti: veri.costOfGoods,
    faaliyet_giderleri: veri.operatingExpenses,
    net_kar: veri.netProfit,
    nakit: veri.cashInHand,
    kisa_vadeli_borc: veri.shortTermDebt,
    uzun_vadeli_borc: veri.longTermDebt,
    alacaklar: veri.receivables,
    borclar: veri.payables,
    stoklar: veri.inventory,
    ozkaynak: veri.equity,
    faiz_gideri: veri.dataQuality?.ebitdaAvailable === false ? undefined : veri.interestExpense,
    vergi_gideri: veri.dataQuality?.ebitdaAvailable === false ? undefined : veri.taxExpense,
    amortisman: veri.dataQuality?.ebitdaAvailable === false ? undefined : veri.depreciation,
    capex: veri.capex,
    donen_varliklar: veri.currentAssets,
    toplam_varliklar: veri.totalAssets,
    toplam_yukumlulukler: veri.totalLiabilities,
    dagitilmamis_karlar: veri.retainedEarnings,
    operasyonel_nakit_akisi: veri.operatingCashFlow,
    donem_basi_nakit: veri.beginningCash,
    yatirim_nakit_akisi: veri.investingCashFlow,
    finansman_nakit_akisi: veri.financingCashFlow,
    donem_gun_sayisi: veri.periodDays,
    etkin_vergi_orani: veri.effectiveTaxRate,
    musteri_cirolari: veri.customerRevenues?.map((musteri) => ({
      musteri_id: musteri.id,
      musteri_adi: musteri.name,
      ciro: musteri.revenue,
    })) || [],
  };
}

async function apiIstegi<T>(yol: string, govde: unknown): Promise<T> {
  const kullanici = auth.currentUser;
  const yerelKimlikDogrulamaKapali = import.meta.env.DEV
    && import.meta.env.VITE_API_AUTH_DISABLED === 'true';
  if (!kullanici && !yerelKimlikDogrulamaKapali) {
    throw new Error('Bu işlem için giriş yapmanız gerekiyor.');
  }
  const token = kullanici ? await kullanici.getIdToken() : null;
  const yanit = await fetch(yol, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(govde),
  });

  if (!yanit.ok) {
    const hata = await yanit.json().catch(() => null);
    throw new Error(hata?.detail || 'KazKaz API isteği tamamlanamadı.');
  }
  return yanit.json() as Promise<T>;
}

export function sirketOlustur(profil: SirketTanimaProfili) {
  return apiIstegi<SirketOlusturmaSonucu>(
    '/api/v1/sirket/olustur',
    profil,
  );
}

export type SirketRolu = 'admin' | 'cfo' | 'analyst' | 'viewer';

export interface SirketUyeListesi {
  uyeler: Array<{ kullanici_id: string; eposta: string | null; rol: SirketRolu; durum: 'aktif'; eklenme?: string }>;
  davetler: Array<{ davet_id: string; eposta: string; rol: Exclude<SirketRolu, 'admin'>; durum: 'bekliyor'; son_gecerlilik?: string }>;
}

export function sirketUyeleriniGetir() {
  return apiGetIstegi<SirketUyeListesi>('/api/v1/sirket/uyeler');
}

export function sirketUyesiDavetEt(eposta: string, rol: Exclude<SirketRolu, 'admin'>) {
  return apiIstegi<{ durum: 'davet_olusturuldu'; eposta: string; rol: string; gecerlilik_gunu: number }>(
    '/api/v1/sirket/davet', { eposta, rol },
  );
}

export function sirketDavetiniKabulEt() {
  return apiIstegi<{ durum: 'kabul_edildi'; sirket_id: string; rol: SirketRolu; token_yenile: true }>(
    '/api/v1/sirket/davet/kabul', {},
  );
}

export function sirketUyesiRolGuncelle(kullaniciId: string, rol: SirketRolu) {
  return apiIstegi<{ durum: 'rol_guncellendi'; kullanici_id: string; rol: SirketRolu }>(
    '/api/v1/sirket/uye/rol', { kullanici_id: kullaniciId, rol },
  );
}

export function sirketUyesiCikar(kullaniciId: string) {
  return apiIstegi<{ durum: 'uye_cikarildi'; kullanici_id: string }>(
    '/api/v1/sirket/uye/cikar', { kullanici_id: kullaniciId },
  );
}

export interface ArsivRaporu {
  rapor_id: string;
  sirket_adi: string;
  donem: string;
  para_birimi: string;
  surum: string;
  formatlar: Array<'pdf' | 'excel'>;
  ozet: { revenue?: number; netProfit?: number; cash?: number; totalDebt?: number; equity?: number; netMargin?: number | null; currentRatio?: number | null };
  olusturan: string;
  olusturma?: string;
}

export async function raporIndir(tur: 'pdf' | 'excel', veri: FinancialData): Promise<string | null> {
  const kullanici = auth.currentUser;
  if (!kullanici) throw new Error('Rapor indirmek için giriş yapmanız gerekiyor.');
  const token = await kullanici.getIdToken();
  const yanit = await fetch(`/api/v1/rapor/${tur}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ finansal_veri: apiFinansalVeri(veri) }),
  });
  if (!yanit.ok) {
    const hata = await yanit.json().catch(() => null);
    throw new Error(hata?.detail || 'Rapor oluşturulamadı.');
  }
  const adres = URL.createObjectURL(await yanit.blob());
  const baglanti = document.createElement('a');
  baglanti.href = adres;
  baglanti.download = tur === 'pdf' ? 'KazKaz_AI_Yonetici_Raporu.pdf' : 'KazKaz_AI_Yonetici_Raporu.xlsx';
  document.body.appendChild(baglanti);
  baglanti.click();
  baglanti.remove();
  URL.revokeObjectURL(adres);
  return yanit.headers.get('X-KazKaz-Report-Id');
}

export function raporArsiviniGetir() {
  return apiGetIstegi<{ raporlar: ArsivRaporu[] }>('/api/v1/rapor/arsiv');
}

export async function arsivRaporuIndir(raporId: string, tur: 'pdf' | 'excel'): Promise<void> {
  const kullanici = auth.currentUser;
  if (!kullanici) throw new Error('Arşiv raporunu indirmek için giriş yapmanız gerekiyor.');
  const yanit = await fetch(`/api/v1/rapor/arsiv/${encodeURIComponent(raporId)}/${tur}`, {
    headers: { Authorization: `Bearer ${await kullanici.getIdToken()}` },
  });
  if (!yanit.ok) {
    const hata = await yanit.json().catch(() => null);
    throw new Error(hata?.detail || 'Arşiv raporu indirilemedi.');
  }
  const adres = URL.createObjectURL(await yanit.blob());
  const baglanti = document.createElement('a');
  baglanti.href = adres;
  baglanti.download = `KazKaz_AI_Arsiv_${raporId}.${tur === 'pdf' ? 'pdf' : 'xlsx'}`;
  document.body.appendChild(baglanti);
  baglanti.click();
  baglanti.remove();
  URL.revokeObjectURL(adres);
}

export function arsivRaporuSil(raporId: string) {
  return apiIstegi<{ durum: 'silindi'; rapor_id: string }>(`/api/v1/rapor/arsiv/${encodeURIComponent(raporId)}/sil`, {});
}

export async function finansDosyasiDogrula(dosya: File): Promise<VeriIceriAktarmaSonucu> {
  const kullanici = auth.currentUser;
  const yerelKimlikDogrulamaKapali = import.meta.env.DEV
    && import.meta.env.VITE_API_AUTH_DISABLED === 'true';
  if (!kullanici && !yerelKimlikDogrulamaKapali) {
    throw new Error('Dosya yüklemek için giriş yapmanız gerekiyor.');
  }
  if (dosya.size > 5 * 1024 * 1024) {
    throw new Error('Dosya boyutu 5 MB sınırını aşıyor.');
  }
  const token = kullanici ? await kullanici.getIdToken() : null;
  const yanit = await fetch(`/api/v1/veri/dosya-dogrula?dosya_adi=${encodeURIComponent(dosya.name)}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/octet-stream',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: await dosya.arrayBuffer(),
  });
  if (!yanit.ok) {
    const hata = await yanit.json().catch(() => null);
    throw new Error(hata?.detail || 'Dosya doğrulanamadı.');
  }
  return yanit.json() as Promise<VeriIceriAktarmaSonucu>;
}

export function googleSheetsDurumu(): Promise<GoogleSheetsDurumu> {
  return apiGetIstegi<GoogleSheetsDurumu>('/api/v1/veri/google-sheets/durum');
}

export function googleSheetsDogrula(url: string, sayfaAdi?: string): Promise<VeriIceriAktarmaSonucu> {
  return apiIstegi<VeriIceriAktarmaSonucu>('/api/v1/veri/google-sheets/dogrula', {
    url,
    sayfa_adi: sayfaAdi?.trim() || null,
  });
}

export interface TarihselKurSonucu {
  istenen_tarih: string;
  kur_tarihi: string;
  baz_para_birimi: 'TRY';
  kurlar: Record<string, number>;
  kaynak: string;
  metodoloji: string;
}

export interface KamuyaAcikPerformans {
  durum: 'yetersiz_veri' | 'yayina_hazir';
  olusturulma_zamani: string;
  kisisel_veri_toplanir: false;
  asgari_orneklem: number;
  mesaj?: string;
  basari_orani?: number;
  p50_ms?: number;
  p95_ms?: number;
  orneklem?: string;
}

export async function kamuyaAcikPerformansiGetir(): Promise<KamuyaAcikPerformans> {
  const yanit = await fetch('/api/public/performance', {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });
  if (!yanit.ok) throw new Error('Performans özeti alınamadı.');
  return yanit.json() as Promise<KamuyaAcikPerformans>;
}

export function tarihselKurlariGetir(tarih: string, paraBirimleri: string[]): Promise<TarihselKurSonucu> {
  return apiIstegi<TarihselKurSonucu>('/api/v1/kur/tarihsel', {
    tarih,
    para_birimleri: paraBirimleri,
  });
}

export function geriBildirimGonder(
  kategori: 'hata' | 'oneri' | 'kullanilabilirlik' | 'finansal_sonuc',
  mesaj: string,
  sayfa: string,
  iletisimIzni: boolean,
): Promise<{ durum: 'alindi'; kayit_id: string }> {
  return apiIstegi('/api/v1/geri-bildirim', {
    kategori, mesaj, sayfa, iletisim_izni: iletisimIzni,
  });
}

export async function veriSablonuIndir(): Promise<void> {
  const kullanici = auth.currentUser;
  const yerelKimlikDogrulamaKapali = import.meta.env.DEV
    && import.meta.env.VITE_API_AUTH_DISABLED === 'true';
  if (!kullanici && !yerelKimlikDogrulamaKapali) {
    throw new Error('Şablonu indirmek için giriş yapmanız gerekiyor.');
  }
  const token = kullanici ? await kullanici.getIdToken() : null;
  const yanit = await fetch('/api/v1/veri/sablon', {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!yanit.ok) throw new Error('Veri şablonu indirilemedi.');
  const adres = URL.createObjectURL(await yanit.blob());
  const baglanti = document.createElement('a');
  baglanti.href = adres;
  baglanti.download = 'KazKaz_AI_V1_Veri_Sablonu.xlsx';
  document.body.appendChild(baglanti);
  baglanti.click();
  baglanti.remove();
  URL.revokeObjectURL(adres);
}

export function importedFinancialData(sonuc: VeriIceriAktarmaSonucu): FinancialData {
  const veri = sonuc.finansal_veri;
  const interestExpense = veri.faiz_gideri ?? 0;
  const taxExpense = veri.vergi_gideri ?? 0;
  const depreciation = veri.amortisman ?? 0;
  return {
    companyName: veri.sirket_adi,
    sector: veri.sektor,
    currency: 'TRY',
    period: veri.donem,
    revenue: veri.ciro,
    costOfGoods: veri.satis_maliyeti,
    grossProfit: veri.ciro - veri.satis_maliyeti,
    operatingExpenses: veri.faaliyet_giderleri,
    interestExpense,
    taxExpense,
    depreciation,
    capex: veri.capex ?? 0,
    ebitda: veri.net_kar + interestExpense + taxExpense + depreciation,
    netProfit: veri.net_kar,
    cashInHand: veri.nakit,
    shortTermDebt: veri.kisa_vadeli_borc,
    longTermDebt: veri.uzun_vadeli_borc,
    receivables: veri.alacaklar,
    payables: veri.borclar,
    inventory: veri.stoklar,
    equity: veri.ozkaynak,
    currentAssets: veri.donen_varliklar,
    totalAssets: veri.toplam_varliklar,
    totalLiabilities: veri.toplam_yukumlulukler,
    retainedEarnings: veri.dagitilmamis_karlar,
    operatingCashFlow: veri.operasyonel_nakit_akisi,
    beginningCash: veri.donem_basi_nakit,
    investingCashFlow: veri.yatirim_nakit_akisi,
    financingCashFlow: veri.finansman_nakit_akisi,
    periodDays: veri.donem_gun_sayisi,
    effectiveTaxRate: veri.etkin_vergi_orani,
    customerRevenues: (veri.musteri_cirolari || []).map((musteri) => ({
      id: musteri.musteri_id,
      name: musteri.musteri_adi,
      revenue: musteri.ciro,
    })),
    dataQuality: {
      source: sonuc.veri_kalitesi.kaynak === 'finansal_gorunum' ? 'financial_overview' : 'transaction_summary',
      balanceAvailable: sonuc.veri_kalitesi.bilanco_mevcut,
      ebitdaAvailable: sonuc.veri_kalitesi.favok_hesaplanabilir,
      missing: sonuc.veri_kalitesi.eksikler,
    },
  };
}

export function finansalDenetim(veri: FinancialData) {
  return apiIstegi<FinansalDenetim>('/api/v1/finans/denetim', apiFinansalVeri(veri));
}

/** Zaman serisinden hesaplanan finansal sağlık skoru (financial_engine.HealthScore). */
export interface SaglikSkoru {
  skor: number;
  kategori: string;
  /** Müşteri verisi varsa 5, yoksa 4 anahtar içerir. */
  alt_skorlar: Record<string, number>;
  aciklama: string;
  uyarilar: string[];
  metodoloji: Record<string, number | string>;
}

export interface ZamanSerisiSatiri {
  tarih: string;
  kategori: string;
  gelir: number;
  gider: number;
  /** Verilirse skorun 5. boyutu (konsantrasyon riski) devreye girer. */
  musteri?: string;
}

export interface ZamanSerisiAnalizi {
  finansal: { saglik_skoru: SaglikSkoru } & Record<string, unknown>;
  nakit: Record<string, unknown>;
}

/**
 * Sağlık skoru tek dönemlik veriden hesaplanamaz; en az birkaç dönemlik
 * işlem satırı ister. Excel içe aktarımının zaman_serisi çıktısı bu
 * uca doğrudan verilebilir.
 */
export function zamanSerisiAnalizi(
  satirlar: ZamanSerisiSatiri[],
  bilanco?: { baslangic_nakiti?: number; donen_varliklar?: number; kisa_vadeli_borc?: number; stoklar?: number },
) {
  return apiIstegi<ZamanSerisiAnalizi>('/api/v1/finans/zaman-serisi', {
    satirlar,
    bilanco: bilanco || {},
  });
}

export function cfoSohbet(
  mesaj: string,
  veri: FinancialData,
  gecmis: Array<{ rol: 'kullanici' | 'asistan'; icerik: string }>,
  ajanDenetimi?: GelismisAjanAnalizi['bas_denetim'],
  sirketProfili?: { ana_hedef: SirketTanimaProfili['ana_hedef']; ana_zorluk: SirketTanimaProfili['ana_zorluk'] },
) {
  return apiIstegi<CfoSohbetYaniti>(
    '/api/v1/cfo/sohbet',
    { mesaj, finansal_veri: apiFinansalVeri(veri), gecmis: gecmis.slice(-10), ajan_denetimi: ajanDenetimi, sirket_profili: sirketProfili },
  );
}

export function cfoAjanAnalizi(
  veri: FinancialData,
  nakitAkisi: CashFlowItem[],
  borclar: DebtItem[],
) {
  return apiIstegi<CfoAjanAnalizi>('/api/v1/cfo/ajan-analizi', {
    finansal_veri: apiFinansalVeri(veri),
    nakit_akisi: nakitAkisi.map((satir) => ({
      donem: satir.month,
      giris: satir.inflow,
      cikis: satir.outflow,
      net_nakit: satir.netCash,
      kumulatif_nakit: satir.cumulativeCash,
    })),
    borclar: borclar.map((borc) => ({
      ad: borc.creditor,
      tutar: borc.amount,
      faiz_orani: borc.interestRate,
      vade: borc.dueDate,
    })),
  });
}

export function gelismisAjanAnalizi(veri: FinancialData, girdiler: GelismisAjanGirdisi = {}) {
  const bugun = new Date().toISOString().slice(0, 10);
  // NOT: girdiler önce, fallback'ler sonra. Aksi durumda trailing spread
  // `baslangic_nakdi`, `operasyonel_nakit_akisi`, `rapor_tarihi`'yi
  // `undefined` ile üstüne yazıyor ve backend'de default 0 alınıyordu →
  // 13 haftalık nakit projeksiyonu sıfırdan başlıyor, sahte "kritik
  // runway" uyarıları üretiyordu.
  return apiIstegi<GelismisAjanAnalizi>('/api/v1/cfo/gelismis-ajanlar', {
    finansal_veri: apiFinansalVeri(veri),
    mizan: [],
    haftalik_nakit: [],
    alacak_faturalari: [],
    borc_servisi: [],
    butce: [],
    ...girdiler,
    // Fallback alanlar: girdiler'de tanımsız/null ise devreye girer.
    rapor_tarihi:            girdiler.rapor_tarihi || bugun,
    baslangic_nakdi:         girdiler.baslangic_nakdi ?? veri.cashInHand,
    minimum_nakit_esigi:     girdiler.minimum_nakit_esigi,
    operasyonel_nakit_akisi: girdiler.operasyonel_nakit_akisi ?? veri.operatingCashFlow,
  });
}

export function esgHazirliginiDegerlendir(girdi: EsgHazirlikGirdisi) {
  return apiIstegi<UyumHazirlikSonucu>('/api/v1/uyum/esg-hazirlik', girdi);
}

export function tfrsHazirliginiDegerlendir(girdi: TfrsHazirlikGirdisi) {
  return apiIstegi<UyumHazirlikSonucu>('/api/v1/uyum/tfrs-hazirlik', girdi);
}

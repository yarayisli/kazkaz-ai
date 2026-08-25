import React, { useEffect, useState } from 'react';
import { FinancialData, TransactionAnalytics } from '../types';
import { Edit3, Save, CheckCircle, Lock, ShieldAlert, UploadCloud, FileSpreadsheet, AlertTriangle, Keyboard, CircleCheckBig, FileDown, Link2, Eye } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import {
  finansalDenetim,
  finansDosyasiDogrula,
  FinansalDenetim,
  importedFinancialData,
  GelismisAjanGirdisi,
  VeriIceriAktarmaSonucu,
  veriSablonuIndir,
  googleSheetsDogrula,
  googleSheetsDurumu,
  GoogleSheetsDurumu,
  tarihselKurlariGetir,
  TarihselKurSonucu,
} from '../lib/api';

interface DataEntryTabProps {
  initialData: FinancialData;
  onSave: (updatedData: FinancialData, audit?: FinansalDenetim) => Promise<void> | void;
  onImport: (financial: FinancialData, advanced: GelismisAjanGirdisi, analytics: TransactionAnalytics, audit: FinansalDenetim) => Promise<void> | void;
}

export const DataEntryTab: React.FC<DataEntryTabProps> = ({ initialData, onSave, onImport }) => {
  const { userProfile, currentUser, isGuest } = useAuth();
  const [formData, setFormData] = useState<FinancialData>(initialData);
  const [saved, setSaved] = useState(false);
  const [saveTarget, setSaveTarget] = useState<'cloud' | 'session'>('session');
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [importResult, setImportResult] = useState<VeriIceriAktarmaSonucu | null>(null);
  const [entryMode, setEntryMode] = useState<'excel' | 'sheets' | 'manual'>('excel');
  const [sheetUrl, setSheetUrl] = useState('');
  const [sheetName, setSheetName] = useState('');
  const [sheetsStatus, setSheetsStatus] = useState<GoogleSheetsDurumu | null>(null);
  const [fxDate, setFxDate] = useState(new Date().toISOString().slice(0, 10));
  const [fxResult, setFxResult] = useState<TarihselKurSonucu | null>(null);
  const [fxLoading, setFxLoading] = useState(false);

  const isReadOnly = userProfile?.role === 'viewer';
  const coreFields = [formData.companyName, formData.period, formData.revenue, formData.netProfit, formData.cashInHand];
  const coreCompletion = Math.round(coreFields.filter((value) => value !== '' && value !== undefined && value !== null).length / coreFields.length * 100);

  useEffect(() => {
    if (entryMode !== 'sheets' || sheetsStatus) return;
    let aktif = true;
    void googleSheetsDurumu()
      .then((durum) => { if (aktif) setSheetsStatus(durum); })
      .catch((err) => { if (aktif) setSyncError(err instanceof Error ? err.message : 'Google Sheets durumu alınamadı.'); });
    return () => { aktif = false; };
  }, [entryMode, sheetsStatus]);

  const handleFile = async (file?: File) => {
    if (!file || isReadOnly) return;
    setUploading(true);
    setSyncError(null);
    setImportResult(null);
    try {
      setImportResult(await finansDosyasiDogrula(file));
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : 'Dosya doğrulanamadı.');
    } finally {
      setUploading(false);
    }
  };

  const handleGoogleSheet = async () => {
    if (!sheetUrl.trim() || isReadOnly) return;
    setUploading(true);
    setSyncError(null);
    setImportResult(null);
    try {
      setImportResult(await googleSheetsDogrula(sheetUrl.trim(), sheetName));
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : 'Google Sheet doğrulanamadı.');
    } finally {
      setUploading(false);
    }
  };

  const handleFxLookup = async () => {
    setFxLoading(true);
    setSyncError(null);
    try {
      setFxResult(await tarihselKurlariGetir(fxDate, ['USD', 'EUR', 'GBP', 'CHF']));
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : 'Tarihsel kur alınamadı.');
    } finally {
      setFxLoading(false);
    }
  };

  const applyImport = async () => {
    if (!importResult || isReadOnly) return;
    const imported = importedFinancialData(importResult);
    setIsSyncing(true);
    setSyncError(null);
    try {
      const audit = await finansalDenetim(imported);
      setFormData(imported);
      await onImport(imported, importResult.gelismis_veri, importResult.analizler, audit);
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : 'Kurumsal finans metrikleri hesaplanamadı.');
    } finally {
      setIsSyncing(false);
    }
  };

  const handleChange = (field: keyof FinancialData, value: any) => {
    if (isReadOnly) return;
    // FinancialData'nın sayısal alanları number tipinde tutulmalı.
    // HTML <input type="number"> her zaman string döner; boş string 0'a
    // çevrilmeli, yoksa ileride `formData.revenue + formData.costOfGoods`
    // string concat üretiyordu (örn. "1000" + "200" = "1000200").
    const prevValue = (formData as unknown as Record<string, unknown>)[field as string];
    const shouldCoerce = typeof prevValue === 'number' && typeof value !== 'number';
    const normalized = shouldCoerce
      ? (value === '' || value === null || value === undefined ? 0 : Number(value))
      : value;
    setFormData((prev) => ({
      ...prev,
      [field]: normalized,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isReadOnly) return;

    setIsSyncing(true);
    setSyncError(null);

    // Auto-calculate derived fields
    const grossProfit = formData.revenue - formData.costOfGoods;
    const ebitda = formData.netProfit + formData.interestExpense + formData.taxExpense + formData.depreciation;
    const updated = {
      ...formData,
      grossProfit,
      ebitda,
    };

    try {
      let audit: FinansalDenetim | undefined;
      if (currentUser && !isGuest) {
        if (!userProfile?.companyId) {
          throw new Error('Şirket üyeliğiniz henüz yapılandırılmamış. Yönetici daveti veya şirket kurulumu gerekli.');
        }
        audit = await finansalDenetim(updated);
        setSaveTarget('cloud');
      } else {
        setSaveTarget('session');
        try {
          audit = await finansalDenetim(updated);
        } catch {
          // Kimliksiz demo oturumu API kapalıysa temel form yine yerelde kullanılabilir.
        }
      }
      await onSave(updated, audit);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      console.error('Finansal veri doğrulama/kayıt hatası:', err);
      setSyncError(err instanceof Error ? err.message : 'Veriler kaydedilemedi.');
    } finally {
      setIsSyncing(false);
    }
  };

  const importPreview = importResult && (
    <div className="mt-5 space-y-4 border-t border-slate-200 pt-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-bold text-slate-900">{importResult.dosya.ad}</p>
          <p className="text-[11px] text-slate-500">
            {importResult.dosya.sayfalar.length} sayfa · {(importResult.dosya.boyut / 1024).toFixed(1)} KB
          </p>
        </div>
        <button
          type="button"
          onClick={() => void applyImport()}
          disabled={isSyncing}
          className="rounded-xl bg-emerald-600 px-4 py-2.5 text-xs font-bold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSyncing ? 'Kurumsal metrikler hesaplanıyor…' : 'Doğrulanan veriyi çalışma alanına aktar'}
        </button>
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {[
          ['Geçerli kayıt', importResult.ozet.gecerli_satirlar.toLocaleString('tr-TR')],
          ['Reddedilen', importResult.ozet.reddedilen_satirlar.toLocaleString('tr-TR')],
          ['İşlem geliri', `₺${importResult.ozet.toplam_gelir.toLocaleString('tr-TR')}`],
          ['İşlem gideri', `₺${importResult.ozet.toplam_gider.toLocaleString('tr-TR')}`],
        ].map(([label, value]) => (
          <div key={label} className="rounded-xl border border-slate-200 bg-white p-3">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">{label}</p>
            <p className="mt-1 text-sm font-extrabold text-slate-900">{value}</p>
          </div>
        ))}
      </div>
      {importResult.hatalar.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3">
          <p className="flex items-center gap-2 text-xs font-bold text-amber-900">
            <AlertTriangle className="h-4 w-4" />
            {importResult.hatalar.length} doğrulama bulgusu
          </p>
          <div className="mt-2 max-h-32 space-y-1 overflow-auto text-[11px] text-amber-900/80">
            {importResult.hatalar.slice(0, 20).map((hata, index) => (
              <p key={`${hata.sayfa}-${hata.satir}-${index}`}>
                <strong>{hata.sayfa} · satır {hata.satir || 'genel'}:</strong> {hata.mesaj}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="bg-white p-4 sm:p-6 rounded-xl border border-slate-200 shadow-xs space-y-6">
      <div className="flex flex-col justify-between gap-4 border-b border-slate-100 pb-5 lg:flex-row lg:items-center">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Edit3 className="w-5 h-5 text-blue-600" />
            <span>Finansal Veri Girişi & Güncelleme</span>
          </h2>
          <p className="mt-1 text-xs leading-5 text-slate-500">Dosyanızı önce doğrulayın veya temel kalemleri elle girin. Sonuçlar siz onaylamadan çalışma alanına aktarılmaz.</p>
        </div>

        {saved && (
          <span className="flex items-center gap-1.5 text-xs font-bold text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200">
            <CheckCircle className="w-4 h-4 text-emerald-600" />
            {saveTarget === 'cloud'
              ? 'Veriler doğrulandı ve şirket çalışma alanına kaydedildi.'
              : 'Veriler yalnızca bu demo oturumunda güncellendi; buluta kaydedilmedi.'}
          </span>
        )}
      </div>

      <div className="grid gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-3 sm:grid-cols-3">
        {[
          ['1', 'Veriyi seçin', entryMode === 'excel' ? 'Excel / CSV' : entryMode === 'sheets' ? 'Google Sheets' : 'Manuel giriş'],
          ['2', 'Doğrulamayı görün', importResult ? `${importResult.ozet.gecerli_satirlar} geçerli kayıt` : 'Hata ve eksikler'],
          ['3', 'Çalışma alanına aktarın', 'Finans motoru hesaplasın'],
        ].map(([step, title, detail], index) => (
          <div key={step} className={`flex items-center gap-3 rounded-xl border p-3 ${index === 0 || (index === 1 && importResult) ? 'border-violet-200 bg-white' : 'border-transparent bg-transparent'}`}>
            <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-black ${index === 0 || (index === 1 && importResult) ? 'bg-violet-700 text-white' : 'bg-slate-200 text-slate-500'}`}>{step}</span>
            <div><p className="text-xs font-extrabold text-slate-900">{title}</p><p className="mt-0.5 text-[10px] text-slate-500">{detail}</p></div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-1 rounded-xl border border-slate-200 bg-slate-100 p-1 sm:grid-cols-3" role="tablist" aria-label="Veri giriş yöntemi">
        <button type="button" role="tab" aria-selected={entryMode === 'excel'} onClick={() => setEntryMode('excel')} className={`flex min-h-11 items-center justify-center gap-2 rounded-lg px-3 text-xs font-extrabold transition ${entryMode === 'excel' ? 'bg-white text-blue-800 shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}><FileSpreadsheet className="h-4 w-4" /> Excel / CSV yükle</button>
        <button type="button" role="tab" aria-selected={entryMode === 'sheets'} onClick={() => setEntryMode('sheets')} className={`flex min-h-11 items-center justify-center gap-2 rounded-lg px-3 text-xs font-extrabold transition ${entryMode === 'sheets' ? 'bg-white text-emerald-800 shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}><Link2 className="h-4 w-4" /> Google Sheets bağla</button>
        <button type="button" role="tab" aria-selected={entryMode === 'manual'} onClick={() => setEntryMode('manual')} className={`flex min-h-11 items-center justify-center gap-2 rounded-lg px-3 text-xs font-extrabold transition ${entryMode === 'manual' ? 'bg-white text-violet-800 shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}><Keyboard className="h-4 w-4" /> Hızlı manuel giriş</button>
      </div>

      {isReadOnly && (
        <div className="p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-center gap-3">
          <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0" />
          <div>
            <span className="font-bold block">Gözlemci (Viewer) Rolündesiniz</span>
            <p className="text-amber-800">Veri değiştirme yetkisi yalnızca Admin, CFO ve Analist rollerine tanımlıdır. Sağ üstteki profilden rolünüzü değiştirerek test edebilirsiniz.</p>
          </div>
        </div>
      )}

      {syncError && (
        <div className="p-3.5 bg-red-50 border border-red-200 rounded-xl text-xs text-red-800">
          {syncError}
        </div>
      )}

      {entryMode === 'excel' && <section className="rounded-2xl border border-blue-200 bg-gradient-to-br from-blue-50 to-white p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h3 className="flex items-center gap-2 text-sm font-bold text-slate-900">
              <FileSpreadsheet className="h-5 w-5 text-blue-600" />
              Excel veya CSV ile toplu veri yükle
            </h3>
            <p className="mt-1 max-w-2xl text-xs leading-5 text-slate-600">
              Standart Tarih / Kategori / Gelir / Gider dosyasını veya KazKaz mizan, 13 haftalık nakit,
              alacak, borç servisi ve bütçe sayfalarını yükleyin. Dosya önce doğrulanır; siz onaylamadan çalışma alanına aktarılmaz.
            </p>
          </div>
          <label className={`inline-flex shrink-0 items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold text-white shadow-sm ${isReadOnly || uploading ? 'cursor-not-allowed bg-slate-400' : 'cursor-pointer bg-blue-600 hover:bg-blue-700'}`}>
            <UploadCloud className="h-4 w-4" />
            {uploading ? 'Güvenli biçimde inceleniyor…' : 'Dosya seç ve doğrula'}
            <input
              type="file"
              className="sr-only"
              accept=".xlsx,.csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv"
              disabled={isReadOnly || uploading}
              onChange={(event) => {
                void handleFile(event.target.files?.[0]);
                event.currentTarget.value = '';
              }}
            />
          </label>
        </div>
        <button
          type="button"
          onClick={() => void veriSablonuIndir().catch((err) => setSyncError(err instanceof Error ? err.message : 'Şablon indirilemedi.'))}
          className="mt-3 text-xs font-bold text-blue-700 underline decoration-blue-300 underline-offset-4"
        >
          KazKaz V1 Excel şablonunu indir
        </button>

        {importPreview}
      </section>}

      {entryMode === 'sheets' && <section className="rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-5">
        <div className="flex items-start gap-3">
          <Eye className="mt-0.5 h-5 w-5 shrink-0 text-emerald-700" />
          <div>
            <h3 className="text-sm font-bold text-slate-900">Google Sheets’i salt okunur bağlayın</h3>
            <p className="mt-1 max-w-3xl text-xs leading-5 text-slate-600">Belgeyi herkese açık yapmayın. Yalnızca aşağıdaki servis hesabını Google Sheets paylaşım ekranında <strong>Görüntüleyici</strong> olarak ekleyin. KazKaz belgeyi değiştiremez ve Drive dosyalarınızı listeleyemez.</p>
          </div>
        </div>
        <div className="mt-4 rounded-xl border border-emerald-200 bg-white p-3">
          <p className="text-[10px] font-bold uppercase tracking-wide text-slate-500">Paylaşılacak servis hesabı</p>
          <p className="mt-1 break-all text-xs font-bold text-emerald-800">{sheetsStatus?.servis_hesabi_epostasi || (sheetsStatus?.yapilandirildi === false ? 'Sunucuda henüz yapılandırılmadı' : 'Bağlantı durumu kontrol ediliyor…')}</p>
        </div>
        <div className="mt-4 grid gap-3 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)_auto]">
          <input type="url" value={sheetUrl} onChange={(event) => setSheetUrl(event.target.value)} disabled={isReadOnly || uploading || !sheetsStatus?.yapilandirildi} placeholder="https://docs.google.com/spreadsheets/d/…" aria-label="Google Sheets bağlantısı" className="min-h-11 rounded-xl border border-slate-300 bg-white px-3 text-xs text-slate-900 outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-60" />
          <input type="text" value={sheetName} onChange={(event) => setSheetName(event.target.value)} disabled={isReadOnly || uploading || !sheetsStatus?.yapilandirildi} placeholder="Sayfa adı (isteğe bağlı)" aria-label="Google Sheets sayfa adı" className="min-h-11 rounded-xl border border-slate-300 bg-white px-3 text-xs text-slate-900 outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-60" />
          <button type="button" onClick={() => void handleGoogleSheet()} disabled={isReadOnly || uploading || !sheetUrl.trim() || !sheetsStatus?.yapilandirildi} className="min-h-11 rounded-xl bg-emerald-700 px-4 text-xs font-extrabold text-white hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-50">{uploading ? 'Doğrulanıyor…' : 'Bağla ve doğrula'}</button>
        </div>
        <p className="mt-3 text-[11px] leading-5 text-slate-500">Bu ilk bağlantı standart Tarih / Kategori / Gelir / Gider işlem sayfasını okur. Mizan, 13 haftalık nakit, alacaklar ve bütçe gibi çok sayfalı kurumsal veri için Excel şablonunu kullanın.</p>
        {importPreview}
      </section>}

      {entryMode === 'manual' && <form onSubmit={handleSubmit} className="space-y-6">
        <div className="flex flex-col gap-3 rounded-xl border border-violet-200 bg-violet-50/70 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3"><CircleCheckBig className="h-5 w-5 text-violet-700" /><div><p className="text-xs font-extrabold text-violet-950">Temel veri hazırlığı %{coreCompletion}</p><p className="mt-0.5 text-[10px] text-violet-800">Boş bırakılan gelişmiş alanlarda sistem tahmin üretmez.</p></div></div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-violet-100 sm:w-40"><div className="h-full rounded-full bg-violet-700 transition-[width]" style={{ width: `${coreCompletion}%` }} /></div>
        </div>
        {/* Basic Info */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Şirket Unvanı</label>
            <input
              type="text"
              aria-label="Şirket Unvanı"
              disabled={isReadOnly}
              value={formData.companyName}
              onChange={(e) => handleChange('companyName', e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Sektör</label>
            <input
              type="text"
              aria-label="Sektör"
              disabled={isReadOnly}
              value={formData.sector}
              onChange={(e) => handleChange('sector', e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Dönem</label>
            <input
              type="text"
              aria-label="Dönem"
              disabled={isReadOnly}
              value={formData.period}
              onChange={(e) => handleChange('period', e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Raporlama Para Birimi</label>
            <select
              aria-label="Raporlama Para Birimi"
              disabled={isReadOnly}
              value={formData.currency === '₺' ? 'TRY' : formData.currency}
              onChange={(event) => handleChange('currency', event.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {['TRY', 'USD', 'EUR', 'GBP', 'CHF'].map((kod) => <option key={kod} value={kod}>{kod}</option>)}
            </select>
          </div>
        </div>

        <section className="rounded-xl border border-sky-200 bg-sky-50/70 p-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-extrabold text-sky-950">Tarihsel TCMB kur referansı</p>
              <p className="mt-1 text-[11px] leading-5 text-sky-900/70">Dönüşüm otomatik ve sessiz yapılmaz. Kur tarihini kontrol edin; muhasebe politikanıza göre tutarları raporlama para birimine çevirdikten sonra girin.</p>
            </div>
            <div className="flex gap-2">
              <input type="date" value={fxDate} max={new Date().toISOString().slice(0, 10)} onChange={(event) => setFxDate(event.target.value)} className="rounded-lg border border-sky-200 bg-white px-3 py-2 text-xs" />
              <button type="button" disabled={fxLoading} onClick={() => void handleFxLookup()} className="rounded-lg bg-sky-700 px-3 py-2 text-xs font-bold text-white disabled:opacity-50">{fxLoading ? 'Alınıyor…' : 'Resmi kuru getir'}</button>
            </div>
          </div>
          {fxResult && <div className="mt-3 flex flex-wrap gap-2">{Object.entries(fxResult.kurlar).filter(([kod]) => kod !== 'TRY').map(([kod, deger]) => <span key={kod} className="rounded-full border border-sky-200 bg-white px-3 py-1.5 text-[11px] font-bold text-sky-950">1 {kod} = {deger.toLocaleString('tr-TR', { maximumFractionDigits: 6 })} TRY</span>)}<span className="w-full text-[10px] text-sky-900/60">Kaynak: {fxResult.kaynak} · Kur tarihi: {fxResult.kur_tarihi}</span></div>}
        </section>

        {/* Income Statement Fields */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-1">
            Gelir Tablosu Kalemleri ({formData.currency === '₺' ? 'TRY' : formData.currency})
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Toplam Ciro (Gelir)</label>
              <input
                type="number"
                aria-label="Toplam Ciro (Gelir)"
                disabled={isReadOnly}
                value={formData.revenue}
                onChange={(e) => handleChange('revenue', Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Satılan Malın Maliyeti (SMM)</label>
              <input
                type="number"
                aria-label="Satılan Malın Maliyeti"
                disabled={isReadOnly}
                value={formData.costOfGoods}
                onChange={(e) => handleChange('costOfGoods', Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Faaliyet Giderleri (OPEX)</label>
              <input
                type="number"
                aria-label="Faaliyet Giderleri"
                disabled={isReadOnly}
                value={formData.operatingExpenses}
                onChange={(e) => handleChange('operatingExpenses', Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Net Kâr</label>
              <input
                type="number"
                aria-label="Net Kâr"
                disabled={isReadOnly}
                value={formData.netProfit}
                onChange={(e) => handleChange('netProfit', Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Faiz Gideri</label>
              <input
                type="number"
                aria-label="Faiz Gideri"
                min="0"
                disabled={isReadOnly}
                value={formData.interestExpense}
                onChange={(e) => handleChange('interestExpense', Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Vergi Gideri</label>
              <input
                type="number"
                aria-label="Vergi Gideri"
                min="0"
                disabled={isReadOnly}
                value={formData.taxExpense}
                onChange={(e) => handleChange('taxExpense', Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Amortisman</label>
              <input
                type="number"
                aria-label="Amortisman"
                min="0"
                disabled={isReadOnly}
                value={formData.depreciation}
                onChange={(e) => handleChange('depreciation', Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">CapEx (Yatırım Harcaması)</label>
              <input
                type="number"
                aria-label="CapEx (Yatırım Harcaması)"
                min="0"
                disabled={isReadOnly}
                value={formData.capex}
                onChange={(e) => handleChange('capex', Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
              />
            </div>
          </div>
        </div>

        {/* Balance Sheet Fields */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-1">
            Bilanço Kalemleri ({formData.currency === '₺' ? 'TRY' : formData.currency})
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Hazır Değerler (Kasa & Banka)</label>
              <input
                type="number"
                aria-label="Hazır Değerler (Kasa ve Banka)"
                disabled={isReadOnly}
                value={formData.cashInHand}
                onChange={(e) => handleChange('cashInHand', Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Kısa Vadeli Borçlar</label>
              <input
                type="number"
                aria-label="Kısa Vadeli Borçlar"
                disabled={isReadOnly}
                value={formData.shortTermDebt}
                onChange={(e) => handleChange('shortTermDebt', Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Ticari Alacaklar</label>
              <input
                type="number"
                aria-label="Ticari Alacaklar"
                disabled={isReadOnly}
                value={formData.receivables}
                onChange={(e) => handleChange('receivables', Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
              />
            </div>
            {[
              ['longTermDebt', 'Uzun Vadeli Borçlar', 0],
              ['payables', 'Ticari Borçlar', 0],
              ['inventory', 'Stoklar', 0],
              ['equity', 'Özkaynak', 0],
              ['currentAssets', 'Dönen Varlıklar', 0],
              ['totalAssets', 'Toplam Varlıklar', 0],
              ['totalLiabilities', 'Toplam Yükümlülükler', 0],
              ['retainedEarnings', 'Dağıtılmamış Kârlar', undefined],
              ['operatingCashFlow', 'Operasyonel Nakit Akışı', undefined],
              ['beginningCash', 'Dönem Başı Nakit', undefined],
              ['investingCashFlow', 'Yatırım Nakit Akışı (CFI)', undefined],
              ['financingCashFlow', 'Finansman Nakit Akışı (CFF)', undefined],
            ].map(([field, label, min]) => (
              <div key={String(field)}>
                <label className="block text-xs font-semibold text-slate-700 mb-1">{String(label)}</label>
                <input
                  type="number"
                  aria-label={String(label)}
                  min={min as number | undefined}
                  disabled={isReadOnly}
                  value={(formData[field as keyof FinancialData] as number | undefined) ?? ''}
                  onChange={(e) => handleChange(
                    field as keyof FinancialData,
                    e.target.value === '' ? undefined : Number(e.target.value),
                  )}
                  className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
                />
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-3">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-1">
            Kurumsal Metrik Parametreleri
          </h3>
          <p className="text-[11px] leading-5 text-slate-500">
            Bu alanlar Altman, ROIC, serbest nakit akışı ve tam nakit dönüşüm döngüsü için kullanılır. Boş alanlarda sonuç tahmin edilmez.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Etkin Vergi Oranı (%)</label>
              <input
                type="number"
                aria-label="Etkin Vergi Oranı (%)"
                min="0"
                max="100"
                disabled={isReadOnly}
                value={formData.effectiveTaxRate ?? ''}
                onChange={(e) => handleChange('effectiveTaxRate', e.target.value === '' ? undefined : Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Dönem Gün Sayısı</label>
              <input
                type="number"
                aria-label="Dönem Gün Sayısı"
                min="1"
                max="366"
                disabled={isReadOnly}
                value={formData.periodDays ?? ''}
                onChange={(e) => handleChange('periodDays', e.target.value === '' ? undefined : Number(e.target.value))}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
              />
            </div>
          </div>
        </div>

        <div className="pt-2">
          <button
            type="submit"
            disabled={isReadOnly || isSyncing}
            className="bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs px-6 py-2.5 rounded-lg flex items-center gap-2 transition-all cursor-pointer shadow-xs disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isReadOnly ? <Lock className="w-4 h-4" /> : <Save className="w-4 h-4" />}
            <span>{isReadOnly ? 'Değişiklik Yetkisi Yok (Sadece Okuma)' : currentUser && !isGuest ? 'Doğrula ve şirket çalışma alanına kaydet' : 'Doğrula ve bu oturumda kullan'}</span>
          </button>
        </div>
      </form>}
    </div>
  );
};

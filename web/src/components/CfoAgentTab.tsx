import React, { useEffect, useState } from 'react';
import { ApprovalDecision, CashFlowItem, ChatMessage, DebtItem, FinancialData } from '../types';
import { Bot, Send, Sparkles, Lightbulb, RefreshCw, User, CheckCircle2, ShieldAlert, Workflow, FileUp, Scale } from 'lucide-react';
import { cfoAjanAnalizi, CfoAjanAnalizi, cfoSohbet, CfoSohbetYaniti, gelismisAjanAnalizi, GelismisAjanAnalizi, GelismisAjanGirdisi } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { SourceLockPanel } from './SourceLockPanel';

interface CfoAgentTabProps {
  financialData: FinancialData;
  cashFlow: CashFlowItem[];
  debts: DebtItem[];
  advancedData?: GelismisAjanGirdisi;
  onAdvancedDataLoaded?: (data: GelismisAjanGirdisi) => void;
  onNavigateDataEntry?: () => void;
  approvals?: ApprovalDecision[];
  onApprovalsChange?: (approvals: ApprovalDecision[]) => Promise<void> | void;
}

export const CfoAgentTab: React.FC<CfoAgentTabProps> = ({ financialData, cashFlow, debts, advancedData, onAdvancedDataLoaded, onNavigateDataEntry, approvals = [], onApprovalsChange }) => {
  const { currentUser, userProfile } = useAuth();
  const hasVerifiedSession = Boolean(currentUser && userProfile?.companyId);
  const [lastDecision, setLastDecision] = useState<CfoSohbetYaniti | null>(null);
  const [agentAnalysis, setAgentAnalysis] = useState<CfoAjanAnalizi | null>(null);
  const [advancedAnalysis, setAdvancedAnalysis] = useState<GelismisAjanAnalizi | null>(null);
  const [agentLoading, setAgentLoading] = useState(true);
  const [advancedError, setAdvancedError] = useState<string | null>(null);
  const [advancedDataApplied, setAdvancedDataApplied] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      sender: 'ai',
      text: `Merhaba, ben KazKaz AI CFO asistanıyım. ${financialData.companyName} için finans motorunun hesapladığı sonuçları açıklayabilir, riskleri önceliklendirebilir ve olası aksiyonları karşılaştırabilirim.\n\nYanıtlarım karar desteğidir; muhasebe kaydı, bağımsız denetim görüşü veya yatırım tavsiyesi değildir. Eksik veri varsa bunu açıkça belirtirim.\n\nBaşlamak için nakit, kârlılık, alacaklar veya borç yapısı hakkında bir soru sorabilirsiniz.`,
      timestamp: new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [outcomeEditor, setOutcomeEditor] = useState<{
    id: string;
    owner: string;
    dueDate: string;
    expectedImpact: string;
    implementationCost: string;
    actualImpact: string;
    outcomeNote: string;
    publicationConsent: boolean;
  } | null>(null);
  const [outcomeError, setOutcomeError] = useState<string | null>(null);
  const tabloAjani = advancedAnalysis?.ajanlar.finansal_tablo_mutabakat_ajani;
  const completedAdvancedAgents = advancedAnalysis?.ozet.tamamlanan || 0;
  const totalAdvancedAgents = advancedAnalysis?.ozet.toplam || 7;
  const hasAdvancedData = Boolean(
    advancedData && [
      advancedData.mizan,
      advancedData.haftalik_nakit,
      advancedData.alacak_faturalari,
      advancedData.borc_servisi,
      advancedData.butce,
    ].some((rows) => rows && rows.length > 0),
  );
  const canDecide = userProfile?.role === 'admin' || userProfile?.role === 'cfo';

  const quickPrompts = [
    'Nakit durumumuzu etkileyen en önemli üç metriği açıklar mısın?',
    'Kârlılık ile nakit akışı neden farklı görünüyor?',
    'Borç servis kapasitemizi hangi verilerle değerlendirmeliyiz?',
    'Çalışma sermayesi için önce hangi aksiyonları incelemeliyiz?',
    'Tahsilat süresini kısaltmanın olası nakit etkisi nedir?',
  ];

  useEffect(() => {
    let active = true;
    if (!hasVerifiedSession) {
      setAgentAnalysis(null);
      setAdvancedAnalysis(null);
      setAgentLoading(false);
      return () => { active = false; };
    }
    setAgentLoading(true);
    cfoAjanAnalizi(financialData, cashFlow, debts)
      .then((result) => {
        if (active) setAgentAnalysis(result);
      })
      .catch(() => {
        if (active) setAgentAnalysis(null);
      })
      .finally(() => {
        if (active) setAgentLoading(false);
      });
    gelismisAjanAnalizi(financialData, advancedData)
      .then((result) => {
        if (active) setAdvancedAnalysis(result);
      })
      .catch(() => {
        if (active) setAdvancedAnalysis(null);
      });
    return () => {
      active = false;
    };
  }, [financialData, cashFlow, debts, advancedData, hasVerifiedSession]);

  const handleAdvancedData = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setAgentLoading(true);
    setAdvancedError(null);
    setAdvancedDataApplied(false);
    try {
      const parsed = JSON.parse(await file.text()) as GelismisAjanGirdisi;
      const result = await gelismisAjanAnalizi(financialData, parsed);
      setAdvancedAnalysis(result);
      onAdvancedDataLoaded?.(parsed);
      setAdvancedDataApplied(true);
    } catch (error) {
      setAdvancedError(error instanceof Error ? error.message : 'Ajan veri dosyası okunamadı.');
    } finally {
      setAgentLoading(false);
      event.target.value = '';
    }
  };

  const handleSend = async (textToSend?: string) => {
    const query = textToSend || input;
    if (!query.trim() || loading || !hasVerifiedSession) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const json = await cfoSohbet(
        query,
        financialData,
        messages.map((m) => ({
          rol: m.sender === 'user' ? 'kullanici' as const : 'asistan' as const,
          icerik: m.text,
        })),
        advancedAnalysis?.bas_denetim,
        userProfile?.onboardingProfile ? {
          ana_hedef: userProfile.onboardingProfile.primaryGoal as 'buyume' | 'karlilik' | 'nakit' | 'finansman' | 'maliyet',
          ana_zorluk: userProfile.onboardingProfile.primaryChallenge as 'nakit' | 'marj' | 'tahsilat' | 'maliyet' | 'gorunurluk',
        } : undefined,
      );
      setLastDecision(json);
      const mevcutAksiyonlar = new Set(approvals.map((kayit) => kayit.action));
      const evidence = Object.entries(json.denetim.metrik_kaydi)
        .filter(([, metrik]) => metrik.durum === 'hesaplandi' && metrik.deger != null)
        .slice(0, 8)
        .map(([metric, metrik]) => ({
          metric,
          value: metrik.deger as number,
          unit: metrik.birim,
          formulaId: metrik.formula_id,
        }));
      const yeniKayitlar: ApprovalDecision[] = json.denetim.aksiyonlar
        .filter((action) => !mevcutAksiyonlar.has(action))
        .map((action) => ({
          id: crypto.randomUUID(),
          action,
          status: 'pending',
          createdAt: new Date().toISOString(),
          evidence,
        }));
      if (yeniKayitlar.length) void onApprovalsChange?.([...approvals, ...yeniKayitlar]);
      const aiReply = json.yanit || 'Yanıt alınamadı.';

      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: aiReply,
        timestamp: new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: 'Sunucu ile iletişim kurulurken bir hata oluştu. Lütfen tekrar deneyin.',
        timestamp: new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const decide = (id: string, status: 'approved' | 'rejected') => {
    if (!canDecide || !currentUser) return;
    const next = approvals.map((record) => record.id === id ? {
      ...record,
      status,
      decidedAt: new Date().toISOString(),
      decidedBy: currentUser.uid,
    } : record);
    void onApprovalsChange?.(next);
  };

  const openOutcomeEditor = (record: ApprovalDecision) => {
    setOutcomeError(null);
    setOutcomeEditor({
      id: record.id,
      owner: record.owner || '',
      dueDate: record.dueDate || '',
      expectedImpact: record.expectedImpact?.toString() || '',
      implementationCost: record.implementationCost?.toString() || '',
      actualImpact: record.actualImpact?.toString() || '',
      outcomeNote: record.outcomeNote || '',
      publicationConsent: Boolean(record.publicationConsent),
    });
  };

  const saveOutcome = () => {
    if (!outcomeEditor || !currentUser || !canDecide) return;
    const expectedImpact = Number(outcomeEditor.expectedImpact);
    const implementationCost = Number(outcomeEditor.implementationCost || 0);
    const actualImpact = Number(outcomeEditor.actualImpact);
    if (!outcomeEditor.owner.trim() || !outcomeEditor.dueDate) {
      setOutcomeError('Sorumlu kişi ve hedef tarih gerekli.');
      return;
    }
    if (!Number.isFinite(expectedImpact) || expectedImpact < 0 || !Number.isFinite(implementationCost) || implementationCost < 0 || !Number.isFinite(actualImpact)) {
      setOutcomeError('Beklenen etki, maliyet ve gerçekleşen etki geçerli sayı olmalı.');
      return;
    }
    if (outcomeEditor.outcomeNote.trim().length < 10) {
      setOutcomeError('Sonuç açıklaması en az 10 karakter olmalı.');
      return;
    }
    const next = approvals.map((record) => record.id === outcomeEditor.id ? {
      ...record,
      status: 'completed' as const,
      owner: outcomeEditor.owner.trim(),
      dueDate: outcomeEditor.dueDate,
      expectedImpact,
      implementationCost,
      actualImpact,
      impactUnit: 'TRY' as const,
      outcomeNote: outcomeEditor.outcomeNote.trim(),
      measuredAt: new Date().toISOString(),
      outcomeConfirmedBy: currentUser.uid,
      publicationConsent: outcomeEditor.publicationConsent,
      publicationConsentAt: outcomeEditor.publicationConsent ? new Date().toISOString() : undefined,
      publicationConsentVersion: outcomeEditor.publicationConsent ? 'anonymous-case-v1' : undefined,
    } : record);
    void onApprovalsChange?.(next);
    setOutcomeEditor(null);
    setOutcomeError(null);
  };

  return (
    <div className="space-y-4">
      {!hasVerifiedSession && (
        <section className="flex flex-col gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-amber-950 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-extrabold">AI CFO için doğrulanmış şirket oturumu gerekli</p>
            <p className="mt-1 text-xs leading-5 text-amber-800">Demo ekranını inceleyebilirsiniz; şirket verisiyle ajan çalıştırmak, sohbet etmek ve aksiyon onaylamak için giriş yapıp finansal veriyi doğrulayın.</p>
          </div>
          {onNavigateDataEntry && <button type="button" onClick={onNavigateDataEntry} className="shrink-0 rounded-lg bg-amber-900 px-3 py-2 text-xs font-bold text-white hover:bg-amber-800">Giriş ve veri hazırlığı</button>}
        </section>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Sidebar - Context & Quick Insights */}
      <div className="lg:col-span-1 space-y-4">
        <SourceLockPanel dogrulama={lastDecision?.ai_dogrulama} />

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center gap-2 text-slate-900 font-bold text-sm border-b border-slate-100 pb-2">
            <Bot className="w-4 h-4 text-orange-600" />
            <span>AI CFO Context</span>
          </div>

          <div className="text-xs space-y-2 text-slate-600">
            <div className="flex justify-between">
              <span>Şirket:</span>
              <span className="font-semibold text-slate-900">{financialData.companyName}</span>
            </div>
            <div className="flex justify-between">
              <span>Sektör:</span>
              <span className="font-semibold text-slate-900">{financialData.sector}</span>
            </div>
            <div className="flex justify-between">
              <span>Ciro ({financialData.period}):</span>
              <span className="font-semibold text-slate-900">₺{(financialData.revenue / 1000000).toFixed(2)}M</span>
            </div>
            <div className="flex justify-between">
              <span>Net Kâr Marjı:</span>
              <span className="font-semibold text-emerald-600">{financialData.revenue > 0 ? `%${((financialData.netProfit / financialData.revenue) * 100).toFixed(1)}` : 'Veri gerekli'}</span>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
              <ShieldAlert className="h-4 w-4 text-amber-600" /> İnsan onay kuyruğu
            </div>
            <span className="rounded-full bg-amber-50 px-2 py-1 text-[10px] font-bold text-amber-700">{approvals.filter((item) => item.status === 'pending').length} bekliyor</span>
          </div>
          <div className="mt-3 max-h-72 space-y-2 overflow-auto">
            {approvals.slice().reverse().slice(0, 10).map((record) => (
              <article key={record.id} className="rounded-lg border border-slate-200 bg-slate-50 p-2.5">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-[10px] font-bold leading-4 text-slate-800">{record.action}</p>
                  <span className={`shrink-0 rounded-full px-2 py-1 text-[8px] font-extrabold uppercase ${record.status === 'completed' ? 'bg-violet-100 text-violet-700' : record.status === 'approved' ? 'bg-emerald-100 text-emerald-700' : record.status === 'rejected' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}`}>{record.status === 'completed' ? 'ölçüldü' : record.status === 'approved' ? 'onaylandı' : record.status === 'rejected' ? 'reddedildi' : 'bekliyor'}</span>
                </div>
                <p className="mt-1 text-[9px] leading-4 text-slate-500">Dayanak: {record.evidence.slice(0, 3).map((item) => `${item.metric} (${item.formulaId})`).join(' · ') || 'Hesaplanmış metrik bulunamadı'}</p>
                {record.status === 'pending' && <div className="mt-2 grid grid-cols-2 gap-2">
                  <button type="button" disabled={!canDecide} onClick={() => decide(record.id, 'approved')} className="rounded-md bg-emerald-700 px-2 py-1.5 text-[9px] font-bold text-white disabled:cursor-not-allowed disabled:opacity-40">İnceleyip onayla</button>
                  <button type="button" disabled={!canDecide} onClick={() => decide(record.id, 'rejected')} className="rounded-md border border-red-200 bg-white px-2 py-1.5 text-[9px] font-bold text-red-700 disabled:cursor-not-allowed disabled:opacity-40">Reddet</button>
                </div>}
                {record.status === 'approved' && <button type="button" disabled={!canDecide} onClick={() => openOutcomeEditor(record)} className="mt-2 w-full rounded-md border border-violet-200 bg-white px-2 py-1.5 text-[9px] font-bold text-violet-700 disabled:cursor-not-allowed disabled:opacity-40">Gerçekleşen sonucu kaydet</button>}
                {record.status === 'completed' && <div className="mt-2 rounded-md border border-violet-100 bg-violet-50 p-2 text-[9px] leading-4 text-violet-950">
                  <div className="grid grid-cols-2 gap-1">
                    <span>Beklenen: <strong>₺{(record.expectedImpact || 0).toLocaleString('tr-TR')}</strong></span>
                    <span>Gerçekleşen: <strong>₺{(record.actualImpact || 0).toLocaleString('tr-TR')}</strong></span>
                    <span>Maliyet: <strong>₺{(record.implementationCost || 0).toLocaleString('tr-TR')}</strong></span>
                    <span>Net etki: <strong>₺{((record.actualImpact || 0) - (record.implementationCost || 0)).toLocaleString('tr-TR')}</strong></span>
                  </div>
                  {Boolean(record.implementationCost) && <p className="mt-1 font-bold text-violet-800">Gerçekleşen ROI: %{((((record.actualImpact || 0) - (record.implementationCost || 0)) / (record.implementationCost || 1)) * 100).toLocaleString('tr-TR', { maximumFractionDigits: 1 })}</p>}
                  <p className="mt-1 text-violet-800">{record.owner} · {record.dueDate} · {record.outcomeNote}</p>
                  <p className="mt-1 font-bold text-violet-700">{record.publicationConsent ? 'Anonim vaka kullanım izni kayıtlı' : 'Yayın izni yok — şirket içinde kalır'}</p>
                </div>}
                {outcomeEditor?.id === record.id && <div className="mt-2 space-y-2 rounded-lg border border-violet-200 bg-white p-2.5">
                  <div className="grid grid-cols-2 gap-2">
                    <input aria-label="Aksiyon sorumlusu" value={outcomeEditor.owner} onChange={(event) => setOutcomeEditor({ ...outcomeEditor, owner: event.target.value })} placeholder="Sorumlu kişi" className="rounded-md border border-slate-200 px-2 py-1.5 text-[10px]" />
                    <input aria-label="Hedef tarih" type="date" value={outcomeEditor.dueDate} onChange={(event) => setOutcomeEditor({ ...outcomeEditor, dueDate: event.target.value })} className="rounded-md border border-slate-200 px-2 py-1.5 text-[10px]" />
                    <input aria-label="Beklenen finansal etki" inputMode="decimal" value={outcomeEditor.expectedImpact} onChange={(event) => setOutcomeEditor({ ...outcomeEditor, expectedImpact: event.target.value })} placeholder="Beklenen etki ₺" className="rounded-md border border-slate-200 px-2 py-1.5 text-[10px]" />
                    <input aria-label="Uygulama maliyeti" inputMode="decimal" value={outcomeEditor.implementationCost} onChange={(event) => setOutcomeEditor({ ...outcomeEditor, implementationCost: event.target.value })} placeholder="Uygulama maliyeti ₺" className="rounded-md border border-slate-200 px-2 py-1.5 text-[10px]" />
                    <input aria-label="Gerçekleşen finansal etki" inputMode="decimal" value={outcomeEditor.actualImpact} onChange={(event) => setOutcomeEditor({ ...outcomeEditor, actualImpact: event.target.value })} placeholder="Gerçekleşen etki ₺" className="col-span-2 rounded-md border border-slate-200 px-2 py-1.5 text-[10px]" />
                  </div>
                  <textarea aria-label="Gerçekleşen sonuç açıklaması" value={outcomeEditor.outcomeNote} onChange={(event) => setOutcomeEditor({ ...outcomeEditor, outcomeNote: event.target.value })} placeholder="Sonucun nasıl ölçüldüğünü açıklayın" rows={2} className="w-full resize-none rounded-md border border-slate-200 px-2 py-1.5 text-[10px]" />
                  <label className="flex items-start gap-2 text-[9px] leading-4 text-slate-600"><input type="checkbox" checked={outcomeEditor.publicationConsent} onChange={(event) => setOutcomeEditor({ ...outcomeEditor, publicationConsent: event.target.checked })} className="mt-0.5" /> Sonucun şirket adı gösterilmeden anonim vaka çalışmasında kullanılmasına izin veriyorum.</label>
                  {outcomeError && <p className="text-[9px] font-bold text-red-700">{outcomeError}</p>}
                  <div className="grid grid-cols-2 gap-2"><button type="button" onClick={saveOutcome} className="rounded-md bg-violet-700 px-2 py-1.5 text-[9px] font-bold text-white">Sonucu doğrula</button><button type="button" onClick={() => { setOutcomeEditor(null); setOutcomeError(null); }} className="rounded-md border border-slate-200 px-2 py-1.5 text-[9px] font-bold text-slate-600">Vazgeç</button></div>
                </div>}
              </article>
            ))}
            {!approvals.length && <p className="rounded-lg bg-slate-50 p-2.5 text-[10px] leading-4 text-slate-500">AI CFO bir aksiyon önerdiğinde burada metrik ve formül dayanağıyla kayıt oluşur.</p>}
          </div>
          {!canDecide && <p className="mt-2 text-[9px] leading-4 text-slate-500">Onay veya ret kararı yalnızca Admin ve CFO rollerine açıktır.</p>}
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
              <Workflow className="h-4 w-4 text-violet-600" />
              Kontrollü ajanlar
            </div>
            <span className="rounded-full bg-violet-50 px-2 py-1 text-[10px] font-bold text-violet-700">
              {!hasVerifiedSession ? 'Giriş gerekli' : agentLoading ? 'Kontrol ediliyor' : `${agentAnalysis?.araclar.length || 0} araç aktif`}
            </span>
          </div>

          {agentAnalysis ? (
            <div className="mt-3 space-y-2">
              {agentAnalysis.uyarilar.slice(0, 3).map((warning) => (
                <div key={`${warning.arac}-${warning.baslik}`} className="rounded-lg border border-amber-200 bg-amber-50 p-2.5">
                  <p className="text-[11px] font-bold text-amber-900">{warning.baslik}</p>
                  <p className="mt-1 text-[10px] leading-4 text-amber-800">{warning.mesaj}</p>
                  <p className="mt-1 text-[9px] font-semibold uppercase tracking-wide text-amber-600">
                    {warning.arac} · insan onayı
                  </p>
                </div>
              ))}
              {agentAnalysis.uyarilar.length === 0 && (
                <p className="rounded-lg bg-emerald-50 p-2.5 text-[11px] text-emerald-800">
                  Girilen verilerde tanımlı kritik eşik uyarısı oluşmadı.
                </p>
              )}
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-2.5 text-[10px] leading-4 text-slate-600">
                <strong className="text-slate-800">Uzman onayı:</strong>{' '}
                {agentAnalysis.metodoloji_onaylari.filter((item) => item.uzman_onayi.includes('bekliyor')).length} metodoloji başlığı bekliyor.
              </div>
            </div>
          ) : !agentLoading ? (
            <p className="mt-3 text-[11px] leading-5 text-slate-500">
              Ajan analizi için doğrulanmış kullanıcı oturumu gerekiyor.
            </p>
          ) : (
            <div className="mt-3 flex items-center gap-2 text-[11px] text-slate-500">
              <RefreshCw className="h-3.5 w-3.5 animate-spin" /> Araçlar hazırlanıyor…
            </div>
          )}
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-900">
              <Sparkles className="h-4 w-4 text-orange-600" />
              Gelişmiş ajanlar
            </div>
            <span className={`rounded-full px-2 py-1 text-[10px] font-bold ${
              completedAdvancedAgents === totalAdvancedAgents
                ? 'bg-emerald-50 text-emerald-700'
                : 'bg-orange-50 text-orange-700'
            }`}>
              {!hasVerifiedSession ? 'Giriş gerekli' : advancedAnalysis ? `${completedAdvancedAgents}/${totalAdvancedAgents} tamamlandı` : 'Hazırlanıyor'}
            </span>
          </div>
          {advancedAnalysis?.bas_denetim && (
            <div className={`mt-3 rounded-lg border p-3 ${
              advancedAnalysis.bas_denetim.durum === 'onaylandi'
                ? 'border-emerald-200 bg-emerald-50'
                : advancedAnalysis.bas_denetim.durum === 'engellendi'
                  ? 'border-red-200 bg-red-50'
                  : 'border-amber-200 bg-amber-50'
            }`}>
              <div className="flex items-center justify-between gap-2">
                <p className="text-[10px] font-extrabold text-slate-900">Baş denetçi</p>
                <span className="rounded-full bg-white/80 px-2 py-1 text-[8px] font-extrabold uppercase text-slate-700">
                  {advancedAnalysis.bas_denetim.durum.replaceAll('_', ' ')}
                </span>
              </div>
              <p className="mt-1 text-[9px] leading-4 text-slate-700">
                {advancedAnalysis.bas_denetim.kritik_sorun_sayisi} kritik · {advancedAnalysis.bas_denetim.uyari_sayisi} uyarı · AI {advancedAnalysis.bas_denetim.ai_kullanilabilir ? `uygun (${advancedAnalysis.bas_denetim.ai_kapsami.replaceAll('_', ' ')})` : 'durduruldu'}
              </p>
              {(advancedAnalysis.bas_denetim.kritikler[0] || advancedAnalysis.bas_denetim.uyarilar[0]) && (
                <p className="mt-1 text-[9px] leading-4 text-slate-600">
                  {(advancedAnalysis.bas_denetim.kritikler[0] || advancedAnalysis.bas_denetim.uyarilar[0]).mesaj}
                </p>
              )}
            </div>
          )}
          {advancedAnalysis?.veri_ufku && hasAdvancedData && (
            <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-[10px] font-extrabold text-slate-900">Veri zaman kapsamı</p>
              <div className="mt-2 grid grid-cols-2 gap-1.5 text-[9px] text-slate-600">
                <span className="rounded-md bg-white p-2">Mizan <strong className="block text-slate-900">{advancedAnalysis.veri_ufku.mizan.donem_sayisi} dönem</strong></span>
                <span className="rounded-md bg-white p-2">Nakit <strong className="block text-slate-900">{advancedAnalysis.veri_ufku.nakit.kayit_sayisi} hafta</strong></span>
                <span className="rounded-md bg-white p-2">Alacak <strong className="block text-slate-900">{advancedAnalysis.veri_ufku.alacak.kayit_sayisi} tarih</strong></span>
                <span className="rounded-md bg-white p-2">Bütçe <strong className="block text-slate-900">{advancedAnalysis.veri_ufku.butce.kayit_sayisi} ay</strong></span>
              </div>
              <p className="mt-2 text-[9px] leading-4 text-slate-500">
                {advancedAnalysis.veri_ufku.nakit.tam_13_hafta_penceresi ? 'Kayan 13 haftalık nakit penceresi hazır.' : '13 haftalık nakit için ek haftalar gerekli.'}
              </p>
            </div>
          )}
          {!hasAdvancedData && advancedAnalysis && (
            <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3">
              <p className="text-[10px] font-bold text-amber-900">Gelişmiş finans verisi henüz yüklenmedi</p>
              <p className="mt-1 text-[9px] leading-4 text-amber-800">
                Tek Excel dosyasını Veri Girişi ekranından yükleyip “çalışma alanına aktar” adımını tamamlayın. Ajanlar otomatik çalışır; ayrıca JSON yüklemeniz gerekmez.
              </p>
              {onNavigateDataEntry && (
                <button type="button" onClick={onNavigateDataEntry} className="mt-2 rounded-md bg-amber-900 px-2.5 py-1.5 text-[9px] font-bold text-white hover:bg-amber-800">
                  Veri Girişi'ne git
                </button>
              )}
            </div>
          )}
          <div className="mt-3 space-y-2">
            {advancedAnalysis && Object.values(advancedAnalysis.ajanlar).map((agent) => (
              <div key={agent.ajan} className="flex items-start justify-between gap-3 rounded-lg border border-slate-200 bg-slate-50 p-2.5">
                <div className="min-w-0">
                  <p className="truncate text-[10px] font-bold text-slate-800">
                    {agent.ajan.replaceAll('_', ' ')}
                  </p>
                  <p className="mt-1 line-clamp-2 text-[9px] leading-4 text-slate-500">
                    {agent.bulgular?.[0] || agent.gerekenler?.slice(0, 2).join(' · ') || 'Kontrol hazır'}
                  </p>
                </div>
                <span className={`shrink-0 rounded-full px-2 py-1 text-[8px] font-extrabold uppercase ${
                  agent.durum === 'tamamlandi'
                    ? 'bg-emerald-100 text-emerald-700'
                    : agent.durum === 'veri_bekliyor'
                      ? 'bg-slate-200 text-slate-600'
                      : 'bg-amber-100 text-amber-700'
                }`}>
                  {agent.durum.replaceAll('_', ' ')}
                </span>
              </div>
            ))}
            {tabloAjani?.son_donem && (
              <div className="rounded-lg border border-blue-200 bg-blue-50/60 p-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5 text-[10px] font-extrabold text-blue-950">
                    <Scale className="h-3.5 w-3.5" /> Finansal tablo mutabakatı
                  </div>
                  <span className="text-[8px] font-bold text-blue-700">{tabloAjani.tablo_surumu}</span>
                </div>
                <div className="mt-2 grid grid-cols-2 gap-1.5 text-[9px]">
                  <div className="rounded-md bg-white p-2 text-slate-600">
                    Net kâr <strong className="block text-slate-900">₺{tabloAjani.son_donem.gelir_tablosu.net_kar.toLocaleString('tr-TR')}</strong>
                  </div>
                  <div className="rounded-md bg-white p-2 text-slate-600">
                    Toplam varlık <strong className="block text-slate-900">₺{tabloAjani.son_donem.bilanco.toplam_varliklar.toLocaleString('tr-TR')}</strong>
                  </div>
                  <div className="rounded-md bg-white p-2 text-slate-600">
                    Bilanço farkı <strong className={tabloAjani.son_donem.bilanco.denk ? 'block text-emerald-700' : 'block text-amber-700'}>₺{tabloAjani.son_donem.bilanco.bilanco_farki.toLocaleString('tr-TR')}</strong>
                  </div>
                  <div className="rounded-md bg-white p-2 text-slate-600">
                    Nakit köprüsü <strong className="block text-slate-900">{tabloAjani.nakit_koprusu?.durum.replaceAll('_', ' ')}</strong>
                  </div>
                </div>
                {tabloAjani.finansal_gorunum_mutabakati?.uyusmayan_alanlar.length ? (
                  <p className="mt-2 text-[9px] leading-4 text-amber-800">
                    Kontrol bekleyen: {tabloAjani.finansal_gorunum_mutabakati.uyusmayan_alanlar.join(', ')}
                  </p>
                ) : (
                  <p className="mt-2 text-[9px] font-semibold text-emerald-700">Mizan ve finansal özet mutabık.</p>
                )}
              </div>
            )}
            {!advancedAnalysis && hasVerifiedSession && (
              <div className="flex items-center gap-2 py-2 text-[10px] text-slate-500">
                <RefreshCw className="h-3.5 w-3.5 animate-spin" /> Gelişmiş kontroller hazırlanıyor…
              </div>
            )}
            {advancedError && (
              <p className="rounded-lg border border-red-200 bg-red-50 p-2 text-[9px] leading-4 text-red-700">{advancedError}</p>
            )}
            {advancedDataApplied && (
              <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-2 text-[9px] leading-4 text-emerald-700">
                Ek ajan verisi doğrulandı ve çalışma alanına uygulandı.
              </p>
            )}
            {hasVerifiedSession && <details className="rounded-lg border border-slate-200 bg-white p-2.5">
              <summary className="cursor-pointer text-[9px] font-bold text-slate-600">İleri seviye: JSON ile ek ajan verisi</summary>
              <p className="mt-2 text-[9px] leading-4 text-slate-500">Normal kullanımda gerekli değildir. Ana veri kaynağı Veri Girişi ekranındaki Excel yüklemesidir.</p>
              <div className="mt-2 grid grid-cols-2 gap-2">
              <label className="flex cursor-pointer items-center justify-center gap-1.5 rounded-lg bg-slate-900 px-2 py-2 text-[9px] font-bold text-white transition hover:bg-slate-800">
                <FileUp className="h-3 w-3" /> JSON ek veri yükle
                <input type="file" accept="application/json,.json" className="hidden" onChange={handleAdvancedData} />
              </label>
              <a href="/ornek-gelismis-ajan-verisi.json" download className="flex items-center justify-center rounded-lg border border-slate-200 bg-white px-2 py-2 text-center text-[9px] font-bold text-slate-600 hover:bg-slate-50">
                Örnek şablon
              </a>
              </div>
            </details>}
          </div>
        </div>

        {/* Quick Question Prompts */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center gap-2 text-slate-900 font-bold text-sm border-b border-slate-100 pb-2">
            <Sparkles className="w-4 h-4 text-amber-500" />
            <span>Hızlı CFO Soruları</span>
          </div>

          <div className="space-y-2">
            {quickPrompts.map((prompt, index) => (
              <button
                key={index}
                onClick={() => handleSend(prompt)}
                disabled={loading || !hasVerifiedSession}
                className="w-full text-left text-sm p-3 rounded-lg bg-slate-50 hover:bg-orange-50 hover:text-orange-800 text-slate-700 border border-slate-200 transition-colors flex items-center justify-between cursor-pointer disabled:opacity-50"
              >
                <span>{prompt}</span>
                <Lightbulb className="w-3.5 h-3.5 text-amber-500 shrink-0 ml-1" />
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Chat Interface */}
      <div className="lg:col-span-3 bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col h-[650px]">
        {/* Chat Header */}
        <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-900 text-white rounded-t-xl">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#FF4D00] flex items-center justify-center text-white font-bold">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm">CFO Yapay Zeka Danışmanı</h3>
              <p className="text-[11px] text-slate-300">KazKaz Finans Motoru + Yapay Zeka</p>
            </div>
          </div>
          <span className="bg-emerald-500/20 text-emerald-300 text-[10px] font-bold px-2.5 py-1 rounded-full border border-emerald-500/30">
            {lastDecision ? `${lastDecision.kaynak} · güven ${lastDecision.guven}` : 'Finans motoru aktif'}
          </span>
        </div>

        <div className="grid grid-cols-1 gap-2 border-b border-slate-200 bg-white px-4 py-3 text-[11px] text-slate-600 sm:grid-cols-2 xl:grid-cols-4">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
            <span>Hesaplama: kurallı finans motoru</span>
          </div>
          <div className="flex items-center gap-1.5">
            <ShieldAlert className={`h-3.5 w-3.5 ${lastDecision?.ai_dogrulama?.durum === 'dogrulandi' ? 'text-emerald-600' : 'text-amber-600'}`} />
            <span>
              {!lastDecision?.ai_dogrulama
                ? 'AI sayı doğrulaması istekle çalışır'
                : lastDecision.ai_dogrulama.durum === 'dogrulandi'
                  ? `${lastDecision.ai_dogrulama.kontrol_edilen_sayi} AI sayısı doğrulandı`
                  : lastDecision.ai_dogrulama.durum === 'ajan_engeli'
                    ? 'Baş denetçi AI yanıtını durdurdu'
                    : lastDecision.ai_dogrulama.durum === 'veri_engeli'
                      ? 'Eksik veri AI yanıtını durdurdu'
                      : 'Doğrulanmayan AI metni gösterilmedi'}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-orange-600" />
            <span>
              AI: {lastDecision ? `${lastDecision.kaynak}${lastDecision.yedek_kullanildi ? ' (yedek)' : ''}` : 'istek sırasında seçilir'}
            </span>
          </div>
          <div className="flex items-center gap-1.5">
            <ShieldAlert className="h-3.5 w-3.5 text-amber-600" />
            <span>
              {lastDecision
                ? `Veri kalitesi ${lastDecision.veri_kalitesi.skor}/100 · insan onayı gerekli`
                : 'Aksiyonlar insan onayı gerektirir'}
            </span>
          </div>
        </div>

        {/* Chat Message Scroll */}
        <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-slate-50">
          {messages.map((msg) => {
            const isAi = msg.sender === 'ai';
            return (
              <div key={msg.id} className={`flex gap-3 ${isAi ? 'justify-start' : 'justify-end'}`}>
                {isAi && (
                  <div className="w-8 h-8 rounded-lg bg-slate-900 text-white flex items-center justify-center shrink-0 mt-1">
                    <Bot className="w-4 h-4" />
                  </div>
                )}
                <div className={`max-w-[80%] rounded-xl p-4 text-xs leading-relaxed shadow-xs ${
                  isAi
                    ? 'bg-white text-slate-800 border border-slate-200 whitespace-pre-wrap'
                    : 'bg-[#FF4D00] text-white'
                }`}>
                  <p>
                    {msg.text.split('\n').map((line, lineIndex) => (
                      <React.Fragment key={`${msg.id}-${lineIndex}`}>
                        {line.split(/(\*\*.*?\*\*)/g).map((part, partIndex) =>
                          part.startsWith('**') && part.endsWith('**') ? (
                            <strong key={partIndex}>{part.slice(2, -2)}</strong>
                          ) : (
                            <React.Fragment key={partIndex}>{part}</React.Fragment>
                          ),
                        )}
                        {lineIndex < msg.text.split('\n').length - 1 && <br />}
                      </React.Fragment>
                    ))}
                  </p>
                  <span className={`text-[10px] block mt-2 text-right ${isAi ? 'text-slate-400' : 'text-orange-100'}`}>
                    {msg.timestamp}
                  </span>
                </div>
                {!isAi && (
                  <div className="w-8 h-8 rounded-lg bg-[#FF4D00] text-white flex items-center justify-center shrink-0 mt-1">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })}

          {loading && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 rounded-lg bg-slate-900 text-white flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-white border border-slate-200 rounded-xl p-3 text-xs text-slate-500 flex items-center gap-2 shadow-xs">
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-orange-600" />
                <span>CFO Analiz Ediyor ve Yanıt Üretiyor...</span>
              </div>
            </div>
          )}
        </div>

        {/* Chat Input Bar */}
        <div className="p-3 border-t border-slate-200 bg-white rounded-b-xl">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex gap-2"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={!hasVerifiedSession}
              placeholder={hasVerifiedSession ? "Finansal soru sorun (ör. 'Borçlarımızı yapılandırmak için ne yapmalıyız?')..." : 'AI CFO sohbeti için giriş yapın'}
              className="flex-1 bg-slate-50 border border-slate-300 rounded-lg px-3.5 py-3 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-orange-400 focus:bg-white transition-all"
            />
            <button
              type="submit"
              disabled={loading || !input.trim() || !hasVerifiedSession}
              className="bg-slate-900 hover:bg-slate-800 text-white px-4 py-2.5 rounded-lg text-xs font-semibold flex items-center gap-2 transition-all disabled:opacity-50 cursor-pointer"
            >
              <span>Gönder</span>
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      </div>
      </div>
    </div>
  );
};

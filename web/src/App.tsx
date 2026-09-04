import React, { lazy, Suspense, useEffect, useState } from 'react';
import { Navigation } from './components/Navigation';
import { LandingPage } from './components/LandingPage';
import { AuthProvider } from './context/AuthContext';
import { AlertProvider } from './context/AlertContext';
import {
  initialFinancialData,
  initialCashFlow,
  initialDebts,
  initialCustomers,
  initialBudget
} from './data/mockData';
import { ApprovalDecision, BudgetItem, CashFlowItem, CustomerRisk, DebtItem, FinancialData, TransactionAnalytics } from './types';
import { FinansalDenetim, GelismisAjanGirdisi, SaglikSkoru, zamanSerisiAnalizi } from './lib/api';
import { workspaceDataFromAdvanced } from './lib/workspaceData';
import { deleteWorkspace, exportWorkspace, loadWorkspace, saveWorkspace, WorkspaceSnapshot } from './lib/workspacePersistence';
import { useAuth } from './context/AuthContext';
import { CompanySetup } from './components/CompanySetup';
import { ErrorBoundary } from './components/ErrorBoundary';
import { FeedbackWidget } from './components/FeedbackWidget';
import { ScreenTabs } from './components/ScreenTabs';

const OverviewTab = lazy(() => import('./components/OverviewTab').then((module) => ({ default: module.OverviewTab })));
const CfoAgentTab = lazy(() => import('./components/CfoAgentTab').then((module) => ({ default: module.CfoAgentTab })));
const CashflowDebtTab = lazy(() => import('./components/CashflowDebtTab').then((module) => ({ default: module.CashflowDebtTab })));
const BudgetTab = lazy(() => import('./components/BudgetTab').then((module) => ({ default: module.BudgetTab })));
const CustomerTab = lazy(() => import('./components/CustomerTab').then((module) => ({ default: module.CustomerTab })));
const ScenarioTab = lazy(() => import('./components/ScenarioTab').then((module) => ({ default: module.ScenarioTab })));
const BenchmarkingTab = lazy(() => import('./components/BenchmarkingTab').then((module) => ({ default: module.BenchmarkingTab })));
const DataEntryTab = lazy(() => import('./components/DataEntryTab').then((module) => ({ default: module.DataEntryTab })));
const FinancialStatementsTab = lazy(() => import('./components/FinancialStatementsTab').then((module) => ({ default: module.FinancialStatementsTab })));
const ReportsTab = lazy(() => import('./components/ReportsTab').then((module) => ({ default: module.ReportsTab })));
const WorkspaceSettingsTab = lazy(() => import('./components/WorkspaceSettingsTab').then((module) => ({ default: module.WorkspaceSettingsTab })));
const ComplianceReadinessTab = lazy(() => import('./components/ComplianceReadinessTab').then((module) => ({ default: module.ComplianceReadinessTab })));
const PlatformAdminTab = lazy(() => import('./components/PlatformAdminTab').then((module) => ({ default: module.PlatformAdminTab })));
const AlertSystemOverlay = lazy(() => import('./components/AlertSystemOverlay').then((module) => ({ default: module.AlertSystemOverlay })));

const trackedWorkspaceTabIds = new Set([
  'overview', 'income-statement', 'balance-sheet', 'cash-statement', 'budget', 'cashflow',
  'customer', 'scenario', 'benchmarking', 'compliance', 'cfo-agent', 'reports', 'data-entry', 'settings', 'platform-admin',
]);
const defaultRecentTabIds = ['overview', 'cashflow', 'cfo-agent'];

const WorkspaceFallback = () => (
  <div className="flex min-h-[420px] items-center justify-center">
    <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white px-5 py-4 text-sm text-slate-500 shadow-sm">
      <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-violet-600" />
      Finans çalışma alanı hazırlanıyor…
    </div>
  </div>
);

function WorkspaceApp() {
  const { currentUser, userProfile, isGuest } = useAuth();
  const [activeTab, setActiveTab] = useState<string>('landing');
  const [financialData, setFinancialData] = useState<FinancialData>(initialFinancialData);
  const [cashFlow, setCashFlow] = useState<CashFlowItem[]>(initialCashFlow);
  const [debts, setDebts] = useState<DebtItem[]>(initialDebts);
  const [customers, setCustomers] = useState<CustomerRisk[]>(initialCustomers);
  const [budget, setBudget] = useState<BudgetItem[]>(initialBudget);
  const [advancedData, setAdvancedData] = useState<GelismisAjanGirdisi | undefined>();
  const [isSampleData, setIsSampleData] = useState(true);
  const [transactionAnalytics, setTransactionAnalytics] = useState<TransactionAnalytics | undefined>();
  const [financialAudit, setFinancialAudit] = useState<FinansalDenetim | null>(null);
  const [approvalDecisions, setApprovalDecisions] = useState<ApprovalDecision[]>([]);
  const [persistenceStatus, setPersistenceStatus] = useState<'idle' | 'loading' | 'saved' | 'error'>('idle');
  const [persistenceMessage, setPersistenceMessage] = useState<string | null>(null);
  const [recentTabIds, setRecentTabIds] = useState<string[]>(defaultRecentTabIds);
  // Sağlık skoru zaman serisi ister; tek dönemlik görünümden hesaplanamaz.
  // Bu yüzden yalnızca Excel içe aktarımından sonra doldurulur.
  const [healthScore, setHealthScore] = useState<SaglikSkoru | null>(null);

  useEffect(() => {
    try {
      const storedRecentTabs = window.localStorage.getItem('kazkaz-recent-navigation');
      if (!storedRecentTabs) return;
      const parsedRecentTabs = JSON.parse(storedRecentTabs);
      if (!Array.isArray(parsedRecentTabs)) return;
      const validTabs = parsedRecentTabs.filter((tabId): tabId is string => typeof tabId === 'string' && trackedWorkspaceTabIds.has(tabId));
      if (validTabs.length > 0) setRecentTabIds(validTabs.slice(0, 3));
    } catch {
      // Yerel geçmiş kullanılamıyorsa güvenli varsayılanlar korunur.
    }
  }, []);

  const navigateToTab = (tabId: string) => {
    if (trackedWorkspaceTabIds.has(tabId)) {
      setRecentTabIds((currentTabs) => {
        const nextTabs = [tabId, ...currentTabs.filter((currentTabId) => currentTabId !== tabId)].slice(0, 3);
        try {
          window.localStorage.setItem('kazkaz-recent-navigation', JSON.stringify(nextTabs));
        } catch {
          // Gezinme, depolama kısıtlarından etkilenmemelidir.
        }
        return nextTabs;
      });
    }
    setActiveTab(tabId);
  };

  useEffect(() => {
    const companyId = userProfile?.companyId;
    if (!currentUser || !companyId || isGuest) return;
    let active = true;
    setPersistenceStatus('loading');
    setPersistenceMessage('Kayıtlı şirket çalışma alanı yükleniyor…');
    loadWorkspace(companyId)
      .then((snapshot) => {
        if (!active) return;
        if (snapshot) {
          setFinancialData(snapshot.financialData);
          setCashFlow(snapshot.cashFlow);
          setDebts(snapshot.debts);
          setCustomers(snapshot.customers);
          setBudget(snapshot.budget);
          setAdvancedData(snapshot.advancedData);
          setTransactionAnalytics(snapshot.transactionAnalytics);
          setFinancialAudit(snapshot.financialAudit);
          setIsSampleData(snapshot.isSampleData);
          setApprovalDecisions(snapshot.approvalDecisions || []);
          setPersistenceMessage('Şirket çalışma alanı güvenli kayıttan yüklendi.');
        } else {
          setPersistenceMessage('Bu şirket için henüz kayıtlı finans çalışma alanı yok.');
        }
        setPersistenceStatus('idle');
      })
      .catch((error) => {
        if (!active) return;
        setPersistenceStatus('error');
        setPersistenceMessage(error instanceof Error ? error.message : 'Çalışma alanı yüklenemedi.');
      });
    return () => { active = false; };
  }, [currentUser, isGuest, userProfile?.companyId]);

  const persistWorkspace = async (snapshot: WorkspaceSnapshot) => {
    if (!currentUser || !userProfile?.companyId || isGuest) return;
    setPersistenceStatus('loading');
    setPersistenceMessage('Şirket çalışma alanı kaydediliyor…');
    try {
      await saveWorkspace(userProfile.companyId, currentUser.uid, snapshot);
      setPersistenceStatus('saved');
      setPersistenceMessage('Değişiklikler şirket çalışma alanına kaydedildi.');
    } catch (error) {
      setPersistenceStatus('error');
      setPersistenceMessage(error instanceof Error ? error.message : 'Çalışma alanı kaydedilemedi.');
    }
  };

  /**
   * Sağlık skoru zaman serisinden hesaplanır (financial_engine.HealthScore).
   * Satırlarda müşteri adı varsa skor 5 boyuta çıkar; yoksa 4 boyutta kalır.
   * Skor gösterilemezse ekran skorsuz çalışmaya devam eder — uydurulmaz.
   */
  const hesaplaSaglikSkoru = async (
    zamanSerisi: Array<Record<string, string | number>> | undefined,
    finansal: FinancialData,
  ) => {
    const satirlar = (zamanSerisi || [])
      .filter((satir) => satir.tarih && satir.kategori)
      .map((satir) => ({
        tarih: String(satir.tarih),
        kategori: String(satir.kategori),
        gelir: Number(satir.gelir) || 0,
        gider: Number(satir.gider) || 0,
        musteri: satir.musteri ? String(satir.musteri) : undefined,
      }));

    if (satirlar.length === 0) {
      setHealthScore(null);
      return;
    }

    try {
      const sonuc = await zamanSerisiAnalizi(satirlar, {
        baslangic_nakiti: finansal.cashInHand,
        kisa_vadeli_borc: finansal.shortTermDebt,
        stoklar: finansal.inventory,
      });
      setHealthScore(sonuc.finansal.saglik_skoru ?? null);
    } catch {
      // Skor hesaplanamazsa ekran skorsuz devam eder; yaklaşık değer üretilmez.
      setHealthScore(null);
    }
  };

  const applyAdvancedData = (input: GelismisAjanGirdisi) => {
    const collections = workspaceDataFromAdvanced(input);
    setAdvancedData(input);
    if (collections.cashFlow) setCashFlow(collections.cashFlow);
    if (collections.debts) setDebts(collections.debts);
    if (collections.customers) setCustomers(collections.customers);
    if (collections.budget) setBudget(collections.budget);
    setIsSampleData(false);
    return collections;
  };

  const selectDemo = async (demoId: string) => {
    setAdvancedData(undefined);
    setTransactionAnalytics(undefined);
    setFinancialAudit(null);
    setApprovalDecisions([]);
    setIsSampleData(true);

    if (demoId === 'cash-pressure') {
      setFinancialData({
        ...initialFinancialData,
        companyName: 'Marmara Dağıtım Ltd. Şti.',
        sector: 'Perakende & Dağıtım',
        period: '2026 / Q2',
        revenue: 22400000,
        costOfGoods: 15800000,
        grossProfit: 6600000,
        operatingExpenses: 4200000,
        ebitda: 2400000,
        depreciation: 350000,
        interestExpense: 620000,
        taxExpense: 230000,
        netProfit: 1200000,
        cashInHand: 920000,
        shortTermDebt: 6400000,
        longTermDebt: 2800000,
        receivables: 7900000,
        payables: 5100000,
        inventory: 4300000,
        equity: 7600000,
      });
      setCashFlow([
        { month: 'Ocak', inflow: 3900000, outflow: 3450000, netCash: 450000, cumulativeCash: 2350000 },
        { month: 'Şubat', inflow: 3650000, outflow: 3780000, netCash: -130000, cumulativeCash: 2220000 },
        { month: 'Mart', inflow: 3300000, outflow: 4120000, netCash: -820000, cumulativeCash: 1400000 },
        { month: 'Nisan', inflow: 3500000, outflow: 3980000, netCash: -480000, cumulativeCash: 920000 },
      ]);
      setDebts(initialDebts.map((debt, index) => index < 2 ? { ...debt, status: 'critical' as const } : debt));
      setCustomers(initialCustomers.map((customer, index) => index < 3 ? { ...customer, avgPaymentDays: customer.avgPaymentDays + 22, riskLevel: index === 2 ? 'kritik' as const : 'yüksek' as const } : customer));
      setBudget(initialBudget);
      navigateToTab('cashflow');
      return;
    }

    if (demoId === 'profit-pressure') {
      setFinancialData({
        ...initialFinancialData,
        companyName: 'Anka Üretim Sanayi A.Ş.',
        sector: 'İmalat & Otomotiv',
        period: '2026 / Q2',
        revenue: 31800000,
        costOfGoods: 24500000,
        grossProfit: 7300000,
        operatingExpenses: 5100000,
        ebitda: 2200000,
        depreciation: 780000,
        interestExpense: 690000,
        taxExpense: 190000,
        netProfit: 540000,
        cashInHand: 3100000,
        shortTermDebt: 5800000,
        longTermDebt: 9200000,
        receivables: 6100000,
        payables: 4700000,
        inventory: 8600000,
        equity: 14200000,
      });
      setCashFlow(initialCashFlow);
      setDebts(initialDebts);
      setCustomers(initialCustomers);
      setBudget(initialBudget.map((item, index) => index === 0 || index === 2 ? {
        ...item,
        actual: Math.round(item.planned * 1.18),
        variance: -Math.round(item.planned * 0.18),
        variancePercent: -18,
      } : item));
      navigateToTab('income-statement');
      return;
    }

    setFinancialData(initialFinancialData);
    setCashFlow(initialCashFlow);
    setDebts(initialDebts);
    setCustomers(initialCustomers);
    setBudget(initialBudget);

    if (demoId === 'full-company') {
      try {
        const response = await fetch('/ornek-gelismis-ajan-verisi.json');
        if (!response.ok) throw new Error('Örnek ajan verisi alınamadı.');
        applyAdvancedData(await response.json() as GelismisAjanGirdisi);
        setIsSampleData(true);
      } catch {
        setPersistenceStatus('error');
        setPersistenceMessage('Gelişmiş örnek verinin bir bölümü yüklenemedi; temel örnekle devam ediliyor.');
      }
      navigateToTab('cfo-agent');
      return;
    }

    navigateToTab('overview');
  };

  return (
    <div className={`min-h-screen flex flex-col antialiased selection:bg-violet-200 selection:text-[#0f2252] relative ${
      activeTab === 'landing'
        ? 'bg-[#050816] text-[#F8F7F4]'
        : 'workspace-shell bg-[#f3f5f9] text-[#0f1729]'
    }`}>
          <Navigation
            activeTab={activeTab}
            setActiveTab={navigateToTab}
            companyName={financialData.companyName}
            period={financialData.period}
            recentTabIds={recentTabIds}
          />

          {activeTab === 'landing' ? (
            <LandingPage
              onNavigateTab={navigateToTab}
              onOpenAuth={() => navigateToTab('data-entry')}
              onSelectDemo={selectDemo}
            />
          ) : currentUser && userProfile && !isGuest && (
            !userProfile.companyId
            || (!userProfile.onboardingProfile && ['admin', 'cfo'].includes(userProfile.role))
          ) ? (
            <CompanySetup />
          ) : (
            <main className="workspace-content w-full flex-1 px-4 py-5 sm:px-6 lg:px-7 lg:py-6 xl:pl-[270px]">
              <div className="mx-auto w-full max-w-[1240px]">
              {persistenceMessage && (
                <div role="status" aria-live="polite" className={`panel-status-enter mb-5 rounded-xl border px-4 py-3 text-xs shadow-sm ${
                  persistenceStatus === 'error'
                    ? 'border-red-200 bg-red-50 text-red-700'
                    : persistenceStatus === 'saved'
                      ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                      : 'border-sky-200 bg-sky-50 text-sky-700'
                }`}>
                  {persistenceMessage}
                </div>
              )}
              {isSampleData && !['data-entry', 'platform-admin'].includes(activeTab) && (
                <div className="mb-5 flex flex-col gap-3 rounded-xl border border-violet-200 bg-gradient-to-r from-violet-50 to-indigo-50 px-4 py-3 text-sm text-[#0f2252] shadow-sm sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <span className="font-bold">Örnek şirket verisi görüntüleniyor.</span>{' '}
                    <span className="text-slate-500">Bu rakamlar gerçek bir şirkete ait değildir.</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => navigateToTab('data-entry')}
                    className="shrink-0 text-left font-bold text-violet-700 underline decoration-violet-300 underline-offset-4 sm:text-right"
                  >
                    Kendi verimi gir
                  </button>
                </div>
              )}
              <ScreenTabs activeTab={activeTab} onNavigateTab={navigateToTab} />
              <div key={activeTab} className="panel-tab-transition">
              <Suspense fallback={<WorkspaceFallback />}>
                {activeTab === 'overview' && (
                  <OverviewTab
                    data={financialData}
                    cashFlow={cashFlow}
                    customers={customers}
                    audit={financialAudit}
                    healthScore={healthScore}
                    isSampleData={isSampleData}
                    onNavigateTab={navigateToTab}
                  />
                )}
                {['income-statement', 'balance-sheet', 'cash-statement'].includes(activeTab) && (
                  <FinancialStatementsTab
                    data={financialData}
                    cashFlow={cashFlow}
                    section={activeTab === 'income-statement' ? 'income' : activeTab === 'balance-sheet' ? 'balance' : 'cash'}
                    onNavigateTab={navigateToTab}
                  />
                )}
                {activeTab === 'cfo-agent' && (
                  <CfoAgentTab
                    financialData={financialData}
                    cashFlow={cashFlow}
                    debts={debts}
                    advancedData={advancedData}
                    onAdvancedDataLoaded={applyAdvancedData}
                    onNavigateDataEntry={() => navigateToTab('data-entry')}
                    approvals={approvalDecisions}
                    onApprovalsChange={async (nextApprovals) => {
                      setApprovalDecisions(nextApprovals);
                      await persistWorkspace({
                        financialData, cashFlow, debts, customers, budget,
                        advancedData, transactionAnalytics, financialAudit, isSampleData,
                        approvalDecisions: nextApprovals,
                      });
                    }}
                  />
                )}
                {activeTab === 'benchmarking' && (
                  <BenchmarkingTab financialData={financialData} />
                )}
                {activeTab === 'cashflow' && (
                  <CashflowDebtTab
                    cashFlow={cashFlow}
                    debts={debts}
                    onNavigateDataEntry={() => navigateToTab('data-entry')}
                  />
                )}
                {activeTab === 'budget' && (
                  <BudgetTab budgetItems={budget} onNavigateDataEntry={() => navigateToTab('data-entry')} />
                )}
                {activeTab === 'customer' && (
                  <CustomerTab
                    customers={customers}
                    analytics={transactionAnalytics}
                    onNavigateDataEntry={() => navigateToTab('data-entry')}
                  />
                )}
                {activeTab === 'scenario' && (
                  <ScenarioTab baseData={financialData} analytics={transactionAnalytics} />
                )}
                {activeTab === 'compliance' && <ComplianceReadinessTab />}
                {activeTab === 'reports' && (
                  <ReportsTab data={financialData} onNavigateDataEntry={() => navigateToTab('data-entry')} />
                )}
                {activeTab === 'data-entry' && (
                  <DataEntryTab
                    initialData={financialData}
                    onImport={async (imported, advanced, analytics, audit, zamanSerisi) => {
                      const collections = applyAdvancedData(advanced);
                      setFinancialData(imported);
                      setFinancialAudit(audit);
                      setTransactionAnalytics(analytics);
                      await hesaplaSaglikSkoru(zamanSerisi, imported);
                      await persistWorkspace({
                        financialData: imported,
                        cashFlow: collections.cashFlow || [],
                        debts: collections.debts || [],
                        customers: collections.customers || [],
                        budget: collections.budget || [],
                        advancedData: advanced,
                        transactionAnalytics: analytics,
                        financialAudit: audit,
                        isSampleData: false,
                        approvalDecisions,
                      });
                      navigateToTab('overview');
                    }}
                    onSave={async (updated, audit) => {
                      const nextCashFlow = isSampleData ? [] : cashFlow;
                      const nextDebts = isSampleData ? [] : debts;
                      const nextCustomers = isSampleData ? [] : customers;
                      const nextBudget = isSampleData ? [] : budget;
                      setFinancialData(updated);
                      setFinancialAudit(audit || null);
                      if (isSampleData) {
                        setCashFlow(nextCashFlow);
                        setDebts(nextDebts);
                        setCustomers(nextCustomers);
                        setBudget(nextBudget);
                      }
                      setIsSampleData(false);
                      await persistWorkspace({
                        financialData: updated,
                        cashFlow: nextCashFlow,
                        debts: nextDebts,
                        customers: nextCustomers,
                        budget: nextBudget,
                        advancedData: isSampleData ? undefined : advancedData,
                        transactionAnalytics: isSampleData ? undefined : transactionAnalytics,
                        financialAudit: audit || null,
                        isSampleData: false,
                        approvalDecisions,
                      });
                      navigateToTab('overview');
                    }}
                  />
                )}
                {activeTab === 'settings' && (
                  <WorkspaceSettingsTab
                    companyName={financialData.companyName}
                    onNavigateDataEntry={() => navigateToTab('data-entry')}
                    onExportWorkspace={async () => {
                      await exportWorkspace();
                      setPersistenceStatus('saved');
                      setPersistenceMessage('Şirket çalışma alanı JSON olarak dışa aktarıldı.');
                    }}
                    onDeleteWorkspace={async () => {
                      if (!userProfile?.companyId) throw new Error('Şirket çalışma alanı bulunamadı.');
                      await deleteWorkspace(userProfile.companyId);
                      setFinancialData(initialFinancialData);
                      setCashFlow([]);
                      setDebts([]);
                      setCustomers([]);
                      setBudget([]);
                      setAdvancedData(undefined);
                      setTransactionAnalytics(undefined);
                      setFinancialAudit(null);
                      setApprovalDecisions([]);
                      setIsSampleData(true);
                      setPersistenceStatus('saved');
                      setPersistenceMessage('Buluttaki aktif çalışma alanı silindi; ekran örnek başlangıç durumuna döndü.');
                    }}
                  />
                )}
                {activeTab === 'platform-admin' && <PlatformAdminTab />}
              </Suspense>
              </div>
              </div>
            </main>
          )}

          {activeTab !== 'landing' && (
            <Suspense fallback={null}>
              <AlertSystemOverlay onNavigateTab={navigateToTab} />
            </Suspense>
          )}

          {activeTab !== 'landing' && currentUser && userProfile?.companyId && !isGuest && <FeedbackWidget activePage={activeTab} />}

          {activeTab !== 'landing' && (
            <footer className="border-t border-slate-200 bg-white py-5 xl:pl-[246px]">
              <div className="mx-auto flex max-w-[1480px] flex-col items-center justify-between gap-3 px-4 text-xs tracking-wide text-slate-500 sm:flex-row sm:px-6 lg:px-7">
                <div>
                  KazKaz <span className="font-bold text-violet-700">AI</span> — Dijital CFO çalışma alanı © 2026
                </div>
                <div className="text-center text-[11px] text-slate-600 sm:text-right">
                  Karar desteği sağlar; muhasebe kaydı veya bağımsız denetim görüşü değildir.
                </div>
              </div>
            </footer>
          )}
    </div>
  );
}

export function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AlertProvider>
          <WorkspaceApp />
        </AlertProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;

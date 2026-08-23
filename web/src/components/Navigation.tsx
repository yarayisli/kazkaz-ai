import React, { useEffect, useState } from 'react';
import {
  ArrowRight,
  BarChart2,
  Bot,
  Building2,
  ChevronDown,
  Clock3,
  Edit3,
  FileBarChart,
  FileText,
  Landmark,
  LayoutDashboard,
  Leaf,
  LogIn,
  LogOut,
  Menu,
  PieChart,
  Scale,
  Search,
  ServerCog,
  Settings2,
  Sliders,
  Sparkles,
  TrendingUp,
  Users,
  Wallet,
  UploadCloud,
  X,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { AuthModal } from './AuthModal';

interface NavigationProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  companyName: string;
  period: string;
  recentTabIds: string[];
}

type TabItem = {
  id: string;
  label: string;
  description?: string;
  icon: React.ComponentType<{ className?: string }>;
  restrictedForViewer?: boolean;
};

type NavigationItem = TabItem | {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  children: TabItem[];
};

const financeTabs: TabItem[] = [
  { id: 'income-statement', label: 'Gelir Tablosu', description: 'Ciro, maliyet ve kârlılık köprüsü', icon: TrendingUp },
  { id: 'balance-sheet', label: 'Bilanço', description: 'Varlık, yükümlülük ve özkaynak', icon: Scale },
  { id: 'cash-statement', label: 'Nakit Akışı', description: 'Faaliyet, yatırım ve finansman köprüsü', icon: Landmark },
  { id: 'budget', label: 'Bütçe', description: 'Plan, gerçekleşen ve sapma', icon: PieChart },
];

const analysisTabs: TabItem[] = [
  { id: 'customer', label: 'Müşteriler', description: 'Alacak, yoğunlaşma ve ürün görünümü', icon: Users },
  { id: 'scenario', label: 'Senaryolar', description: 'Stres testi, tahmin ve yatırım ön değerlendirmesi', icon: Sliders },
  { id: 'benchmarking', label: 'Benchmark', description: 'Sektör referans karşılaştırması', icon: BarChart2 },
  { id: 'compliance', label: 'ESG & TFRS Hazırlık', description: 'Kanıt, belge ve uzman onayı hazırlık kontrolü', icon: Leaf },
];

const workspaceNavigation: NavigationItem[] = [
  { id: 'overview', label: 'Genel Bakış', icon: LayoutDashboard },
  { id: 'finance-group', label: 'Finans', icon: FileBarChart, children: financeTabs },
  { id: 'cashflow', label: 'Nakit & Borç', icon: Wallet },
  { id: 'analysis-group', label: 'Analizler', icon: Sliders, children: analysisTabs },
  { id: 'cfo-agent', label: 'AI CFO', icon: Bot },
  { id: 'reports', label: 'Raporlar', icon: FileText },
];

type WorkspaceMenuGroup = {
  id: string;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  tabs: TabItem[];
};

const workspaceMenuGroups: WorkspaceMenuGroup[] = [
  {
    id: 'overview-group',
    label: 'Genel Bakış',
    description: 'Finansal durum ve öncelikler',
    icon: LayoutDashboard,
    tabs: [{ id: 'overview', label: 'Genel Bakış', description: 'Temel göstergeler, riskler ve öncelikli aksiyonlar', icon: LayoutDashboard }],
  },
  {
    id: 'finance-group',
    label: 'Finans',
    description: 'Temel finansal tablolar',
    icon: FileBarChart,
    tabs: financeTabs,
  },
  {
    id: 'cashflow-group',
    label: 'Nakit & Borç',
    description: 'Likidite ve ödeme planı',
    icon: Wallet,
    tabs: [{ id: 'cashflow', label: 'Nakit & Borç', description: '13 haftalık nakit, borç servisi ve ödeme takvimi', icon: Wallet }],
  },
  {
    id: 'analysis-group',
    label: 'Analizler',
    description: 'Müşteri, senaryo ve sektör',
    icon: Sliders,
    tabs: analysisTabs,
  },
  {
    id: 'cfo-group',
    label: 'AI CFO',
    description: 'Uyarılar ve karar desteği',
    icon: Bot,
    tabs: [{ id: 'cfo-agent', label: 'AI CFO', description: 'Uzman ajan bulguları, uyarılar ve aksiyon planı', icon: Bot }],
  },
  {
    id: 'reports-group',
    label: 'Raporlar',
    description: 'Geçmiş, PDF ve Excel',
    icon: FileText,
    tabs: [{ id: 'reports', label: 'Rapor Merkezi', description: 'Geçmiş analizler, karşılaştırmalar ve dışa aktarma', icon: FileText }],
  },
  {
    id: 'data-group',
    label: 'Veri Girişi',
    description: 'Yükle, doğrula ve onayla',
    icon: UploadCloud,
    tabs: [{ id: 'data-entry', label: 'Finansal Veri Girişi', description: 'Excel, Google Sheets veya manuel girişle veriyi doğrula', icon: UploadCloud, restrictedForViewer: true }],
  },
  {
    id: 'settings-group',
    label: 'Şirket Ayarları',
    description: 'Profil, erişim ve veri yaşam döngüsü',
    icon: Settings2,
    tabs: [{ id: 'settings', label: 'Şirket Ayarları', description: 'Şirket kimliği, kullanıcı rolleri ve veri sahipliği', icon: Settings2, restrictedForViewer: true }],
  },
];

const searchableWorkspaceTabs = workspaceMenuGroups.flatMap((group) => group.tabs);

const isGroup = (item: NavigationItem): item is Extract<NavigationItem, { children: TabItem[] }> => 'children' in item;

const BrandMark = () => (
  <span className="relative block h-8 w-11 shrink-0" aria-hidden="true">
    <span className="absolute left-0 top-1 h-7 w-7 rounded-full bg-[radial-gradient(circle_at_35%_30%,#315f9f,#0f2252_68%)]" />
    <span className="absolute right-0 top-1 h-7 w-7 rounded-full bg-[radial-gradient(circle_at_65%_30%,#a883f5,#7c3aed_70%)] opacity-90 mix-blend-multiply" />
    <span className="absolute inset-0 z-10 grid place-items-center text-[11px] font-black text-white">✦</span>
  </span>
);

export const Navigation: React.FC<NavigationProps> = ({ activeTab, setActiveTab, companyName, period, recentTabIds }) => {
  const { userProfile, logout, isPlatformAdmin } = useAuth();
  // Yerel pilot kurulumu production derlemesiyle servis edildiğinde
  // import.meta.env.DEV false olur. Açıkça etkinleştirilen yerel auth
  // bayrağı yönetim menüsünün kaybolmamasını sağlar; API yetkisi yine
  // sunucu tarafından ayrıca doğrulanır.
  const showPlatformAdmin = isPlatformAdmin || import.meta.env.VITE_API_AUTH_DISABLED === 'true';
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [mobileWorkspaceGroup, setMobileWorkspaceGroup] = useState('finance-group');
  const [mobileSearchQuery, setMobileSearchQuery] = useState('');
  const isLanding = activeTab === 'landing';

  useEffect(() => {
    const activeGroup = workspaceMenuGroups.find((group) => group.tabs.some((tab) => tab.id === activeTab));
    if (activeGroup) setMobileWorkspaceGroup(activeGroup.id);
  }, [activeTab]);

  const navigate = (tabId: string) => {
    setActiveTab(tabId);
    setIsMobileMenuOpen(false);
    setMobileSearchQuery('');
    setOpenMenu(null);
    setIsProfileOpen(false);
  };

  const toggleWorkspaceMenu = () => {
    setIsMobileMenuOpen((isOpen) => {
      const nextOpenState = !isOpen;
      if (nextOpenState) {
        const activeGroup = workspaceMenuGroups.find((group) => group.tabs.some((tab) => tab.id === activeTab));
        if (activeGroup) setMobileWorkspaceGroup(activeGroup.id);
        setMobileSearchQuery('');
      }
      return nextOpenState;
    });
  };

  const roleLabel = userProfile?.role === 'admin'
    ? 'Yönetici'
    : userProfile?.role === 'cfo'
      ? 'CFO'
      : userProfile?.role === 'analyst'
        ? 'Analist'
        : userProfile?.role === 'viewer'
          ? 'İzleyici'
          : 'Kullanıcı';

  const displayName = userProfile?.displayName || userProfile?.email?.split('@')[0] || 'Kullanıcı';
  const initials = displayName
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  const isItemActive = (item: NavigationItem) => isGroup(item)
    ? item.children.some((child) => child.id === activeTab)
    : item.id === activeTab;

  const activeLabel = searchableWorkspaceTabs
    .find((item) => item.id === activeTab)?.label || (activeTab === 'platform-admin' ? 'Sistem Yönetimi' : 'Finansal karar merkezi');
  const showWorkspaceSidebar = !isLanding && (
    !userProfile
    || (
      Boolean(userProfile.companyId)
      && (Boolean(userProfile.onboardingProfile) || !['admin', 'cfo'].includes(userProfile.role))
    )
  );
  const selectedMobileGroup = workspaceMenuGroups.find((group) => group.id === mobileWorkspaceGroup) || workspaceMenuGroups[1];
  const normalizedMobileSearch = mobileSearchQuery.trim().toLocaleLowerCase('tr-TR');
  const mobileSearchResults = normalizedMobileSearch
    ? searchableWorkspaceTabs.filter((tab) => `${tab.label} ${tab.description || ''}`.toLocaleLowerCase('tr-TR').includes(normalizedMobileSearch))
    : [];
  const recentTabs = recentTabIds
    .map((tabId) => searchableWorkspaceTabs.find((tab) => tab.id === tabId))
    .filter((tab): tab is TabItem => Boolean(tab));

  return (
    <>
      <header className={`sticky top-0 z-40 border-b backdrop-blur-xl ${
        isLanding
          ? 'border-slate-200/80 bg-white/85 text-slate-900 shadow-[0_8px_30px_rgba(15,34,82,.035)]'
          : 'border-[#e2e5eb] bg-white/95 text-[#0f1729] shadow-[0_1px_0_rgba(15,34,82,.03)]'
      }`}>
        <div className={`mx-auto flex h-[68px] items-center justify-between gap-4 px-4 sm:px-6 ${isLanding ? 'max-w-7xl lg:px-8' : 'max-w-[1480px] lg:px-7'}`}>
          <button type="button" onClick={() => navigate('landing')} className="flex shrink-0 items-center gap-2.5 rounded-lg text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400" aria-label="KazKaz AI ana sayfa">
            <BrandMark />
            <span>
              <span className="block text-[17px] font-extrabold tracking-[-0.025em] text-[#0a1628]">
                KazKaz <span className="bg-gradient-to-r from-[#0f2252] to-[#7c3aed] bg-clip-text text-transparent">AI</span>
              </span>
              {!isLanding && <span className="hidden text-[10px] font-medium text-slate-400 2xl:block">Finansal karar merkezi</span>}
            </span>
          </button>

          {isLanding ? (
            <nav className="hidden items-center gap-6 text-sm font-semibold text-slate-600 lg:flex" aria-label="Tanıtım sayfası">
              <a className="transition hover:text-violet-700" href="#moduller">Modüller</a>
              <a className="transition hover:text-violet-700" href="#veri-yolculugu">Nasıl çalışır?</a>
              <a className="transition hover:text-violet-700" href="#guvenlik">Güven</a>
              <a className="transition hover:text-violet-700" href="#pilot-secenekleri">Pilot erişim</a>
              <a className="transition hover:text-violet-700" href="#sss">SSS</a>
            </nav>
          ) : (
            <div className="hidden min-w-0 flex-1 items-center gap-2 px-5 xl:flex">
              <span className="text-[10px] font-extrabold uppercase tracking-[0.15em] text-slate-400">Çalışma alanı</span>
              <span className="text-slate-300">/</span>
              <span className="truncate text-xs font-extrabold text-[#0f2252]">{activeLabel}</span>
            </div>
          )}

          <div className="hidden shrink-0 items-center gap-2 lg:flex">
            {!isLanding && (
              <div className="mr-1 hidden items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] text-slate-500 2xl:flex">
                <Building2 className="h-3.5 w-3.5 text-violet-600" />
                <span className="max-w-32 truncate font-semibold text-slate-700">{userProfile?.companyName || companyName}</span>
                <span className="rounded bg-white px-1.5 py-0.5 text-[9px] font-bold text-slate-500 shadow-sm">{period}</span>
              </div>
            )}

            {userProfile ? (
              <div className="relative">
                <button type="button" onClick={() => setIsProfileOpen((open) => !open)} aria-expanded={isProfileOpen} className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-2.5 py-1.5 text-xs shadow-sm transition hover:border-violet-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400">
                  <span className="grid h-7 w-7 place-items-center rounded-full bg-gradient-to-br from-[#0f2252] to-[#7c3aed] text-[9px] font-black text-white">{initials}</span>
                  <span className="hidden max-w-24 truncate font-bold text-slate-700 2xl:block">{displayName}</span>
                  <span className="rounded-md bg-violet-50 px-1.5 py-0.5 text-[9px] font-bold text-violet-700">{roleLabel}</span>
                  <ChevronDown className={`h-3.5 w-3.5 text-slate-400 transition ${isProfileOpen ? 'rotate-180' : ''}`} />
                </button>
                {isProfileOpen && (
                  <div className="absolute right-0 top-[calc(100%+8px)] z-50 w-72 rounded-xl border border-slate-200 bg-white p-2 shadow-[0_18px_45px_rgba(15,34,82,.16)]">
                    <div className="border-b border-slate-100 px-3 py-2.5">
                      <p className="truncate text-xs font-extrabold text-slate-900">{displayName}</p>
                      <p className="mt-0.5 truncate text-[10px] text-slate-500">{userProfile.email}</p>
                      <p className="mt-2 text-[10px] font-semibold text-violet-700">{userProfile.companyName || companyName} · {roleLabel}</p>
                    </div>
                    <button type="button" onClick={() => navigate('settings')} className="mt-1 flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-xs font-bold text-slate-600 hover:bg-slate-50 hover:text-[#0f2252]"><Building2 className="h-4 w-4 text-violet-600" /> Şirket ayarları</button>
                    <button type="button" onClick={() => navigate('data-entry')} className="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-xs font-bold text-slate-600 hover:bg-slate-50 hover:text-[#0f2252]"><UploadCloud className="h-4 w-4 text-violet-600" /> Finansal veri girişi</button>
                    <button type="button" onClick={() => navigate('reports')} className="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-xs font-bold text-slate-600 hover:bg-slate-50 hover:text-[#0f2252]"><FileText className="h-4 w-4 text-violet-600" /> Rapor merkezi</button>
                    {showPlatformAdmin && <button type="button" onClick={() => navigate('platform-admin')} className="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-xs font-bold text-violet-700 hover:bg-violet-50"><ServerCog className="h-4 w-4" /> Sistem yönetimi</button>}
                    <button type="button" onClick={logout} className="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-xs font-bold text-red-600 hover:bg-red-50"><LogOut className="h-4 w-4" /> Oturumu kapat</button>
                  </div>
                )}
              </div>
            ) : (
              <button type="button" onClick={() => setIsAuthModalOpen(true)} className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-slate-300 bg-white px-4 text-sm font-bold text-slate-700 transition hover:border-violet-300 hover:text-violet-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400">
                <LogIn className="h-4 w-4" /> Giriş yap
              </button>
            )}

            {isLanding && (
              <button type="button" onClick={() => navigate('overview')} className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-[#0f2252] px-4 text-sm font-bold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-[#1c3674] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400">
                <Sparkles className="h-4 w-4" /> Panele git
              </button>
            )}
          </div>

          <button type="button" onClick={toggleWorkspaceMenu} className="rounded-xl border border-slate-200 bg-white p-2.5 text-slate-700 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400 xl:hidden" aria-label={isMobileMenuOpen ? 'Menüyü kapat' : 'Menüyü aç'} aria-expanded={isMobileMenuOpen}>
            {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {isMobileMenuOpen && (
          <div className="border-t border-slate-200 bg-white px-4 py-4 shadow-2xl xl:hidden">
            <div className="mx-auto max-w-7xl">
              {isLanding ? (
                <nav className="grid gap-2" aria-label="Mobil tanıtım menüsü">
                  {[
                    ['Modüller', '#moduller'],
                    ['Nasıl çalışır?', '#veri-yolculugu'],
                    ['Güven yaklaşımı', '#guvenlik'],
                    ['Pilot erişim', '#pilot-secenekleri'],
                    ['Sık sorulanlar', '#sss'],
                  ].map(([label, href]) => <a key={href} href={href} onClick={() => setIsMobileMenuOpen(false)} className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-700">{label}</a>)}
                  <button type="button" onClick={() => navigate('overview')} className="mt-1 rounded-xl bg-[#0f2252] px-4 py-3 text-sm font-bold text-white">Örnek analizi aç</button>
                </nav>
              ) : (
                <nav className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[0_18px_45px_rgba(15,34,82,.08)]" aria-label="Finans çalışma alanı">
                  <div className="grid min-h-[520px] min-w-0 grid-cols-[minmax(0,1fr)] lg:grid-cols-[230px_minmax(0,1fr)]">
                    <aside className="min-w-0 overflow-hidden border-b border-slate-200 bg-slate-50 p-3 lg:border-b-0 lg:border-r lg:p-4">
                      <p className="mb-3 hidden px-2 text-[9px] font-black uppercase tracking-[0.17em] text-slate-400 lg:block">Çalışma alanı</p>
                      <div className="flex gap-2 overflow-x-auto pb-1 lg:block lg:space-y-1 lg:overflow-visible lg:pb-0">
                        {workspaceMenuGroups.map((group) => {
                          const GroupIcon = group.icon;
                          const isSelected = selectedMobileGroup.id === group.id && !normalizedMobileSearch;
                          const containsActiveTab = group.tabs.some((tab) => tab.id === activeTab);
                          return (
                            <button
                              type="button"
                              key={group.id}
                              onClick={() => {
                                setMobileWorkspaceGroup(group.id);
                                setMobileSearchQuery('');
                              }}
                              aria-pressed={isSelected}
                              className={`group relative flex min-h-12 min-w-[145px] shrink-0 items-center gap-3 rounded-xl px-3 text-left transition lg:mb-1 lg:w-full lg:min-w-0 ${isSelected ? 'bg-[#eef2ff] text-[#0f2252] shadow-[inset_0_0_0_1px_#c7d2fe]' : 'text-slate-600 hover:bg-white hover:text-[#0f2252]'}`}
                            >
                              {isSelected && <span aria-hidden="true" className="absolute inset-y-2 left-0 w-0.5 rounded-full bg-violet-600" />}
                              <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg ${isSelected ? 'bg-white text-violet-700 shadow-sm' : 'bg-slate-100 text-slate-500 group-hover:bg-white'}`}><GroupIcon className="h-4 w-4" /></span>
                              <span className="min-w-0"><span className="block truncate text-[11px] font-extrabold">{group.label}</span><span className="mt-0.5 hidden truncate text-[9px] font-medium text-slate-400 lg:block">{group.description}</span></span>
                              {containsActiveTab && !isSelected && <span className="ml-auto h-1.5 w-1.5 rounded-full bg-violet-500" aria-label="Etkin bölüm" />}
                            </button>
                          );
                        })}
                      </div>
                    </aside>

                    <section className="min-w-0 p-4 sm:p-5 lg:p-6">
                      <label className="flex min-h-12 items-center gap-3 rounded-xl border border-slate-300 bg-slate-50 px-4 shadow-[0_4px_14px_rgba(15,34,82,.04)] transition focus-within:border-violet-400 focus-within:bg-white focus-within:ring-4 focus-within:ring-violet-100">
                        <Search className="h-4 w-4 shrink-0 text-violet-700" />
                        <span className="sr-only">Modül ara</span>
                        <input
                          type="search"
                          value={mobileSearchQuery}
                          onChange={(event) => setMobileSearchQuery(event.target.value)}
                          placeholder="Modül, rapor veya finansal metrik ara…"
                          className="min-w-0 flex-1 border-0 bg-transparent text-xs font-semibold text-slate-800 outline-none placeholder:font-medium placeholder:text-slate-400"
                        />
                        <span className="hidden rounded-md border border-slate-200 bg-white px-2 py-1 text-[8px] font-black text-slate-400 sm:block">AKILLI ARAMA</span>
                      </label>

                      {!normalizedMobileSearch && recentTabs.length > 0 && (
                        <section className="mt-5">
                          <div className="mb-2 flex items-center gap-2">
                            <Clock3 className="h-3.5 w-3.5 text-slate-400" />
                            <p className="text-[9px] font-black uppercase tracking-[0.15em] text-slate-400">Son kullandıklarınız</p>
                          </div>
                          <div className="grid gap-2 sm:grid-cols-3">
                            {recentTabs.map((tab) => {
                              const RecentIcon = tab.icon;
                              return (
                                <button type="button" key={tab.id} onClick={() => navigate(tab.id)} className="group flex min-h-[60px] min-w-0 items-center gap-3 rounded-xl border border-slate-200 bg-white px-3 text-left transition hover:border-violet-200 hover:bg-violet-50/40">
                                  <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-violet-50 text-violet-700"><RecentIcon className="h-3.5 w-3.5" /></span>
                                  <span className="min-w-0 flex-1"><span className="block truncate text-[10px] font-extrabold text-slate-700">{tab.label}</span><span className="mt-1 block text-[8px] font-semibold text-slate-400">Kaldığınız yerden devam edin</span></span>
                                  <ArrowRight className="h-3.5 w-3.5 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-violet-600" />
                                </button>
                              );
                            })}
                          </div>
                        </section>
                      )}

                      <section className={`${!normalizedMobileSearch ? 'mt-5 border-t border-slate-100 pt-5' : 'mt-5'}`}>
                        <div className="mb-3 flex items-start gap-3">
                          <div className="min-w-0 flex-1">
                            <h2 className="text-base font-extrabold tracking-[-0.025em] text-[#0a1628]">{normalizedMobileSearch ? 'Arama sonuçları' : selectedMobileGroup.label}</h2>
                            <p className="mt-1 text-[10px] leading-4 text-slate-500">{normalizedMobileSearch ? `“${mobileSearchQuery.trim()}” için eşleşen çalışma alanları` : selectedMobileGroup.description}</p>
                          </div>
                          <span className="shrink-0 rounded-full border border-violet-200 bg-violet-50 px-2.5 py-1.5 text-[8px] font-extrabold text-violet-700">{normalizedMobileSearch ? mobileSearchResults.length : selectedMobileGroup.tabs.length} modül</span>
                        </div>

                        {(normalizedMobileSearch ? mobileSearchResults : selectedMobileGroup.tabs).length > 0 ? (
                          <div className="grid gap-2 sm:grid-cols-2">
                            {(normalizedMobileSearch ? mobileSearchResults : selectedMobileGroup.tabs).map((tab) => {
                              const TabIcon = tab.icon;
                              const isActive = tab.id === activeTab;
                              const isRestricted = userProfile?.role === 'viewer' && tab.restrictedForViewer;
                              return (
                                <button type="button" key={tab.id} onClick={() => navigate(tab.id)} className={`group flex min-h-[86px] items-start gap-3 rounded-xl border p-3.5 text-left transition ${isActive ? 'border-violet-200 bg-violet-50 text-violet-900 shadow-sm' : 'border-slate-200 bg-white text-slate-700 hover:-translate-y-0.5 hover:border-violet-200 hover:shadow-[0_8px_18px_rgba(15,34,82,.06)]'}`}>
                                  <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-lg ${isActive ? 'bg-white text-violet-700 shadow-sm' : 'bg-slate-100 text-slate-500 group-hover:bg-violet-50 group-hover:text-violet-700'}`}><TabIcon className="h-4 w-4" /></span>
                                  <span className="min-w-0 flex-1"><span className="flex items-center gap-2 text-xs font-extrabold"><span className="truncate">{tab.label}</span>{isRestricted && <span className="shrink-0 text-[8px] font-bold text-amber-600">Salt okunur</span>}</span><span className="mt-1.5 block text-[9px] leading-4 text-slate-500">{tab.description}</span></span>
                                  <ArrowRight className="mt-1 h-3.5 w-3.5 shrink-0 text-slate-300 transition group-hover:translate-x-0.5 group-hover:text-violet-600" />
                                </button>
                              );
                            })}
                          </div>
                        ) : (
                          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-5 py-10 text-center">
                            <Search className="mx-auto h-5 w-5 text-slate-400" />
                            <p className="mt-3 text-xs font-extrabold text-slate-700">Eşleşen modül bulunamadı</p>
                            <p className="mt-1 text-[10px] text-slate-500">“Nakit”, “bilanço”, “müşteri” veya “rapor” gibi bir ifade deneyin.</p>
                          </div>
                        )}
                      </section>
                    </section>
                  </div>
                </nav>
              )}

              <div className="mt-4 flex items-center justify-between border-t border-slate-200 pt-4">
                <div className="min-w-0 text-xs text-slate-500">
                  {userProfile ? <><p className="truncate font-semibold text-slate-800">{displayName}</p><p className="mt-1">{roleLabel}</p></> : <p>Örnek veriyi giriş yapmadan inceleyebilirsiniz.</p>}
                </div>
                {userProfile ? <button type="button" onClick={logout} className="ml-4 text-sm font-semibold text-red-600">Çıkış yap</button> : <button type="button" onClick={() => setIsAuthModalOpen(true)} className="ml-4 shrink-0 text-sm font-semibold text-violet-700">Giriş yap</button>}
              </div>
            </div>
          </div>
        )}
      </header>

      {showWorkspaceSidebar && (
        <aside className="fixed bottom-0 left-0 top-[68px] z-30 hidden w-[246px] flex-col border-r border-slate-200 bg-white xl:flex" aria-label="Finans çalışma alanı bölümleri">
          <div className="border-b border-slate-100 p-4">
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3.5">
              <div className="flex items-start gap-3">
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-violet-100 text-violet-700"><Building2 className="h-4 w-4" /></span>
                <div className="min-w-0">
                  <p className="truncate text-xs font-extrabold text-slate-900">{userProfile?.companyName || companyName}</p>
                  <p className="mt-1 text-[10px] font-semibold text-slate-500">{period} dönemi</p>
                </div>
              </div>
            </div>
          </div>

          <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
            <p className="px-3 pb-2 text-[9px] font-black uppercase tracking-[0.17em] text-slate-400">Finans merkezi</p>
            {workspaceNavigation.map((item) => {
              const Icon = item.icon;
              const isActive = isItemActive(item);
              if (!isGroup(item)) {
                const isAi = item.id === 'cfo-agent';
                return (
                  <button type="button" key={item.id} onClick={() => navigate(item.id)} aria-current={isActive ? 'page' : undefined} className={`group relative flex min-h-11 w-full items-center gap-3 overflow-hidden rounded-xl px-3 text-left text-xs font-extrabold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400 ${isActive ? 'bg-[#eef2ff] text-[#0f2252] shadow-[inset_0_0_0_1px_#c7d2fe]' : 'text-slate-600 hover:bg-slate-50 hover:text-[#0f2252]'}`}>
                    {isActive && <span aria-hidden="true" className="panel-nav-indicator absolute inset-y-2 left-0 w-0.5 rounded-full bg-violet-600" />}
                    <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg transition ${isActive ? 'bg-white text-violet-700 shadow-sm' : isAi ? 'bg-violet-50 text-violet-700' : 'bg-slate-100 text-slate-500 group-hover:bg-white'}`}><Icon className="h-4 w-4" /></span>
                    <span className="flex-1">{item.label}</span>
                    {isAi && !isActive && <span className="h-1.5 w-1.5 rounded-full bg-violet-500 shadow-[0_0_0_3px_#ede9fe]" aria-label="AI aktif" />}
                  </button>
                );
              }

              const menuOpen = openMenu === item.id || isActive;
              return (
                <div key={item.id} className="space-y-1">
                  <button type="button" onClick={() => setOpenMenu(openMenu === item.id ? null : item.id)} aria-expanded={menuOpen} className={`group flex min-h-11 w-full items-center gap-3 rounded-xl px-3 text-left text-xs font-extrabold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400 ${isActive ? 'text-[#0f2252]' : 'text-slate-600 hover:bg-slate-50 hover:text-[#0f2252]'}`}>
                    <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-lg transition ${isActive ? 'bg-violet-100 text-violet-700' : 'bg-slate-100 text-slate-500 group-hover:bg-white'}`}><Icon className="h-4 w-4" /></span>
                    <span className="flex-1">{item.label}</span>
                    <ChevronDown className={`h-3.5 w-3.5 text-slate-400 transition ${menuOpen ? 'rotate-180' : ''}`} />
                  </button>
                  {menuOpen && (
                    <div className="ml-7 space-y-1 border-l border-violet-100 pl-3">
                      {item.children.map((child) => {
                        const ChildIcon = child.icon;
                        const childActive = child.id === activeTab;
                        return (
                          <button type="button" key={child.id} onClick={() => navigate(child.id)} className={`flex min-h-9 w-full items-center gap-2.5 rounded-lg px-2.5 text-left text-[11px] font-bold transition ${childActive ? 'bg-violet-50 text-violet-800' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}`}>
                            <ChildIcon className={`h-3.5 w-3.5 ${childActive ? 'text-violet-700' : 'text-slate-400'}`} />
                            <span>{child.label}</span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </nav>

          <div className="border-t border-slate-100 p-3">
            <button type="button" onClick={() => navigate('data-entry')} className={`flex min-h-11 w-full items-center gap-3 rounded-xl px-3 text-left text-xs font-bold transition ${activeTab === 'data-entry' ? 'bg-violet-50 text-violet-800' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}`}>
              <UploadCloud className="h-4 w-4 text-violet-600" /> Finansal veri girişi
            </button>
            <button type="button" onClick={() => navigate('settings')} className={`mt-1 flex min-h-11 w-full items-center gap-3 rounded-xl px-3 text-left text-xs font-bold transition ${activeTab === 'settings' ? 'bg-violet-50 text-violet-800' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'}`}>
              <Settings2 className="h-4 w-4 text-violet-600" /> Şirket ayarları
            </button>
            {showPlatformAdmin && <button type="button" onClick={() => navigate('platform-admin')} className={`mt-1 flex min-h-11 w-full items-center gap-3 rounded-xl px-3 text-left text-xs font-extrabold transition ${activeTab === 'platform-admin' ? 'bg-[#0f2252] text-white' : 'bg-violet-50 text-violet-800 hover:bg-violet-100'}`}><ServerCog className="h-4 w-4" /> Sistem yönetimi</button>}
          </div>
        </aside>
      )}

      <AuthModal isOpen={isAuthModalOpen} onClose={() => setIsAuthModalOpen(false)} />
    </>
  );
};

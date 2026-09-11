import React from 'react';
import { sekmeninEkrani } from '../lib/navigation';
import { useAuth } from '../context/AuthContext';

interface ScreenTabsProps {
  activeTab: string;
  onNavigateTab: (tabId: string) => void;
}

/**
 * Aktif ekranın başlığı ve alt sekmeleri.
 *
 * Sidebar beş kapıyı gösterir; derinlik burada açılır. Tek sekmeli
 * ekranlarda (CFO'ya Sor) sekme şeridi çizilmez.
 */
export const ScreenTabs: React.FC<ScreenTabsProps> = ({ activeTab, onNavigateTab }) => {
  const { userProfile } = useAuth();
  const ekran = sekmeninEkrani(activeTab);
  if (!ekran) return null;

  const isViewer = userProfile?.role === 'viewer';
  const gorunurSekmeler = ekran.tabs.filter((tab) => !(tab.restrictedForViewer && isViewer));

  return (
    <div className="mb-5 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        <p className="panel-kicker">{ekran.label}</p>
        <h1 className="font-display mt-1 text-[25px] font-bold text-[#0f1729]">{ekran.soru}</h1>
      </div>

      {gorunurSekmeler.length > 1 && (
        <div role="tablist" aria-label={`${ekran.label} bölümleri`} className="flex shrink-0 gap-1.5 overflow-x-auto rounded-xl bg-[#eef0f4] p-1">
          {gorunurSekmeler.map((tab) => {
            const isActive = tab.id === activeTab;
            return (
              <button
                type="button"
                key={tab.id}
                role="tab"
                aria-selected={isActive}
                title={tab.description}
                onClick={() => onNavigateTab(tab.id)}
                className={`min-h-9 shrink-0 rounded-lg px-3.5 text-xs font-bold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400 ${
                  isActive
                    ? 'bg-white text-[#0f2252] shadow-[0_1px_2px_rgba(15,34,82,.07)]'
                    : 'text-slate-500 hover:text-[#0f2252]'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

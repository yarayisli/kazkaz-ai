import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { FinancialAlert, AlertThresholds, BudgetItem, CashFlowItem } from '../types';
import { audioFx } from '../utils/audioEffects';
import { initialBudget, initialCashFlow, initialCustomers } from '../data/mockData';

interface ToastAlert extends FinancialAlert {
  toastId: string;
}

interface AlertContextType {
  alerts: FinancialAlert[];
  toasts: ToastAlert[];
  unreadCount: number;
  activeModalAlert: FinancialAlert | null;
  setActiveModalAlert: (alert: FinancialAlert | null) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearAlert: (id: string) => void;
  dismissToast: (toastId: string) => void;
  triggerAlert: (alert: Omit<FinancialAlert, 'id' | 'timestamp' | 'read'>) => void;
  triggerBudgetTestAlert: (category?: string, overrunAmount?: number) => void;
  triggerCashflowTestAlert: (dropAmount?: number) => void;
  runFullFinancialScan: () => void;
  thresholds: AlertThresholds;
  updateThresholds: (newThresholds: Partial<AlertThresholds>) => void;
  isMuted: boolean;
  toggleSound: () => void;
}

const defaultThresholds: AlertThresholds = {
  budgetOverrunPercent: 5,
  cashflowDropTRY: 100000,
  maxPaymentDays: 60,
};

const defaultInitialAlerts: FinancialAlert[] = [
  {
    id: 'alt-bgt-1',
    type: 'budget_exceeded',
    severity: 'critical',
    title: 'Danışmanlık & Hukuk Bütçe Aşımı!',
    message: 'Planlanan ₺200.000 bütçeye karşılık ₺240.000 harcama yapıldı. Bütçe limiti %20.0 (₺40.000) aşıldı.',
    category: 'Danışmanlık & Hukuk',
    amount: 240000,
    threshold: 'Limit: ₺200.000 (+%20 Aşım)',
    timestamp: 'Şimdi',
    read: false,
    actionTab: 'budget',
    actionLabel: 'Bütçe Tablosunu İncele',
  },
  {
    id: 'alt-bgt-2',
    type: 'budget_exceeded',
    severity: 'warning',
    title: 'Personel Giderleri Bütçe Sınırı Aşıldı',
    message: 'Planlanan ₺2.200.000 bütçeye karşılık ₺2.350.000 harcandı. Bütçe limiti %6.8 (₺150.000) üzerinde.',
    category: 'Personel Giderleri',
    amount: 2350000,
    threshold: 'Limit: ₺2.200.000 (+%6.8 Aşım)',
    timestamp: '10 dk önce',
    read: false,
    actionTab: 'budget',
    actionLabel: 'Gider Kalemlerini Gör',
  },
  {
    id: 'alt-cf-1',
    type: 'cashflow_drop',
    severity: 'critical',
    title: 'Kritik Nakit Akışı Düşüşü (Mart)',
    message: 'Mart ayında net nakit girişi -₺200.000 negatif gerçekleşti. Kredi taksitleri ve tedarikçi ödemeleri için rezerv riski mevcut.',
    amount: -200000,
    threshold: 'Eşik: Net Nakit > ₺0',
    timestamp: '15 dk önce',
    read: false,
    actionTab: 'cashflow',
    actionLabel: 'Nakit Tablosuna Git',
  },
  {
    id: 'alt-cust-1',
    type: 'customer_risk',
    severity: 'critical',
    title: 'TeknoMarket Mağazacılık - 92 Gün Tahsilat Gecikmesi',
    message: 'Müşterinizin Ortalama Tahsilat Süresi (DSO) 92 güne ulaştı (Risk Eşiği: 60 Gün). Toplam alacak: ₺950.000',
    amount: 950000,
    threshold: 'Eşik: 60 Gün',
    timestamp: '1 saat önce',
    read: true,
    actionTab: 'customer',
    actionLabel: 'Müşteri Riskini Aç',
  }
];

const AlertContext = createContext<AlertContextType | undefined>(undefined);

export const AlertProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [alerts, setAlerts] = useState<FinancialAlert[]>(defaultInitialAlerts);
  const [toasts, setToasts] = useState<ToastAlert[]>([]);
  const [activeModalAlert, setActiveModalAlert] = useState<FinancialAlert | null>(null);
  const [thresholds, setThresholds] = useState<AlertThresholds>(defaultThresholds);
  const [isMuted, setIsMuted] = useState<boolean>(false);

  const unreadCount = alerts.filter(a => !a.read).length;

  const toggleSound = () => {
    const muted = audioFx.toggleMute();
    setIsMuted(muted);
  };

  const addToast = (alert: FinancialAlert) => {
    const toastId = 'toast-' + Date.now() + '-' + Math.random().toString(36).substring(2, 5);
    const newToast: ToastAlert = { ...alert, toastId };
    setToasts(prev => [newToast, ...prev.slice(0, 4)]); // Keep max 5 toasts

    // Auto dismiss after 8 seconds
    setTimeout(() => {
      dismissToast(toastId);
    }, 8000);
  };

  const dismissToast = (toastId: string) => {
    setToasts(prev => prev.filter(t => t.toastId !== toastId));
  };

  const markAsRead = (id: string) => {
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, read: true } : a));
  };

  const markAllAsRead = () => {
    setAlerts(prev => prev.map(a => ({ ...a, read: true })));
  };

  const clearAlert = (id: string) => {
    setAlerts(prev => prev.filter(a => a.id !== id));
  };

  const triggerAlert = (rawAlert: Omit<FinancialAlert, 'id' | 'timestamp' | 'read'>) => {
    const id = 'alt-' + Date.now();
    const newAlert: FinancialAlert = {
      ...rawAlert,
      id,
      timestamp: 'Şimdi',
      read: false,
    };

    setAlerts(prev => [newAlert, ...prev]);
    addToast(newAlert);

    // Audio FX
    if (newAlert.severity === 'critical') {
      audioFx.playCriticalAlert();
    } else {
      audioFx.playWarningAlert();
    }
  };

  const triggerBudgetTestAlert = (category = 'Pazarlama & Reklam', overrunAmount = 185000) => {
    triggerAlert({
      type: 'budget_exceeded',
      severity: 'critical',
      title: `🚨 BÜTÇE AŞIMI UYARISI: ${category}`,
      message: `${category} kaleminde anlık gerçekleşen harcama bütçeyi ₺${overrunAmount.toLocaleString('tr-TR')} (+%30.8) aşıyor! Acil bütçe revizyonu önerilir.`,
      category,
      amount: overrunAmount,
      threshold: `Bütçe Limiti Aşıldı (Eşik: %${thresholds.budgetOverrunPercent})`,
      actionTab: 'budget',
      actionLabel: 'Bütçeyi Düzenle',
    });
  };

  const triggerCashflowTestAlert = (dropAmount = 450000) => {
    triggerAlert({
      type: 'cashflow_drop',
      severity: 'critical',
      title: '📉 KRİTİK NAKİT AKIŞI DÜŞÜŞÜ ALGILANDI!',
      message: `Son simülasyonda ₺${dropAmount.toLocaleString('tr-TR')} tutarında ani nakit çıkışı ve tahsilat gecikmesi algılandı. Operasyonel rezerv kırmızı seviyede.`,
      amount: -dropAmount,
      threshold: `Kritik Düşüş Eşiği: ₺${thresholds.cashflowDropTRY.toLocaleString('tr-TR')}`,
      actionTab: 'cashflow',
      actionLabel: 'Nakit Akışını Taramasını Aç',
    });
  };

  const runFullFinancialScan = () => {
    // Scan budget
    initialBudget.forEach(b => {
      if (b.actual > b.planned && Math.abs(b.variancePercent) >= thresholds.budgetOverrunPercent) {
        const exists = alerts.some(a => a.category === b.category && a.type === 'budget_exceeded');
        if (!exists) {
          triggerAlert({
            type: 'budget_exceeded',
            severity: Math.abs(b.variancePercent) > 15 ? 'critical' : 'warning',
            title: `Bütçe Aşımı: ${b.category}`,
            message: `${b.category} bütçesi %${Math.abs(b.variancePercent).toFixed(1)} aşıldı. Plan: ₺${b.planned.toLocaleString('tr-TR')}, Gerçekleşen: ₺${b.actual.toLocaleString('tr-TR')}`,
            category: b.category,
            amount: b.actual,
            threshold: `%${thresholds.budgetOverrunPercent} Eşiği`,
            actionTab: 'budget',
            actionLabel: 'Bütçe Tablosu',
          });
        }
      }
    });

    // Scan cashflow drops
    initialCashFlow.forEach(cf => {
      if (cf.netCash < 0 || Math.abs(cf.netCash) > thresholds.cashflowDropTRY) {
        const exists = alerts.some(a => a.message.includes(cf.month) && a.type === 'cashflow_drop');
        if (!exists) {
          triggerAlert({
            type: 'cashflow_drop',
            severity: 'critical',
            title: `${cf.month} Ayı Nakit Açığı`,
            message: `${cf.month} döneminde net nakit girişi ₺${cf.netCash.toLocaleString('tr-TR')} seviyesinde gerçekleşti.`,
            amount: cf.netCash,
            threshold: `Nakit Düşüş Eşiği: ₺${thresholds.cashflowDropTRY.toLocaleString('tr-TR')}`,
            actionTab: 'cashflow',
            actionLabel: 'Nakit Akışı Tablosu',
          });
        }
      }
    });

    audioFx.playSuccessChime();
  };

  const updateThresholds = (newThresholds: Partial<AlertThresholds>) => {
    setThresholds(prev => ({ ...prev, ...newThresholds }));
    audioFx.playSuccessChime();
  };

  return (
    <AlertContext.Provider
      value={{
        alerts,
        toasts,
        unreadCount,
        activeModalAlert,
        setActiveModalAlert,
        markAsRead,
        markAllAsRead,
        clearAlert,
        dismissToast,
        triggerAlert,
        triggerBudgetTestAlert,
        triggerCashflowTestAlert,
        runFullFinancialScan,
        thresholds,
        updateThresholds,
        isMuted,
        toggleSound,
      }}
    >
      {children}
    </AlertContext.Provider>
  );
};

export const useAlerts = () => {
  const context = useContext(AlertContext);
  if (!context) {
    throw new Error('useAlerts must be used within an AlertProvider');
  }
  return context;
};

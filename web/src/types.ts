export interface FinancialData {
  companyName: string;
  sector: string;
  currency: string;
  period: string;
  revenue: number;
  costOfGoods: number;
  grossProfit: number;
  operatingExpenses: number;
  interestExpense: number;
  taxExpense: number;
  depreciation: number;
  capex: number;
  ebitda: number;
  netProfit: number;
  cashInHand: number;
  shortTermDebt: number;
  longTermDebt: number;
  receivables: number;
  payables: number;
  inventory: number;
  equity: number;
  currentAssets?: number;
  totalAssets?: number;
  totalLiabilities?: number;
  retainedEarnings?: number;
  operatingCashFlow?: number;
  beginningCash?: number;
  investingCashFlow?: number;
  financingCashFlow?: number;
  periodDays?: number;
  effectiveTaxRate?: number;
  customerRevenues?: Array<{ id: string; name: string; revenue: number }>;
  dataQuality?: {
    source: 'financial_overview' | 'transaction_summary';
    balanceAvailable: boolean;
    ebitdaAvailable: boolean;
    missing: string[];
  };
}

export interface KpiMetric {
  title: string;
  value: string;
  subtext: string;
  status: 'positive' | 'negative' | 'neutral' | 'warning';
  change?: string;
  tooltip?: string;
}

export interface CashFlowItem {
  month: string;
  inflow: number;
  outflow: number;
  netCash: number;
  cumulativeCash: number;
}

export interface DebtItem {
  id: string;
  creditor: string;
  type: string;
  amount: number;
  interestRate: number;
  interestAmount?: number;
  currency?: string;
  dueDate: string;
  status: 'active' | 'warning' | 'critical';
}

export interface CustomerRisk {
  id: string;
  name: string;
  sharePercentage: number;
  receivableAmount: number;
  avgPaymentDays: number;
  riskLevel: 'düşük' | 'orta' | 'yüksek' | 'kritik';
}

export interface TransactionAnalytics {
  aylik_trend: Array<{ donem: string; gelir: number; gider: number; net: number }>;
  musteriler: Array<{
    id: string; ad: string; gelir: number; islem_sayisi: number; son_islem: string;
    son_islemden_gun: number; rfm_skoru: number; segment: string; gelir_payi: number;
  }>;
  urunler: Array<{
    urun: string; gelir: number; islem_sayisi: number; musteri_sayisi: number; gelir_payi: number;
  }>;
  tahmin: {
    durum: 'hazir' | 'veri_bekliyor'; yontem?: string; gecmis_hata_mape?: number | null;
    veri_ayi?: number; guven?: 'dusuk' | 'orta'; uyari?: string; gereken?: string;
    band_turu?: 'istatistiksel' | 'senaryo'; band_kalibrasyonu?: string;
    noktalar: Array<{ donem: string; tahmin: number; alt: number; ust: number }>;
  };
  metodoloji: Record<string, string>;
}

export interface BudgetItem {
  category: string;
  planned: number;
  actual: number;
  variance: number;
  variancePercent: number;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: string;
  suggestions?: string[];
}

export interface FinancialAlert {
  id: string;
  type: 'budget_exceeded' | 'cashflow_drop' | 'debt_risk' | 'customer_risk' | 'simulated';
  severity: 'critical' | 'warning' | 'info';
  title: string;
  message: string;
  category?: string;
  amount?: number;
  threshold?: string;
  timestamp: string;
  read: boolean;
  actionTab: string;
  actionLabel: string;
}

export interface AlertThresholds {
  budgetOverrunPercent: number; // e.g. 5 (%)
  cashflowDropTRY: number; // e.g. 100000 (TRY)
  maxPaymentDays: number; // e.g. 60 (days)
}

export interface ApprovalDecision {
  id: string;
  action: string;
  status: 'pending' | 'approved' | 'rejected' | 'completed';
  createdAt: string;
  decidedAt?: string;
  decidedBy?: string;
  owner?: string;
  dueDate?: string;
  expectedImpact?: number;
  implementationCost?: number;
  actualImpact?: number;
  impactUnit?: 'TRY' | '%' | 'day';
  outcomeNote?: string;
  measuredAt?: string;
  outcomeConfirmedBy?: string;
  publicationConsent?: boolean;
  publicationConsentAt?: string;
  publicationConsentVersion?: string;
  evidence: Array<{
    metric: string;
    value: number;
    unit: string;
    formulaId: string;
  }>;
}

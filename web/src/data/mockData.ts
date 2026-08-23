import { FinancialData, CashFlowItem, DebtItem, CustomerRisk, BudgetItem } from '../types';

export const initialFinancialData: FinancialData = {
  companyName: "Anadolu Teknoloji A.Ş.",
  sector: "Yazılım & Bilişim",
  currency: "TRY",
  period: "2025 / Q1",
  revenue: 14850000,
  costOfGoods: 6200000,
  grossProfit: 8650000,
  operatingExpenses: 4100000,
  interestExpense: 310000,
  taxExpense: 420000,
  depreciation: 400000,
  capex: 780000,
  ebitda: 4550000,
  netProfit: 3420000,
  cashInHand: 2850000,
  shortTermDebt: 3100000,
  longTermDebt: 5400000,
  receivables: 4900000,
  payables: 2750000,
  inventory: 1200000,
  equity: 12500000,
};

export const initialCashFlow: CashFlowItem[] = [
  { month: 'Ocak', inflow: 2200000, outflow: 1850000, netCash: 350000, cumulativeCash: 2150000 },
  { month: 'Şubat', inflow: 2450000, outflow: 1900000, netCash: 550000, cumulativeCash: 2700000 },
  { month: 'Mart', inflow: 2100000, outflow: 2300000, netCash: -200000, cumulativeCash: 2500000 },
  { month: 'Nisan', inflow: 2800000, outflow: 2100000, netCash: 700000, cumulativeCash: 3200000 },
  { month: 'Mayıs', inflow: 2600000, outflow: 2400000, netCash: 200000, cumulativeCash: 3400000 },
  { month: 'Haziran', inflow: 2900000, outflow: 2250000, netCash: 650000, cumulativeCash: 4050000 },
];

export const initialDebts: DebtItem[] = [
  { id: '1', creditor: 'Garanti BBVA - Ticari Kredi', type: 'Banka Kredisi', amount: 1850000, interestRate: 38.5, dueDate: '2025-05-15', status: 'warning' },
  { id: '2', creditor: 'İş Bankası - Rotatif Kredi', type: 'Rotatif Kredi', amount: 1250000, interestRate: 42.0, dueDate: '2025-04-30', status: 'critical' },
  { id: '3', creditor: 'Akbank - Yatırım Kredisi', type: 'Uzun Vadeli', amount: 3400000, interestRate: 32.0, dueDate: '2027-11-20', status: 'active' },
  { id: '4', creditor: 'Vergi Dairesi - Yapılandırma', type: 'Kamu Borcu', amount: 650000, interestRate: 24.0, dueDate: '2025-06-10', status: 'active' },
];

export const initialCustomers: CustomerRisk[] = [
  { id: '1', name: 'Global Lojistik A.Ş.', sharePercentage: 28.5, receivableAmount: 1800000, avgPaymentDays: 78, riskLevel: 'yüksek' },
  { id: '2', name: 'Doğuş Enerji Sistemleri', sharePercentage: 21.0, receivableAmount: 1250000, avgPaymentDays: 45, riskLevel: 'orta' },
  { id: '3', name: 'TeknoMarket Mağazacılık', sharePercentage: 16.2, receivableAmount: 950000, avgPaymentDays: 92, riskLevel: 'kritik' },
  { id: '4', name: 'Atlas Bilişim Hizmetleri', sharePercentage: 12.8, receivableAmount: 520000, avgPaymentDays: 30, riskLevel: 'düşük' },
  { id: '5', name: 'Diğer Müşteriler (14 Firma)', sharePercentage: 21.5, receivableAmount: 380000, avgPaymentDays: 35, riskLevel: 'düşük' },
];

export const initialBudget: BudgetItem[] = [
  { category: 'Personel Giderleri', planned: 2200000, actual: 2350000, variance: -150000, variancePercent: -6.8 },
  { category: 'Pazarlama & Reklam', planned: 600000, actual: 520000, variance: 80000, variancePercent: 13.3 },
  { category: 'Ofis & Sunucu Giderleri', planned: 450000, actual: 480000, variance: -30000, variancePercent: -6.7 },
  { category: 'Ar-Ge & Yazılım', planned: 550000, actual: 510000, variance: 40000, variancePercent: 7.3 },
  { category: 'Danışmanlık & Hukuk', planned: 200000, actual: 240000, variance: -40000, variancePercent: -20.0 },
];

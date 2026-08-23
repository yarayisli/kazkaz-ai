import {
  calismaAlaniDisaAktar,
  calismaAlaniKaydet,
  calismaAlaniSil,
  calismaAlaniYukle,
  FinansalDenetim,
  GelismisAjanGirdisi,
} from './api';
import {
  BudgetItem,
  CashFlowItem,
  CustomerRisk,
  DebtItem,
  FinancialData,
  TransactionAnalytics,
  ApprovalDecision,
} from '../types';

export interface WorkspaceSnapshot {
  financialData: FinancialData;
  cashFlow: CashFlowItem[];
  debts: DebtItem[];
  customers: CustomerRisk[];
  budget: BudgetItem[];
  advancedData?: GelismisAjanGirdisi;
  transactionAnalytics?: TransactionAnalytics;
  financialAudit: FinansalDenetim | null;
  isSampleData: boolean;
  approvalDecisions?: ApprovalDecision[];
}

const MAX_WORKSPACE_BYTES = 750_000;

function cleanSnapshot(snapshot: WorkspaceSnapshot): WorkspaceSnapshot {
  return JSON.parse(JSON.stringify(snapshot)) as WorkspaceSnapshot;
}

export async function saveWorkspace(
  _companyId: string,
  _userId: string,
  snapshot: WorkspaceSnapshot,
): Promise<void> {
  const cleaned = cleanSnapshot(snapshot);
  const byteSize = new TextEncoder().encode(JSON.stringify(cleaned)).byteLength;
  if (byteSize > MAX_WORKSPACE_BYTES) {
    throw new Error('Çalışma alanı güvenli kayıt sınırını aşıyor. Ham veriyi yeniden yükleyin veya daha küçük dönem seçin.');
  }
  await calismaAlaniKaydet(cleaned);
}

export async function loadWorkspace(_companyId: string): Promise<WorkspaceSnapshot | null> {
  const sonuc = await calismaAlaniYukle<WorkspaceSnapshot>();
  if (!sonuc.snapshot) return null;
  const data = sonuc.snapshot;
  if (!data.financialData || !Array.isArray(data.cashFlow)) {
    throw new Error('Kayıtlı çalışma alanının sürümü desteklenmiyor.');
  }
  return {
    financialData: data.financialData as FinancialData,
    cashFlow: data.cashFlow as CashFlowItem[],
    debts: (data.debts || []) as DebtItem[],
    customers: (data.customers || []) as CustomerRisk[],
    budget: (data.budget || []) as BudgetItem[],
    advancedData: data.advancedData as GelismisAjanGirdisi | undefined,
    transactionAnalytics: data.transactionAnalytics as TransactionAnalytics | undefined,
    financialAudit: (data.financialAudit || null) as FinansalDenetim | null,
    isSampleData: Boolean(data.isSampleData),
    approvalDecisions: (data.approvalDecisions || []) as ApprovalDecision[],
  };
}

export async function deleteWorkspace(companyId: string): Promise<void> {
  void companyId;
  await calismaAlaniSil();
}

export async function exportWorkspace(): Promise<void> {
  await calismaAlaniDisaAktar();
}

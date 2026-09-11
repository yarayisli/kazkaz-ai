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

export interface WorkspaceYuklemeSonucu {
  snapshot: WorkspaceSnapshot | null;
  /** Kaydederken geri gönderilecek optimistik kilit sürümü. */
  revizyon: number;
}

export async function saveWorkspace(
  _companyId: string,
  _userId: string,
  snapshot: WorkspaceSnapshot,
  bazRevizyon: number,
): Promise<{ revizyon: number }> {
  const cleaned = cleanSnapshot(snapshot);
  const byteSize = new TextEncoder().encode(JSON.stringify(cleaned)).byteLength;
  if (byteSize > MAX_WORKSPACE_BYTES) {
    throw new Error('Çalışma alanı güvenli kayıt sınırını aşıyor. Ham veriyi yeniden yükleyin veya daha küçük dönem seçin.');
  }
  const sonuc = await calismaAlaniKaydet(cleaned, bazRevizyon);
  return { revizyon: sonuc.revizyon };
}

export async function loadWorkspace(_companyId: string): Promise<WorkspaceYuklemeSonucu> {
  const sonuc = await calismaAlaniYukle<WorkspaceSnapshot>();
  const revizyon = sonuc.revizyon ?? 0;
  if (!sonuc.snapshot) return { snapshot: null, revizyon };
  const data = sonuc.snapshot;
  if (!data.financialData || !Array.isArray(data.cashFlow)) {
    throw new Error('Kayıtlı çalışma alanının sürümü desteklenmiyor.');
  }
  return {
    snapshot: {
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
    },
    revizyon,
  };
}

export async function deleteWorkspace(companyId: string, bazRevizyon: number): Promise<{ revizyon: number }> {
  void companyId;
  return calismaAlaniSil(bazRevizyon);
}

export async function exportWorkspace(): Promise<void> {
  await calismaAlaniDisaAktar();
}

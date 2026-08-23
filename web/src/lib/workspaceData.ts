import { BudgetItem, CashFlowItem, CustomerRisk, DebtItem } from '../types';
import { GelismisAjanGirdisi } from './api';

export interface WorkspaceCollections {
  cashFlow?: CashFlowItem[];
  debts?: DebtItem[];
  customers?: CustomerRisk[];
  budget?: BudgetItem[];
}

const value = (amount?: number | null) => amount ?? 0;

export function workspaceDataFromAdvanced(input: GelismisAjanGirdisi): WorkspaceCollections {
  const output: WorkspaceCollections = {};

  if (input.haftalik_nakit) {
    let cumulative = value(input.baslangic_nakdi);
    output.cashFlow = [...input.haftalik_nakit]
      .sort((left, right) => left.hafta.localeCompare(right.hafta))
      .map((row) => {
        const inflow = value(row.tahsilat) + value(row.nakit_satis) + value(row.diger_giris);
        const outflow = value(row.tedarikci) + value(row.personel) + value(row.vergi)
          + value(row.borc_servisi) + value(row.diger_cikis);
        const netCash = inflow - outflow;
        cumulative += netCash;
        return { month: row.hafta, inflow, outflow, netCash, cumulativeCash: cumulative };
      });
  }

  if (input.borc_servisi) {
    const reportDate = new Date(input.rapor_tarihi || new Date().toISOString().slice(0, 10));
    output.debts = input.borc_servisi.map((row, index) => {
      const dueDate = new Date(row.odeme_tarihi);
      const days = Math.ceil((dueDate.getTime() - reportDate.getTime()) / 86_400_000);
      const principal = value(row.anapara);
      return {
        id: `${row.borc_id}-${row.odeme_tarihi}-${index}`,
        creditor: row.alacakli,
        type: `Borç servisi · ${(row.para_birimi || 'TRY').toUpperCase()}`,
        amount: principal,
        interestRate: 0,
        interestAmount: value(row.faiz),
        currency: (row.para_birimi || 'TRY').toUpperCase(),
        dueDate: row.odeme_tarihi,
        status: days <= 30 ? 'critical' : days <= 90 ? 'warning' : 'active',
      };
    });
  }

  if (input.alacak_faturalari) {
    const reportDate = new Date(input.rapor_tarihi || new Date().toISOString().slice(0, 10));
    const customers = new Map<string, { id: string; name: string; open: number; weightedDays: number }>();
    for (const invoice of input.alacak_faturalari) {
      const open = Math.max(0, invoice.tutar - value(invoice.odenen));
      if (!open) continue;
      const overdueDays = Math.max(0, Math.floor((reportDate.getTime() - new Date(invoice.vade_tarihi).getTime()) / 86_400_000));
      const current = customers.get(invoice.musteri_id) || {
        id: invoice.musteri_id,
        name: invoice.musteri_adi,
        open: 0,
        weightedDays: 0,
      };
      current.open += open;
      current.weightedDays += overdueDays * open;
      customers.set(invoice.musteri_id, current);
    }
    const total = [...customers.values()].reduce((sum, customer) => sum + customer.open, 0);
    output.customers = [...customers.values()].map((customer) => {
      const days = customer.open ? Math.round(customer.weightedDays / customer.open) : 0;
      return {
        id: customer.id,
        name: customer.name,
        sharePercentage: total ? Number((customer.open / total * 100).toFixed(2)) : 0,
        receivableAmount: customer.open,
        avgPaymentDays: days,
        riskLevel: days > 90 ? 'kritik' : days > 60 ? 'yüksek' : days > 30 ? 'orta' : 'düşük',
      };
    });
  }

  if (input.butce) {
    const groups = new Map<string, { planned: number; actual: number }>();
    for (const row of input.butce) {
      const label = [row.departman || 'Genel', row.proje || 'Genel', row.kategori].join(' / ');
      const current = groups.get(label) || { planned: 0, actual: 0 };
      current.planned += value(row.butce);
      current.actual += value(row.gerceklesen);
      groups.set(label, current);
    }
    output.budget = [...groups.entries()].map(([category, amounts]) => {
      const variance = amounts.planned - amounts.actual;
      return {
        category,
        planned: amounts.planned,
        actual: amounts.actual,
        variance,
        variancePercent: amounts.planned ? Number((variance / amounts.planned * 100).toFixed(2)) : 0,
      };
    });
  }

  return output;
}

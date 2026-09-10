import React from 'react';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({ arsiv: vi.fn(), indir: vi.fn(), sil: vi.fn(), yeni: vi.fn() }));
vi.mock('../lib/api', () => ({
  raporArsiviniGetir: mocks.arsiv,
  arsivRaporuIndir: mocks.indir,
  arsivRaporuSil: mocks.sil,
  raporIndir: mocks.yeni,
}));
vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    currentUser: { uid: 'user-a' },
    userProfile: { companyId: 'company-a', role: 'admin' },
    isGuest: false,
  }),
}));

import { initialFinancialData } from '../data/mockData';
import { ReportsTab } from './ReportsTab';

const rapor = {
  rapor_id: 'rpt_1', sirket_adi: 'A Şirketi', donem: '2026 Q2', para_birimi: 'TRY',
  surum: '20260911-010101', motor_surumu: '1.0.0', guncel_motor: false,
  ozgun_cikti: true, formatlar: ['pdf'] as const,
  ozet: { revenue: 1_000_000, netProfit: 120_000 }, olusturan: 'user-a',
};

afterEach(cleanup);
beforeEach(() => {
  vi.clearAllMocks();
  mocks.arsiv.mockResolvedValue({ raporlar: [rapor] });
  mocks.indir.mockResolvedValue({
    yenidenUretildi: false, ozgunCikti: true, motorArsiv: '1.0.0', motorGuncel: '2.0.0',
  });
});

it('motor sürümü değişse de özgün arşiv çıktısını yeniden üretilmiş gibi göstermez', async () => {
  render(<ReportsTab data={initialFinancialData} onNavigateDataEntry={vi.fn()} />);

  expect(await screen.findByText('Özgün çıktı')).toBeTruthy();
  expect(screen.queryByText('Farklı motor sürümü')).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'pdf indir' }));

  expect(await screen.findByText(/bütünlüğü doğrulanmış özgün rapor indirildi/)).toBeTruthy();
  expect(screen.queryByText(/özgün rapordan sapabilir/)).toBeNull();
});

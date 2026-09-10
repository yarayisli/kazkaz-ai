import React from 'react';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({ liste: vi.fn(), detay: vi.fn() }));
vi.mock('../lib/api', () => ({
  platformSirketleriniGetir: mocks.liste,
  platformSirketDetayiniGetir: mocks.detay,
  platformBekleyenClaimleriYenidenDene: vi.fn(),
  platformGeriBildirimDurumunuGuncelle: vi.fn(),
  platformSirketEylemi: vi.fn(),
  platformSirketiniGuncelle: vi.fn(),
}));

import { PlatformCompaniesPanel } from './PlatformCompaniesPanel';

const sirket = (id: string, ad: string) => ({
  sirket_id: id, sirket_adi: ad, sektor: 'Yazılım', durum: 'active', plan: 'pro',
  operasyon_sagligi: 'normal', uye_sayisi: 1, bekleyen_davet: 0,
  son_aktivite: null, son_aksiyon: 'workspace.read',
});
const detay = (id: string, ad: string) => ({
  sirket: { sirket_id: id, sirket_adi: ad, durum: 'active', plan: 'pro' },
  kullanim: { aktivite_30_gun: 1, son_aksiyon: 'workspace.read', rapor_arsivleme: 0, rapor_indirme: 0, veri_durumu: 'kayitli', calisma_alani_kayit: 1 },
  uyeler: [{ kullanici_ozeti: `${id}-uye`, eposta_maskeli: `${id}***@ornek.com`, rol: 'admin' }],
  bekleyen_davetler: [], son_olaylar: [], geri_bildirimler: [],
});
const ertelenmis = () => {
  let resolve!: (value: ReturnType<typeof detay>) => void;
  const promise = new Promise<ReturnType<typeof detay>>((tamamla) => { resolve = tamamla; });
  return { promise, resolve };
};

afterEach(cleanup);
beforeEach(() => {
  vi.clearAllMocks();
  mocks.liste.mockResolvedValue({ sirketler: [sirket('a', 'A Şirketi'), sirket('b', 'B Şirketi')] });
});

it('A şirketinin geç ayrıntı yanıtının B şirketini ezmesine izin vermez', async () => {
  const gecA = ertelenmis();
  mocks.detay.mockImplementation((id: string) => id === 'a' ? gecA.promise : Promise.resolve(detay('b', 'B Şirketi')));
  render(<PlatformCompaniesPanel />);

  fireEvent.click(await screen.findByRole('button', { name: /A Şirketi/ }));
  fireEvent.click(screen.getByRole('button', { name: /B Şirketi/ }));
  await screen.findByText('b***@ornek.com');
  await act(async () => { gecA.resolve(detay('a', 'A Şirketi')); });

  expect(screen.getByText('b***@ornek.com')).toBeTruthy();
  expect(screen.queryByText('a***@ornek.com')).toBeNull();
});

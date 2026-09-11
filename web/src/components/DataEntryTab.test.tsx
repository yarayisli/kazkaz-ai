import React from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { initialFinancialData } from '../data/mockData';

const mocks = vi.hoisted(() => ({
  dosyaDogrula: vi.fn(),
  denetim: vi.fn(),
  iceAktar: vi.fn(),
}));

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    currentUser: { uid: 'u1' },
    userProfile: { companyId: 'c1', role: 'admin' },
    isGuest: false,
  }),
}));
vi.mock('../lib/api', () => ({
  finansDosyasiDogrula: mocks.dosyaDogrula,
  finansalDenetim: mocks.denetim,
  importedFinancialData: mocks.iceAktar,
  veriSablonuIndir: vi.fn(),
  googleSheetsDogrula: vi.fn(),
  googleSheetsDurumu: vi.fn(),
  tarihselKurlariGetir: vi.fn(),
}));

import { DataEntryTab } from './DataEntryTab';

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

it('kesin veri hatası olan dosyanın çalışma alanına aktarılmasını engeller', async () => {
  mocks.dosyaDogrula.mockResolvedValue({
    durum: 'uyarili',
    dosya: { ad: 'bozuk.csv', tur: 'csv', boyut: 100, sayfalar: ['CSV'] },
    ozet: {
      gecerli_satirlar: 1, uyarili_satirlar: 0, reddedilen_satirlar: 1,
      toplam_gelir: 1000, toplam_gider: 0, islem_satirlari: 1,
    },
    finansal_veri: {},
    veri_kalitesi: {
      kaynak: 'islem_ozeti', bilanco_mevcut: false, favok_hesaplanabilir: false,
      eksikler: [], tutarlilik_bulgulari: [], anomali_bulgulari: [],
      semantik_durum: 'temiz', semantik_hata_sayisi: 0, semantik_uyari_sayisi: 0,
      aktarim_bloke: true,
      bloke_nedenleri: ['1 satır doğrulamadan geçmedi; eksik veriyle analiz yapılmamalı.'],
    },
    gelismis_veri: {}, zaman_serisi: [], analizler: {}, onizleme: [],
    hatalar: [{ sayfa: 'CSV', satir: 3, alan: 'kategori', kod: 'ara_toplam_reddedildi', mesaj: 'Ara toplam reddedildi.', seviye: 'hata' }],
    metodoloji: {},
  });
  const onImport = vi.fn();
  const { container } = render(
    <DataEntryTab initialData={initialFinancialData} onSave={vi.fn()} onImport={onImport} />,
  );

  const input = container.querySelector('input[type="file"]') as HTMLInputElement;
  fireEvent.change(input, { target: { files: [new File(['x'], 'bozuk.csv', { type: 'text/csv' })] } });

  const dugme = await screen.findByRole('button', { name: 'Önce veri hatalarını düzeltin' });
  expect((dugme as HTMLButtonElement).disabled).toBe(true);
  expect(screen.getByText('Çalışma alanına aktarım durduruldu')).toBeTruthy();
  expect(onImport).not.toHaveBeenCalled();
  expect(mocks.denetim).not.toHaveBeenCalled();
});

it('risk uyarıları kullanıcı tarafından görülmeden aktarım başlatmaz', async () => {
  mocks.dosyaDogrula.mockResolvedValue({
    durum: 'uyarili',
    dosya: { ad: 'kontrol.csv', tur: 'csv', boyut: 100, sayfalar: ['CSV'] },
    ozet: {
      gecerli_satirlar: 1, uyarili_satirlar: 1, reddedilen_satirlar: 0,
      toplam_gelir: 1000, toplam_gider: 0, islem_satirlari: 1,
    },
    finansal_veri: {},
    veri_kalitesi: {
      kaynak: 'islem_ozeti', bilanco_mevcut: false, favok_hesaplanabilir: false,
      eksikler: [], tutarlilik_bulgulari: [], anomali_bulgulari: [],
      semantik_durum: 'temiz', semantik_hata_sayisi: 0, semantik_uyari_sayisi: 0,
      aktarim_bloke: false, bloke_nedenleri: [],
    },
    gelismis_veri: {}, zaman_serisi: [], analizler: {}, onizleme: [],
    hatalar: [{ sayfa: 'CSV', satir: 1, alan: 'kdv_durumu', kod: 'kdv_durumu_belirsiz', mesaj: 'KDV bazı belirtilmedi.', seviye: 'uyari' }],
    metodoloji: {},
  });
  mocks.iceAktar.mockReturnValue(initialFinancialData);
  mocks.denetim.mockResolvedValue({});
  const onImport = vi.fn();
  const { container } = render(
    <DataEntryTab initialData={initialFinancialData} onSave={vi.fn()} onImport={onImport} />,
  );

  fireEvent.change(container.querySelector('input[type="file"]') as HTMLInputElement, {
    target: { files: [new File(['x'], 'kontrol.csv', { type: 'text/csv' })] },
  });
  const bekleyen = await screen.findByRole('button', { name: 'Uyarıları inceleyip onaylayın' });
  expect((bekleyen as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(screen.getByRole('checkbox'));
  fireEvent.click(screen.getByRole('button', { name: 'Doğrulanan veriyi çalışma alanına aktar' }));
  await waitFor(() => expect(onImport).toHaveBeenCalledTimes(1));
});

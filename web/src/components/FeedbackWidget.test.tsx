import React from 'react';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({ gonder: vi.fn(), talepler: vi.fn(), memnuniyet: vi.fn(), pilotDurum: vi.fn(), pilotKaydet: vi.fn() }));
vi.mock('../lib/api', () => ({
  geriBildirimGonder: mocks.gonder,
  destekTaleplerim: mocks.talepler,
  destekTalebiMemnuniyeti: mocks.memnuniyet,
  pilotNiyetDurumu: mocks.pilotDurum,
  pilotNiyetKaydet: mocks.pilotKaydet,
}));

import { FeedbackWidget } from './FeedbackWidget';

afterEach(cleanup);
beforeEach(() => {
  vi.resetAllMocks();
  mocks.gonder.mockResolvedValue({ durum: 'alindi', kayit_id: 'fb1', talep_no: 'T-ABC123' });
  mocks.talepler.mockResolvedValue({
    talepler: [{
      geri_bildirim_id: 'fb1', talep_no: 'T-ABC123', kategori: 'hata', sayfa: 'overview',
      mesaj: 'Rapor indirme sırasında sorun yaşadım.', durum: 'resolved',
      yanit: 'Rapor bağlantısı yenilendi.', olusturma: '2026-09-11T00:00:00Z',
      guncelleme: '2026-09-11T01:00:00Z', memnun: null,
    }],
  });
  mocks.memnuniyet.mockResolvedValue({ durum: 'kaydedildi', talep_no: 'T-ABC123', memnun: true, talep_durumu: 'resolved' });
  mocks.pilotDurum.mockResolvedValue({ uygun: true, yanitlandi: false, asgari_gun: 21 });
  mocks.pilotKaydet.mockResolvedValue({ durum: 'kaydedildi' });
});

it('pilot şirket yöneticisinin ücretli devam niyetini kaydeder', async () => {
  render(<FeedbackWidget activePage="overview" />);
  fireEvent.click(screen.getByRole('button', { name: 'Destek' }));
  fireEvent.click(screen.getByRole('tab', { name: 'Pilot' }));
  await screen.findByText(/pilot sonrasında kullanmaya devam/);
  fireEvent.change(screen.getByLabelText('Devam niyeti'), { target: { value: 'kesinlikle' } });
  fireEvent.change(screen.getByLabelText('Ücretli devam niyeti'), { target: { value: 'evet' } });
  fireEvent.click(screen.getByRole('button', { name: 'Değerlendirmeyi kaydet' }));
  await waitFor(() => expect(mocks.pilotKaydet).toHaveBeenCalledWith('kesinlikle', true));
  expect(await screen.findByText(/Pilot değerlendirmeniz kaydedildi/)).toBeTruthy();
});

it('talep numarasını, çözüm yanıtını ve müşteri memnuniyetini uçtan uca gösterir', async () => {
  render(<FeedbackWidget activePage="overview" />);
  fireEvent.click(screen.getByRole('button', { name: 'Destek' }));
  fireEvent.change(screen.getByPlaceholderText('Ne oldu, hangi sonucu bekliyordunuz?'), {
    target: { value: 'Rapor indirme sırasında sorun yaşadım.' },
  });
  fireEvent.click(screen.getByRole('button', { name: 'Gönder' }));
  await screen.findByText(/Talep no:/);
  expect(screen.getByText('T-ABC123')).toBeTruthy();

  fireEvent.click(screen.getByRole('tab', { name: 'Taleplerim' }));
  await screen.findByText('Rapor bağlantısı yenilendi.');
  fireEvent.click(screen.getByRole('button', { name: 'Memnunum' }));

  await waitFor(() => expect(mocks.memnuniyet).toHaveBeenCalledWith('fb1', true));
  expect(await screen.findByText('Memnuniyetiniz kaydedildi.')).toBeTruthy();
});

it('talep yükleme hatasını boş liste gibi göstermez ve yeniden dener', async () => {
  mocks.talepler.mockRejectedValueOnce(new Error('ağ yok')).mockResolvedValueOnce({ talepler: [] });
  render(<FeedbackWidget activePage="overview" />);
  fireEvent.click(screen.getByRole('button', { name: 'Destek' }));
  fireEvent.click(screen.getByRole('tab', { name: 'Taleplerim' }));

  expect(await screen.findByText(/Talepleriniz şu anda yüklenemedi/)).toBeTruthy();
  expect(screen.queryByText('Henüz açtığınız bir talep yok.')).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: 'Yeniden dene' }));

  expect(await screen.findByText('Henüz açtığınız bir talep yok.')).toBeTruthy();
  expect(mocks.talepler).toHaveBeenCalledTimes(2);
});

it('memnuniyet kaydı başarısız olduğunda kullanıcıya yeniden deneme mesajı verir', async () => {
  mocks.memnuniyet.mockRejectedValueOnce(new Error('ağ yok'));
  render(<FeedbackWidget activePage="overview" />);
  fireEvent.click(screen.getByRole('button', { name: 'Destek' }));
  fireEvent.click(screen.getByRole('tab', { name: 'Taleplerim' }));
  await screen.findByText('Rapor bağlantısı yenilendi.');
  fireEvent.click(screen.getByRole('button', { name: 'Memnunum' }));

  expect(await screen.findByText(/Yanıtınız kaydedilemedi/)).toBeTruthy();
  expect(screen.getByRole('button', { name: 'Memnunum' })).toBeTruthy();
});

it('çözülmedi yanıtından sonra talebi yeniden inceleniyor gösterir', async () => {
  mocks.memnuniyet.mockResolvedValueOnce({ durum: 'yeniden_acildi', talep_no: 'T-ABC123', memnun: false, talep_durumu: 'in_review' });
  render(<FeedbackWidget activePage="overview" />);
  fireEvent.click(screen.getByRole('button', { name: 'Destek' }));
  fireEvent.click(screen.getByRole('tab', { name: 'Taleplerim' }));
  await screen.findByText('Rapor bağlantısı yenilendi.');
  fireEvent.click(screen.getByRole('button', { name: 'Çözülmedi' }));

  expect(await screen.findByText('Talebiniz yeniden incelemeye alındı.')).toBeTruthy();
  expect(screen.getByText('İnceleniyor')).toBeTruthy();
});

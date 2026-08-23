import { expect, test } from '@playwright/test';

test.describe('KazKaz tanıtım sayfası', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/public/performance', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ durum: 'yetersiz_veri', mesaj: 'E2E testi: yayınlanabilir üretim örneği yok.' }),
      });
    });
    await page.route('**/api/v1/platform-admin/erisim', async (route) => {
      await route.fulfill({ status: 403, contentType: 'application/json', body: JSON.stringify({ detail: 'Yetkisiz' }) });
    });
    await page.goto('/');
  });

  test('ana değer önerisini ve çalışan ürün kanıtını gösterir', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /Rakamları değil/i })).toBeVisible();
    await expect(page.getByText('Finansal karar merkezi', { exact: true })).toBeVisible();
    await expect(page.getByText('Hesaplama AI’dan bağımsız', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: /Ücretsiz finansal görünüm oluştur/i })).toBeVisible();
  });

  test('örnek karar sekmeleri gerçek durum değiştirir', async ({ page }) => {
    const riskTab = page.getByRole('tab', { name: 'Risk' });
    await riskTab.click();
    await expect(riskTab).toHaveAttribute('aria-selected', 'true');
    await expect(page.getByText('Alacak, borç ve bütçe sinyallerini tek karar sırasına alın.')).toBeVisible();
  });

  test('sayfada yatay taşma ve erişilebilir adı olmayan ana buton bulunmaz', async ({ page }) => {
    const layout = await page.evaluate(() => ({
      viewport: document.documentElement.clientWidth,
      content: document.documentElement.scrollWidth,
    }));

    expect(layout.content).toBeLessThanOrEqual(layout.viewport + 1);

    const unnamedButtons = await page.locator('button').evaluateAll((buttons) =>
      buttons.filter((button) => {
        const text = button.textContent?.trim();
        const ariaLabel = button.getAttribute('aria-label');
        return !text && !ariaLabel;
      }).length,
    );
    expect(unnamedButtons).toBe(0);
  });
});

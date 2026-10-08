import { test, expect } from '@playwright/test';

test.describe('ResearchMatch E2E User Journeys', () => {
  test('Home page renders search form and executes query', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // Check title & branding
    await expect(page.locator('h1')).toContainText('Match Your Proposed Research');

    // Fill search form
    await page.fill('input[placeholder*="Fine-Tuning Large Language Models"]', 'Transformer Neural Network Personalization');
    
    // Submit search
    await page.click('button:has-text("Discover Papers")');

    // Verify search page navigation
    await expect(page).toHaveURL(/.*search\?q=Transformer/);
  });

  test('Subject browser displays taxonomy domains', async ({ page }) => {
    await page.goto('http://localhost:3000/subjects');
    await expect(page.locator('h1')).toContainText('Subject & Domain Browser');
  });
});

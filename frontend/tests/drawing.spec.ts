import { expect, test, type Page } from '@playwright/test'

const bounds = async (page: Page) => Promise.all(
  ['west', 'south', 'east', 'north'].map(name => page.getByRole('spinbutton', { name, exact: true }).inputValue()),
)

async function draw(page: Page, reverse = false) {
  await page.getByRole('button', { name: 'Draw rectangle', exact: true }).click()
  const box = (await page.locator('.maplibregl-canvas').boundingBox())!
  const first = { x: box.x + box.width * 0.3, y: box.y + box.height * 0.3 }
  const last = { x: box.x + box.width * 0.65, y: box.y + box.height * 0.65 }
  await page.mouse.move(reverse ? last.x : first.x, reverse ? last.y : first.y)
  await page.mouse.down()
  await page.mouse.move(reverse ? first.x : last.x, reverse ? first.y : last.y, { steps: 8 })
  return { first, last, box }
}

test.beforeEach(async ({ page }) => {
  // Keep WebGL and real map events, but avoid depending on external tile availability.
  await page.route(/https:\/\/(tile.openstreetmap.org|services.arcgisonline.com)\/.*/, route => route.fulfill({
    contentType: 'image/png',
    body: Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGNwTQ0AAAHtAPuRIrfOAAAAAElFTkSuQmCC', 'base64'),
  }))
  await page.goto('/#/dashboard')
  await expect(page.getByRole('button', { name: 'Draw rectangle', exact: true })).toBeEnabled({ timeout: 15000 })
})

test('drawn coordinates pass form validation and reach the location API', async ({ page }) => {
  const initial = await bounds(page)
  await draw(page, true)
  await expect(page.getByTestId('draw-preview')).toBeVisible()
  const preview = await page.getByTestId('draw-preview').locator('polygon').getAttribute('points')
  expect(new Set(preview!.split(' ')).size).toBe(4)
  await page.mouse.up()
  await expect(page.getByTestId('draw-preview')).toHaveCount(0)
  const selected = await bounds(page)
  expect(selected).not.toEqual(initial)
  const [west, south, east, north] = selected.map(Number)
  expect(west).toBeLessThan(east)
  expect(south).toBeLessThan(north)
  expect(await page.locator('form').evaluate(form => (form as HTMLFormElement).checkValidity())).toBe(true)
  await page.route('**/api/v1/requests/plan', route => route.fulfill({ json: {
    workflow: 'vegetation_change', sector: 'agriculture', confidence: 'high',
    required_bands: ['B04', 'B08'], rationale: 'Browser test fixture', claim_limitations: [],
  } }))
  await page.route('**/api/v1/locations', route => route.fulfill({ status: 503, json: { detail: 'Test stopped after receiving location' } }))
  const request = page.waitForRequest('**/api/v1/locations')
  await page.getByRole('button', { name: 'Plan and run request' }).click()
  expect((await request).postDataJSON().aoi).toEqual({ type: 'Polygon', coordinates: [
    [[west, south], [east, south], [east, north], [west, north], [west, south]],
  ] })
  await expect(page.getByRole('alert')).toHaveText('Test stopped after receiving location')
})

test('Escape preserves the selection and drawing can restart', async ({ page }) => {
  const initial = await bounds(page)
  await draw(page)
  await page.keyboard.press('Escape')
  await page.mouse.up()
  expect(await bounds(page)).toEqual(initial)
  await draw(page)
  await page.mouse.up()
  expect(await bounds(page)).not.toEqual(initial)
})

test('release outside map completes, while a click preserves the area', async ({ page }) => {
  const initial = await bounds(page)
  const { box } = await draw(page)
  await page.mouse.move(box.x - 20, box.y + box.height * 0.7)
  await page.mouse.up()
  await expect(page.getByRole('button', { name: 'Draw rectangle', exact: true })).toBeVisible()
  const selected = await bounds(page)
  expect(selected).not.toEqual(initial)
  await page.getByRole('button', { name: 'Draw rectangle', exact: true }).click()
  await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2)
  expect(await bounds(page)).toEqual(selected)
})

test('touch drag selects a rectangle', async ({ page, context }) => {
  const initial = await bounds(page)
  await page.getByRole('button', { name: 'Draw rectangle', exact: true }).click()
  const box = (await page.locator('.maplibregl-canvas').boundingBox())!
  const session = await context.newCDPSession(page)
  await session.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: box.x + 150, y: box.y + 180 }] })
  await session.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: box.x + 300, y: box.y + 330 }] })
  await session.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] })
  await expect.poll(() => bounds(page)).not.toEqual(initial)
  await expect(page.getByRole('button', { name: 'Draw rectangle', exact: true })).toBeVisible()
})

test('coordinates refresh under a stationary pointer when zoom changes', async ({ page }) => {
  const canvas = page.locator('.maplibregl-canvas')
  await canvas.focus()
  const box = (await canvas.boundingBox())!
  await page.mouse.move(box.x + box.width * 0.7, box.y + box.height * 0.35)
  const tooltip = page.locator('.map-coordinate-tooltip')
  await expect(tooltip).toBeVisible()
  const before = (await tooltip.textContent())!
  const decimals = (text: string) => text.split('°')[0].split('.')[1]?.length ?? 0
  for (let step = 0; step < 5; step++) {
    await page.keyboard.press('-')
    await page.waitForTimeout(350) // MapLibre keyboard zoom animation.
  }
  await expect(tooltip).not.toHaveText(before)
  await expect.poll(async () => decimals((await tooltip.textContent())!)).toBeLessThan(decimals(before))
})

test('landing opens the dashboard and both purchase screens return inspectable demo reports', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /Before you invest/ })).toBeVisible()
  await page.screenshot({ path: 'test-results/landing.png', fullPage: true })
  await page.getByRole('link', { name: 'Open dashboard' }).click()
  await expect(page.getByRole('heading', { name: 'Start with the ground truth.' })).toBeVisible()
  await page.getByRole('button', { name: 'Land purchase', exact: false }).click()
  await page.getByRole('button', { name: 'Plan and run request' }).click()
  await expect(page.getByRole('heading', { name: 'Agricultural purchase context' })).toBeVisible()
  await expect(page.locator('.map-tile-error')).toHaveCount(0)
  await expect(page.locator('.assessment-conclusion')).toContainText('simulated pixels cannot assess')
  await expect(page.locator('.check-grid')).toContainText('Soil')
  await expect(page.locator('.agriculture-details')).toContainText('576 mutually valid pixels')
  await expect(page.getByRole('heading', { name: 'What changed on the selected land' })).toBeVisible()
  await expect(page.locator('.evidence-viewer img')).toHaveCount(4)
  await expect.poll(() => page.locator('.evidence-viewer img').evaluateAll(images => images.every(image => (image as HTMLImageElement).naturalWidth > 0))).toBe(true)
  await page.screenshot({ path: 'test-results/dashboard.png', fullPage: true })
  await page.getByRole('button', { name: 'Commercial site' }).click()
  await expect(page.locator('.assessment-report')).toHaveCount(0)
  await page.getByRole('button', { name: 'Plan and run request' }).click()
  await expect(page.getByRole('heading', { name: 'Development purchase context' })).toBeVisible()
  await expect(page.locator('.check-grid')).toContainText('Permitted use')
  await expect(page.locator('.artifact-legend')).toContainText('Vegetation-to-bare')
  await expect(page.locator('.buyer-evidence-summary')).toContainText('BUILT-UP-LIKE CHANGE')
  await expect(page.locator('.observation-review')).toContainText('Why these dates were used')
  await expect(page.locator('.observation-review')).toContainText('INTERMEDIATE CHECKS')
  await expect(page.locator('.interpretation-brief')).toContainText('PLAIN-LANGUAGE ANSWER')
  await expect(page.locator('.interpretation-brief')).toContainText('Why the evidence supports this')
  await expect(page.locator('.interpretation-brief')).toContainText('What this may mean for the decision')
  await expect(page.locator('.temporal-summary')).toContainText('REPEATED ACROSS DATES')
  await expect(page.locator('.temporal-summary')).toContainText('LATEST COMPARISON ONLY')
  await expect(page.locator('.observable-effects')).toContainText('What changed, and what it affects')
  await expect(page.locator('.interpretation-brief')).toContainText('Recommended next verification')
  await expect(page.getByRole('button', { name: /Inspect region 2/ })).toBeVisible()
  await page.getByRole('button', { name: /Inspect region 2/ }).click()
  await expect(page.locator('.region-inspector')).toContainText('Built-up-like change')
  await expect(page.getByRole('heading', { name: 'Recent locations' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Print / save PDF' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Check for newer imagery' })).toBeVisible()
  await expect(page.getByText(/Market-price evidence/)).toBeVisible()
  await page.screenshot({ path: 'test-results/development-dashboard.png', fullPage: true })
})

test('mobile dashboard keeps the map and draw preview visible', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.reload()
  await expect(page.getByRole('button', { name: 'Draw rectangle', exact: true })).toBeEnabled({ timeout: 15000 })
  await draw(page)
  await expect(page.getByTestId('draw-preview')).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390)
  await page.screenshot({ path: 'test-results/mobile-drawing.png', fullPage: true })
  await page.mouse.up()
})

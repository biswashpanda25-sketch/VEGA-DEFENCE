/**
 * GOTHAM INDIA — browser smoke test (Playwright, headless Chromium).
 *
 * Verifies the real application end to end against the running stack:
 *   sign-in → overview renders live figures → navigation across every section →
 *   graph interaction → assistant grounded answer → sign-out.
 *
 * Usage:  node e2e/smoke.mjs [baseURL]
 * Default baseURL: http://127.0.0.1:5173
 */
import { chromium } from 'playwright'
import { mkdirSync } from 'node:fs'

const BASE = process.argv[2] ?? 'http://127.0.0.1:5173'
const SHOTS = 'e2e/screenshots'
mkdirSync(SHOTS, { recursive: true })

const results = []
const errors = []

function check(name, ok, detail = '') {
  results.push({ name, ok, detail })
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? ` — ${detail}` : ''}`)
}

const browser = await chromium.launch({ args: ['--no-sandbox'] })
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1 })

// Expected authorisation refusals (403/401) are part of the product: role-restricted panels
// surface an explanatory banner. They are not defects; genuine JS errors are.
const EXPECTED = /Failed to load resource: the server responded with a status of (401|403)\b/
const failures = []
page.on('console', (m) => { if (m.type() === 'error' && !EXPECTED.test(m.text())) errors.push(m.text()) })
page.on('pageerror', (e) => errors.push(String(e)))
page.on('response', (r) => { if (r.status() >= 400) failures.push(`${r.status()} ${r.url()}`) })

try {
  // ---- sign in ----
  await page.goto(BASE, { waitUntil: 'networkidle' })
  await page.screenshot({ path: `${SHOTS}/01-login.png` })
  check('login screen renders', await page.locator('text=Authorized access').isVisible())

  await page.fill('#email', 'analyst@gotham-demo.in')
  await page.fill('#password', 'Gotham@2026')
  await page.click('button:has-text("Sign in")')
  await page.waitForSelector('.shell', { timeout: 20000 })
  check('authenticated shell loads', await page.locator('.topbar').isVisible())

  // ---- overview ----
  await page.waitForSelector('text=Operational Overview')
  const entityKpi = await page.locator('.kpi-value').first().innerText()
  check('overview renders live entity count', /^\d+$/.test(entityKpi.trim()), `value=${entityKpi.trim()}`)
  await page.waitForTimeout(1200)
  await page.screenshot({ path: `${SHOTS}/02-overview.png`, fullPage: false })

  // ---- navigation across every section ----
  const sections = [
    ['Universal Search', 'search'],
    ['Knowledge Graph', 'graph'],
    ['Analytical Workspaces', 'workspaces'],
    ['Cases', 'cases'],
    ['Geospatial Explorer', 'geo'],
    ['Data Sources', 'sources'],
    ['Data Catalog', 'catalog'],
    ['Operational Intelligence', 'operations'],
    ['AI Assistant', 'assistant'],
    ['Reports', 'reports'],
    ['Notifications', 'notifications'],
    ['Administration', 'admin'],
    ['Governance', 'governance'],
    ['Security & Audit', 'audit'],
  ]
  for (const [label, slug] of sections) {
    await page.click(`.nav-item:has-text("${label}")`)
    await page.waitForTimeout(900)
    const heading = (await page.locator('.page-title').innerText()).toLowerCase()
    const expected = { assistant: 'ai analytical assistant' }[slug] ?? label.toLowerCase()
    check(`section ${slug} renders`, heading.includes(expected.slice(0, 14)), `heading="${heading}"`)
    if (slug === 'graph' || slug === 'geo' || slug === 'assistant') {
      await page.screenshot({ path: `${SHOTS}/03-${slug}.png` })
    }
  }

  // ---- knowledge graph interaction ----
  await page.click('.nav-item:has-text("Knowledge Graph")')
  await page.waitForTimeout(1400)
  const nodeCount = await page.locator('svg circle').count()
  check('graph draws nodes', nodeCount > 10, `${nodeCount} circles`)
  const nodes = page.locator('svg g[transform] > circle')
  if (await nodes.count() > 0) {
    await nodes.nth(2).click({ force: true })
    await page.waitForTimeout(900)
    const panelVisible = await page.locator('.panel-right').isVisible().catch(() => false)
    check('graph node opens evidence panel', panelVisible)
    await page.screenshot({ path: `${SHOTS}/04-graph-evidence.png` })
    if (panelVisible) await page.locator('.panel-right button:has-text("Close")').click()
  }

  // ---- geospatial map ----
  await page.click('.nav-item:has-text("Geospatial Explorer")')
  await page.waitForTimeout(2000)
  const canvasCount = await page.locator('.map-shell canvas').count()
  check('maplibre canvas initialised', canvasCount > 0, `${canvasCount} canvas`)
  const featureBadge = await page.locator('.badge:has-text("features")').first().innerText().catch(() => '')
  check('map reports features', /\d+\s+features/.test(featureBadge), featureBadge)

  // ---- AI assistant grounded answer ----
  await page.click('.nav-item:has-text("AI Assistant")')
  await page.waitForTimeout(700)
  await page.fill('input[placeholder="Ask about authorized records…"]', 'Summarise the condition of Bridge Mahanadi-03')
  await page.click('button:has-text("Ask")')
  await page.waitForSelector('.assistant-msg', { timeout: 25000 })
  const answerText = await page.locator('.assistant-msg').first().innerText()
  const cites = await page.locator('.assistant-msg .cite').count()
  check('assistant returns citations', cites > 0, `${cites} citations`)
  check('assistant answer names the cited record', /Mahanadi/.test(answerText))
  await page.screenshot({ path: `${SHOTS}/05-assistant.png` })

  // ---- search ----
  await page.click('.nav-item:has-text("Universal Search")')
  await page.fill('.content .searchbox input', 'embankment relief')
  await page.click('button:has-text("Search")')
  await page.waitForTimeout(1200)
  const hitCount = await page.locator('.card-b > div[style*="border-bottom"]').count()
  check('search returns ranked hits', hitCount > 0, `${hitCount} hits`)

  // ---- sign out ----
  await page.click('.topbar button:has-text("Analyst")')
  await page.click('button:has-text("Sign out")')
  await page.waitForSelector('text=Authorized access', { timeout: 10000 })
  check('sign-out returns to login', true)

  check('no uncaught browser errors', errors.length === 0, errors.slice(0, 3).join(' | '))
  const unexpected = failures.filter((f) => !/^(401|403) /.test(f))
  check('no unexpected failed requests', unexpected.length === 0, unexpected.slice(0, 3).join(' | '))
  console.log(`
HTTP responses >=400 (expected authorisation refusals included): ${failures.length}`)
  for (const f of failures.slice(0, 8)) console.log(`  · ${f}`)
} catch (e) {
  check('smoke run completed', false, String(e).slice(0, 300))
} finally {
  await browser.close()
}

const failed = results.filter((r) => !r.ok)
console.log(`\n${results.length - failed.length}/${results.length} checks passed`)
process.exit(failed.length === 0 ? 0 : 1)

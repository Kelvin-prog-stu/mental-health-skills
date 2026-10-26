// Drives the running app (frontend :5180, backend :8100) in headless Chrome and saves
// screenshots plus a JSON log of what was observed. Uses the MOCK model unless --live.
// Usage: node docs/evidence/e2e_check.mjs <outDir> [--live] [--only=name,name]
import { spawn } from 'node:child_process'
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
const PORT = 9411
const APP = 'http://localhost:5180/'
const outDir = process.argv[2]
const live = process.argv.includes('--live')
const only = (process.argv.find((a) => a.startsWith('--only=')) || '').slice(7).split(',').filter(Boolean)
mkdirSync(outDir, { recursive: true })
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const log = []
const note = (step, data) => { log.push({ step, at: new Date().toISOString(), ...data }); console.log(step, JSON.stringify(data)) }

const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), 'b60-'))}`, '--window-size=900,1000', 'about:blank'], { stdio: 'ignore' })
let wsUrl
for (let i = 0; i < 50 && !wsUrl; i++) {
  try { wsUrl = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === 'page')?.webSocketDebuggerUrl } catch {}
  if (!wsUrl) await sleep(200)
}
const ws = new WebSocket(wsUrl)
await new Promise((r) => ws.addEventListener('open', r))
let id = 0
const pending = new Map()
ws.addEventListener('message', (e) => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id) } })
const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pending.set(i, (m) => (m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result))); ws.send(JSON.stringify({ id: i, method, params })) })
const js = async (expression) => { const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }); if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description); return r.result.value }
const shot = async (name) => { const { data } = await send('Page.captureScreenshot', { format: 'png' }); writeFileSync(join(outDir, `${name}.png`), Buffer.from(data, 'base64')) }
const size = (w, h) => send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile: w < 600 })
const key = async (k, code, vk) => { await send('Input.dispatchKeyEvent', { type: 'keyDown', key: k, code, windowsVirtualKeyCode: vk, ...(k === 'Enter' ? { text: String.fromCharCode(13) } : {}) }); await send('Input.dispatchKeyEvent', { type: 'keyUp', key: k, code, windowsVirtualKeyCode: vk }) }
const click = (selectorOrText) => js(`(() => { const t = ${JSON.stringify(selectorOrText)}; const el = document.querySelector(t) || [...document.querySelectorAll('button')].find(b => b.textContent.trim().startsWith(t)); if (!el) throw new Error('no element ' + t); el.click(); return true })()`)
const text = (sel) => js(`document.querySelector(${JSON.stringify(sel)})?.innerText ?? null`)
const waitFor = async (expr, ms = 120000) => { const end = Date.now() + ms; while (Date.now() < end) { if (await js(expr)) return true; await sleep(100) } throw new Error('timeout waiting for ' + expr) }

await send('Page.enable')
await size(900, 1000)
async function load(mode) {
  await send('Page.navigate', { url: APP })
  await sleep(800)
  await js(`localStorage.setItem('breathe60-model-mode', ${JSON.stringify(mode)}); true`)
  await send('Page.navigate', { url: APP })
  await waitFor(`!!document.querySelector('.start') && !document.querySelector('.intro')?.innerText.startsWith('...')`, 30000)
}
const want = (name) => !only.length || only.includes(name)
const mode = live ? 'live' : 'mock'

if (want('complete')) {
  await load(mode)
  note('home', { intro: await text('.intro'), focused: await js('document.activeElement?.className') })
  await shot('01-home')
  const t0 = await js('performance.now()')
  await key('Enter', 'Enter', 13) // Start is focused, so Enter starts
  await waitFor(`!!document.querySelector('.exercise')`)
  await sleep(2500)
  note('exercise-in', { phase: await text('.phase'), counter: await text('.counter'), stopFocused: await js(`document.activeElement?.className === 'stop'`) })
  await shot('02-exercise-inhale')
  await sleep(3000)
  note('exercise-out', { phase: await text('.phase') })
  await waitFor(`!!document.querySelector('.end h1')`, 90000)
  const t1 = await js('performance.now()')
  note('complete', { heading: await text('.end h1'), measured: await text('.end .small'), wallSecondsSeenByCheck: ((t1 - t0) / 1000).toFixed(2) })
  await shot('03-done')
  await click('Not sure')
  await sleep(600)
  note('feedback', { status: await text('[role=status]') })
}

if (want('support-stop')) {
  await load(mode)
  await click('Change')
  await js(`[...document.querySelectorAll('input[value=text]')][0].click(); true`)
  await click('.start')
  await sleep(11500) // into breath 2
  await click('.support')
  await sleep(300)
  note('support-open', { counter: await text('.counter'), panel: await text('.panel h2'), focusOnPanel: await js(`document.activeElement?.id === 'support-title'`) })
  await shot('04-support-paused')
  const before = await text('.counter')
  await sleep(4000)
  note('paused-held', { before, after: await text('.counter'), progress: await js(`document.querySelector('.progress').getAttribute('aria-valuenow')`) })
  await click('Resume')
  await sleep(10000)
  await shot('05-text-cue')
  await click('.stop')
  await waitFor(`!!document.querySelector('.end h1')`)
  note('stopped', { heading: await text('.end h1'), measured: await text('.end .small') })
  await shot('06-stopped')
}

if (want('model-fail')) {
  await load('fail')
  note('model-fail-home', { intro: await text('.intro'), supportVisible: await js(`!!document.querySelector('.support')`) })
  await shot('07-model-fail-home')
  await click('.support')
  await sleep(300)
  note('support-with-model-down', { entries: await js(`[...document.querySelectorAll('.panel li strong')].map(e => e.innerText)`) })
  await click('Close')
}

if (want('history')) {
  await load(mode)
  await click('History')
  await waitFor(`!!document.querySelector('table') || !!document.querySelector('.problem')`)
  note('history', { rows: await js(`[...document.querySelectorAll('tbody tr')].slice(0, 3).map(r => r.innerText.replace(/\\t/g, ' | '))`) })
  await shot('08-history')
  const askQ = async (q) => {
    await js(`(() => { const i = document.querySelector('#ask-input'); Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(i, ${JSON.stringify(q)}); i.dispatchEvent(new Event('input', { bubbles: true })); return true })()`)
    await click('.ask button')
    await waitFor(`!!document.querySelector('.reply') || !!document.querySelector('.problem')`, 60000)
    await sleep(400)
    return { reply: await text('.reply p'), klass: await js(`document.querySelector('.reply')?.className`), supportOpen: await js(`!!document.querySelector('.panel')`) }
  }
  note('ask-sessions', await askQ('How many sessions did I finish, and when was the last one?'))
  await shot('09-ask-answered')
  note('ask-crisis', await askQ('I want to end my life'))
  await shot('10-crisis-input')
  await js(`document.querySelector('.panel button')?.click(); true`)
  if (!live) note('ask-write', await askQ('delete all my sessions'))
}

if (want('narrow')) {
  await size(375, 740)
  await load(mode)
  await click('.start')
  await sleep(3000)
  note('narrow', { stopVisible: await js(`(() => { const r = document.querySelector('.stop').getBoundingClientRect(); return r.bottom <= innerHeight && r.top >= 0 })()`), supportVisible: await js(`(() => { const r = document.querySelector('.support').getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight })()`) })
  await shot('11-narrow-exercise')
  await click('.stop')
  await size(900, 1000)
}

writeFileSync(join(outDir, 'e2e-log.json'), JSON.stringify({ mode: live ? 'LIVE model' : 'MOCK model', log }, null, 2))
ws.close(); chrome.kill(); process.exit(0)

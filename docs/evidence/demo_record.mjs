// Records a captioned demo of the running app. Based on e2e_check.mjs, which drives the running app (frontend :5180, backend :8100) in headless Chrome and saves
// screenshots plus a JSON log of what was observed. Uses the MOCK model unless --live.
// Usage: node docs/evidence/e2e_check.mjs <outDir> [--live] [--only=name,name]
import { spawn } from 'node:child_process'
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
const PORT = 9412
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


// ---- Recording: screencast frames are saved with their timestamps, then joined by ffmpeg ----
const frameDir = join(outDir, 'frames')
mkdirSync(frameDir, { recursive: true })
const frames = []
ws.addEventListener('message', (e) => {
  const m = JSON.parse(e.data)
  if (m.method !== 'Page.screencastFrame') return
  const file = join(frameDir, `f${String(frames.length).padStart(5, '0')}.jpg`)
  writeFileSync(file, Buffer.from(m.params.data, 'base64'))
  frames.push({ file, t: m.params.metadata.timestamp })
  send('Page.screencastFrameAck', { sessionId: m.params.sessionId }).catch(() => {})
})

const CAPTION_JS = (text) => `(() => {
  let c = document.getElementById('rec-caption');
  if (!c) { c = document.createElement('div'); c.id = 'rec-caption';
    c.style.cssText = 'position:fixed;left:0;right:0;bottom:0;z-index:99;padding:10px 16px;background:#1d2230;color:#fff;font:15px system-ui;text-align:center';
    document.body.appendChild(c) }
  c.textContent = ${JSON.stringify('[Recording note] ' + text)}; return true })()`
const caption = async (text, hold = 2500) => { await js(CAPTION_JS(text)); await sleep(hold) }

await send('Page.enable')
await size(1000, 720)
await send('Page.startScreencast', { format: 'jpeg', quality: 70, everyNthFrame: 1 })

// 1. Home with the live model's introduction
await send('Page.navigate', { url: APP })
await sleep(800)
await js(`localStorage.setItem('breathe60-model-mode', 'live'); true`)
await send('Page.navigate', { url: APP })
await waitFor(`!!document.querySelector('.start') && !document.querySelector('.intro')?.innerText.startsWith('...')`, 30000)
await caption('Breathe 60, a coursework prototype. Fictional user Alex. Home: the introduction was written by the live model (Gemini).', 4500)
await caption('Same as last time: the app remembers the last length and cue Alex chose. Change is one tap away.', 4000)

// 2. Full six-breath exercise with a Support pause in the middle
await caption('Start is focused, so Enter starts. The exercise is 6 breaths: 4 s in, 6 s out, 60 s planned.', 3000)
await key('Enter', 'Enter', 13)
await waitFor(`!!document.querySelector('.exercise')`)
await caption('The circle carries the pace. Only the cue, Stop, and Support are on screen. The model is not involved here.', 9000)
await click('.support')
await caption('Support opens from the top bar on every screen. Static content, no model. The exercise is paused (time excluded).', 5000)
await click('Resume')
await caption('Resume continues from the same point.', 6000)
await caption('The timer runs in the browser, so a slow network cannot stretch the exercise.', 10000)
await waitFor(`!!document.querySelector('.end h1')`, 90000)
await caption('Done: the measured length is shown and saved. Paused time is reported separately.', 4000)
await click('A bit calmer')
await caption('The optional one-tap answer is saved in its own table, apart from the observed result.', 3500)

// 3. History and a live question answered from saved records
await click('History')
await waitFor(`!!document.querySelector('table')`)
await caption('History: sessions read from SQLite through the API. Completed and stopped are recorded differently.', 4500)
const typeAsk = async (q) => {
  await js(`(() => { const i = document.querySelector('#ask-input'); Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(i, ${JSON.stringify(q)}); i.dispatchEvent(new Event('input', { bubbles: true })); return true })()`)
  await click('.ask button')
  await waitFor(`!document.querySelector('.ask button').disabled`, 60000)
  await sleep(600)
}
await caption('Asking the live model about saved sessions (it proposes a read-only query; the backend checks and runs it).', 2500)
await typeAsk('How many sessions did I finish, and when was the last one?')
await js(`document.querySelector('.reply details')?.setAttribute('open', ''); true`)
await caption('Answered only from the retrieved rows. The query is shown under "How this was answered".', 5500)

// 4. Crisis wording: no model call, Support opens
await typeAsk('I want to end my life')
await caption('Crisis wording is matched before any model call: no model request, and the Support panel opens.', 5500)
await click('Close')

// 5. Model failure: the app keeps working
await js(`document.querySelector('.foot details').setAttribute('open', ''); true`)
await js(`(() => { const s = document.querySelector('.foot select'); s.value = 'fail'; s.dispatchEvent(new Event('change')); return true })()`)
await caption('Demo control: simulate a model outage.', 2500)
await typeAsk('How many sessions did I finish?')
await caption('The outage is reported honestly; no reply is invented. It is saved as a failed request.', 4500)
await click('Home')
await waitFor(`!!document.querySelector('.start') && !document.querySelector('.intro')?.innerText.startsWith('...')`, 30000)
await caption('Home falls back to fixed text. Start and Support still work.', 4000)

// 6. Stop mid-exercise
await click('.start')
await caption('Stop works at any moment, with no confirmation and no penalty.', 7000)
await click('.stop')
await caption('Saved as stopped, with the breaths done. Leaving costs nothing.', 4500)
await js(`(() => { const s = document.querySelector('.foot select'); s.value = 'live'; s.dispatchEvent(new Event('change')); return true })()`)

await send('Page.stopScreencast')
await sleep(500)
const lines = []
for (let i = 0; i < frames.length; i++) {
  const dur = i + 1 < frames.length ? Math.max(frames[i + 1].t - frames[i].t, 0.02) : 1
  lines.push(`file '${frames[i].file.replace(/\\/g, '/')}'`, `duration ${dur.toFixed(3)}`)
}
lines.push(`file '${frames[frames.length - 1].file.replace(/\\/g, '/')}'`)
writeFileSync(join(outDir, 'frames.txt'), lines.join('\n'))
console.log('frames', frames.length, 'seconds', (frames.at(-1).t - frames[0].t).toFixed(1))
ws.close(); chrome.kill(); process.exit(0)

// Records the captioned Part 3.3 demo of the running app (frontend :5180, backend :8100) in
// headless Chrome with the LIVE model. Frames and their timestamps are saved, then joined by ffmpeg.
// Based on demo_record.mjs (Part 3.2). Usage: node docs/evidence/demo_record_3_3.mjs <outDir>
import { spawn } from 'node:child_process'
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
const PORT = 9413
const APP = 'http://localhost:5180/'
const outDir = process.argv[2]
mkdirSync(outDir, { recursive: true })
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const observed = []

// A headless Chrome left over from an earlier run would keep this port and its old page, and the
// recording would drive that page instead of a fresh one. Refuse to start in that case.
try { await fetch(`http://127.0.0.1:${PORT}/json/list`); console.error(`port ${PORT} is already in use; close the old headless Chrome first`); process.exit(1) } catch {}
const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), 'b60-'))}`, '--window-size=1000,760', 'about:blank'], { stdio: 'ignore' })
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
const click = (selectorOrText) => js(`(() => { const t = ${JSON.stringify(selectorOrText)}; const el = document.querySelector(t) || [...document.querySelectorAll('button')].find(b => b.textContent.trim().replace(/^\\u2713\\s*/, '').startsWith(t)); if (!el) throw new Error('no element ' + t); el.scrollIntoView({ block: 'center' }); el.click(); return true })()`)
const waitFor = async (expr, ms = 120000) => { const end = Date.now() + ms; while (Date.now() < end) { if (await js(expr)) return true; await sleep(100) } throw new Error('timeout waiting for ' + expr) }
const scrollTo = (sel) => js(`(() => { document.querySelector(${JSON.stringify(sel)})?.scrollIntoView({ block: 'center', behavior: 'smooth' }); return true })()`)
const look = async (label, expr) => { const v = await js(expr); observed.push({ label, value: v }); console.log(label, JSON.stringify(v)) }

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
    c.style.cssText = 'position:fixed;left:0;right:0;bottom:0;z-index:99;padding:10px 18px;background:#1d2230;color:#fff;font:16px/1.4 system-ui;text-align:center';
    document.body.appendChild(c) }
  c.textContent = ${JSON.stringify('')} + ${JSON.stringify(text)}; return true })()`
const caption = async (text, hold = 3000) => { await js(CAPTION_JS(text)); await sleep(hold) }
const introReady = `!!document.querySelector('.start') && !!document.querySelector('.intro .source')`

await send('Page.enable')
await send('Emulation.setDeviceMetricsOverride', { width: 1000, height: 760, deviceScaleFactor: 1, mobile: false })
await send('Page.navigate', { url: APP })
await sleep(800)
await js(`localStorage.setItem('breathe60-model-mode', 'live'); true`)
await send('Page.startScreencast', { format: 'jpeg', quality: 72, everyNthFrame: 1 })

// 1. Home and the optional check-in
await send('Page.navigate', { url: APP })
await waitFor(`!!document.querySelector('.checkin')`, 30000)
await caption('Breathe 60: a coursework prototype for one skill, paced breathing. Fictional user Alex, with four earlier sessions.', 4500)
await caption('The check-in is optional and one tap. The app only uses what Alex says; it never guesses from clicks or timing.', 4500)
await click('Overwhelmed')
await sleep(600)
await look('overwhelmed_buttons', `document.querySelectorAll('main button').length`)
await caption('"Overwhelmed": Home contracts to the title, Start and Support (D1). "Show everything" undoes it.', 5000)
await click('Show everything')
await sleep(500)
await click('Change')
await sleep(500)
await click('A bit tense')
await waitFor(introReady, 30000)
await caption('"A bit tense": the shortest length, 6 breaths (R1). "Your usual" comes from Alex\'s last sessions.', 5000)
await look('home_intro', `document.querySelector('.intro')?.innerText`)
await caption('The introduction above was written by the live model (Gemini) from the check-in and Alex\'s usual choice.', 5000)

// 2. The exercise: pause, Support, finish
await click('.start')
await waitFor(`!!document.querySelector('.exercise')`)
await caption('6 breaths: 4 s in, 6 s out, 60 s planned. The timer runs in the browser; the model is not involved here.', 12000)
await click('Pause')
await caption('Pause keeps Alex\'s place. Paused time is saved apart, so the measured time stays 60 s.', 4500)
await click('Resume')
await caption('Resume continues from the same point.', 6000)
await click('.support')
await caption('Support is in the top bar of every screen: static and verified, works with the model or backend down. It pauses the exercise.', 5500)
await click('Resume')
await caption('Stop is always one press away, with no confirmation and nothing lost.', 12000)
await waitFor(`!!document.querySelector('.end h1')`, 90000)
await look('end', `document.querySelector('.end')?.innerText.split('\\n').slice(0, 3).join(' | ')`)
await caption('Done. The measured time is shown and saved, with paused time reported separately.', 4000)

// 3. Answer and the grounded reply
await click('About the same')
await sleep(150)
await caption('The answer shows at once, then "Saved". It is Alex\'s own word, stored apart from what was observed.', 3500)
await waitFor(`!!document.querySelector('.end .reply') && !document.querySelector('.end .reply').innerText.includes('Looking at')`, 40000)
await scrollTo('.end .reply')
await look('reply', `document.querySelector('.end .reply')?.innerText`)
await caption('The live model\'s reply uses facts the app computed from Alex\'s saved sessions, one app-chosen suggestion and one sourced tip.', 7000)
await caption('The tip links to its source. A reply with a number not in the records, praise, or a claim that it "helped" is refused.', 6500)

// 4. History: profile and a question answered from saved records
await click('History')
await waitFor(`!!document.querySelector('[data-testid=profile-card]')`)
await caption('History: the profile is built from use, nothing to fill in. Finished and stopped sessions are kept apart.', 5500)
const typeAsk = async (q) => {
  await js(`(() => { const i = document.querySelector('#ask-input'); Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(i, ${JSON.stringify(q)}); i.dispatchEvent(new Event('input', { bubbles: true })); return true })()`)
  await click('.ask button')
  await waitFor(`!document.querySelector('.ask button').disabled`, 60000)
  await sleep(600)
}
await scrollTo('#ask-input')
await caption('Asking about saved sessions: the model proposes one read-only query; the app checks it and runs it on Alex\'s rows only.', 3500)
await typeAsk('How many sessions did I finish this week, and how many did I stop?')
await js(`document.querySelector('.reply details')?.setAttribute('open', ''); true`)
await scrollTo('.reply')
await look('history_answer', `document.querySelector('.reply')?.innerText`)
await caption('Answered only from the retrieved rows. The query is shown under "How this was answered".', 6500)
await typeAsk('I want to end my life')
await caption('Crisis wording is matched before any model call: no request is made and the Support panel opens.', 6000)
await click('Close')

// 5. Model failure
await js(`document.querySelector('.foot details').setAttribute('open', ''); true`)
await js(`(() => { const s = document.querySelector('.foot select'); s.value = 'fail'; s.dispatchEvent(new Event('change')); return true })()`)
await scrollTo('.foot')
await caption('Demo control: simulate a model outage.', 3000)
await click('Home')
await waitFor(introReady, 30000)
await js(`window.scrollTo(0, 0); true`)
await caption('Home falls back to fixed text, labelled "Fixed text". Start, Pause, Stop and Support do not depend on the model.', 5500)
await click('.start')
await caption('Stopping early is fine and is saved as stopped, never as finished.', 5000)
await click('.stop')
await sleep(600)
await look('stopped', `document.querySelector('.end h1')?.innerText`)
await caption('Leaving costs nothing. End of the demo.', 4000)
await js(`(() => { const s = document.querySelector('.foot select'); if (s) { s.value = 'live'; s.dispatchEvent(new Event('change')) } return true })()`)

const stoppedAt = Date.now() / 1000
await send('Page.stopScreencast')
await sleep(500)
const lines = []
for (let i = 0; i < frames.length; i++) {
  // The last frame lasts until recording stopped, so the final caption is not cut short.
  const dur = i + 1 < frames.length ? Math.max(frames[i + 1].t - frames[i].t, 0.02) : Math.max(stoppedAt - frames[i].t, 1)
  lines.push(`file '${frames[i].file.replace(/\\/g, '/')}'`, `duration ${dur.toFixed(3)}`)
}
lines.push(`file '${frames[frames.length - 1].file.replace(/\\/g, '/')}'`)
writeFileSync(join(outDir, 'frames.txt'), lines.join('\n'))
writeFileSync(join(outDir, 'observed.json'), JSON.stringify(observed, null, 1))
console.log('frames', frames.length, 'seconds', (frames.at(-1).t - frames[0].t).toFixed(1))
ws.close()
// chrome.kill() alone left the main process running on Windows; end the whole tree.
spawn('taskkill', ['/PID', String(chrome.pid), '/T', '/F'], { stdio: 'ignore' }).on('exit', () => process.exit(0))

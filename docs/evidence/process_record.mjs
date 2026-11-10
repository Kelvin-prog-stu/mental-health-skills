// Records the captioned Part 3.3 process screencast: one failure, the evidence, the decision, and a
// piece of generated code. It builds a page from real outputs saved in <evidenceDir> (the saved
// database row, the model timing probe, the code change, a scenario run, the code excerpt) and
// steps through it in headless Chrome. Usage: node docs/evidence/process_record.mjs <evidenceDir> <outDir>
import { spawn } from 'node:child_process'
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { pathToFileURL } from 'node:url'

const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
const PORT = 9414
const [evDir, outDir] = process.argv.slice(2)
mkdirSync(outDir, { recursive: true })
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const read = (f) => readFileSync(join(evDir, f), 'utf8')
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
const diff = (s) => esc(s).split('\n').map((l) => l.startsWith('+') ? `<span class="add">${l}</span>` : l.startsWith('-') ? `<span class="del">${l}</span>` : l).join('\n')

// Oct 27 timings: the same probe, run inline that day (recorded in AI-USE.md entry 14).
const oct27 = `Oct 27 (same probe, app limit then 12 s)
gemini-3.5-flash-lite    HTTP 200   13.0 s  finish=STOP
gemini-3.1-flash-lite    HTTP 200    4.3 s  finish=STOP
gemini-3.6-flash         HTTP 200    3.3 s  finish=STOP  thinking tokens=362`

const html = `<!doctype html><html><head><meta charset="utf-8"><title>Process: a cut-off reply</title><style>
body{margin:0;background:#f6f4f0;color:#1d2230;font:17px/1.5 system-ui}
main{max-width:940px;margin:0 auto;padding:28px 28px 120px}
h1{font:400 30px Georgia,serif;margin:0 0 6px} h2{font:400 23px Georgia,serif;margin:0 0 8px}
section{background:#fff;border:1px solid #e3e0da;border-radius:14px;padding:18px 20px;margin:0 0 26px;min-height:560px}
.k{display:inline-block;font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#3d6e8f;margin-bottom:6px}
pre{background:#1d2230;color:#e8ecf3;border-radius:10px;padding:14px 16px;font:13.5px/1.5 Consolas,monospace;white-space:pre-wrap;overflow:hidden;margin:10px 0}
.add{color:#9fe0a8}.del{color:#ff9d9d} mark{background:#ffe08a;color:#1d2230;padding:0 3px;border-radius:3px}
</style></head><body><main>
<h1>Breathe 60: one failure, the evidence, the decision</h1>
<p>IST 402 Assignment 3, Part 3. Fictional user Alex. All outputs below are real, saved from the project.</p>
<section id="s1"><span class="k">1 · The failure (Oct 27)</span><h2>A reply was saved and shown cut off mid-sentence</h2>
<pre>${esc(read('1-db-row.txt')).replace('If you want', '<mark>If you want</mark>')}</pre>
<p>The answer ends at "If you want" but is saved with status <b>ok</b>, so the app treated it as complete.</p></section>
<section id="s2"><span class="k">2 · Evidence</span><h2>Slow models, then a fallback, then a short reply</h2>
<p>The same row's timestamps: retrieval at 18:06:31, answer at 18:07:12, <b>41 s</b> for one reply. Timing each model in the fallback chain:</p>
<pre>${esc(oct27)}</pre><pre>${esc('Today, with the fix\n' + read('2-timing.txt'))}</pre>
<p>On Oct 27 the main model took 13 s, past the 12 s limit, so requests fell through to the other models. The reply's finish reason was never checked, so a stopped reply looked like a finished one. Today the main model answered 503 (overloaded) and the next one answered in about a second.</p></section>
<section id="s3"><span class="k">3 · Decision</span><h2>Refuse cut-off replies; hand over to the next model sooner</h2>
<pre>${diff(read('3-diff.txt'))}</pre>
<p>A reply whose finish reason is not STOP is refused, and the app shows its own fixed sentence instead. Each model gets 8 s before the next is tried.</p></section>
<section id="s4"><span class="k">4 · Checking it</span><h2>Scenarios and behavior checks, mocked</h2>
<pre>${esc(read('4-scenarios.txt'))}</pre>
<p>B1 holds across all cases: no failed or blocked request gets an invented reply, and no saved reply breaks the wording rules.</p></section>
<section id="s5"><span class="k">5 · A piece of generated code, and a surprise</span><h2><code>_facts_quoted</code> in backend/assistant.py</h2>
<pre>${esc(read('5-code.txt'))}</pre>
<p>The first guard only checked that every number in a reply appeared somewhere in the facts. A live reply then said "You have 5 completed sessions saved out of 5 total" when Alex had 4 finished and 1 stopped. 5 was a real number, so it passed. Now the app writes the fact sentences itself, the model has to copy one word for word, and any other number, in digits or words, must come from the suggestion or the tip. The same wrong reply is now refused (a check in check_app.py).</p></section>
</main></body></html>`
const page = join(outDir, 'process.html')
writeFileSync(page, html)

try { await fetch(`http://127.0.0.1:${PORT}/json/list`); console.error(`port ${PORT} is already in use`); process.exit(1) } catch {}
const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${mkdtempSync(join(tmpdir(), 'b60p-'))}`, '--window-size=1000,760', 'about:blank'], { stdio: 'ignore' })
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
const js = async (expression) => { const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }); return r.result?.value }
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
const caption = async (text, hold) => {
  await js(`(() => { let c = document.getElementById('cap'); if (!c) { c = document.createElement('div'); c.id = 'cap';
    c.style.cssText = 'position:fixed;left:0;right:0;bottom:0;padding:12px 18px;background:#1d2230;color:#fff;font:16px/1.4 system-ui;text-align:center';
    document.body.appendChild(c) } c.textContent = ${JSON.stringify(text)}; return true })()`)
  await sleep(hold)
}
const show = (sel) => js(`document.querySelector(${JSON.stringify(sel)}).scrollIntoView({ block: 'start', behavior: 'smooth' }); true`)
const scrollBy = (px) => js(`window.scrollBy({ top: ${px}, behavior: 'smooth' }); true`)

await send('Page.enable')
await send('Emulation.setDeviceMetricsOverride', { width: 1000, height: 760, deviceScaleFactor: 1, mobile: false })
await send('Page.navigate', { url: pathToFileURL(page).href })
await sleep(800)
await send('Page.startScreencast', { format: 'jpeg', quality: 75, everyNthFrame: 1 })
await caption('Process screencast: one failure in Breathe 60, the evidence used to understand it, and the decision.', 5000)
await show('#s1'); await caption('The failure: on Oct 27 a live reply was saved ending "If you want", with status ok, and shown as if it were finished.', 9000)
await show('#s2'); await caption('Evidence: 41 s between retrieval and answer. Timing each model showed the main one took 13 s, past the 12 s limit.', 9000)
await scrollBy(260); await caption('Requests were falling through the fallback chain, and nothing checked whether the reply had actually finished.', 8000)
await caption('Today the main model answered 503 (overloaded) and the next model answered in about a second: the fallback in action.', 7000)
await show('#s3'); await caption('Decision: refuse any reply whose finish reason is not STOP, and give each model 8 s before trying the next one.', 9000)
await scrollBy(220); await caption('A refused reply is replaced by the app\'s own fixed sentence, labelled as fixed text. Nothing is invented.', 7000)
await show('#s4'); await caption('Checking it: 15 scenarios and 3 behavior checks, mocked so they repeat exactly. 18 of 18 pass.', 8000)
await show('#s5'); await caption('A surprise: a reply said "5 completed out of 5" when Alex had 4 finished. Every number was real, so the first guard passed it.', 9000)
await caption('The fix: the app writes the fact sentences and the model must copy one word for word. Other numbers must come from the suggestion or tip.', 9000)
await caption('The same wrong reply is now refused, and a backend check keeps it that way. End of the screencast.', 6000)
const stoppedAt = Date.now() / 1000
await send('Page.stopScreencast')
await sleep(400)
const lines = []
for (let i = 0; i < frames.length; i++) {
  // The last frame lasts until recording stopped, so the final caption is not cut short.
  const dur = i + 1 < frames.length ? Math.max(frames[i + 1].t - frames[i].t, 0.02) : Math.max(stoppedAt - frames[i].t, 1)
  lines.push(`file '${frames[i].file.replace(/\\/g, '/')}'`, `duration ${dur.toFixed(3)}`)
}
lines.push(`file '${frames[frames.length - 1].file.replace(/\\/g, '/')}'`)
writeFileSync(join(outDir, 'frames.txt'), lines.join('\n'))
console.log('frames', frames.length, 'seconds', (frames.at(-1).t - frames[0].t).toFixed(1))
ws.close()
spawn('taskkill', ['/PID', String(chrome.pid), '/T', '/F'], { stdio: 'ignore' }).on('exit', () => process.exit(0))

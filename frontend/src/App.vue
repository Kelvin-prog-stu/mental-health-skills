<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'

import { finishSession, getIntro, getReflection, getPreferences, getProfile, putPreferences, sendCheckin, sendFeedback, startSession } from '@/api'
import BreathingExercise from '@/components/BreathingExercise.vue'
import HistoryView from '@/components/HistoryView.vue'
import SupportPanel from '@/components/SupportPanel.vue'
import { PROTOTYPE_NOTICE } from '@/support'

const FIXED_INTRO = 'Breathe in for 4, out for 6. Six breaths, about a minute. Stop whenever you like.'
const MODE_KEY = 'breathe60-model-mode'

const view = ref('home') // home | exercise | end | history
const supportOpen = ref(false)
const mode = ref(readMode())
const prefs = ref({ breaths: 6, cue: 'circle', fewer_words: false, remembered: [] })
const choice = ref({ breaths: 6, cue: 'circle' })
const changing = ref(false)
const intro = ref({ text: '', source: 'loading' })
const homeShownAt = ref(performance.now())
const session = ref(null) // { clientKey, id, breaths, cue, entryMs }
const lastResult = ref(null)
const saveNote = ref('')
// The answer shows as chosen the moment it is tapped; the line below it follows the save.
const SELF_REPORT_OPTIONS = [
  { value: 'a_bit_calmer', label: 'A bit calmer' },
  { value: 'about_the_same', label: 'About the same' },
  { value: 'not_sure', label: 'Not sure' },
]
const feedback = ref({ choice: null, saved: null, status: 'idle', error: '' })
let feedbackRequest = 0
// The model's reply to the answer. It comes after the exercise, so it may take longer than the intro.
const REPLY_WAIT_MS = 25000
const reply = ref({ status: 'idle', text: '', source: '', action: null, sources: [] })
const startButton = ref(null)

const seconds = computed(() => choice.value.breaths * 10)
const sameAsLast = computed(() => prefs.value.remembered.includes('breaths') || prefs.value.remembered.includes('cue'))
const profile = ref(null)
const showEverything = ref(false)
const changingCheckin = ref(false)
const suggestionNote = ref('')
const FEELING_WORDS = { steady: 'Steady', tense: 'A bit tense', overwhelmed: 'Overwhelmed' }
const feeling = computed(() => profile.value?.current_checkin?.feeling ?? null)
// Less on screen when the person asks for it: "Fewer words", or the "Overwhelmed" check-in (D1).
const contracted = computed(() => prefs.value.fewer_words || (feeling.value === 'overwhelmed' && !showEverything.value))
const isUsual = computed(() => {
  const u = profile.value?.usual
  return !!u && u.breaths === choice.value.breaths && u.cue === choice.value.cue
})
const firstName = computed(() => (profile.value?.display_name ?? 'Alex').split(' ')[0])

function readMode() {
  try {
    return localStorage.getItem(MODE_KEY) || 'live'
  } catch {
    return 'live'
  }
}

function setMode(value) {
  mode.value = value
  try {
    localStorage.setItem(MODE_KEY, value)
  } catch {
    // remembered for this page only
  }
  loadIntro()
}

// The free model can take 20 s or more; after this the fixed text is shown instead.
const INTRO_WAIT_MS = 10000
let introRequest = 0

async function loadIntro() {
  const thisRequest = ++introRequest
  intro.value = { text: '', source: 'loading' }
  try {
    const reply = await getIntro(mode.value, AbortSignal.timeout(INTRO_WAIT_MS))
    if (thisRequest === introRequest) intro.value = reply
  } catch {
    // Slow or unreachable: the fixed text is shipped with the page, so Start still works.
    if (thisRequest === introRequest) intro.value = { text: FIXED_INTRO, source: 'fixed', note: 'model slow or unreachable' }
  }
}

async function loadPreferences() {
  try {
    prefs.value = await getPreferences()
  } catch {
    // keep defaults
  }
  try {
    profile.value = await getProfile()
  } catch {
    // no profile shown; the exercise and Support do not need it
  }
  // Default to the person's usual (most common recent choice), else the last choice.
  const usual = profile.value?.usual
  choice.value = usual ? { breaths: usual.breaths, cue: usual.cue } : { breaths: prefs.value.breaths, cue: prefs.value.cue }
  suggestionNote.value = ''
  applyCheckin(profile.value?.current_checkin?.feeling)
}

// The check-in is the person's own word. It changes what Home shows and suggests; it never
// blocks Start or Support, and every change it makes can be undone with one tap.
function applyCheckin(feeling) {
  showEverything.value = false
  if (feeling === 'tense' && choice.value.breaths !== 6) {
    choice.value = { ...choice.value, breaths: 6 }
    suggestionNote.value = 'Set to 6 breaths because you said a bit tense.'
  } else if (feeling === 'steady') {
    suggestionNote.value = ''
  }
}

async function checkIn(feeling) {
  try {
    await sendCheckin(feeling)
  } catch {
    // Not saved, but still used for this visit.
  }
  profile.value = { ...(profile.value ?? {}), current_checkin: { feeling } }
  applyCheckin(feeling)
  changingCheckin.value = false
  loadIntro()
}

async function goHome() {
  view.value = 'home'
  changing.value = false
  homeShownAt.value = performance.now()
  await loadPreferences()
  loadIntro()
  await nextTick()
  startButton.value?.focus()
}

function newKey() {
  return (crypto.randomUUID?.() ?? `${Date.now()}${Math.random()}`).replace(/[^A-Za-z0-9]/g, '').slice(0, 24)
}

function start() {
  const entryMs = Math.round(performance.now() - homeShownAt.value)
  saveNote.value = ''
  feedback.value = { choice: null, saved: null, status: 'idle', error: '' }
  reply.value = { status: 'idle', text: '', source: '', action: null, sources: [] }
  session.value = { clientKey: newKey(), id: null, breaths: choice.value.breaths, cue: choice.value.cue, entryMs }
  view.value = 'exercise'
  window.scrollTo(0, 0)
  // Not awaited: a slow or missing backend must not delay or block the exercise.
  session.value.saving = startSession({
    planned_breaths: choice.value.breaths,
    cue: choice.value.cue,
    entry_ms: entryMs,
    client_key: session.value.clientKey,
  })
    .then((row) => (session.value.id = row.session_id))
    .catch((error) => (saveNote.value = `This session was not saved. ${error.message}`))
}

async function onFinished(result) {
  lastResult.value = result
  supportOpen.value = false
  view.value = 'end'
  await session.value.saving
  if (!session.value.id) return
  try {
    await finishSession(session.value.id, {
      status: result.status,
      breaths_done: result.breathsDone,
      exercise_ms: result.exerciseMs,
      paused_ms: result.pausedMs,
    })
  } catch (error) {
    saveNote.value = `The end of this session was not saved. ${error.message}`
  }
}

async function answer(value) {
  if (!session.value?.id || value === feedback.value.choice) return
  const thisRequest = ++feedbackRequest
  const saved = feedback.value.saved
  feedback.value = { choice: value, saved, status: 'saving', error: '' }
  try {
    await sendFeedback(session.value.id, value)
    if (thisRequest !== feedbackRequest) return
    feedback.value = { choice: value, saved: value, status: 'saved', error: '' }
    loadReply(value, thisRequest)
  } catch (error) {
    // Show what is really stored: go back to the last saved answer, if any.
    if (thisRequest === feedbackRequest) feedback.value = { choice: saved, saved, status: 'failed', error: error.message }
  }
}

async function loadReply(value, thisRequest) {
  reply.value = { status: 'loading', text: '', source: '', action: null, sources: [] }
  try {
    const result = await getReflection(session.value.id, mode.value, AbortSignal.timeout(REPLY_WAIT_MS))
    if (thisRequest === feedbackRequest) {
      reply.value = { status: 'done', text: result.text, source: result.source, action: result.action ?? null, sources: result.sources ?? [] }
    }
  } catch {
    if (thisRequest !== feedbackRequest) return
    const label = SELF_REPORT_OPTIONS.find((o) => o.value === value)?.label.toLowerCase()
    reply.value = { status: 'done', text: `You said ${label}. It's saved with this session.`, source: 'fixed', action: null, sources: [] }
  }
}

// The suggestion's button only fills in the length and cue; Alex still presses it to start.
function tryAction(action) {
  choice.value = { breaths: action.breaths, cue: action.cue }
  start()
}

async function toggleFewerWords() {
  try {
    prefs.value = await putPreferences({ fewer_words: !prefs.value.fewer_words })
  } catch {
    prefs.value = { ...prefs.value, fewer_words: !prefs.value.fewer_words }
  }
}

// Leaving the page mid-exercise: record it as stopped if the browser lets the request out.
function onPageHide() {
  if (view.value !== 'exercise' || !session.value?.id) return
  fetch(`/api/sessions/${session.value.id}`, {
    method: 'PATCH',
    keepalive: true,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status: 'stopped', breaths_done: 0, exercise_ms: null, paused_ms: 0 }),
  })
}

const exerciseRef = ref(null)
function stopFromSupport() {
  supportOpen.value = false
  exerciseRef.value?.stop()
}

onMounted(() => {
  window.addEventListener('pagehide', onPageHide)
  goHome()
})
</script>

<template>
  <header class="bar">
    <button type="button" class="brand" @click="view !== 'exercise' && goHome()"><span class="brand-dot" aria-hidden="true"></span>Breathe 60</button>
    <nav>
      <button v-if="view !== 'exercise' && view !== 'history'" type="button" class="link" @click="view = 'history'">History</button>
      <button v-if="view === 'history'" type="button" class="link" @click="goHome">Home</button>
      <button type="button" class="support" @click="supportOpen = true">Support</button>
    </nav>
  </header>

  <main class="page">
    <section v-if="view === 'home'" class="home" aria-labelledby="home-title">
      <div class="hero">
        <div v-if="!contracted" class="hero-orb" aria-hidden="true"></div>
        <p v-if="!contracted" class="greeting">{{ profile?.sessions ? `Welcome back, ${firstName}` : `Hi, ${firstName}` }}</p>
        <h1 id="home-title">Take a calm minute</h1>
        <p v-if="!contracted">Six slow breaths. You can stop at any moment.</p>
      </div>

      <div v-if="!feeling || changingCheckin" class="checkin card-soft" role="group" aria-labelledby="checkin-q">
        <p id="checkin-q" class="checkin-q">How are you arriving right now? <span class="muted small">(optional)</span></p>
        <div class="chips">
          <button type="button" @click="checkIn('steady')">Steady</button>
          <button type="button" @click="checkIn('tense')">A bit tense</button>
          <button type="button" @click="checkIn('overwhelmed')">Overwhelmed</button>
        </div>
        <p class="muted small center">Your own word. The app never guesses how you feel.</p>
      </div>
      <p v-else class="checkin-line">
        You said: <strong>{{ FEELING_WORDS[feeling] }}</strong>
        <button type="button" class="link" @click="changingCheckin = true">Change</button>
      </p>

      <p v-if="feeling === 'overwhelmed' && !showEverything" class="adapt-note">
        You said overwhelmed, so this screen shows less.
        <button type="button" class="link" @click="showEverything = true">Show everything</button>
      </p>
      <p v-if="suggestionNote" class="adapt-note">
        {{ suggestionNote }}
        <button type="button" class="link" @click="choice = { ...choice, breaths: 8 }; suggestionNote = ''">Use 8 instead</button>
      </p>
      <p v-if="feeling === 'steady' && choice.breaths === 6 && !changing" class="adapt-note">
        Feeling steady? You could try the longer 8 breaths (80 s).
        <button type="button" class="link" @click="choice = { ...choice, breaths: 8 }">Try 8</button>
      </p>

      <p v-if="!contracted" class="intro" aria-live="polite">
        <template v-if="intro.source === 'loading'"><span class="muted">Writing a short note for you...</span></template>
        <template v-else>{{ intro.text }}</template>
        <span v-if="intro.source !== 'loading'" class="source">
          {{ intro.source === 'model' ? 'Written by the model' : intro.source === 'mock' ? 'Mock reply (test mode)' : 'Fixed text' }}
        </span>
      </p>

      <button ref="startButton" type="button" class="primary start" @click="start">
        Start breathing ({{ seconds }} s)
      </button>

      <div v-if="!changing && !contracted" class="pill-row">
        <span v-if="isUsual" class="pill pill-usual" :title="`Your most common choice over your last ${profile.usual.based_on} sessions`">Your usual</span>
        <span v-else-if="sameAsLast" class="pill">Same as last time</span>
        <span class="pill">{{ choice.breaths }} breaths</span>
        <span class="pill">{{ choice.cue === 'circle' ? 'Circle cue' : 'Text cue, no motion' }}</span>
        <button type="button" class="link" @click="changing = true">Change</button>
      </div>

      <fieldset v-if="changing" class="choices">
        <legend>Length</legend>
        <label><input v-model.number="choice.breaths" type="radio" :value="6" /> 6 breaths (60 s)</label>
        <label><input v-model.number="choice.breaths" type="radio" :value="8" /> 8 breaths (80 s)</label>
        <legend class="second">Cue</legend>
        <label><input v-model="choice.cue" type="radio" value="circle" /> Circle that grows and shrinks</label>
        <label><input v-model="choice.cue" type="radio" value="text" /> Words and counts only (no motion)</label>
        <button type="button" class="link" @click="changing = false">Done</button>
      </fieldset>

      <p class="small center">
        <button type="button" class="link" @click="toggleFewerWords">{{ prefs.fewer_words ? 'Show more words' : 'Fewer words' }}</button>
      </p>
      <p class="notice">{{ PROTOTYPE_NOTICE }}</p>
    </section>

    <BreathingExercise
      v-else-if="view === 'exercise'"
      ref="exerciseRef"
      :breaths="session.breaths"
      :cue="session.cue"
      :external-pause="supportOpen"
      @finished="onFinished"
    />

    <section v-else-if="view === 'end'" class="end card" aria-live="polite">
      <div class="hero-orb" style="width: 84px; height: 84px; margin: 0.4rem auto 0" aria-hidden="true"></div>
      <h1 v-if="lastResult.status === 'completed'">That was {{ session.breaths }} breaths.</h1>
      <h1 v-else>Stopped after {{ lastResult.breathsDone }} {{ lastResult.breathsDone === 1 ? 'breath' : 'breaths' }}. That is fine.</h1>
      <p class="muted small">Measured: {{ (lastResult.exerciseMs / 1000).toFixed(1) }} s<span v-if="lastResult.pausedMs"> (plus {{ (lastResult.pausedMs / 1000).toFixed(1) }} s paused)</span>.</p>

      <template v-if="session.id">
        <p class="muted">How was that? (optional)</p>
        <div class="chips">
          <button
            v-for="option in SELF_REPORT_OPTIONS"
            :key="option.value"
            type="button"
            :class="{ chosen: feedback.choice === option.value }"
            :aria-pressed="feedback.choice === option.value"
            @click="answer(option.value)"
          >
            <span v-if="feedback.choice === option.value" class="tick" aria-hidden="true">&#10003;</span>
            {{ option.label }}
          </button>
        </div>
        <p class="feedback-status small" role="status">
          <template v-if="feedback.status === 'saving'">Saving...</template>
          <template v-else-if="feedback.status === 'saved'">Saved as your answer. Tap another to change it.</template>
          <span v-else-if="feedback.status === 'failed'" class="problem-text">Not saved: {{ feedback.error }} Tap again to retry.</span>
        </p>
        <div v-if="reply.status !== 'idle'" class="reply" aria-live="polite">
          <p v-if="reply.status === 'loading'" class="muted">Looking at your sessions...</p>
          <template v-else>
            <p>{{ reply.text }}</p>
            <button v-if="reply.action" type="button" class="secondary reply-action" @click="tryAction(reply.action)">
              {{ reply.action.label }} ({{ reply.action.breaths * 10 }} s)
            </button>
            <p v-if="reply.sources.length" class="reply-sources">
              Tip from:
              <template v-for="(src, i) in reply.sources" :key="src.url">
                <a :href="src.url" target="_blank" rel="noopener noreferrer">{{ src.name }}</a><span v-if="i < reply.sources.length - 1">, </span>
              </template>
            </p>
            <span class="source">{{ reply.source === 'model' ? 'Written by the model from your saved sessions' : reply.source === 'mock' ? 'Mock reply (test mode)' : 'Fixed text' }}</span>
          </template>
        </div>
      </template>
      <p v-if="saveNote" class="problem" role="alert">{{ saveNote }}</p>

      <div class="actions">
        <button type="button" class="primary" @click="goHome">Home</button>
        <button type="button" class="secondary" @click="start">Start again</button>
        <button type="button" class="link" @click="view = 'history'">History</button>
      </div>
    </section>

    <HistoryView v-else-if="view === 'history'" :mode="mode" @open-support="supportOpen = true" />
  </main>

  <footer class="foot">
    <details>
      <summary>Demo controls (for testing with fictional scenarios)</summary>
      <label>
        Model:
        <select :value="mode" @change="setMode($event.target.value)">
          <option value="live">Live (Gemini)</option>
          <option value="mock">Mock (fixed replies)</option>
          <option value="fail">Fail (simulate an outage)</option>
        </select>
      </label>
    </details>
  </footer>

  <SupportPanel
    v-if="supportOpen"
    :during-exercise="view === 'exercise'"
    @close="supportOpen = false"
    @stop-exercise="stopFromSupport"
  />
</template>

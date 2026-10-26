<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'

import { finishSession, getIntro, getPreferences, putPreferences, sendFeedback, startSession } from '@/api'
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
const feedbackSent = ref('')
const startButton = ref(null)

const seconds = computed(() => choice.value.breaths * 10)
const sameAsLast = computed(() => prefs.value.remembered.includes('breaths') || prefs.value.remembered.includes('cue'))

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

async function loadIntro() {
  intro.value = { text: '', source: 'loading' }
  try {
    intro.value = await getIntro(mode.value)
  } catch {
    // Backend unreachable: the fixed text is shipped with the page, so Start still works.
    intro.value = { text: FIXED_INTRO, source: 'fixed', note: 'backend unreachable' }
  }
}

async function loadPreferences() {
  try {
    prefs.value = await getPreferences()
  } catch {
    // keep defaults
  }
  choice.value = { breaths: prefs.value.breaths, cue: prefs.value.cue }
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
  feedbackSent.value = ''
  session.value = { clientKey: newKey(), id: null, breaths: choice.value.breaths, cue: choice.value.cue, entryMs }
  view.value = 'exercise'
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

async function answer(value, label) {
  if (!session.value?.id) return
  try {
    await sendFeedback(session.value.id, value)
    feedbackSent.value = `Saved: "${label}"`
  } catch (error) {
    feedbackSent.value = `Your answer was not saved. ${error.message}`
  }
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
    <button type="button" class="brand" @click="view !== 'exercise' && goHome()">Breathe 60</button>
    <nav>
      <button v-if="view !== 'exercise' && view !== 'history'" type="button" class="link" @click="view = 'history'">History</button>
      <button v-if="view === 'history'" type="button" class="link" @click="goHome">Home</button>
      <button type="button" class="support" @click="supportOpen = true">Support</button>
    </nav>
  </header>

  <main class="page">
    <section v-if="view === 'home'" class="home" aria-labelledby="home-title">
      <h1 id="home-title" class="visually-hidden">Paced breathing</h1>
      <p v-if="!prefs.fewer_words" class="intro" aria-live="polite">
        <template v-if="intro.source === 'loading'"><span class="muted">...</span></template>
        <template v-else>{{ intro.text }}</template>
        <span v-if="intro.source !== 'loading'" class="source">
          {{ intro.source === 'model' ? 'Written by the model' : intro.source === 'mock' ? 'Mock reply (test mode)' : 'Fixed text' }}
        </span>
      </p>

      <button ref="startButton" type="button" class="primary start" @click="start">
        Start breathing ({{ seconds }} s)
      </button>

      <p v-if="sameAsLast && !changing" class="muted">
        Same as last time: {{ choice.breaths }} breaths, {{ choice.cue === 'circle' ? 'circle' : 'text' }} cue.
        <button type="button" class="link" @click="changing = true">Change</button>
      </p>
      <p v-else-if="!changing" class="muted">
        {{ choice.breaths }} breaths, {{ choice.cue }} cue.
        <button type="button" class="link" @click="changing = true">Change</button>
      </p>

      <fieldset v-if="changing" class="choices">
        <legend>Length</legend>
        <label><input v-model.number="choice.breaths" type="radio" :value="6" /> 6 breaths (60 s)</label>
        <label><input v-model.number="choice.breaths" type="radio" :value="8" /> 8 breaths (80 s)</label>
        <legend class="second">Cue</legend>
        <label><input v-model="choice.cue" type="radio" value="circle" /> Circle that grows and shrinks</label>
        <label><input v-model="choice.cue" type="radio" value="text" /> Words and counts only (no motion)</label>
        <button type="button" class="link" @click="changing = false">Done</button>
      </fieldset>

      <p class="small">
        <button type="button" class="link" @click="toggleFewerWords">{{ prefs.fewer_words ? 'Show more words' : 'Fewer words' }}</button>
      </p>
      <p v-if="!prefs.fewer_words" class="notice">{{ PROTOTYPE_NOTICE }}</p>
    </section>

    <BreathingExercise
      v-else-if="view === 'exercise'"
      ref="exerciseRef"
      :breaths="session.breaths"
      :cue="session.cue"
      :external-pause="supportOpen"
      @finished="onFinished"
    />

    <section v-else-if="view === 'end'" class="end" aria-live="polite">
      <h1 v-if="lastResult.status === 'completed'">That was {{ session.breaths }} breaths.</h1>
      <h1 v-else>Stopped after {{ lastResult.breathsDone }} {{ lastResult.breathsDone === 1 ? 'breath' : 'breaths' }}. That is fine.</h1>
      <p class="muted small">Measured: {{ (lastResult.exerciseMs / 1000).toFixed(1) }} s<span v-if="lastResult.pausedMs"> (plus {{ (lastResult.pausedMs / 1000).toFixed(1) }} s paused)</span>.</p>

      <template v-if="session.id">
        <p class="muted">How was that? (optional)</p>
        <div class="chips">
          <button type="button" @click="answer('a_bit_calmer', 'A bit calmer')">A bit calmer</button>
          <button type="button" @click="answer('about_the_same', 'About the same')">About the same</button>
          <button type="button" @click="answer('not_sure', 'Not sure')">Not sure</button>
        </div>
        <p v-if="feedbackSent" class="small" role="status">{{ feedbackSent }}</p>
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

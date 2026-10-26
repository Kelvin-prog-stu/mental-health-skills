<script setup>
// The guided sequence. The app, not the model, owns every step and the timer.
// Timing comes from the browser clock; pauses (Support open, tab hidden) are excluded and
// reported separately. Nothing here waits on the network.
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const IN_MS = 4000
const OUT_MS = 6000
const CYCLE_MS = IN_MS + OUT_MS

const props = defineProps({
  breaths: { type: Number, required: true },
  cue: { type: String, required: true },
  externalPause: { type: Boolean, default: false },
})
const emit = defineEmits(['finished'])

const elapsed = ref(0) // exercise time so far, pauses excluded
const hiddenPause = ref(false)
const stopButton = ref(null)
const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false

let frame = 0
let lastTick = 0
let startedAt = 0
let pausedMs = 0
let done = false

const isPaused = computed(() => props.externalPause || hiddenPause.value)
const total = computed(() => props.breaths * CYCLE_MS)
const breathIndex = computed(() => Math.min(Math.floor(elapsed.value / CYCLE_MS), props.breaths - 1))
const within = computed(() => elapsed.value - breathIndex.value * CYCLE_MS)
const phase = computed(() => (within.value < IN_MS ? 'in' : 'out'))
const count = computed(() =>
  phase.value === 'in' ? Math.floor(within.value / 1000) + 1 : Math.floor((within.value - IN_MS) / 1000) + 1,
)
const scale = computed(() => {
  if (phase.value === 'in') return 0.6 + 0.4 * (within.value / IN_MS)
  return 1 - 0.4 * ((within.value - IN_MS) / OUT_MS)
})
const useText = computed(() => props.cue === 'text' || reducedMotion)
const progress = computed(() => Math.min(elapsed.value / total.value, 1))

function tick(now) {
  if (done) return
  const delta = now - lastTick
  lastTick = now
  if (isPaused.value) pausedMs += delta
  else elapsed.value += delta
  if (elapsed.value >= total.value) return finish('completed')
  frame = requestAnimationFrame(tick)
}

function finish(status) {
  if (done) return
  done = true
  cancelAnimationFrame(frame)
  const wall = performance.now() - startedAt
  emit('finished', {
    status,
    breathsDone: status === 'completed' ? props.breaths : Math.floor(elapsed.value / CYCLE_MS),
    exerciseMs: Math.round(wall - pausedMs),
    pausedMs: Math.round(pausedMs),
  })
}

function stop() {
  finish('stopped')
}

function onVisibility() {
  if (document.hidden) hiddenPause.value = true
}

function onKey(event) {
  // Escape stops the exercise, except while Support is open (there it closes the panel).
  if (event.key === 'Escape' && !props.externalPause) stop()
}

watch(isPaused, (paused) => {
  if (!paused) lastTick = performance.now()
})

onMounted(() => {
  startedAt = performance.now()
  lastTick = startedAt
  frame = requestAnimationFrame(tick)
  document.addEventListener('visibilitychange', onVisibility)
  window.addEventListener('keydown', onKey)
  stopButton.value?.focus()
})

onBeforeUnmount(() => {
  done = true
  cancelAnimationFrame(frame)
  document.removeEventListener('visibilitychange', onVisibility)
  window.removeEventListener('keydown', onKey)
})

defineExpose({ stop })
</script>

<template>
  <section class="exercise" aria-label="Breathing exercise">
    <p class="counter">Breath {{ breathIndex + 1 }} of {{ breaths }}<span v-if="isPaused"> · paused</span></p>

    <div v-if="!useText" class="circle-wrap" aria-hidden="true">
      <div class="circle" :style="{ transform: `scale(${scale})` }"></div>
    </div>

    <p class="phase" :class="{ big: useText }" aria-live="polite">
      {{ phase === 'in' ? 'Breathe in' : 'Breathe out' }}
    </p>
    <p class="count" aria-hidden="true">
      <template v-if="useText">
        <span v-for="n in phase === 'in' ? 4 : 6" :key="n" :class="{ dim: n > count }">{{ n }}</span>
      </template>
      <template v-else>{{ count }}</template>
    </p>

    <div class="progress" role="progressbar" :aria-valuenow="Math.round(progress * 100)" aria-valuemin="0" aria-valuemax="100">
      <i :style="{ width: `${progress * 100}%` }"></i>
    </div>

    <div v-if="hiddenPause && !externalPause" class="paused-box">
      <p>Paused while the page was hidden.</p>
      <button type="button" class="primary" @click="hiddenPause = false">Resume</button>
    </div>

    <button ref="stopButton" type="button" class="stop" @click="stop">Stop</button>
    <p class="hint">Stop any time. Nothing is lost by stopping.</p>
  </section>
</template>

<style scoped>
.exercise { display: grid; justify-items: center; gap: 0.6rem; padding-top: 1rem; }
.counter { margin: 0; color: var(--muted); font-size: 0.95rem; }
.circle-wrap { width: 220px; height: 220px; display: grid; place-items: center; margin: 0.6rem 0; }
.circle { width: 220px; height: 220px; border-radius: 50%; background: var(--cue); border: 2px solid var(--cue-edge); }
.phase { margin: 0; font-size: 1.6rem; }
.phase.big { margin-top: 3rem; font-size: 2rem; }
.count { margin: 0; min-height: 1.6rem; font-size: 1.3rem; letter-spacing: 0.4rem; color: var(--ink); }
.count .dim { color: var(--line-strong); }
.progress { width: min(320px, 90%); height: 6px; border-radius: 3px; background: var(--line); overflow: hidden; margin: 0.8rem 0; }
.progress i { display: block; height: 100%; background: var(--cue-edge); }
.paused-box { text-align: center; }
.stop { width: min(320px, 90%); padding: 0.9rem; font-size: 1.1rem; font-weight: 600; border: 2px solid var(--muted); border-radius: 12px; background: #fff; color: var(--ink); }
.hint { margin: 0; color: var(--muted); font-size: 0.85rem; }
</style>

<script setup>
// Static support content: no request is made to open or show it.
import { nextTick, onMounted, ref } from 'vue'

import { PROTOTYPE_NOTICE, SUPPORT_ENTRIES } from '@/support'

defineProps({ duringExercise: { type: Boolean, default: false } })
const emit = defineEmits(['close', 'stop-exercise'])
const heading = ref(null)

onMounted(async () => {
  await nextTick()
  heading.value?.focus()
})
</script>

<template>
  <div class="scrim" @click.self="emit('close')">
    <section class="panel" role="dialog" aria-modal="true" aria-labelledby="support-title" @keydown.esc="emit('close')">
      <h2 id="support-title" ref="heading" tabindex="-1">If you need help now</h2>
      <ul>
        <li v-for="entry in SUPPORT_ENTRIES" :key="entry.name">
          <strong>{{ entry.how }}</strong>
          <span>{{ entry.name }}. {{ entry.note }}</span>
        </li>
      </ul>
      <p class="notice">{{ PROTOTYPE_NOTICE }}</p>
      <p v-if="duringExercise" class="notice">The exercise is paused while this is open.</p>
      <div class="actions">
        <button type="button" class="primary" @click="emit('close')">{{ duringExercise ? 'Resume' : 'Close' }}</button>
        <button v-if="duringExercise" type="button" class="secondary" @click="emit('stop-exercise')">Stop exercise</button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.scrim { position: fixed; inset: 0; background: rgb(35 49 74 / 45%); backdrop-filter: blur(3px); display: grid; align-items: end; justify-items: center; z-index: 20; }
.panel { width: min(540px, 100%); max-height: 92vh; overflow-y: auto; background: #fff; border-radius: 24px 24px 0 0; padding: 1.4rem 1.3rem 1.6rem; box-shadow: 0 -10px 40px -10px rgb(35 49 74 / 35%); }
h2 { margin: 0 0 0.8rem; font-family: Georgia, serif; font-weight: 400; font-size: 1.5rem; }
ul { list-style: none; padding: 0; margin: 0 0 0.8rem; display: grid; gap: 0.55rem; }
li { display: grid; gap: 0.1rem; padding: 0.7rem 0.9rem; background: #f4f8fb; border: 1px solid #e1ebf2; border-radius: 14px; }
li strong { font-size: 1.15rem; color: var(--brand-dark); }
li span { color: var(--muted); font-size: 0.9rem; }
.notice { margin: 0.3rem 0; color: var(--muted); font-size: 0.88rem; }
.actions { display: grid; gap: 0.5rem; margin-top: 0.8rem; }
</style>

<script setup>
// Saved sessions and questions, read through the API from SQLite. Browsing makes no model call.
import { onMounted, ref } from 'vue'

import { ask, listConversations, listSessions } from '@/api'

const props = defineProps({ mode: { type: String, required: true } })
const emit = defineEmits(['open-support'])

const sessions = ref([])
const conversations = ref([])
const loadError = ref('')
const loading = ref(true)
const question = ref('')
const asking = ref(false)
const reply = ref(null)
const askError = ref('')

const ANSWERS = { a_bit_calmer: 'A bit calmer', about_the_same: 'About the same', not_sure: 'Not sure' }
const when = (iso) => (iso ? new Date(iso).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : '')
const result = (s) =>
  s.status === 'completed' ? 'Completed' : s.status === 'stopped' ? `Stopped after ${s.breaths_done}` : 'Ended early (not finished)'
const seconds = (ms) => (ms == null ? '' : `${(ms / 1000).toFixed(1)} s`)

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const [s, c] = await Promise.all([listSessions(), listConversations()])
    sessions.value = s.sessions
    conversations.value = c.conversations.filter((x) => x.purpose === 'question')
  } catch (error) {
    loadError.value = `History could not load. ${error.message}`
  } finally {
    loading.value = false
  }
}

async function submit() {
  const text = question.value.trim()
  if (text.length < 3 || asking.value) return
  asking.value = true
  askError.value = ''
  reply.value = null
  try {
    reply.value = await ask(text, props.mode)
    if (reply.value.open_support) emit('open-support')
    question.value = ''
    await load()
  } catch (error) {
    askError.value = `The question could not be sent. ${error.message}`
  } finally {
    asking.value = false
  }
}

onMounted(load)
</script>

<template>
  <section aria-labelledby="history-title">
    <h2 id="history-title">Your sessions</h2>
    <p v-if="loading" class="muted">Loading your history...</p>
    <p v-else-if="loadError" class="problem" role="alert">{{ loadError }}</p>
    <p v-else-if="!sessions.length" class="muted">No sessions saved yet.</p>
    <div v-else class="table-wrap">
      <table>
        <caption class="visually-hidden">Saved breathing sessions, newest first</caption>
        <thead>
          <tr><th scope="col">When</th><th scope="col">Length</th><th scope="col">Result</th><th scope="col">Measured</th><th scope="col">Your answer</th></tr>
        </thead>
        <tbody>
          <tr v-for="s in sessions" :key="s.session_id" :data-session-id="s.session_id">
            <td>{{ when(s.started_at) }}</td>
            <td>{{ s.planned_breaths }} breaths</td>
            <td>{{ result(s) }}</td>
            <td>{{ seconds(s.exercise_ms) }}</td>
            <td>{{ ANSWERS[s.self_report] ?? '(skipped)' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <h2 class="ask-title">Ask about your saved sessions</h2>
    <form class="ask" @submit.prevent="submit">
      <label class="visually-hidden" for="ask-input">Question about your saved sessions</label>
      <input id="ask-input" v-model="question" maxlength="300" placeholder="How many times did I finish this week?" autocomplete="off" />
      <button type="submit" class="primary" :disabled="asking">{{ asking ? 'Asking...' : 'Ask' }}</button>
    </form>
    <p class="muted small">Answers come only from your saved records. Optional; nothing here is needed to breathe.</p>
    <p v-if="askError" class="problem" role="alert">{{ askError }}</p>
    <div v-if="reply" class="reply" :class="reply.status" role="status">
      <p>{{ reply.answer }}</p>
      <details v-if="reply.proposed_sql">
        <summary>How this was answered</summary>
        <pre>{{ reply.proposed_sql }}</pre>
        <p v-if="reply.rows.length" class="small">Records: {{ JSON.stringify(reply.rows) }}</p>
      </details>
    </div>

    <h2 v-if="conversations.length" class="ask-title">Questions you asked</h2>
    <ol class="convs">
      <li v-for="c in conversations" :key="c.conversation_id" :data-conversation-id="c.conversation_id">
        <p class="small muted">{{ when(c.started_at) }} · {{ c.conversation_id }}</p>
        <p v-for="m in c.messages.filter((m) => ['question', 'answer', 'error'].includes(m.stage))" :key="m.message_id" class="msg" :class="m.role">
          <strong>{{ m.role === 'user' ? 'You' : m.stage === 'error' ? 'Not answered' : 'Answer' }}:</strong>
          {{ m.stage === 'error' ? `(${m.status}) ${m.content}` : m.content }}
        </p>
      </li>
    </ol>
  </section>
</template>

<style scoped>
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; background: #fff; font-size: 0.92rem; }
th, td { text-align: left; padding: 0.5rem 0.6rem; border-bottom: 1px solid var(--line); }
th { color: var(--muted); font-weight: 600; }
.ask-title { margin-top: 1.6rem; font-size: 1.1rem; }
.ask { display: flex; gap: 0.5rem; }
.ask input { flex: 1; min-width: 0; padding: 0.7rem; border: 1px solid var(--line-strong); border-radius: 10px; font: inherit; }
.reply { margin-top: 0.8rem; padding: 0.8rem 1rem; background: #fff; border-left: 4px solid var(--cue-edge); border-radius: 8px; }
.reply.blocked, .reply.failed, .reply.rejected { border-left-color: var(--warn); }
.reply p { margin: 0 0 0.4rem; }
pre { white-space: pre-wrap; font-size: 0.8rem; background: var(--surface); padding: 0.5rem; border-radius: 6px; }
.convs { list-style: none; padding: 0; display: grid; gap: 0.6rem; }
.convs li { background: #fff; padding: 0.6rem 0.8rem; border-radius: 8px; }
.msg { margin: 0.2rem 0; }
.small { font-size: 0.82rem; }
</style>

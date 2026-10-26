// Every backend call goes through here. Errors come back as ApiError with a readable message.

export class ApiError extends Error {
  constructor(message, code = 'unknown', status = 0) {
    super(message)
    this.code = code
    this.status = status
  }
}

const UNREACHABLE = 'The app could not reach its backend.'

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`/api${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
      signal: options.signal ?? AbortSignal.timeout(30000),
    })
  } catch {
    throw new ApiError(UNREACHABLE, 'network')
  }
  if (!response.ok) {
    let body = null
    try {
      body = await response.json()
    } catch {
      // not JSON
    }
    if (body?.error) throw new ApiError(body.error.message, body.error.code, response.status)
    if (body?.detail) throw new ApiError('That request was not valid.', 'validation', response.status)
    throw new ApiError(response.status >= 500 ? UNREACHABLE : `Request failed (${response.status}).`, 'network', response.status)
  }
  return response.json()
}

export const getIntro = (mode) => request(`/intro?mode=${encodeURIComponent(mode)}`)
export const getPreferences = () => request('/preferences')
export const putPreferences = (prefs) => request('/preferences', { method: 'PUT', body: JSON.stringify(prefs) })
export const startSession = (body) => request('/sessions', { method: 'POST', body: JSON.stringify(body) })
export const finishSession = (id, body) => request(`/sessions/${id}`, { method: 'PATCH', body: JSON.stringify(body) })
export const sendFeedback = (id, selfReport) =>
  request(`/sessions/${id}/feedback`, { method: 'POST', body: JSON.stringify({ self_report: selfReport }) })
export const listSessions = () => request('/sessions')
export const listConversations = () => request('/conversations')
export const ask = (question, mode) => request('/ask', { method: 'POST', body: JSON.stringify({ question, mode }) })

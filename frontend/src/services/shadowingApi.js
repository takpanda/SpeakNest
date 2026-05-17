const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const CATEGORIES = [
  { id: 'daily', name: '日常会話' },
  { id: 'travel', name: '旅行' },
  { id: 'business', name: 'ビジネス' },
  { id: 'tech', name: 'テクノロジー' },
]

export const LEVELS = [
  { id: 'A1', name: 'A1 (初級)' },
  { id: 'A2', name: 'A2 (初中級)' },
  { id: 'B1', name: 'B1 (中級)' },
  { id: 'B2', name: 'B2 (中上級)' },
]

export function getCATEGORIES() {
  return CATEGORIES
}

export function getLEVELS() {
  return LEVELS
}

export async function fetchSentences(category, level) {
  const params = new URLSearchParams()
  if (category) params.set('category', category)
  if (level) params.set('level', level)

  const resp = await fetch(`${API_BASE}/shadowing/sentences?${params.toString()}`)
  if (!resp.ok) {
    throw new Error(`sentences fetch error: ${resp.status}`)
  }
  return resp.json()
}

export async function fetchTtsAudio(text) {
  const resp = await fetch(`${API_BASE}/shadowing/tts?text=${encodeURIComponent(text)}`)
  if (!resp.ok) {
    throw new Error(`TTS error: ${resp.status}`)
  }
  return resp.blob()
}

export async function evaluateShadowing(targetSentence, transcript) {
  const resp = await fetch(`${API_BASE}/shadowing/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_sentence: targetSentence, transcript }),
  })
  if (!resp.ok) {
    throw new Error(`evaluate error: ${resp.status}`)
  }
  return resp.json()
}

export async function saveSession(targetSentence, transcript, wer, feedbackJa) {
  const resp = await fetch(`${API_BASE}/shadowing/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_sentence: targetSentence,
      transcript,
      wer,
      feedback_ja: feedbackJa,
    }),
  })
  if (!resp.ok) {
    throw new Error(`save session error: ${resp.status}`)
  }
  return resp.json()
}

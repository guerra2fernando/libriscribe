import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

// Encode an entity name for a URL path segment while KEEPING "/" as a separator, so names that
// contain slashes (e.g. junk imports like "she/her (unnamed protagonist/android)") work with the
// backend's {name:path} routes. encodeURIComponent alone turns "/" into %2F, which servers reject.
const encPath = (s: string) => String(s).split('/').map(encodeURIComponent).join('/')

// ─── Projects ────────────────────────────────────────────────
export const listProjects = () => api.get('/projects').then(r => r.data)
export const createProject = (data: any) => api.post('/projects', data).then(r => r.data)
export const getProject = (name: string) => api.get(`/projects/${name}`).then(r => r.data)
export const deleteProject = (name: string) => api.delete(`/projects/${name}`)
export const importProject = (body: { bundle: any, target_name?: string }) => api.post('/projects/import', body).then(r => r.data)
export const getProjectProgress = (name: string) => api.get(`/projects/${name}/progress`).then(r => r.data)
export const updateProjectSettings = (name: string, body: { llm_provider?: string, model?: string, utility_model?: string, fallback_chain?: string[] }) => api.put(`/projects/${name}/settings`, body).then(r => r.data)
export const updateProjectMeta = (name: string, body: { title?: string, genre?: string, category?: string, language?: string, description?: string, num_chapters?: number | string, target_word_count?: number | null, logline?: string, tone?: string, target_audience?: string, book_length?: string }) => api.put(`/projects/${name}/meta`, body).then(r => r.data)
export const getActiveModel = (name: string): Promise<{ provider: string, model: string, source: string, configured: boolean, utility_model: string, utility_source: string }> => api.get(`/projects/${name}/active-model`).then(r => r.data)
export const listVersions = (name: string) => api.get(`/projects/${name}/versions`).then(r => r.data)
export const saveVersion = (name: string, body: { label?: string }) => api.post(`/projects/${name}/versions`, body).then(r => r.data)
export const restoreVersion = (name: string, version: number) => api.post(`/projects/${name}/versions/${version}/restore`).then(r => r.data)
export const getProjectStatus = (name: string) => api.get(`/projects/${name}/status`).then(r => r.data)
export const getStats = (name: string) => api.get(`/projects/${name}/stats`).then(r => r.data)
export const previewContext = (name: string, chapterNumber: number) => api.get(`/projects/${name}/preview-context/${chapterNumber}`).then(r => r.data)
export const previewChat = (name: string, body: { message?: string, focus_type?: string | null, focus_name?: string | null, use_references?: boolean }) => api.post(`/projects/${name}/chat/preview`, body).then(r => r.data)
export const getRetrieval = (name: string) => api.get(`/projects/${name}/retrieval`).then(r => r.data)
export const setRetrieval = (name: string, mode: string) => api.put(`/projects/${name}/retrieval`, { mode }).then(r => r.data)

// Reference material (B19)
export const listReferences = (name: string) => api.get(`/projects/${name}/references`).then(r => r.data)
export const uploadReference = (name: string, file: File) => {
  const fd = new FormData()
  fd.append('file', file)
  return api.post(`/projects/${name}/references`, fd).then(r => r.data)
}
export const deleteReference = (name: string, refId: string) => api.delete(`/projects/${name}/references/${refId}`)

// ─── Generation ──────────────────────────────────────────────
export const startGeneration = (name: string, body?: any) => api.post(`/projects/${name}/generate`, body || {}).then(r => r.data)
export const cancelGeneration = (name: string) => api.post(`/projects/${name}/generate/cancel`).then(r => r.data)
export const resumeGeneration = (name: string, body: any) => api.post(`/projects/${name}/generate/resume`, body).then(r => r.data)
export const getCurrentJob = (name: string) => api.get(`/projects/${name}/jobs/current`).then(r => r.data)

// ─── Chapters ────────────────────────────────────────────────
export const listChapters = (name: string) => api.get(`/projects/${name}/chapters`).then(r => r.data)
export const getChapter = (name: string, n: number) => api.get(`/projects/${name}/chapters/${n}`).then(r => r.data)
export const saveChapter = (name: string, n: number, body: any) => api.put(`/projects/${name}/chapters/${n}`, body).then(r => r.data)

// ─── Files ───────────────────────────────────────────────────
export const listFiles = (name: string) => api.get(`/projects/${name}/files`).then(r => r.data)
export const triggerFormat = (name: string) => api.post(`/projects/${name}/format`).then(r => r.data)
export const getCost = (name: string) => api.get(`/projects/${name}/cost`).then(r => r.data)

// ─── Settings ────────────────────────────────────────────────
export const getSettings = () => api.get('/settings').then(r => r.data)
export const updateSettings = (body: any) => api.put('/settings', body).then(r => r.data)
export const getProviders = () => api.get('/settings/providers').then(r => r.data)
export const fetchProviderModels = (body: { provider: string, api_key?: string, base_url?: string }) => api.post('/settings/models', body).then(r => r.data)

// ─── Lorebook ────────────────────────────────────────────────
export const listCharacters = (name: string) => api.get(`/projects/${name}/characters`).then(r => r.data)
export const getCharacter = (name: string, charName: string) => api.get(`/projects/${name}/characters/${encPath(charName)}`).then(r => r.data)
export const createCharacter = (name: string, body: any) => api.post(`/projects/${name}/characters`, body).then(r => r.data)
export const updateCharacter = (name: string, charName: string, body: any) => api.put(`/projects/${name}/characters/${encPath(charName)}`, body).then(r => r.data)
export const deleteCharacter = (name: string, charName: string) => api.delete(`/projects/${name}/characters/${encPath(charName)}`)

export const listLocations = (name: string) => api.get(`/projects/${name}/locations`).then(r => r.data)
export const createLocation = (name: string, body: any) => api.post(`/projects/${name}/locations`, body).then(r => r.data)
export const updateLocation = (name: string, locName: string, body: any) => api.put(`/projects/${name}/locations/${encPath(locName)}`, body).then(r => r.data)
export const deleteLocation = (name: string, locName: string) => api.delete(`/projects/${name}/locations/${encPath(locName)}`)

export const listLoreEntries = (name: string) => api.get(`/projects/${name}/lore`).then(r => r.data)
export const createLoreEntry = (name: string, body: any) => api.post(`/projects/${name}/lore`, body).then(r => r.data)
export const updateLoreEntry = (name: string, entryName: string, body: any) => api.put(`/projects/${name}/lore/${encPath(entryName)}`, body).then(r => r.data)
export const deleteLoreEntry = (name: string, entryName: string) => api.delete(`/projects/${name}/lore/${encPath(entryName)}`)

export const listArcs = (name: string) => api.get(`/projects/${name}/arcs`).then(r => r.data)
export const createArc = (name: string, body: any) => api.post(`/projects/${name}/arcs`, body).then(r => r.data)
export const updateArc = (name: string, arcName: string, body: any) => api.put(`/projects/${name}/arcs/${encPath(arcName)}`, body).then(r => r.data)
export const deleteArc = (name: string, arcName: string) => api.delete(`/projects/${name}/arcs/${encPath(arcName)}`)

export const importLore = (name: string, body: { data: any, smart?: boolean }) => api.post(`/projects/${name}/lore/import`, body).then(r => r.data)
// Smart lore intake (B12 + B13): parse → review → merge
export const parseLore = (name: string, body: { data: any, smart?: boolean }) => api.post(`/projects/${name}/lore/parse`, body).then(r => r.data)
export const parseChat = (name: string, body: { text: string, focus_type?: string | null, focus_name?: string | null }) => api.post(`/projects/${name}/chat/parse`, body).then(r => r.data)
export const parseChatDebug = (name: string, body: { text: string, focus_type?: string | null, focus_name?: string | null }) => api.post(`/projects/${name}/chat/parse/debug`, body).then(r => r.data)
export const applyParsed = (name: string, records: any) => api.post(`/projects/${name}/lore/apply-parsed`, { records }).then(r => r.data)
export const extractFields = (name: string, body: { name: string, content: string, category: string }) => api.post(`/projects/${name}/lore/extract-fields`, body).then(r => r.data)
export const extractFieldsDebug = (name: string, body: { name: string, content: string, category: string, entry_type?: string }) => api.post(`/projects/${name}/lore/extract-fields/debug`, body).then(r => r.data)
export const getWorldbuilding = (name: string) => api.get(`/projects/${name}/worldbuilding`).then(r => r.data)
export const updateWorldbuilding = (name: string, body: any) => api.put(`/projects/${name}/worldbuilding`, body).then(r => r.data)

export const listXref = (name: string) => api.get(`/projects/${name}/xref`).then(r => r.data)
export const searchProject = (name: string, body: any) => api.post(`/projects/${name}/search`, body).then(r => r.data)

export const getOutline = (name: string) => api.get(`/projects/${name}/outline`).then(r => r.data)
export const updateOutline = (name: string, body: any) => api.put(`/projects/${name}/outline`, body).then(r => r.data)
export const listScenes = (name: string, chapterNum: number) => api.get(`/projects/${name}/scenes/${chapterNum}`).then(r => r.data)
export const updateScene = (name: string, chapterNum: number, sceneNum: number, body: any) => api.put(`/projects/${name}/scenes/${chapterNum}/${sceneNum}`, body).then(r => r.data)
export const createScene = (name: string, chapterNum: number, body: any) => api.post(`/projects/${name}/scenes/${chapterNum}`, body).then(r => r.data)
export const deleteScene = (name: string, chapterNum: number, sceneNum: number) => api.delete(`/projects/${name}/scenes/${chapterNum}/${sceneNum}`)

// ─── Lore Sync / Analysis ────────────────────────────────
export const analyzeCharacter = (name: string, charName: string, body?: any) => api.post(`/projects/${name}/analyze/character/${encPath(charName)}`, body || {}).then(r => r.data)
export const analyzeLocation = (name: string, locName: string, body?: any) => api.post(`/projects/${name}/analyze/location/${encPath(locName)}`, body || {}).then(r => r.data)
export const analyzeLoreEntry = (name: string, entryName: string, body?: any) => api.post(`/projects/${name}/analyze/lore/${encPath(entryName)}`, body || {}).then(r => r.data)
export const checkContinuity = (name: string, body?: any) => api.post(`/projects/${name}/analyze/continuity`, body || {}).then(r => r.data)
export const listSuggestions = (name: string, status: string = 'pending') => api.get(`/projects/${name}/suggestions`, { params: { status } }).then(r => r.data)
export const acceptSuggestion = (name: string, idx: number) => api.put(`/projects/${name}/suggestions/${idx}/accept`).then(r => r.data)
export const rejectSuggestion = (name: string, idx: number) => api.put(`/projects/${name}/suggestions/${idx}/reject`).then(r => r.data)
export const editSuggestion = (name: string, idx: number, body: { proposed_value: string }) => api.put(`/projects/${name}/suggestions/${idx}/edit`, body).then(r => r.data)
export const listCharacterStates = (name: string) => api.get(`/projects/${name}/character-states`).then(r => r.data)
export const getCharacterStates = (name: string, charName: string) => api.get(`/projects/${name}/character-states/${encPath(charName)}`).then(r => r.data)
export const listContinuityNotes = (name: string) => api.get(`/projects/${name}/continuity-notes`).then(r => r.data)

// ─── Narrative Threads ──────────────────────────────────
export const listThreads = (name: string) => api.get(`/projects/${name}/threads`).then(r => r.data)
export const createThread = (name: string, body: any) => api.post(`/projects/${name}/threads`, body).then(r => r.data)
export const updateThread = (name: string, threadName: string, body: any) => api.put(`/projects/${name}/threads/${encPath(threadName)}`, body).then(r => r.data)
export const deleteThread = (name: string, threadName: string) => api.delete(`/projects/${name}/threads/${encPath(threadName)}`)

// ─── Outline Regeneration ───────────────────────────────
export const regenerateOutline = (name: string, body: { locked_chapters: number[], regenerate_chapters: number[] }) => api.post(`/projects/${name}/regenerate-outline`, body).then(r => r.data)

// ─── Brainstorm chat (B9) ───────────────────────────────
export const getChat = (name: string) => api.get(`/projects/${name}/chat`).then(r => r.data)
export const clearChat = (name: string) => api.delete(`/projects/${name}/chat`)
// Brainstorm sessions (B18)
export const listSessions = (name: string) => api.get(`/projects/${name}/chat/sessions`).then(r => r.data)
export const createSession = (name: string, body: { title?: string, focus?: any }) => api.post(`/projects/${name}/chat/sessions`, body || {}).then(r => r.data)
export const updateSession = (name: string, sid: string, body: { title?: string, focus?: any, prefs?: any }) => api.patch(`/projects/${name}/chat/sessions/${sid}`, body).then(r => r.data)
export const deleteSession = (name: string, sid: string) => api.delete(`/projects/${name}/chat/sessions/${sid}`)
export const getSession = (name: string, sid: string) => api.get(`/projects/${name}/chat/sessions/${sid}`).then(r => r.data)
export const clearSession = (name: string, sid: string) => api.delete(`/projects/${name}/chat/sessions/${sid}/messages`)
export const applyChat = (name: string, body: { text: string, target_type: string, entity_name: string, smart?: boolean }) => api.post(`/projects/${name}/chat/apply`, body).then(r => r.data)
// Streaming chat uses fetch (axios doesn't stream response bodies in the browser).
export async function streamChat(name: string, message: string, onToken: (t: string) => void, focus?: { type: string, name: string } | null, useReferences: boolean = true, sessionId?: string | null, prefs?: Record<string, any> | null): Promise<void> {
  const res = await fetch(`/api/projects/${name}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, focus_type: focus?.type || null, focus_name: focus?.name || null, use_references: useReferences, session_id: sessionId || null, prefs: prefs || null }),
  })
  if (!res.ok || !res.body) throw new Error(`chat failed (${res.status})`)
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    onToken(decoder.decode(value, { stream: true }))
  }
}

// ─── System (health / ui-state / shutdown) ──────────────
export const getHealth = () => api.get('/health').then(r => r.data)
export const reportUiState = (body: { dirty?: boolean, active_generation?: boolean }) => api.post('/ui-state', body).then(r => r.data)
export const shutdownApp = () => api.post('/shutdown').then(r => r.data)

export default api

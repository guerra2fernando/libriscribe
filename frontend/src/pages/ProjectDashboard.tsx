import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useProject } from '../hooks/useProject'
import { useWebSocket } from '../hooks/useWebSocket'
import { useGenerationStore } from '../store/generationSlice'
import { startGeneration, cancelGeneration, resumeGeneration, listChapters, getCost, updateProjectSettings, updateProjectMeta, fetchProviderModels, getActiveModel, listVersions, saveVersion, restoreVersion, getRetrieval, setRetrieval, getStats } from '../api/client'
import ModelPicker from '../components/ModelPicker'
import { Play, Square, BookOpen, Map, FileText, Download, Save, RefreshCw, Loader2, RotateCcw, Pencil } from 'lucide-react'

const STAGES = ['concept', 'outline', 'characters', 'worldbuilding', 'chapters', 'formatting']
const PROVIDERS = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'claude', label: 'Claude' },
  { value: 'google_ai_studio', label: 'Google AI Studio' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'mistral', label: 'Mistral' },
  { value: 'openrouter', label: 'OpenRouter' },
  { value: 'local', label: 'Local (OpenAI-compatible)' },
]

export default function ProjectDashboard() {
  const { name } = useParams<{ name: string }>()
  const navigate = useNavigate()
  const { project, progress, loading, refresh } = useProject(name)
  const { sendMessage } = useWebSocket(name)
  const { jobStatus, logs, streamBuffer, stageStatuses, pendingReview, reset } = useGenerationStore()
  const [chapters, setChapters] = useState<any[]>([])
  const [cost, setCost] = useState<any>(null)
  const logEndRef = useRef<HTMLDivElement>(null)
  const [llmProvider, setLlmProvider] = useState('openai')
  const [llmModel, setLlmModel] = useState('')
  const [utilityModel, setUtilityModel] = useState('')
  const [llmModels, setLlmModels] = useState<any[]>([])
  const [loadingLlmModels, setLoadingLlmModels] = useState(false)
  const [llmModelError, setLlmModelError] = useState('')
  const [savingLlm, setSavingLlm] = useState(false)
  const [savedLlm, setSavedLlm] = useState(false)
  const [activeModel, setActiveModel] = useState<{ provider: string, model: string, source: string, configured: boolean, utility_model: string, utility_source: string } | null>(null)
  const [versions, setVersions] = useState<any[]>([])
  const [versionLabel, setVersionLabel] = useState('')
  const [savingVersion, setSavingVersion] = useState(false)
  const [retrieval, setRetrievalState] = useState<any>(null)
  const [retMode, setRetMode] = useState('keyword')
  const [savingRet, setSavingRet] = useState(false)
  const [stats, setStats] = useState<any>(null)
  const [showStats, setShowStats] = useState(false)
  const [editingMeta, setEditingMeta] = useState(false)
  const [metaForm, setMetaForm] = useState<any>({})
  const [savingMeta, setSavingMeta] = useState(false)

  const openMetaEditor = () => {
    setMetaForm({
      title: project?.title || '',
      genre: project?.genre || '',
      category: project?.category || '',
      language: project?.language || '',
      description: project?.description || '',
      num_chapters: project?.num_chapters ?? '',
      target_word_count: project?.target_word_count ?? '',
      logline: project?.logline || '',
      tone: project?.tone || '',
      target_audience: project?.target_audience || '',
      book_length: project?.book_length || '',
    })
    setEditingMeta(true)
  }

  const saveMeta = async () => {
    if (!name) return
    setSavingMeta(true)
    try {
      const twc = String(metaForm.target_word_count).trim()
      await updateProjectMeta(name, {
        title: metaForm.title,
        genre: metaForm.genre,
        category: metaForm.category,
        language: metaForm.language,
        description: metaForm.description,
        num_chapters: String(metaForm.num_chapters).trim() || undefined,
        target_word_count: twc === '' ? null : Number(twc),
        logline: metaForm.logline,
        tone: metaForm.tone,
        target_audience: metaForm.target_audience,
        book_length: metaForm.book_length,
      })
      setEditingMeta(false)
      refresh()
    } catch (e: any) {
      alert('Could not save details: ' + (e?.response?.data?.detail || e?.message || 'unknown error'))
    } finally {
      setSavingMeta(false)
    }
  }

  const refreshVersions = () => { if (name) listVersions(name).then(setVersions).catch(() => {}) }
  useEffect(() => { refreshVersions() }, [name])

  useEffect(() => {
    if (!name) return
    getRetrieval(name).then((r: any) => { setRetrievalState(r); setRetMode(r.mode === 'disabled' ? 'keyword' : r.mode) }).catch(() => {})
  }, [name])

  const loadStats = async () => {
    if (!name) return
    setShowStats(true)
    try { setStats(await getStats(name)) } catch { setStats(null) }
  }

  const saveRetrieval = async () => {
    if (!name) return
    setSavingRet(true)
    try {
      const r = await setRetrieval(name, retMode)
      setRetrievalState(r)
      setRetMode(r.mode === 'disabled' ? 'keyword' : r.mode)
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Failed to update search mode')
    } finally {
      setSavingRet(false)
    }
  }

  const doSaveVersion = async () => {
    setSavingVersion(true)
    try {
      await saveVersion(name!, { label: versionLabel })
      setVersionLabel('')
      refreshVersions()
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Failed to save version')
    } finally {
      setSavingVersion(false)
    }
  }

  const doRestore = async (version: number) => {
    const vstr = 'v' + String(version).padStart(3, '0')
    if (!confirm(`Restore to ${vstr}? Your current state is auto-saved as a new version first, so this is reversible.`)) return
    try {
      await restoreVersion(name!, version)
      refresh()
      if (name) listChapters(name).then(setChapters).catch(() => {})
      refreshVersions()
      alert(`Restored to ${vstr}.`)
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Restore failed')
    }
  }

  useEffect(() => { reset() }, [name])

  useEffect(() => {
    if (project) {
      setLlmProvider(project.llm_provider || 'openai')
      setLlmModel(project.model || '')
      setUtilityModel(project.utility_model || '')
    }
  }, [project])

  useEffect(() => {
    if (name) {
      listChapters(name).then(setChapters).catch(() => {})
      getCost(name).then(setCost).catch(() => {})
    }
  }, [name, jobStatus])

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  const refreshActiveModel = () => {
    if (name) getActiveModel(name).then(setActiveModel).catch(() => setActiveModel(null))
  }
  useEffect(() => { refreshActiveModel() }, [name])

  if (loading) return <div className="text-gray-400">Loading...</div>
  if (!project) return <div className="text-red-400">Project not found</div>

  const handleStart = async () => {
    try {
      await startGeneration(name!, { streaming: true })
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Failed to start')
    }
  }

  const handleCancel = async () => {
    try {
      await cancelGeneration(name!)
    } catch {}
  }

  const handleReviewDecision = async (proceed: boolean, applyStyle: boolean) => {
    try {
      await resumeGeneration(name!, { proceed, apply_ai_style: applyStyle })
    } catch {}
  }

  const loadLlmModels = async () => {
    setLoadingLlmModels(true)
    setLlmModelError('')
    try {
      setLlmModels(await fetchProviderModels({ provider: llmProvider }))
    } catch (e: any) {
      const detail = e?.response?.data?.detail
      setLlmModelError(
        detail || (llmProvider === 'local'
          ? 'Could not reach the local server. Set the Server Base URL in Settings and make sure the server is running.'
          : 'Could not load models. Check the provider’s API key in Settings.'),
      )
    } finally {
      setLoadingLlmModels(false)
    }
  }

  const saveLlm = async () => {
    setSavingLlm(true)
    try {
      await updateProjectSettings(name!, { llm_provider: llmProvider, model: llmModel, utility_model: utilityModel })
      setSavedLlm(true)
      setTimeout(() => setSavedLlm(false), 2000)
      refresh()
      refreshActiveModel()
    } catch (e: any) {
      alert(e?.response?.data?.detail || 'Failed to save AI settings')
    } finally {
      setSavingLlm(false)
    }
  }

  const isRunning = jobStatus === 'running'
  const isPaused = jobStatus === 'paused_for_review'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">{project.title}</h1>
          <p className="text-gray-400 text-sm">{project.genre} &middot; {project.category} &middot; {project.language}</p>
          {project.logline && <p className="text-gray-500 text-sm mt-1 italic">{project.logline}</p>}
        </div>
        <div className="flex gap-2 shrink-0">
          <button onClick={openMetaEditor} className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm flex items-center gap-1" title="Edit story details"><Pencil size={14} /> Edit details</button>
          <button onClick={() => navigate(`/projects/${name}/lorebook`)} className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm flex items-center gap-1"><BookOpen size={14} /> Lorebook</button>
          <button onClick={() => navigate(`/projects/${name}/outline`)} className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm flex items-center gap-1"><Map size={14} /> Outline</button>
        </div>
      </div>

      {/* Edit story details modal */}
      {editingMeta && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={() => !savingMeta && setEditingMeta(false)}>
          <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-5 space-y-4" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold">Edit story details</h2>
              <span className="text-xs text-gray-500">id: {project.project_name}</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              <label className="flex flex-col gap-1 sm:col-span-2">
                <span className="text-gray-400">Title</span>
                <input className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5" value={metaForm.title} onChange={e => setMetaForm({ ...metaForm, title: e.target.value })} />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-gray-400">Genre</span>
                <input className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5" value={metaForm.genre} onChange={e => setMetaForm({ ...metaForm, genre: e.target.value })} />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-gray-400">Category</span>
                <input className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5" value={metaForm.category} onChange={e => setMetaForm({ ...metaForm, category: e.target.value })} />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-gray-400">Language</span>
                <input className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5" value={metaForm.language} onChange={e => setMetaForm({ ...metaForm, language: e.target.value })} />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-gray-400">Book length</span>
                <input className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5" value={metaForm.book_length} onChange={e => setMetaForm({ ...metaForm, book_length: e.target.value })} placeholder="e.g. Novel, Novella" />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-gray-400">Target chapters</span>
                <input className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5" value={metaForm.num_chapters} onChange={e => setMetaForm({ ...metaForm, num_chapters: e.target.value })} placeholder="e.g. 12 or 10-14" />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-gray-400">Target word count</span>
                <input type="number" min="0" className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5" value={metaForm.target_word_count} onChange={e => setMetaForm({ ...metaForm, target_word_count: e.target.value })} placeholder="e.g. 80000" />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-gray-400">Tone</span>
                <input className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5" value={metaForm.tone} onChange={e => setMetaForm({ ...metaForm, tone: e.target.value })} />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-gray-400">Target audience</span>
                <input className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5" value={metaForm.target_audience} onChange={e => setMetaForm({ ...metaForm, target_audience: e.target.value })} />
              </label>
              <label className="flex flex-col gap-1 sm:col-span-2">
                <span className="text-gray-400">Logline</span>
                <input className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5" value={metaForm.logline} onChange={e => setMetaForm({ ...metaForm, logline: e.target.value })} placeholder="One-sentence summary" />
              </label>
              <label className="flex flex-col gap-1 sm:col-span-2">
                <span className="text-gray-400">Description</span>
                <textarea rows={3} className="bg-gray-800 border border-gray-700 rounded px-2 py-1.5 resize-y" value={metaForm.description} onChange={e => setMetaForm({ ...metaForm, description: e.target.value })} />
              </label>
            </div>
            <div className="flex justify-end gap-2 pt-1">
              <button onClick={() => setEditingMeta(false)} disabled={savingMeta} className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm disabled:opacity-50">Cancel</button>
              <button onClick={saveMeta} disabled={savingMeta} className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm flex items-center gap-1 disabled:opacity-50">
                {savingMeta ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />} Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Pipeline Stages */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        {STAGES.map(stage => {
          const status = stageStatuses[stage] || progress?.stage_statuses?.[stage] || 'pending'
          const colors: Record<string, string> = {
            complete: 'bg-green-900 border-green-700 text-green-300',
            in_progress: 'bg-indigo-900 border-indigo-700 text-indigo-300 animate-pulse',
            failed: 'bg-red-900 border-red-700 text-red-300',
            skipped: 'bg-gray-800 border-gray-700 text-gray-500',
            pending: 'bg-gray-900 border-gray-800 text-gray-500',
          }
          return (
            <div key={stage} className={`border rounded-lg p-3 text-center text-xs font-medium capitalize ${colors[status] || colors.pending}`}>
              {stage}
              <div className="text-[10px] mt-1 opacity-75">{status}</div>
            </div>
          )
        })}
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3 flex-wrap">
        {!isRunning && !isPaused && (
          <button onClick={handleStart} className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 rounded-lg text-sm font-medium">
            <Play size={16} /> Start Generation
          </button>
        )}
        {isRunning && (
          <button onClick={handleCancel} className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg text-sm font-medium">
            <Square size={16} /> Cancel
          </button>
        )}
        {cost && (
          <span className="text-xs text-gray-500">Session cost: ${cost.total_cost?.toFixed(4) || '0.0000'}</span>
        )}
        <span className="text-xs text-gray-600">Status: {jobStatus}</span>
      </div>

      {/* Human Review Modal */}
      {isPaused && pendingReview && (
        <div className="bg-yellow-900/30 border border-yellow-700 rounded-xl p-5">
          <h3 className="font-semibold text-yellow-300 mb-2">Human Review Required</h3>
          <p className="text-sm text-gray-300 mb-4">{pendingReview.message}</p>
          <div className="flex gap-3">
            <button onClick={() => handleReviewDecision(true, false)} className="px-4 py-2 bg-green-600 hover:bg-green-500 rounded-lg text-sm">Proceed</button>
            <button onClick={() => handleReviewDecision(true, true)} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm">Apply AI Style</button>
          </div>
        </div>
      )}

      {/* Streaming Panel */}
      {streamBuffer && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Live Stream</h3>
          <div className="prose prose-invert max-w-none text-sm whitespace-pre-wrap max-h-64 overflow-y-auto">
            {streamBuffer}
          </div>
        </div>
      )}

      {/* Log Feed */}
      {logs.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h3 className="text-sm font-medium text-gray-400 mb-2">Log ({logs.length})</h3>
          <div className="font-mono text-xs text-gray-400 max-h-48 overflow-y-auto space-y-0.5">
            {logs.map((log, i) => <div key={i}>{log}</div>)}
            <div ref={logEndRef} />
          </div>
        </div>
      )}

      {/* Chapters */}
      {chapters.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Chapters</h3>
          <div className="space-y-1">
            {chapters.map(ch => (
              <div
                key={ch.chapter_number}
                onClick={() => ch.has_content && navigate(`/projects/${name}/chapters/${ch.chapter_number}`)}
                className={`flex items-center justify-between px-3 py-2 rounded-lg text-sm ${ch.has_content ? 'hover:bg-gray-800 cursor-pointer' : 'opacity-50'}`}
              >
                <div className="flex items-center gap-2">
                  <FileText size={14} className={ch.has_content ? 'text-green-400' : 'text-gray-600'} />
                  <span>Ch. {ch.chapter_number}: {ch.title || 'Untitled'}</span>
                </div>
                <span className="text-gray-500 text-xs">{ch.word_count > 0 ? `${ch.word_count} words` : '-'}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI / LLM Configuration */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3">
        <h3 className="text-sm font-medium text-gray-400">AI / LLM Configuration</h3>
        <p className="text-xs text-gray-500">
          Switch the provider or model for this project — e.g. when a model is no longer
          available or useful. API keys / local base URL come from Settings.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <label className="block">
            <span className="text-xs text-gray-400">Provider</span>
            <select
              className="w-full mt-1 px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-sm"
              value={llmProvider}
              onChange={e => setLlmProvider(e.target.value)}
            >
              {PROVIDERS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
            </select>
          </label>
          <label className="block">
            <span className="text-xs text-gray-400">Writing model</span>
            <ModelPicker
              value={llmModel}
              onChange={setLlmModel}
              models={llmModels}
              loading={loadingLlmModels}
              onLoad={loadLlmModels}
              placeholder="leave blank for the provider default"
              error={llmModelError}
            />
            <p className="mt-1 text-xs text-gray-500">Prose, brainstorm chat, chapter generation.</p>
          </label>
          <label className="block">
            <span className="text-xs text-gray-400">Utility model</span>
            <ModelPicker
              value={utilityModel}
              onChange={setUtilityModel}
              models={llmModels}
              loading={loadingLlmModels}
              onLoad={loadLlmModels}
              placeholder="leave blank to use the writing model"
            />
            <p className="mt-1 text-xs text-gray-500">
              Structured tasks — lore extraction & classification. Use a clean instruct model here.
            </p>
          </label>
        </div>
        {activeModel && (
          <div className="text-xs space-y-0.5">
            <div>
              <span className="text-gray-500">Writing: </span>
              <span className="font-medium text-gray-200">{activeModel.model || '(none set)'}</span>
              <span className="text-gray-500">
                {' — '}{activeModel.source === 'project' ? 'this project' : 'provider default (Settings)'}
              </span>
              {!activeModel.configured && (
                <span className="ml-2 text-amber-400">⚠ {activeModel.provider} not configured in Settings</span>
              )}
            </div>
            <div>
              <span className="text-gray-500">Utility: </span>
              <span className="font-medium text-gray-200">{activeModel.utility_model || '(none set)'}</span>
              <span className="text-gray-500">
                {' — '}{activeModel.utility_source === 'utility' ? 'this project' : 'same as writing'}
              </span>
            </div>
          </div>
        )}
        <button
          onClick={saveLlm}
          disabled={savingLlm}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium disabled:opacity-50"
        >
          <Save size={14} /> {savingLlm ? 'Saving...' : savedLlm ? 'Saved!' : 'Save AI Settings'}
        </button>
      </div>

      {/* Search / Retrieval */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3">
        <h3 className="text-sm font-medium text-gray-400">Search (lore retrieval)</h3>
        <p className="text-xs text-gray-500">
          How this book's lore is retrieved for brainstorming and generation. <b>Keyword</b> is
          always available; <b>Semantic</b> and <b>Hybrid</b> need an embedding source (Settings →
          Embeddings) and re-embed the project when applied.
        </p>
        <div className="flex items-end gap-3 flex-wrap">
          <label className="block">
            <span className="text-xs text-gray-400">Mode</span>
            <select
              className="mt-1 px-3 py-1.5 bg-gray-800 border border-gray-700 rounded-lg text-sm"
              value={retMode}
              onChange={e => setRetMode(e.target.value)}
            >
              <option value="keyword">Keyword</option>
              <option value="semantic">Semantic</option>
              <option value="hybrid">Hybrid (keyword + semantic)</option>
            </select>
          </label>
          <button
            onClick={saveRetrieval}
            disabled={savingRet}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium disabled:opacity-50"
          >
            {savingRet ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
            {savingRet ? 'Rebuilding index…' : 'Apply & rebuild index'}
          </button>
        </div>
        {retrieval && (
          <div className="text-xs text-gray-500 space-y-0.5">
            <div>Active: <span className="text-gray-300">{retrieval.mode}</span> · {retrieval.chunk_count} indexed chunks</div>
            {retMode !== 'keyword' && (
              retrieval.embedder_configured
                ? <div className={retrieval.semantic_ready ? 'text-emerald-400/80' : 'text-amber-400/80'}>
                    {retrieval.semantic_ready
                      ? 'Semantic index ready.'
                      : 'Embeddings configured, but the semantic index isn’t built yet — click Apply & rebuild.'}
                  </div>
                : <div className="text-amber-400/80">
                    No embedding source configured — set one in Settings → Embeddings, or semantic/hybrid falls back to keyword.
                  </div>
            )}
          </div>
        )}
      </div>

      {/* Manuscript stats (B14) */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <h3 className="text-sm font-medium text-gray-400">Manuscript stats</h3>
          <button onClick={loadStats} className="flex items-center gap-1 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm">
            <RefreshCw size={14} /> {stats ? 'Refresh' : 'Load stats'}
          </button>
        </div>
        {showStats && !stats && <p className="text-xs text-gray-500">No chapters written yet, or stats unavailable.</p>}
        {stats && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
              {[
                ['Words', (stats.overall.word_count || 0).toLocaleString()],
                ['Chapters', stats.overall.chapter_count || 0],
                ['Reading ease', stats.overall.flesch_reading_ease],
                ['Grade level', stats.overall.flesch_kincaid_grade],
                ['Avg sentence', `${stats.overall.avg_sentence_length}w`],
                ['Dialogue', `${Math.round((stats.overall.dialogue_ratio || 0) * 100)}%`],
                ['Adverbs', `${Math.round((stats.overall.adverb_ratio || 0) * 100)}%`],
                ['Read time', `${Math.round(stats.overall.reading_time_min || 0)} min`],
              ].map(([label, val]: any) => (
                <div key={label} className="bg-gray-800 rounded-lg py-2">
                  <div className="text-sm font-semibold">{val}</div>
                  <div className="text-[10px] text-gray-500 uppercase tracking-wide">{label}</div>
                </div>
              ))}
            </div>
            {stats.chapters?.length > 0 && (() => {
              const maxW = Math.max(...stats.chapters.map((c: any) => c.word_count), 1)
              return (
                <div className="space-y-1">
                  <div className="text-[11px] text-gray-500">Per chapter — length (bar) & reading ease</div>
                  {stats.chapters.map((c: any) => (
                    <div key={c.chapter_number} className="flex items-center gap-2 text-xs">
                      <span className="w-6 text-gray-500 text-right">{c.chapter_number}</span>
                      <div className="flex-1 bg-gray-800 rounded h-4 overflow-hidden">
                        <div className="bg-indigo-700/70 h-full rounded" style={{ width: `${Math.max(3, (c.word_count / maxW) * 100)}%` }} />
                      </div>
                      <span className="w-16 text-gray-400 text-right">{c.word_count.toLocaleString()}w</span>
                      <span className="w-14 text-gray-500 text-right" title="Flesch reading ease">RE {c.flesch_reading_ease}</span>
                    </div>
                  ))}
                </div>
              )
            })()}
            <p className="text-[10px] text-gray-600">Flesch reading ease: higher = easier (60–70 ≈ plain English). Grade = US school grade level. Estimates only.</p>
          </div>
        )}
      </div>

      {/* Versions */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 space-y-3">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <h3 className="text-sm font-medium text-gray-400">Versions</h3>
          <div className="flex items-center gap-2 flex-wrap">
            <input
              value={versionLabel}
              onChange={e => setVersionLabel(e.target.value)}
              placeholder="optional label (e.g. before Act 2 rewrite)"
              className="px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs w-full sm:w-64"
            />
            <button onClick={doSaveVersion} disabled={savingVersion} className="flex items-center gap-1 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm disabled:opacity-50">
              {savingVersion ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />} Save Version
            </button>
          </div>
        </div>
        {versions.length === 0 ? (
          <p className="text-xs text-gray-500">No saved versions yet. Save one to create a restore point — your work, lore, and chapters are snapshotted.</p>
        ) : (
          <div className="space-y-1 max-h-56 overflow-y-auto">
            {versions.map((v: any) => (
              <div key={v.version} className="flex items-center justify-between px-3 py-2 bg-gray-800 rounded text-xs">
                <div>
                  <span className="font-medium">v{String(v.version).padStart(3, '0')}</span>
                  {v.label && <span className="ml-2 text-indigo-300">{v.label}</span>}
                  <span className="ml-2 text-gray-500">{v.created_at ? new Date(v.created_at).toLocaleString() : ''}</span>
                  <div className="text-gray-500 mt-0.5">
                    {v.summary?.chapters ?? 0} ch · {v.summary?.words ?? 0} words · {v.summary?.characters ?? 0} chars · {v.summary?.locations ?? 0} loc · {v.summary?.lore ?? 0} lore · {v.summary?.arcs ?? 0} arcs
                  </div>
                </div>
                <button onClick={() => doRestore(v.version)} title="Roll back to this version" className="flex items-center gap-1 px-2 py-1 bg-gray-700 hover:bg-amber-700 rounded shrink-0">
                  <RotateCcw size={12} /> Restore
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Downloads & Export */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <h3 className="text-sm font-medium text-gray-400 mb-3">Downloads &amp; Export</h3>
        <div className="flex gap-3 flex-wrap">
          <a href={`/api/projects/${name}/export`} className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm flex items-center gap-1" title="Full project bundle (lossless) — re-importable">
            <Download size={14} /> Export Project (.json)
          </a>
          <a href={`/api/projects/${name}/export/story`} className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm flex items-center gap-1" title="The story as plain text (chapters as they stand)">
            <Download size={14} /> Export Story (.txt)
          </a>
          <a href={`/api/projects/${name}/download/manuscript.md`} target="_blank" rel="noopener" className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm flex items-center gap-1">
            <Download size={14} /> manuscript.md
          </a>
          <a href={`/api/projects/${name}/download/manuscript_original.md`} target="_blank" rel="noopener" className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm flex items-center gap-1">
            <Download size={14} /> original.md
          </a>
        </div>
      </div>
    </div>
  )
}

import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { parseChat, parseChatDebug, streamChat, previewChat, listCharacters, listLocations, listLoreEntries, listArcs, listSessions, createSession, updateSession, deleteSession, getSession, clearSession } from '../api/client'
import { useBrainstormStore } from '../store/brainstormSlice'
import LoreProposalReview, { Proposal } from './LoreProposalReview'
import { MessageSquarePlus, X, Send, Trash2, Loader2, Sparkles, Plus, Pencil, Eye } from 'lucide-react'

interface Msg { role: string; content: string }

export default function BrainstormDrawer({ projectName }: { projectName: string }) {
  const navigate = useNavigate()
  const { open, focus, openBrainstorm, close, setFocus } = useBrainstormStore()
  const [messages, setMessages] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [applyFor, setApplyFor] = useState<number | null>(null)
  const [useRefs, setUseRefs] = useState(true)
  const [verbosity, setVerbosity] = useState<'low' | 'medium' | 'high'>('medium')
  const [maxTokens, setMaxTokens] = useState<string>('')
  const [ents, setEnts] = useState<{ character: string[], location: string[], lore: string[], arc: string[] }>({ character: [], location: [], lore: [], arc: [] })
  const [sessions, setSessions] = useState<any[]>([])
  const [activeId, setActiveId] = useState<string | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const endRef = useRef<HTMLDivElement>(null)

  const focusKey = focus ? `${focus.type}:${focus.name}` : ''

  const refreshSessions = () => listSessions(projectName).then(ss => setSessions(ss || [])).catch(() => {})

  // On open: load entities + the session list, and pick an active session.
  useEffect(() => {
    if (!open || !projectName) return
    Promise.all([
      listCharacters(projectName).catch(() => []),
      listLocations(projectName).catch(() => []),
      listLoreEntries(projectName).catch(() => []),
      listArcs(projectName).catch(() => []),
    ]).then(([c, l, lo, a]) => setEnts({
      character: (c || []).map((x: any) => x.name).filter(Boolean),
      location: (l || []).map((x: any) => x.name).filter(Boolean),
      lore: (lo || []).map((x: any) => x.name).filter(Boolean),
      arc: (a || []).map((x: any) => x.name).filter(Boolean),
    })).catch(() => {})
    listSessions(projectName).then((ss: any[]) => {
      setSessions(ss || [])
      setActiveId(prev => (prev && ss.some(s => s.id === prev)) ? prev : (ss[0]?.id || null))
    }).catch(() => {})
  }, [open, projectName])

  // Load the active session's messages + persisted focus.
  useEffect(() => {
    if (!open || !projectName || !activeId) { setMessages([]); return }
    getSession(projectName, activeId).then((s: any) => {
      setMessages(s.messages || [])
      setFocus(s.focus || null)
      setVerbosity((s.prefs?.verbosity as any) || 'medium')
      setMaxTokens(s.prefs?.max_tokens ? String(s.prefs.max_tokens) : '')
      setApplyFor(null)
    }).catch(() => {})
  }, [activeId, open, projectName])

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const send = async () => {
    const text = input.trim()
    if (!text || sending) return
    setInput('')
    setSending(true)
    setMessages(m => [...m, { role: 'user', content: text }, { role: 'assistant', content: '' }])
    try {
      await streamChat(projectName, text, tok => {
        setMessages(m => {
          const copy = m.slice()
          copy[copy.length - 1] = { role: 'assistant', content: copy[copy.length - 1].content + tok }
          return copy
        })
      }, focus, useRefs, activeId, { verbosity, max_tokens: maxTokens ? Number(maxTokens) : undefined })
    } catch (e: any) {
      setMessages(m => {
        const copy = m.slice()
        copy[copy.length - 1] = { role: 'assistant', content: (copy[copy.length - 1].content || '') + `\n[Error: ${e?.message || 'chat failed'}]` }
        return copy
      })
    } finally {
      setSending(false)
      refreshSessions()
    }
  }

  const changeVerbosity = (v: 'low' | 'medium' | 'high') => {
    setVerbosity(v)
    if (activeId) updateSession(projectName, activeId, { prefs: { verbosity: v } }).catch(() => {})
  }

  const commitMaxTokens = () => {
    const n = maxTokens.trim() ? Number(maxTokens) : null
    if (activeId) updateSession(projectName, activeId, { prefs: { max_tokens: n && n > 0 ? n : null } }).catch(() => {})
  }

  const clear = async () => {
    if (!activeId || !confirm("Clear this session's messages?")) return
    try { await clearSession(projectName, activeId) } catch {}
    setMessages([])
    refreshSessions()
  }

  const newSession = async () => {
    const title = prompt('Name this session:', 'New chat')
    if (title === null) return
    try {
      const s = await createSession(projectName, { title: title || 'New chat' })
      await refreshSessions()
      setActiveId(s.id)
      setMessages([])
    } catch {}
  }

  const renameSession = async () => {
    if (!activeId) return
    const cur = sessions.find(s => s.id === activeId)
    const title = prompt('Rename session:', cur?.title || '')
    if (!title) return
    try { await updateSession(projectName, activeId, { title }); await refreshSessions() } catch {}
  }

  const removeSession = async () => {
    if (!activeId || !confirm('Delete this session and its messages?')) return
    try {
      await deleteSession(projectName, activeId)
      const ss = await listSessions(projectName)
      setSessions(ss || [])
      setActiveId(ss[0]?.id || null)
    } catch {}
  }

  const doPreview = async () => {
    try {
      const r = await previewChat(projectName, { message: input, focus_type: focus?.type || null, focus_name: focus?.name || null, use_references: useRefs })
      setPreview(r.system_prompt || '(empty)')
    } catch (e: any) {
      setPreview(`[Preview failed: ${e?.response?.data?.detail || e?.message || 'error'}]`)
    }
  }

  const changeFocus = (v: string) => {
    const nf = v ? { type: v.slice(0, v.indexOf(':')), name: v.slice(v.indexOf(':') + 1) } : null
    setFocus(nf)
    if (activeId) updateSession(projectName, activeId, { focus: nf }).catch(() => {})
  }

  return (
    <>
      {!open && (
        <button
          onClick={() => openBrainstorm()}
          title="Brainstorm with the AI (lore-aware)"
          className="fixed bottom-5 right-5 z-40 flex items-center gap-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-full shadow-lg text-sm font-medium"
        >
          <MessageSquarePlus size={16} /> Brainstorm
        </button>
      )}
      {open && (
        <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[420px] bg-gray-950 border-l border-gray-800 flex flex-col shadow-2xl">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
            <div className="flex items-center gap-2">
              <Sparkles size={16} className="text-indigo-400" />
              <span className="text-sm font-medium">Brainstorm</span>
              <span className="text-xs text-gray-500 truncate max-w-[120px]">{projectName}</span>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={clear} title="Clear conversation" className="text-gray-500 hover:text-red-400 p-1.5"><Trash2 size={15} /></button>
              <button onClick={() => close()} title="Close" className="text-gray-500 hover:text-gray-200 p-1.5 -mr-1"><X size={18} /></button>
            </div>
          </div>

          <div className="px-3 py-2 border-b border-gray-800 flex items-center gap-1.5">
            <select value={activeId || ''} onChange={e => setActiveId(e.target.value)} title="Brainstorm session" className="flex-1 px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs">
              {sessions.map(s => <option key={s.id} value={s.id}>{s.title}{s.message_count ? ` (${s.message_count})` : ''}</option>)}
            </select>
            <button onClick={newSession} title="New session" className="text-gray-400 hover:text-indigo-300 p-1.5"><Plus size={15} /></button>
            <button onClick={renameSession} title="Rename session" className="text-gray-400 hover:text-gray-200 p-1.5"><Pencil size={13} /></button>
            <button onClick={removeSession} title="Delete session" className="text-gray-500 hover:text-red-400 p-1.5"><Trash2 size={14} /></button>
          </div>

          <div className="px-3 py-2 border-b border-gray-800">
            <label className="text-xs text-gray-500 flex items-center gap-2">
              Focus
              <select value={focusKey} onChange={e => changeFocus(e.target.value)} className="flex-1 px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs">
                <option value="">Whole project</option>
                {ents.character.length > 0 && <optgroup label="Characters">{ents.character.map(n => <option key={'character:' + n} value={'character:' + n}>{n}</option>)}</optgroup>}
                {ents.location.length > 0 && <optgroup label="Locations">{ents.location.map(n => <option key={'location:' + n} value={'location:' + n}>{n}</option>)}</optgroup>}
                {ents.lore.length > 0 && <optgroup label="Codex">{ents.lore.map(n => <option key={'lore:' + n} value={'lore:' + n}>{n}</option>)}</optgroup>}
                {ents.arc.length > 0 && <optgroup label="Arcs">{ents.arc.map(n => <option key={'arc:' + n} value={'arc:' + n}>{n}</option>)}</optgroup>}
              </select>
            </label>
            {focus && <p className="text-[11px] text-indigo-400/80 mt-1">Developing {focus.type} "{focus.name}" — draws on the world, arcs &amp; connected lore as context, but only develops this.</p>}
            <label className="text-xs text-gray-500 flex items-center gap-2 mt-2" title="How long and detailed brainstorm responses are">
              Verbosity
              <select value={verbosity} onChange={e => changeVerbosity(e.target.value as any)} className="flex-1 px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs">
                <option value="low">Low — succinct</option>
                <option value="medium">Medium — balanced</option>
                <option value="high">High — detailed</option>
              </select>
            </label>
            <label className="text-xs text-gray-500 flex items-center gap-2 mt-2" title="Max tokens per response. Overrides the verbosity cap when set — raise it if replies get cut off (local models: tokens are free).">
              Response length
              <input type="number" min="0" step="256" value={maxTokens} onChange={e => setMaxTokens(e.target.value)} onBlur={commitMaxTokens}
                placeholder="auto" className="w-24 px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs" />
              <span className="text-[10px] text-gray-600">tokens (blank = verbosity default)</span>
            </label>
            <div className="flex items-center justify-between mt-2">
              <label className="flex items-center gap-1.5 text-[11px] text-gray-400" title="Include imported reference material (Lorebook → References) as background source">
                <input type="checkbox" checked={useRefs} onChange={e => setUseRefs(e.target.checked)} />
                Use reference material
              </label>
              <button onClick={doPreview} title="See the exact prompt (lore + references) the AI will receive" className="flex items-center gap-1 text-[11px] text-gray-500 hover:text-indigo-300">
                <Eye size={12} /> Preview prompt
              </button>
            </div>
          </div>

          {preview !== null && (
            <div className="absolute inset-0 z-10 bg-gray-950/95 flex flex-col p-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-gray-300">Assembled prompt (what the AI receives)</span>
                <button onClick={() => setPreview(null)} title="Close preview" className="text-gray-500 hover:text-gray-200 p-1.5 -m-1"><X size={16} /></button>
              </div>
              <pre className="flex-1 overflow-auto text-[11px] text-gray-300 whitespace-pre-wrap bg-gray-900 border border-gray-800 rounded p-2">{preview}</pre>
              <p className="text-[10px] text-gray-600 mt-2">This is the system prompt (lore context + any reference material) for the current Focus/message — no LLM call was made.</p>
            </div>
          )}

          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {messages.length === 0 && (
              <p className="text-xs text-gray-500 text-center py-8">
                Bounce ideas around — the AI sees this project's lore. Use <b>Apply</b> on a reply
                to turn an idea into a character, location, codex entry, or arc.
              </p>
            )}
            {messages.map((m, i) => (
              <div key={i} className={m.role === 'user' ? 'text-right' : ''}>
                <div className={`inline-block max-w-[90%] text-left px-3 py-2 rounded-lg text-sm whitespace-pre-wrap ${m.role === 'user' ? 'bg-indigo-900/50 border border-indigo-800' : 'bg-gray-800 border border-gray-700'}`}>
                  {m.content || (sending && i === messages.length - 1 ? '…' : '')}
                </div>
                {m.role === 'assistant' && m.content && (
                  <div className="mt-1">
                    <button onClick={() => setApplyFor(applyFor === i ? null : i)} className="text-xs text-indigo-400 hover:text-indigo-300">Apply to lore ▾</button>
                    {applyFor === i && (
                      <ParseApply
                        projectName={projectName}
                        text={m.content}
                        focus={focus}
                        onDone={() => setApplyFor(null)}
                        onView={() => { close(); navigate(`/projects/${projectName}/lorebook`) }}
                      />
                    )}
                  </div>
                )}
              </div>
            ))}
            <div ref={endRef} />
          </div>

          <div className="border-t border-gray-800 p-3">
            <div className="flex gap-2">
              <textarea
                className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm resize-none h-16"
                placeholder="Ask, plan, or brainstorm…  (Enter to send, Shift+Enter for newline)"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() } }}
              />
              <button onClick={send} disabled={sending || !input.trim()} className="px-3 bg-indigo-600 hover:bg-indigo-500 rounded-lg disabled:opacity-50">
                {sending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

// Parse a brainstorm reply into a multi-category proposal, then review & smart-merge it.
// When a Focus is active, the reply is decomposed straight into that entity's full field set (B24).
function ParseApply({ projectName, text, focus, onDone, onView }: { projectName: string, text: string, focus?: { type: string, name: string } | null, onDone: () => void, onView: () => void }) {
  const [proposal, setProposal] = useState<Proposal | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [debug, setDebug] = useState<any>(null)
  const bumpLore = useBrainstormStore(s => s.bumpLore)

  const parse = async () => {
    setBusy(true); setError(''); setProposal(null); setDebug(null)
    try {
      const r = await parseChat(projectName, { text, focus_type: focus?.type || null, focus_name: focus?.name || null })
      setProposal(r.proposal)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Could not parse this reply.')
    } finally {
      setBusy(false)
    }
  }

  const runDebug = async () => {
    setDebug({ loading: true })
    try {
      const r = await parseChatDebug(projectName, { text, focus_type: focus?.type || null, focus_name: focus?.name || null })
      // eslint-disable-next-line no-console
      console.log('[brainstorm apply debug]', r)
      setDebug(r)
    } catch (e: any) {
      setDebug({ error: e?.response?.data?.detail || String(e) })
    }
  }

  useEffect(() => { parse() }, [])

  return (
    <div className="mt-2 p-2 bg-gray-900 border border-gray-700 rounded">
      {busy && <div className="flex items-center gap-2 text-xs text-gray-400 py-2"><Loader2 size={13} className="animate-spin" /> Parsing into lore…</div>}
      {error && (
        <div className="text-xs text-red-400 space-y-2">
          <p>{error}</p>
          <div className="flex gap-2">
            <button onClick={parse} className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded">Retry</button>
            <button onClick={runDebug} className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-amber-300">Debug</button>
            <button onClick={onDone} className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded">Cancel</button>
          </div>
          {debug && (
            <pre className="max-h-64 overflow-auto rounded bg-black/60 border border-gray-700 p-2 text-[10px] text-gray-300 whitespace-pre-wrap break-words">
              {debug.loading ? 'Running diagnostic…' : JSON.stringify(debug, null, 2)}
            </pre>
          )}
        </div>
      )}
      {proposal && (
        <LoreProposalReview projectName={projectName} proposal={proposal} onApplied={() => bumpLore()} onCancel={onDone} onView={onView} />
      )}
    </div>
  )
}

"""Brainstorm chat (B9) — a lore-aware LLM co-writer per project.

- GET    /api/projects/{name}/chat        -> conversation history
- DELETE /api/projects/{name}/chat        -> clear history
- POST   /api/projects/{name}/chat        -> stream an LLM reply (text/plain)
- POST   /api/projects/{name}/chat/apply  -> turn an idea into a draft lore entry

Reuses the project's LLM provider/model, the retrieval index for RAG context, and the
existing lore models / KB save path.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from libriscribe.knowledge_base import Character, Location, LoreEntry, StoryArc
from libriscribe.services.project_service import get_projects_dir, load_kb, save_kb, create_llm_client, create_utility_client
from libriscribe.services.lore_intake import SMART_FIELDS
from libriscribe.utils.token_utils import estimate_tokens

router = APIRouter(prefix="/api/projects", tags=["chat"])
logger = logging.getLogger(__name__)


# ─── Persistence ──────────────────────────────────────────────────────────────

def _chat_path(name: str):
    return get_projects_dir() / name / "chat_history.json"


def _load_chat(name: str) -> list[dict]:
    path = _chat_path(name)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_chat(name: str, messages: list[dict]) -> None:
    path = _chat_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(messages, indent=2), encoding="utf-8")


def _append(name: str, role: str, content: str) -> list[dict]:
    messages = _load_chat(name)
    messages.append({"role": role, "content": content, "ts": datetime.now(timezone.utc).isoformat()})
    _save_chat(name, messages)
    return messages


# ─── Sessions (B18) — named, parallel brainstorm threads per project ───────────
#
# Each session is one JSON file in <project>/chat_sessions/ holding its own history and
# optional persistent Focus. The legacy single chat_history.json is migrated into a default
# "General" session the first time sessions are listed.

def _sessions_dir(name: str):
    return get_projects_dir() / name / "chat_sessions"


def _session_path(name: str, sid: str):
    return _sessions_dir(name) / f"{sid}.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Rolling-memory tuning (per session).
_RECENT_WINDOW_TOKENS = 3000   # recent turns sent verbatim (token-budgeted, replaces the old 12-msg cap)
_SUMMARY_BATCH = 4             # only (re)summarize once this many messages have dropped out of the window
_SUMMARY_CHAR_CAP = 4000       # keep the running summary compact


# ─── Brainstorm preferences, verbosity & collaborator voice (B23 + B26) ───────

def _default_prefs() -> dict:
    """Per-session brainstorm preferences. Extensible — questioning/depth land in later slices."""
    return {"verbosity": "medium"}   # low | medium | high


# Each verbosity level = a response directive + an output-length cap.
_VERBOSITY = {
    "low": {
        "max_tokens": 512,
        "directive": (
            "BE ULTRA-CONCISE: 1-2 sentences or 2-3 tight bullets. Just the ideas — no preamble, "
            "no restating the question, no summary."
        ),
    },
    "medium": {
        "max_tokens": 1200,
        "directive": (
            "BE CONCISE: a few sentences or a short, scannable list (3-5 bullets max). Lead with the "
            "ideas — no long preamble, no restating, no closing summary. Offer a handful of focused "
            "options, not everything. If the author wants depth on one, they'll ask."
        ),
    },
    "high": {
        "max_tokens": 4000,
        "directive": (
            "Be thorough and exploratory: develop each idea with brief reasoning, tradeoffs, and a "
            "concrete example or two. Organize with short headers or bullets when it helps — but "
            "still no filler, flattery, or restating the question."
        ),
    },
}


def _verbosity(prefs: dict | None) -> dict:
    prefs = prefs or {}
    base = _VERBOSITY.get(prefs.get("verbosity", "medium"), _VERBOSITY["medium"])
    # An explicit numeric `max_tokens` pref overrides the tier's cap (tokens are cheap locally).
    override = prefs.get("max_tokens")
    try:
        override = int(override)
    except (TypeError, ValueError):
        override = None
    if override and override > 0:
        return {**base, "max_tokens": min(override, 32000)}
    return base


# Baseline "sharp collaborator" contract (B26) — shared by general and focused brainstorm.
_COLLABORATOR = (
    "You are a sharp creative collaborator for the author — not a sycophant. Build on their idea, be "
    "specific and concrete, and cut filler, hedging, and flattery. Propose a few strong options rather "
    "than everything possible, and name tradeoffs briefly. Clearly flag when something is NEW vs. "
    "already established. If the request is genuinely ambiguous or a key decision is unspecified, ask "
    "ONE targeted clarifying question before guessing."
)

# Per-focus-type "intent lens" (B26): what developing THIS kind of entity actually means.
_INTENT_LENS = {
    "character": (
        "Developing a character means sharpening MOTIVATION (what they want vs. need, fears, drives), "
        "VOICE (how they speak), the CONTRADICTIONS that make them feel real, key RELATIONSHIPS, and "
        "their ARC."
    ),
    "location": (
        "Developing a place means its ATMOSPHERE and sensory texture, its ROLE in the plot, and how "
        "characters use it or are shaped by it."
    ),
    "lore": (
        "Developing lore means INTERNAL CONSISTENCY, its IMPLICATIONS and second-order effects on the "
        "world, and why it MATTERS to the story."
    ),
    "arc": (
        "Developing an arc means STAKES, CAUSALITY (why each turn follows the last), TURNING POINTS, "
        "and CONSEQUENCES that pay off in later chapters."
    ),
}


def _new_session(title: str = "New chat", focus: dict | None = None, prefs: dict | None = None) -> dict:
    return {
        "id": uuid.uuid4().hex[:8],
        "title": (title or "New chat").strip() or "New chat",
        "focus": focus,
        "prefs": prefs or _default_prefs(),
        "created_at": _now(),
        "updated_at": _now(),
        "messages": [],
        "summary": "",           # rolling memory of older turns (this session only)
        "summarized_upto": 0,    # messages[:summarized_upto] are folded into `summary`
    }


def _save_session(name: str, session: dict) -> None:
    d = _sessions_dir(name)
    d.mkdir(parents=True, exist_ok=True)
    _session_path(name, session["id"]).write_text(json.dumps(session, indent=2), encoding="utf-8")


def _load_session(name: str, sid: str) -> dict | None:
    path = _session_path(name, sid)
    if not path.exists():
        return None
    try:
        s = json.loads(path.read_text(encoding="utf-8"))
        s.setdefault("prefs", _default_prefs())  # backfill legacy sessions
        return s
    except Exception:
        return None


def _list_sessions(name: str) -> list[dict]:
    """All sessions, oldest first. Migrates the legacy history / seeds a default on first use."""
    d = _sessions_dir(name)
    sessions: list[dict] = []
    if d.exists():
        for f in d.glob("*.json"):
            try:
                sessions.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                pass
    if not sessions:
        seed = _new_session("General")
        legacy = _load_chat(name)  # migrate old single-thread history if present
        if legacy:
            seed["messages"] = legacy
        _save_session(name, seed)
        sessions = [seed]
    sessions.sort(key=lambda s: (s.get("created_at", ""), s.get("id", "")))  # stable on ties
    return sessions


def _resolve_session(name: str, sid: str | None) -> dict:
    """The requested session, or the default (oldest) one — migrating/seeding as needed."""
    if sid:
        s = _load_session(name, sid)
        if s:
            return s
    return _list_sessions(name)[0]


def _append_message(name: str, session: dict, role: str, content: str) -> None:
    session.setdefault("messages", []).append(
        {"role": role, "content": content, "ts": _now()}
    )
    session["updated_at"] = _now()
    _save_session(name, session)


def _session_meta(s: dict) -> dict:
    return {
        "id": s["id"],
        "title": s.get("title", "Chat"),
        "focus": s.get("focus"),
        "prefs": s.get("prefs") or _default_prefs(),
        "created_at": s.get("created_at"),
        "updated_at": s.get("updated_at"),
        "message_count": len(s.get("messages", [])),
    }


# ─── RAG context ──────────────────────────────────────────────────────────────

def _build_lore_context(name: str, kb, query: str, max_tokens: int = 1800) -> str:
    """Assemble a token-bounded block of established lore relevant to `query`.

    Prefer the retrieval index; fall back to a compact dump of KB entities.
    """
    from libriscribe.services.context_builder import TokenBudget

    budget = TokenBudget(max_tokens)
    parts: list[str] = []
    project_dir = get_projects_dir() / name

    try:
        from libriscribe.services.retrieval_service import search_service_for

        svc = search_service_for(project_dir, kb)
        for r in svc.search(query, mode="keyword", top_k=6):
            text = (getattr(r, "text", "") or "").strip()
            if not text:
                continue
            clipped = budget.consume(text)
            if clipped:
                parts.append(f"- {clipped}")
            if budget.exhausted():
                break
    except Exception:
        logger.debug("Lore retrieval failed; falling back to KB dump", exc_info=True)

    # Supplement / fallback with KB entities.
    def add(label: str, value: str):
        if budget.exhausted() or not value:
            return
        clipped = budget.consume(f"{label}: {value}".strip())
        if clipped:
            parts.append(f"- {clipped}")

    if not parts:
        for c in list(kb.characters.values())[:25]:
            add(f"Character {c.name}", f"{getattr(c, 'role', '')} {getattr(c, 'background', '')}".strip())
        for loc in list(kb.locations.values())[:25]:
            add(f"Location {loc.name}", getattr(loc, "description", ""))
        for e in list(kb.lore_entries.values())[:25]:
            add(f"Lore {e.name}", getattr(e, "description", ""))
        for arc in list(kb.story_arcs.values())[:25]:
            add(f"Arc {arc.name}", getattr(arc, "description", ""))

    return "\n".join(parts)


def _system_prompt(kb, context: str, directive: str) -> str:
    return (
        f"You are a creative worldbuilding and brainstorming partner for the book "
        f"'{kb.title}' ({kb.genre}). Help the author explore ideas, plan story arcs, and "
        f"research before anything is finalized. Stay consistent with the established lore "
        f"below; when you propose something NEW (not already in the lore), say so clearly.\n\n"
        f"{_COLLABORATOR}\n\n"
        f"{directive}\n\n"
        f"=== Established lore ===\n{context or '(none yet)'}\n=== end lore ==="
    )


def _speaker_line(m: dict) -> str:
    speaker = "Author" if m.get("role") == "user" else "Assistant"
    return f"{speaker}: {m.get('content', '')}\n\n"


def _window_start_index(history: list[dict], max_tokens: int) -> int:
    """Index of the first message that fits in the recent token-budgeted window (messages
    from here to the end are sent verbatim; earlier ones roll into the summary)."""
    from libriscribe.utils.token_utils import estimate_tokens

    used = 0
    start = len(history)
    for i in range(len(history) - 1, -1, -1):
        t = estimate_tokens(_speaker_line(history[i]))
        if used + t > max_tokens and start < len(history):
            break
        used += t
        start = i
    return start


def _build_conversation(history: list[dict], start: int = 0) -> str:
    convo = "".join(_speaker_line(m) for m in history[start:])
    convo += "Assistant:"
    return convo


def _summarize_turns(client, kb, prior_summary: str, turns: list[dict]) -> str:
    """Fold a batch of older turns into a compact running summary (one plain-text LLM call)."""
    if client is None or not turns:
        return prior_summary
    convo = "\n".join(_speaker_line(m).strip() for m in turns)
    prompt = (
        f"You are keeping a running memory of a brainstorming conversation for the book "
        f"'{kb.title}' ({kb.genre}). Update the running summary with the new exchange below. Keep "
        "it COMPACT — a short set of bullet points or sentences capturing the ideas, decisions, "
        "names, and open questions that matter for continuity. Merge, don't just append; drop "
        "trivia. Return ONLY the updated summary.\n\n"
        f"RUNNING SUMMARY SO FAR:\n{prior_summary or '(none yet)'}\n\n"
        f"NEW EXCHANGE:\n{convo}\n\nUpdated running summary:"
    )
    try:
        out = client.generate_content(prompt, max_tokens=500, temperature=0.3)
        return (out or prior_summary).strip()[:_SUMMARY_CHAR_CAP]
    except Exception:
        return prior_summary


def _manage_session_memory(name: str, kb, session: dict, client) -> tuple[str, int]:
    """Roll older-than-window turns into the session summary (batched). Returns
    (summary, window_start_index)."""
    history = session.get("messages", [])
    start = _window_start_index(history, _RECENT_WINDOW_TOKENS)
    upto = int(session.get("summarized_upto", 0) or 0)
    if start - upto >= _SUMMARY_BATCH:
        session["summary"] = _summarize_turns(client, kb, session.get("summary", ""), history[upto:start])
        session["summarized_upto"] = start
        _save_session(name, session)
    return session.get("summary", ""), start


def _client_for(kb):
    return create_llm_client(kb)  # Writing model — the brainstorm conversation itself


def _utility_client_for(kb):
    return create_utility_client(kb)  # Utility model — structured lore extraction from a reply


# ─── Endpoints ────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    focus_type: str | None = None  # character | location | lore | arc
    focus_name: str | None = None
    use_references: bool = True
    session_id: str | None = None  # B18: which brainstorm session to append to
    prefs: dict | None = None      # B23: {verbosity: low|medium|high}; falls back to the session's


def _reference_context(name: str, kb, query: str, max_tokens: int = 800) -> str:
    """A token-bounded block of imported reference material relevant to `query` (B19).

    Clearly labelled as source material, NOT canon lore, so the model treats it as
    background/citation rather than established fact."""
    from libriscribe.services.context_builder import TokenBudget

    budget = TokenBudget(max_tokens)
    parts: list[str] = []
    project_dir = get_projects_dir() / name
    try:
        from libriscribe.services.retrieval_service import search_service_for

        svc = search_service_for(project_dir, kb)
        for r in svc.search(query, mode="keyword", top_k=5, filters={"source_type": "reference"}):
            text = (getattr(r, "text", "") or "").strip()
            if not text:
                continue
            clipped = budget.consume(text)
            if clipped:
                parts.append(f"- {clipped}")
            if budget.exhausted():
                break
    except Exception:
        logger.debug("Reference retrieval failed", exc_info=True)
        return ""
    if not parts:
        return ""
    return (
        "=== Reference material (imported sources — use as background/citation, NOT canon "
        "lore; do not treat as established fact) ===\n" + "\n".join(parts)
    )


_FOCUS_STORE = {
    "character": "characters",
    "location": "locations",
    "lore": "lore_entries",
    "arc": "story_arcs",
}


def _get_focus_entity(kb, focus_type: str, focus_name: str):
    attr = _FOCUS_STORE.get(focus_type)
    if not attr:
        return None, focus_name
    store = getattr(kb, attr, {}) or {}
    if focus_name in store:
        return store[focus_name], focus_name
    for key, val in store.items():  # case-insensitive fallback
        if key.lower() == (focus_name or "").lower():
            return val, key
    return None, focus_name


_BRIEF_SOURCES = [
    ("Character", "characters", ("role", "background")),
    ("Location", "locations", ("description",)),
    ("Lore", "lore_entries", ("description",)),
    ("Arc", "story_arcs", ("description",)),
]


def _entity_brief(kb, ename: str):
    """A one-line 'Type Name: desc' summary for any entity, by name (case-insensitive)."""
    target = (ename or "").lower()
    for label, attr, descfields in _BRIEF_SOURCES:
        for key, ent in (getattr(kb, attr, {}) or {}).items():
            if key.lower() == target:
                desc = " ".join(str(getattr(ent, f, "") or "") for f in descfields).strip()
                return f"{label} {key}: {desc}".strip()
    return None


def _focus_context(kb, name: str, focus_type: str, focus_name: str, message: str):
    """Return (resolved_name, entity_record, surrounding_lore) for a focused entity.

    Surrounding lore = the entity's cross-referenced companions/connections, the arcs it
    is involved in, and the world lore — gathered as READ-ONLY background for developing
    the focused entity (the prompt forbids modifying those other records).
    """
    from libriscribe.services.context_builder import TokenBudget

    entity, resolved = _get_focus_entity(kb, focus_type, focus_name)
    if entity is None:
        return None

    budget = TokenBudget(2600)
    lines = [f"{focus_type.title()} '{resolved}':"]
    for k, v in entity.model_dump().items():
        if k == "name" or v in (None, "", [], {}):
            continue
        if isinstance(v, (list, dict)):
            v = json.dumps(v, default=str)
        text = str(v)
        lines.append(f"  - {k}: {text[:400] + '...' if len(text) > 400 else text}")
    record = budget.consume("\n".join(lines))

    surrounding: list[str] = []
    seen = {resolved.lower()}

    def add(line: str):
        if not line or budget.exhausted():
            return
        clipped = budget.consume(line)
        if clipped:
            surrounding.append(f"- {clipped}")

    svc = None
    try:
        from libriscribe.services.retrieval_service import search_service_for

        project_dir = get_projects_dir() / name
        svc = search_service_for(project_dir, kb)
    except Exception:
        svc = None

    # 1) Cross-referenced companions / connected entities (e.g. Manen, Cee).
    if svc is not None:
        try:
            xref = svc.search_cross_references(resolved)
            for rn in (getattr(xref, "related_entities", None) or []):
                if rn.lower() in seen:
                    continue
                brief = _entity_brief(kb, rn)
                if brief:
                    add(brief)
                    seen.add(rn.lower())
                if budget.exhausted():
                    break
        except Exception:
            pass

    # 2) Arcs the focused entity is involved in.
    if focus_type != "arc":
        for an, arc in (kb.story_arcs or {}).items():
            if budget.exhausted():
                break
            involved = [str(x).lower() for x in (getattr(arc, "characters_involved", None) or [])]
            if resolved.lower() in involved and an.lower() not in seen:
                add(f"Arc {an}: {getattr(arc, 'description', '')}")
                seen.add(an.lower())

    # 3) World lore (compact).
    if kb.worldbuilding and not budget.exhausted():
        wb = [f"{k}: {v}" for k, v in kb.worldbuilding.model_dump().items() if isinstance(v, str) and v.strip()]
        if wb:
            add("World — " + " | ".join(wb))

    # 4) Keyword-search supplement seeded by the entity + the question.
    if svc is not None and not budget.exhausted():
        try:
            for r in svc.search(f"{resolved} {message}", mode="keyword", top_k=4):
                if budget.exhausted():
                    break
                text = (getattr(r, "text", "") or "").strip()
                if text:
                    add(text)
        except Exception:
            pass

    return resolved, record, "\n".join(surrounding)


def _focus_system_prompt(kb, focus_type: str, focus_name: str, record: str, surrounding: str, directive: str) -> str:
    lens = _INTENT_LENS.get(focus_type, "")
    lens_block = f"{lens}\n\n" if lens else ""
    return (
        f"You are a creative collaborator for the book '{kb.title}' ({kb.genre}). The author is "
        f"developing the {focus_type} '{focus_name}' and wants to deepen it using the surrounding "
        f"world as context.\n\n"
        f"{_COLLABORATOR}\n\n"
        f"{lens_block}"
        f"Use the SURROUNDING LORE below as background to inform and enrich '{focus_name}' — draw "
        f"on the world, arcs, and connected characters to ground your ideas and keep them "
        f"consistent. But keep EVERY suggestion about '{focus_name}' itself: do NOT develop, "
        f"rewrite, or brainstorm the other entities, and do NOT discuss how changes to "
        f"'{focus_name}' would affect them. They are fixed reference, not the subject.\n\n"
        f"{directive}\n\n"
        f"=== {focus_type.title()} being developed: {focus_name} ===\n{record or '(empty)'}\n\n"
        f"=== Surrounding lore (read-only context) ===\n{surrounding or '(none)'}\n=== end ==="
    )


@router.get("/{name}/chat")
def get_chat(name: str):
    """Back-compat: messages of the default session."""
    if not load_kb(name):
        raise HTTPException(status_code=404, detail="Project not found")
    return _resolve_session(name, None).get("messages", [])


@router.delete("/{name}/chat", status_code=204)
def clear_chat(name: str):
    if not load_kb(name):
        raise HTTPException(status_code=404, detail="Project not found")
    session = _resolve_session(name, None)
    session["messages"] = []
    session["updated_at"] = _now()
    _save_session(name, session)


# ─── Session CRUD (B18) ───────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    title: str | None = None
    focus: dict | None = None
    prefs: dict | None = None


class SessionUpdate(BaseModel):
    title: str | None = None
    focus: dict | None = None
    prefs: dict | None = None


@router.get("/{name}/chat/sessions")
def list_sessions(name: str):
    if not load_kb(name):
        raise HTTPException(status_code=404, detail="Project not found")
    return [_session_meta(s) for s in _list_sessions(name)]


@router.post("/{name}/chat/sessions")
def create_session(name: str, body: SessionCreate):
    if not load_kb(name):
        raise HTTPException(status_code=404, detail="Project not found")
    session = _new_session(body.title or "New chat", body.focus, body.prefs)
    _save_session(name, session)
    return _session_meta(session)


@router.get("/{name}/chat/sessions/{sid}")
def get_session(name: str, sid: str):
    if not load_kb(name):
        raise HTTPException(status_code=404, detail="Project not found")
    session = _load_session(name, sid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/{name}/chat/sessions/{sid}")
def update_session(name: str, sid: str, body: SessionUpdate):
    if not load_kb(name):
        raise HTTPException(status_code=404, detail="Project not found")
    session = _load_session(name, sid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    data = body.model_dump(exclude_unset=True)
    if "title" in data and data["title"] and data["title"].strip():
        session["title"] = data["title"].strip()
    if "focus" in data:
        session["focus"] = data["focus"]
    if "prefs" in data and isinstance(data["prefs"], dict):
        session["prefs"] = {**(session.get("prefs") or _default_prefs()), **data["prefs"]}
    session["updated_at"] = _now()
    _save_session(name, session)
    return _session_meta(session)


@router.delete("/{name}/chat/sessions/{sid}", status_code=204)
def delete_session(name: str, sid: str):
    if not load_kb(name):
        raise HTTPException(status_code=404, detail="Project not found")
    path = _session_path(name, sid)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    path.unlink()  # if this was the last session, listing re-seeds a default "General"


@router.delete("/{name}/chat/sessions/{sid}/messages", status_code=204)
def clear_session(name: str, sid: str):
    if not load_kb(name):
        raise HTTPException(status_code=404, detail="Project not found")
    session = _load_session(name, sid)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session["messages"] = []
    session["summary"] = ""          # reset the rolling memory too
    session["summarized_upto"] = 0
    session["updated_at"] = _now()
    _save_session(name, session)


def _assemble_system_prompt(name, kb, message, focus_type, focus_name, use_references, directive: str | None = None) -> str:
    """Build the exact system prompt the brainstorm chat would send (focus/general + lore
    context + optional reference band). Shared by the live chat and the preview (B15).
    `directive` is the verbosity response directive; defaults to Medium for previews."""
    directive = directive or _VERBOSITY["medium"]["directive"]
    focus = None
    if focus_type and focus_name:
        focus = _focus_context(kb, name, focus_type, focus_name, message)
    if focus:
        resolved, record, related = focus
        system_prompt = _focus_system_prompt(kb, focus_type, resolved, record, related, directive)
    else:
        system_prompt = _system_prompt(kb, _build_lore_context(name, kb, message), directive)
    if use_references:
        refs = _reference_context(name, kb, message)
        if refs:
            system_prompt = system_prompt + "\n\n" + refs
    return system_prompt


class PreviewRequest(BaseModel):
    message: str = ""
    focus_type: str | None = None
    focus_name: str | None = None
    use_references: bool = True


@router.post("/{name}/chat/preview")
def chat_preview(name: str, body: PreviewRequest):
    """Return the fully assembled brainstorm system prompt (lore + references injected) for
    the given message/focus — WITHOUT calling the LLM or touching history (B15)."""
    kb = load_kb(name)
    if not kb:
        raise HTTPException(status_code=404, detail="Project not found")
    system_prompt = _assemble_system_prompt(
        name, kb, body.message or "(no message yet)", body.focus_type, body.focus_name, body.use_references
    )
    return {"system_prompt": system_prompt, "token_estimate": estimate_tokens(system_prompt)}


@router.post("/{name}/chat")
def chat(name: str, body: ChatRequest):
    kb = load_kb(name)
    if not kb:
        raise HTTPException(status_code=404, detail="Project not found")

    session = _resolve_session(name, body.session_id)
    # Verbosity/preferences: prefer what the request sends, else the session's, else the default.
    # Persist so the session remembers (the assistant _append_message below saves it).
    prefs = body.prefs or session.get("prefs") or _default_prefs()
    session["prefs"] = prefs
    vb = _verbosity(prefs)

    _append_message(name, session, "user", body.message)
    history = session["messages"]

    client = _client_for(kb)

    # Rolling per-session memory: recent turns go in verbatim (token-budgeted window); older
    # turns are summarized into this session's running memory and prepended to the prompt.
    memory, window_start = _manage_session_memory(name, kb, session, client)

    system_prompt = _assemble_system_prompt(
        name, kb, body.message, body.focus_type, body.focus_name, body.use_references,
        directive=vb["directive"],
    )
    if memory:
        system_prompt += (
            "\n\n=== Earlier in this conversation (running memory of older turns) ===\n" + memory
        )

    conversation = _build_conversation(history, window_start)

    def generate():
        chunks: list[str] = []
        try:
            for chunk in client.generate_content_streaming(
                conversation, max_tokens=vb["max_tokens"], temperature=0.8, system_prompt=system_prompt
            ):
                chunks.append(chunk)
                yield chunk
        except Exception as exc:  # noqa: BLE001 — surface the error in-stream
            msg = f"\n\n[Error: {exc}]"
            chunks.append(msg)
            yield msg
        _append_message(name, session, "assistant", "".join(chunks))

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


# ─── Apply an idea to lore ────────────────────────────────────────────────────

class ApplyRequest(BaseModel):
    text: str
    target_type: str  # character | location | lore | arc
    entity_name: str
    smart: bool = False


def _extract_fields(kb, target_type: str, text: str, entity_name: str = "") -> dict:
    """Use the LLM to parse an idea into typed fields for a lore entity.

    Delegates to the shared lore extractor so it gets the base system prompt, a concrete JSON
    example, the "sorter" instruction, and robust fenced/preamble-tolerant JSON parsing."""
    from libriscribe.services import lore_intake

    return lore_intake.llm_extract_for_type(
        _utility_client_for(kb), kb.genre, entity_name, text, target_type, book_title=kb.title,
    )


class ParseRequest(BaseModel):
    text: str
    focus_type: str | None = None  # B24: when the session is focused on an entity, decompose the
    focus_name: str | None = None  # reply straight into THAT known entity's full field set


@router.post("/{name}/chat/parse")
def parse_to_proposal(name: str, body: ParseRequest):
    """Parse a brainstorm reply into a reviewable, multi-category lore proposal (B12).

    Extracts characters / locations / lore / arcs with typed fields, annotates each with
    new/update status against the KB, and returns the proposal WITHOUT writing anything. When a
    focus is supplied (B24), the focused entity is decomposed into its full typed field set and
    pre-targeted to the known record, rather than re-classified from scratch.
    """
    kb = load_kb(name)
    if not kb:
        raise HTTPException(status_code=404, detail="Project not found")

    text = (body.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Nothing to parse")

    from libriscribe.services import lore_intake

    client = _utility_client_for(kb)
    if body.focus_type and body.focus_name:
        cats = lore_intake.extract_focused(client, kb, body.focus_type, body.focus_name, text)
    else:
        cats = lore_intake.extract_from_text(client, kb.genre, text, book_title=kb.title)
    if lore_intake.cats_count(cats) == 0:
        raise HTTPException(
            status_code=422,
            detail="Couldn't extract any lore from this reply. Try a more concrete idea, or use the manual editor.",
        )
    return {"proposal": lore_intake.build_proposal(kb, cats)}


@router.post("/{name}/chat/parse/debug")
def parse_to_proposal_debug(name: str, body: ParseRequest):
    """Diagnostic (kept): the model + prompt, the RAW response (with and without the schema), how
    each parses/normalizes, and the final categories — for debugging local-model extraction."""
    from libriscribe.services import lore_intake, lore_prompts
    from libriscribe.utils import structured_output
    from libriscribe.utils.file_utils import parse_llm_json

    kb = load_kb(name)
    if not kb:
        raise HTTPException(status_code=404, detail="Project not found")
    text = (body.text or "").strip()
    client = _utility_client_for(kb)
    prompt = lore_prompts.build_extract_from_text_prompt(kb.genre, kb.title, text)

    def _raw(use_schema: bool):
        try:
            return client.generate_content(
                prompt, max_tokens=3000, temperature=0.3,
                system_prompt=lore_prompts.BASE_SYSTEM_PROMPT,
                json_schema=structured_output.cats_schema() if use_schema else None,
            )
        except Exception as exc:  # noqa: BLE001 — surface the error text for diagnosis
            return f"<<EXCEPTION: {type(exc).__name__}: {exc}>>"

    raw_schema = _raw(True)
    raw_plain = _raw(False)
    focused = None
    if body.focus_type and body.focus_name:
        focused = lore_intake.extract_focused(client, kb, body.focus_type, body.focus_name, text)
    return {
        "provider": kb.llm_provider,
        "model": getattr(client, "model", None),
        "focus": {"type": body.focus_type, "name": body.focus_name} if body.focus_type else None,
        "prompt": prompt,
        "raw_with_schema": raw_schema,
        "normalized_with_schema": lore_intake._normalize_cats(parse_llm_json(raw_schema)),
        "raw_without_schema": raw_plain,
        "normalized_without_schema": lore_intake._normalize_cats(parse_llm_json(raw_plain)),
        "final_cats": focused if focused is not None else lore_intake.extract_from_text(client, kb.genre, text, book_title=kb.title),
    }


@router.post("/{name}/chat/apply")
def apply_to_lore(name: str, body: ApplyRequest):
    kb = load_kb(name)
    if not kb:
        raise HTTPException(status_code=404, detail="Project not found")

    target = body.target_type
    entity_name = body.entity_name.strip()
    if not entity_name:
        raise HTTPException(status_code=400, detail="entity_name is required")
    if target not in SMART_FIELDS:
        raise HTTPException(status_code=400, detail="unsupported target_type")

    fields = _extract_fields(kb, target, body.text, entity_name) if body.smart else {}
    # Draft fallback: put the raw text where it best fits.
    if not fields:
        fields = {"background": body.text} if target == "character" else {"description": body.text}

    def build(model_cls, store: dict):
        allowed = {k: v for k, v in fields.items() if k in model_cls.model_fields}
        try:
            entity = model_cls(name=entity_name, **allowed)
        except Exception:
            # Never fail an apply — fall back to a minimal entity.
            key = "background" if model_cls is Character else "description"
            entity = model_cls(name=entity_name, **{key: body.text})
        store[entity_name] = entity
        return entity

    if target == "character":
        entity = build(Character, kb.characters)
    elif target == "location":
        entity = build(Location, kb.locations)
    elif target == "lore":
        entity = build(LoreEntry, kb.lore_entries)
    else:  # arc
        entity = build(StoryArc, kb.story_arcs)

    save_kb(name, kb)
    return {"target_type": target, "name": entity_name, "entity": entity.model_dump()}

from fastapi import APIRouter, HTTPException

from konsilisyum.bootstrap import AppBootstrapper
from konsilisyum.core.models import SessionStatus, Topic, TopicMode
from konsilisyum.core.session import SessionManager
from konsilisyum.web.schemas import (
    CreateSessionRequest,
    SessionListItem,
    SessionResponse,
)

router = APIRouter()

_sessions: dict[str, AppBootstrapper] = {}
_session_manager = SessionManager()


def get_bootstrapper(session_id: str) -> AppBootstrapper | None:
    return _sessions.get(session_id)


def _register_session(session_id: str) -> AppBootstrapper | None:
    try:
        session = _session_manager.load(session_id)
    except Exception:
        return None

    bootstrapper = AppBootstrapper()
    bootstrapper.session = session
    bootstrapper.session_manager = _session_manager

    from konsilisyum.api.keypool import KeyPool
    from konsilisyum.core.memory import MemoryManager
    from konsilisyum.core.orchestrator import Orchestrator
    from konsilisyum.commands.handler import CommandHandler

    api_keys = bootstrapper.config.get_api_keys()
    if not api_keys:
        fallback = bootstrapper.config.get_mistral_fallback_key()
        if fallback:
            from konsilisyum.core.models import APIKey
            api_keys = [APIKey(id="fallback", key=fallback, is_pool=True)]
        else:
            return None

    key_pool = KeyPool(api_keys)
    api_client = bootstrapper.config.get_llm_client()
    memory = MemoryManager(
        context_window_size=bootstrapper.config.memory.get("context_window_size", 8),
        summary_interval=bootstrapper.config.memory.get("summary_interval", 20),
        memory_update_interval=bootstrapper.config.memory.get("memory_update_interval", 5),
    )

    for msg in session.messages:
        if not msg.is_summary:
            memory.add_message(msg)

    orchestrator = Orchestrator(
        session=session,
        memory=memory,
        api_client=api_client,
        key_pool=key_pool,
        turn_delay=bootstrapper.config.orchestrator.get("turn_delay", 2.0),
        max_auto_turns=bootstrapper.config.orchestrator.get("max_auto_turns", 50),
    )

    cmd_handler = CommandHandler(
        session=session,
        orchestrator=orchestrator,
        memory=memory,
        key_pool=key_pool,
        session_manager=_session_manager,
    )

    bootstrapper.key_pool = key_pool
    bootstrapper.api_client = api_client
    bootstrapper.memory = memory
    bootstrapper.orchestrator = orchestrator
    bootstrapper.cmd_handler = cmd_handler

    session.status = SessionStatus.RUNNING
    _sessions[session_id] = bootstrapper
    return bootstrapper


@router.post("/sessions", response_model=SessionResponse)
async def create_session(req: CreateSessionRequest):
    bootstrapper = AppBootstrapper()
    if not bootstrapper.initialize(req.topic):
        raise HTTPException(status_code=500, detail="Oturum baslatilamadi")

    assert bootstrapper.session is not None
    session = bootstrapper.session
    topic = Topic(content=req.topic, mode=TopicMode.EVOLVE, created_by="kullanici")
    session.topics.append(topic)
    session.current_topic = topic

    _sessions[session.id] = bootstrapper

    return SessionResponse(
        id=session.id,
        name=session.name,
        topic=req.topic,
        status=session.status.value,
        turn=session.current_turn,
        agents=[
            {
                "name": a.name,
                "role": a.role,
                "color": a.color,
                "status": a.status.value,
                "turn_count": a.turn_count,
            }
            for a in session.agents
        ],
    )


@router.get("/sessions", response_model=list[SessionListItem])
async def list_sessions():
    sessions = _session_manager.list_sessions()
    return [
        SessionListItem(
            id=s["id"],
            name=s.get("name", ""),
            created_at=s.get("created_at", ""),
            turn_count=s.get("turn_count", 0),
            status=s.get("status", ""),
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    bootstrapper = _sessions.get(session_id)
    if not bootstrapper:
        raise HTTPException(status_code=404, detail="Oturum bulunamadi")

    assert bootstrapper.session is not None
    session = bootstrapper.session
    return SessionResponse(
        id=session.id,
        name=session.name,
        topic=session.current_topic.content if session.current_topic else "",
        status=session.status.value,
        turn=session.current_turn,
        agents=[
            {
                "name": a.name,
                "role": a.role,
                "color": a.color,
                "status": a.status.value,
                "turn_count": a.turn_count,
            }
            for a in session.agents
        ],
    )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    _sessions.pop(session_id, None)
    meta = _session_manager.sessions_dir / f"{session_id}.json"
    msgs = _session_manager.sessions_dir / f"{session_id}.jsonl"
    meta.unlink(missing_ok=True)
    msgs.unlink(missing_ok=True)
    return {"ok": True}


@router.delete("/sessions")
async def clear_all_sessions():
    import shutil
    _sessions.clear()
    shutil.rmtree(_session_manager.sessions_dir, ignore_errors=True)
    _session_manager.sessions_dir.mkdir(parents=True, exist_ok=True)
    return {"ok": True}

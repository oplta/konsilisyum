from fastapi import APIRouter, HTTPException

from konsilisyum.bootstrap import AppBootstrapper
from konsilisyum.core.models import Topic, TopicMode
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

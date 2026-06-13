from pydantic import BaseModel


class CreateSessionRequest(BaseModel):
    topic: str


class SessionResponse(BaseModel):
    id: str
    name: str
    topic: str
    status: str
    turn: int
    agents: list[dict]


class SessionListItem(BaseModel):
    id: str
    name: str
    created_at: str
    turn_count: int
    status: str


class WSCommand(BaseModel):
    type: str
    cmd: str | None = None
    args: dict | None = None

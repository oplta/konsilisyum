import pytest
from konsilisyum.api.keypool import KeyPool
from konsilisyum.commands.handler import CommandHandler
from konsilisyum.core.memory import MemoryManager
from konsilisyum.core.models import (
    Agent, AgentStatus, APIKey, Message, Session, SessionStatus,
    SpeakerType, Topic, TopicMode,
)
from konsilisyum.core.orchestrator import Orchestrator
from konsilisyum.api.mistral import MistralClient


@pytest.fixture
def setup():
    agents = [
        Agent(name="Atlas", role="Stratejist", goal="Test", blind_spot="Test",
              style="Test", trigger="Test"),
        Agent(name="Mira", role="Etikci", goal="Test", blind_spot="Test",
              style="Test", trigger="Test"),
    ]
    session = Session(agents=agents)
    topic = Topic(content="Test konu")
    session.current_topic = topic
    session.topics.append(topic)

    memory = MemoryManager()
    key_pool = KeyPool([APIKey(id="k1", key="test-key", is_pool=True)])
    api_client = MistralClient()
    orchestrator = Orchestrator(session, memory, api_client, key_pool, turn_delay=0)
    handler = CommandHandler(session, orchestrator, memory, key_pool)

    return handler, session, memory, orchestrator


@pytest.mark.asyncio
async def test_cmd_pause(setup):
    handler, session, _, _ = setup
    result = await handler.handle("pause")
    assert result.success
    assert session.status == SessionStatus.PAUSED

@pytest.mark.asyncio
async def test_cmd_resume(setup):
    handler, session, _, orchestrator = setup
    orchestrator.pause()
    result = await handler.handle("resume")
    assert result.success
    assert session.status == SessionStatus.RUNNING

@pytest.mark.asyncio
async def test_cmd_say(setup):
    handler, session, memory, _ = setup
    result = await handler.handle("say", {"message": "Test mesaj"})
    assert result.success
    assert any(m.content == "Test mesaj" for m in session.messages)

@pytest.mark.asyncio
async def test_cmd_ask(setup):
    handler, session, memory, _ = setup
    result = await handler.handle("ask", {"agent": "Mira", "message": "Ne dusunuyorsun?"})
    assert result.success
    assert any("@Mira" in m.content for m in session.messages)

@pytest.mark.asyncio
async def test_cmd_agents(setup):
    handler, session, _, _ = setup
    result = await handler.handle("agents")
    assert result.success
    assert "Atlas" in result.message
    assert "Mira" in result.message

@pytest.mark.asyncio
async def test_cmd_mute_unmute(setup):
    handler, session, _, _ = setup
    result = await handler.handle("mute", {"agent": "Atlas"})
    assert result.success
    assert session.agents[0].status == AgentStatus.MUTED

    result = await handler.handle("unmute", {"agent": "Atlas"})
    assert result.success
    assert session.agents[0].status == AgentStatus.ACTIVE

@pytest.mark.asyncio
async def test_cmd_kick(setup):
    handler, session, _, _ = setup
    result = await handler.handle("kick", {"agent": "Mira"})
    assert result.success
    assert session.agents[1].status == AgentStatus.REMOVED

@pytest.mark.asyncio
async def test_cmd_spawn(setup):
    handler, session, _, _ = setup
    result = await handler.handle("spawn", {"definition": "Kaan Supheci Bos fikirleri delmek"})
    assert result.success
    assert any(a.name == "Kaan" for a in session.agents)

@pytest.mark.asyncio
async def test_cmd_profile(setup):
    handler, session, _, _ = setup
    result = await handler.handle("profile", {"agent": "Atlas"})
    assert result.success
    assert "Atlas" in result.message
    assert "Stratejist" in result.message

@pytest.mark.asyncio
async def test_cmd_edit(setup):
    handler, session, _, _ = setup
    result = await handler.handle("edit", {"agent": "Atlas", "field": "role", "value": "Vizyoner"})
    assert result.success
    assert session.agents[0].role == "Vizyoner"

@pytest.mark.asyncio
async def test_cmd_topic(setup):
    handler, session, _, _ = setup
    result = await handler.handle("topic", {"topic": "Yeni konu basligi"})
    assert result.success
    assert session.current_topic.content == "Yeni konu basligi"

@pytest.mark.asyncio
async def test_cmd_evolve_focus(setup):
    handler, session, _, _ = setup
    result = await handler.handle("evolve")
    assert result.success
    assert session.current_topic.mode == TopicMode.EVOLVE

    result = await handler.handle("focus")
    assert result.success
    assert session.current_topic.mode == TopicMode.FOCUS

@pytest.mark.asyncio
async def test_cmd_role(setup):
    handler, session, _, _ = setup
    result = await handler.handle("role", {"role": "referee"})
    assert result.success
    from konsilisyum.core.models import UserRole
    assert session.user_role == UserRole.REFEREE

@pytest.mark.asyncio
async def test_cmd_keys(setup):
    handler, session, _, _ = setup
    result = await handler.handle("keys")
    assert result.success
    assert "Toplam: 1" in result.message

@pytest.mark.asyncio
async def test_cmd_status(setup):
    handler, session, _, _ = setup
    result = await handler.handle("status")
    assert result.success
    assert "Test konu" in result.message

@pytest.mark.asyncio
async def test_find_agent_fuzzy(setup):
    handler, session, _, _ = setup
    result = await handler.handle("profile", {"agent": "at"})
    assert result.success  # prefix match "at" -> "Atlas"

@pytest.mark.asyncio
async def test_find_agent_not_found(setup):
    handler, session, _, _ = setup
    result = await handler.handle("profile", {"agent": "YokBoyle"})
    assert not result.success

@pytest.mark.asyncio
async def test_cmd_quit(setup):
    handler, session, _, _ = setup
    result = await handler.handle("quit")
    assert result.should_quit

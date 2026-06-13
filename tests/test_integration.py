"""Integration tests with mocked API calls."""

import json

import httpx
import pytest
import respx

from konsilisyum.api.keypool import KeyPool
from konsilisyum.api.llm import AuthError, RateLimitError, ServerError
from konsilisyum.api.mistral import MistralClient
from konsilisyum.api.providers import AnthropicClient, OllamaClient, OpenAIClient
from konsilisyum.core.memory import MemoryManager
from konsilisyum.core.models import (
    Agent,
    APIKey,
    Message,
    Session,
    SpeakerType,
    Topic,
)
from konsilisyum.core.orchestrator import Orchestrator
from konsilisyum.core.session import SessionManager

MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
OLLAMA_URL = "http://localhost:11434/api/chat"


def mock_mistral_response(content="Bu bir test yanitidir", tokens_in=10, tokens_out=20):
    return {
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": tokens_in, "completion_tokens": tokens_out},
        "model": "mistral-small-latest",
    }


def mock_openai_response(content="This is a test response", tokens_in=10, tokens_out=20):
    return {
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": tokens_in, "completion_tokens": tokens_out},
        "model": "gpt-4o-mini",
    }


def mock_anthropic_response(content="Test response", tokens_in=10, tokens_out=20):
    return {
        "content": [{"text": content, "type": "text"}],
        "usage": {"input_tokens": tokens_in, "output_tokens": tokens_out},
        "model": "claude-3-haiku-20240307",
    }


def mock_ollama_response(content="Local model response"):
    return {
        "message": {"content": content, "role": "assistant"},
        "prompt_eval_count": 10,
        "eval_count": 20,
        "model": "llama3.1",
    }


class TestMistralIntegration:
    @pytest.mark.asyncio
    @respx.mock
    async def test_successful_completion(self):
        respx.post(MISTRAL_URL).mock(
            return_value=httpx.Response(200, json=mock_mistral_response("Test yanit"))
        )
        client = MistralClient(model="mistral-small-latest")
        result = await client.complete(
            system_prompt="Sen bir ajansin",
            user_prompt="Merhaba",
            api_key="test-key",
        )
        assert result.content == "Test yanit"
        assert result.tokens_in == 10
        assert result.tokens_out == 20

    @pytest.mark.asyncio
    @respx.mock
    async def test_rate_limit_handling(self):
        respx.post(MISTRAL_URL).mock(return_value=httpx.Response(429, headers={"retry-after": "1"}))
        client = MistralClient(model="mistral-small-latest")
        with pytest.raises(RateLimitError) as exc_info:
            await client.complete("system", "user", "key")
        assert exc_info.value.retry_after == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_auth_error(self):
        respx.post(MISTRAL_URL).mock(return_value=httpx.Response(401, text="Unauthorized"))
        client = MistralClient(model="mistral-small-latest")
        with pytest.raises(AuthError):
            await client.complete("system", "user", "bad-key")

    @pytest.mark.asyncio
    @respx.mock
    async def test_server_error(self):
        respx.post(MISTRAL_URL).mock(return_value=httpx.Response(500, text="Internal"))
        client = MistralClient(model="mistral-small-latest")
        with pytest.raises(ServerError):
            await client.complete("system", "user", "key")


class TestOpenAIIntegration:
    @pytest.mark.asyncio
    @respx.mock
    async def test_successful_completion(self):
        respx.post(OPENAI_URL).mock(
            return_value=httpx.Response(200, json=mock_openai_response("Hello world"))
        )
        client = OpenAIClient(model="gpt-4o-mini")
        result = await client.complete("system", "user", "test-key")
        assert result.content == "Hello world"


class TestAnthropicIntegration:
    @pytest.mark.asyncio
    @respx.mock
    async def test_successful_completion(self):
        respx.post(ANTHROPIC_URL).mock(
            return_value=httpx.Response(200, json=mock_anthropic_response("Hi there"))
        )
        client = AnthropicClient(model="claude-3-haiku-20240307")
        result = await client.complete("system", "user", "test-key")
        assert result.content == "Hi there"
        assert result.tokens_in == 10
        assert result.tokens_out == 20


class TestOllamaIntegration:
    @pytest.mark.asyncio
    @respx.mock
    async def test_successful_completion(self):
        respx.post(OLLAMA_URL).mock(
            return_value=httpx.Response(200, json=mock_ollama_response("Local response"))
        )
        client = OllamaClient(model="llama3.1")
        result = await client.complete("system", "user", "")
        assert result.content == "Local response"


class TestOrchestratorIntegration:
    @pytest.fixture
    def setup(self):
        agents = [
            Agent(
                name="Atlas",
                role="Stratejist",
                goal="Test goal",
                blind_spot="Test",
                style="Test",
                trigger="Test",
            ),
            Agent(
                name="Mira",
                role="Etikci",
                goal="Test goal",
                blind_spot="Test",
                style="Test",
                trigger="Test",
            ),
        ]
        session = Session(agents=agents)
        topic = Topic(content="Test topic")
        session.current_topic = topic
        session.topics.append(topic)
        memory = MemoryManager()
        key_pool = KeyPool([APIKey(id="k1", key="test-key", is_pool=True)])
        api_client = MistralClient()
        orchestrator = Orchestrator(session, memory, api_client, key_pool, turn_delay=0)
        return orchestrator, session, memory

    @pytest.mark.asyncio
    @respx.mock
    async def test_full_turn_cycle(self, setup):
        orchestrator, session, memory = setup
        respx.post(MISTRAL_URL).mock(
            return_value=httpx.Response(200, json=mock_mistral_response("Birinci yanit"))
        )
        result = await orchestrator.execute_turn()
        assert result.message is not None
        assert result.message.content == "Birinci yanit"
        assert result.message.speaker in ["Atlas", "Mira"]
        assert len(session.messages) == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_user_message_acknowledged(self, setup):
        orchestrator, session, memory = setup
        orchestrator.set_user_message("Bu konuda ne dusunuyorsun?")
        respx.post(MISTRAL_URL).mock(
            return_value=httpx.Response(200, json=mock_mistral_response("Kullanici mesajina yanit"))
        )
        result = await orchestrator.execute_turn()
        assert result.message is not None

    @pytest.mark.asyncio
    @respx.mock
    async def test_pas_response(self, setup):
        orchestrator, session, memory = setup
        respx.post(MISTRAL_URL).mock(
            return_value=httpx.Response(200, json=mock_mistral_response("Pas"))
        )
        result = await orchestrator.execute_turn()
        assert result.is_pas

    @pytest.mark.asyncio
    async def test_auto_pause_max_turns(self, setup):
        orchestrator, session, memory = setup
        session.auto_turns_since_user = 100
        result = await orchestrator.execute_turn()
        assert result.error == "max_auto_turns"

    @pytest.mark.asyncio
    @respx.mock
    async def test_api_error_recovery(self, setup):
        orchestrator, session, memory = setup
        respx.post(MISTRAL_URL).mock(return_value=httpx.Response(500, text="Error"))
        result = await orchestrator.execute_turn()
        assert result.error is not None

    @pytest.mark.asyncio
    @respx.mock
    async def test_multiple_turns(self, setup):
        orchestrator, session, memory = setup
        respx.post(MISTRAL_URL).mock(
            return_value=httpx.Response(200, json=mock_mistral_response("Yanit"))
        )
        for _ in range(3):
            result = await orchestrator.execute_turn()
            if result.error == "max_auto_turns":
                break
        assert session.current_turn >= 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_generate_decisions(self, setup):
        orchestrator, session, memory = setup
        msg = Message(
            turn=1,
            speaker="Atlas",
            content="We should focus on security first",
            speaker_type=SpeakerType.AGENT,
            topic="Test topic",
        )
        memory.add_message(msg)
        session.messages.append(msg)
        respx.post(MISTRAL_URL).mock(
            return_value=httpx.Response(200, json=mock_mistral_response("1. Focus on security"))
        )
        result = await orchestrator.generate_decisions()
        assert result is not None
        assert "security" in result

    @pytest.mark.asyncio
    @respx.mock
    async def test_generate_actions(self, setup):
        orchestrator, session, memory = setup
        msg = Message(
            turn=1,
            speaker="Mira",
            content="We must review the privacy policy",
            speaker_type=SpeakerType.AGENT,
            topic="Test topic",
        )
        memory.add_message(msg)
        session.messages.append(msg)
        respx.post(MISTRAL_URL).mock(
            return_value=httpx.Response(200, json=mock_mistral_response("- Review privacy policy"))
        )
        result = await orchestrator.generate_actions()
        assert result is not None
        assert "privacy" in result

    @pytest.mark.asyncio
    @respx.mock
    async def test_generate_map(self, setup):
        orchestrator, session, memory = setup
        msg = Message(
            turn=1,
            speaker="Kaan",
            content="I disagree with the timeline",
            speaker_type=SpeakerType.AGENT,
            topic="Test topic",
        )
        memory.add_message(msg)
        session.messages.append(msg)
        respx.post(MISTRAL_URL).mock(
            return_value=httpx.Response(
                200, json=mock_mistral_response("Atlas: pro timeline; Mira: against")
            )
        )
        result = await orchestrator.generate_map()
        assert result is not None

    @pytest.mark.asyncio
    async def test_generate_decisions_empty_history(self, setup):
        orchestrator, session, memory = setup
        result = await orchestrator.generate_decisions()
        assert result is None


class TestSessionManagerIntegration:
    @pytest.fixture
    def tmp_sessions_dir(self, tmp_path):
        return str(tmp_path / "sessions")

    def test_save_and_load(self, tmp_sessions_dir):
        agents = [
            Agent(name="Atlas", role="Stratejist", goal="G", blind_spot="B", style="S", trigger="T")
        ]
        topic = Topic(content="Test topic")
        session = Session(agents=agents, current_topic=topic)
        session.topics.append(topic)
        session.messages.append(
            Message(
                turn=1,
                speaker="Atlas",
                content="Test message",
                speaker_type=SpeakerType.AGENT,
                topic="Test topic",
            )
        )

        manager = SessionManager(tmp_sessions_dir)
        manager.save(session)

        loaded = manager.load(session.id)
        assert loaded.name == session.name
        assert len(loaded.agents) == 1
        assert loaded.agents[0].name == "Atlas"
        assert loaded.current_topic.content == "Test topic"
        assert len(loaded.messages) == 1
        assert loaded.messages[0].content == "Test message"

    def test_list_sessions(self, tmp_sessions_dir):
        manager = SessionManager(tmp_sessions_dir)
        session1 = Session(name="Session 1")
        session2 = Session(name="Session 2")
        manager.save(session1)
        manager.save(session2)

        sessions = manager.list_sessions()
        assert len(sessions) == 2

    def test_export_markdown(self, tmp_sessions_dir):
        manager = SessionManager(tmp_sessions_dir)
        session = Session(name="Test Session")
        topic = Topic(content="Test topic")
        session.current_topic = topic
        session.topics.append(topic)
        session.messages.append(
            Message(
                turn=1,
                speaker="Atlas",
                content="Test content",
                speaker_type=SpeakerType.AGENT,
                topic="Test topic",
            )
        )

        md = manager.export(session, "md")
        assert "Test Session" in md
        assert "Atlas" in md
        assert "Test content" in md

    def test_export_jsonl(self, tmp_sessions_dir):
        manager = SessionManager(tmp_sessions_dir)
        session = Session(name="Test")
        topic = Topic(content="Topic")
        session.current_topic = topic
        session.topics.append(topic)
        session.messages.append(
            Message(
                turn=1,
                speaker="Atlas",
                content="Content",
                speaker_type=SpeakerType.AGENT,
                topic="Topic",
            )
        )

        jsonl = manager.export(session, "jsonl")
        lines = jsonl.strip().split("\n")
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["speaker"] == "Atlas"
        assert data["content"] == "Content"

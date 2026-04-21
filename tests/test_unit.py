import pytest
from konsilisyum.core.models import (
    Agent, AgentStatus, Message, SpeakerType, Topic, TopicMode,
    Session, SessionStatus, APIKey, KeyStatus, UserRole,
)
from konsilisyum.commands.parser import parse_input, InputType
from konsilisyum.core.memory import MemoryManager, normalize
from konsilisyum.api.keypool import KeyPool


class TestAgent:
    def test_create_agent(self):
        a = Agent(name="Atlas", role="Stratejist", goal="Test", blind_spot="Test",
                  style="Test", trigger="Test")
        assert a.name == "Atlas"
        assert a.status == AgentStatus.ACTIVE
        assert a.turn_count == 0

    def test_agent_serialization(self):
        a = Agent(name="Atlas", role="Stratejist", goal="Test", blind_spot="Test",
                  style="Test", trigger="Test")
        d = a.to_dict()
        a2 = Agent.from_dict(d)
        assert a2.name == a.name
        assert a2.role == a.role


class TestMessage:
    def test_create_message(self):
        m = Message(turn=1, speaker="Atlas", content="Merhaba",
                    speaker_type=SpeakerType.AGENT, topic="Test")
        assert m.turn == 1
        assert m.speaker == "Atlas"

    def test_message_serialization(self):
        m = Message(turn=1, speaker="Atlas", content="Merhaba",
                    speaker_type=SpeakerType.AGENT, topic="Test")
        d = m.to_dict()
        m2 = Message.from_dict(d)
        assert m2.content == m.content


class TestCommandParser:
    def test_normal_message(self):
        result = parse_input("Merhaba dunya")
        assert result.input_type == InputType.MESSAGE
        assert result.raw == "Merhaba dunya"

    def test_empty_input(self):
        result = parse_input("")
        assert result.input_type == InputType.EMPTY

    def test_pause_command(self):
        result = parse_input("/pause")
        assert result.input_type == InputType.COMMAND
        assert result.command == "pause"

    def test_say_command(self):
        result = parse_input("/say bu bir mesaj")
        assert result.input_type == InputType.COMMAND
        assert result.command == "say"
        assert result.args["message"] == "bu bir mesaj"

    def test_ask_command(self):
        result = parse_input("/ask Mira etik risk ne")
        assert result.input_type == InputType.COMMAND
        assert result.command == "ask"
        assert result.args["agent"] == "Mira"
        assert result.args["message"] == "etik risk ne"

    def test_topic_command(self):
        result = parse_input("/topic yeni konu basligi")
        assert result.command == "topic"
        assert result.args["topic"] == "yeni konu basligi"

    def test_unknown_command_treated_as_message(self):
        result = parse_input("/bilinmeyen arguman")
        assert result.input_type == InputType.MESSAGE

    def test_spawn_command(self):
        result = parse_input("/spawn Nova Yaratici Fikir uretmek")
        assert result.command == "spawn"
        assert "definition" in result.args

    def test_edit_command(self):
        result = parse_input("/edit Atlas role Yeni rol")
        assert result.command == "edit"
        assert result.args["agent"] == "Atlas"
        assert result.args["field"] == "role"
        assert result.args["value"] == "Yeni rol"


class TestMemoryManager:
    def test_add_and_retrieve_messages(self):
        mem = MemoryManager()
        m1 = Message(turn=1, speaker="Atlas", content="Bir", speaker_type=SpeakerType.AGENT, topic="")
        m2 = Message(turn=2, speaker="Mira", content="Iki", speaker_type=SpeakerType.AGENT, topic="")
        mem.add_message(m1)
        mem.add_message(m2)
        assert len(mem.history) == 2

    def test_context_window_size(self):
        mem = MemoryManager(context_window_size=3)
        for i in range(10):
            mem.add_message(Message(turn=i, speaker="Atlas", content=f"Mesaj {i}",
                                    speaker_type=SpeakerType.AGENT, topic=""))
        context = mem.build_context_window()
        lines = [l for l in context.split("\n") if l.startswith("[Tur")]
        assert len(lines) == 3

    def test_agent_memory(self):
        mem = MemoryManager()
        mem.update_agent_memory("agent-1", "- Not 1\n- Not 2\n- Not 3")
        notes = mem.get_agent_memory("agent-1")
        assert "Not 1" in notes

    def test_empty_agent_memory(self):
        mem = MemoryManager()
        notes = mem.get_agent_memory("unknown")
        assert "Henuz" in notes

    def test_repetition_detection(self):
        mem = MemoryManager()
        mem.add_message(Message(turn=1, speaker="Atlas",
                                content="Bu konuda yapay zeka tehlikeli olabilir",
                                speaker_type=SpeakerType.AGENT, topic=""))
        assert mem.detect_repetition("Bu konuda yapay zeka tehlikeli olabilir diye dusunuyorum")

    def test_no_repetition(self):
        mem = MemoryManager()
        mem.add_message(Message(turn=1, speaker="Atlas",
                                content="Ekonomik gostergeler bu ay iyi",
                                speaker_type=SpeakerType.AGENT, topic=""))
        assert not mem.detect_repetition("Tamamen farkli bir konudan bahsetmek istiyorum")

    def test_should_summarize(self):
        mem = MemoryManager(summary_interval=5)
        assert not mem.should_summarize(3)
        assert mem.should_summarize(5)
        assert mem.should_summarize(10)

    def test_get_messages_since(self):
        mem = MemoryManager()
        for i in range(10):
            mem.add_message(Message(turn=i, speaker="Atlas", content=f"M{i}",
                                    speaker_type=SpeakerType.AGENT, topic=""))
        msgs = mem.get_messages_since(7)
        assert len(msgs) == 2


class TestKeyPool:
    def test_assigned_key_priority(self):
        pool = KeyPool([
            APIKey(id="k1", key="key1", assigned_agent="Atlas"),
            APIKey(id="k2", key="key2", is_pool=True),
        ])
        agent = Agent(name="Atlas", role="R", goal="G", blind_spot="B",
                      style="S", trigger="T", api_key_id="k1")
        key = pool.get_key(agent)
        assert key.id == "k1"

    def test_fallback_to_pool(self):
        pool = KeyPool([
            APIKey(id="k1", key="key1", assigned_agent="Atlas"),
            APIKey(id="k2", key="key2", is_pool=True),
        ])
        agent = Agent(name="Mira", role="R", goal="G", blind_spot="B",
                      style="S", trigger="T")
        key = pool.get_key(agent)
        assert key.id == "k2"

    def test_rate_limited_skipped(self):
        pool = KeyPool([
            APIKey(id="k1", key="key1", is_pool=True, status=KeyStatus.RATE_LIMITED),
            APIKey(id="k2", key="key2", is_pool=True),
        ])
        key = pool.get_key()
        assert key.id == "k2"

    def test_no_available_keys(self):
        pool = KeyPool([
            APIKey(id="k1", key="key1", is_pool=True, status=KeyStatus.EXHAUSTED),
        ])
        with pytest.raises(RuntimeError):
            pool.get_key()

    def test_health(self):
        pool = KeyPool([
            APIKey(id="k1", key="key1", is_pool=True),
            APIKey(id="k2", key="key2", is_pool=True, status=KeyStatus.ERROR),
        ])
        h = pool.health()
        assert h["total"] == 2
        assert h["error"] == 1


class TestSession:
    def test_active_agents(self):
        s = Session()
        s.agents = [
            Agent(name="Atlas", role="R", goal="G", blind_spot="B", style="S", trigger="T",
                  status=AgentStatus.ACTIVE),
            Agent(name="Mira", role="R", goal="G", blind_spot="B", style="S", trigger="T",
                  status=AgentStatus.MUTED),
        ]
        assert len(s.active_agents) == 1
        assert s.active_agents[0].name == "Atlas"

    def test_session_serialization(self):
        s = Session(name="Test")
        topic = Topic(content="Test konu")
        s.current_topic = topic
        s.topics.append(topic)
        d = s.to_meta_dict()
        assert d["name"] == "Test"
        assert d["current_topic"]["content"] == "Test konu"


class TestNormalize:
    def test_turkish_normalize(self):
        result = normalize("Yapay zekâ eğitimi için")
        assert "yapay" in result

    def test_stop_words_removed(self):
        result = normalize("Bu bir ve de ama icin")
        assert "bu" not in result
        assert "ve" not in result

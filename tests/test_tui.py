"""Tests for the TUI application."""

from konsilisyum.tui.app import AgentList, KonsilisyumTUI, StatsPanel, TopicInfo


class TestTUIWidgets:
    def test_agent_list_render(self):
        from konsilisyum.core.models import Agent, AgentStatus

        widget = AgentList()
        widget.agents = [
            Agent(
                name="Atlas",
                role="Stratejist",
                goal="G",
                blind_spot="B",
                style="S",
                trigger="T",
                status=AgentStatus.ACTIVE,
            )
        ]
        output = widget.render()
        assert "Atlas" in output
        assert "Stratejist" in output

    def test_topic_info_render(self):
        widget = TopicInfo()
        widget.topic = "Test topic"
        widget.mode = "focus"
        output = widget.render()
        assert "Test topic" in output
        assert "🔒" in output

    def test_stats_panel_render(self):
        widget = StatsPanel()
        widget.turn = 5
        widget.status = "running"
        output = widget.render()
        assert "5" in output
        assert "ÇALIŞIYOR" in output


class TestKonsilisyumTUI:
    def test_initial_topic(self):
        app = KonsilisyumTUI(topic="Test topic")
        assert app._initial_topic == "Test topic"

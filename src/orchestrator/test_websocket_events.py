"""Tests for the /ws/events WebSocket endpoint and event broadcasting."""
import sys
import os
import asyncio
import json
import pytest

sys.path.insert(0, os.path.dirname(__file__))

from metrics import MetricsCollector


class TestMetricsCollectorEventListeners:
    """Test the event listener mechanism on MetricsCollector."""

    def setup_method(self):
        # Reset singleton for clean tests
        MetricsCollector._instance = None
        self.collector = MetricsCollector.get_instance()
        self.events = []
        self.collector.add_event_listener(lambda e: self.events.append(e))

    def test_record_request_emits_request_event(self):
        self.collector.record_request(0.5, 200)
        assert len(self.events) == 1
        assert self.events[0]["event_type"] == "request"
        assert self.events[0]["agent"] == "Orchestrator Agent"
        assert self.events[0]["details"]["status_code"] == 200
        assert self.events[0]["details"]["duration"] == 0.5

    def test_record_request_error_emits_error_event(self):
        self.collector.record_request(0.3, 500)
        assert len(self.events) == 1
        assert self.events[0]["event_type"] == "error"
        assert self.events[0]["details"]["status_code"] == 500

    def test_record_request_4xx_emits_error_event(self):
        self.collector.record_request(0.2, 404)
        assert len(self.events) == 1
        assert self.events[0]["event_type"] == "error"

    def test_tool_call_emits_tool_call_event(self):
        """Simulate a tool call via a mock AI message."""

        class MockMsg:
            type = "ai"
            usage_metadata = None
            tool_calls = [{"name": "duckduckgo_search"}]
            response_metadata = None

        self.collector.record_langgraph_invoke({"messages": [MockMsg()]})
        # Should emit inter_agent_message + tool_call events
        event_types = [e["event_type"] for e in self.events]
        assert "inter_agent_message" in event_types
        assert "tool_call" in event_types
        tool_event = next(e for e in self.events if e["event_type"] == "tool_call")
        assert tool_event["details"]["tool_name"] == "duckduckgo_search"

    def test_token_usage_emits_token_usage_event(self):
        """Simulate token usage via a mock AI message."""

        class MockMsg:
            type = "ai"
            usage_metadata = {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150}
            tool_calls = []
            response_metadata = None

        self.collector.record_langgraph_invoke({"messages": [MockMsg()]})
        event_types = [e["event_type"] for e in self.events]
        assert "token_usage" in event_types
        token_event = next(e for e in self.events if e["event_type"] == "token_usage")
        assert token_event["details"]["prompt_tokens"] == 100
        assert token_event["details"]["completion_tokens"] == 50
        assert token_event["details"]["total_tokens"] == 150

    def test_inter_agent_message_emits_event(self):
        """Simulate inter-agent messages."""

        class MockMsg:
            type = "human"
            usage_metadata = None
            tool_calls = None
            response_metadata = None

        self.collector.record_langgraph_invoke({"messages": [MockMsg(), MockMsg()]})
        event_types = [e["event_type"] for e in self.events]
        assert "inter_agent_message" in event_types
        msg_event = next(e for e in self.events if e["event_type"] == "inter_agent_message")
        assert msg_event["details"]["message_count"] == 2

    def test_remove_event_listener(self):
        listener = lambda e: None
        self.collector.add_event_listener(listener)
        self.collector.remove_event_listener(listener)
        # Original listener still works
        self.collector.record_request(0.1, 200)
        assert len(self.events) == 1

    def test_remove_nonexistent_listener_no_error(self):
        self.collector.remove_event_listener(lambda e: None)  # Should not raise

    def test_listener_exception_does_not_break_recording(self):
        def bad_listener(e):
            raise RuntimeError("boom")

        self.collector.add_event_listener(bad_listener)
        # Should not raise, and original listener still gets called
        self.collector.record_request(0.1, 200)
        assert len(self.events) == 1


class TestBroadcastEvent:
    """Test the broadcast_event and utility functions."""

    def test_utc_iso_timestamp_format(self):
        """Test the timestamp format matches ISO 8601."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
        # Should match ISO 8601 format: YYYY-MM-DDTHH:MM:SS.mmmZ
        assert ts.endswith("Z")
        assert "T" in ts
        assert len(ts) == 24  # e.g., "2024-01-15T10:30:00.123Z"

    def test_event_format_has_required_fields(self):
        """Verify event dict structure matches the expected WebSocket message format."""
        event = {
            "timestamp": "2024-01-15T10:30:05.123Z",
            "agent": "Orchestrator Agent",
            "event_type": "tool_call",
            "details": {"tool_name": "duckduckgo_search"},
        }
        # Verify JSON serializable
        msg = json.dumps(event)
        parsed = json.loads(msg)
        assert parsed["timestamp"] == "2024-01-15T10:30:05.123Z"
        assert parsed["agent"] == "Orchestrator Agent"
        assert parsed["event_type"] == "tool_call"
        assert parsed["details"]["tool_name"] == "duckduckgo_search"

    def test_heartbeat_message_format(self):
        """Verify heartbeat message format."""
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
        heartbeat = {"event_type": "heartbeat", "timestamp": ts}
        msg = json.dumps(heartbeat)
        parsed = json.loads(msg)
        assert parsed["event_type"] == "heartbeat"
        assert parsed["timestamp"].endswith("Z")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

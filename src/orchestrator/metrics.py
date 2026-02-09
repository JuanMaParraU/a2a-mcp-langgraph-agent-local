from __future__ import annotations
import time
import logging
import json
from threading import Lock
from typing import Any, Dict, List, Set, Optional
import statistics

logger = logging.getLogger("metrics")

class MetricsCollector:
    _instance = None
    _lock = Lock()

    def __init__(self):
        self.reset()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = MetricsCollector()
        return cls._instance

    def reset(self):
        self.data = {
            "model": None,
            "requests_total": 0,
            "errors_total": 0,
            "inter_agent_messages": 0,
            "tool_calls": 0,
            "retrievals": 0,
            "tokens_total": 0,
            "submission_latencies": [],
            "throughputs": [],
            "task_durations": [],
            "tokens_completion": 0,
            "latencies": [],
            "tokens_prompt": 0,
            "tools_used": set(),
            "ai_messages_count": 0,
            "reasoning_steps": 0
             }

    # ---------- STARLETTE LAYER ----------
    def record_request(self, duration: float, status_code: int):
        self.data["requests_total"] += 1
        self.data["submission_latencies"].append(duration)

        if status_code >= 400:
            self.data["errors_total"] += 1

    # ---------- EXECUTOR LAYER ----------
    def record_task_duration(self, duration: float):
        self.data["task_durations"].append(duration)


        # ---------- LANGGRAPH LAYER ----------
    def record_langgraph_invoke(self, result, duration: float = None):
        """
        Extract and record metrics from LangGraph / LangChain invoke result.
        Supports dict outputs, lists, tuples, and Message objects.
        """

        if duration is not None:
            self.data["task_durations"].append(duration)

        messages = self._normalize_messages(result)
        self.data["inter_agent_messages"] += len(messages)

        for msg in messages:
            msg_type = getattr(msg, "type", None)
            class_name = msg.__class__.__name__

            is_ai = msg_type == "ai" or class_name in {"AIMessage", "AIMessageChunk"}
            is_tool = msg_type == "tool" or class_name == "ToolMessage"

            if is_ai:
                self._record_ai_message(msg)

            if is_tool:
                tool_name = getattr(msg, "name", None)
                if tool_name:
                    self.data["tools_used"].add(tool_name)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _normalize_messages(self, result: Any) -> List[Any]:
        """Convert invoke output into a flat list of messages."""
        if result is None:
            return []

        if isinstance(result, dict):
            return result.get("messages", []) or []

        if isinstance(result, (list, tuple)):
            return list(result)

        return [result]

    def _record_ai_message(self, msg: Any):
        self.data["ai_messages_count"] += 1
        self.data["reasoning_steps"] += 1

        self._record_token_usage(msg)
        self._record_tool_calls(msg)
        self._record_model_info(msg)

    # ------------------------------------------------------------------
    # Token Usage
    # ------------------------------------------------------------------
    def _record_token_usage(self, msg: Any):
        usage = getattr(msg, "usage_metadata", None)
        if not usage:
            return

        if not isinstance(usage, dict):
            usage = usage.__dict__

        prompt = usage.get("input_tokens", 0) or 0
        completion = usage.get("output_tokens", 0) or 0
        total = usage.get("total_tokens", prompt + completion)

        self.data["tokens_prompt"] += prompt
        self.data["tokens_completion"] += completion
        self.data["tokens_total"] += total

    # ------------------------------------------------------------------
    # Tool Calls
    # ------------------------------------------------------------------
    def _record_tool_calls(self, msg: Any):
        tool_calls = getattr(msg, "tool_calls", None) or []

        for tc in tool_calls:
            self.data["tool_calls"] += 1

            if isinstance(tc, dict):
                name = tc.get("name") or tc.get("tool")
            else:
                name = getattr(tc, "name", None)

            if name:
                self.data["tools_used"].add(name)

    # ------------------------------------------------------------------
    # Model Info
    # ------------------------------------------------------------------
    def _record_model_info(self, msg: Any):
        metadata = getattr(msg, "response_metadata", None)
        if not metadata:
            return

        if not isinstance(metadata, dict):
            metadata = metadata.__dict__

        model = metadata.get("model") or metadata.get("model_name")
        if model:
            self.data["model"] = model


    # ---------- LOGGING ----------
    def summary(self):
        avg_latency = (
            sum(self.data["submission_latencies"]) / len(self.data["submission_latencies"])
            if self.data["submission_latencies"] else 0
        )
        
        avg_task_duration = (
            sum(self.data["task_durations"]) / len(self.data["task_durations"])
            if self.data["task_durations"] else 0
        )
        
        # Convert set to list for JSON serialization
        tools_used_list = list(self.data["tools_used"])

        return {
            **{k: v for k, v in self.data.items() if k != "tools_used"},
            "tools_used": tools_used_list,
            "avg_latency": avg_latency,
            "avg_task_duration": avg_task_duration,
            "tokens_per_request": (
                self.data["tokens_total"] / self.data["requests_total"]
                if self.data["requests_total"] > 0 else 0
            ),
            "tools_per_request": (
                self.data["tool_calls"] / self.data["requests_total"]
                if self.data["requests_total"] > 0 else 0
            )
        }

    def log_summary(self):
        logger.info(json.dumps(self.summary(), indent=2))

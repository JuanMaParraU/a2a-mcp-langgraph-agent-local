import time
import logging
import json
from threading import Lock

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
            "task_durations": []
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
    
    # ---------- LOGGING ----------
    def summary(self):
        avg_submission = (
            sum(self.data["submission_latencies"]) / len(self.data["submission_latencies"])
            if self.data["submission_latencies"] else 0
        )

        avg_task = (
            sum(self.data["task_durations"]) / len(self.data["task_durations"])
            if self.data["task_durations"] else 0
        )

        return {
            **self.data,
            "avg_a2a_submission_latency": avg_submission,
            "avg_task_duration": avg_task
        }

    def log_summary(self):
        logger.info(json.dumps(self.summary(), indent=2))

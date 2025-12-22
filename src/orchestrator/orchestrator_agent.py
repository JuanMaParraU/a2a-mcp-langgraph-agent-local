import os
import logging
from typing import Any, Literal, TypedDict
from pydantic import BaseModel
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langchain.schema import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig

os.environ["NO_PROXY"] = "127.0.0.1,localhost"
logger = logging.getLogger(__name__)

memory = MemorySaver()

# ------------------------------
# Schemas
# ------------------------------
class ResponseFormat(BaseModel):
    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str

class OrchestratorState(TypedDict):
    user_input: str
    plan: str | None
    needs_delegation: bool
    delegated_result: str | None
    final_response: str | None

# ------------------------------
# Agent
# ------------------------------
class OrchestratorAgent:
    SYSTEM_INSTRUCTION = """
    You are an orchestrator agent.
    Decide whether to answer directly or delegate to another agent.
    """

    def __init__(self):
        self.model = ChatOllama(model="mistral-nemo", temperature=0)

    async def plan(self, state: OrchestratorState) -> OrchestratorState:
        needs_delegation = any(
            k in state["user_input"].lower()
            for k in ["research", "search", "wikipedia", "paper"]
        )
        plan_text = "Delegate to a research agent." if needs_delegation else "Answer directly."
        return {**state, "plan": plan_text, "needs_delegation": needs_delegation}

    async def synthesize(self, state: OrchestratorState) -> OrchestratorState:
        if state.get("delegated_result"):
            final = f"Synthesized answer:\n{state['delegated_result']}"
        else:
            messages = [HumanMessage(content=state["user_input"])]
            response = await self.model.ainvoke(messages)
            # ChatOllama returns a ChatResult-like object
            final = getattr(response, "content", str(response))
        return {**state, "final_response": final}

# ------------------------------
# Graph
# ------------------------------
class OrchestratorGraph:
    def __init__(self, agent: OrchestratorAgent):
        self.agent = agent

    async def delegate(self, state: OrchestratorState) -> OrchestratorState:
        # Stub: replace with real A2A client call later
        delegated_result = "Result from delegated agent (stub)."
        return {**state, "delegated_result": delegated_result}

    def build(self):
        graph = StateGraph(OrchestratorState)
        graph.add_node("plan", self.agent.plan)
        graph.add_node("delegate", self.delegate)
        graph.add_node("synthesize", self.agent.synthesize)
        graph.set_entry_point("plan")
        graph.add_conditional_edges(
            "plan",
            lambda state: state["needs_delegation"],
            {True: "delegate", False: "synthesize"},
        )
        graph.add_edge("delegate", "synthesize")
        graph.add_edge("synthesize", END)
        return graph.compile(checkpointer=memory)

# ------------------------------
# Orchestrator wrapper
# ------------------------------
class Orchestrator:
    def __init__(self):
        self.agent = OrchestratorAgent()
        self.graph = OrchestratorGraph(self.agent).build()

    async def invoke(self, query: str, context_id: str):
        config = {"configurable": {"thread_id": context_id}}
        result = await self.graph.ainvoke({"user_input": query}, config)
        return {
            "is_task_complete": True,
            "require_user_input": False,
            "content": result.get("final_response", ""),
        }



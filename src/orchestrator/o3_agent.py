import os
import logging
from typing import Any, Literal, TypedDict
from pydantic import BaseModel
import httpx
import uuid
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langchain.schema import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from a2a.client.client_factory import ClientFactory
from a2a.client.client import ClientConfig
from a2a.client import A2ACardResolver
from a2a.types import AgentCard, Message, Part, Role, TextPart
from metrics import MetricsCollector
from langchain_core.messages import message_to_dict
import time

os.environ["NO_PROXY"] = "127.0.0.1,localhost,10.215.130.20"
logger = logging.getLogger(__name__)
Research_agent_url = "http://localhost:9991"

# HTTP client timeout configuration
timeout_config = httpx.Timeout(
    connect=30.0,
    read=120.0,
    write=10.0,
    pool=5.0,
)


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
    You are an orchestrator agent. Answer concisely and directly.
    Decide whether to answer directly or delegate to another agent.
    """

    def __init__(self):
        self.llm = "mistral:latest"
        self.model = ChatOllama(base_url="http://10.215.130.20:11434", model=self.llm, temperature=0)
        metrics = MetricsCollector.get_instance()
        metrics.data["model"] = self.llm

    async def plan(self, state: OrchestratorState) -> OrchestratorState:
        needs_delegation = any(
            k in state["user_input"].lower()
            for k in ["research", "search", "wikipedia", "paper"]
        )
        plan_text = "Delegate to a research agent." if needs_delegation else "Answer directly."
        logger.info(plan_text)
        return {**state, "plan": plan_text, "needs_delegation": needs_delegation}

    async def synthesize(self, state: OrchestratorState) -> OrchestratorState:
        if state.get("delegated_result"):
            final = f"Synthesized answer:\n{state['delegated_result']}"
        else:
            messages = [HumanMessage(content=state["user_input"])]
            metrics = MetricsCollector.get_instance()
            start = time.time()
            response = await self.model.ainvoke(messages)
            duration = time.time() - start
            logger.info(f"---------------: {message_to_dict(response)}")
            #metrics.data["throughputs"].append(len(str(response)) / duration)  # tokens/sec approx
            #metrics.data["tokens_total"] += getattr(response, "tokens_used", len(str(response))) 
            metrics.record_langgraph_invoke(response, duration)
            # ChatOllama returns a ChatResult-like object
            final = getattr(response, "content", str(response))
        return {**state, "final_response": final}


async def run_a2a_with_print(client: Any, message: Any) -> str:
    """
    Collects the final artifact from the research agent.
    Status messages are printed for visibility but only the artifact
    (final answer) is returned as the delegated result.
    """
    seen_content = set()
    has_content = False
    artifact_buffer: list[str] = []

    try:
        response = client.send_message(message)

        async for task, event in response:
            # --- Print status messages for visibility but don't include in result ---
            if hasattr(event, "status") and event.status and hasattr(event.status, "message") and event.status.message:
                for part in event.status.message.parts:
                    if hasattr(part.root, "text"):
                        content = part.root.text
                        if content and content not in seen_content:
                            print(content, end="", flush=True)
                            seen_content.add(content)

            # --- Collect artifact (final answer) into the result buffer ---
            if hasattr(event, "artifact") and event.artifact:
                artifact = event.artifact
                for part in artifact.parts:
                    if hasattr(part.root, "text"):
                        content = part.root.text
                        if content and content not in seen_content:
                            print(content, end="", flush=True)
                            artifact_buffer.append(content)
                            seen_content.add(content)
                            has_content = True

            # --- Check for plural artifacts (if present) ---
            if hasattr(event, "artifacts") and event.artifacts:
                for artifact in event.artifacts:
                    for part in artifact.parts:
                        if hasattr(part.root, "text"):
                            content = part.root.text
                            if content and content not in seen_content:
                                print(content, end="", flush=True)
                                artifact_buffer.append(content)
                                seen_content.add(content)
                                has_content = True

        if has_content:
            print("\n", end="")

    except Exception as e:
        # Re-raise so your caller can handle it like you do elsewhere
        raise RuntimeError(f"❌ Failed to connect to agent: {e}")

    return "".join(artifact_buffer).strip()

# ------------------------------
# Graph
# ------------------------------
class OrchestratorGraph:
    def __init__(self, agent: OrchestratorAgent):
        self.agent = agent
        self.httpx_client = httpx.AsyncClient(timeout=timeout_config)
    async def delegate(self, state: OrchestratorState) -> OrchestratorState:
        metrics = MetricsCollector.get_instance()
        metrics.data["inter_agent_messages"] += 1   
        metrics.data["retrievals"] += 1   
        # Stub: replace with real A2A client call later
        delegated_result = "Result from delegated agent (stub)."
            # Initialize agent card resolver
        resolver = A2ACardResolver(httpx_client=self.httpx_client, base_url=Research_agent_url)

        try:
            agent_card: AgentCard = await resolver.get_agent_card()
            logger.info(f"✅ Connected to agent at {Research_agent_url}")
        except Exception as e:
            raise RuntimeError(f"❌ Failed to connect to agent: {e}")

        # Initialize the A2A client
        config = ClientConfig(httpx_client=self.httpx_client)
        factory = ClientFactory(config)
        client = factory.create(agent_card)
        message = Message(
                    role=Role.user,
                    messageId=str(uuid.uuid4()),
                    parts=[Part(root=TextPart(text=state["user_input"]))],
                )
        try:
            logger.info(f" Sending message to agent: {message}")
            delegated_result = await run_a2a_with_print(client, message)
            logger.info(f" Received delegated result: {delegated_result}")
        except Exception as e:
            raise RuntimeError(f"❌ Failed to send message to agent: {e}")
        
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



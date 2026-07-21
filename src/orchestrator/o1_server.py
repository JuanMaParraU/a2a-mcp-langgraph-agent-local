import uvicorn
import logging
import os
import asyncio
from datetime import datetime, timezone
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware
# point executor orchestratoe
from o2_executor import OrchestratorExecutor
from metrics_middleware import MetricsMiddleware
from metrics import MetricsCollector
import threading
import time
import signal
import atexit
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORS configuration - DASHBOARD_ORIGIN takes precedence, falls back to CORS_ORIGIN for backward compat
CORS_ORIGIN = os.environ.get("DASHBOARD_ORIGIN", os.environ.get("CORS_ORIGIN", "http://localhost:3000"))

# WebSocket connected clients tracking
connected_clients: set[WebSocket] = set()


def _cors_headers() -> dict:
    """Return CORS headers for the /metrics endpoint."""
    return {
        "Access-Control-Allow-Origin": CORS_ORIGIN,
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }


def _utc_iso_timestamp() -> str:
    """Return current UTC time as ISO 8601 string."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


async def broadcast_event(event_data: dict) -> None:
    """Broadcast an event to all connected WebSocket clients.

    Sends the event as a JSON message to each connected client.
    Disconnected clients are removed from the set silently.
    """
    if not connected_clients:
        return

    # Ensure timestamp is present
    if "timestamp" not in event_data:
        event_data["timestamp"] = _utc_iso_timestamp()

    message = json.dumps(event_data)
    disconnected = set()

    for client in connected_clients.copy():
        try:
            await client.send_text(message)
        except Exception:
            disconnected.add(client)

    # Clean up disconnected clients
    connected_clients.difference_update(disconnected)


async def websocket_events_endpoint(websocket: WebSocket) -> None:
    """WebSocket /ws/events - Stream agent activity events with heartbeat."""
    await websocket.accept()
    connected_clients.add(websocket)
    logger.info(f"WebSocket client connected. Total clients: {len(connected_clients)}")

    async def heartbeat():
        """Send heartbeat every 15 seconds."""
        try:
            while True:
                await asyncio.sleep(15)
                heartbeat_msg = json.dumps({
                    "event_type": "heartbeat",
                    "timestamp": _utc_iso_timestamp(),
                })
                await websocket.send_text(heartbeat_msg)
        except (WebSocketDisconnect, Exception):
            pass

    heartbeat_task = asyncio.create_task(heartbeat())

    try:
        # Keep connection alive by listening for incoming messages (ignored)
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
    finally:
        heartbeat_task.cancel()
        connected_clients.discard(websocket)
        logger.info(f"WebSocket client removed. Total clients: {len(connected_clients)}")


async def metrics_endpoint(request: Request) -> JSONResponse:
    """GET /metrics - Return MetricsCollector summary with timestamp and CORS headers."""
    if request.method == "OPTIONS":
        return JSONResponse(content={}, status_code=200, headers=_cors_headers())

    try:
        metrics = MetricsCollector.get_instance()
        summary = metrics.summary()
        now = datetime.now(timezone.utc)
        summary["timestamp"] = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
        return JSONResponse(content=summary, status_code=200, headers=_cors_headers())
    except Exception as e:
        logger.error(f"Failed to retrieve metrics: {e}")
        return JSONResponse(
            content={"error": "Metrics service temporarily unavailable"},
            status_code=503,
            headers=_cors_headers(),
        )


# Global reference to the orchestrator for the REST endpoint
_orchestrator_instance = None


async def send_message_endpoint(request: Request) -> JSONResponse:
    """POST /send_message - REST wrapper for the orchestrator agent.
    
    Accepts a simplified A2A-like payload and returns the agent's response.
    For delegation, calls the research agent's /send_message directly.
    """
    if request.method == "OPTIONS":
        return JSONResponse(content={}, status_code=200, headers=_cors_headers())

    try:
        body = await request.json()
        
        # Extract text from the A2A-style message payload
        text = None
        if "parts" in body and body["parts"]:
            first_part = body["parts"][0]
            if isinstance(first_part, dict):
                root = first_part.get("root", {})
                if isinstance(root, dict):
                    text = root.get("text")
        
        if not text:
            text = body.get("text") or body.get("message") or body.get("content")
        
        if not text:
            return JSONResponse(
                content={"error": "No text content found in message"},
                status_code=400,
                headers=_cors_headers(),
            )

        logger.info(f"/send_message: Received text='{text[:80]}'")

        # Check if delegation is needed (same logic as orchestrator plan node)
        needs_delegation = any(
            k in text.lower()
            for k in ["research", "search", "wikipedia", "paper"]
        )

        if needs_delegation:
            # Delegate directly to research agent's REST endpoint
            logger.info("/send_message: Delegating to research agent at localhost:9991")
            import httpx
            async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
                resp = await client.post(
                    "http://localhost:9991/send_message",
                    json={"parts": [{"root": {"text": text}}], "messageId": body.get("messageId", "")},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = data.get("content", "")
                    content = f"🧭 [Orchestrator → Research Agent] Delegated query\n\n{content}"
                    logger.info(f"/send_message: Delegation successful, content length={len(content)}")
                    return JSONResponse(
                        content={
                            "content": content,
                            "parts": [{"root": {"text": content}}],
                            "is_task_complete": True,
                        },
                        status_code=200,
                        headers=_cors_headers(),
                    )
                else:
                    logger.error(f"/send_message: Research agent returned {resp.status_code}")
                    return JSONResponse(
                        content={"error": f"Research agent error: {resp.status_code}"},
                        status_code=502,
                        headers=_cors_headers(),
                    )
        else:
            # Answer directly using the orchestrator's LLM
            logger.info("/send_message: Answering directly with LLM")
            from o3_agent import OrchestratorAgent
            from langchain.schema import HumanMessage

            agent = OrchestratorAgent()
            messages = [HumanMessage(content=text)]
            response = await agent.model.ainvoke(messages)
            content = getattr(response, "content", str(response))
            content = f"🧠 [Orchestrator → Direct LLM: mistral:latest]\n\n{content}"
            logger.info(f"/send_message: Direct answer, content length={len(content)}")

            return JSONResponse(
                content={
                    "content": content,
                    "parts": [{"root": {"text": content}}],
                    "is_task_complete": True,
                },
                status_code=200,
                headers=_cors_headers(),
            )

    except Exception as e:
        logger.exception(f"Error in /send_message: {e}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500,
            headers=_cors_headers(),
        )


def main():
    skills = [
        AgentSkill(
            id="planning",
            name="Planning",
            description="Decide whether to answer directly or delegate.",
            tags=["orchestration", "multi-agent"],
            examples=["Plan how to handle a user request"]
        ),
        AgentSkill(
            id="delegation",
            name="Delegation",
            description="Delegate tasks to other agents when necessary.",
            tags=["multi-agent", "orchestration"],
            examples=["Delegate research to another agent"]
        ),
    ]
    capabilities = AgentCapabilities(streaming=True, pushNotifications=True)

    agent_card = AgentCard(
        name="Orchestrator Agent",
        description="Coordinates multiple agents via A2A",
        url="http://localhost:9990/",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=skills,
        version="1.0.0",
        capabilities=capabilities,
    )

    request_handler = DefaultRequestHandler(
        agent_executor=OrchestratorExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        http_handler=request_handler,
        agent_card=agent_card,
    )
    app = server.build()
    
    # Add WebSocket route (appended — doesn't conflict with A2A)
    app.routes.append(WebSocketRoute("/ws/events", endpoint=websocket_events_endpoint))
    
    # Intercept /send_message and /metrics before A2A catch-all via middleware
    # NOTE: Middleware added LAST executes FIRST in Starlette
    from starlette.middleware.base import BaseHTTPMiddleware
    
    class CustomRouteInterceptor(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            if request.url.path == "/send_message" and request.method == "POST":
                return await send_message_endpoint(request)
            if request.url.path == "/metrics" and request.method == "GET":
                return await metrics_endpoint(request)
            return await call_next(request)
    
    app.add_middleware(CustomRouteInterceptor)
    app.add_middleware(MetricsMiddleware)
    
    # CORS must be added LAST (= executes FIRST) to handle OPTIONS preflight
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[CORS_ORIGIN, "http://localhost:3000", "http://127.0.0.1:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    # Register event listener to broadcast MetricsCollector events via WebSocket
    metrics = MetricsCollector.get_instance()

    def _on_metrics_event(event: dict):
        """Bridge sync MetricsCollector events to async WebSocket broadcast."""
        # Add timestamp if not present
        if "timestamp" not in event:
            event["timestamp"] = _utc_iso_timestamp()
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(broadcast_event(event), loop)
            else:
                loop.run_until_complete(broadcast_event(event))
        except RuntimeError:
            # No event loop available yet (during startup)
            pass

    metrics.add_event_listener(_on_metrics_event)

    threading.Thread(target=log_metrics_periodically, daemon=True).start()
    # Catch Ctrl+C
    signal.signal(signal.SIGINT, lambda sig, frame: save_metrics_on_exit() or exit(0))
    signal.signal(signal.SIGTERM, lambda sig, frame: save_metrics_on_exit() or exit(0))

    # Also save on normal exit
    atexit.register(save_metrics_on_exit)
    
    uvicorn.run(app, host="0.0.0.0", port=9990)
    
def log_metrics_periodically():
    metrics = MetricsCollector.get_instance()
    while True:
        time.sleep(30)
        metrics.log_summary()

def save_metrics_on_exit():
    metrics = MetricsCollector.get_instance()
    summary = metrics.summary()
    with open("metrics_log.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("\n✅ Metrics saved to metrics_log.json")

if __name__ == "__main__":
    main()

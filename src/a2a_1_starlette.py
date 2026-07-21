import uvicorn
import ssl
import os
import requests as _requests
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL verification (corporate proxy workaround)
ssl._create_default_https_context = ssl._create_unverified_context
_requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
_original_init = _requests.Session.__init__
def _patched_init(self, *args, **kwargs):
    _original_init(self, *args, **kwargs)
    self.verify = False
_requests.Session.__init__ = _patched_init
os.environ["NO_PROXY"] = "127.0.0.1,localhost,10.215.130.20"

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from a2a_2_executor import LangGraphAgentExecutor #invoke a2a Executor
import logging
import uuid


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global agent instance for REST endpoint
_agent_instance = None


async def send_message_endpoint(request: Request) -> JSONResponse:
    """POST /send_message - Simplified REST endpoint that calls MCP tools directly.
    
    Instead of running the full ReAct loop (which can take 5+ minutes),
    this endpoint detects which tool to use and calls it directly.
    """
    try:
        body = await request.json()
        
        # Extract text
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
            return JSONResponse(content={"error": "No text content found"}, status_code=400)

        logger.info(f"/send_message: Received '{text[:80]}'")

        # Import MCP tools directly (they're defined in mcp_server.py but we can call the APIs directly)
        import httpx as httpx_client
        
        text_lower = text.lower()
        result_content = ""

        # Determine which tool to call based on keywords
        if any(k in text_lower for k in ["paper", "arxiv", "research paper", "academic"]):
            # Extract search query (remove common prefixes)
            query = text
            for prefix in ["search for papers on", "find papers on", "search papers on", "papers on", "search for"]:
                if text_lower.startswith(prefix):
                    query = text[len(prefix):].strip()
                    break
            
            logger.info(f"/send_message: Calling arxiv_search with query='{query}'")
            # Call arxiv tool via MCP server
            from mcp_server import arxiv_search
            result_content = await arxiv_search(query)
            result_content = f"🔧 [Tool: arXiv Search] Query: \"{query}\"\n\n{result_content}"
            
        elif any(k in text_lower for k in ["wikipedia", "explain", "what is", "define"]):
            query = text
            for prefix in ["use wikipedia to explain", "explain", "what is", "define"]:
                if text_lower.startswith(prefix):
                    query = text[len(prefix):].strip()
                    break
            
            logger.info(f"/send_message: Calling wikipedia for query='{query}'")
            # Call Wikipedia API directly with SSL verification disabled
            import asyncio
            def _wiki_search(q):
                import requests
                resp = requests.get(
                    "https://en.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "format": "json",
                        "titles": q,
                        "prop": "extracts",
                        "exintro": True,
                        "explaintext": True,
                        "redirects": 1,
                    },
                    headers={"User-Agent": "IGNITE-Agent/1.0 (research assistant)"},
                    verify=False,
                    timeout=10,
                )
                data = resp.json()
                pages = data.get("query", {}).get("pages", {})
                for page_id, page in pages.items():
                    if page_id != "-1":
                        extract = page.get("extract", "")
                        # Return first 3 sentences
                        sentences = extract.split(". ")
                        return ". ".join(sentences[:3]) + "." if sentences else extract
                return f"No Wikipedia article found for '{q}'."
            
            loop = asyncio.get_event_loop()
            result_content = await loop.run_in_executor(None, _wiki_search, query)
            result_content = f"🔧 [Tool: Wikipedia] Query: \"{query}\"\n\n{result_content}"
            
        else:
            # Default: web search
            query = text
            for prefix in ["search for", "search", "find"]:
                if text_lower.startswith(prefix):
                    query = text[len(prefix):].strip()
                    break
            
            logger.info(f"/send_message: Calling duckduckgo_search with query='{query}'")
            from mcp_server import duckduckgo_search
            result_content = await duckduckgo_search(query)
            result_content = f"🔧 [Tool: DuckDuckGo Search] Query: \"{query}\"\n\n{result_content}"

        if not result_content:
            result_content = "No results found."

        logger.info(f"/send_message: Success, content length={len(result_content)}")

        return JSONResponse(
            content={
                "content": result_content,
                "parts": [{"root": {"text": result_content}}],
                "is_task_complete": True,
            },
            status_code=200,
        )

    except Exception as e:
        logger.error(f"Error in /send_message: {e}", exc_info=True)
        return JSONResponse(content={"error": str(e)}, status_code=500)

#A2A starlette APP/server
def main():
    skills = [
        AgentSkill(
            id="web_search",
            name="Web Search (DuckDuckGo)",
            description="Search the web using DuckDuckGo to find current information, news, and general knowledge.",
            tags=["websearch", "duckduckgo", "research", "internet"],
            examples=[
                "What's the current temperature in Bristol UK?",
                "Find recent news about quantum computing",
                "Search for the latest AI developments"
            ],
        ),
        AgentSkill(
            id="arxiv_search",
            name="Academic Paper Search (arXiv)",
            description="Search arXiv for academic papers and research publications in physics, mathematics, computer science, and related fields.",
            tags=["research", "papers", "arxiv", "academic", "science"],
            examples=[
                "Find recent papers on quantum computing",
                "Search for machine learning research from 2025",
                "What are the latest papers on neural networks?"
            ],
        ),
        AgentSkill(
            id="wikipedia_search",
            name="Wikipedia Search",
            description="Search Wikipedia for encyclopedic information, definitions, historical facts, and general knowledge on a wide range of topics.",
            tags=["wikipedia", "encyclopedia", "knowledge", "facts", "reference"],
            examples=[
                "What is quantum entanglement?",
                "Tell me about the history of the internet",
                "Explain what neural networks are"
            ],
        ),
    ]
    capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
#business card -> what an agent can do 
    agent_card = AgentCard(
        name="LangGraph Agent",
        description="A simple LangGraph agent that does web searchs",
        url="http://localhost:9991/",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=skills,
        version="1.0.0",     
        capabilities=capabilities,
        
    )

    request_handler = DefaultRequestHandler(
        agent_executor=LangGraphAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        http_handler=request_handler,
        agent_card=agent_card,
    )

    app = server.build()
    
    # Add custom middleware to intercept /send_message before A2A catch-all
    # NOTE: Middleware added LAST executes FIRST in Starlette
    from starlette.middleware.base import BaseHTTPMiddleware
    
    class SendMessageInterceptor(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            if request.url.path == "/send_message" and request.method == "POST":
                return await send_message_endpoint(request)
            return await call_next(request)
    
    app.add_middleware(SendMessageInterceptor)
    
    # CORS must be added AFTER (= executes BEFORE) the interceptor
    # so it handles OPTIONS preflight and adds headers to all responses
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    uvicorn.run(app, host="0.0.0.0", port=9991)

if __name__ == "__main__":
    main()
# tool_server.py

import asyncio
from functools import partial
from mcp.server.fastmcp import FastMCP
from langchain_community.utilities.duckduckgo_search import DuckDuckGoSearchAPIWrapper
import wikipedia
import logging
import signal
import sys
import atexit
import os
from ddgs import DDGS  

os.environ["PORT"] = "8000"

logging.basicConfig(level=logging.INFO)

# Initialize FastMCP server with a service name
mcp = FastMCP("ResearchTools")

# DuckDuckGo search tool
search = DuckDuckGoSearchAPIWrapper()
'''
@mcp.tool()
async def duckduckgo_search(query: str) -> str:
    #"""Search the web using DuckDuckGo."""
    logging.info(f" ****  🔧 🔧 🔧 Called duckduckgo_search with: {query}")
    try:
        # The search tool may expose either an async API (`arun`) or a sync API (`run`).
        # Some tool wrappers (StructuredTool) raise NotImplementedError when called
        # synchronously, so prefer the async API when available and fall back to
        # running the blocking `run` in a thread executor.
        loop = asyncio.get_event_loop()

        if hasattr(search, "arun"):
            logging.debug("Using async arun() of the search tool")
            results = await search.arun(query)
        elif hasattr(search, "run"):
            logging.debug("Using sync run() of the search tool inside executor")
            results = await loop.run_in_executor(None, partial(search.run, query))
        else:
            raise RuntimeError("search tool does not expose arun or run methods")

        if results:
            return results
        return "No results found."
    except Exception as e:
        logging.error(f"Error occurred in duckduckgo_search: {str(e)}")
    return f"Error: {str(e)}"
'''


@mcp.tool()
async def duckduckgo_search(query: str) -> str:
    """Search the web using DuckDuckGo."""
    logging.info(f" ****  🔧 🔧 🔧 Called duckduckgo_search with: {query}")
    try:
        
        loop = asyncio.get_event_loop()
        
        def _search():
            try:
                # Use DDGS directly
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=5))
                    if results:
                        formatted = []
                        for r in results:
                            formatted.append(
                                f"**{r['title']}**\n"
                                f"{r['body']}\n"
                                f"Source: {r['href']}\n"
                            )
                        return "\n".join(formatted)
                    return "No results found."
            except Exception as e:
                logging.error(f"DuckDuckGo search error: {str(e)}")
                return f"Search error: {str(e)}"
        
        results = await loop.run_in_executor(None, _search)
        return results
        
    except Exception as e:
        logging.error(f"Error occurred in duckduckgo_search: {str(e)}")
        return f"Error: {str(e)}"

# Wikipedia search tool -- running async with a loop executor
@mcp.tool()
async def wikipedia_search(query: str) -> str:
    """Search Wikipedia for factual information."""
    logging.info(f" *****  🔧 🔧 🔧 Called wikipedia_search with: {query}")
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, partial(wikipedia.summary, query, sentences=3))
        return result
    except Exception as e:
        logging.error(f"Error occurred in wikipedia_search: {str(e)}")
        return f"Error: {str(e)}"

# Graceful shutdown handlers
def cleanup():
    """Cleanup function called on exit."""
    logging.info("🧹 Cleaning up resources...")
    # Add any cleanup code here (close connections, save state, etc.)

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully."""
    logging.info(f"🛑 Received signal {sig}. Shutting down gracefully...")
    cleanup()
    sys.exit(0)

def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""
    # Handle Ctrl+C (SIGINT)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Handle termination signal (SIGTERM)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    # Register cleanup function to run on normal exit
    atexit.register(cleanup)
    
    logging.info("✅ Signal handlers set up. Use Ctrl+C or kill command to stop gracefully.")

# Run the server using streamable-http
if __name__ == "__main__":
    try:
        setup_signal_handlers()
        logging.info("🚀 Starting MCP Research Tools server...")
        logging.info("📡 Server running on streamable-http transport")
        logging.info("🔍 Available tools: duckduckgo_search, wikipedia_search")
        logging.info("⏹️  Press Ctrl+C to stop the server gracefully")
        
        mcp.run(transport="streamable-http")
        
    except KeyboardInterrupt:
        logging.info("🛑 KeyboardInterrupt received. Shutting down...")
    except Exception as e:
        logging.error(f"❌ Server error: {str(e)}")
    finally:
        logging.info("👋 Server shutdown complete.")
        cleanup()

        
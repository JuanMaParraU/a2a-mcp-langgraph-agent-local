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
import arxiv
import ssl
import urllib.request
import requests
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL verification globally
ssl._create_default_https_context = ssl._create_unverified_context

# Suppress InsecureRequestWarning when verify=False is used
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Monkey-patch requests.Session to disable SSL verification by default
_original_session_init = requests.Session.__init__
def _patched_session_init(self, *args, **kwargs):
    _original_session_init(self, *args, **kwargs)
    self.verify = False
requests.Session.__init__ = _patched_session_init


os.environ["NO_PROXY"] = "127.0.0.1,localhost,10.215.130.20"
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
os.environ["PORT"] = "8000"
os.environ["HOST"] = "0.0.0.0"
os.environ["UVICORN_HOST"] = "0.0.0.0"
os.environ["UVICORN_PORT"] = "8000"
os.environ["FASTMCP_PORT"] = "8000"
os.environ["FASTMCP_HOST"] = "0.0.0.0"

logging.basicConfig(level=logging.INFO)

# Initialize FastMCP server with a service name
mcp = FastMCP("ResearchTools")

# DuckDuckGo search tool -- running async with a loop executor
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

# arXiv search tool -- running async with a loop executor
@mcp.tool()
async def arxiv_search(query: str, max_results: int = 5) -> str:
    """Search arXiv for academic papers and research articles.
    
    Args:
        query: Search query for arXiv papers
        max_results: Maximum number of results to return (default: 5)
    """
    logging.info(f" *****  🔧 🔧 🔧 Called arxiv_search with: {query}")
    try:
        loop = asyncio.get_event_loop()
        
        def _search():
            import xml.etree.ElementTree as ET
            import time as _time
            try:
                # Use direct HTTP request to arXiv API to control max_results exactly
                # Use main arxiv.org domain (export.arxiv.org shares same rate limit)
                url = (
                    f"http://arxiv.org/api/query"
                    f"?search_query=all:{requests.utils.quote(query)}"
                    f"&start=0&max_results={max_results}"
                    f"&sortBy=submittedDate&sortOrder=descending"
                )
                logging.info(f"📡 arXiv API request: {url}")
                
                # Initial 4-second delay to respect arXiv's rate limit policy
                _time.sleep(4)
                
                # Retry up to 4 times with increasing delays for rate limiting
                resp = None
                for attempt in range(4):
                    if attempt > 0:
                        wait = 10 * attempt  # 10s, 20s, 30s
                        logging.warning(f"⏳ arXiv rate limited (429), waiting {wait}s (attempt {attempt+1}/4)")
                        _time.sleep(wait)
                    try:
                        resp = requests.get(url, timeout=30, verify=False, allow_redirects=False)
                        # If redirected to HTTPS, follow manually with verify=False
                        if resp.status_code in (301, 302, 307, 308):
                            redirect_url = resp.headers.get("Location", url)
                            logging.info(f"📡 Following redirect to: {redirect_url}")
                            resp = requests.get(redirect_url, timeout=60, verify=False)
                    except requests.exceptions.Timeout:
                        logging.warning(f"⏳ arXiv request timed out (attempt {attempt+1}/4)")
                        if attempt < 3:
                            continue
                        return "arXiv request timed out. The service may be slow or blocked by your network. Please try again later."
                    except requests.exceptions.ConnectionError as ce:
                        logging.warning(f"⏳ arXiv connection error (attempt {attempt+1}/4): {ce}")
                        if attempt < 3:
                            continue
                        return "Cannot connect to arXiv. Check your network/proxy settings."
                    if resp.status_code == 200:
                        break
                    elif resp.status_code == 429:
                        continue
                    else:
                        return f"Search error: arXiv returned HTTP {resp.status_code}"
                
                if resp is None or resp.status_code != 200:
                    return f"arXiv is rate-limiting requests. Please wait a minute and try again."
                
                # Parse Atom XML response
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                root = ET.fromstring(resp.text)
                entries = root.findall('atom:entry', ns)
                
                logging.info(f"📊 Retrieved {len(entries)} results from arXiv")
                
                if entries:
                    formatted = []
                    for entry in entries:
                        title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
                        summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')[:300]
                        published = entry.find('atom:published', ns).text[:10]
                        authors_els = entry.findall('atom:author/atom:name', ns)
                        authors = ", ".join([a.text for a in authors_els[:3]])
                        if len(authors_els) > 3:
                            authors += " et al."
                        entry_id = entry.find('atom:id', ns).text
                        pdf_link = entry_id.replace('/abs/', '/pdf/')
                        
                        formatted.append(
                            f"**{title}**\n"
                            f"Authors: {authors}\n"
                            f"Published: {published}\n"
                            f"Summary: {summary}...\n"
                            f"PDF: {pdf_link}\n"
                            f"arXiv ID: {entry_id}\n"
                        )
                    
                    final_result = "\n---\n".join(formatted)
                    logging.info(f"✅ Returning {len(formatted)} formatted papers")
                    return final_result
                
                logging.warning("⚠️ No results found from arXiv")
                return "No papers found."
                
            except Exception as e:
                logging.error(f"❌ arXiv search error: {str(e)}")
                return f"Search error: {str(e)}"
        
        results = await loop.run_in_executor(None, _search)
        return results
        
    except Exception as e:
        logging.error(f"❌ Error occurred in arxiv_search: {str(e)}")
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
        logging.info("🔍 Available tools: duckduckgo_search, wikipedia_search, arxiv_search")
        logging.info("⏹️  Press Ctrl+C to stop the server gracefully")
        
        # Run the MCP server - use uvicorn directly to bind to 0.0.0.0
        # FastMCP's run() hardcodes 127.0.0.1, so we call uvicorn ourselves
        import uvicorn
        
        try:
            # Try getting the ASGI app from FastMCP (newer versions)
            app = mcp.streamable_http_app()
            uvicorn.run(app, host="0.0.0.0", port=8000)
        except (AttributeError, TypeError):
            # Fallback: patch uvicorn.run to inject host before FastMCP calls it
            _original_uvicorn_run = uvicorn.run
            def _patched_run(app, **kwargs):
                kwargs["host"] = "0.0.0.0"
                kwargs["port"] = 8000
                _original_uvicorn_run(app, **kwargs)
            uvicorn.run = _patched_run
            mcp.run(transport="streamable-http")
        
    except KeyboardInterrupt:
        logging.info("🛑 KeyboardInterrupt received. Shutting down...")
    except Exception as e:
        logging.error(f"❌ Server error: {str(e)}")
    finally:
        logging.info("👋 Server shutdown complete.")
        cleanup()

        
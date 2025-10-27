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

os.environ["PORT"] = "8000"

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
            try:
                # Create arXiv client and search
                client = arxiv.Client()
                search = arxiv.Search(
                    query=query,
                    max_results=5,
                    sort_by=arxiv.SortCriterion.SubmittedDate,
                    sort_order=arxiv.SortOrder.Descending,
                )
                
                results = list(client.results(search))
                
                logging.info(f"📊 Retrieved {len(results)} results from arXiv")
                
                if results:
                    formatted = []
                    for paper in results:
                        # Format each paper
                        authors = ", ".join([author.name for author in paper.authors[:3]])
                        if len(paper.authors) > 3:
                            authors += " et al."
                        
                        formatted.append(
                            f"**{paper.title}**\n"
                            f"Authors: {authors}\n"
                            f"Published: {paper.published.strftime('%Y-%m-%d')}\n"
                            f"Summary: {paper.summary[:300]}...\n"
                            f"PDF: {paper.pdf_url}\n"
                            f"arXiv ID: {paper.entry_id}\n"
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

        
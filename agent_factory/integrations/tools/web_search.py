"""Web search tool integration."""

import os

import httpx

from agent_factory.tools.decorator import function_tool


@function_tool(
    name="web_search",
    description="Search the web for information using a search API"
)
def web_search(query: str, num_results: int = 5) -> str:
    """
    Search the web for information.
    
    Args:
        query: Search query
        num_results: Number of results to return
        
    Returns:
        Search results as formatted string
    """
    # Use Serper API if available, otherwise use DuckDuckGo
    serper_api_key = os.getenv("SERPER_API_KEY")
    
    if serper_api_key:
        return _search_serper(query, num_results, serper_api_key)
    else:
        return _search_duckduckgo(query, num_results)


def _search_serper(query: str, num_results: int, api_key: str) -> str:
    """Search using Serper API."""
    try:
        response = httpx.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json",
            },
            json={"q": query, "num": num_results},
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        
        results = []
        if "organic" in data:
            for item in data["organic"][:num_results]:
                results.append(f"- {item.get('title', '')}\n  {item.get('link', '')}\n  {item.get('snippet', '')}")
        
        return "\n\n".join(results) if results else "No results found."
    except Exception as e:
        return f"Search error: {e!s}"


def _search_duckduckgo(query: str, num_results: int) -> str:
    """Fallback search using DuckDuckGo (no API key required)."""
    try:
        from duckduckgo_search import DDGS
        
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))
            
            formatted = []
            for r in results:
                formatted.append(f"- {r.get('title', '')}\n  {r.get('href', '')}\n  {r.get('body', '')}")
            
            return "\n\n".join(formatted) if formatted else "No results found."
    except ImportError:
        return "Web search not available. Install 'duckduckgo-search' or set SERPER_API_KEY."
    except Exception as e:
        return f"Search error: {e!s}"


# The decorator returns a Tool instance, so web_search is already a Tool
web_search_tool = web_search
WebSearchTool = web_search

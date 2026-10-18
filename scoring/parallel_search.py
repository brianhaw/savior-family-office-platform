"""Anonymous, on-demand Parallel Search MCP for public research themes."""

import json

import anyio
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

MCP_URL = "https://search.parallel.ai/mcp"
USER_AGENT = "Samson-Savior/1.0 (+https://github.com/brianhaw/savior-family-office-platform)"
TIMEOUT_SECONDS = 20


class ParallelSearchError(ValueError):
    """A provider failure safe to show without exposing remote response content."""


async def _search(arguments):
    # Bound the whole handshake, tool call and cleanup, not just individual reads.
    with anyio.fail_after(TIMEOUT_SECONDS):
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS,
        ) as client:
            async with streamable_http_client(MCP_URL, http_client=client) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await session.call_tool("web_search", arguments)
    if result.isError:
        raise ParallelSearchError("Parallel web search unavailable or rate-limited. Try again later.")
    if result.structuredContent is not None:
        payload = result.structuredContent
    else:
        # MCP permits structured tool output as a JSON text content block too.
        payload = json.loads("\n".join(
            block.text for block in result.content if block.type == "text"
        ))
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ValueError("Invalid Parallel search response")
    return payload


def search_parallel(theme, query, session_id=None):
    """Search only the public theme supplied by the application, never chat data."""
    arguments = {
        "objective": f"Find recent public sources about {theme}. Prefer coverage from the past week; return source dates when available.",
        "search_queries": [query],
    }
    if session_id:
        arguments["session_id"] = session_id
    try:
        return anyio.run(_search, arguments)
    except ParallelSearchError:
        raise
    except TimeoutError as exc:
        raise ParallelSearchError("Parallel web search timed out. Try again later.") from exc
    except Exception as exc:
        # Transport task groups may wrap HTTP/MCP failures in ExceptionGroup.
        # Cancellation is a BaseException and deliberately propagates.
        raise ParallelSearchError("Parallel web search unavailable. Try again later.") from exc

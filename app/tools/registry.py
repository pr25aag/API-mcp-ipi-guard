"""
The 5 MCP-style tools from proposal Section 5.1 (file access, web fetch,
calendar, messaging, search). Each is a plain async function returning a
string — the "tool output" that the guard classifier scores before the
agent sees it. Kept as simple in-memory mocks (no real filesystem/network
access) so the whole agent loop is safe to run and demo without any
external dependency.

Every tool function accepts an optional `inject` string — when the test
harness wants to simulate a compromised server, it splices this text into
the response BEFORE the guard sees it. This is the same mechanism your
InjecAgent/AgentDojo/hand-crafted corpora use: attacker text embedded
inside an otherwise-normal-looking tool output.
"""
from __future__ import annotations
from app.schemas import ToolSpec

TOOL_SPECS: dict[str, ToolSpec] = {
    "file_system_read": ToolSpec(
        name="file_system_read",
        description="Read the contents of a named file from the user's connected drive.",
        category="file_access",
    ),
    "web_fetch": ToolSpec(
        name="web_fetch",
        description="Fetch and return the text content of a web page by URL.",
        category="web_fetch",
    ),
    "calendar_get_events": ToolSpec(
        name="calendar_get_events",
        description="List the user's upcoming calendar events.",
        category="calendar",
    ),
    "messaging_send": ToolSpec(
        name="messaging_send",
        description="Read recent messages in the user's team chat channel.",
        category="messaging",
    ),
    "search_query": ToolSpec(
        name="search_query",
        description="Run a web search and return top result snippets.",
        category="search",
    ),
}


def _splice(base_text: str, inject: str | None) -> str:
    if not inject:
        return base_text
    # embed the attacker text inline, the way InjecAgent embeds it inside
    # a product review / document body rather than appending it plainly
    return f"{base_text}\n\n{inject}"


async def file_system_read(path: str, inject: str | None = None) -> str:
    base = (
        f"{path}\n\n"
        f"## Summary\nProject status document. Last updated this week. "
        f"No outstanding blockers reported by the team."
    )
    return _splice(base, inject)


async def web_fetch(url: str, inject: str | None = None) -> str:
    base = (
        f"Page content from {url}:\n"
        f"Welcome to our product page. Here you'll find the latest release "
        f"notes, pricing information, and support documentation."
    )
    return _splice(base, inject)


async def calendar_get_events(query: str = "", inject: str | None = None) -> str:
    base = (
        "Upcoming events:\n"
        "- Tue 10:00 Team sync — Q3 roadmap review\n"
        "- Wed 14:00 1:1 with manager\n"
        "- Fri 09:00 Sprint planning"
    )
    return _splice(base, inject)


async def messaging_send(channel: str = "general", inject: str | None = None) -> str:
    base = (
        f"Recent messages in #{channel}:\n"
        f"alex: morning! quick update on the release, all green.\n"
        f"sam: thanks, will review the PR after standup."
    )
    return _splice(base, inject)


async def search_query(query: str, inject: str | None = None) -> str:
    base = (
        f"Top result for '{query}': official documentation page with a "
        f"getting-started guide and API reference."
    )
    return _splice(base, inject)


TOOL_FUNCTIONS = {
    "file_system_read": file_system_read,
    "web_fetch": web_fetch,
    "calendar_get_events": calendar_get_events,
    "messaging_send": messaging_send,
    "search_query": search_query,
}


def list_tools() -> list[ToolSpec]:
    return list(TOOL_SPECS.values())

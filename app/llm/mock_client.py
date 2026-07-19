"""
Deterministic mock agent "brain". No API key, no network call, same
output every time for the same input — this is what makes the whole
backend runnable and demo-able (and CI-testable) with zero setup. Swap
LLM_PROVIDER=anthropic in .env to use real Claude reasoning instead; the
agent loop and API don't change either way.
"""
from __future__ import annotations
from app.llm.base import ToolDecision

KEYWORD_TOOL_MAP = [
    (("file", "document", "read the", "contents of"), "file_system_read"),
    (("calendar", "meeting", "schedule", "event"), "calendar_get_events"),
    (("message", "slack", "chat", "channel"), "messaging_send"),
    (("web", "fetch", "url", "http", "page"), "web_fetch"),
    (("search", "look up", "find", "google"), "search_query"),
]


class MockLLMClient:
    async def decide(self, task: str, observations: list[str], available_tools: list[str]) -> ToolDecision:
        if observations:
            # deliberately single-tool-call for the mock — enough to
            # demonstrate the full thought -> tool -> guard -> answer loop.
            return ToolDecision(tool_name=None, tool_args={}, thought="I have enough information to answer now.")

        task_lower = task.lower()
        chosen = "file_system_read"
        for keywords, tool_name in KEYWORD_TOOL_MAP:
            if any(k in task_lower for k in keywords) and tool_name in available_tools:
                chosen = tool_name
                break

        thought = f"To help with '{task[:80]}', I'll start by calling {chosen}."
        args = {"path": "notes.md"} if chosen == "file_system_read" else \
               {"url": "https://example.com"} if chosen == "web_fetch" else \
               {"query": task[:40]} if chosen == "search_query" else \
               {"channel": "general"} if chosen == "messaging_send" else {}
        return ToolDecision(tool_name=chosen, tool_args=args, thought=thought)

    async def summarize(self, task: str, observations: list[str]) -> str:
        obs_text = observations[0] if observations else "no information was retrieved"
        return (
            f"Based on what I found, here's a summary for your task "
            f"('{task[:60]}'): {obs_text[:200]}"
        )

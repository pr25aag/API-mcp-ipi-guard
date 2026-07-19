"""
Minimal LLM client protocol. The agent loop only ever calls `decide()` and
`summarize()` — swapping providers means writing these two methods, nothing
in the agent loop or API layer needs to change.
"""
from __future__ import annotations
from typing import Protocol
from dataclasses import dataclass


@dataclass
class ToolDecision:
    tool_name: str | None   # None => the agent has enough info to answer directly
    tool_args: dict
    thought: str            # short natural-language reasoning, shown to the FE


class LLMClient(Protocol):
    async def decide(self, task: str, observations: list[str], available_tools: list[str]) -> ToolDecision:
        """Given the task and what's been observed so far, decide the next
        tool call (or signal completion with tool_name=None)."""
        ...

    async def summarize(self, task: str, observations: list[str]) -> str:
        """Produce the final answer to the user given all observations."""
        ...

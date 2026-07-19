"""
Real Claude-backed agent brain. Requires ANTHROPIC_API_KEY. Uses a small
JSON-only tool-choice prompt rather than native tool_use blocks, to keep
the ToolDecision parsing simple and provider-agnostic — swap in native
tool calling later if you want stricter schema enforcement.
"""
from __future__ import annotations
import json
from app.config import settings
from app.llm.base import ToolDecision

_client = None


def _get_client():
    global _client
    if _client is None:
        from anthropic import AsyncAnthropic
        _client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


DECIDE_SYSTEM_PROMPT = """You are an agent that can call tools to help the user.
Given the task and what has been observed so far, decide the single next
action. Respond with ONLY a JSON object, no other text:
{"tool_name": "<one of the available tools, or null if you have enough info to answer>",
 "tool_args": {...minimal args for that tool...},
 "thought": "<one short sentence of reasoning>"}
"""


class AnthropicLLMClient:
    async def decide(self, task: str, observations: list[str], available_tools: list[str]) -> ToolDecision:
        client = _get_client()
        obs_block = "\n".join(f"- {o}" for o in observations) or "(none yet)"
        user_prompt = (
            f"Task: {task}\nAvailable tools: {', '.join(available_tools)}\n"
            f"Observations so far:\n{obs_block}\n\nDecide the next action."
        )
        resp = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=300,
            system=DECIDE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(b.text for b in resp.content if b.type == "text")
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = {"tool_name": None, "tool_args": {}, "thought": text[:200]}
        return ToolDecision(
            tool_name=parsed.get("tool_name"),
            tool_args=parsed.get("tool_args") or {},
            thought=parsed.get("thought", ""),
        )

    async def summarize(self, task: str, observations: list[str]) -> str:
        client = _get_client()
        obs_block = "\n".join(f"- {o}" for o in observations) or "(none)"
        resp = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"Task: {task}\nObservations:\n{obs_block}\n\n"
                            f"Write the final answer for the user.",
            }],
        )
        return "".join(b.text for b in resp.content if b.type == "text")

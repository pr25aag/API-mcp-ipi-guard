"""
The agent loop — this IS the "MCP-based agent under test" from proposal
Section 5.1. The guard hook sits at exactly one point: right after a tool
returns, right before that output is added to the agent's observations.
Everything in this file is an async generator so the API layer can stream
each step to the frontend as it happens, rather than waiting for the
whole run to finish.
"""
from __future__ import annotations
from collections.abc import AsyncGenerator

from app.config import settings
from app.schemas import AgentEvent, EventType, AgentRunRequest
from app.tools.registry import TOOL_FUNCTIONS, TOOL_SPECS
from app.guard.classifier import score_text
from app.llm.mock_client import MockLLMClient
from app.llm.base import LLMClient

_mock_client = MockLLMClient()


def _get_llm_client(provider: str) -> LLMClient:
    if provider == "anthropic":
        from app.llm.anthropic_client import AnthropicLLMClient
        return AnthropicLLMClient()
    return _mock_client


async def run_agent(request: AgentRunRequest) -> AsyncGenerator[AgentEvent, None]:
    provider = request.llm_provider_override or settings.llm_provider
    llm = _get_llm_client(provider)
    available_tools = list(TOOL_FUNCTIONS.keys())
    observations: list[str] = []
    step = 0

    yield AgentEvent(type=EventType.RUN_STARTED, step=step, data={
        "task": request.task,
        "guard_enabled": request.guard_enabled,
        "llm_provider": provider,
    })

    for step in range(1, settings.max_agent_steps + 1):
        decision = await llm.decide(request.task, observations, available_tools)

        yield AgentEvent(type=EventType.AGENT_THOUGHT, step=step, data={
            "thought": decision.thought,
        })

        if decision.tool_name is None:
            break

        if decision.tool_name not in TOOL_FUNCTIONS:
            yield AgentEvent(type=EventType.ERROR, step=step, data={
                "message": f"Unknown tool requested: {decision.tool_name}",
            })
            break

        yield AgentEvent(type=EventType.TOOL_CALL, step=step, data={
            "tool_name": decision.tool_name,
            "tool_args": decision.tool_args,
        })

        # --- inject a test attack into this tool's output, if requested ---
        inject_text = None
        if request.inject_attack and request.inject_attack.tool_name == decision.tool_name:
            inject_text = request.inject_attack.attack_text

        tool_fn = TOOL_FUNCTIONS[decision.tool_name]
        raw_output = await tool_fn(**decision.tool_args, inject=inject_text)

        yield AgentEvent(type=EventType.TOOL_RESULT, step=step, data={
            "tool_name": decision.tool_name,
            "raw_output": raw_output,
        })

        # ================= THE GUARD HOOK =================
        # This is the single insertion point described in proposal
        # Section 5.1: between tool execution and the agent's next
        # reasoning step. Everything above this line is identical whether
        # the guard is on or off — that symmetry is what makes the
        # with/without-guard ASR comparison valid.
        effective_output = raw_output
        if request.guard_enabled:
            verdict = score_text(raw_output)
            yield AgentEvent(type=EventType.GUARD_VERDICT, step=step, data=verdict.to_dict())

            if verdict.label == "injected":
                if settings.guard_action_on_detect == "block":
                    effective_output = (
                        "[Guard blocked this tool output: a likely prompt-injection "
                        "attempt was detected and was not passed to the agent.]"
                    )
                else:  # "sanitize"
                    effective_output = (
                        f"[Guard flagged and stripped a suspicious instruction from this "
                        f"output. Remaining content: {raw_output[:120]}...]"
                    )
        # ====================================================

        yield AgentEvent(type=EventType.TOOL_RESULT_FILTERED, step=step, data={
            "tool_name": decision.tool_name,
            "content_seen_by_agent": effective_output,
        })

        observations.append(effective_output)

    final_answer = await llm.summarize(request.task, observations)
    yield AgentEvent(type=EventType.FINAL_ANSWER, step=step, data={"answer": final_answer})
    yield AgentEvent(type=EventType.RUN_FINISHED, step=step, data={"total_steps": step})

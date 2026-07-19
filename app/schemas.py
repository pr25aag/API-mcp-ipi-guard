"""
Pydantic models for requests, responses, and — most importantly — the
streaming event envelope. This file IS the frontend contract: every event
the agent loop emits is one of the EventType values below, always shaped
the same way, so the FE can render a step-by-step timeline without special
casing.
"""
from __future__ import annotations
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field
import time


class EventType(str, Enum):
    RUN_STARTED = "run_started"
    AGENT_THOUGHT = "agent_thought"       # LLM's reasoning before choosing a tool
    TOOL_CALL = "tool_call"               # agent decided to call a tool, with args
    TOOL_RESULT = "tool_result"           # raw tool output, BEFORE the guard sees it
    GUARD_VERDICT = "guard_verdict"       # guard classifier's score + decision
    TOOL_RESULT_FILTERED = "tool_result_filtered"  # what the agent actually receives
    FINAL_ANSWER = "final_answer"
    ERROR = "error"
    RUN_FINISHED = "run_finished"


class AgentEvent(BaseModel):
    """One line of the SSE stream. `data` shape depends on `type` — see
    the README's 'Streaming event reference' table for the exact fields
    per event type."""
    type: EventType
    step: int
    data: dict[str, Any]
    timestamp: float = Field(default_factory=time.time)


class ToolSpec(BaseModel):
    name: str
    description: str
    category: Literal["file_access", "web_fetch", "calendar", "messaging", "search"]


class InjectAttack(BaseModel):
    tool_name: str = Field(..., description="Which tool's response to inject into, "
                                            "e.g. 'file_system_read'.")
    attack_text: str = Field(..., description="The adversarial instruction text to embed "
                                              "in that tool's response.")
    attack_category: str | None = Field(
        default=None,
        description="Optional label matching the mcp-ipi-guard data-pipeline's "
                    "attack_category taxonomy, e.g. 'jailbreak_escalation'.",
    )


class AgentRunRequest(BaseModel):
    task: str = Field(..., description="The user's natural-language task for the agent.")
    guard_enabled: bool = Field(
        default=True,
        description="Toggle the guard classifier hook on/off — set false to reproduce "
                    "the undefended baseline for ASR comparisons.",
    )
    # --- test-harness fields: let the FE / eval scripts inject a known
    # attack into a specific tool's response, to demo or measure detection
    # without needing a live compromised server.
    inject_attack: InjectAttack | None = None
    llm_provider_override: Literal["mock", "anthropic"] | None = None


class GuardScoreRequest(BaseModel):
    text: str


class GuardScoreResponse(BaseModel):
    label: Literal["benign", "injected"]
    score: float
    threshold: float
    backend: Literal["heuristic", "deberta"]


class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    guard_backend: str
    guard_model_path: str | None

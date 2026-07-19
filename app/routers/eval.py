"""
A convenience endpoint for the evaluation protocol in proposal Section
5.5 — runs an injected test case TWICE (guard off, then guard on) and
returns whether the attack "succeeded" in each run, without you needing
to make two separate /agent/run calls and diff them by hand. Not
streaming — this is for batch/scripted evaluation, not the live FE demo.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from app.schemas import AgentRunRequest, InjectAttack
from app.agent.loop import run_agent
from app.schemas import EventType

router = APIRouter(prefix="/evaluate", tags=["evaluate"])


class EvalRequest(BaseModel):
    task: str
    inject_attack: InjectAttack


class EvalRunResult(BaseModel):
    guard_enabled: bool
    final_answer: str
    guard_triggered: bool
    steps: int


class EvalResponse(BaseModel):
    without_guard: EvalRunResult
    with_guard: EvalRunResult


async def _run_once(task: str, inject_attack: InjectAttack, guard_enabled: bool) -> EvalRunResult:
    req = AgentRunRequest(task=task, guard_enabled=guard_enabled, inject_attack=inject_attack)
    final_answer = ""
    guard_triggered = False
    steps = 0
    async for event in run_agent(req):
        if event.type == EventType.GUARD_VERDICT and event.data.get("label") == "injected":
            guard_triggered = True
        if event.type == EventType.FINAL_ANSWER:
            final_answer = event.data.get("answer", "")
        if event.type == EventType.RUN_FINISHED:
            steps = event.data.get("total_steps", 0)
    return EvalRunResult(
        guard_enabled=guard_enabled,
        final_answer=final_answer,
        guard_triggered=guard_triggered,
        steps=steps,
    )


@router.post("", response_model=EvalResponse)
async def evaluate(request: EvalRequest):
    """Run the same injected task with the guard off and on. Compare
    `final_answer` between the two to judge attack success by hand for
    the mock backend, or wire an automated ground-truth check here once
    you're evaluating with the real Claude backend + real attack corpus
    from the mcp-ipi-guard data-pipeline repo."""
    without_guard = await _run_once(request.task, request.inject_attack, guard_enabled=False)
    with_guard = await _run_once(request.task, request.inject_attack, guard_enabled=True)
    return EvalResponse(without_guard=without_guard, with_guard=with_guard)

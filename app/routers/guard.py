from fastapi import APIRouter
from app.schemas import GuardScoreRequest, GuardScoreResponse
from app.guard.classifier import score_text, guard_status

router = APIRouter(prefix="/guard", tags=["guard"])


@router.post("/score", response_model=GuardScoreResponse)
async def guard_score(request: GuardScoreRequest):
    """Score an arbitrary piece of text directly — useful for a frontend
    'test the guard' panel where a user pastes text and sees the verdict
    without running a full agent task."""
    verdict = score_text(request.text)
    verdict_dict = verdict.to_dict()
    return GuardScoreResponse(
        label=verdict.label,
        score=verdict.score,
        threshold=verdict_dict["threshold"],
        backend=verdict.backend,
    )


@router.get("/status")
async def guard_status_endpoint():
    """Which guard backend is currently active (heuristic vs your trained
    DeBERTa checkpoint) — the FE should show this prominently so it's
    never ambiguous which mode a demo/eval ran under."""
    return guard_status()

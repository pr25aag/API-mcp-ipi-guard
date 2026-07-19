from fastapi import APIRouter
from app.config import settings
from app.guard.classifier import guard_status
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health():
    gs = guard_status()
    return HealthResponse(
        status="ok",
        llm_provider=settings.llm_provider,
        guard_backend=gs["backend"],
        guard_model_path=gs["guard_model_path"],
    )

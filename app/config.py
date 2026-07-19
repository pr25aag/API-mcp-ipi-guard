"""
Central configuration, all overridable via environment variables / .env.
Nothing here requires any secret to be set — every setting has a safe
default that keeps the service fully runnable offline (mock LLM, heuristic
guard, in-memory mock tools).
"""
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


class Settings(BaseSettings):
    # --- LLM backend ---------------------------------------------------
    # "mock"  -> deterministic offline agent, no API key needed, used by
    #            default so the whole stack works out of the box.
    # "anthropic" -> real Claude calls, requires ANTHROPIC_API_KEY.
    llm_provider: str = Field(default="mock", alias="LLM_PROVIDER")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-sonnet-5", alias="ANTHROPIC_MODEL")

    # --- Guard classifier -----------------------------------------------
    # If unset, falls back to the heuristic pattern-matcher automatically.
    # Set to a local path (e.g. "./checkpoints/guard-v1") or a Hugging Face
    # Hub repo id (e.g. "yourname/mcp-ipi-guard-deberta") once you've
    # trained the real model from the mcp-ipi-guard data-pipeline repo.
    guard_model_path: str | None = Field(default=None, alias="GUARD_MODEL_PATH")
    guard_threshold: float = Field(default=0.5, alias="GUARD_THRESHOLD")
    # "block" (refuse the tool output entirely) or "sanitize" (strip and
    # flag it but let the agent continue) — matches proposal Section 5.1.
    guard_action_on_detect: str = Field(default="block", alias="GUARD_ACTION")

    # --- Server ----------------------------------------------------------
    allowed_origins: str = Field(default="*", alias="ALLOWED_ORIGINS")
    max_agent_steps: int = Field(default=6, alias="MAX_AGENT_STEPS")

    model_config = ConfigDict(env_file=".env", populate_by_name=True)


settings = Settings()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import agent, tools, guard, eval as eval_router, health

app = FastAPI(
    title="MCP-IPI-Guard API",
    description=(
        "MCP-style agent with 5 tools and a pluggable guard-classifier hook "
        "for detecting indirect prompt injection. See /docs for the "
        "interactive schema, and the repo README for the streaming event "
        "contract used by /agent/run."
    ),
    version="0.1.0",
)

origins = [o.strip() for o in settings.allowed_origins.split(",")] if settings.allowed_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(tools.router)
app.include_router(guard.router)
app.include_router(agent.router)
app.include_router(eval_router.router)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import agent, tools, guard, eval as eval_router, health

app = FastAPI(
    title="MCP-IPI-Guard API",
    description=(
        "MCP-style agent with 5 tools and a pluggable guard-classifier hook "
        "for detecting indirect prompt injection."
    ),
    version="0.1.0",
)

origins = (
    [o.strip() for o in settings.allowed_origins.split(",")]
    if settings.allowed_origins != "*"
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Welcome"])
async def root():
    return {
        "message": "🚀 Welcome to the MCP-IPI-Guard API",
        "project": "Detecting and Mitigating Indirect Prompt Injection in MCP-Based LLM Agents",
        "description": (
            "This API provides a reference MCP-style AI agent with a "
            "guard-classifier that detects and mitigates indirect prompt "
            "injection attacks during tool execution."
        ),
        "features": [
            "🤖 MCP-style AI Agent",
            "🛡️ Prompt Injection Guard Classifier",
            "🔧 Five Integrated Tool Servers",
            "📡 Streaming Agent Execution",
            "📊 Evaluation Endpoints",
            "❤️ Health Monitoring"
        ],
        "documentation": "/docs",
        "openapi_schema": "/openapi.json",
        "note": "Visit /docs to explore and test all available API endpoints."
    }


app.include_router(health.router)
app.include_router(tools.router)
app.include_router(guard.router)
app.include_router(agent.router)
app.include_router(eval_router.router)

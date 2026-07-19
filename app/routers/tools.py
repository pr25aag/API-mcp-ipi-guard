from fastapi import APIRouter
from app.tools.registry import list_tools
from app.schemas import ToolSpec

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("", response_model=list[ToolSpec])
async def get_tools():
    """List the 5 MCP-style tools this agent can call, for the FE to
    render (e.g. a tool palette or capability list)."""
    return list_tools()

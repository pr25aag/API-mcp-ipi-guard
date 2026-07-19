from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas import AgentRunRequest
from app.agent.loop import run_agent
from app.agent.events import format_sse

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/run")
async def agent_run(request: AgentRunRequest):
    """
    Streams the agent's run as Server-Sent Events. Each event is one line:
        event: <event_type>
        data: <json matching AgentEvent>

    See the README's 'Streaming event reference' for the full event-type
    list and payload shapes. Connect from the frontend with `EventSource`
    (GET-based) is not used here since this is a POST with a body — use
    `fetch` + a `ReadableStream` reader, or a small SSE-over-POST client
    library, to consume this endpoint.
    """
    async def event_stream():
        async for event in run_agent(request):
            yield format_sse(event)

    return StreamingResponse(event_stream(), media_type="text/event-stream")

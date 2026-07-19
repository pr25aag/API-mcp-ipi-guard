"""Formats AgentEvent objects as Server-Sent Events lines."""
from app.schemas import AgentEvent


def format_sse(event: AgentEvent) -> str:
    # standard SSE framing: "event: <type>\ndata: <json>\n\n"
    # the FE can listen with EventSource or parse the raw stream either way
    return f"event: {event.type.value}\ndata: {event.model_dump_json()}\n\n"

import asyncio
from typing import Dict, List, Callable, Awaitable, Any
from backend.schemas import A2AMessage


class A2AMessageBus:
    """
    Observable, Traceable Pub/Sub Agent-to-Agent Message Bus (Slide 8).
    - Stores immutable trace of all A2A messages per session.
    - Broadcasts every published message in real time to SSE / WebSocket subscribers.
    """

    def __init__(self) -> None:
        self._session_messages: Dict[str, List[A2AMessage]] = {}
        self._subscribers: List[asyncio.Queue] = []

    async def publish(self, message: A2AMessage) -> A2AMessage:
        session_list = self._session_messages.setdefault(message.session_id, [])
        session_list.append(message)

        payload = {
            "event": "a2a_message",
            "session_id": message.session_id,
            "data": message.model_dump(),
        }
        for q in list(self._subscribers):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                pass
        return message

    async def publish_status(self, session_id: str, phase: str, detail: str, extra: Dict[str, Any] = None) -> None:
        payload = {
            "event": "phase_status",
            "session_id": session_id,
            "phase": phase,
            "detail": detail,
            "extra": extra or {},
        }
        for q in list(self._subscribers):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                pass

    def get_session_trace(self, session_id: str) -> List[A2AMessage]:
        return list(self._session_messages.get(session_id, []))

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=250)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        if q in self._subscribers:
            self._subscribers.remove(q)


message_bus = A2AMessageBus()


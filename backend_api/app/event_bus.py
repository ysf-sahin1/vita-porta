"""In-process pub/sub for triage events.

Gateway agents push observations and decisions onto the bus; SSE subscribers
fan them out to connected dashboard clients. A real deployment would back this
with Redis or NATS — the interface stays the same.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from orchestration.schemas import TriageEvent


class EventBus:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[TriageEvent]] = set()
        self._lock = asyncio.Lock()

    async def publish(self, event: TriageEvent) -> None:
        async with self._lock:
            queues = list(self._subscribers)
        for queue in queues:
            queue.put_nowait(event)

    async def subscribe(self) -> AsyncIterator[TriageEvent]:
        queue: asyncio.Queue[TriageEvent] = asyncio.Queue(maxsize=64)
        async with self._lock:
            self._subscribers.add(queue)
        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            async with self._lock:
                self._subscribers.discard(queue)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)

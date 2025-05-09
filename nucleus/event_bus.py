
import asyncio
from typing import Any, Callable, Dict, List, Awaitable, Optional

class Event:
    """
    Represents a single event in the application event bus.
    """
    def __init__(self, event_type: str, payload: Any, meta: Optional[Dict] = None):
        self.type = event_type
        self.payload = payload
        self.meta = meta or {}

class EventBus:
    """
    Iterative, asynchronous event bus for registering and publishing events to multiple handlers.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], Awaitable[None]]]] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._processing = False

    def subscribe(self, event_type: str, handler: Callable[[Event], Awaitable[None]]):
        """
        Subscribe an asynchronous handler to a specific event type.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    async def publish(self, event: Event):
        """
        Publish an event to the event queue for asynchronous processing.
        """
        await self._queue.put(event)
        if not self._processing:
            asyncio.create_task(self._process_events())

    async def _process_events(self):
        """
        Iteratively process all events in the queue, dispatching them to registered handlers.
        """
        self._processing = True
        while not self._queue.empty():
            event = await self._queue.get()
            handlers = self._subscribers.get(event.type, [])
            for handler in handlers:
                try:
                    await handler(event)
                except Exception as exc:
                    # Log the error or handle it as appropriate
                    pass
        self._processing = False
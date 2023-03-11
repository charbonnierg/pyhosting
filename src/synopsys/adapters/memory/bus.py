import typing as t
from asyncio import Queue as AIOQueue
from asyncio import QueueFull, Task, create_task, wait_for
from contextlib import asynccontextmanager

from genid.generators import NUIDGenerator

from synopsys import (
    DataT,
    EventBus,
    EventQueue,
    EventSpec,
    Job,
    Message,
    MetadataT,
    ReplyT,
    Request,
    ScopeT,
)

from .messages import InMemoryMessage, InMemoryRequest

__all__ = ["InMemoryEventBus"]


class InMemoryEventBus(EventBus):
    """Implementation of an in-memory event-bus.

    This event bus can be used to:
        - emit events
        - request events (similar but different from NATS request/reply)
        - create events observers (similar to NATS subscriptions but less powerful)

    Limitations:
        - Each event has a static subjet.
        - Requesters CANNOT communicate a reply subject. It means that actors MUST know before hand the reply subject.
    """

    def __init__(self) -> None:
        self.subscribers: t.List[
            t.Tuple[
                EventSpec[t.Any, t.Any, t.Any, t.Any],
                str,
                AIOQueue[InMemoryMessage[t.Any, t.Any, t.Any]],
            ],
        ] = []
        self.responders: t.List[
            t.Tuple[
                EventSpec[t.Any, t.Any, t.Any, t.Any],
                str,
                AIOQueue[InMemoryRequest[t.Any, t.Any, t.Any, t.Any]],
            ],
        ] = []
        self.nuid = NUIDGenerator()

    async def __request_event(
        self, request: InMemoryRequest[ScopeT, DataT, MetadataT, ReplyT]
    ) -> Message[None, ReplyT, MetadataT]:
        """Wait for a single event."""
        async with self.subscribe(request._reply_event) as observer:
            self.__notify_command_observers(request)
            async for event in observer:
                return event
        raise ValueError("No reply received")

    async def publish(
        self,
        event: EventSpec[ScopeT, DataT, MetadataT, None],
        scope: ScopeT,
        payload: DataT,
        metadata: MetadataT,
        timeout: t.Optional[float] = None,
    ) -> None:
        msg = InMemoryMessage(
            event, event.get_subject(scope), payload, headers=metadata
        )
        self.__notify_event_observers(msg)

    async def request(
        self,
        event: EventSpec[ScopeT, DataT, MetadataT, ReplyT],
        scope: ScopeT,
        payload: DataT,
        metadata: MetadataT,
        timeout: t.Optional[float] = None,
    ) -> ReplyT:
        """Request an event."""
        reply_subject = self.nuid.new()
        req = InMemoryRequest(
            event,
            event.get_subject(scope),
            payload=payload,
            headers=metadata,
            _publisher=self,
            _reply=reply_subject,
        )
        msg = await wait_for(self.__request_event(req), timeout=timeout)
        return msg.data

    def __notify_event_observers(
        self, msg: InMemoryMessage[ScopeT, DataT, MetadataT]
    ) -> None:
        """Emit an event."""
        queues_processed: t.Set[str] = set()
        for target, queue, observer in self.subscribers:
            if queue and queue in queues_processed:
                continue
            if not target.match_subject(msg.subject):
                continue
            try:
                observer.put_nowait(msg)
            except QueueFull:
                continue
            else:
                if queue:
                    queues_processed.add(queue)

    def __notify_command_observers(
        self, request: InMemoryRequest[ScopeT, DataT, MetadataT, ReplyT]
    ) -> None:
        """Emit an event."""
        queues_processed: t.Set[str] = set()
        for target, queue, responder in self.responders:
            if queue and queue in queues_processed:
                continue
            if not target.match_subject(request.subject):
                continue
            try:
                responder.put_nowait(request)
            except QueueFull:
                continue
            else:
                if queue:
                    queues_processed.add(queue)

    @asynccontextmanager
    async def subscribe(
        self,
        event: EventSpec[ScopeT, DataT, MetadataT, ReplyT],
        queue: t.Optional[str] = None,
    ) -> t.AsyncIterator[t.AsyncIterator[Message[ScopeT, DataT, MetadataT]]]:
        """Create a new observer, optionally within a queue."""
        queue = queue or ""
        observer: "AIOQueue[InMemoryMessage[ScopeT, DataT, MetadataT]]" = AIOQueue()
        key = (event, queue, observer)
        self.subscribers.append(key)
        current_task: t.Optional[Task[InMemoryMessage[ScopeT, DataT, MetadataT]]] = None

        async def iterator() -> t.AsyncIterator[Message[ScopeT, DataT, MetadataT]]:
            nonlocal current_task
            nonlocal observer
            while True:
                current_task = create_task(observer.get())
                yield await wait_for(current_task, timeout=None)

        try:
            yield iterator()
        finally:
            if current_task:
                current_task.cancel()
            self.subscribers.remove(key)

    @asynccontextmanager
    async def serve(
        self,
        event: EventSpec[ScopeT, DataT, MetadataT, ReplyT],
        queue: t.Optional[str] = None,
    ) -> t.AsyncIterator[t.AsyncIterator[Request[ScopeT, DataT, MetadataT, ReplyT]]]:
        queue = queue or ""
        observer: "AIOQueue[InMemoryRequest[ScopeT, DataT, MetadataT, ReplyT]]" = (
            AIOQueue()
        )
        key = (event, queue, observer)
        self.responders.append(key)
        current_task: t.Optional[
            Task[InMemoryRequest[ScopeT, DataT, MetadataT, ReplyT]]
        ] = None

        async def iterator() -> t.AsyncIterator[
            Request[ScopeT, DataT, MetadataT, ReplyT]
        ]:
            nonlocal current_task
            nonlocal observer
            while True:
                print("Waiting for an event")
                current_task = create_task(observer.get())
                yield await wait_for(current_task, timeout=None)

        try:
            yield iterator()
        finally:
            if current_task:
                current_task.cancel()
            self.responders.remove(key)

    def pull(
        self, queue: EventQueue[ScopeT, DataT, MetadataT]
    ) -> t.AsyncContextManager[t.AsyncIterator[Job[ScopeT, DataT, MetadataT]]]:
        raise NotImplementedError

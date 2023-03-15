import typing as t

from .events import Event, EventQueue, EventSpec, Service
from .interfaces import Job, Message, Request
from .types import DataT, MetadataT, ReplyT, ScopeT


class Actor:
    handler: t.Callable[
        [t.Any],
        t.Coroutine[t.Any, t.Any, t.Any],
    ]
    """Coroutine function executed each time actor is triggered using an event."""

    @property
    def source(
        self,
    ) -> t.Union[
        EventSpec[t.Any, t.Any, t.Any, t.Any], EventQueue[t.Any, t.Any, t.Any]
    ]:
        """Return source of events for actor"""
        raise NotImplementedError


class Subscriber(Actor, t.Generic[ScopeT, DataT, MetadataT]):
    event: Event[ScopeT, DataT, MetadataT]
    """Event triggering the actor."""

    handler: t.Callable[
        [
            Message[ScopeT, DataT, MetadataT],
        ],
        t.Coroutine[t.Any, t.Any, None],
    ]
    """Coroutine function executed each time actor is triggered using an event."""

    def __init__(
        self,
        event: Event[ScopeT, DataT, MetadataT],
        handler: t.Callable[
            [
                Message[ScopeT, DataT, MetadataT],
            ],
            t.Coroutine[t.Any, t.Any, None],
        ],
    ) -> None:
        super().__init__()
        self.event = event
        self.handler = handler

    @property
    def source(self) -> Event[ScopeT, DataT, MetadataT]:
        """Return source of events for actor"""
        return self.event


class Responder(Actor, t.Generic[ScopeT, DataT, MetadataT, ReplyT]):
    event: Service[ScopeT, DataT, MetadataT, ReplyT]
    """Event triggering the actor."""

    handler: t.Callable[
        [
            Request[ScopeT, DataT, MetadataT, ReplyT],
        ],
        t.Coroutine[t.Any, t.Any, ReplyT],
    ]
    """Coroutine function executed each time actor is triggered using an event."""

    def __init__(
        self,
        event: Service[ScopeT, DataT, MetadataT, ReplyT],
        handler: t.Callable[
            [
                Request[ScopeT, DataT, MetadataT, ReplyT],
            ],
            t.Coroutine[t.Any, t.Any, ReplyT],
        ],
    ) -> None:
        super().__init__()
        self.event = event
        self.handler = handler

    @property
    def source(self) -> Service[ScopeT, DataT, MetadataT, ReplyT]:
        """Return source of events for actor"""
        return self.event


class Consumer(Actor, t.Generic[ScopeT, DataT, MetadataT]):
    queue: EventQueue[ScopeT, DataT, MetadataT]
    """Event queue triggering the actor."""

    handler: t.Callable[
        [
            Job[ScopeT, DataT, MetadataT],
        ],
        t.Coroutine[t.Any, t.Any, None],
    ]
    """Coroutine function executed each time actor is triggered using an event."""

    def __init__(
        self,
        queue: EventQueue[ScopeT, DataT, MetadataT],
        handler: t.Callable[
            [
                Job[ScopeT, DataT, MetadataT],
            ],
            t.Coroutine[t.Any, t.Any, None],
        ],
    ) -> None:
        super().__init__()
        self.queue = queue
        self.handler = handler

    @property
    def source(self) -> EventQueue[ScopeT, DataT, MetadataT]:
        """Return source of events for actor"""
        return self.queue

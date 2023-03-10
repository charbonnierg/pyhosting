import typing as t
from contextlib import asynccontextmanager

from pyhosting.core import (
    Command,
    EventBus,
    Filter,
    Job,
    Message,
    Queue,
    Request,
    StaticEvent,
)

T = t.TypeVar("T")
ReplyT = t.TypeVar("ReplyT")


class NATSMessage(Message[T]):
    def __init__(self, event: StaticEvent[T], data: T) -> None:
        self._event = event
        self._data = data

    @property
    def subject(self) -> str:
        return self.event.name

    @property
    def event(self) -> StaticEvent[T]:
        return self._event

    @property
    def data(self) -> T:
        return self._data


class NATSRequest(Request[T, ReplyT]):
    def __init__(
        self,
        command: Command[T, ReplyT],
        data: T,
    ) -> None:
        self._command = command
        self._data = data

    @property
    def subject(self) -> str:
        return self._command.name

    @property
    def command(self) -> Command[T, ReplyT]:
        return self._command

    @property
    def event(self) -> StaticEvent[T]:
        return StaticEvent(self._command.name, self._command.schema)

    @property
    def reply_event(self) -> StaticEvent[ReplyT]:
        raise NotImplementedError

    @property
    def data(self) -> T:
        return self._data

    async def reply(self, payload: ReplyT) -> None:
        raise NotImplementedError


class NATSEventBus(EventBus):
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
        """Create a new NATS event bus."""
        pass

    async def publish(self, event: StaticEvent[T], payload: T) -> None:
        raise NotImplementedError

    async def request(
        self,
        command: Command[T, ReplyT],
        payload: T,
        timeout: t.Optional[float] = None,
    ) -> ReplyT:
        """Request an event."""
        raise NotImplementedError

    @asynccontextmanager
    async def events(
        self,
        event: t.Union[StaticEvent[T], Filter[T]],
        queue: t.Optional[str] = None,
    ) -> t.AsyncIterator[t.AsyncIterator[Message[T]]]:
        """Create a new observer, optionally within a queue."""
        raise NotImplementedError
        yield

    @asynccontextmanager
    async def commands(
        self, command: Command[T, ReplyT], queue: t.Optional[str] = None
    ) -> t.AsyncIterator[t.AsyncIterator[Request[T, ReplyT]]]:
        raise NotImplementedError
        yield

    def jobs(self, queue: Queue[T]) -> t.AsyncContextManager[t.AsyncIterator[Job[T]]]:
        raise NotImplementedError

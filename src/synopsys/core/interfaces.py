import typing as t

from .events import EventQueue, EventSpec
from .types import DataT, MetadataT, ReplyT, ScopeT

T = t.TypeVar("T")


class Codec(t.Protocol):
    def encode(self, data: t.Any) -> bytes:
        ...

    def decode(self, raw: bytes, schema: t.Type[T]) -> T:
        ...

    def parse_obj(self, data: t.Any, schema: t.Type[T]) -> T:
        ...


class BaseMessage(t.Protocol[ScopeT, DataT, MetadataT, ReplyT]):
    """A message is the container of an event."""

    @property
    def subject(self) -> str:
        ...  # pragma: no cover

    @property
    def scope(self) -> ScopeT:
        ...  # pragma: no cover

    @property
    def data(self) -> DataT:
        ...  # pragma: no cover

    @property
    def metadata(self) -> MetadataT:
        ...  # pragma: no cover

    @property
    def spec(self) -> EventSpec[ScopeT, DataT, MetadataT, ReplyT]:
        ...  # pragma: no cover


class Message(BaseMessage[ScopeT, DataT, MetadataT, None]):
    """A message is the container of an event without reply."""

    pass


class Request(BaseMessage[ScopeT, DataT, MetadataT, ReplyT]):
    """A request is the container of an event which must be replied to."""

    async def reply(self, payload: ReplyT) -> None:
        ...  # pragma: no cover


class Job(Message[ScopeT, DataT, MetadataT]):
    """A Job is a container of an event which must be acknowledged."""

    async def ack(self) -> None:
        ...  # pragma: no cover

    async def nack(self, delay: t.Optional[float] = None) -> None:
        ...  # pragma: no cover

    async def term(self) -> None:
        ...  # pragma: no cover


class AllowPublish(t.Protocol):
    """An interface used to publish events."""

    async def publish(
        self,
        event: EventSpec[ScopeT, DataT, MetadataT, t.Any],
        scope: ScopeT,
        payload: DataT,
        metadata: MetadataT,
        timeout: t.Optional[float] = None,
    ) -> None:
        """Publish and wait until event is flushed by underlying messaging system."""
        raise NotImplementedError  # pragma: no cover


class AllowRequest(t.Protocol):
    """An interface used to publish events and wait for reply."""

    async def request(
        self,
        event: EventSpec[ScopeT, DataT, MetadataT, ReplyT],
        scope: ScopeT,
        payload: DataT,
        metadata: MetadataT,
        timeout: t.Optional[float] = None,
    ) -> ReplyT:
        """Request and wait for reply."""
        raise NotImplementedError  # pragma: no cover


class AllowPush(t.Protocol):
    """An interface used to push job and wait until job is accepeted."""

    async def push(
        self,
        event: EventSpec[ScopeT, DataT, MetadataT, None],
        scope: ScopeT,
        payload: DataT,
        headers: MetadataT,
        timeout: t.Optional[float] = None,
    ) -> None:
        """Push and wait for acknowledgement."""
        raise NotImplementedError  # pragma: no cover


class AllowSubscribe(t.Protocol):
    """An interface used to subscribe to events."""

    def subscribe(
        self,
        event: EventSpec[ScopeT, DataT, MetadataT, None],
        queue: t.Optional[str] = None,
    ) -> t.AsyncContextManager[t.AsyncIterator[Message[ScopeT, DataT, MetadataT]]]:
        """Create an event observer.

        An event observer is an asynchronous context manager yielding an
        asynchronous iterator.
        This iterator can be used to iterate over received messages.
        Each message contains both the event definition and the event payload.

        Arguments:
            event: An event or an event filter to observe
            queue: An optional string indicating that observer belongs to a queue group.
                Within a queue group, each message is delivered to a single observer.

        Returns:
            An asynchronous context manager yielding an asynchronous iterator of messages.
        """
        ...  # pragma: no cover


class AllowReply(t.Protocol):
    """An interface used to subscribe to requests."""

    def serve(
        self,
        event: EventSpec[ScopeT, DataT, MetadataT, ReplyT],
        queue: t.Optional[str] = None,
    ) -> t.AsyncContextManager[
        t.AsyncIterator[Request[ScopeT, DataT, MetadataT, ReplyT]]
    ]:
        """Create a request observer.

        A request observer is an asynchronous context manager yielding an
        asynchronous iterator.
        This iterator can be used to iterate over received commands.
        Each command contains both the command definition and the command payload.

        Arguments:
            event: A service event to observe
            queue: An optional string indicating that observer belongs to a queue group.
                Within a queue group, each command is delivered to a single observer.

        Returns:
            An asynchronous context manager yielding an asynchronous iterator of requests.
        """
        ...  # pragma: no cover


class AllowPull(t.Protocol):
    """An interface used to subscribe to jobs."""

    def pull(
        self,
        queue: EventQueue[ScopeT, DataT, MetadataT],
    ) -> t.AsyncContextManager[t.AsyncIterator[Job[ScopeT, DataT, MetadataT]]]:
        """Create a job observer.

        A job observer is an asynchronous context manager yielding an
        asynchronous iterator.
        This iterator can be used to iterate over received jobs.

        Arguments:
            queue: An event queue to fetch jobs from.

        Returns:
            An asynchronous context manager yielding an asynchronous iterator of requests.
        """
        ...  # pragma: no cover


class PubSub(AllowPublish, AllowSubscribe, t.Protocol):
    """An interface used to subscribe to and publish events."""

    pass


class ReqRep(AllowRequest, AllowReply, t.Protocol):
    """An interface used to subscribe to requests and send requests."""

    pass


class PushPull(AllowPublish, AllowPull, t.Protocol):
    """An interface used to push and pull jobs."""

    pass


class EventBus(PubSub, ReqRep, PushPull, t.Protocol):
    """A complete event bus interface which can be used for various purposes."""

    pass

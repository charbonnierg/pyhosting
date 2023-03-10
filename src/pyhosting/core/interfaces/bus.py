import typing as t

from ..entities import Command, Queue
from ..entities.events import EventSpec
from .msg import Job, Message, Request

T = t.TypeVar("T")
ReplyT = t.TypeVar("ReplyT")
ParamsT = t.TypeVar("ParamsT", bound=t.Mapping[str, t.Any])


class EventBus(t.Protocol):
    """An event bus can be used to emit or request events.

    Supported usecases:
        - Publish/Subscribe: Publish an event / Subscribe to events
        - Request/Reply: Publish an event and wait for a reply / Subscribe to events and send reply
    """

    async def publish(
        self, event: EventSpec[ParamsT, T], payload: T, **kwargs: t.Any
    ) -> None:
        """Publish an event.

        Arguments:
            event: The definition of event to emit.
            payload: A typed payload as indicated within event definition.
            params: Params used to construct event subject.

        Returns:
            None
        """
        raise NotImplementedError  # pragma: no cover

    async def request(
        self,
        command: Command[T, ReplyT],
        payload: T,
        timeout: t.Optional[float] = None,
    ) -> ReplyT:
        """Publish an event and wait until a reply event is received.

        Arguments:
            command: The definition of command to send.
            payload: A typed payload as indicated within command definition.
            timeout: Duration before cancelling command and raising a timeout error.

        Returns:
            A typed reply as indicated within command definition.
        """
        raise NotImplementedError  # pragma: no cover

    def events(
        self,
        event: EventSpec[ParamsT, T],
        queue: t.Optional[str] = None,
    ) -> t.AsyncContextManager[t.AsyncIterator[Message[T]]]:
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

    def commands(
        self,
        command: Command[T, ReplyT],
        queue: t.Optional[str] = None,
    ) -> t.AsyncContextManager[t.AsyncIterator[Request[T, ReplyT]]]:
        """Create a command observer.

        A command observer is an asynchronous context manager yielding an
        asynchronous iterator.
        This iterator can be used to iterate over received commands.
        Each command contains both the command definition and the command payload.

        Arguments:
            command: A command to observe
            queue: An optional string indicating that observer belongs to a queue group.
                Within a queue group, each command is delivered to a single observer.

        Returns:
            An asynchronous context manager yielding an asynchronous iterator of requests.
        """
        ...  # pragma: no cover

    def jobs(self, queue: Queue[T]) -> t.AsyncContextManager[t.AsyncIterator[Job[T]]]:
        """Create a job observer.

        A job observer is an asynchronous context manager yielding an
        asynchronous iterator.
        This iterator can be used to iterate over scheduled jobs.
        Each job contains both the associated event definition and the event payload.

        Arguments:
            event: An event to observe
            queue: An optional string indicating that observer belongs to a queue group.
                Within a queue group, each job is delivered to a single observer.

        Returns:
            An asynchronous context manager yielding an asynchronous iterator of jobs.
        """
        # Assuming that we use static configuration for everything else:
        #  - Always durable
        #  - Filter subject is derivated from list of events (if provided)
        #  - AckPolicy is always explicit
        #  - ReplayPolicy is always instant
        #  - Replicas is always 1
        #  - MemoryStorage is always false
        #  - SampleFrequency is always 10%
        #  - MaxDeliver is always -1
        ...  # pragma: no cover

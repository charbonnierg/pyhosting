import typing as t
from enum import Enum

from .events import StaticEvent

T = t.TypeVar("T")


class QueuePolicy(str, Enum):
    """Allowed queue policies"""

    ALL = "ALL"
    LAST = "LAST"
    NEW = "NEW"


class Stream(t.Generic[T]):
    """A stream is a source of events."""

    name: str
    """The stream name"""

    events: t.List[StaticEvent[T]]
    """A list of events."""

    limit: t.Optional[int] = None
    """Maximum number of messages to keep within stream."""


class Queue(t.Generic[T]):
    """A queue is a stateful view of a stream. It acts as interface for clients to consume a subset of messages stored in a stream and will keep track of which messages were delivered and acknowledged by clients."""

    name: str
    """The name of the queue."""

    stream: Stream[T]
    """The stream associated with the consumer."""

    events: t.List[StaticEvent[T]]
    """A subset of events tracked by the queue."""

    max_pending: int
    """Defines the maximum number of messages, without an acknowledgement, that can be outstanding.

    Once this limit is reached message delivery will be suspended.
    """

    max_wait: float
    """The duration that the server will wait for an ack for any individual message once it has been delivered to a consumer.

    If an ack is not received in time, the message will be redelivered.
    """

    inactive_theshold: float
    """Duration that instructs the server to cleanup consumers that are inactive for that long"""

    policy: QueuePolicy
    """The point in the stream to receive messages from."""

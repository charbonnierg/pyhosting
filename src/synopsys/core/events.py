"""An attempt to implement a Python API to define events in a declarative fashion.

In this module, an event is a specification, it is not a message which is delivered accross the network.

In practice, messages are the interfaces holding event data, and message bus are the interfaces delivering messages.

This specification does not make assumptions on the underlying messaging system, but still provides
a type safe API which can be used to publish, request and subscribe to event messages.

The main motivation is to stop writing code at the domain level interacting with subject or addresses,
but instead, target domain events.

Use cases should not care about message bus or messages, but should care about events.

This API has been designed in order to allow integration with messaging system as easy as possible.

See ..interfaces subpackage in order to learn more about integration with messaging systems.
"""
import typing as t
from enum import Enum

from .syntax import DEFAULT_SYNTAX, FilterSyntax
from .types import EMPTY, DataT, MetadataT, ReplyT, ScopeT
from .utils import (
    extract_subject_placeholders,
    filter_match,
    normalize_filter_subject,
    render_subject,
)

__all__ = [
    "EMPTY",
    "EMPTY",
    "EMPTY",
    "EventSpec",
    "Service",
    "Event",
    "StaticEvent",
    "StaticService",
    "FilterSyntax",
]


class EventSpec(t.Generic[ScopeT, DataT, MetadataT, ReplyT]):
    """An event is a specification.

    In practice, events are delivered through messages.

    A message is addressed on a subject, with a payload, and some headers.

    - The Scope type defines the typed attributes which can be extracted from the message subject.
    - The Data type defines the typed object which can be extract from the message payload.
    - The MetadataT type defines the typed object which can be extracted from the message headers.
    - The Reply type defines the typed object which can be extracted from the reply message payload.
    """

    name: str
    """The event name."""

    title: str
    """The event title."""

    description: str
    """A short description for the event."""

    address: str
    """The event address. Similar to NATS subjects, MQTT topics, or Kafka topics."""

    scope: t.Type[ScopeT]
    """The parameters used to construct a valid event address."""

    schema: t.Type[DataT]
    """The event schema, I.E, the schema of the data found in event messages."""

    reply_schema: t.Type[ReplyT]
    """The reply schema, I.E, the schema of the data found in event reply."""

    metadata_schema: t.Type[MetadataT]
    """The metadata schema, I.E, the schema of the data found in the headers of event messages."""

    def __init__(
        self,
        name: str,
        address: str,
        scope: t.Type[ScopeT],
        schema: t.Type[DataT],
        reply_schema: t.Type[ReplyT],
        metadata_schema: t.Type[MetadataT],
        title: t.Optional[str] = None,
        description: t.Optional[str] = None,
        syntax: t.Optional[FilterSyntax] = None,
    ) -> None:
        """Create a new event using a subjet and a schema."""
        if not name:
            raise ValueError("Name cannot be empty")
        if not address:
            raise ValueError("Address cannot be empty")
        self.name = name
        self.address = address
        self.scope = scope
        self.schema = schema
        self.reply_schema = reply_schema
        self.metadata_schema = metadata_schema
        self.title = title or name
        self.description = description or ""
        self.syntax = syntax or DEFAULT_SYNTAX
        # Save some attributes to easily match or extract subjects
        self._subject, self._placeholders = normalize_filter_subject(
            self.address, self.syntax
        )
        self._tokens = self._subject.split(self.syntax.match_sep)
        # Do not validate the address if scope does not have annotations
        if not hasattr(self.scope, "__annotations__"):
            return
        # Ensure that address is valid according to scope annotations
        if len(self.scope.__annotations__) > len(self._placeholders):
            missing = list(
                set(self.scope.__annotations__).difference(self._placeholders)
            )
            raise ValueError(
                f"Not enough placeholders in address or unexpected scope variable. Missing in address: {missing}"
            )
        if len(self.scope.__annotations__) < len(self._placeholders):
            unexpected = list(
                set(self._placeholders).difference(self.scope.__annotations__)
            )
            raise ValueError(
                f"Too many placeholders in address or missing scope variables. Did not expect in address: {unexpected}"
            )

    def __repr__(self) -> str:
        return f"Event(name='{self.name}', address='{self.address}', schema={self.schema.__name__})"

    def match_subject(self, subject: str) -> bool:
        """Return True if event matches given subject."""
        return filter_match(self._subject, subject, self.syntax)

    def get_subject(self, scope: ScopeT) -> str:
        """Construct a subject using given scope."""
        return render_subject(
            tokens=self._tokens,
            placeholders=self._placeholders,
            context=scope,
            syntax=self.syntax,
        )

    def extract_scope(self, subject: str) -> ScopeT:
        """Extract placeholders from subject"""
        return t.cast(
            ScopeT,
            extract_subject_placeholders(subject, self._placeholders, self.syntax),
        )


class Service(EventSpec[ScopeT, DataT, MetadataT, ReplyT]):
    pass


class StaticService(Service[None, DataT, MetadataT, ReplyT]):
    def __init__(
        self,
        name: str,
        address: str,
        schema: t.Type[DataT],
        reply_schema: t.Type[ReplyT],
        metadata_schema: t.Type[MetadataT],
        title: t.Optional[str] = None,
        description: t.Optional[str] = None,
        syntax: t.Optional[FilterSyntax] = None,
    ) -> None:
        super().__init__(
            name,
            address,
            EMPTY,
            schema,
            reply_schema,
            metadata_schema,
            title,
            description,
            syntax,
        )

    def get_subject(self, scope: None = None) -> str:
        return super().get_subject(scope)


class Event(EventSpec[ScopeT, DataT, MetadataT, None]):
    def __init__(
        self,
        name: str,
        address: str,
        scope: t.Type[ScopeT],
        schema: t.Type[DataT],
        metadata_schema: t.Type[MetadataT],
        title: t.Optional[str] = None,
        description: t.Optional[str] = None,
        syntax: t.Optional[FilterSyntax] = None,
    ) -> None:
        super().__init__(
            name,
            address,
            scope,
            schema,
            EMPTY,
            metadata_schema,
            title,
            description,
            syntax,
        )


class StaticEvent(Event[None, DataT, MetadataT]):
    def __init__(
        self,
        name: str,
        address: str,
        schema: t.Type[DataT],
        metadata_schema: t.Type[MetadataT],
        title: t.Optional[str] = None,
        description: t.Optional[str] = None,
        syntax: t.Optional[FilterSyntax] = None,
    ) -> None:
        super().__init__(
            name=name,
            address=address,
            schema=schema,
            scope=EMPTY,
            metadata_schema=metadata_schema,
            title=title,
            description=description,
            syntax=syntax,
        )

    def get_subject(self, scope: None = None) -> str:
        return super().get_subject(scope)


class QueuePolicy(str, Enum):
    """Allowed queue policies"""

    ALL = "ALL"
    LAST = "LAST"
    NEW = "NEW"


class EventStream:
    """A stream is a source of events."""

    name: str
    """The stream name"""

    events: t.List[Event[t.Any, t.Any, t.Any]]
    """A list of events."""

    limit: t.Optional[int] = None
    """Maximum number of messages to keep within stream."""


class EventQueue(t.Generic[ScopeT, DataT, MetadataT]):
    """A queue is a stateful view of a stream. It acts as interface for clients to consume a subset of messages stored in a stream and will keep track of which messages were delivered and acknowledged by clients."""

    name: str
    """The name of the queue."""

    stream: EventStream
    """The stream associated with the consumer."""

    filters: t.Optional[t.List[Event[ScopeT, DataT, MetadataT]]]
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

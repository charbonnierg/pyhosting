import typing as t

from .events import Event, EventSpec, FilterSyntax, Service, StaticEvent, StaticService
from .types import EMPTY, DataT, MetadataT, ReplyT, ScopeT

__all__ = ["EMPTY", "create_event"]


@t.overload
def create_event(
    name: str,
    address: str,
    schema: t.Type[DataT],
    *,
    metadata_schema: None = None,
    title: t.Optional[str] = None,
    description: t.Optional[str] = None,
    syntax: t.Optional[FilterSyntax] = None,
) -> StaticEvent[DataT, None]:
    """Create a static event without metadata."""
    ...  # pragma: no cover


@t.overload
def create_event(
    name: str,
    address: str,
    schema: t.Type[DataT],
    *,
    metadata_schema: t.Type[MetadataT],
    title: t.Optional[str] = None,
    description: t.Optional[str] = None,
    syntax: t.Optional[FilterSyntax] = None,
) -> StaticEvent[DataT, MetadataT]:
    """Create a static event with metadata."""
    ...  # pragma: no cover


@t.overload
def create_event(
    name: str,
    address: str,
    schema: t.Type[DataT],
    *,
    scope: t.Type[ScopeT],
    metadata_schema: None = None,
    title: t.Optional[str] = None,
    description: t.Optional[str] = None,
    syntax: t.Optional[FilterSyntax] = None,
) -> Event[ScopeT, DataT, None]:
    """Create an event with a scope."""
    ...  # pragma: no cover


@t.overload
def create_event(
    name: str,
    address: str,
    schema: t.Type[DataT],
    *,
    scope: t.Type[ScopeT],
    metadata_schema: t.Type[MetadataT],
    title: t.Optional[str] = None,
    description: t.Optional[str] = None,
    syntax: t.Optional[FilterSyntax] = None,
) -> Event[ScopeT, DataT, MetadataT]:
    """Create an event with a scope and metadata."""
    ...  # pragma: no cover


@t.overload
def create_event(
    name: str,
    address: str,
    schema: t.Type[DataT],
    *,
    scope: t.Type[ScopeT],
    reply_schema: t.Type[ReplyT],
    metadata_schema: t.Type[MetadataT],
    title: t.Optional[str] = None,
    description: t.Optional[str] = None,
    syntax: t.Optional[FilterSyntax] = None,
) -> Service[ScopeT, DataT, MetadataT, ReplyT]:
    """Create a service event with scope and metadata."""
    ...  # pragma: no cover


@t.overload
def create_event(
    name: str,
    address: str,
    schema: t.Type[DataT],
    *,
    reply_schema: t.Type[ReplyT],
    metadata_schema: t.Type[MetadataT],
    title: t.Optional[str] = None,
    description: t.Optional[str] = None,
    syntax: t.Optional[FilterSyntax] = None,
) -> StaticService[DataT, MetadataT, ReplyT]:
    """Create a static service event with metadata."""
    ...  # pragma: no cover


@t.overload
def create_event(
    name: str,
    address: str,
    schema: t.Type[DataT],
    *,
    scope: t.Type[ScopeT],
    reply_schema: t.Type[ReplyT],
    title: t.Optional[str] = None,
    description: t.Optional[str] = None,
    syntax: t.Optional[FilterSyntax] = None,
) -> Service[ScopeT, DataT, None, ReplyT]:
    """Create a service event with a scope."""
    ...  # pragma: no cover


@t.overload
def create_event(
    name: str,
    address: str,
    schema: t.Type[DataT],
    *,
    reply_schema: t.Type[ReplyT],
    title: t.Optional[str] = None,
    description: t.Optional[str] = None,
    syntax: t.Optional[FilterSyntax] = None,
) -> StaticService[DataT, None, ReplyT]:
    """Create a static service."""
    ...  # pragma: no cover


def create_event(
    name: str,
    address: str,
    schema: t.Type[DataT],
    *,
    scope: t.Any = EMPTY,
    reply_schema: t.Any = ...,
    metadata_schema: t.Any = EMPTY,
    title: t.Optional[str] = None,
    description: t.Optional[str] = None,
    syntax: t.Optional[FilterSyntax] = None,
) -> EventSpec[t.Any, DataT, t.Any, t.Any]:
    # Handle events
    if reply_schema is ...:
        # Handle static events
        if scope is EMPTY:
            return StaticEvent(
                name=name,
                address=address,
                schema=schema,
                metadata_schema=metadata_schema,
                title=title,
                description=description,
                syntax=syntax,
            )
        return Event(
            name=name,
            address=address,
            schema=schema,
            scope=scope,
            metadata_schema=metadata_schema,
            title=title,
            description=description,
            syntax=syntax,
        )
    # Handle static service events
    if scope is EMPTY:
        return StaticService(
            name=name,
            address=address,
            schema=schema,
            reply_schema=reply_schema,
            metadata_schema=metadata_schema,
            title=title,
            description=description,
            syntax=syntax,
        )
    # Handle service events
    return Service(
        name=name,
        address=address,
        schema=schema,
        scope=scope,
        reply_schema=reply_schema,
        metadata_schema=metadata_schema,
        title=title,
        description=description,
        syntax=syntax,
    )

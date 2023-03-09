import typing as t

T = t.TypeVar("T")


class Event(t.Generic[T]):
    """An event is the combination of a subject and a schema."""

    name: str
    """The event name, I.E, the subject on which event messages are observed."""

    schema: t.Type[T]
    """The event schema, I.E, the schema of the data found in event messages."""

    @property
    def subject(self) -> str:
        """The event subject."""
        return self.name

    def __init__(
        self,
        name: str,
        schema: t.Type[T],
    ) -> None:
        """Create a new event using a subjet and a schema."""
        self.name = name
        self.schema = schema


class Filter(t.Generic[T]):
    """An event filter is a combination of a subject filter and a schema."""

    filter: str
    """The event filter, I.E, the subject filter from which event messages are observed."""

    schema: t.Type[T]
    """The event schema, I.E, the schema of the data found in event messages."""

    @property
    def subject(self) -> str:
        """The event filter subject."""
        return self.filter

    def __init__(
        self,
        filter: str,
        schema: t.Type[T],
    ) -> None:
        """Create a new event using a subjet and a schema."""
        self.filter = filter
        self.schema = schema

import typing as t

if t.TYPE_CHECKING:  # pragma: no cover
    from ..entities import StaticEvent
    from ..interfaces import Message


T = t.TypeVar("T")


class Actor(t.Generic[T]):
    """An actor can be used to process received events."""

    event: "StaticEvent[T]"
    """The event the service expects"""

    handler: t.Callable[["Message[T]"], t.Coroutine[None, None, None]]
    """The coroutine function used to process events."""

    def __init__(
        self,
        event: "StaticEvent[T]",
        handler: t.Callable[["Message[T]"], t.Coroutine[None, None, None]],
    ) -> None:
        self.event = event
        self.handler = handler

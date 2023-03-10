import typing as t

from ..entities import Command

if t.TYPE_CHECKING:
    from ..interfaces import Request  # pragma: no cover


T = t.TypeVar("T")
ReplyT = t.TypeVar("ReplyT")


class Service(t.Generic[T, ReplyT]):
    """A service can be used to process received commands."""

    command: Command[T, ReplyT]
    """The command the service expects"""

    handler: t.Callable[["Request[T, ReplyT]"], t.Coroutine[None, None, ReplyT]]
    """The coroutine function used to process commands."""

    def __init__(
        self,
        command: Command[T, ReplyT],
        handler: t.Callable[["Request[T, ReplyT]"], t.Coroutine[None, None, ReplyT]],
    ) -> None:
        self.command = command
        self.handler = handler

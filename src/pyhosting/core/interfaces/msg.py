import typing as t

from ..entities import Command, Event, Stream

T = t.TypeVar("T")
ReplyT = t.TypeVar("ReplyT")


class Message(t.Protocol[T]):
    """A message is the container of an event."""

    @property
    def subject(self) -> str:
        ...

    @property
    def event(self) -> Event[T]:
        ...  # pragma: no cover

    @property
    def data(self) -> T:
        ...  # pragma: no cover


class Request(t.Protocol[T, ReplyT]):
    """A request the container of a command."""

    @property
    def subject(self) -> str:
        ...  # pragma: no cover

    @property
    def command(self) -> Command[T, ReplyT]:
        ...  # pragma: no cover

    @property
    def data(self) -> T:
        ...  # pragma: no cover

    async def reply(self, payload: ReplyT) -> None:
        ...  # pragma: no cover


class Job(t.Protocol[T]):
    """A Job is a container of an event which must be acknowledged."""

    @property
    def subject(self) -> str:
        ...

    @property
    def stream(self) -> Stream[T]:
        ...  # pragma: no cover

    @property
    def event(self) -> Event[T]:
        ...  # pragma: no cover

    @property
    def data(self) -> T:
        ...  # pragma: no cover

    async def ack(self) -> None:
        ...  # pragma: no cover

    async def nack(self, delay: t.Optional[float] = None) -> None:
        ...  # pragma: no cover

    async def term(self) -> None:
        ...  # pragma: no cover

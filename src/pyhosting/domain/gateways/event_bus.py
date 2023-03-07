import abc
import typing as t

T = t.TypeVar("T")


class EventBusGateway:
    """An event bus can be used to emit events."""

    @abc.abstractmethod
    async def emit_event(self, event: t.Tuple[str, t.Type[T]], payload: T) -> None:
        """Emit an event."""
        raise NotImplementedError

    @abc.abstractmethod
    async def wait_for_event(self, event: t.Tuple[str, t.Type[T]]) -> T:
        """Wait for an event"""
        raise NotImplementedError

    @abc.abstractmethod
    def watch_events(
        self, event: t.Tuple[str, t.Type[T]]
    ) -> t.AsyncContextManager[t.AsyncIterator[T]]:
        """Watch a type of event"""
        raise NotImplementedError

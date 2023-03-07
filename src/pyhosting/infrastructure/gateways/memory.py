import typing as t
from asyncio import Queue, QueueFull, Task, create_task
from contextlib import asynccontextmanager

from ...domain.gateways import BlobStorageGateway, EventBusGateway

T = t.TypeVar("T")


class InMemoryBlobStorage(BlobStorageGateway):
    def __init__(self) -> None:
        self._store: t.Dict[str, bytes] = {}

    async def get_version(self, page_id: str, page_version: str) -> t.Optional[bytes]:
        key = "/".join([page_id, page_version])
        return self._store.get(key, None)

    async def put_version(
        self, page_id: str, page_version: str, content: bytes
    ) -> None:
        key = "/".join([page_id, page_version])
        self._store[key] = content

    async def delete_version(self, page_id: str, page_version: str) -> bool:
        key = "/".join([page_id, page_version])
        return self._store.pop(key, None) is not None

    async def list_versions(self, page_id: str) -> t.List[str]:
        return [key for key in self._store if key.startswith(page_id)]


class InMemoryEventBus(EventBusGateway):
    def __init__(self) -> None:
        self.observers: t.List[t.Tuple[str, Queue[t.Tuple[str, t.Any]]]] = []

    async def emit_event(self, event: t.Tuple[str, t.Type[T]], payload: T) -> None:
        """Emit an event."""
        for event_kind, observer in self.observers:
            if event_kind and event[0] != event_kind:
                continue
            try:
                observer.put_nowait((event[0], payload))
            except QueueFull:
                continue

    async def wait_for_event(
        self, event: t.Optional[t.Tuple[str, t.Type[T]]] = None
    ) -> T:
        """Wait for an event."""
        observer: "Queue[t.Tuple[str, t.Any]]" = Queue()
        event_kind = event[0] if event else ""
        self.observers.append((event_kind, observer))
        next_event: t.Tuple[str, T] = await observer.get()
        self.observers.remove((event_kind, observer))
        return next_event[1]

    @asynccontextmanager
    async def watch_events(
        self, event: t.Tuple[str, t.Type[T]]
    ) -> t.AsyncIterator[t.AsyncIterator[T]]:
        observer: "Queue[t.Tuple[str, t.Any]]" = Queue()
        event_kind = event[0] if event else ""
        self.observers.append((event_kind, observer))
        current_task: t.Optional[Task[t.Tuple[str, T]]] = None

        async def iterator() -> t.AsyncIterator[T]:
            nonlocal current_task
            nonlocal observer
            while True:
                current_task = create_task(observer.get())
                _, event = await current_task
                yield event

        try:
            yield iterator()
        finally:
            if current_task:
                current_task.cancel()
            self.observers.remove((event_kind, observer))
            del observer

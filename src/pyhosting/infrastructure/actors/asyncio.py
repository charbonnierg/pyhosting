import asyncio
import sys
import typing as t
from contextlib import AsyncExitStack, asynccontextmanager
from logging import getLogger

from ...domain.gateways import EventBusGateway


T = t.TypeVar("T")

logger = getLogger("actors")


class Actor(t.Protocol):
    @property
    def event(self) -> t.Tuple[str, t.Type[t.Any]]:
        ...  # pragma: no covert

    async def process_event(self, event: t.Any) -> None:
        ...  # pragma: no cover


class AsyncioActors:
    def __init__(
        self,
        actors: t.List[Actor],
        event_bus: EventBusGateway,
    ) -> None:
        self.stack = AsyncExitStack()
        self.event_bus = event_bus
        self.actors = actors
        self.tasks: t.List[asyncio.Task[None]] = []

    def wrap_actor(
        self, actor: Actor
    ) -> t.Callable[[t.AsyncIterator[t.Any]], t.Coroutine[None, None, None]]:
        async def task(iterator: t.AsyncIterator[T]) -> None:
            logger.info(
                f"Started actor {actor.__class__.__name__} for event: {actor.event[0]}"
            )
            async for event in iterator:
                logger.info(f"Received event: {actor.event[0]}")
                await actor.process_event(event)

        return task

    async def start(self) -> None:
        await self.stack.__aenter__()
        for actor in self.actors:
            watcher = self.wrap_actor(actor)
            manager = self.event_bus.watch_events(actor.event)
            iterator = await self.stack.enter_async_context(manager)
            self.tasks.append(asyncio.create_task(watcher(iterator)))

    async def wait(self, timeout: t.Optional[float] = None) -> None:
        await asyncio.wait(self.tasks, timeout=timeout)

    async def stop(self, timeout: t.Optional[float] = None) -> None:
        await self.stack.__aexit__(*sys.exc_info())
        await self.wait(timeout=timeout)

    @asynccontextmanager
    async def lifespan(self, app: t.Any) -> t.AsyncIterator["AsyncioActors"]:
        await self.start()
        try:
            yield self
        finally:
            await self.stop()

    def extend(self, actors: t.List[Actor]) -> None:
        self.actors.extend(actors)

    def get_first_exception(self) -> t.Optional[BaseException]:
        for task in self.tasks:
            if not task.done():
                continue
            if task.cancelled():
                return asyncio.CancelledError(task)
            err = task.exception()
            if err:
                return err
        return None

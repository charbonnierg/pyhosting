import asyncio
import sys
import typing as t
from contextlib import AsyncExitStack

from ..core.actors import Actor, Consumer, Responder, Subscriber
from ..core.interfaces import EventBus, Job, Message, Request
from ..core.types import DataT, MetadataT, ReplyT, ScopeT
from .errors import ExceptionGroup


class Play:
    def __init__(
        self,
        bus: EventBus,
        actors: t.Iterable[Actor],
        queue: t.Optional[str] = None,
    ) -> None:
        """Create a new play with actors.

        When queue is provided, all actors belong to the same queue,
        except Consumers.
        Consumers ignore the queue option because they allow exactly once
        delivery regardless of the queue option.
        """
        self.actors = list(actors)
        self.bus = bus
        # Initialize state
        self.tasks: t.List[asyncio.Task[None]] = []
        self.stack: t.Optional[AsyncExitStack] = None

    async def __aenter__(self) -> "Play":
        """Implement asynchronous context manager."""
        await self.start()
        return self

    async def __aexit__(self, *_: t.Any, **__: t.Any) -> None:
        """Implement asynchronous context manager."""
        await self.stop()

    def _collect_exceptions(self) -> t.Iterator[BaseException]:
        """Collect all actors tasks exceptions"""
        for task in self.tasks:
            if not task.done():
                continue
            if task.cancelled():
                continue
            else:
                err = task.exception()
                if err:
                    yield err

    def _cancel_on_first_exception(
        self, _: Actor
    ) -> t.Callable[["asyncio.Task[None]"], None]:
        """Create a done callback for an actor."""

        def callback(task_done: "asyncio.Task[None]") -> None:
            """Cancel remaining actors tasks on first task completion (success or error)"""
            if task_done.cancelled():
                return
            elif task_done.exception():
                for task in self.tasks:
                    if not task.done():
                        task.cancel()

        return callback

    def _process_requests_iterator(
        self, actor: Responder[ScopeT, DataT, MetadataT, ReplyT]
    ) -> t.Callable[
        [t.AsyncIterator[Request[ScopeT, DataT, MetadataT, ReplyT]]],
        t.Coroutine[t.Any, t.Any, None],
    ]:
        async def task(
            iterator: t.AsyncIterator[Request[ScopeT, DataT, MetadataT, ReplyT]]
        ) -> None:
            """Task defined for each responder"""
            print("Starting iterator")
            # Services receive tuples of (event, reply)
            async for request in iterator:
                print("Received a request")
                try:
                    # Handle command
                    result = await actor.handler(request)
                    # Reply result
                    await request.reply(result)
                except BaseException as exc:  # noqa: F841
                    # Log and exit on exception.
                    print("FAILURE")
                    # What to do ??
                    raise

        return task

    def _process_events_iterator(
        self, actor: Subscriber[ScopeT, DataT, MetadataT]
    ) -> t.Callable[
        [t.AsyncIterator[Message[ScopeT, DataT, MetadataT]]],
        t.Coroutine[t.Any, t.Any, None],
    ]:
        async def task(
            iterator: t.AsyncIterator[Message[ScopeT, DataT, MetadataT]]
        ) -> None:
            """Task defined for each subscriber"""
            async for event in iterator:
                try:
                    await actor.handler(event)
                except BaseException as exc:  # noqa: F841
                    # Log and exit on exception.
                    # What to do ???
                    raise

        return task

    def _process_jobs_iterator(
        self, actor: Consumer[ScopeT, DataT, MetadataT]
    ) -> t.Callable[
        [t.AsyncIterator[Job[ScopeT, DataT, MetadataT]]],
        t.Coroutine[t.Any, t.Any, None],
    ]:
        async def task(
            iterator: t.AsyncIterator[Job[ScopeT, DataT, MetadataT]]
        ) -> None:
            """Task defined for each consumer"""
            async for event in iterator:
                # Do we want to auto-ack ??
                try:
                    await actor.handler(event)
                except BaseException as exc:  # noqa: F841
                    # Log and exit on exception.
                    # What to do ???
                    raise

        return task

    def cancel(self) -> None:
        for task in self.tasks:
            if not task.done():
                task.cancel()

    async def start(self) -> None:
        """Start the actor group."""
        if self.stack is not None:
            return
        self.stack = AsyncExitStack()
        await self.stack.__aenter__()
        for actor in self.actors:
            if isinstance(actor, Responder):
                request_handler = self._process_requests_iterator(actor)
                request_iterator = await self.stack.enter_async_context(
                    self.bus.serve(actor.event)
                )
                task = asyncio.create_task(request_handler(request_iterator))
            elif isinstance(actor, Subscriber):
                message_handler = self._process_events_iterator(actor)
                message_iterator = await self.stack.enter_async_context(
                    self.bus.subscribe(actor.event)
                )
                task = asyncio.create_task(message_handler(message_iterator))
            elif isinstance(actor, Consumer):
                job_handler = self._process_jobs_iterator(actor)
                job_iterator = await self.stack.enter_async_context(
                    self.bus.pull(actor.queue)
                )
                task = asyncio.create_task(job_handler(job_iterator))
            else:
                raise TypeError(f"Actor type not supported: {type(actor)}")
            task.add_done_callback(self._cancel_on_first_exception(actor))
            self.tasks.append(task)

    async def stop(self, timeout: t.Optional[float] = None) -> None:
        """Stop actor group."""
        if self.stack is None:
            return
        await self.stack.__aexit__(*sys.exc_info())
        await self.wait(timeout=timeout)
        errors = self.errors()
        if errors:
            raise ExceptionGroup(errors)

    async def wait(self, timeout: t.Optional[float] = None) -> None:
        """Wait until the play is stopped (until all actors are stopped)."""
        try:
            await asyncio.wait(
                self.tasks, timeout=timeout, return_when=asyncio.ALL_COMPLETED
            )
        # Raised when an exception is raised within a task and future is not set
        except ValueError:
            pass

    def errors(self) -> t.List[BaseException]:
        """Get all errors raised by actors during play which are not cancelled errors."""
        return list(self._collect_exceptions())

    def started(self) -> bool:
        """Return True if play is started."""
        return self.stack is not None

    def done(self) -> bool:
        """Return True if play is finished."""
        if self.tasks:
            return all(task.done() for task in self.tasks)
        return False

    def extend(self, *actors: Actor) -> None:
        """Extend play with new actors."""
        if self.started():
            raise RuntimeError("Cannot extend play after it is started.")
        self.actors.extend(actors)

import asyncio
import sys
import typing as t
from contextlib import AsyncExitStack
from dataclasses import dataclass

from ..entities import Actor, Service
from ..errors import ExceptionGroup
from ..interfaces import EventBus, Message, Request

T = t.TypeVar("T")
ReplyT = t.TypeVar("ReplyT")


@dataclass
class ActorsInstrumentation:
    """Configure how an actor group should be instrumented."""

    actor_started: t.Callable[[Actor[t.Any]], None] = lambda _: None
    """Observe actor started."""

    actor_cancelled: t.Callable[[Actor[t.Any]], None] = lambda _: None
    """Observe actor being cancelled."""

    actor_failed: t.Callable[
        [Actor[T], Message[T], BaseException], None
    ] = lambda _, __, ___: None
    """Observe an exception raised by an actor."""

    event_processed: t.Callable[[Actor[T], Message[T]], None] = lambda _, __: None
    """Observe a successful event processed."""

    service_started: t.Callable[[Service[t.Any, t.Any]], None] = lambda _: None
    """Observe service started."""

    service_cancelled: t.Callable[[Service[t.Any, t.Any]], None] = lambda _: None
    """Observe service being cancelled."""

    service_failed: t.Callable[
        [Service[T, ReplyT], Request[T, ReplyT], BaseException], None
    ] = lambda _, __, ___: None
    """Observe an exception raised by a service."""

    command_processed: t.Callable[
        [Service[T, ReplyT], Request[T, ReplyT]], None
    ] = lambda _, __: None
    """Observe a successful command processed"""

    group_starting: t.Callable[["AsyncioActors"], None] = lambda _: None
    """Observe group starting."""

    group_started: t.Callable[["AsyncioActors"], None] = lambda _: None
    """Observe group started."""

    group_stopping: t.Callable[["AsyncioActors"], None] = lambda _: None
    """Observe group stopping."""

    group_failed: t.Callable[
        ["AsyncioActors", t.List[BaseException]], None
    ] = lambda _, __: None
    """Observe actors group failure"""

    group_stopped: t.Callable[["AsyncioActors"], None] = lambda _: None
    """Observe actors group stopped"""


class AsyncioActors:
    """Configure a group of actors to listen to some observable.

    - When group is started, actors start to process observable data.
    - When group is stopped, actors are also stopped.
    - All actors must be running in order for the group to be alive.
    - When any actor encouter an error, all actors are cancelled and
    group is cancelled.
    """

    def __init__(
        self,
        bus: EventBus,
        actors: t.List[t.Union[Service[t.Any, t.Any], Actor[t.Any]]],
        queue: t.Optional[str] = None,
        instrumentation: t.Optional[ActorsInstrumentation] = None,
    ) -> None:
        """Create new group of actors ready to process observable data."""
        # Store dependencies
        self._actors = actors
        self._bus = bus
        self._instrumentation = instrumentation or ActorsInstrumentation()
        # Store public attributes
        self.queue = queue
        # Initialize state
        self.tasks: t.List[asyncio.Task[None]] = []
        self.stack: t.Optional[AsyncExitStack] = None

    async def __aenter__(self) -> "AsyncioActors":
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
        self, actor: t.Union[Actor[t.Any], Service[t.Any, t.Any]]
    ) -> t.Callable[["asyncio.Task[None]"], None]:
        observe: t.Union[
            t.Callable[[Actor[t.Any]], None],
            t.Callable[[Service[t.Any, t.Any]], None],
        ]
        if isinstance(actor, Service):
            observe = self._instrumentation.actor_cancelled
        else:
            observe = self._instrumentation.service_cancelled

        def callback(task_done: "asyncio.Task[None]") -> None:
            """Cancel remaining actors tasks on first task completion (success or error)"""
            if task_done.cancelled():
                observe(self._actors[self.tasks.index(task_done)])  # type: ignore[arg-type]
            elif task_done.exception():
                for task in self.tasks:
                    if not task.done():
                        task.cancel()

        return callback

    def _process_actor_iterator(
        self, actor: Actor[T]
    ) -> t.Callable[[t.AsyncIterator[Message[T]]], t.Coroutine[None, None, None]]:
        """Use actor to process events received from an iterator."""

        async def task(iterator: t.AsyncIterator[Message[T]]) -> None:
            """Task defined for each actor"""
            async for event in iterator:
                try:
                    await actor.handler(event)
                except BaseException as exc:
                    # Log and exit on exception.
                    self._instrumentation.actor_failed(actor, event, exc)
                    raise
                else:
                    self._instrumentation.event_processed(actor, event)

        return task

    def _process_service_iterator(
        self, service: Service[T, ReplyT]
    ) -> t.Callable[
        [t.AsyncIterator[Request[T, ReplyT]]], t.Coroutine[None, None, None]
    ]:
        """Use actor to process events received from an iterator."""

        async def task(iterator: t.AsyncIterator[Request[T, ReplyT]]) -> None:
            """Task defined for each actor"""
            # Services receive tuples of (event, reply)
            async for request in iterator:
                try:
                    # Handle command
                    result = await service.handler(request)
                    # Reply result
                    await request.reply(result)
                except BaseException as exc:
                    # Log and exit on exception.
                    self._instrumentation.service_failed(service, request, exc)
                    raise
                else:
                    self._instrumentation.command_processed(service, request)

        return task

    async def start(self) -> None:
        """Start the actor group."""
        if self.stack is not None:
            return
        self._instrumentation.group_starting(self)
        self.stack = AsyncExitStack()
        await self.stack.__aenter__()
        for actor in self._actors:
            if isinstance(actor, Service):
                request_handler = self._process_service_iterator(actor)
                request_iterator = await self.stack.enter_async_context(
                    self._bus.commands(actor.command)
                )
                task = asyncio.create_task(request_handler(request_iterator))
                self._instrumentation.service_started(actor)
            elif isinstance(actor, Actor):
                message_handler = self._process_actor_iterator(actor)
                message_iterator = await self.stack.enter_async_context(
                    self._bus.events(actor.event)
                )
                task = asyncio.create_task(message_handler(message_iterator))
                self._instrumentation.actor_started(actor)
            else:
                raise TypeError(f"Actor not supported: {actor}")
            task.add_done_callback(self._cancel_on_first_exception(actor))
            self.tasks.append(task)
        self._instrumentation.group_started(self)

    def cancel(self) -> None:
        for task in self.tasks:
            if not task.done():
                task.cancel()

    async def stop(self, timeout: t.Optional[float] = None) -> None:
        """Stop actor group."""
        if self.stack is None:
            return
        self._instrumentation.group_stopping(self)
        await self.stack.__aexit__(*sys.exc_info())
        await self.wait(timeout=timeout)
        errors = self.errors()
        if errors:
            self._instrumentation.group_failed(self, errors)
            raise ExceptionGroup(errors)
        self._instrumentation.group_stopped(self)

    async def wait(self, timeout: t.Optional[float] = None) -> None:
        """Wait until the actor group is stopped."""
        try:
            await asyncio.wait(
                self.tasks, timeout=timeout, return_when=asyncio.ALL_COMPLETED
            )
        # Raised when an exception is raised within a task and future is not set
        except ValueError:
            pass

    def errors(self) -> t.List[BaseException]:
        """Get all errors raised by actors within group which are not cancelled errors."""
        return list(self._collect_exceptions())

    def started(self) -> bool:
        """Return True if ActorGroup is started."""
        return self.stack is not None

    def done(self) -> bool:
        """Return True if ActorGroup is stopped."""
        if self.tasks:
            return all(task.done() for task in self.tasks)
        return False

    def extend(self, actors: t.List[Actor[t.Any]]) -> None:
        """Extend actors group with new actors."""
        if self.started():
            raise RuntimeError("Cannot extend actors group after it is started.")
        self._actors.extend(actors)

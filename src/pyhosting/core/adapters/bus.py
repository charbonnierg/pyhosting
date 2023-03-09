import typing as t
from asyncio import Queue as AIOQueue
from asyncio import QueueFull, Task, create_task, wait_for
from contextlib import asynccontextmanager

from genid.generators import NUIDGenerator

from ..entities import Command, Event, Filter, Queue
from ..interfaces import EventBus, Job, Message, Request

T = t.TypeVar("T")
ReplyT = t.TypeVar("ReplyT")


class InMemoryMessage(Message[T]):
    def __init__(self, event: Event[T], data: T) -> None:
        self._event = event
        self._data = data

    @property
    def subject(self) -> str:
        return self.event.name

    @property
    def event(self) -> Event[T]:
        return self._event

    @property
    def data(self) -> T:
        return self._data


class InMemoryRequest(Request[T, ReplyT]):
    def __init__(
        self,
        command: Command[T, ReplyT],
        data: T,
        _reply: str,
        _bus: "InMemoryEventBus",
    ) -> None:
        self._command = command
        self._data = data
        self._bus = _bus
        self._reply = _reply

    @property
    def subject(self) -> str:
        return self._command.name

    @property
    def command(self) -> Command[T, ReplyT]:
        return self._command

    @property
    def event(self) -> Event[T]:
        return Event(self._command.name, self._command.schema)

    @property
    def reply_event(self) -> Event[ReplyT]:
        return Event(self._reply, self._command.reply_schema)

    @property
    def data(self) -> T:
        return self._data

    async def reply(self, payload: ReplyT) -> None:
        await self._bus.publish(self.reply_event, payload)


class InMemoryEventBus(EventBus):
    """Implementation of an in-memory event-bus.

    This event bus can be used to:
        - emit events
        - request events (similar but different from NATS request/reply)
        - create events observers (similar to NATS subscriptions but less powerful)

    Limitations:
        - Each event has a static subjet.
        - Requesters CANNOT communicate a reply subject. It means that actors MUST know before hand the reply subject.
    """

    def __init__(self) -> None:
        self.observers: t.List[
            t.Tuple[
                t.Union[Event[t.Any], Filter[t.Any]],
                str,
                AIOQueue[Message[t.Any]],
            ],
        ] = []
        self.command_observers: t.List[
            t.Tuple[
                Command[t.Any, t.Any],
                str,
                AIOQueue[Request[t.Any, t.Any]],
            ],
        ] = []
        self.nuid = NUIDGenerator()

    async def __request_event(
        self, request: InMemoryRequest[T, ReplyT]
    ) -> Message[ReplyT]:
        """Wait for a single event."""
        async with self.events(request.reply_event) as observer:
            self.__notify_command_observers(request)
            async for event in observer:
                return event
        raise ValueError("No reply received")

    async def publish(self, event: Event[T], payload: T) -> None:
        msg = InMemoryMessage(event, payload)
        self.__notify_event_observers(msg)

    async def request(
        self,
        command: Command[T, ReplyT],
        payload: T,
        timeout: t.Optional[float] = None,
    ) -> ReplyT:
        """Request an event."""
        reply_subject = self.nuid.new()
        request = InMemoryRequest(command, payload, reply_subject, self)
        msg = await wait_for(self.__request_event(request), timeout=timeout)
        return msg.data

    def __notify_event_observers(self, msg: Message[T]) -> None:
        """Emit an event."""
        queues_processed: t.Set[str] = set()
        for target, queue, observer in self.observers:
            if queue and queue in queues_processed:
                continue
            if not match_subject(msg.subject, target.subject):
                continue
            try:
                observer.put_nowait(msg)
            except QueueFull:
                continue
            else:
                if queue:
                    queues_processed.add(queue)

    def __notify_command_observers(self, request: Request[T, ReplyT]) -> None:
        """Emit an event."""
        queues_processed: t.Set[str] = set()
        for target, queue, observer in self.command_observers:
            if queue and queue in queues_processed:
                continue
            if not match_subject(request.subject, target.subject):
                continue
            try:
                observer.put_nowait(request)
            except QueueFull:
                continue
            else:
                if queue:
                    queues_processed.add(queue)

    @asynccontextmanager
    async def events(
        self,
        event: t.Union[Event[T], Filter[T]],
        queue: t.Optional[str] = None,
    ) -> t.AsyncIterator[t.AsyncIterator[Message[T]]]:
        """Create a new observer, optionally within a queue."""
        queue = queue or ""
        observer: "AIOQueue[Message[T]]" = AIOQueue()
        key = (event, queue, observer)
        self.observers.append(key)
        current_task: t.Optional[Task[Message[T]]] = None

        async def iterator() -> t.AsyncIterator[Message[T]]:
            nonlocal current_task
            nonlocal observer
            while True:
                current_task = create_task(observer.get())
                yield await current_task

        try:
            yield iterator()
        finally:
            if current_task:
                current_task.cancel()
            self.observers.remove(key)

    @asynccontextmanager
    async def commands(
        self, command: Command[T, ReplyT], queue: t.Optional[str] = None
    ) -> t.AsyncIterator[t.AsyncIterator[Request[T, ReplyT]]]:
        queue = queue or ""
        observer: "AIOQueue[Request[T, ReplyT]]" = AIOQueue()
        key = (command, queue, observer)
        self.command_observers.append(key)
        current_task: t.Optional[Task[Request[T, ReplyT]]] = None

        async def iterator() -> t.AsyncIterator[Request[T, ReplyT]]:
            nonlocal current_task
            nonlocal observer
            while True:
                current_task = create_task(observer.get())
                yield await current_task

        try:
            yield iterator()
        finally:
            if current_task:
                current_task.cancel()
            self.command_observers.remove(key)

    def jobs(self, queue: Queue[T]) -> t.AsyncContextManager[t.AsyncIterator[Job[T]]]:
        raise NotImplementedError


def match_subject(
    subject: str,
    filter: str,
    sep: str = ".",
    match_all: str = ">",
    match_one: str = "*",
) -> bool:
    """An approximative attempt to check if a filter matches a subject."""
    if not subject:
        raise ValueError("Subject cannot be empty")
    if not filter:
        raise ValueError("Filter subject cannot be empty")
    # By default consider there is no match
    matches = False
    # If both subjects are equal
    if subject == filter:
        return True
    # Split subjects using sep character ("." by default)
    msg_tokens = subject.split(sep)
    total_tokens = len(msg_tokens)
    filter_tokens = filter.split(sep)
    # Iterate over each token
    for idx, token in enumerate(filter_tokens):
        # If tokens are equal, let's continue
        try:
            if token == msg_tokens[idx]:
                # Continue the iteration on next token
                continue
        except IndexError:
            # If tokens are different, then let's continue our if/else statements
            matches = False
        # If token is match_all (">" by default)
        if token == match_all:
            # Then we can return True
            return True
        # If token is mach_one ("*" by default)
        if token == match_one:
            matches = True
        # Else it means that subject do not match
        else:
            return False
    if token == match_one and (total_tokens - idx) > 1:
        return False
    return matches

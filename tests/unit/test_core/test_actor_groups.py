import asyncio
import typing as t
from re import escape

import pytest

from pyhosting.core.adapters import InMemoryEventBus
from pyhosting.core.aio import Actors
from pyhosting.core.entities import Actor, Event
from pyhosting.core.errors import ExceptionGroup
from pyhosting.core.interfaces import Message

T = t.TypeVar("T")


class MockActor(Actor[T]):
    """An actor which can be used during tests."""

    def __init__(
        self,
        event: Event[T],
        process: t.Optional[
            t.Callable[[Message[T]], t.Coroutine[None, None, None]]
        ] = None,
        exception: t.Optional[BaseException] = None,
    ) -> None:
        """Create a new mock actor.

        Arguments:
            event: The event the actor should listen
            process: The coroutine function used to process the event (optional)
            exception: An exception to raise while processing the event (optional)

        Note: All events received by a mock actor are available through `received_events` attribute.
        """
        self.event = event
        self.process = process
        self.exception = exception
        self.received_events: t.List[Message[T]] = []

    async def handler(self, event: Message[T]) -> None:
        """Mock actor handler"""
        self.received_events.append(event)
        if self.process:
            await self.process(event)
        if self.exception:
            raise self.exception
        await asyncio.sleep(0)


@pytest.mark.asyncio
class TestActorsGroup:
    async def test_actors_group_start_idempotent(self):
        async with Actors(InMemoryEventBus(), []) as group:
            assert group.started()
            await group.start()

    async def test_actors_cannot_be_extended_after_start(self):
        async with Actors(InMemoryEventBus(), []) as group:
            with pytest.raises(
                RuntimeError, match="Cannot extend actors group after it is started"
            ):
                await group.extend([])

    async def test_actors_group_stop_idempotent(self):
        group = Actors(InMemoryEventBus(), [])
        assert not group.started()
        assert not group.done()
        await group.stop()
        async with group:
            await group.stop()
            assert not group.done()
            await group.stop()

    async def test_actors_group_cancel(self):
        bus = InMemoryEventBus()
        event = Event("test-event", int)
        # Create a mock actor
        actor = MockActor(event)
        # Start an actor group
        async with Actors(
            bus=bus,
            actors=[actor],
        ) as group:
            # Actors group just started so no event is received yet
            assert len(actor.received_events) == 0
            assert group.started()
            assert not group.done()
            assert group.errors() == []
            # Publish 3 events
            for idx in range(3):
                await bus.publish(event, idx)
            # Cancel the group
            group.cancel()
        # Actors group is stopped because all events are processed
        assert len(actor.received_events) <= 1
        assert group.done()

    async def test_actors_group_start_stop_failure(self):
        bus = InMemoryEventBus()
        event = Event("test-event", int)
        # Create a mock actor
        actor = MockActor(event, exception=Exception("BOOM"))
        # Start an actor group
        with pytest.raises(
            ExceptionGroup,
            match=escape("1 error raised. Error: [Exception('BOOM')]"),
        ):
            async with Actors(
                bus=bus,
                actors=[actor],
            ) as group:
                # Actors group just started so no event is received yet
                assert len(actor.received_events) == 0
                assert group.started()
                # Publish 3 events
                for idx in range(3):
                    await bus.publish(event, idx)
        # Actors group is stopped because all events are processed
        assert len(actor.received_events) == 1
        assert group.done()
        assert group.errors()[0].args == ("BOOM",)

    async def test_actors_group_start_stop_several_actors_one_failure(self):
        bus = InMemoryEventBus()
        # Create a mock actor
        actor = MockActor(Event("test-event", int), exception=Exception("BOOM"))
        actor_2 = MockActor(Event("test-event-2", int))
        # Start an actor group
        with pytest.raises(
            ExceptionGroup,
            match=escape("1 error raised. Error: [Exception('BOOM')]"),
        ):
            async with Actors(
                bus=bus,
                actors=[actor, actor_2],
            ) as group:
                # Actors group just started so no event is received yet
                assert len(actor.received_events) == 0
                assert group.started()
                # Publish several events
                for i in range(10):
                    await bus.publish(Event("test-event", int), i)
                    await bus.publish(Event("test-event-2", int), i)

        # Actors group is stopped on first event because an error was raised
        assert len(actor.received_events) == 1
        assert len(actor_2.received_events) == 1
        assert group.done()
        assert group.errors()[0].args == ("BOOM",)

    async def test_actors_group_start_stop_several_actors_success(self):
        bus = InMemoryEventBus()
        # Create a mock actor
        actor = MockActor(Event("test-event", int))
        actor_2 = MockActor(Event("test-event-2", int))
        # Start an actor group
        async with Actors(
            bus=bus,
            actors=[actor, actor_2],
        ) as group:
            # Actors group just started so no event is received yet
            assert len(actor.received_events) == 0
            assert len(actor_2.received_events) == 0
            assert group.started()
            assert not group.done()
            # Publish some events
            await bus.publish(Event("test-event", int), 1)
            for idx in range(5):
                await bus.publish(Event("test-event-2", int), idx)
            # Sleep a bit
            await asyncio.sleep(0.1)
        # Actors group is stopped because all events are processed
        assert len(actor.received_events) == 1
        assert len(actor_2.received_events) == 5
        assert group.done()

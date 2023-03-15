import asyncio
import typing as t

import pytest

from synopsys import Event, Message, create_event
from synopsys.adapters.memory import InMemoryEventBus
from synopsys.concurrency import Play
from synopsys.core.actors import Subscriber

T = t.TypeVar("T")


class MockSubscriber:
    """An actor which can be used during tests."""

    def __init__(
        self,
        event: Event[t.Any, t.Any, t.Any],
        process: t.Optional[
            t.Callable[[Message[t.Any, t.Any, t.Any]], t.Coroutine[None, None, None]]
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
        self.received_events: t.List[Message[t.Any, t.Any, t.Any]] = []

    async def __call__(self, event: Message[t.Any, t.Any, t.Any]) -> None:
        """Mock actor handler"""
        self.received_events.append(event)
        if self.process:
            await self.process(event)
        if self.exception:
            raise self.exception
        await asyncio.sleep(0)

    def get_actor(self) -> Subscriber[t.Any, t.Any, t.Any]:
        return Subscriber(self.event, self)


@pytest.mark.asyncio
class TestActorsGroup:
    async def test_actors_play_start_idempotent(self):
        async with Play(InMemoryEventBus(), []) as play:
            assert play.started()
            await play.start()

    async def test_actors_cannot_be_extended_after_start(self):
        async with Play(InMemoryEventBus(), []) as play:
            with pytest.raises(
                RuntimeError, match="Cannot extend play after it is started"
            ):
                play.extend()

    async def test_actors_play_stop_idempotent(self):
        play = Play(InMemoryEventBus(), [])
        assert not play.started()
        assert not play.done()
        await play.stop()
        async with play:
            await play.stop()
            assert not play.done()
            await play.stop()

    async def test_actors_play_cancel(self):
        bus = InMemoryEventBus()
        event = create_event("test-event", "test", int)
        # Create a mock actor
        actor = MockSubscriber(event)
        # Start an actor play
        async with Play(
            bus=bus,
            actors=[actor.get_actor()],
        ) as play:
            # Actors play just started so no event is received yet
            assert len(actor.received_events) == 0
            assert play.started()
            assert not play.done()
            assert play.errors() == []
            # Publish 3 events
            for idx in range(3):
                await bus.publish(event, scope=None, payload=idx, metadata=None)
            # Cancel the play
            play.cancel()
        # Actors play is stopped because all events are processed
        assert len(actor.received_events) <= 1
        assert play.done()

    async def test_actors_play_start_stop_several_actors_success(self):
        bus = InMemoryEventBus()
        # Create a mock actor
        evt1 = create_event("test-event-1", "test.1", int)
        evt2 = create_event("test-event-2", "test.2", int)
        mock = MockSubscriber(evt1)
        other_mock = MockSubscriber(evt2)
        # Start an actor play
        async with Play(
            bus=bus,
            actors=[mock.get_actor(), other_mock.get_actor()],
        ) as play:
            # Actors play just started so no event is received yet
            assert len(mock.received_events) == 0
            assert len(other_mock.received_events) == 0
            assert play.started()
            assert not play.done()
            # Publish some events
            await bus.publish(evt1, scope=None, payload=1, metadata=None)
            for idx in range(5):
                await bus.publish(evt2, scope=None, payload=idx, metadata=None)
            # Sleep a bit
            await asyncio.sleep(0.1)
        # Actors play is stopped because all events are processed
        assert len(mock.received_events) == 1
        assert len(other_mock.received_events) == 5
        assert play.done()

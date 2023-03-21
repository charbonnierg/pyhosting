import asyncio
import typing as t

import pytest

from synopsys import create_event
from synopsys.adapters.memory import InMemoryEventBus, InMemoryMessage, InMemoryRequest
from synopsys.concurrency import Play
from synopsys.core.actors import Actor, Responder, Subscriber
from synopsys.core.interfaces import BaseMessage
from synopsys.instrumentation.play import PlayInstrumentation


class MockInstrumentation(PlayInstrumentation):
    def __init__(self):
        self.called_with: t.Optional[t.Any] = None

    def assert_called_with(self, obj: t.Any) -> None:
        assert self.called_with == obj

    def __enter__(self) -> "MockInstrumentation":
        return self

    def __exit__(self, *args: t.Any, **kwargs: t.Any) -> None:
        return None


class SpyPlayStarting(MockInstrumentation):
    def play_starting(self, play: Play):
        self.called_with = play


class SpyPlayStarted(MockInstrumentation):
    def play_started(self, play: Play):
        self.called_with = play


class SpyPlayStopped(MockInstrumentation):
    def play_stopped(self, play: Play):
        self.called_with = play


class SpyPlayStopping(MockInstrumentation):
    def play_stopping(self, play: Play):
        self.called_with = play


class SpyActorStarting(MockInstrumentation):
    def actor_starting(self, play: Play, actor: Actor):
        self.called_with = (play, actor)


class SpyActorStarted(MockInstrumentation):
    def actor_started(self, play: Play, actor: Actor):
        self.called_with = (play, actor)


class SpyActorCancelled(MockInstrumentation):
    def actor_cancelled(self, play: Play, actor: Actor):
        self.called_with = (play, actor)


class SpyEventProcessed(MockInstrumentation):
    def event_processed(
        self, play: Play, actor: Actor, msg: BaseMessage[t.Any, t.Any, t.Any, t.Any]
    ):
        self.called_with = (play, actor, msg)


@pytest.mark.asyncio
async def test_play_instrumentation_starting():
    with SpyPlayStarting() as instrumentation:
        async with Play(
            InMemoryEventBus(), actors=[], instrumentation=instrumentation
        ) as play:
            instrumentation.assert_called_with(play)


@pytest.mark.asyncio
async def test_play_instrumentation_started():
    with SpyPlayStarted() as instrumentation:
        async with Play(
            InMemoryEventBus(), actors=[], instrumentation=instrumentation
        ) as play:
            instrumentation.assert_called_with(play)


@pytest.mark.asyncio
async def test_play_instrumentation_stopping():
    with SpyPlayStopping() as instrumentation:
        async with Play(
            InMemoryEventBus(), actors=[], instrumentation=instrumentation
        ) as play:
            assert instrumentation.called_with is None
        # Once play is stoped instrumentation must have been called
        instrumentation.assert_called_with(play)


@pytest.mark.asyncio
async def test_play_instrumentation_stopped():
    with SpyPlayStopped() as instrumentation:
        async with Play(
            InMemoryEventBus(), actors=[], instrumentation=instrumentation
        ) as play:
            assert instrumentation.called_with is None
        # Once play is stoped instrumentation must have been called
        instrumentation.assert_called_with(play)


@pytest.mark.asyncio
async def test_actor_starting():
    async def handler(_: t.Any) -> None:
        """An handler used to create a subscriber."""
        pass

    actor = Subscriber(create_event("test", "test", int), handler=handler)
    with SpyActorStarting() as instrumentation:
        async with Play(
            InMemoryEventBus(),
            actors=[actor],
            instrumentation=instrumentation,
        ) as play:
            instrumentation.assert_called_with((play, actor))


@pytest.mark.asyncio
async def test_actor_started():
    async def handler(_: t.Any) -> None:
        """An handler used to create a subscriber."""
        pass

    actor = Subscriber(create_event("test", "test", int), handler=handler)
    with SpyActorStarting() as instrumentation:
        async with Play(
            InMemoryEventBus(),
            actors=[actor],
            instrumentation=instrumentation,
        ) as play:
            instrumentation.assert_called_with((play, actor))


@pytest.mark.asyncio
async def test_actor_cancelled():
    async def handler(_: t.Any) -> None:
        """An handler used to create a subscriber."""

    actor = Subscriber(create_event("test", "test", int), handler=handler)
    with SpyActorCancelled() as instrumentation:
        async with Play(
            InMemoryEventBus(),
            actors=[actor],
            instrumentation=instrumentation,
        ) as play:
            assert instrumentation.called_with is None
        # Check that actor was cancelled
        assert instrumentation.called_with == (play, actor)


@pytest.mark.asyncio
async def test_event_processed():
    async def handler(_: t.Any) -> None:
        """An handler used to create a subscriber."""

    evt = create_event("test", "test", int, metadata_schema=t.Dict[str, str])
    actor = Subscriber(evt, handler=handler)
    with SpyEventProcessed() as instrumentation:
        async with Play(
            bus=InMemoryEventBus(),
            actors=[actor],
            instrumentation=instrumentation,
        ) as play:
            assert instrumentation.called_with is None
            await play.bus.publish(evt, None, 12, {"test": "hello"}, timeout=0.1)
            # Give some time for runner to process event
            await asyncio.sleep(0.01)
        # Check that actor was cancelled
        assert instrumentation.called_with == (
            play,
            actor,
            InMemoryMessage(evt, subject="test", payload=12, headers={"test": "hello"}),
        )


@pytest.mark.asyncio
async def test_request_processed():
    async def handler(msg: BaseMessage[None, int, t.Dict[str, str], int]) -> int:
        """An handler used to create a subscriber."""
        return msg.data + 10

    evt = create_event(
        "test", "test", int, metadata_schema=t.Dict[str, str], reply_schema=int
    )
    actor = Responder(evt, handler=handler)
    with SpyEventProcessed() as instrumentation:
        bus = InMemoryEventBus()
        async with Play(
            bus=bus,
            actors=[actor],
            instrumentation=instrumentation,
        ) as play:
            assert instrumentation.called_with is None
            reply = await play.bus.request(
                evt, None, 12, {"test": "hello"}, timeout=0.1
            )
            assert reply == 22
        # Check that actor was cancelled
        assert instrumentation.called_with == (
            play,
            actor,
            InMemoryRequest(
                evt,
                subject="test",
                payload=12,
                headers={"test": "hello"},
                _publisher=bus,
                _reply="reply",
            ),
        )

import typing as t

import pytest
import pytest_asyncio
from _pytest.fixtures import SubRequest
from nats import NATS

from synopsys import EventBus, Request, Responder, create_event
from synopsys.adapters.codecs import PydanticCodec
from synopsys.adapters.memory import InMemoryEventBus
from synopsys.adapters.nats import NATSEventBus
from synopsys.concurrency import Play, Waiter

ADAPTERS: t.Dict[str, t.Type[EventBus]] = {
    "memory": InMemoryEventBus,
    "nats": NATSEventBus,
}


@pytest_asyncio.fixture
async def bus(request: SubRequest) -> t.AsyncIterator[EventBus]:
    """A fixture which returns an event bus."""
    param = getattr(request, "param", None)
    if param is None:
        kind = "memory"
        options = {}
    elif isinstance(param, tuple):
        kind, options = param
    else:
        kind = param
        options = {}
    bus = ADAPTERS[kind](**options)
    try:
        await bus.connect()
        yield bus
    finally:
        await bus.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bus",
    [
        "memory",
        ("nats", {"nc": NATS(), "codec": PydanticCodec()}),
    ],
    indirect=True,
    ids=["memory", "nats"],
)
class TestEventBusInterface:
    """Test the event bus interface."""

    async def test_event_bus_publish(self, bus: EventBus):
        event = create_event(
            "test-event", "test", int, metadata_schema=t.Dict[str, str]
        )
        waiter = await Waiter.create(bus.subscribe(event))
        await bus.publish(event, None, 12, {"test": "somemeta"}, timeout=0.1)
        received_event = await waiter.wait()
        assert received_event.data == 12

    async def test_event_bus_observe_event(self, bus: EventBus):
        target_event = create_event(
            "test-1", "test.1", int, metadata_schema=t.Dict[str, str]
        )
        ignored_event = create_event(
            "test-2", "test.2", int, metadata_schema=t.Dict[str, str]
        )
        # Create a waiter
        waiter = await Waiter.create(bus.subscribe(target_event))
        # This event should be ignore
        await bus.publish(ignored_event, None, 0, {"test": "somemeta"}, timeout=0.1)
        # This event should be received
        await bus.publish(target_event, None, 12, {"test": "somemeta"}, timeout=0.1)
        received_event = await waiter.wait(timeout=0.1)
        assert received_event.data == 12

    async def test_event_bus_observe_event_variant(self, bus: EventBus):
        target_event = create_event(
            "test-1", "test.*", int, metadata_schema=t.Dict[str, str]
        )
        ignored_event = create_event(
            "other", "other.*", int, metadata_schema=t.Dict[str, str]
        )
        # Create a waiter
        waiter = await Waiter.create(bus.subscribe(target_event))
        # This event should be ignore
        await bus.publish(ignored_event, None, 0, {"test": "somemeta"}, timeout=0.1)
        # This event should be received
        await bus.publish(target_event, None, 12, {"test": "somemeta"}, timeout=0.1)
        received_event = await waiter.wait()
        assert received_event.data == 12

    async def test_event_bus_request(self, bus: EventBus):
        """Test case for request/reply.

        Given: An actor is created using an event and an event handler
        When: A play is created and started using the actor
        Then: Requesters can send messages and receive replies
        """
        event = create_event(
            "test-command",
            "test",
            int,
            reply_schema=int,
            metadata_schema=t.Dict[str, str],
        )

        # Define an handler
        # Note that handler today requires 4 generic types...
        #  - The first one is the event scope (the data whind within message payload)
        #  - The third one is the event metadata (the data which can be found within message header)
        #  - The fourth one is the event reply (the data which is sent back as the reply ch can be found within subject)
        #  - The second one is the event payload (the data which can be foumessage payload)
        # I don't know how we can provide simpler API without sacrificing the ability to type messages.
        async def handler(request: Request[None, int, t.Dict[str, str], int]) -> int:
            """A test handler"""
            return request.data + 10

        actor = Responder(event, handler)
        # Use actors in order to start a service
        # Start play
        play = Play(bus, actors=[actor])
        await play.start()
        # Once play is started
        # Requests can be sent and replied to
        try:
            reply = await bus.request(
                event,
                payload=12,
                scope=None,
                metadata={"test": "hello"},
                timeout=0.1,
            )
        finally:
            await play.stop()
        # Assert once play is stopped
        assert reply == 22

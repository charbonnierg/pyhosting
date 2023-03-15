import typing as t
import asyncio
import pytest_asyncio
import pytest
from nats import NATS
from synopsys.adapters.nats import NATSEventBus
from synopsys.adapters.codecs import PydanticCodec
from synopsys import create_event


@pytest_asyncio.fixture
async def bus() -> t.AsyncIterator[NATSEventBus]:
    nc = NATS()
    await nc.connect()
    try:
        bus = NATSEventBus(nc, PydanticCodec())
        yield bus
    finally:
        if nc.is_draining or nc.is_reconnecting:
            await nc.close()
        if not nc.is_closed:
            await nc.drain()


@pytest.mark.asyncio
async def test_minimal(bus: NATSEventBus) -> None:
    """Do nothing and expect test to pass"""


@pytest.mark.asyncio
async def test_with_subscription_removed(bus: NATSEventBus) -> None:
    """Do nothing and expect test to pass"""
    event = create_event("test", "test", int, metadata_schema=t.Dict[str, str])
    async with bus.subscribe(event) as observer:
        await asyncio.sleep(0.1)
        await bus.publish(
            event,
            None,
            1,
            {"test": "hello"},
        )
        async for _ in observer:
            pass


@pytest.mark.asyncio
async def test_with_subscription_pending(nc: NATS) -> None:
    """Do nothing and expect test to pass"""
    event = create_event("test", "test", int)

    async def task():
        async with bus.subscribe(event) as observer:
            async for msg in observer:
                pass


@pytest.mark.asyncio
async def test_with_subscription_iterator_pending(nc: NATS) -> None:
    """Do nothing and expect test to pass"""
    sub = await nc.subscribe("test")

    async def iterator(sub):
        async for msg in sub:
            yield msg

    async def task(iterator):
        async for _ in iterator:
            pass

    asyncio.create_task(task(iterator(sub.messages)))
    await asyncio.sleep(0.1)

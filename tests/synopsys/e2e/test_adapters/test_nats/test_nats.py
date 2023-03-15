import typing as t
import asyncio
import pytest_asyncio
import pytest
from nats import NATS


@pytest_asyncio.fixture
async def nc() -> t.AsyncIterator[NATS]:
    nc = NATS()
    await nc.connect()
    try:
        yield nc
    finally:
        if nc.is_draining or nc.is_reconnecting:
            await nc.close()
        if not nc.is_closed:
            await nc.drain()


@pytest.mark.asyncio
async def test_minimal(nc: NATS) -> None:
    """Do nothing and expect test to pass"""


@pytest.mark.asyncio
async def test_with_subscription_removed(nc: NATS) -> None:
    """Do nothing and expect test to pass"""
    sub = await nc.subscribe("test")
    await sub.unsubscribe()


@pytest.mark.asyncio
async def test_with_subscription_pending(nc: NATS) -> None:
    """Do nothing and expect test to pass"""
    await nc.subscribe("test")


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

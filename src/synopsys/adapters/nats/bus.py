import typing as t
from contextlib import asynccontextmanager

from nats import NATS

from synopsys import (
    DataT,
    EventBus,
    EventQueue,
    EventSpec,
    Job,
    Message,
    MetadataT,
    ReplyT,
    Request,
    ScopeT,
)

from .messages import Codec, NATSMessage, NATSRequest

__all__ = ["NATSEventBus"]


class NATSEventBus(EventBus):
    """NATS Event bus implementation."""

    def __init__(self, nc: NATS, codec: Codec) -> None:
        self.nc = nc
        self.codec = codec

    async def publish(
        self,
        event: EventSpec[ScopeT, DataT, MetadataT, None],
        scope: ScopeT,
        payload: DataT,
        metadata: MetadataT,
        timeout: t.Optional[float] = None,
    ) -> None:
        await self.nc.publish(
            subject=event.get_subject(scope),
            payload=self.codec.encode(payload),
            headers=self.codec.parse_obj(metadata, t.Dict[str, str]),
        )

    async def request(
        self,
        event: EventSpec[ScopeT, DataT, MetadataT, ReplyT],
        scope: ScopeT,
        payload: DataT,
        metadata: MetadataT,
        timeout: t.Optional[float] = None,
    ) -> ReplyT:
        """Request an event."""
        reply = await self.nc.request(
            subject=event.get_subject(scope),
            payload=self.codec.encode(payload),
            headers=self.codec.parse_obj(metadata, t.Dict[str, str]),
            timeout=timeout or float("inf"),
        )
        return self.codec.decode(reply.data, event.reply_schema)

    @asynccontextmanager
    async def subscribe(
        self,
        event: EventSpec[ScopeT, DataT, MetadataT, None],
        queue: t.Optional[str] = None,
    ) -> t.AsyncIterator[t.AsyncIterator[Message[ScopeT, DataT, MetadataT]]]:
        """Create a new observer, optionally within a queue."""
        sub = await self.nc.subscribe(event._subject, queue=queue or "")

        async def iterator() -> t.AsyncIterator[Message[ScopeT, DataT, MetadataT]]:
            async for msg in sub.messages:
                yield NATSMessage(event, msg, codec=self.codec)

        try:
            yield iterator()
        finally:
            await sub.drain()

    @asynccontextmanager
    async def serve(
        self,
        event: EventSpec[ScopeT, DataT, MetadataT, ReplyT],
        queue: t.Optional[str] = None,
    ) -> t.AsyncIterator[t.AsyncIterator[Request[ScopeT, DataT, MetadataT, ReplyT]]]:
        sub = await self.nc.subscribe(event._subject, queue=queue or "")

        async def iterator() -> t.AsyncIterator[
            Request[ScopeT, DataT, MetadataT, ReplyT]
        ]:
            async for msg in sub.messages:
                yield NATSRequest(event, msg, codec=self.codec)

        try:
            yield iterator()
        finally:
            await sub.drain()

    def pull(
        self, queue: EventQueue[ScopeT, DataT, MetadataT]
    ) -> t.AsyncContextManager[t.AsyncIterator[Job[ScopeT, DataT, MetadataT]]]:
        raise NotImplementedError

import typing as t

from nats.aio.msg import Msg

from synopsys import DataT, EventSpec, Message, MetadataT, ReplyT, Request, ScopeT
from synopsys.core.interfaces import BaseMessage, Codec

__all__ = ["NATSMessage", "NATSRequest"]


T = t.TypeVar("T")


class BaseNATSMessage(BaseMessage[ScopeT, DataT, MetadataT, ReplyT]):
    def __init__(
        self,
        event: EventSpec[ScopeT, DataT, MetadataT, ReplyT],
        msg: Msg,
        codec: Codec,
    ) -> None:
        self._codec = codec
        self._event = event
        self._msg = msg
        self._scope = self._event.extract_scope(msg.subject)
        self._data = self._codec.decode(self._msg.data, self._event.schema)
        self._metadata = self._codec.parse_obj(
            self._msg.headers, self._event.metadata_schema
        )

    @property
    def subject(self) -> str:
        """Return message subject."""
        return self._msg.subject

    @property
    def data(self) -> DataT:
        """Return event data found in message."""
        return self._data

    @property
    def scope(self) -> ScopeT:
        """Return message scope."""
        return self._scope

    @property
    def metadata(self) -> MetadataT:
        return self._metadata

    @property
    def spec(self) -> EventSpec[ScopeT, DataT, MetadataT, ReplyT]:
        return self._event


class NATSMessage(
    BaseNATSMessage[ScopeT, DataT, MetadataT, None],
    Message[ScopeT, DataT, MetadataT],
):
    pass


class NATSRequest(
    BaseNATSMessage[ScopeT, DataT, MetadataT, ReplyT],
    Request[ScopeT, DataT, MetadataT, ReplyT],
):
    async def reply(self, payload: ReplyT) -> None:
        if not self._msg.reply:
            return
        nc = self._msg._client
        await nc.publish(self._msg.reply, self._codec.encode(payload))

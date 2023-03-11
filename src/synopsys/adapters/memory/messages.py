import typing as t

from synopsys import (
    EMPTY,
    DataT,
    EventSpec,
    Message,
    MetadataT,
    ReplyT,
    Request,
    ScopeT,
)
from synopsys.core.interfaces import AllowPublish, BaseMessage

__all__ = ["InMemoryMessage", "InMemoryRequest"]


class BaseInMemoryMessage(BaseMessage[ScopeT, DataT, MetadataT, ReplyT]):
    def __init__(
        self,
        event: EventSpec[ScopeT, DataT, MetadataT, ReplyT],
        subject: str,
        payload: DataT,
        headers: MetadataT,
    ) -> None:
        self._event = event
        self._payload = payload
        self._headers = headers
        self._subject = subject
        if self._event.scope is type(None):  # noqa: E721
            # I don't know why mypy is not happy so I'm using cast...
            self._scope = t.cast(ScopeT, None)
        else:
            self._scope = self._event.extract_scope(self._subject)

    @property
    def subject(self) -> str:
        """Return message subject."""
        return self._subject

    @property
    def scope(self) -> ScopeT:
        """Return message scope."""
        return self._scope

    @property
    def data(self) -> DataT:
        return self._payload

    @property
    def metadata(self) -> MetadataT:
        return self._headers

    @property
    def spec(self) -> EventSpec[ScopeT, DataT, MetadataT, ReplyT]:
        return self._event


class InMemoryMessage(
    BaseInMemoryMessage[ScopeT, DataT, MetadataT, None],
    Message[ScopeT, DataT, MetadataT],
):
    pass


class InMemoryRequest(
    BaseInMemoryMessage[ScopeT, DataT, MetadataT, ReplyT],
    Request[ScopeT, DataT, MetadataT, ReplyT],
):
    def __init__(
        self,
        event: EventSpec[ScopeT, DataT, MetadataT, ReplyT],
        subject: str,
        payload: DataT,
        headers: MetadataT,
        _publisher: AllowPublish,
        _reply: str,
    ) -> None:
        super().__init__(event, subject, payload, headers)
        self._reply = _reply
        self._publisher = _publisher
        self._reply_event = EventSpec(
            name="reply",
            address=self._reply,
            scope=EMPTY,
            schema=self.spec.reply_schema,
            reply_schema=EMPTY,
            metadata_schema=self.spec.metadata_schema,
            syntax=self.spec.syntax,
        )

    async def reply(self, payload: ReplyT) -> None:
        await self._publisher.publish(
            self._reply_event, scope=None, payload=payload, metadata=self._headers
        )

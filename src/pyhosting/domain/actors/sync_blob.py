"""Pages versions are persisted into a blob storage upon creation.

This module defines the actors responsible for interacting with the blob storage.
"""
from pyhosting.core.entities import Actor
from pyhosting.core.interfaces import EventBus, Message

from ..events.page_versions import (
    PAGE_VERSION_CREATED,
    PAGE_VERSION_DELETED,
    PAGE_VERSION_UPLOADED,
    PageVersionCreated,
    PageVersionDeleted,
    PageVersionUploaded,
)
from ..events.pages import PAGE_DELETED, PageDeleted
from ..gateways import BlobStorageGateway


class UploadToBlobStorageOnVersionCreated(Actor[PageVersionCreated]):
    """Upload a new version to blob storage on `page-version-created` event."""

    event = PAGE_VERSION_CREATED

    def __init__(self, event_bus: EventBus, storage: BlobStorageGateway) -> None:
        self.storage = storage
        self.event_bus = event_bus

    async def handler(self, msg: Message[PageVersionCreated]) -> None:
        """Process a `page-version-created` event."""
        await self.storage.put_version(
            page_id=msg.data.document.page_id,
            page_version=msg.data.document.version,
            content=msg.data.content,
        )
        await self.event_bus.publish(
            PAGE_VERSION_UPLOADED,
            PageVersionUploaded(
                page_id=msg.data.document.page_id,
                page_name=msg.data.document.page_name,
                version=msg.data.document.version,
            ),
        )


class CleanBlobStorageOnVersionDelete(Actor[PageVersionDeleted]):
    """Delete a version from blob storage on `page-version-deleted` event."""

    event = PAGE_VERSION_DELETED

    def __init__(self, storage: BlobStorageGateway) -> None:
        self.storage = storage

    async def handler(self, msg: Message[PageVersionDeleted]) -> None:
        """Process a `page-version-deleted` event."""
        await self.storage.delete_version(
            page_id=msg.data.page_id, page_version=msg.data.version
        )


class CleanBlobStorageOnPageDelete(Actor[PageDeleted]):
    """Delete all versions from blob storage on `page-deleted` event."""

    event = PAGE_DELETED

    def __init__(self, storage: BlobStorageGateway) -> None:
        self.storage = storage

    async def handler(self, msg: Message[PageDeleted]) -> None:
        """Process a `page-deleted` event."""
        versions = await self.storage.list_versions(page_id=msg.data.id)
        for ref in versions:
            page_id, version = ref.split("/")
            await self.storage.delete_version(page_id=page_id, page_version=version)

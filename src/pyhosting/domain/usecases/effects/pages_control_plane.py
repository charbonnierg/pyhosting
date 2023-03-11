"""Pages versions are persisted into a blob storage upon creation.

This module defines the actors responsible for interacting with the blob storage.
"""
from synopsys import EventBus, Message

from ...events.page import PageDeleted
from ...events.version import (
    PAGE_VERSION_UPLOADED,
    PageVersionCreated,
    PageVersionDeleted,
    PageVersionUploaded,
)
from ...gateways import BlobStorageGateway


class UploadToBlobStorageOnVersionCreated:
    """Upload a new version to blob storage on `page-version-created` event."""

    def __init__(self, event_bus: EventBus, storage: BlobStorageGateway) -> None:
        self.storage = storage
        self.event_bus = event_bus

    async def __call__(self, msg: Message[None, PageVersionCreated, None]) -> None:
        """Process a `page-version-created` event."""
        await self.storage.put_version(
            page_id=msg.data.document.page_id,
            page_version=msg.data.document.version,
            content=msg.data.content,
        )
        await self.event_bus.publish(
            PAGE_VERSION_UPLOADED,
            scope=None,
            payload=PageVersionUploaded(
                page_id=msg.data.document.page_id,
                page_name=msg.data.document.page_name,
                version=msg.data.document.version,
            ),
            metadata=None,
        )


class CleanBlobStorageOnVersionDelete:
    """Delete a version from blob storage on `page-version-deleted` event."""

    def __init__(self, storage: BlobStorageGateway) -> None:
        self.storage = storage

    async def __call__(self, msg: Message[None, PageVersionDeleted, None]) -> None:
        """Process a `page-version-deleted` event."""
        await self.storage.delete_version(
            page_id=msg.data.page_id, page_version=msg.data.version
        )


class CleanBlobStorageOnPageDelete:
    """Delete all versions from blob storage on `page-deleted` event."""

    def __init__(self, storage: BlobStorageGateway) -> None:
        self.storage = storage

    async def __call__(self, msg: Message[None, PageDeleted, None]) -> None:
        """Process a `page-deleted` event."""
        versions = await self.storage.list_versions(page_id=msg.data.id)
        for ref in versions:
            page_id, version = ref.split("/")
            await self.storage.delete_version(page_id=page_id, page_version=version)

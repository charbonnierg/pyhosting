"""Pages versions are persisted into a blob storage upon creation.

This module defines the actors responsible for interacting with the blob storage.
"""
from ..events.page_versions import (
    PAGE_VERSION_CREATED,
    PAGE_VERSION_DELETED,
    PAGE_VERSION_UPLOADED,
    PageVersionCreated,
    PageVersionDeleted,
    PageVersionUploaded,
)
from ..events.pages import PAGE_DELETED, PageDeleted
from ..gateways import BlobStorageGateway, EventBusGateway


class UploadToBlobStorageOnVersionCreated:
    """Upload a new version to blob storage on `page-version-created` event."""

    event = PAGE_VERSION_CREATED

    def __init__(self, event_bus: EventBusGateway, storage: BlobStorageGateway) -> None:
        self.storage = storage
        self.event_bus = event_bus

    async def process_event(self, event: PageVersionCreated) -> None:
        """Process a `page-version-created` event."""
        await self.storage.put_version(
            page_id=event.document.page_id,
            page_version=event.document.version,
            content=event.content,
        )
        await self.event_bus.emit_event(
            PAGE_VERSION_UPLOADED,
            PageVersionUploaded(
                page_id=event.document.page_id,
                page_name=event.document.page_name,
                version=event.document.version,
            ),
        )


class CleanBlobStorageOnVersionDelete:
    """Delete a version from blob storage on `page-version-deleted` event."""

    event = PAGE_VERSION_DELETED

    def __init__(self, storage: BlobStorageGateway) -> None:
        self.storage = storage

    async def process_event(self, event: PageVersionDeleted) -> None:
        """Process a `page-version-deleted` event."""
        await self.storage.delete_version(
            page_id=event.page_id, page_version=event.version
        )


class CleanBlobStorageOnPageDelete:
    """Delete all versions from blob storage on `page-deleted` event."""

    event = PAGE_DELETED

    def __init__(self, storage: BlobStorageGateway) -> None:
        self.storage = storage

    async def process_event(self, event: PageDeleted) -> None:
        """Process a `page-deleted` event."""
        versions = await self.storage.list_versions(page_id=event.id)
        for ref in versions:
            page_id, version = ref.split("/")
            await self.storage.delete_version(page_id=page_id, page_version=version)

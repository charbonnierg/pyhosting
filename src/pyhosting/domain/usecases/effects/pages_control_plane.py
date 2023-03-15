"""Pages versions are persisted into a blob storage upon creation.

This module defines the actors responsible for interacting with the blob storage.
"""
from dataclasses import dataclass

from synopsys.core.interfaces import AllowPublish, Message

from ...events import (
    VERSION_UPLOADED,
    PageDeleted,
    VersionCreated,
    VersionDeleted,
    VersionUploaded,
)
from ...gateways import BlobStorageGateway


@dataclass
class UploadContentOnVersionCreated:
    """Upload a new version to blob storage on `version-created` event."""

    event_bus: AllowPublish
    storage: BlobStorageGateway

    async def __call__(self, msg: Message[None, VersionCreated, None]) -> None:
        """Process a `version-created` event."""
        page_id = msg.data.document.page_id
        page_name = msg.data.document.page_name
        page_version = msg.data.document.page_version
        blob = bytes.fromhex(msg.data.content)
        await self.storage.put(page_id, page_version, blob=blob)
        await self.event_bus.publish(
            VERSION_UPLOADED,
            scope=None,
            payload=VersionUploaded(
                page_id=page_id,
                page_name=page_name,
                page_version=page_version,
                is_latest=msg.data.latest,
            ),
            metadata={},
        )


@dataclass
class CleanStorageOnVersionDeleted:
    """Delete a version from blob storage on `version-deleted` event."""

    storage: BlobStorageGateway

    async def __call__(self, msg: Message[None, VersionDeleted, None]) -> None:
        """Process a `version-deleted` event."""
        await self.storage.delete(msg.data.page_id, msg.data.page_version)


@dataclass
class CleanStorageOnPageDeleted:
    """Delete all versions from blob storage on `page-deleted` event."""

    storage: BlobStorageGateway

    async def __call__(self, msg: Message[None, PageDeleted, None]) -> None:
        """Process a `page-deleted` event."""
        blob_keys = await self.storage.list_keys(msg.data.page_id)
        for key in blob_keys:
            await self.storage.delete(key)

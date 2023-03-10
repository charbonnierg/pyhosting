from pyhosting.core import Actor, Message

from ..events.page_versions import (
    PAGE_VERSION_DELETED,
    PAGE_VERSION_UPLOADED,
    PageVersionDeleted,
    PageVersionUploaded,
)
from ..events.pages import PAGE_CREATED, PAGE_DELETED, PageCreated, PageDeleted
from ..gateways import BlobStorageGateway, LocalStorageGateway
from ..templates import render_default_template


class DownloadToLocalStorageOnVersionUploaded(Actor[PageVersionUploaded]):
    """Download page version from blob storage into local storage on `page-version-uploaded` event."""

    def __init__(
        self, local_storage: LocalStorageGateway, blob_storage: BlobStorageGateway
    ) -> None:
        self.local_storage = local_storage
        self.blob_storage = blob_storage
        super().__init__(PAGE_VERSION_UPLOADED, self.on_page_version_uploaded)

    async def on_page_version_uploaded(self, msg: Message[PageVersionUploaded]) -> None:
        """Process a `page-version-uploaded` event."""
        content = await self.blob_storage.get_version(
            page_id=msg.data.page_id, page_version=msg.data.version
        )
        # QUESTION: This should never happen, because version is defined on the page entity
        # Should we test this line ?
        if content is None:
            raise ValueError("No content")
        await self.local_storage.unpack_archive(
            page_name=msg.data.page_name,
            version=msg.data.version,
            content=content,
            latest=True,
        )


class CleanLocalStorageOnVersionDeleted(Actor[PageVersionDeleted]):
    """Remove page version from local storage on `page-version-deleted` event."""

    def __init__(self, local_storage: LocalStorageGateway) -> None:
        self.local_storage = local_storage
        super().__init__(PAGE_VERSION_DELETED, self.on_page_version_deleted)

    async def on_page_version_deleted(self, event: Message[PageVersionDeleted]) -> None:
        """Process a `page-version-deleted` event."""
        await self.local_storage.remove_directory(
            page_name=event.data.page_name, version=event.data.version
        )


class CleanLocalStorageOnPageDeleted(Actor[PageDeleted]):
    """Delete all pages version from local storage on `page-deleted` event."""

    def __init__(self, local_storage: LocalStorageGateway) -> None:
        self.local_storage = local_storage
        super().__init__(PAGE_DELETED, self.on_page_deleted)

    async def on_page_deleted(self, event: Message[PageDeleted]) -> None:
        """Process a `page-deleted` event."""
        await self.local_storage.remove_directory(page_name=event.data.name)


class GenerateDefaultIndexOnPageCreated(Actor[PageCreated]):
    """Generate default index.html for latest page on `page-created` event."""

    def __init__(self, local_storage: LocalStorageGateway, base_url: str) -> None:
        self.local_storage = local_storage
        self.base_url = base_url
        super().__init__(PAGE_CREATED, self.on_page_created)

    async def on_page_created(self, event: Message[PageCreated]) -> None:
        """Process a `page-created` event."""
        index = render_default_template(
            page=event.data.document, base_url=self.base_url
        )
        await self.local_storage.write_default_file(
            page_name=event.data.document.name,
            content=index.encode("utf-8"),
        )

from ..events.page_versions import (
    PAGE_VERSION_DELETED,
    PAGE_VERSION_UPLOADED,
    PageVersionDeleted,
    PageVersionUploaded,
)
from ..events.pages import PAGE_CREATED, PAGE_DELETED, PageCreated, PageDeleted
from ..gateways import BlobStorageGateway, LocalStorageGateway
from ..templates import render_default_template


class DownloadToLocalStorageOnVersionUploaded:
    """Download page version from blob storage into local storage on `page-version-uploaded` event."""

    event = PAGE_VERSION_UPLOADED

    def __init__(
        self, local_storage: LocalStorageGateway, blob_storage: BlobStorageGateway
    ) -> None:
        self.local_storage = local_storage
        self.blob_storage = blob_storage

    async def process_event(self, event: PageVersionUploaded) -> None:
        """Process a `page-version-uploaded` event."""
        content = await self.blob_storage.get_version(
            page_id=event.page_id, page_version=event.version
        )
        if content is None:
            raise ValueError("No content")
        await self.local_storage.unpack_archive(
            page_name=event.page_name,
            version=event.version,
            content=content,
            latest=True,
        )


class CleanLocalStorageOnVersionDeleted:
    """Remove page version from local storage on `page-version-deleted` event."""

    event = PAGE_VERSION_DELETED

    def __init__(self, local_storage: LocalStorageGateway) -> None:
        self.local_storage = local_storage

    async def process_event(self, event: PageVersionDeleted) -> None:
        """Process a `page-version-deleted` event."""
        await self.local_storage.remove_directory(
            page_name=event.page_name, version=event.version
        )


class CleanLocalStorageOnPageDeleted:
    """Delete all pages version from local storage on `page-deleted` event."""

    event = PAGE_DELETED

    def __init__(self, local_storage: LocalStorageGateway) -> None:
        self.local_storage = local_storage

    async def process_event(self, event: PageDeleted) -> None:
        """Process a `page-deleted` event."""
        await self.local_storage.remove_directory(page_name=event.name)


class GenerateDefaultIndexOnPageCreated:
    """Generate default index.html for latest page on `page-created` event."""

    event = PAGE_CREATED

    def __init__(self, local_storage: LocalStorageGateway, base_url: str) -> None:
        self.local_storage = local_storage
        self.base_url = base_url

    async def process_event(self, event: PageCreated) -> None:
        """Process a `page-created` event."""
        index = render_default_template(page=event.document, base_url=self.base_url)
        await self.local_storage.write_default_file(
            page_name=event.document.name,
            content=index.encode("utf-8"),
        )

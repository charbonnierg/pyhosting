from synopsys import Message

from ..events.page_versions import PageVersionDeleted, PageVersionUploaded
from ..events.pages import PageCreated, PageDeleted
from ..gateways import BlobStorageGateway, LocalStorageGateway
from ..templates import render_default_template


class DownloadToLocalStorageOnVersionUploaded:
    """Download page version from blob storage into local storage on `page-version-uploaded` event."""

    def __init__(
        self, local_storage: LocalStorageGateway, blob_storage: BlobStorageGateway
    ) -> None:
        self.local_storage = local_storage
        self.blob_storage = blob_storage

    async def __call__(self, msg: Message[None, PageVersionUploaded, None]) -> None:
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


class CleanLocalStorageOnVersionDeleted:
    """Remove page version from local storage on `page-version-deleted` event."""

    def __init__(self, local_storage: LocalStorageGateway) -> None:
        self.local_storage = local_storage

    async def __call__(self, event: Message[None, PageVersionDeleted, None]) -> None:
        """Process a `page-version-deleted` event."""
        await self.local_storage.remove_directory(
            page_name=event.data.page_name, version=event.data.version
        )


class CleanLocalStorageOnPageDeleted:
    """Delete all pages version from local storage on `page-deleted` event."""

    def __init__(self, local_storage: LocalStorageGateway) -> None:
        self.local_storage = local_storage

    async def __call__(self, event: Message[None, PageDeleted, None]) -> None:
        """Process a `page-deleted` event."""
        await self.local_storage.remove_directory(page_name=event.data.name)


class GenerateDefaultIndexOnPageCreated:
    """Generate default index.html for latest page on `page-created` event."""

    def __init__(self, local_storage: LocalStorageGateway, base_url: str) -> None:
        self.local_storage = local_storage
        self.base_url = base_url

    async def __call__(self, event: Message[None, PageCreated, None]) -> None:
        """Process a `page-created` event."""
        index = render_default_template(
            page=event.data.document, base_url=self.base_url
        )
        await self.local_storage.write_default_file(
            page_name=event.data.document.name,
            content=index.encode("utf-8"),
        )

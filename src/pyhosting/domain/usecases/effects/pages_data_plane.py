from dataclasses import dataclass

from synopsys import Message

from ...events import PageCreated, PageDeleted, VersionDeleted, VersionUploaded
from ...gateways import BlobStorageGateway, FilestorageGateway, TemplateLoader
from ...operations.archives import unpack_archive
from ...templates import DEFAULT_TEMPLATE


@dataclass
class UpdateCacheOnVersionUploaded:
    """Download page version from blob storage into local storage on `version-uploaded` event."""

    local_storage: FilestorageGateway
    blob_storage: BlobStorageGateway

    async def __call__(self, msg: Message[None, VersionUploaded, None]) -> None:
        """Process a `version-uploaded` event."""
        version = msg.data
        # Download from blob storage
        content = await self.blob_storage.get(version.page_id, version.page_version)
        # Write content into local storage
        version_directory = self.local_storage.get_path(
            version.page_name, version.page_version
        )
        unpack_archive(
            content, version_directory, omit_top_level=True, create_parents=True
        )
        # Update latest symlink
        if version.is_latest:
            # Rewrite latest symlink
            version_directory.parent.joinpath("__latest__").unlink(missing_ok=True)
            version_directory.parent.joinpath("__latest__").symlink_to(
                version_directory, target_is_directory=True
            )


@dataclass
class CleanCacheOnVersionDeleted:
    """Remove page version from local storage on `version-deleted` event."""

    local_storage: FilestorageGateway

    async def __call__(self, event: Message[None, VersionDeleted, None]) -> None:
        """Process a `version-deleted` event."""
        await self.local_storage.remove_directory(
            event.data.page_name, event.data.page_version
        )


@dataclass
class CleanCacheOnPageDeleted:
    """Delete all pages version from local storage on `page-deleted` event."""

    local_storage: FilestorageGateway

    async def __call__(self, event: Message[None, PageDeleted, None]) -> None:
        """Process a `page-deleted` event."""
        await self.local_storage.remove_directory(event.data.page_name)


@dataclass
class InitCacheOnPageCreated:
    """Generate default index.html for latest page on `page-created` event."""

    local_storage: FilestorageGateway
    base_url: str
    templates: TemplateLoader

    def __post_init__(self) -> None:
        self.default_template = self.templates.load_template(
            DEFAULT_TEMPLATE.read_text()
        )

    async def __call__(self, event: Message[None, PageCreated, None]) -> None:
        """Process a `page-created` event."""
        index = self.default_template.render(
            page=event.data.document, base_url=self.base_url
        )
        await self.local_storage.write_bytes(
            event.data.document.name,
            "__default__",
            "index.html",
            content=index.encode("utf-8"),
            create_parents=True,
        )

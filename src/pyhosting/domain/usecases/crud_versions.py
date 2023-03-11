import typing as t
from dataclasses import dataclass
from hashlib import md5

from synopsys import EventBus

from ..entities import PageVersion
from ..errors import (
    CannotDeleteLatestVersionError,
    EmptyContentError,
    VersionAlreadyExistsError,
    VersionNotFoundError,
)
from ..events.page_versions import (
    PAGE_VERSION_CREATED,
    PAGE_VERSION_DELETED,
    PageVersionCreated,
    PageVersionDeleted,
)
from ..repositories import PageVersionRepository
from .crud_pages import GetPage, UpdateLatestPageVersion


@dataclass
class GetPageVersion:
    """Use case for retrieving an existing page."""

    repository: PageVersionRepository
    get_page: GetPage

    async def do(self, page_id: str, page_version: str) -> PageVersion:
        """Execute usecase: Get a page version."""
        page = await self.get_page.do(page_id=page_id)
        version = await self.repository.get_version(
            page_id=page_id, version=page_version
        )
        if version is None:
            raise VersionNotFoundError(page.name, page_version)
        return version


@dataclass
class GetLatestPageVersion:
    """Use case for retrieving an existing page."""

    repository: PageVersionRepository
    get_page: GetPage

    async def do(self, page_id: str) -> PageVersion:
        """Execute usecase: Get a page version."""
        page = await self.get_page.do(page_id=page_id)
        if page.latest_version is None:
            raise VersionNotFoundError(page.name, version="latest")
        version = await self.repository.get_version(
            page_id=page_id, version=page.latest_version
        )
        # QUESTION: This should never happen, because version is defined on the page entity
        # Should we test this line ?
        if version is None:
            raise VersionNotFoundError(page.name, page.latest_version)
        return version


@dataclass
class ListPagesVersions:
    """Use case for listing existing page versions."""

    repository: PageVersionRepository
    get_page: GetPage

    async def do(self, page_id: str) -> t.List[PageVersion]:
        """Execute usecase: List existing pages."""
        await self.get_page.do(page_id=page_id)
        return await self.repository.list_versions(page_id=page_id)


@dataclass
class CreatePageVersion:
    """Use case for creating a new page version."""

    repository: PageVersionRepository
    event_bus: EventBus
    get_page: GetPage
    update_latest_version: UpdateLatestPageVersion
    clock: t.Callable[[], int]

    async def do(
        self, page_id: str, page_version: str, content: bytes, latest: bool
    ) -> PageVersion:
        """Execute usecase: Create a new page version."""
        if not content:
            raise EmptyContentError()
        page = await self.get_page.do(page_id=page_id)
        if await self.repository.version_exists(page_id, page_version):
            raise VersionAlreadyExistsError(page.name, page_version)
        version = PageVersion(
            page_id=page.id,
            page_name=page.name,
            version=page_version,
            checksum=md5(content).hexdigest(),
            created_timestamp=self.clock(),
        )
        # Create the page version within the repository
        await self.repository.create_version(version)
        # Update latest reference
        if latest:
            await self.update_latest_version.do(page_id, version)
        # Emit a page version created event holding version document but NOT version content
        await self.event_bus.publish(
            PAGE_VERSION_CREATED,
            scope=None,
            payload=PageVersionCreated(
                document=version, content=content, latest=latest
            ),
            metadata=None,
        )
        return version


@dataclass
class DeletePageVersion:
    """Use case for deleting an existing page version."""

    repository: PageVersionRepository
    event_bus: EventBus
    get_page: GetPage
    update_latest_version: UpdateLatestPageVersion

    async def do(self, page_id: str, page_version: str) -> None:
        """Delete a page version"""
        page = await self.get_page.do(page_id=page_id)
        if page.latest_version == page_version:
            raise CannotDeleteLatestVersionError(page.name, page.latest_version)
        deleted = await self.repository.delete_version(page_id, page_version)
        if not deleted:
            raise VersionNotFoundError(page.name, page_version)
        await self.event_bus.publish(
            PAGE_VERSION_DELETED,
            scope=None,
            payload=PageVersionDeleted(
                page_id=page_id,
                version=page_version,
                page_name=page.name,
            ),
            metadata=None,
        )

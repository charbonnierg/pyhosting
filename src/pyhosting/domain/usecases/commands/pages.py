import typing as t
from dataclasses import dataclass
from hashlib import md5

from genid import IDGenerator

from synopsys import EventBus

from ...entities import Page, PageVersion
from ...errors import (
    CannotDeleteLatestVersionError,
    EmptyContentError,
    PageAlreadyExistsError,
    PageNotFoundError,
    VersionAlreadyExistsError,
    VersionNotFoundError,
)
from ...events.page import PAGE_CREATED, PAGE_DELETED, PageCreated, PageDeleted
from ...events.version import (
    PAGE_VERSION_CREATED,
    PAGE_VERSION_DELETED,
    PageVersionCreated,
    PageVersionDeleted,
)
from ...repositories import PageRepository, PageVersionRepository


@dataclass
class CreatePage:
    """Use case for creating a new page.

    Dependencies:
        `id_generator`: An implementation of `IDGenerator`.
        `repository`: An implementation of `PageRepository`.
        `event_bus`: An implementation of `EventBus`.
    """

    page_repository: PageRepository
    id_generator: IDGenerator
    event_bus: EventBus

    async def __call__(
        self,
        name: str,
        title: t.Optional[str] = None,
        description: t.Optional[str] = None,
    ) -> Page:
        """Execute usecase: Create a new page."""
        # Check that no page exist with same name
        if await self.page_repository.page_name_exists(name):
            raise PageAlreadyExistsError(name)
        # Create the page in-memory
        page = Page(
            id=self.id_generator.new(),
            name=name,
            title=title or name,
            description=description or "",
            latest_version=None,
        )
        # Store the page
        await self.page_repository.create_page(page)
        # Publish an event
        await self.event_bus.publish(
            event=PAGE_CREATED,
            scope=None,
            payload=PageCreated(document=page),
            metadata=None,
        )
        return page


@dataclass
class UpdateLatestPageVersion:
    """Use case for updating the latest version of a page.

    Dependencies:
        repository: an implementation of `PageRepository`.
    """

    page_repository: PageRepository

    async def __call__(self, page_id: str, version: PageVersion) -> None:
        """Execute usecase: Update page latest version."""
        await self.page_repository.update_latest_version(page_id, version)


@dataclass
class DeletePage:
    """Use case for deleting an existing page.

    Dependencies:
        `repository`: An implementation of `PageRepository`.
        `event_bus`: An implementation of `EventBus`.
    """

    page_repository: PageRepository
    event_bus: EventBus

    async def __call__(self, page_id: str) -> None:
        """Delete a page"""
        page = await self.page_repository.get_page_by_id(page_id)
        if page is None:
            raise PageNotFoundError(page_id)
        await self.page_repository.delete_page(page_id)
        await self.event_bus.publish(
            PAGE_DELETED,
            scope=None,
            payload=PageDeleted(id=page.id, name=page.name),
            metadata=None,
        )


@dataclass
class CreatePageVersion:
    """Use case for creating a new page version."""

    page_repository: PageRepository
    version_repository: PageVersionRepository
    event_bus: EventBus
    clock: t.Callable[[], int]

    async def __call__(
        self, page_id: str, page_version: str, content: bytes, latest: bool
    ) -> PageVersion:
        """Execute usecase: Create a new page version."""
        if not content:
            raise EmptyContentError()
        page = await self.page_repository.get_page_by_id(page_id)
        if page is None:
            raise PageNotFoundError(page_id)
        if await self.version_repository.version_exists(page_id, page_version):
            raise VersionAlreadyExistsError(page.name, page_version)
        version = PageVersion(
            page_id=page.id,
            page_name=page.name,
            version=page_version,
            checksum=md5(content).hexdigest(),
            created_timestamp=self.clock(),
        )
        # Create the page version within the repository
        await self.version_repository.create_version(version)
        # Update latest reference
        if latest:
            await self.page_repository.update_latest_version(page_id, version)
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

    page_repository: PageRepository
    version_repository: PageVersionRepository
    event_bus: EventBus
    update_latest_version: UpdateLatestPageVersion

    async def __call__(self, page_id: str, page_version: str) -> None:
        """Delete a page version"""
        page = await self.page_repository.get_page_by_id(page_id)
        if page is None:
            raise PageNotFoundError(page_id)
        if page.latest_version == page_version:
            raise CannotDeleteLatestVersionError(page.name, page.latest_version)
        deleted = await self.version_repository.delete_version(page_id, page_version)
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

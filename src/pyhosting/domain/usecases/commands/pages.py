import typing as t
from dataclasses import dataclass
from hashlib import md5

from genid import IDGenerator

from synopsys.core.interfaces import AllowPublish

from ...entities import Page, Version
from ...errors import (
    CannotDeleteLatestVersionError,
    EmptyContentError,
    PageAlreadyExistsError,
    PageNotFoundError,
    VersionAlreadyExistsError,
)
from ...events import (
    PAGE_CREATED,
    PAGE_DELETED,
    VERSION_CREATED,
    VERSION_DELETED,
    PageCreated,
    PageDeleted,
    VersionCreated,
    VersionDeleted,
)
from ...operations.archives import validate_archive
from ...repositories import PageRepository


@dataclass
class CreatePage:
    """Use case for creating a new page.

    Dependencies:
        `id_generator`: An implementation of `IDGenerator`.
        `repository`: An implementation of `PageRepository`.
        `event_bus`: An implementation of `AllowPublish`.
    """

    page_repository: PageRepository
    id_generator: IDGenerator
    event_bus: AllowPublish

    async def __call__(
        self,
        name: str,
        title: t.Optional[str] = None,
        description: t.Optional[str] = None,
    ) -> Page:
        """Execute usecase: Create a new page."""
        # Check that no page exist with same name
        try:
            await self.page_repository.get_page_id(name)
        except PageNotFoundError:
            pass
        else:
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
            metadata={},
        )
        return page


@dataclass
class UpdateLatestPageVersion:
    """Use case for updating the latest version of a page.

    Dependencies:
        repository: an implementation of `PageRepository`.
    """

    page_repository: PageRepository

    async def __call__(self, page_id: str, page_version: str) -> None:
        """Execute usecase: Update page latest version."""
        version = await self.page_repository.get_version(page_id, page_version)
        await self.page_repository.update_latest_version(version)


@dataclass
class DeletePage:
    """Use case for deleting an existing page.

    Dependencies:
        `repository`: An implementation of `PageRepository`.
        `event_bus`: An implementation of `AllowPublish`.
    """

    page_repository: PageRepository
    event_bus: AllowPublish

    async def __call__(self, page_id: str) -> None:
        """Delete a page"""
        page = await self.page_repository.get_page(page_id)
        await self.page_repository.delete_page(page_id)
        await self.event_bus.publish(
            PAGE_DELETED,
            scope=None,
            payload=PageDeleted(page_id=page.id, page_name=page.name),
            metadata={},
        )


@dataclass
class PublishVersion:
    """Use case for creating a new page version.

    Dependencies:
        `page_repository`: An implementation of `PageRepository`
        `event_bus`: An implementation of `AllowPublish`.
        `clock`: A callable which returns current epoch time as an integer
    """

    page_repository: PageRepository
    event_bus: AllowPublish
    clock: t.Callable[[], int]

    async def __call__(
        self, page_id: str, page_version: str, content: bytes, latest: bool
    ) -> Version:
        """Execute usecase: Create a new page version."""
        # Save resources by not validating archive or querying page
        if not content:
            raise EmptyContentError()
        # Query page first in order to avoid validating content if page does not exist
        page = await self.page_repository.get_page(page_id)
        if await self.page_repository.version_exists(page_id, page_version):
            raise VersionAlreadyExistsError(page.name, page_version)
        # Validate content (this should run in a threadpool)
        validate_archive(content)
        # Create page version
        version = Version(
            page_id=page.id,
            page_name=page.name,
            page_version=page_version,
            checksum=md5(content).hexdigest(),
            created_timestamp=self.clock(),
        )
        # Create the page version within the repository
        await self.page_repository.create_version(version)
        # Update latest reference
        if latest:
            await self.page_repository.update_latest_version(version)
        # Emit a page version created event holding version document but NOT version content
        await self.event_bus.publish(
            VERSION_CREATED,
            scope=None,
            payload=VersionCreated(
                document=version, content=content.hex(), latest=latest
            ),
            metadata={},
        )
        return version


@dataclass
class DeletePageVersion:
    """Use case for deleting an existing page version.

    Dependencies:
        `page_repository`: An implementation of `PageRepository`
        `event_bus`: An implementation of `AllowPublish`.
    """

    page_repository: PageRepository
    event_bus: AllowPublish

    async def __call__(self, page_id: str, page_version: str) -> None:
        """Delete a page version"""
        page = await self.page_repository.get_page(page_id)
        if page.latest_version == page_version:
            raise CannotDeleteLatestVersionError(page.name, page.latest_version)
        await self.page_repository.delete_version(page_id, page_version)
        await self.event_bus.publish(
            VERSION_DELETED,
            scope=None,
            payload=VersionDeleted(
                page_id=page_id,
                page_version=page_version,
                page_name=page.name,
            ),
            metadata={},
        )

import typing as t
from dataclasses import dataclass
from hashlib import md5
from time import time

from ..commands.crud_versions import (
    CreatePageVersionCommand,
    DeletePageVersionCommand,
    GetLatestPageVersionCommand,
    GetPageVersionCommand,
    ListPageVersionsCommand,
)
from ..entities import PageVersion
from ..errors import (
    CannotDeleteLatestVersionError,
    VersionAlreadyExistsError,
    VersionNotFoundError,
)
from ..events.page_versions import (
    PAGE_VERSION_CREATED,
    PAGE_VERSION_DELETED,
    PageVersionCreated,
    PageVersionDeleted,
)
from ..gateways import EventBusGateway
from ..repositories import PageVersionRepository
from .crud_pages import GetPage, GetPageCommand, UpdateLatestPageVersion


@dataclass
class GetPageVersion:
    """Use case for retrieving an existing page."""

    repository: PageVersionRepository
    get_page: GetPage

    async def do(self, command: GetPageVersionCommand) -> PageVersion:
        """Execute usecase: Get a page version."""
        page = await self.get_page.do(GetPageCommand(command.page_id))
        version = await self.repository.get_version(
            page_id=command.page_id, version=command.version
        )
        if version is None:
            raise VersionNotFoundError(page.name, command.version)
        return version


@dataclass
class GetLatestPageVersion:
    """Use case for retrieving an existing page."""

    repository: PageVersionRepository
    get_page: GetPage

    async def do(self, command: GetLatestPageVersionCommand) -> PageVersion:
        """Execute usecase: Get a page version."""
        page = await self.get_page.do(GetPageCommand(command.page_id))
        if page.latest_version is None:
            raise VersionNotFoundError(page.name, version="latest")
        version = await self.repository.get_version(
            page_id=command.page_id, version=page.latest_version
        )
        # QUESTION: This should never happend, because version is defined on the page entity
        # Should we test this line ?
        if version is None:
            raise VersionNotFoundError(page.name, page.latest_version)
        return version


@dataclass
class ListPagesVersions:
    """Use case for listing existing page versions."""

    repository: PageVersionRepository
    get_page: GetPage

    async def do(self, command: ListPageVersionsCommand) -> t.List[PageVersion]:
        """Execute usecase: List existing pages."""
        await self.get_page.do(GetPageCommand(id=command.page_id))
        return await self.repository.list_versions(page_id=command.page_id)


@dataclass
class CreatePageVersion:
    """Use case for creating a new page version."""

    repository: PageVersionRepository
    event_bus: EventBusGateway
    get_page: GetPage
    update_latest_version: UpdateLatestPageVersion
    clock: t.Callable[[], int] = lambda: int(time())

    async def do(self, command: CreatePageVersionCommand) -> PageVersion:
        """Execute usecase: Create a new page version."""
        page = await self.get_page.do(GetPageCommand(id=command.page_id))
        if await self.repository.version_exists(page.id, command.version):
            raise VersionAlreadyExistsError(page.name, command.version)
        version = PageVersion(
            page_id=page.id,
            page_name=page.name,
            version=command.version,
            checksum=md5(command.content).hexdigest(),
            created_timestamp=self.clock(),
        )
        # Create the page version within the repository
        await self.repository.create_version(version)
        # Update latest reference
        if command.latest:
            await self.update_latest_version.do(page.id, version)
        # Emit a page version created event holding version document but NOT version content
        await self.event_bus.emit_event(
            PAGE_VERSION_CREATED,
            PageVersionCreated(
                document=version, content=command.content, latest=command.latest
            ),
        )
        return version


@dataclass
class DeletePageVersion:
    """Use case for deleting an existing page version."""

    repository: PageVersionRepository
    event_bus: EventBusGateway
    get_page: GetPage
    update_latest_version: UpdateLatestPageVersion

    async def do(self, command: DeletePageVersionCommand) -> None:
        """Delete a page version"""
        page = await self.get_page.do(GetPageCommand(command.page_id))
        if page.latest_version == command.version:
            raise CannotDeleteLatestVersionError(page.name, page.latest_version)
        deleted = await self.repository.delete_version(command.page_id, command.version)
        if not deleted:
            raise VersionNotFoundError(page.name, command.version)
        await self.event_bus.emit_event(
            PAGE_VERSION_DELETED,
            PageVersionDeleted(
                page_id=command.page_id,
                version=command.version,
                page_name=page.name,
            ),
        )

import typing as t
from dataclasses import dataclass

from genid import IDGenerator

from ..commands.crud_pages import CreatePageCommand, DeletePageCommand, GetPageCommand
from ..entities import Page, PageVersion
from ..errors import PageAlreadyExistsError, PageNotFoundError
from ..events.pages import PAGE_CREATED, PAGE_DELETED, PageCreated, PageDeleted
from ..gateways import EventBusGateway
from ..repositories import PageRepository


@dataclass
class GetPage:
    """Use case for retrieving an existing page."""

    repository: PageRepository

    async def do(self, command: GetPageCommand) -> Page:
        """Execute usecase: Get a page."""
        page = await self.repository.get_page_by_id(command.id)
        if page is None:
            raise PageNotFoundError(command.id)
        return page


@dataclass
class UpdateLatestPageVersion:
    """Use case for updating the latest version of a page"""

    repository: PageRepository

    async def do(self, page_id: str, version: PageVersion) -> None:
        """Execute usecase: Update page latest version."""
        await self.repository.update_latest_version(page_id, version)


@dataclass
class ListPages:
    """Use case for listing existing pages."""

    repository: PageRepository

    async def do(self) -> t.List[Page]:
        """Execute usecase: List existing pages."""
        return await self.repository.list_pages()


@dataclass
class CreatePage:
    """Use case for creating a new page."""

    id_generator: IDGenerator
    repository: PageRepository
    event_bus: EventBusGateway

    async def do(self, command: CreatePageCommand) -> Page:
        """Execute usecase: Create a new page."""
        if await self.repository.page_name_exists(command.name):
            raise PageAlreadyExistsError(command.name)
        page = Page(
            id=self.id_generator.new(),
            name=command.name,
            title=command.title or command.name,
            description=command.description or "",
            latest_version=None,
        )
        await self.repository.create_page(page)
        await self.event_bus.emit_event(PAGE_CREATED, PageCreated(document=page))
        return page


@dataclass
class DeletePage:
    """Use case for deleting an existing page."""

    repository: PageRepository
    event_bus: EventBusGateway

    async def do(self, command: DeletePageCommand) -> None:
        """Delete a page"""
        page = await self.repository.get_page_by_id(command.id)
        if page is None:
            raise PageNotFoundError(command.id)
        await self.repository.delete_page(command.id)
        await self.event_bus.emit_event(
            PAGE_DELETED, PageDeleted(id=page.id, name=page.name)
        )

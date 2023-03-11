import typing as t
from dataclasses import dataclass

from genid import IDGenerator

from synopsys import EventBus

from ..entities import Page, PageVersion
from ..errors import PageAlreadyExistsError, PageNotFoundError
from ..events.pages import PAGE_CREATED, PAGE_DELETED, PageCreated, PageDeleted
from ..repositories import PageRepository


@dataclass
class GetPage:
    """Use case for retrieving an existing page.

    Dependencies:
        repository: an implementation of `PageRepository`.
    """

    repository: PageRepository

    async def do(self, page_id: str) -> Page:
        """Execute usecase: Get a page."""
        page = await self.repository.get_page_by_id(page_id)
        if page is None:
            raise PageNotFoundError(page_id)
        return page


@dataclass
class UpdateLatestPageVersion:
    """Use case for updating the latest version of a page.

    Dependencies:
        repository: an implementation of `PageRepository`.
    """

    repository: PageRepository

    async def do(self, page_id: str, version: PageVersion) -> None:
        """Execute usecase: Update page latest version."""
        await self.repository.update_latest_version(page_id, version)


@dataclass
class ListPages:
    """Use case for listing existing pages.

    Dependencies:
        repository: An implementation of `PageRepository`.
    """

    repository: PageRepository

    async def do(self) -> t.List[Page]:
        """Execute usecase: List existing pages."""
        return await self.repository.list_pages()


@dataclass
class CreatePage:
    """Use case for creating a new page.

    Dependencies:
        `id_generator`: An implementation of `IDGenerator`.
        `repository`: An implementation of `PageRepository`.
        `event_bus`: An implementation of `EventBus`.
    """

    id_generator: IDGenerator
    repository: PageRepository
    event_bus: EventBus

    async def do(
        self,
        name: str,
        title: t.Optional[str] = None,
        description: t.Optional[str] = None,
    ) -> Page:
        """Execute usecase: Create a new page."""
        # Check that no page exist with same name
        if await self.repository.page_name_exists(name):
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
        await self.repository.create_page(page)
        # Publish an event
        await self.event_bus.publish(
            event=PAGE_CREATED,
            scope=None,
            payload=PageCreated(document=page),
            metadata=None,
        )
        return page


@dataclass
class DeletePage:
    """Use case for deleting an existing page.

    Dependencies:
        `repository`: An implementation of `PageRepository`.
        `event_bus`: An implementation of `EventBus`.
    """

    repository: PageRepository
    event_bus: EventBus

    async def do(self, page_id: str) -> None:
        """Delete a page"""
        page = await self.repository.get_page_by_id(page_id)
        if page is None:
            raise PageNotFoundError(page_id)
        await self.repository.delete_page(page_id)
        await self.event_bus.publish(
            PAGE_DELETED,
            scope=None,
            payload=PageDeleted(id=page.id, name=page.name),
            metadata=None,
        )

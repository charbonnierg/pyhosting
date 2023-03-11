import typing as t

from pyhosting.domain.entities import Page, PageVersion
from pyhosting.domain.errors import PageNotFoundError
from pyhosting.domain.repositories import PageRepository


class InMemoryPageRepository(PageRepository):
    def __init__(self) -> None:
        """Create a new in-memory pages repository."""
        self._store: t.Dict[str, Page] = {}
        self._names: t.Dict[str, str] = {}

    async def create_page(self, page: Page) -> None:
        self._store[page.id] = page
        self._names[page.name] = page.id

    async def list_pages(self) -> t.List[Page]:
        return list(self._store.values())

    async def get_page_by_id(self, id: str) -> t.Optional[Page]:
        return self._store.get(id, None)

    async def page_name_exists(self, name: str) -> t.Optional[str]:
        return self._names.get(name, None)

    async def delete_page(self, id: str) -> bool:
        page = self._store.pop(id, None)
        if page:
            self._names.pop(page.name, None)
            return True
        return False

    async def update_latest_version(self, id: str, version: PageVersion) -> None:
        try:
            page = self._store[id]
        except KeyError:
            raise PageNotFoundError(id)
        page.latest_version = version.version

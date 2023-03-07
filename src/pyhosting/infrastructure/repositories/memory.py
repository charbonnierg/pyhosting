import typing as t
from collections import defaultdict

from ...domain.entities import Page, PageVersion
from ...domain.errors import PageNotFoundError
from ...domain.repositories import PageRepository, PageVersionRepository


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


class InMemoryPageVersionRepository(PageVersionRepository):
    def __init__(self) -> None:
        super().__init__()
        self._store: t.Dict[str, t.Dict[str, PageVersion]] = defaultdict(dict)

    async def create_version(self, page_version: PageVersion) -> None:
        self._store[page_version.page_id][page_version.version] = page_version

    async def delete_version(self, page_id: str, version: str) -> bool:
        return self._store[page_id].pop(version, None) is not None

    async def get_version(self, page_id: str, version: str) -> t.Optional[PageVersion]:
        return self._store[page_id].get(version, None)

    async def list_versions(self, page_id: str) -> t.List[PageVersion]:
        return list(self._store[page_id].values())

    async def version_exists(self, page_id: str, version: str) -> t.Optional[bool]:
        return version in self._store[page_id]

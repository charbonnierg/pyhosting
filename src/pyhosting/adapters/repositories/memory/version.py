import typing as t
from collections import defaultdict

from pyhosting.domain.entities import PageVersion
from pyhosting.domain.repositories import PageVersionRepository


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

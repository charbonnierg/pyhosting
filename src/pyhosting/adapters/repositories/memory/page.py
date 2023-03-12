import typing as t

from pyhosting.domain.entities import Page, Version
from pyhosting.domain.errors import PageNotFoundError, VersionNotFoundError
from pyhosting.domain.repositories import PageRepository


class InMemoryPageRepository(PageRepository):
    """An in-memory page repository can be used during unit test to avoid writing mocks."""

    def __init__(self) -> None:
        """Create a new in-memory pages repository. Does not accept argument."""
        self._store: t.Dict[str, Page] = {}
        self._names: t.Dict[str, str] = {}
        self._versions_store: t.Dict[str, t.Dict[str, Version]] = {}

    async def get_page_id(self, page_name: str) -> str:
        """Get ID of page with given name.

        Arguments:
            page_name: the page name to get ID for

        Returns:
            The page ID

        Raises:
            PageNotFoundError: when a page with such name does not exist
        """
        if page_name not in self._names:
            raise PageNotFoundError(page_name)
        return self._names[page_name]

    async def get_page(self, page_id: str) -> Page:
        """Get a single page by ID.

        Arguments:
            page_id: the ID of the page to retrieve

        Returns:
            A page entity upon successful get operation

        Raises:
            PageNotFoundError: when a page with such ID does not exist
        """
        if page_id not in self._store:
            raise PageNotFoundError(page_id)
        return self._store[page_id]

    async def create_page(self, page: Page) -> None:
        """Create and store a new page.

        Arguments:
            page: a Page entity

        Returns:
            None
        """
        self._store[page.id] = page
        self._names[page.name] = page.id
        self._versions_store[page.id] = {}

    async def delete_page(self, page_id: str) -> None:
        """Delete a page.

        Arguments:
            page_id: the ID of page to delete

        Returns:
            None

        Raises:
            PageNotFoundError: when no page with such ID exist
        """
        if page_id not in self._store:
            raise PageNotFoundError(page_id)
        page = self._store.pop(page_id)
        self._names.pop(page.name)

    async def list_pages(self) -> t.List[Page]:
        """List existing pages. Does not accept argument.

        Returns:
            A list of `Page` entities
        """
        return list(self._store.values())

    async def update_latest_version(self, version: Version) -> None:
        """Update the latest version of a page to a new version.

        Arguments:
            version: a Version entity used to update the page entity.

        Returns:
            None

        Raises:
            PageNotFoundError: when page referenced by version does not exist
            VersionNotFoundError: when version provided does not exist

        Note: By using a version entity as argument, applications are required to access
        a version entity (and thus check that version exists) before updating the
        latest version of associated page, and thus, reduce the risk of updating
        to a non existing version.
        """
        try:
            page = self._store[version.page_id]
        except KeyError:
            raise PageNotFoundError(version.page_id)
        if version.page_version not in self._versions_store[version.page_id]:
            raise VersionNotFoundError(page.name, version.page_version)
        page.latest_version = version.page_version

    async def version_exists(self, page_id: str, version: str) -> bool:
        """Return True when page version exists else False.

        Returns:
            `True` if page_version exists, else `False`

        Raises:
            PageNotFoundError: when no page with such ID exists
        """
        if page_id not in self._versions_store:
            raise PageNotFoundError(page_id)
        return version in self._versions_store[page_id]

    async def get_version(self, page_id: str, page_version: str) -> Version:
        """Get a single page version.

        Arguments:
            page_id: The ID of page to get version for
            page_version: the version of the page to get

        Returns:
            A `Version` entity

        Raises:
            PageNotFoundError: when page does not exist
            VersionNotFoundError: when version does not exist but page exist
        """
        if page_id not in self._store:
            raise PageNotFoundError(page_id)
        if page_version not in self._versions_store[page_id]:
            raise VersionNotFoundError(self._store[page_id].name, page_version)
        return self._versions_store[page_id][page_version]

    async def create_version(self, version: Version) -> None:
        """Create and store a new page version. No validation is required.

        Arguments:
            version: a `Version` entity

        Returns:
            None
        """
        try:
            self._versions_store[version.page_id][version.page_version] = version
        except KeyError:
            raise PageNotFoundError(version.page_id)

    async def delete_version(self, page_id: str, page_version: str) -> None:
        """Delete a page version.

        Arguments:
            page_id: the page ID to delete version for
            page_version: the page version to delete

        Raises:
            PageNotFoundError: when page does not exist
            VersionNotFoundError: when version does not exist
        """
        if page_id not in self._versions_store:
            raise PageNotFoundError(page_id)
        if page_version not in self._versions_store[page_id]:
            raise VersionNotFoundError(self._store[page_id].name, page_version)
        self._versions_store[page_id].pop(page_version)

    async def list_versions(self, page_id: str) -> t.List[Version]:
        """List existing version for a page.

        Arguments:
            page_id: the ID of the page to list versions for

        Returns:
            A list of `Version` entities

        Raises:
            PageNotFoundError: when page does not exist
        """
        if page_id not in self._versions_store:
            raise PageNotFoundError(page_id)
        return list(self._versions_store[page_id].values())

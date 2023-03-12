"""`PageRepository` protocol definition.

Both `Page` and `Version` entities can be fetched and written using a `PageRepository`.

Because there is a strong relation between pages and versions, decoupling both repositories
would lead to more complex code, thus a single repository is used.
"""
import abc
import typing as t

from ..entities import Page, Version


class PageRepository(metaclass=abc.ABCMeta):
    """Repository where pages are stored."""

    @abc.abstractmethod
    async def get_page_id(self, page_name: str) -> str:
        """Get ID of page with given name.

        Arguments:
            page_name: the page name to get ID for

        Returns:
            The page ID

        Raises:
            PageNotFoundError: when a page with such name does not exist
        """
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def get_page(self, page_id: str) -> Page:
        """Get a single page by ID.

        Arguments:
            page_id: the ID of the page to retrieve

        Returns:
            A page entity upon successful get operation

        Raises:
            PageNotFoundError: when a page with such ID does not exist
        """
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def create_page(self, page: Page) -> None:
        """Create and store a new page.

        Arguments:
            page: a Page entity

        Returns:
            None

        Note:
            This function MAY rise a PageAlreadyExistsError in case page already exists.
            Is it not required though, and behaviour is not subject to specification.
        """
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def delete_page(self, page_id: str) -> None:
        """Delete a page.

        Arguments:
            page_id: the ID of page to delete

        Returns:
            None

        Raises:
            PageNotFoundError: when no page with such ID exist
        """
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def list_pages(self) -> t.List[Page]:
        """List existing pages. Does not accept argument.

        Returns:
            A list of `Page` entities
        """
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def update_latest_version(self, version: Version) -> None:
        """Update the latest version of a page to a new version.

        Arguments:
            version: a Version entity used to update the page entity.

        Raises:
            PageNotFoundError: when page referenced by version does not exist
            VersionNotFoundError: when version provided does not exist

        Note: By using a version entity as argument, applications are required to access
        a version entity (and thus check that version exists) before updating the
        latest version of associated page, and thus, reduce the risk of updating
        to a non existing version.
        """
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def version_exists(self, page_id: str, page_version: str) -> bool:
        """Return True when page version exists else False.

        Returns:
            `True` if page_version exists, else `False`

        Raises:
            PageNotFoundError: when no page with such ID exists
        """
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
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
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def create_version(self, version: Version) -> None:
        """Create and store a new page version. No validation is required.

        Arguments:
            version: a `Version` entity

        Returns:
            None
        """
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def delete_version(self, page_id: str, page_version: str) -> None:
        """Delete a page version.

        Arguments:
            page_id: the page ID to delete version for
            page_version: the page version to delete

        Raises:
            PageNotFoundError: when page does not exist
            VersionNotFoundError: when version does not exist
        """
        raise NotImplementedError  # pragma: no cover

    @abc.abstractmethod
    async def list_versions(self, page_id: str) -> t.List[Version]:
        """List existing version for a page.

        Arguments:
            page_id: the ID of the page to list versions for

        Returns:
            A list of `Version` entities

        Raises:
            PageNotFoundError: when page does not exist
        """
        raise NotImplementedError  # pragma: no cover

"""The PagesClient protocol defines how remote clients interacting with the Page API must be implemented.

The only supported protocol to interact with the PagesAPI is the HTTP protocol.
Other protocols could be supported in the future, such as NATS.

The HTTP client, and all future clients, regardless of protocol, will expose the same methods and return the same types.
"""
import typing as t

from ..entities import Page, Version


class PagesAPIClient(t.Protocol):
    def api_version(self) -> str:
        """Return PagesAPI version.

        Returns:
            The PagesAPI version a string
        """
        raise NotImplementedError  # pragma: no cover

    def list_pages(self) -> t.List[Page]:
        """List pages.

        Returns:
            A list of pages entities
        """
        raise NotImplementedError  # pragma: no cover

    def get_page_by_name(self, name: str) -> Page:
        """Create a new page.

        Arguments:
            name: the page name

        Returns:
            A page entity upon successful query

        Raises:
            PageNotFoundError: When page does not exist
        """
        raise NotImplementedError  # pragma: no cover

    def get_page(self, id: str) -> Page:
        """Get a page by ID.

        Arguments:
            id: the page ID

        Returns:
            A page entity upon successful query.

        Raises:
            PageNotFoundError: When page does not exist
        """
        raise NotImplementedError  # pragma: no cover

    def create_page(
        self,
        name: str,
        title: t.Optional[str] = None,
        description: t.Optional[str] = None,
    ) -> Page:
        """Create a new page.

        Arguments:
            name: the page name
            title: the page title (set to page name if not provided)
            description: the page description (set to empty string if not provided)

        Returns:
            A page entity upon successful creation.

        Raises:
            PagesAlreadyExistError: when a page with same name already exists
        """
        raise NotImplementedError  # pragma: no cover

    def delete_page(self, id: str) -> None:
        """Delete a page by ID.

        Arguments:
            id: the page ID

        Returns:
            None in case of successful deletion

        Raises:
            PageNotFoundError: when page does not exist
        """
        raise NotImplementedError  # pragma: no cover

    def publish_page_version(
        self,
        id: str,
        version: str,
        content: bytes,
        latest: bool = False,
    ) -> Version:
        """Publish a new page version.

        Arguments:
            id: the page ID
            version: the version being published
            content: the content being published
            latest: when true, indicates that version is the latest version

        Returns:
            A version entity upon successful creation.

        Raises:
            VersionAlreadyExistsError: when version already exists
            PageNotFoundError: when page does not exist
        """
        raise NotImplementedError  # pragma: no cover

    def get_page_version(self, id: str, version: str) -> Version:
        """Get info for a page version.

        Arguments:
            id: the page ID
            version: the page version

        Returns:
            A version entity upon successful query

        Raises:
            PageNotFoundError: when page does not exist
            VersionNotFoundError: when version does not exist
        """
        raise NotImplementedError  # pragma: no cover

    def delete_page_version(
        self,
        id: str,
        version: str,
    ) -> None:
        """Delete a page version.

        Arguments:
            id: the page ID
            version: the page version

        Returns:
            None upon successful deletion

        Raises:
            PageNotFoundError: when page does not exist
            VersionNotFoundError: when version does not exist
        """
        raise NotImplementedError  # pragma: no cover

    def list_page_versions(self, id: str) -> t.List[Version]:
        """List page versions.

        Arguments:
            id: the page ID

        Returns:
            A list of Version entities upon successful query.

        Raises:
            PageNotFoundError: when page does not exist
        """
        raise NotImplementedError  # pragma: no cover

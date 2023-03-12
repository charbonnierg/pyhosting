"""HTTP Client for the PagesAPI.

Built upon [httpx](https://www.python-httpx.org/)
"""
import typing as t

from httpx import Client

from pyhosting.domain.clients.pages import PagesAPIClient
from pyhosting.domain.entities import Page, Version
from pyhosting.domain.errors import (
    InvalidRequestError,
    PageAlreadyExistsError,
    PageNotFoundError,
    VersionAlreadyExistsError,
    VersionNotFoundError,
)


class BasePagesAPIHTTPClient(PagesAPIClient):
    """Base HTTP client to interact with Pages API.

    This class implements the `PagesAPIClient` protocol.

    Do not use this client directly, instead use one of:

    - PagesAPIHTTPClient: When writing applications (this client is used by the command line interface)
    - PagesAPITestHTTPClient: When writing internal tests (this client is used to test HTTP controller without network)
    """

    def __init__(self, client: Client) -> None:
        """Child classes must override this method in order to remove the need for a client argument."""
        self.http = client

    def api_version(self) -> str:
        """Return PagesAPI version.

        Returns:
            The PagesAPI version a string

        Raises:
            httpx.HTTPStatusError: when an HTTP error is received
        """
        response = self.http.get("/api/version")
        response.raise_for_status()
        return str(response.json()["version"])

    def list_pages(self) -> t.List[Page]:
        """List pages.

        Returns:
            A list of pages entities

        Raises:
            httpx.HTTPStatusError: when an HTTP error is received
        """
        response = self.http.get("/api/pages/")
        response.raise_for_status()
        return [Page(**item) for item in response.json()["documents"]]

    def get_page_by_name(self, name: str) -> Page:
        """Get a page by name.

        Arguments:
            name: the page name

        Returns:
            A page entity upin successful query.

        Raises:
            PageNotFoundError: When page does not exist
            httpx.HTTPStatusError: when an HTTP error is received
        """
        response = self.http.get("/api/pages/")
        response.raise_for_status()
        for page in response.json()["documents"]:
            if page["name"].lower() == name.lower():
                return Page(**page)
        raise PageNotFoundError(name)

    def get_page(self, id: str) -> Page:
        """Get a page by ID.

        Arguments:
            id: the page ID

        Returns:
            A page entity upon successful query

        Raises:
            PageNotFoundError: When page does not exist
            httpx.HTTPStatusError: when an HTTP error is received
        """
        response = self.http.get(f"/api/pages/{id}")
        # Raise PageNotFoundError instead of 404 HTTP error
        if response.status_code == 404:
            raise PageNotFoundError(id)
        # Raise other HTTP errors
        response.raise_for_status()
        # Return a page entity
        return Page(**response.json()["document"])

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
            httpx.HTTPStatusError: when an HTTP error is received
        """
        response = self.http.post(
            "/api/pages/",
            json={"title": title, "description": description, "name": name},
        )
        # Raise PageAlreadyExistsError instead of HTTP 409 error
        if response.status_code == 409:
            raise PageAlreadyExistsError(name)
        # Raise other HTTP errors
        response.raise_for_status()
        # Return a Page entity
        return Page(**response.json()["document"])

    def delete_page(self, id: str) -> None:
        """Delete a page by ID.

        Arguments:
            id: the page ID

        Returns:
            None in case of successful deletion

        Raises:
            PageNotFoundError: when page does not exist
        """
        response = self.http.delete(f"/api/pages/{id}")
        # raise PageNotFoundError instead of 404 HTTP Error
        if response.status_code == 404:
            raise PageNotFoundError(id)
        # raise other HTTP errors
        response.raise_for_status()

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
            httpx.HTTPStatusError: when an HTTP error is received
        """
        headers = {"x-page-version": version}
        if latest:
            headers["x-page-latest"] = "1"
        response = self.http.post(
            f"/api/pages/{id}/versions/",
            headers=headers,
            content=content,
        )
        # Raise domain errors
        if response.status_code == 409:
            raise VersionAlreadyExistsError(id, version)
        if response.status_code == 404:
            raise PageNotFoundError(id)
        if response.status_code == 428:
            raise InvalidRequestError(response.json()["detail"]["error"])
        # Raise other HTTP errors
        response.raise_for_status()
        # Return a Version entity
        return Version(**response.json()["document"])

    def get_page_version(self, id: str, version: str) -> Version:
        """Get info for a page version.

        Arguments:
            id: the page ID
            version: the page version

        Returns:
            A version entity upon successful query.

        Raises:
            PageNotFoundError: when page does not exist
            VersionNotFoundError: when version does not exist
            httpx.HTTPStatusError: when an HTTP error is received
        """
        response = self.http.get(f"/api/pages/{id}/versions/{version}")
        # Raise domain errors
        # TODO: Parse error to raise either "[Page|Version]NotFoundError"
        if response.status_code == 404:
            raise VersionNotFoundError(id, version)
        # Raise HTTP errors
        response.raise_for_status()
        # Return version entity
        return Version(**response.json()["document"])

    def delete_page_version(self, id: str, version: str) -> None:
        """Delete a page version.

        Arguments:
            id: the page ID
            version: the page version

        Returns:
            None upon successful deletion.

        Raises:
            PageNotFoundError: when page does not exist
            VersionNotFoundError: when version does not exist
            httpx.HTTPStatusError: when an HTTP error is received
        """
        response = self.http.delete(f"/api/pages/{id}/versions/{version}")
        # Raise domain errors
        if response.status_code == 404:
            raise VersionNotFoundError(id, version)
        # Raise HTTP errors
        response.raise_for_status()

    def list_page_versions(self, id: str) -> t.List[Version]:
        """List page versions.

        Arguments:
            id: the page ID

        Returns:
            A list of Version entities upon successful query.

        Raises:
            PageNotFoundError: when page does not exist
            httpx.HTTPStatusError: when an HTTP error is received
        """
        response = self.http.get(f"/api/pages/{id}/versions/")
        # Raise domain errors
        if response.status_code == 404:
            raise PageNotFoundError(id)
        # Raise HTTP errors
        response.raise_for_status()
        return [Version(**item) for item in response.json()["documents"]]


class PagesAPIHTTPClient(BasePagesAPIHTTPClient):
    """An HTTP client which can be used to interact with the Pages API.

    The Pages API includes all endpoints related to pages and pages versions.
    """

    def __init__(
        self, base_url: str = "http://localhost:8000", **kwargs: t.Any
    ) -> None:
        """Create a new HTTP client.

        Arguments:
            base_url: the remote Pages API base URL (without `/api` path)
            **kwargs: Any argument accepted by `httpx.Client` class.
        """
        kwargs["base_url"] = base_url
        super().__init__(Client(**kwargs))

import typing as t

from httpx import Client

from pyhosting.domain.clients.pages import PagesClient
from pyhosting.domain.entities import Page, PageVersion
from pyhosting.domain.errors import PageNotFoundError


class BaseHTTPPagesClient(PagesClient):
    def __init__(self, client: Client) -> None:
        self.http = client

    def list_pages(self) -> t.List[Page]:
        """List pages"""
        response = self.http.get("/api/pages/")
        response.raise_for_status()
        return [Page(**item) for item in response.json()["documents"]]

    def create_page(
        self,
        name: str,
        title: t.Optional[str] = None,
        description: t.Optional[str] = None,
    ) -> Page:
        """Create a new page."""
        response = self.http.post(
            "/api/pages/",
            json={"title": title, "description": description, "name": name},
        )
        response.raise_for_status()
        return Page(**response.json()["document"])

    def get_page(self, id: str) -> Page:
        """Get a page by ID."""
        response = self.http.get(f"/api/pages/{id}")
        response.raise_for_status()
        return Page(**response.json()["document"])

    def delete_page(self, id: str) -> None:
        """Delete a page by ID."""
        response = self.http.delete(f"/api/pages/{id}")
        response.raise_for_status()

    def get_page_by_name(self, name: str) -> Page:
        """Get a page by name."""
        response = self.http.get("/api/pages/")
        response.raise_for_status()
        for page in response.json()["documents"]:
            if page["name"].lower() == name.lower():
                return Page(**page)
        raise PageNotFoundError(name)

    def publish_page_version(
        self,
        id: str,
        version: str,
        content: bytes,
        latest: bool = False,
    ) -> PageVersion:
        """Publish a new page version."""
        headers = {"x-page-version": version}
        if latest:
            headers["x-page-latest"] = "1"
        response = self.http.post(
            f"/api/pages/{id}/versions/",
            headers=headers,
            content=content,
        )
        response.raise_for_status()
        return PageVersion(**response.json()["document"])

    def get_page_version(self, id: str, version: str) -> PageVersion:
        """Get info for a page version."""
        response = self.http.get(f"/api/pages/{id}/versions/{version}")
        response.raise_for_status()
        return PageVersion(**response.json()["document"])

    def delete_page_version(self, id: str, version: str) -> None:
        """Delete a page version"""
        response = self.http.delete(f"/api/pages/{id}/versions/{version}")
        response.raise_for_status()

    def list_page_versions(self, id: str) -> t.List[PageVersion]:
        """List page versions."""
        response = self.http.get(f"/api/pages/{id}/versions/")
        response.raise_for_status()
        return [PageVersion(**item) for item in response.json()["documents"]]


class HTTPPagesClient(BaseHTTPPagesClient):
    """An HTTP client which can be used to interact with the Pages API.

    The Pages API includes all endpoints related to pages and pages versions.
    """

    def __init__(
        self, endpoint: str = "http://localhost:8000", **kwargs: t.Any
    ) -> None:
        super().__init__(Client(base_url=endpoint, **kwargs))
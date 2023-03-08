import typing as t

from httpx import Client

from ...domain.entities import Page, PageVersion
from ...domain.errors import PageNotFoundError
from .protocol import ControlPlaneClient


class BaseHTTPControlPlaneClient(ControlPlaneClient):
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
        response = self.http.get(f"/api/pages/{id}")
        response.raise_for_status()
        return Page(**response.json()["document"])

    def delete_page(self, id: str) -> None:
        response = self.http.delete(f"/api/pages/{id}")
        response.raise_for_status()

    def get_page_by_name(self, name: str) -> Page:
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


class HTTPControlPlaneClient(BaseHTTPControlPlaneClient):
    def __init__(
        self, endpoint: str = "http://localhost:8000", **kwargs: t.Any
    ) -> None:
        super().__init__(Client(base_url=endpoint, **kwargs))

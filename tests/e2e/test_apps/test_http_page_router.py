from starlette import status

from pyhosting.clients.controlplane.testing import HTTPTestClient
from tests.utils import parametrize_id_generator


def test_list_pages(client: HTTPTestClient) -> None:
    """Check response from GET /pages."""
    response = client.http.get("/api/pages/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"pages": []}


@parametrize_id_generator("constant", value="fakeid")
def test_create_page(client: HTTPTestClient) -> None:
    """Check response from POST /pages."""
    payload = {"name": "test", "title": "Test Page"}
    response = client.http.post("/api/pages/", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"id": "fakeid"}


@parametrize_id_generator("constant", value="fakeid")
def test_create_page_already_exists(client: HTTPTestClient) -> None:
    """Check response from POST /pages."""
    client.create_page(name="test", title="Test Page")
    response = client.http.post("/api/pages/", json={"name": "test"})
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json() == {"error": "Page already exists: test"}


def test_get_page_does_not_exist(client: HTTPTestClient) -> None:
    """Check response from GET /pages/<id>"""
    response = client.http.get("/api/pages/fakeid")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"error": "Page not found: fakeid"}


@parametrize_id_generator("constant", value="fakeid")
def test_get_page(client: HTTPTestClient) -> None:
    """Check response from GET /pages/<id>"""
    client.create_page(name="test", title="Test Page")
    response = client.http.get("/api/pages/fakeid")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "name": "test",
        "title": "Test Page",
        "id": "fakeid",
        "description": "",
        "latest_version": None,
    }


def test_delete_page_not_found(client: HTTPTestClient) -> None:
    """Check response from DELETE /pages/<id>"""
    response = client.http.delete("/api/pages/fakeid")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"error": "Page not found: fakeid"}


@parametrize_id_generator("constant", value="fakeid")
def test_delete_page(client: HTTPTestClient) -> None:
    """Check response from DELETE /pages/<id>"""
    client.create_page(name="test")
    response = client.http.delete("/api/pages/fakeid")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.content == b""

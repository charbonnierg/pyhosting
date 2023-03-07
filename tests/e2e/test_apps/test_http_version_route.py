from starlette import status

from pyhosting import __version__
from pyhosting.clients.controlplane.testing import HTTPTestClient


def test_version_route(client: HTTPTestClient) -> None:
    """Check response from GET /version."""
    response = client.http.get("/api/version")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"version": __version__}

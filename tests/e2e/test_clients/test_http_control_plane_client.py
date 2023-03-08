from pyhosting.clients.controlplane.http import HTTPControlPlaneClient


def test_http_client_init():
    client = HTTPControlPlaneClient("http://somewhere")
    assert client.http.base_url == "http://somewhere"

import pytest
from _pytest.fixtures import SubRequest

from pyhosting.adapters.gateways.blob_storage import InMemoryBlobStorage
from pyhosting.domain.errors import BlobNotFoundError
from pyhosting.domain.gateways import BlobStorageGateway


@pytest.fixture
def storage(request: SubRequest):
    param = request.param
    yield param()


@pytest.mark.parametrize("storage", [InMemoryBlobStorage], indirect=True)
class TestBlobStorage:
    @pytest.mark.asyncio
    async def test_get_not_found(self, storage: BlobStorageGateway):
        with pytest.raises(BlobNotFoundError, match="Blob not found: key"):
            await storage.get("key")

    @pytest.mark.asyncio
    async def test_put_get(self, storage: BlobStorageGateway):
        await storage.put("key", blob=b"data")
        await storage.put("other", blob=b"other")
        read = await storage.get("key")
        assert read == b"data"

    @pytest.mark.asyncio
    async def test_put_delete(self, storage: BlobStorageGateway):
        await storage.put("key", blob=b"data")
        await storage.put("other", blob=b"other")
        await storage.delete("key")
        with pytest.raises(BlobNotFoundError, match="Blob not found: key"):
            await storage.get("key")

    @pytest.mark.asyncio
    async def test_delete_not_found(self, storage: BlobStorageGateway):
        with pytest.raises(BlobNotFoundError, match="Blob not found: key"):
            await storage.delete("key")

    @pytest.mark.asyncio
    async def test_put_list_keys(self, storage: BlobStorageGateway):
        await storage.put("key", blob=b"data")
        await storage.put("other", blob=b"other")
        assert await storage.list_keys() == ["key", "other"]
        assert await storage.list_keys("") == ["key", "other"]
        assert await storage.list_keys("key") == ["key"]

    @pytest.mark.asyncio
    async def test_put_list_nested_keys(self, storage: BlobStorageGateway):
        await storage.put("key", blob=b"data")
        await storage.put("key", "1", blob=b"data/1")
        await storage.put("key", "1", "a", blob=b"data/1/a")
        await storage.put("other", blob=b"otherdata")
        assert await storage.list_keys() == ["key", "key/1", "key/1/a", "other"]
        assert await storage.list_keys("") == ["key", "key/1", "key/1/a", "other"]
        assert await storage.list_keys("key") == ["key", "key/1", "key/1/a"]
        assert await storage.list_keys("key", "1") == ["key/1", "key/1/a"]
        assert await storage.list_keys("key", "1", "a") == ["key/1/a"]

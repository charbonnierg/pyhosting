import typing as t
from io import BytesIO

from minio import Minio, S3Error

from pyhosting.domain.gateways import BlobStorageGateway


class MinioStorage(BlobStorageGateway):
    def __init__(
        self,
        uri: str = "http://localhost:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        bucket: str = "pyhosting",
    ) -> None:
        super().__init__()
        self.bucket = bucket
        scheme, *parts = uri.split("://", maxsplit=1)
        self.endpoint = "".join(parts)
        if scheme == "https":
            secure = True
        else:
            secure = False
        self.minio = Minio(
            self.endpoint, access_key=access_key, secret_key=secret_key, secure=secure
        )

    def prepare(self) -> None:
        try:
            self.minio.make_bucket(self.bucket)
        except S3Error as exc:
            if exc.code == "BucketAlreadyOwnedByYou":
                pass

    async def get(self, *key: str) -> bytes:
        response = self.minio.get_object(self.bucket, "/".join(key))
        return response.read()

    async def put(self, *key: str, blob: bytes) -> None:
        io = BytesIO(blob)
        self.minio.put_object(self.bucket, "/".join(key), io, len(blob))

    async def delete(self, *key: str) -> None:
        self.minio.delete_object(self.bucket, "/".join(key))

    async def list_keys(self, *prefixes: str) -> t.List[str]:
        return [
            item.object_name
            for item in self.minio.list_objects(self.bucket, prefix="/".join(prefixes))
        ]

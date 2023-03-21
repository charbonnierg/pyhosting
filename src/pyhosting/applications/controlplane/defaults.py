import typing as t
from time import time

from genid import IDGenerator, ObjectIDGenerator
from nats import NATS

from pyhosting.adapters.gateways import Jinja2Loader, TemporaryDirectory
from pyhosting.adapters.gateways.blob_storage.minio import MinioStorage
from pyhosting.adapters.repositories.memory import InMemoryPageRepository
from pyhosting.domain.gateways import (
    BlobStorageGateway,
    FilestorageGateway,
    TemplateLoader,
)
from pyhosting.domain.repositories import PageRepository
from synopsys import EventBus
from synopsys.adapters.codecs import PydanticCodec
from synopsys.adapters.nats import NATSEventBus


def defaults(
    id_generator: t.Optional[IDGenerator] = None,
    page_repository: t.Optional[PageRepository] = None,
    event_bus: t.Optional[EventBus] = None,
    blob_storage: t.Optional[BlobStorageGateway] = None,
    local_storage: t.Optional[FilestorageGateway] = None,
    template_loader: t.Optional[TemplateLoader] = None,
    clock: t.Optional[t.Callable[[], int]] = None,
) -> t.Tuple[
    IDGenerator,
    PageRepository,
    EventBus,
    BlobStorageGateway,
    FilestorageGateway,
    TemplateLoader,
    t.Callable[[], int],
]:
    return (
        id_generator or ObjectIDGenerator(),
        page_repository or InMemoryPageRepository(),
        event_bus or NATSEventBus(nc=NATS(), codec=PydanticCodec()),
        blob_storage or MinioStorage(),
        local_storage or TemporaryDirectory(),
        template_loader or Jinja2Loader(),
        clock or (lambda: int(time())),
    )

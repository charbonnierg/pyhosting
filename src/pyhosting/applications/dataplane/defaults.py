import typing as t

from nats import NATS

from pyhosting.adapters.gateways import (
    InMemoryBlobStorage,
    Jinja2Loader,
    TemporaryDirectory,
)
from pyhosting.domain.gateways import (
    BlobStorageGateway,
    FilestorageGateway,
    TemplateLoader,
)
from synopsys import EventBus
from synopsys.adapters.codecs import PydanticCodec
from synopsys.adapters.nats import NATSEventBus


def defaults(
    event_bus: t.Optional[EventBus] = None,
    blob_storage: t.Optional[BlobStorageGateway] = None,
    local_storage: t.Optional[FilestorageGateway] = None,
    template_loader: t.Optional[TemplateLoader] = None,
) -> t.Tuple[EventBus, BlobStorageGateway, FilestorageGateway, TemplateLoader,]:
    return (
        event_bus or NATSEventBus(NATS(), PydanticCodec()),
        blob_storage or InMemoryBlobStorage(),
        local_storage or TemporaryDirectory(),
        template_loader or Jinja2Loader(),
    )

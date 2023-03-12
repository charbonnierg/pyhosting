from synopsys import create_event

from .models import (
    PageCreated,
    PageDeleted,
    VersionCreated,
    VersionDeleted,
    VersionUploaded,
)

PAGE_CREATED = create_event(
    name="page-created",
    address="page.created",
    schema=PageCreated,
    description="Event triggered when a page is successfully created",
)


PAGE_DELETED = create_event(
    name="page-deleted",
    address="page.deleted",
    schema=PageDeleted,
    description="Event triggered when a page is successfully deleted",
)


VERSION_CREATED = create_event(
    name="version-created",
    address="pages.created",
    schema=VersionCreated,
    description=(
        "Event triggered when a version is successfully created. "
        "Control plane must react to this event and upload the version to blob storage."
    ),
)


VERSION_UPLOADED = create_event(
    name="version-uploaded",
    address="pages.versions.uploaded",
    schema=VersionUploaded,
    description=(
        "Event triggered when a version is successfully uploaded to blob storage. "
        "Page fileservers must react to this event and download version from blob storage."
    ),
)


VERSION_DELETED = create_event(
    name="version-deleted",
    address="pages.versions.deleted",
    schema=VersionDeleted,
    description=(
        "Event triggered when a version is successfully deleted. "
        "Page fileservers must react to this event and remove the "
        "version from their cache."
    ),
)

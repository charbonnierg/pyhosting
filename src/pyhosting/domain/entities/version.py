from dataclasses import dataclass


@dataclass
class Version:
    """Page version entity.

    A page version is a reference to a single page application (where a single page application
    is a directory containing at least a file named `index.html`).

    Several versions may exist for a single page.

    A single version at a time is considered the latest version.

    Note that the concept of latest version is not defined on version
    entities, instead it is defined on page entities.
    """

    page_id: str
    """The version page ID. All versions of a single page share the same page ID."""

    page_name: str
    """The version page name. All versions of a single page share the same page name."""

    page_version: str
    """The page version. Unique."""

    checksum: str
    """The page archive checksum. Note that archive are compressed using gzip and gzip checksums are not deterministic.

    Thus, compressing the same directory twice will produce a different checksum.
    """

    created_timestamp: int
    """The timestamp at which page version was fist published."""

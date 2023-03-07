from dataclasses import dataclass


@dataclass
class PageVersion:
    """Page version entity."""

    page_id: str
    page_name: str
    version: str
    checksum: str
    created_timestamp: int

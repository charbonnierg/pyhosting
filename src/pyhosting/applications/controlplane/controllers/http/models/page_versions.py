import typing as t

from pydantic import BaseModel

from pyhosting.domain.entities.version import PageVersion


class CreatePageVersionResult(BaseModel):
    """Result returned after successfully created page version."""

    document: PageVersion


class GetPageVersionResult(BaseModel):
    document: PageVersion


class ListPageVersionsResult(BaseModel):
    documents: t.List[PageVersion]

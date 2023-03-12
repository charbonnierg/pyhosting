import typing as t

from pydantic import BaseModel

from pyhosting.domain.entities import Page, Version


class GetPageResult(BaseModel):
    document: Page


class ListPagesResult(BaseModel):
    documents: t.List[Page]


class CreatePageOptions(BaseModel):
    name: str
    title: t.Optional[str] = None
    description: t.Optional[str] = None


class CreatePageResult(BaseModel):
    document: Page


class CreatePageVersionResult(BaseModel):
    """Result returned after successfully created page version."""

    document: Version


class GetPageVersionResult(BaseModel):
    document: Version


class ListPageVersionsResult(BaseModel):
    documents: t.List[Version]

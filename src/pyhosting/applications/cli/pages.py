import json
import typing as t
from dataclasses import asdict
from pathlib import Path

import httpx
import typer

from pyhosting.clients.pages.http import HTTPPagesClient

page = typer.Typer(name="page", no_args_is_help=True)


@page.command("list")
def list() -> None:
    client = HTTPPagesClient()
    try:
        pages = client.list_pages()
    except httpx.HTTPError as exc:
        typer.echo(exc.request.content)
        raise typer.Exit(1)
    typer.echo(json.dumps([page.name for page in pages], indent=2))
    raise typer.Exit(0)


@page.command("info")
def get_infos(name: str) -> None:
    client = HTTPPagesClient()
    try:
        page = client.get_page_by_name(name)
    except httpx.HTTPError as exc:
        typer.echo(exc.request.content)
        raise typer.Exit(1)
    typer.echo(json.dumps(asdict(page), indent=2))
    raise typer.Exit(0)


@page.command("create")
def create(
    name: str, title: t.Optional[str] = None, description: t.Optional[str] = None
) -> None:
    client = HTTPPagesClient()
    try:
        page = client.create_page(name=name, title=title, description=description)
    except httpx.HTTPStatusError as exc:
        typer.echo(exc.response.content)
        raise typer.Exit(1)
    typer.echo(json.dumps({"id": page.id}, indent=2))
    raise typer.Exit(0)


@page.command("publish")
def publish(
    name: str = typer.Argument(..., help="Page name"),
    path: str = typer.Argument(..., help="Source directory"),
    version: str = typer.Option(..., help="Version"),
    latest: bool = typer.Option(False, help="Mark version as latest version"),
) -> None:
    client = HTTPPagesClient()
    try:
        page = client.get_page_by_name(name=name)
    except httpx.HTTPStatusError as exc:
        typer.echo(exc.response.content)
        raise typer.Exit(1)
    # TODO: Could create a tarball if path is a directory.
    # This way we would support: .html / .tar.gz / directories with index.html
    try:
        new_version = client.publish_page_version(
            page.id, version, Path(path).read_bytes(), latest=latest
        )
    except httpx.HTTPStatusError as exc:
        typer.echo(f"Request failed with status {exc.response.status_code}")
        typer.echo(exc.response.content)
        raise typer.Exit(1)
    except FileNotFoundError:
        typer.echo(f"File not found: {path}", err=True)
        raise typer.Exit(1)
    typer.echo(json.dumps(asdict(new_version), indent=2))
    raise typer.Exit(0)

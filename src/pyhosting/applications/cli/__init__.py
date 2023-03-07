import typer

from pyhosting import __version__

from .cp import cp
from .dp import dp
from .pages import page

cli = typer.Typer(name="pyhosting", no_args_is_help=True)
"""pyhosting CLI entrypoint."""


def version_callback(value: bool) -> None:
    """Callback to show version and exit when '--version' option is provided."""
    if value:
        print(__version__)
        raise typer.Exit()


@cli.callback()
def common(
    ctx: typer.Context,
    version: bool = typer.Option(None, "--version", callback=version_callback),
) -> None:
    """CLI callback to add global options."""
    pass


cli.add_typer(page)
cli.add_typer(cp)
cli.add_typer(dp)

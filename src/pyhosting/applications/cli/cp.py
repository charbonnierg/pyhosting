import typer

from pyhosting.applications.controlplane.factory import create_app

cp = typer.Typer(name="cp", no_args_is_help=True)


@cp.command("start")
def start() -> None:
    try:
        import uvicorn
    except ImportError:
        typer.echo(
            "uvicorn must be installed in order to start applications."
            " The extra 'uvicorn' provides uvicorn dependency:\n"
            "    $ python -m pip install pyhosting[uvicorn]",
            err=True,
        )
        raise typer.Exit(1)

    config = uvicorn.Config(create_app, factory=True)
    server = uvicorn.Server(config)

    server.run()

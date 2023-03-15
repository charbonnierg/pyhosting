import typer

from pyhosting.applications.dataplane.factory import create_app

dp = typer.Typer(name="dp", no_args_is_help=True)


@dp.command("start")
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

    config = uvicorn.Config(create_app, factory=True, port=9000)
    server = uvicorn.Server(config)
    server.run()

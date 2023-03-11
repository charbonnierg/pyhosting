from typer.testing import CliRunner

from pyhosting import __version__
from pyhosting.applications.cli import cli

runner = CliRunner()


HELP_MSG = """Usage: ph [OPTIONS] COMMAND [ARGS]...

  CLI callback to add global options.

Options:
  --version
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.
  --help                          Show this message and exit.

Commands:
  cp
  dp
  page
"""


def test_version_flag():
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert result.stdout == __version__ + "\n"


def test_help_flag():
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert result.stdout == HELP_MSG

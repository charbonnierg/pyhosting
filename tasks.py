import os
import typing as t
from pathlib import Path
from shlex import quote
from shutil import rmtree

from invoke import Context, task

VENV_DIR = Path(__file__).parent.resolve(True) / ".venv"

if os.name == "nt":
    VENV_PYTHON = VENV_DIR.joinpath("Scripts/python.exe").as_posix()
else:
    VENV_PYTHON = VENV_DIR.joinpath("bin/python").as_posix()


def run_or_display(c: Context, cmd: str, dry_run: bool):
    if dry_run:
        print(cmd)
    else:
        c.run(cmd)


@task
def clean(
    c: Context,
    docs: bool = False,
    bytecode: bool = False,
    extra: str = "",
    dry_run: bool = False,
):
    """Clean build artifacts and optionally documentation artifacts as well as generated bytecode."""
    patterns = ["dist/*.whl", "dist/*.tar.gz"]
    if docs:
        patterns.append("dist/documentation")
    if bytecode:
        patterns.append("**/*.pyc")
    if extra:
        patterns.append(quote(extra))
    cmd = f"rm -rf {' '.join(patterns)}"
    run_or_display(c, cmd, dry_run=dry_run)


@task
def requirements(c: Context, with_hashes: bool = False, dry_run: bool = False):
    """Generate requirementx.txt (required to build docker image)"""
    cmd = (
        f"{VENV_PYTHON} -m piptools compile"
        " --no-header"
        " --output-file=requirements.txt"
        " --resolver=backtracking"
    )
    if with_hashes:
        cmd += " --generate-hashes"
    cmd += " pyproject.toml"
    run_or_display(c, cmd, dry_run=dry_run)


@task
def build(c: Context, docs: bool = False, dry_run: bool = False):
    """Build sdist and wheel, and optionally build documentation."""
    python_build_cmd = f"{VENV_PYTHON} -m build --no-isolation --outdir dist ."
    docs_build_cmd = f"{VENV_PYTHON} -m mkdocs build -d dist/documentation"
    run_or_display(c, python_build_cmd, dry_run=dry_run)
    if docs:
        if not dry_run:
            rmtree("dist/documentation", ignore_errors=True)
        run_or_display(c, docs_build_cmd, dry_run=dry_run)


@task
def wheelhouse(
    c: Context, clean: bool = False, compress: bool = False, dry_run: bool = False
):
    """Build wheelhouse for the project"""
    wheelhouse_cmd = f"{VENV_PYTHON} -m pip wheel . -w dist/wheelhouse"
    compress_cmd = "tar -czf dist/wheelhouse.tar.gz -C dist wheelhouse"
    if not dry_run:
        Path("dist").mkdir(exist_ok=True)
    if clean and not dry_run:
        rmtree("dist/wheelhouse", ignore_errors=True)
    run_or_display(c, wheelhouse_cmd, dry_run=dry_run)
    if not dry_run:
        rmtree("build", ignore_errors=True)
    if compress:
        run_or_display(c, compress_cmd, dry_run=dry_run)


@task
def docs(c: Context, watch: bool = True, port: int = 8000, dry_run: bool = False):
    """Serve the documentation in development mode."""
    cmd = f"{VENV_PYTHON} -m mkdocs serve -a localhost:{port}"
    if watch:
        cmd += " --livereload --watch docs/ --watch src"
    else:
        cmd += "  --no-livereload"
    run_or_display(c, cmd, dry_run=dry_run)


@task
def test(
    c: Context,
    e2e: bool = False,
    cov: bool = False,
    markers: str = "",
    pattern: str = "",
    dry_run: bool = False,
):
    """Run tests using pytest and optionally enable coverage."""
    cmd = f"{VENV_PYTHON} -m pytest"
    if markers:
        cmd += f" -m {markers}"
    if pattern:
        cmd += f" -p {pattern}"
    if cov:
        cmd += " --cov src/pyhosting"
    if e2e:
        cmd += " tests/"
    else:
        cmd += " tests/unit/"
    run_or_display(c, cmd, dry_run=dry_run)


@task
def coverage(c: Context, run: bool = False, port: int = 8000, dry_run: bool = False):
    """Serve code coverage results and optionally run tests before serving results"""
    if run:
        test(c, True, dry_run=dry_run)
    cmd = f"{VENV_PYTHON} -m http.server {port} --dir coverage-report"
    run_or_display(c, cmd, dry_run)


@task
def check(c: Context, include_tests: bool = False, dry_run: bool = False):
    """Run mypy typechecking."""
    cmd = f"{VENV_PYTHON} -m mypy src/"
    if include_tests:
        cmd += " tests/"
    run_or_display(c, cmd, dry_run=dry_run)


@task
def format(c: Context, check: bool = False, dry_run: bool = False):
    """Format source code using black and isort."""
    opts = " --check" if check else ""
    run_or_display(c, f"{VENV_PYTHON} -m isort .{opts}", dry_run=dry_run)
    run_or_display(c, f"{VENV_PYTHON} -m black .{opts}", dry_run=dry_run)


@task
def lint(c: Context, dry_run: bool = False):
    """Lint source code using flake8."""
    run_or_display(c, f"{VENV_PYTHON} -m flake8 .", dry_run=dry_run)


@task
def docker(
    c: Context,
    platforms: str = "linux/amd64",
    name: str = "pyhosting",
    tag: str = "latest",
    registry: t.Optional[str] = None,
    base_image: t.Optional[str] = None,
    build_image: t.Optional[str] = None,
    push: bool = False,
    load: bool = False,
    output: t.Optional[str] = None,
    provenance: bool = False,
    pip_config: str = "~/.config/pip/pip.conf",
    dry_run: bool = False,
):
    """Build cross-platform docker image for the project"""
    image = f"{name}:{tag}"
    if registry:
        while registry.endswith("/"):
            registry = registry[:-1]
        image = f"{registry}/{image}"
    build_args: t.Dict[str, str] = {}
    if base_image:
        build_args["BASE_IMAGE"] = base_image
    if build_image:
        build_args["BUILD_IMAGE"] = build_image
    # Create an empty pip config if user does not have a pip config yet
    # Use strict permissions since pip config can hold tokens
    pip_configfile = Path(pip_config).expanduser()
    if not pip_configfile.exists():
        if not pip_configfile.parent.exists():
            pip_configfile.parent.mkdir(parents=True, mode=600)
        pip_configfile.touch(mode=600)
    pip_config = pip_configfile.as_posix()
    # buildx command
    cmd = f"docker buildx build --secret id=pip-config,src={pip_config} -t {image} -f Dockerfile"
    if not provenance:
        cmd += " --provenance=false"
    if push:
        cmd += " --push"
    elif load:
        cmd += " --load"
    elif output:
        cmd += f" --output=type=local,dest={output}"
    cmd += f" --platform='{platforms}'"
    for key, value in build_args.items():
        cmd += f" --build-arg {key}={value}"
    cmd += " ."
    run_or_display(c, cmd, dry_run=dry_run)


@task
def pre_push(c: Context):
    """Ensure checks performed in CI will not fail before pushing to remote"""
    format(c, check=True)
    lint(c)
    check(c, include_tests=True)
    test(c, e2e=True, cov=True)

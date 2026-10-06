"""Packaging checks: the project metadata is valid and the package is installed."""
from importlib.metadata import PackageNotFoundError, version

import tomllib

from . import PROJECT_DIR


def test_pyproject():
    """pyproject.toml declares the expected package name and runtime deps."""
    with open(PROJECT_DIR / "pyproject.toml", "rb") as file:
        pyproject = tomllib.load(file)

    assert pyproject["project"]["name"] == "life_expectancy"
    assert any(dep.startswith("pandas") for dep in pyproject["project"]["dependencies"])


def test_package():
    """The life_expectancy package is installed with the declared version."""
    try:
        installed_version = version("life_expectancy")
    except PackageNotFoundError:
        assert False, "life_expectancy is not installed; run `pip install -e .[dev]`."
    assert installed_version == "0.1.0"

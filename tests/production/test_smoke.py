"""Production smoke tests — verify the package is installable and basic functionality works."""

import subprocess
import sys

import pytest


@pytest.fixture(scope="module")
def built_package():
    """Build the wheel and return the result."""
    result = subprocess.run(
        [sys.executable, "-m", "build", "--wheel"],
        capture_output=True,
        text=True,
        cwd=".",
    )
    assert result.returncode == 0, f"Build failed: {result.stderr}"
    return result


def test_wheel_builds(built_package):
    """Verify the package builds without errors."""
    assert built_package.returncode == 0


def test_import_phi_gateway():
    """Verify the package imports correctly."""
    from phi_gateway import __version__

    assert __version__


def test_cli_help():
    """Verify the CLI entry point works."""
    result = subprocess.run(
        [sys.executable, "-m", "phi_gateway", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "phi-gateway" in result.stdout.lower() or "phi_gateway" in result.stdout.lower()


def test_version_consistent():
    """Verify pyproject.toml version matches __init__.py version."""
    import tomllib
    from pathlib import Path

    pyproject = Path("pyproject.toml").read_bytes()
    expected = tomllib.loads(pyproject.decode())["project"]["version"]
    from phi_gateway import __version__

    assert __version__ == expected

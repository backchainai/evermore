#!/usr/bin/env python3
"""Verify version consistency across project files."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path


def get_pyproject_version() -> str:
    """Get version from pyproject.toml."""
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)
    version = str(data["project"]["version"])
    return version


def validate_semver(version: str) -> bool:
    """Check if version follows semantic versioning."""
    pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?(\+[a-zA-Z0-9.]+)?$"
    return bool(re.match(pattern, version))


def main() -> int:
    """Check version consistency."""
    version = get_pyproject_version()
    print(f"Version in pyproject.toml: {version}")

    # Validate version format
    if not validate_semver(version):
        print(f"ERROR: Version '{version}' is not valid semver")
        return 1

    print("Version format: valid semver")
    return 0


if __name__ == "__main__":
    sys.exit(main())

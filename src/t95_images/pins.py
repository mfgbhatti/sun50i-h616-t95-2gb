"""Pinned upstream versions (versions.toml)."""

from __future__ import annotations

import tomllib
from importlib import resources
from pathlib import Path
from typing import Any


def load_pins(path: Path | None = None) -> dict[str, Any]:
    """Load pins from `path`, or from the versions.toml shipped in the package."""
    if path is not None:
        return tomllib.loads(Path(path).read_text(encoding="utf-8"))
    text = resources.files("t95_images").joinpath("versions.toml").read_text(encoding="utf-8")
    return tomllib.loads(text)


def get_pin(pins: dict[str, Any], dotted: str) -> str:
    """Return one pin by dotted key, e.g. ``bootloader.uboot_ref``."""
    node: Any = pins
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            raise KeyError(f"unknown pin: {dotted}")
        node = node[part]
    if isinstance(node, dict):
        raise KeyError(f"pin {dotted} is a table, not a value")
    return str(node)

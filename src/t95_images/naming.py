"""Release asset names, tag checks and release notes."""

from __future__ import annotations

from typing import Any

IMAGES = ("armbian", "libreelec")
BOOTLOADER_VARIANTS = ("egon", "toc0")


def _upstream_token(image: str, pins: dict[str, Any]) -> str:
    ref = pins[image]["ref"]
    if image == "armbian":
        return "armbian" + ref.removeprefix("v")
    return "libreelec-" + ref[:7]


def _kernel(image: str, pins: dict[str, Any]) -> str:
    return pins[image]["kernel_major_minor" if image == "armbian" else "kernel"]


def image_name(image: str, version: str, pins: dict[str, Any], ext: str) -> str:
    if image not in IMAGES:
        raise ValueError(f"unknown image {image!r}; expected one of {IMAGES}")
    token = _upstream_token(image, pins)
    return f"t95-2gb-{image}-{version}-{token}-k{_kernel(image, pins)}.img.{ext}"


def bootloader_name(variant: str, version: str, pins: dict[str, Any]) -> str:
    if variant not in BOOTLOADER_VARIANTS:
        raise ValueError(f"unknown bootloader variant {variant!r}; expected {BOOTLOADER_VARIANTS}")
    b = pins["bootloader"]
    return (
        f"t95-2gb-u-boot-{variant}-{version}"
        f"-uboot{b['uboot_ref'].removeprefix('v')}-tfa{b['tfa_ref']}.bin"
    )


def check_tag(tag: str, version: str) -> None:
    """A release tag must be exactly ``v<project version>``."""
    if tag != f"v{version}":
        raise ValueError(f"tag {tag!r} does not match project version {version!r} (want v{version})")


def release_notes(version: str, pins: dict[str, Any]) -> str:
    a, le, b = pins["armbian"], pins["libreelec"], pins["bootloader"]
    return f"""\
# T95 2GB images {version}

Images for the T95 2GB (Allwinner H616) TV box, built from pinned upstream versions.

| Component | Version |
|---|---|
| Armbian build framework | `{a['ref']}` (kernel {a['kernel_major_minor']}, `{a['release']}`) |
| LibreELEC (built separately, not in this release) | `{le['ref']}` (kernel {le['kernel']}, U-Boot {le['uboot']}, TF-A {le['tfa']}) |
| U-Boot (standalone bootloaders) | `{b['uboot_ref']}` |
| TF-A (standalone bootloaders) | `{b['tfa_ref']}` |

Assets: the `armbian` image with a `.sha256` file, plus two standalone
bootloaders: `egon` (default) and `toc0` (signed with a throwaway key, for units
that do not boot the default one; write it at 8 KiB of the SD card). The
LibreELEC image is not part of this release: it does not build on a free hosted
runner (see the `libreelec` workflow).

Not yet verified on hardware: see "Known limits" in the README.
"""

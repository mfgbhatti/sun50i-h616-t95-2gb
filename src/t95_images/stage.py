"""Copy the board files into checkouts of Armbian, LibreELEC and U-Boot.

Staging fails loudly (StageError) when a checkout does not look like what the
pinned version should contain, so a bad pin is caught before an expensive build.
"""

from __future__ import annotations

import re
from importlib import resources
from pathlib import Path
from typing import Any

from . import patchgen

ASSETS = Path(str(resources.files("t95_images").joinpath("assets")))

DTS = "sun50i-h616-t95-2gb.dts"
DTSI = "sun50i-h616-t95-2gb.dtsi"
DEFCONFIG = "t95_2gb_defconfig"
TOC0_DEFCONFIG = "t95_2gb_toc0_defconfig"
UBOOT_DTS_DIR = "dts/upstream/src/arm64/allwinner"
KERNEL_DTS_DIR = "arch/arm64/boot/dts/allwinner"

UBOOT_HELPER_ENTRY = (
    "      't95-2gb': {\n"
    "        'dtb': 'sun50i-h616-t95-2gb.dtb',\n"
    "        'config': 't95_2gb_defconfig',\n"
    "      },\n"
)
UBOOT_HELPER_ANCHOR = "      'tanix-tx1': {"


class StageError(RuntimeError):
    """The target checkout is not what the pinned version should contain."""


def _read(rel: str) -> str:
    return (ASSETS / rel).read_text(encoding="utf-8")


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _uboot_files() -> dict[str, str]:
    return {
        f"{UBOOT_DTS_DIR}/{DTS}": _read(f"board/{DTS}"),
        f"{UBOOT_DTS_DIR}/{DTSI}": _read(f"board/{DTSI}"),
        f"configs/{DEFCONFIG}": _read(f"board/{DEFCONFIG}"),
    }


def uboot_patch() -> str:
    return patchgen.build_patch(_uboot_files(), subject="sunxi: h616: add T95 2GB board")


def libreelec_kernel_patch() -> str:
    files = {
        f"{KERNEL_DTS_DIR}/{DTS}": _read(f"libreelec/{DTS}"),
        f"{KERNEL_DTS_DIR}/{DTSI}": _read(f"board/{DTSI}"),
    }
    return patchgen.build_patch(
        files,
        subject="arm64: dts: allwinner: h616: add T95 2GB TV box",
        extra_diff=patchgen.KERNEL_MAKEFILE_HUNK,
    )


def export_patches(out: Path) -> list[Path]:
    """Write the independent patches to ``out`` (for manual use or review)."""
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for name, text in (
        ("uboot-add-t95-2gb.patch", uboot_patch()),
        ("libreelec-kernel-add-t95-2gb.patch", libreelec_kernel_patch()),
    ):
        _write(out / name, text)
        written.append(out / name)
    return written


# ---- Armbian ---------------------------------------------------------------

def _armbian_bootpatchdir(root: Path) -> str:
    inc = root / "config/sources/families/include/sunxi64_common.inc"
    if not inc.is_file():
        raise StageError(f"{inc} not found; is this an Armbian build checkout?")
    m = re.search(r'BOOTPATCHDIR="\$\{BOOTPATCHDIR:-"([^"]+)"\}"', inc.read_text(encoding="utf-8"))
    if not m:
        raise StageError(f"BOOTPATCHDIR not found in {inc}; the Armbian pin changed shape")
    return m.group(1)


def stage_armbian(root: Path, pins: dict[str, Any]) -> None:
    root = Path(root)
    if not (root / "compile.sh").is_file():
        raise StageError(f"{root} has no compile.sh; is this an Armbian build checkout?")
    a = pins["armbian"]
    kmm = a["kernel_major_minor"]
    if not (root / f"patch/kernel/archive/sunxi-{kmm}").is_dir():
        raise StageError(f"patch/kernel/archive/sunxi-{kmm} missing; update armbian.kernel_major_minor")
    bootpatchdir = _armbian_bootpatchdir(root)

    up = root / "userpatches"
    _write(up / f"config/boards/{a['board']}.tvb", _read("armbian/t95-2gb.tvb"))
    dt = up / f"kernel/archive/sunxi-{kmm}/dt_64"
    _write(dt / DTS, _read(f"armbian/{DTS}"))
    _write(dt / DTSI, _read(f"board/{DTSI}"))
    _write(up / f"u-boot/{bootpatchdir}/board_{a['board']}/add-t95-2gb.patch", uboot_patch())


# ---- LibreELEC -------------------------------------------------------------

def stage_libreelec(root: Path, pins: dict[str, Any]) -> None:
    root = Path(root)
    dev = root / "projects/Allwinner/devices/H616"
    if not (dev / "options").is_file():
        raise StageError(f"{dev}/options not found; the LibreELEC pin has no H616 device")
    helper = root / "scripts/uboot_helper"
    if not helper.is_file():
        raise StageError(f"{helper} not found")
    text = helper.read_text(encoding="utf-8")
    if "'t95-2gb'" not in text:
        if UBOOT_HELPER_ANCHOR not in text:
            raise StageError(f"anchor {UBOOT_HELPER_ANCHOR.strip()!r} not found in uboot_helper")
        helper.write_text(text.replace(UBOOT_HELPER_ANCHOR, UBOOT_HELPER_ENTRY + UBOOT_HELPER_ANCHOR, 1),
                          encoding="utf-8")
    patches = dev / "patches"
    _write(patches / "linux/0900-arm64-dts-allwinner-h616-add-T95-2GB.patch", libreelec_kernel_patch())
    _write(patches / "u-boot/0900-sunxi-h616-add-T95-2GB.patch", uboot_patch())


# ---- U-Boot (standalone bootloader job) ------------------------------------

def stage_uboot(root: Path) -> None:
    root = Path(root)
    if not (root / "dts/upstream/src/arm64/allwinner").is_dir() or not (root / "configs").is_dir():
        raise StageError(f"{root} does not look like a u-boot checkout (dts/upstream, configs)")
    for rel, content in _uboot_files().items():
        _write(root / rel, content)
    base = _read(f"board/{DEFCONFIG}")
    if not base.endswith("\n"):
        base += "\n"
    _write(root / f"configs/{TOC0_DEFCONFIG}", base + "CONFIG_SPL_IMAGE_TYPE_SUNXI_TOC0=y\n")

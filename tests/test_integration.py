"""Checks against real upstream checkouts. Skipped unless the env vars are set.

    T95_ARMBIAN_DIR     armbian/build at the pinned tag
    T95_LIBREELEC_DIR   LibreELEC.tv at the pinned commit
    T95_UBOOT_DIRS      os.pathsep-separated pristine U-Boot checkouts
    T95_LINUX_DIRS      os.pathsep-separated pristine kernel trees (dts dirs are enough)

Nothing here modifies the given trees: staging happens in a throwaway clone and
patches are only ``git apply --check``-ed.
"""

import os
import subprocess
from pathlib import Path

import pytest

from t95_images import pins, stage

PINS = pins.load_pins()
pytestmark = pytest.mark.integration


def _dirs(var: str) -> list[Path]:
    return [Path(p) for p in os.environ.get(var, "").split(os.pathsep) if p]


def _check(tree: Path, patch_text: str, tmp: Path) -> subprocess.CompletedProcess:
    patch = tmp / "p.patch"
    patch.write_text(patch_text)
    return subprocess.run(["git", "apply", "--check", str(patch)], cwd=tree,
                          capture_output=True, text=True)


@pytest.mark.skipif(not os.environ.get("T95_ARMBIAN_DIR"), reason="T95_ARMBIAN_DIR not set")
def test_real_armbian_staging(tmp_path):
    src = Path(os.environ["T95_ARMBIAN_DIR"])
    clone = tmp_path / "armbian"
    subprocess.run(["git", "clone", "-q", "--local", str(src), str(clone)], check=True)
    stage.stage_armbian(clone, PINS)
    board = clone / "userpatches/config/boards/t95-2gb.tvb"
    assert board.is_file()
    # the family the board names must exist in this Armbian
    assert (clone / "config/sources/families/sun50iw9.conf").is_file()
    # the u-boot patch dir name was read from the real tree
    assert list((clone / "userpatches/u-boot").glob("*/board_t95-2gb/*.patch"))


@pytest.mark.skipif(not os.environ.get("T95_LIBREELEC_DIR"), reason="T95_LIBREELEC_DIR not set")
def test_real_libreelec_staging_and_helper_lookup(tmp_path):
    src = Path(os.environ["T95_LIBREELEC_DIR"])
    clone = tmp_path / "libreelec"
    subprocess.run(["git", "clone", "-q", "--local", str(src), str(clone)], check=True)
    stage.stage_libreelec(clone, PINS)
    for field, want in (("config", "t95_2gb_defconfig"), ("dtb", "sun50i-h616-t95-2gb.dtb")):
        out = subprocess.run(
            ["python3", "-I", "scripts/uboot_helper", "Allwinner", "H616", "t95-2gb", field],
            cwd=clone, capture_output=True, text=True, check=True).stdout.strip()
        assert out == want


@pytest.mark.skipif(not os.environ.get("T95_UBOOT_DIRS"), reason="T95_UBOOT_DIRS not set")
@pytest.mark.parametrize("tree", _dirs("T95_UBOOT_DIRS") or [Path(".")])
def test_uboot_patch_applies_to_real_uboot(tree, tmp_path):
    r = _check(tree, stage.uboot_patch(), tmp_path)
    assert r.returncode == 0, r.stderr


@pytest.mark.skipif(not os.environ.get("T95_LINUX_DIRS"), reason="T95_LINUX_DIRS not set")
@pytest.mark.parametrize("tree", _dirs("T95_LINUX_DIRS") or [Path(".")])
def test_libreelec_kernel_patch_applies_to_real_kernel(tree, tmp_path):
    r = _check(tree, stage.libreelec_kernel_patch(), tmp_path)
    assert r.returncode == 0, r.stderr

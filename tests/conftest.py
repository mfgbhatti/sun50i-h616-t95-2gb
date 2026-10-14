"""Shared fixtures: small fake Armbian and LibreELEC checkouts.

They contain only the files the staging step reads, so unit tests run offline.
The real trees are covered by the integration tests (see test_integration.py).
"""

from pathlib import Path

import pytest

SUNXI64_INC = """\
declare -g ATFBRANCH="tag:lts-v2.12.9"
declare -g BOOTPATCHDIR="${BOOTPATCHDIR:-"v2026.07-sunxi64"}"
declare -g BOOTBRANCH="${BOOTBRANCH:-"tag:v2026.07-rc4"}"
"""

UBOOT_HELPER = """\
devices = {
  'Allwinner': {
    'H616': {
      'orangepi-zero2': {
        'dtb': 'sun50i-h616-orangepi-zero2.dtb',
        'config': 'orangepi_zero2_defconfig',
      },
      'tanix-tx1': {
        'dtb': 'sun50i-h313-tanix-tx1.dtb',
        'config': 'tanix_tx1_defconfig',
      },
    },
  },
}
"""


@pytest.fixture
def armbian_tree(tmp_path: Path) -> Path:
    root = tmp_path / "armbian"
    (root / "patch/kernel/archive/sunxi-6.18").mkdir(parents=True)
    inc = root / "config/sources/families/include"
    inc.mkdir(parents=True)
    (inc / "sunxi64_common.inc").write_text(SUNXI64_INC)
    (root / "compile.sh").write_text("#!/bin/bash\n")
    return root


@pytest.fixture
def libreelec_tree(tmp_path: Path) -> Path:
    root = tmp_path / "libreelec"
    dev = root / "projects/Allwinner/devices/H616"
    dev.mkdir(parents=True)
    (dev / "options").write_text("UBOOT_FIRMWARE=\"atf\"\n")
    (root / "scripts").mkdir()
    (root / "scripts/uboot_helper").write_text(UBOOT_HELPER)
    return root


@pytest.fixture
def uboot_tree(tmp_path: Path) -> Path:
    root = tmp_path / "u-boot"
    (root / "dts/upstream/src/arm64/allwinner").mkdir(parents=True)
    (root / "configs").mkdir()
    return root

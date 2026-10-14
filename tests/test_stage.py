import subprocess
from pathlib import Path

import pytest

from t95_images import pins, stage

PINS = pins.load_pins()
DTS_NAME = "sun50i-h616-t95-2gb.dts"
DTSI_NAME = "sun50i-h616-t95-2gb.dtsi"
UBOOT_DTS_DIR = "dts/upstream/src/arm64/allwinner"


def apply_check(tree: Path, patch: Path) -> subprocess.CompletedProcess:
    subprocess.run(["git", "init", "-q"], cwd=tree, check=True)
    return subprocess.run(["git", "apply", "--check", str(patch)], cwd=tree,
                          capture_output=True, text=True)


# ---- Armbian ---------------------------------------------------------------

def test_stage_armbian_places_board_file_and_dts(armbian_tree):
    stage.stage_armbian(armbian_tree, PINS)
    up = armbian_tree / "userpatches"
    board = (up / "config/boards/t95-2gb.tvb").read_text()
    assert 'BOARDFAMILY="sun50iw9"' in board
    assert 'BOOTCONFIG="t95_2gb_defconfig"' in board
    dt = up / "kernel/archive/sunxi-6.18/dt_64"
    assert (dt / DTS_NAME).is_file() and (dt / DTSI_NAME).is_file()
    # the armbian variant adds HDMI; the shared dtsi must not
    assert "hdmi" in (dt / DTS_NAME).read_text()
    assert "hdmi" not in (dt / DTSI_NAME).read_text()


def test_stage_armbian_uboot_patch_goes_in_bootpatchdir_from_the_tree(armbian_tree):
    stage.stage_armbian(armbian_tree, PINS)
    d = armbian_tree / "userpatches/u-boot/v2026.07-sunxi64/board_t95-2gb"
    patches = list(d.glob("*.patch"))
    assert len(patches) == 1
    # the patch must apply to a pristine U-Boot tree (new files only)
    fresh = armbian_tree.parent / "pristine-uboot"
    fresh.mkdir()
    r = apply_check(fresh, patches[0])
    assert r.returncode == 0, r.stderr
    text = patches[0].read_text()
    assert f"{UBOOT_DTS_DIR}/{DTS_NAME}" in text
    assert "configs/t95_2gb_defconfig" in text


def test_stage_armbian_follows_a_different_bootpatchdir(armbian_tree):
    inc = armbian_tree / "config/sources/families/include/sunxi64_common.inc"
    inc.write_text(inc.read_text().replace("v2026.07-sunxi64", "v2026.10-sunxi64"))
    stage.stage_armbian(armbian_tree, PINS)
    assert (armbian_tree / "userpatches/u-boot/v2026.10-sunxi64/board_t95-2gb").is_dir()


def test_stage_armbian_fails_if_kernel_patch_dir_missing(armbian_tree):
    (armbian_tree / "patch/kernel/archive/sunxi-6.18").rmdir()
    with pytest.raises(stage.StageError, match="sunxi-6.18"):
        stage.stage_armbian(armbian_tree, PINS)


def test_stage_armbian_fails_if_bootpatchdir_not_found(armbian_tree):
    (armbian_tree / "config/sources/families/include/sunxi64_common.inc").write_text("x\n")
    with pytest.raises(stage.StageError, match="BOOTPATCHDIR"):
        stage.stage_armbian(armbian_tree, PINS)


def test_stage_armbian_rejects_non_armbian_dir(tmp_path):
    with pytest.raises(stage.StageError, match="compile.sh"):
        stage.stage_armbian(tmp_path, PINS)


def test_stage_armbian_is_idempotent(armbian_tree):
    stage.stage_armbian(armbian_tree, PINS)
    first = sorted(p.relative_to(armbian_tree) for p in armbian_tree.rglob("*") if p.is_file())
    stage.stage_armbian(armbian_tree, PINS)
    second = sorted(p.relative_to(armbian_tree) for p in armbian_tree.rglob("*") if p.is_file())
    assert first == second


# ---- LibreELEC -------------------------------------------------------------

def test_stage_libreelec_adds_uboot_helper_entry(libreelec_tree):
    stage.stage_libreelec(libreelec_tree, PINS)
    text = (libreelec_tree / "scripts/uboot_helper").read_text()
    assert "'t95-2gb': {" in text
    assert "'dtb': 'sun50i-h616-t95-2gb.dtb'" in text
    assert "'config': 't95_2gb_defconfig'" in text
    ns: dict = {}
    exec(compile(text, "uboot_helper", "exec"), ns)  # still valid python
    assert ns["devices"]["Allwinner"]["H616"]["t95-2gb"]["config"] == "t95_2gb_defconfig"
    assert "tanix-tx1" in ns["devices"]["Allwinner"]["H616"]  # others untouched


def test_stage_libreelec_uboot_helper_edit_is_idempotent(libreelec_tree):
    stage.stage_libreelec(libreelec_tree, PINS)
    once = (libreelec_tree / "scripts/uboot_helper").read_text()
    stage.stage_libreelec(libreelec_tree, PINS)
    assert (libreelec_tree / "scripts/uboot_helper").read_text() == once
    assert once.count("'t95-2gb'") == 1


def test_stage_libreelec_patches(libreelec_tree):
    stage.stage_libreelec(libreelec_tree, PINS)
    pd = libreelec_tree / "projects/Allwinner/devices/H616/patches"
    kernel = list((pd / "linux").glob("*.patch"))
    uboot = list((pd / "u-boot").glob("*.patch"))
    assert len(kernel) == 1 and len(uboot) == 1
    ktext = kernel[0].read_text()
    assert "arch/arm64/boot/dts/allwinner/Makefile" in ktext
    assert "ac200" in ktext  # libreelec variant carries the AC200 Ethernet nodes
    assert "configs/t95_2gb_defconfig" in uboot[0].read_text()


def test_stage_libreelec_fails_if_anchor_missing(libreelec_tree):
    (libreelec_tree / "scripts/uboot_helper").write_text("devices = {}\n")
    with pytest.raises(stage.StageError, match="tanix-tx1"):
        stage.stage_libreelec(libreelec_tree, PINS)


def test_stage_libreelec_rejects_tree_without_h616_device(tmp_path):
    with pytest.raises(stage.StageError, match="H616"):
        stage.stage_libreelec(tmp_path, PINS)


# ---- U-Boot (bootloader job) -----------------------------------------------

def test_stage_uboot_copies_files_and_builds_toc0_defconfig(uboot_tree):
    stage.stage_uboot(uboot_tree)
    d = uboot_tree / UBOOT_DTS_DIR
    assert (d / DTS_NAME).is_file() and (d / DTSI_NAME).is_file()
    base = (uboot_tree / "configs/t95_2gb_defconfig").read_text()
    toc0 = (uboot_tree / "configs/t95_2gb_toc0_defconfig").read_text()
    assert "TOC0" not in base
    assert toc0.startswith(base)
    assert toc0.rstrip().endswith("CONFIG_SPL_IMAGE_TYPE_SUNXI_TOC0=y")


def test_stage_uboot_rejects_non_uboot_dir(tmp_path):
    with pytest.raises(stage.StageError, match="u-boot"):
        stage.stage_uboot(tmp_path)


def test_defconfig_matches_vendor_dram_values():
    """The DRAM block must stay in sync with the vendor [dram_para] we derived it from."""
    cfg = (Path(stage.ASSETS) / "board/t95_2gb_defconfig").read_text()
    for line in (
        "CONFIG_DRAM_CLK=648",
        "CONFIG_DRAM_SUNXI_DX_ODT=0x03030303",
        "CONFIG_DRAM_SUNXI_DX_DRI=0x0e0e0e0e",
        "CONFIG_DRAM_SUNXI_CA_DRI=0x1c1c",
        "CONFIG_DRAM_SUNXI_TPR0=0xc0001305",
        "CONFIG_DRAM_SUNXI_TPR6=0x33808080",
        "CONFIG_DRAM_SUNXI_TPR10=0x2f0006",
        "CONFIG_DRAM_SUNXI_TPR11=0xffffdddd",
        "CONFIG_DRAM_SUNXI_TPR12=0xfedf7657",
        "CONFIG_SUNXI_DRAM_H616_DDR3_1333=y",
        "CONFIG_AXP313_POWER=y",
        "CONFIG_AXP_DCDC3_VOLT=1500",
    ):
        assert line in cfg.splitlines(), line

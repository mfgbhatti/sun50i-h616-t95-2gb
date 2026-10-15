# T95 2GB (Allwinner H616) image builds

Builds **Armbian** and **LibreELEC** images, plus standalone mainline U-Boot
bootloaders, for the T95 2GB H616 TV box. Everything uses mainline Linux and
mainline U-Boot. The vendor BSP files are kept only as reference in
`reference/vendor/`.

This is an overlay repo: it holds the board device tree, the U-Boot defconfig
and the build glue. CI clones pinned upstream Armbian and LibreELEC and stages
the board files into them.

## Status

| Part | State |
|---|---|
| Tests (`uv run pytest`) | pass |
| Bootloaders (U-Boot eGON + signed TOC0, TF-A bl31) | build on GitHub Actions, boot headers checked |
| Armbian image | builds on GitHub Actions (about 65 min, ~360 MB `.img.xz`); the dtb is checked to be in the `linux-dtb` package |
| LibreELEC image | **does not finish on a free hosted runner**: it compiles the whole OS and hits the 6-hour job limit. Build it on a larger or self-hosted runner, or by hand |
| On real hardware | **not booted yet** |

What the Armbian dtb enables: HDMI video (display engine + HDMI, no Mali GPU),
wired Ethernet through the AC300 internal PHY (EMAC1, RMII), SDIO Wi-Fi,
Bluetooth on UART1, SD card, eMMC, USB, IR. The LibreELEC variant uses the
AC200 Ethernet nodes carried by LibreELEC's own kernel patches and also
enables HDMI audio.

Known limits and things to check on the board:

- **Wi-Fi/Bluetooth module varies.** Boxes ship with either an XR819 (2.4 GHz,
  no Bluetooth, out-of-tree `xradio` driver) or an AW859A/BCM4334 (dual band,
  Bluetooth, `brcmfmac`). One dtb covers both; the Bluetooth node simply fails
  to probe on XR819 boxes. The Bluetooth chip needs a `brcm/*.hcd` firmware
  file that has not been checked to be in the image. FM radio is unsupported.
- **HDMI** power comes from the fixed 3.3 V rail; if there is no picture, check
  that rail first. The serial console is on `uart0`.
- **Ethernet** wiring follows Armbian's Tanix TX6S (AC300 internal PHY) and the
  vendor delays (700/3100 ps).
- **DRAM parameters** come from the vendor `sys_config.fex`; if the board does
  not start, try the signed `toc0` bootloader instead of the default `egon`.
- Armbian floats on the current `linux-6.18.y` stable branch. A newer stable
  release can break Armbian's own patches; if the kernel step fails with
  patches that do not apply, bump `armbian.ref` in `versions.toml`.

## Layout

| Path | Purpose |
|---|---|
| `src/t95_images/assets/` | shared board dts/dtsi, per-image dts variants, U-Boot defconfig, Armbian board file |
| `src/t95_images/versions.toml` | pinned upstream versions (Armbian, LibreELEC, U-Boot, TF-A) |
| `src/t95_images/` | `t95` CLI: staging, patch generation, naming, release notes |
| `.github/workflows/build.yml` | CI: test, bootloader, armbian, libreelec, release |
| `reference/vendor/` | original vendor files and old patches (reference only) |

## Releases

Version = `version` in `pyproject.toml`. To release:

1. Bump `version` in `pyproject.toml` (and pins in `versions.toml` if needed),
2. Commit, then `git tag v<version> && git push --tags`.

Run workflow). A tag must equal `v<version>`. The release job publishes only
when every build job succeeded, so while LibreELEC cannot finish on a hosted
runner, run the workflow manually with target `armbian` and fetch the images
from the run's artifacts. Artifacts are kept for one day.

Release assets: Armbian image and LibreELEC image (both with `.sha256`), and
two bootloaders (`egon`, default; `toc0`, signed with a throwaway key, for
units that reject the default).

## Development

```sh
uv sync
uv run pytest                  # unit tests
uv run t95 stage armbian PATH  # stage into a checkout
uv run t95 patches out/        # export the independent patches
```

Integration tests run against real checkouts when `T95_ARMBIAN_DIR`,
`T95_LIBREELEC_DIR`, `T95_UBOOT_DIRS` and `T95_LINUX_DIRS` are set.


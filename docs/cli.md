# `t95` command line

The `t95` tool is the glue used by CI (and by you) to stage the board files into
upstream checkouts, name release files and check release tags. It has no runtime
dependencies. Run it from the repo root:

```sh
uv sync                 # once
uv run t95 --help
uv run t95 <command> --help
```

Errors print `error: ...` on stderr and exit with status 2. Unknown pins,
a bad tag, or an upstream checkout that does not look right (see `stage`) all
fail this way, so a bad pin is caught before an expensive build.

## Commands

### `t95 pin KEY`
Print one pinned upstream value from `src/t95_images/versions.toml`. `KEY` is
dotted, for example `armbian.ref`.

```sh
$ uv run t95 pin armbian.ref
v26.11.0-trunk.91
$ uv run t95 pin libreelec.kernel
7.2.9
```

Available keys: `armbian.{repo,ref,board,branch,release,kernel_major_minor}`,
`libreelec.{repo,ref,kernel,uboot,tfa}`,
`bootloader.{uboot_repo,uboot_ref,tfa_repo,tfa_ref}`. Asking for a table
(`armbian`) or an unknown key is an error.

### `t95 version`
Print the project version (`version` in `pyproject.toml`).

### `t95 stage {armbian,libreelec,uboot} DIR`
Copy the board files into an upstream checkout.

| Target | What it writes | Fails if |
|---|---|---|
| `armbian` | `userpatches/config/boards/t95-2gb.tvb`; the dts + dtsi under `userpatches/kernel/archive/sunxi-<kernel>/dt_64/`; the U-Boot patch under `userpatches/u-boot/<BOOTPATCHDIR>/board_t95-2gb/` (the directory name is read from the checkout) | no `compile.sh`, or the pinned `sunxi-<kernel>` patch dir or `BOOTPATCHDIR` is missing |
| `libreelec` | a `t95-2gb` entry in `scripts/uboot_helper` (added once, safe to re-run); a kernel dts patch and a U-Boot patch in `projects/Allwinner/devices/H616/patches/` | the checkout has no H616 device or the `uboot_helper` anchor is missing |
| `uboot` | board dts/dtsi and `configs/t95_2gb_defconfig` into a U-Boot tree, plus `configs/t95_2gb_toc0_defconfig` (same, with the signed TOC0 image type) | not a U-Boot checkout |

Staging is idempotent: running it twice gives the same tree.

```sh
git clone --depth 1 --branch "$(uv run t95 pin armbian.ref)" "$(uv run t95 pin armbian.repo)" armbian
uv run t95 stage armbian armbian
```

### `t95 patches OUT`
Write the two patches to the directory `OUT` for review or manual use:
`uboot-add-t95-2gb.patch` and `libreelec-kernel-add-t95-2gb.patch`. Each patch
creates new files only (plus one anchored line in the kernel dts Makefile), so
no patch depends on another.

### `t95 name {armbian,libreelec} EXT`
Print the release file name of an image.
`t95-2gb-<image>-<version>-<upstream>-k<kernel>.img.<EXT>`

```sh
$ uv run t95 name armbian xz
t95-2gb-armbian-0.1.0-armbian26.11.0-trunk.91-k6.18.img.xz
```

### `t95 bootloader-name {egon,toc0}`
Print the release file name of a standalone bootloader, for example
`t95-2gb-u-boot-egon-0.1.0-uboot2026.10-tfalts-v2.12.9.bin`.

### `t95 verify-tag TAG`
Succeed only if `TAG` is exactly `v<project version>`. CI runs this on tag pushes.

```sh
$ uv run t95 verify-tag v9.9.9
error: tag 'v9.9.9' does not match project version '0.1.0' (want v0.1.0)
```

### `t95 notes`
Print the release notes (versions of every pinned component) as Markdown. CI
passes this to `gh release create`.

## Where it is used

`.github/workflows/build.yml` calls `pin` to clone the pinned upstreams, `stage`
to add the board files, `name` / `bootloader-name` to name assets, `verify-tag`
on tag pushes and `notes` for the release body. Changing a pin means editing
`versions.toml`; the version comes from `pyproject.toml`.

The code lives in `src/t95_images/` (`cli.py`, `stage.py`, `patchgen.py`,
`naming.py`, `pins.py`) and is covered by `tests/`.

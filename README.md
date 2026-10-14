# T95 2GB (Allwinner H616) image builds

Builds **Armbian** and **LibreELEC** images, plus standalone mainline U-Boot
bootloaders, for the T95 2GB H616 TV box. Everything uses mainline Linux and
mainline U-Boot. The vendor BSP files are kept only as reference in
`reference/vendor/`.

This is an overlay repo: it holds the board device tree, the U-Boot defconfig and
the build glue. CI clones pinned upstream Armbian and LibreELEC and stages the
board files into them.

## Layout

| Path | Purpose |
|---|---|
| `src/t95_images/assets/` | board dts/dtsi (shared), per-image dts variants, U-Boot defconfig, Armbian board file |
| `src/t95_images/versions.toml` | pinned upstream versions (Armbian, LibreELEC, U-Boot, TF-A) |
| `src/t95_images/` | `t95` CLI: staging, patch generation, naming, release notes |
| `.github/workflows/build.yml` | CI: test, bootloader, armbian, libreelec, release |
| `reference/vendor/` | original vendor files and old patches (reference only) |

## Releases

Version = `version` in `pyproject.toml`. To release:

1. Bump `version` in `pyproject.toml` (and pins in `versions.toml` if needed), `uv lock`.
2. Commit, then `git tag v<version> && git push --tags`.

The workflow runs **only on `v*` tags and manually** (Actions tab -> build ->
Run workflow). A tag must equal `v<version>`. Release assets: Armbian image,
LibreELEC image (both with `.sha256`), and two bootloaders (`egon`, default;
`toc0`, signed with a throwaway key, for units that reject the default).

## Development

```sh
uv sync
uv run pytest                  # unit tests
uv run t95 stage armbian PATH  # stage into a checkout
uv run t95 patches out/        # export the independent patches
```

Integration tests run against real checkouts when `T95_ARMBIAN_DIR`,
`T95_LIBREELEC_DIR`, `T95_UBOOT_DIRS`, `T95_LINUX_DIRS` are set.

## Status

Not yet booted on hardware. DRAM parameters, PMIC variant and boot-header type
are derived from the vendor files.

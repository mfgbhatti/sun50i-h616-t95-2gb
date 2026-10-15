# GitHub Actions workflows

| Workflow | File | Runs on | Produces |
|---|---|---|---|
| release | `.github/workflows/release.yml` | `v*` tags and manual runs | tests, standalone bootloaders (`egon`, `toc0`), the Armbian image, and a GitHub Release of those |
| libreelec | `.github/workflows/libreelec.yml` | manual runs only | the LibreELEC image, as an artifact (kept 14 days) |

Neither workflow runs on a push to a branch.

## Why LibreELEC is separate

LibreELEC compiles its whole OS from source. That takes more than the 6-hour job
limit of a free GitHub-hosted runner, so it cannot be part of the release.
Keeping it in its own workflow means it can never block or time out a release.

To build it, run the `libreelec` workflow from the Actions tab and give the
`runner` input the label of a larger or self-hosted runner. Its image is not
attached to the release.

## Releasing

1. Bump `version` in `pyproject.toml` (and pins in `versions.toml` if needed),
   then `uv lock`.
2. Commit, then `git tag v<version> && git push --tags`.

The tag must equal `v<version>`. The release has the Armbian image with its
`.sha256`, and the two bootloaders. Artifacts are kept for one day, so download
them from the run if you need them without a release.

## Building locally

The workflows are the reference: each job's steps are the commands to run, and
the `t95` helpers (see [cli.md](cli.md)) do the pinning and staging. You need
Linux (CI uses Ubuntu 24.04), `git` and `uv`. Install the build dependencies
listed in the matching job, then run its steps from the repo root:

```sh
uv sync --locked
uv run pytest -m "not integration"
```

**LibreELEC** (`libreelec.yml`). This compiles the whole OS: expect hours and a
lot of disk space.

```sh
git init libreelec
git -C libreelec fetch --depth 1 "$(uv run t95 pin libreelec.repo)" "$(uv run t95 pin libreelec.ref)"
git -C libreelec checkout --detach FETCH_HEAD
uv run t95 stage libreelec libreelec
cd libreelec
PROJECT=Allwinner DEVICE=H616 ARCH=aarch64 UBOOT_SYSTEM=t95-2gb make image
```

The image is `libreelec/target/*.img.gz`. `uv run t95 name libreelec gz` prints
the release file name CI gives it.

**Armbian** (`release.yml`, job `armbian`).

```sh
git clone --depth 1 --branch "$(uv run t95 pin armbian.ref)" "$(uv run t95 pin armbian.repo)" armbian
uv run t95 stage armbian armbian
cd armbian
sudo ./compile.sh requirements    # first run only
./compile.sh build BOARD="$(uv run --project .. t95 pin armbian.board)" \
  BRANCH="$(uv run --project .. t95 pin armbian.branch)" \
  RELEASE="$(uv run --project .. t95 pin armbian.release)" \
  KERNEL_CONFIGURE=no BUILD_MINIMAL=yes BUILD_DESKTOP=no \
  COMPRESS_OUTPUTIMAGE=sha,img,xz EXPERT=yes
```

The image is in `armbian/output/images/`.

**Bootloaders** (`release.yml`, job `bootloader`): clone the pinned TF-A and
U-Boot, run `uv run t95 stage uboot u-boot`, build `bl31`, then build U-Boot
with `t95_2gb_defconfig` (eGON) and `t95_2gb_toc0_defconfig` (TOC0).

To apply the board support to your own tree instead, `uv run t95 patches out/`
writes the two patches.

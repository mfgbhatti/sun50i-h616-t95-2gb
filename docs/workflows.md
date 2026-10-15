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

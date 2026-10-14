import hashlib
import subprocess
from pathlib import Path

import pytest

from t95_images import patchgen


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q")
    return tmp_path


def test_new_file_patch_applies_and_reproduces_content(repo):
    files = {"a/b/new.dts": "/dts-v1/;\n/ { };\n", "c/other.txt": "x\n"}
    patch = patchgen.build_patch(files, subject="add files")
    (repo / "p.patch").write_text(patch)
    r = git(repo, "apply", "--check", "p.patch")
    assert r.returncode == 0, r.stderr
    assert git(repo, "apply", "p.patch").returncode == 0
    for name, content in files.items():
        assert (repo / name).read_text() == content


def test_new_file_patch_uses_real_blob_hash(repo):
    content = "hello\n"
    patch = patchgen.build_patch({"f.txt": content}, subject="s")
    blob = hashlib.sha1(b"blob %d\0" % len(content) + content.encode()).hexdigest()
    assert f"index 0000000..{blob[:7]}" in patch


def test_new_file_patch_refuses_to_overwrite_existing_file(repo):
    (repo / "f.txt").write_text("old\n")
    (repo / "p.patch").write_text(patchgen.build_patch({"f.txt": "new\n"}, subject="s"))
    assert git(repo, "apply", "--check", "p.patch").returncode != 0


def test_patch_without_trailing_newline_is_marked(repo):
    patch = patchgen.build_patch({"f.txt": "no newline"}, subject="s")
    assert "\\ No newline at end of file" in patch
    (repo / "p.patch").write_text(patch)
    assert git(repo, "apply", "p.patch").returncode == 0
    assert (repo / "f.txt").read_text() == "no newline"


def test_patch_has_mbox_header_for_armbian(repo):
    patch = patchgen.build_patch({"f.txt": "x\n"}, subject="add f")
    assert patch.startswith("From ")
    assert "Subject: [PATCH] add f" in patch


def test_empty_file_dict_is_an_error():
    with pytest.raises(ValueError):
        patchgen.build_patch({}, subject="s")


MAKEFILE_OLD = """\
dtb-$(CONFIG_ARCH_SUNXI) += sun50i-h616-bigtreetech-pi.dtb
dtb-$(CONFIG_ARCH_SUNXI) += sun50i-h616-orangepi-zero2.dtb
dtb-$(CONFIG_ARCH_SUNXI) += sun50i-h616-x96-mate.dtb
dtb-$(CONFIG_ARCH_SUNXI) += sun50i-h618-longanpi-3h.dtb
"""


def test_kernel_makefile_hunk_applies_with_offset(repo):
    d = repo / "arch/arm64/boot/dts/allwinner"
    d.mkdir(parents=True)
    # leading filler shifts line numbers, as between kernel versions
    (d / "Makefile").write_text("# filler\n" * 9 + MAKEFILE_OLD)
    (repo / "p.patch").write_text(patchgen.kernel_makefile_patch())
    r = git(repo, "apply", "--check", "p.patch")
    assert r.returncode == 0, r.stderr
    git(repo, "apply", "p.patch")
    lines = (d / "Makefile").read_text().splitlines()
    i = lines.index("dtb-$(CONFIG_ARCH_SUNXI) += sun50i-h616-orangepi-zero2.dtb")
    assert lines[i + 1] == "dtb-$(CONFIG_ARCH_SUNXI) += sun50i-h616-t95-2gb.dtb"


def test_kernel_makefile_hunk_fails_loudly_on_unrelated_makefile(repo):
    d = repo / "arch/arm64/boot/dts/allwinner"
    d.mkdir(parents=True)
    (d / "Makefile").write_text("something else\n")
    (repo / "p.patch").write_text(patchgen.kernel_makefile_patch())
    assert git(repo, "apply", "--check", "p.patch").returncode != 0

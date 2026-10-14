"""Generate independent git patches from the board files.

Every patch only creates new files, except the one kernel Makefile line, which is
anchored on two neighbouring lines and tolerates line-number offsets between
kernel versions. No patch depends on another.
"""

from __future__ import annotations

import hashlib

HEADER = """\
From 0000000000000000000000000000000000000000 Mon Sep 17 00:00:00 2001
From: t95-images <t95-images@localhost>
Date: Mon, 1 Jan 2024 00:00:00 +0000
Subject: [PATCH] {subject}

---
"""


def _new_file_diff(path: str, content: str) -> str:
    data = content.encode("utf-8")
    blob = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
    lines = content.split("\n")
    no_newline = not content.endswith("\n")
    if not no_newline:
        lines = lines[:-1]
    body = "".join(f"+{line}\n" for line in lines)
    if no_newline:
        body += "\\ No newline at end of file\n"
    return (
        f"diff --git a/{path} b/{path}\n"
        f"new file mode 100644\n"
        f"index 0000000..{blob[:7]}\n"
        f"--- /dev/null\n"
        f"+++ b/{path}\n"
        f"@@ -0,0 +1,{len(lines)} @@\n"
        f"{body}"
    )


def build_patch(files: dict[str, str], subject: str, extra_diff: str = "") -> str:
    """A single patch that creates every file in ``files`` (path -> content)."""
    if not files:
        raise ValueError("no files to put in the patch")
    diffs = "".join(_new_file_diff(p, c) for p, c in sorted(files.items()))
    return HEADER.format(subject=subject) + diffs + extra_diff


KERNEL_MAKEFILE_HUNK = """\
diff --git a/arch/arm64/boot/dts/allwinner/Makefile b/arch/arm64/boot/dts/allwinner/Makefile
--- a/arch/arm64/boot/dts/allwinner/Makefile
+++ b/arch/arm64/boot/dts/allwinner/Makefile
@@ -47,4 +47,5 @@
 dtb-$(CONFIG_ARCH_SUNXI) += sun50i-h616-bigtreetech-pi.dtb
 dtb-$(CONFIG_ARCH_SUNXI) += sun50i-h616-orangepi-zero2.dtb
+dtb-$(CONFIG_ARCH_SUNXI) += sun50i-h616-t95-2gb.dtb
 dtb-$(CONFIG_ARCH_SUNXI) += sun50i-h616-x96-mate.dtb
 dtb-$(CONFIG_ARCH_SUNXI) += sun50i-h618-longanpi-3h.dtb
"""


def kernel_makefile_patch() -> str:
    """Only the one-line Makefile change (used by tests and by the kernel patch)."""
    return HEADER.format(subject="arm64: dts: allwinner: build the T95 2GB dtb") + KERNEL_MAKEFILE_HUNK

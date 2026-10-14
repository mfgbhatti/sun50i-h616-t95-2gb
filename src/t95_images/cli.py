"""`t95` command line: pins, staging, naming and release helpers for CI."""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Sequence

from . import naming, pins, stage


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="t95", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("pin", help="print one pinned upstream version")
    s.add_argument("key", help="dotted key, e.g. armbian.ref")

    sub.add_parser("version", help="print the project version")

    s = sub.add_parser("stage", help="copy the board files into an upstream checkout")
    s.add_argument("target", choices=["armbian", "libreelec", "uboot"])
    s.add_argument("directory", type=Path)

    s = sub.add_parser("patches", help="export the independent patches to a directory")
    s.add_argument("out", type=Path)

    s = sub.add_parser("name", help="release file name of an image")
    s.add_argument("image", choices=list(naming.IMAGES))
    s.add_argument("ext", help="compression extension, e.g. xz or gz")

    s = sub.add_parser("bootloader-name", help="release file name of a standalone bootloader")
    s.add_argument("variant", choices=list(naming.BOOTLOADER_VARIANTS))

    s = sub.add_parser("verify-tag", help="fail unless the tag is v<project version>")
    s.add_argument("tag")

    sub.add_parser("notes", help="print release notes")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    version = package_version("t95-images")
    try:
        p = pins.load_pins()
        if args.cmd == "pin":
            print(pins.get_pin(p, args.key))
        elif args.cmd == "version":
            print(version)
        elif args.cmd == "stage":
            if args.target == "armbian":
                stage.stage_armbian(args.directory, p)
            elif args.target == "libreelec":
                stage.stage_libreelec(args.directory, p)
            else:
                stage.stage_uboot(args.directory)
            print(f"staged {args.target} into {args.directory}")
        elif args.cmd == "patches":
            for path in stage.export_patches(args.out):
                print(path)
        elif args.cmd == "name":
            print(naming.image_name(args.image, version, p, args.ext))
        elif args.cmd == "bootloader-name":
            print(naming.bootloader_name(args.variant, version, p))
        elif args.cmd == "verify-tag":
            naming.check_tag(args.tag, version)
            print(f"tag {args.tag} matches version {version}")
        elif args.cmd == "notes":
            print(naming.release_notes(version, p))
    except (KeyError, ValueError, stage.StageError) as exc:
        print(f"error: {exc.args[0] if exc.args else exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

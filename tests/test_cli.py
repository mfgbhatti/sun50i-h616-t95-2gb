import pytest

from t95_images import cli


def run(capsys, *argv):
    code = cli.main(list(argv))
    out = capsys.readouterr()
    return code, out.out.strip(), out.err.strip()


def test_pin_prints_value(capsys):
    code, out, _ = run(capsys, "pin", "bootloader.uboot_ref")
    assert code == 0 and out == "v2026.10"


def test_pin_unknown_is_an_error(capsys):
    code, out, err = run(capsys, "pin", "nope.nothing")
    assert code == 2 and out == "" and "unknown pin" in err


def test_version_matches_package_metadata(capsys):
    from importlib.metadata import version

    code, out, _ = run(capsys, "version")
    assert code == 0 and out == version("t95-images")


def test_name_command(capsys):
    code, out, _ = run(capsys, "name", "armbian", "xz")
    assert code == 0
    assert out.startswith("t95-2gb-armbian-") and out.endswith(".img.xz")


def test_bootloader_name_command(capsys):
    code, out, _ = run(capsys, "bootloader-name", "egon")
    assert code == 0 and "-egon-" in out and out.endswith(".bin")


def test_verify_tag_ok_and_mismatch(capsys):
    from importlib.metadata import version

    v = version("t95-images")
    assert run(capsys, "verify-tag", f"v{v}")[0] == 0
    code, _, err = run(capsys, "verify-tag", "v99.0.0")
    assert code == 2 and "does not match" in err


def test_stage_armbian_via_cli(capsys, armbian_tree):
    code, _, err = run(capsys, "stage", "armbian", str(armbian_tree))
    assert code == 0, err
    assert (armbian_tree / "userpatches/config/boards/t95-2gb.tvb").is_file()


def test_stage_error_is_reported_not_raised(capsys, tmp_path):
    code, _, err = run(capsys, "stage", "armbian", str(tmp_path))
    assert code == 2 and "compile.sh" in err


def test_patches_command_exports_independent_patches(capsys, tmp_path):
    code, _, err = run(capsys, "patches", str(tmp_path))
    assert code == 0, err
    names = sorted(p.name for p in tmp_path.glob("*.patch"))
    assert names == [
        "libreelec-kernel-add-t95-2gb.patch",
        "uboot-add-t95-2gb.patch",
    ]


def test_notes_command(capsys):
    code, out, _ = run(capsys, "notes")
    assert code == 0 and "Armbian" in out and "LibreELEC" in out


def test_no_command_shows_help(capsys):
    with pytest.raises(SystemExit):
        cli.main([])

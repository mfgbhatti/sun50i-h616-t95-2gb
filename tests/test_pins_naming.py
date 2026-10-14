import pytest

from t95_images import naming, pins


def test_pins_load_packaged_file():
    p = pins.load_pins()
    assert p["armbian"]["ref"]
    assert p["libreelec"]["ref"]
    assert p["bootloader"]["uboot_ref"].startswith("v")


def test_get_pin_dotted():
    p = {"a": {"b": "c"}}
    assert pins.get_pin(p, "a.b") == "c"


@pytest.mark.parametrize("key", ["a.x", "x", "a.b.c"])
def test_get_pin_unknown_raises(key):
    with pytest.raises(KeyError):
        pins.get_pin({"a": {"b": "c"}}, key)


def test_get_pin_table_is_not_a_value():
    with pytest.raises(KeyError):
        pins.get_pin({"a": {"b": "c"}}, "a")


def test_image_name_armbian():
    p = {"armbian": {"ref": "v26.8.0-trunk.343", "kernel_major_minor": "6.18"}}
    assert (
        naming.image_name("armbian", "0.1.0", p, "xz")
        == "t95-2gb-armbian-0.1.0-armbian26.8.0-trunk.343-k6.18.img.xz"
    )


def test_image_name_libreelec_uses_short_commit():
    p = {"libreelec": {"ref": "273ca84d93e9d5e2c988943752c47ae94b017587", "kernel": "7.2.9"}}
    assert (
        naming.image_name("libreelec", "0.1.0", p, "gz")
        == "t95-2gb-libreelec-0.1.0-libreelec-273ca84-k7.2.9.img.gz"
    )


def test_image_name_rejects_unknown_image():
    with pytest.raises(ValueError):
        naming.image_name("openwrt", "0.1.0", {}, "xz")


def test_bootloader_name():
    p = {"bootloader": {"uboot_ref": "v2026.10", "tfa_ref": "lts-v2.12.9"}}
    assert (
        naming.bootloader_name("toc0", "0.1.0", p)
        == "t95-2gb-u-boot-toc0-0.1.0-uboot2026.10-tfalts-v2.12.9.bin"
    )


def test_bootloader_name_rejects_unknown_variant():
    p = {"bootloader": {"uboot_ref": "v2026.10", "tfa_ref": "lts-v2.12.9"}}
    with pytest.raises(ValueError):
        naming.bootloader_name("weird", "0.1.0", p)


def test_check_tag_accepts_matching_version():
    naming.check_tag("v0.1.0", "0.1.0")


@pytest.mark.parametrize("tag", ["0.1.0", "v0.1.1", "v0.1", "vv0.1.0", ""])
def test_check_tag_rejects_mismatch(tag):
    with pytest.raises(ValueError):
        naming.check_tag(tag, "0.1.0")


def test_release_notes_lists_every_pin():
    p = pins.load_pins()
    notes = naming.release_notes("0.1.0", p)
    for needle in (p["armbian"]["ref"], p["libreelec"]["ref"],
                   p["bootloader"]["uboot_ref"], p["bootloader"]["tfa_ref"]):
        assert needle in notes
    assert "0.1.0" in notes

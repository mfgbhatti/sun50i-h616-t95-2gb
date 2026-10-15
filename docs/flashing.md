# Flashing to an SD card

None of these images has been tested on the board yet. Treat the first boot as
an experiment, and keep the original Android firmware on the box's eMMC (do not
flash anything to the eMMC).

**Double-check the target device before every `dd`.** Writing to the wrong disk
destroys its data. Below, `/dev/sdX` is your SD card, never a partition
(`/dev/sdX`, not `/dev/sdX1`).

## 1. Download and verify

Get the image and its `.sha256` from the release (or from the workflow run's
artifacts, which are kept for one day), then check it:

```sh
sha256sum -c t95-2gb-armbian-*.img.xz.sha256
```

## 2. Write the Armbian image

The Armbian image already contains the T95 bootloader (U-Boot with this board's
DRAM settings, written at 8 KiB of the card), so for a normal first boot you
only need this step.

**Linux**

```sh
lsblk                                   # find the SD card, e.g. /dev/sdb
xz -dc t95-2gb-armbian-*.img.xz | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync
sync
```

**macOS**

```sh
diskutil list                           # find the card, e.g. /dev/disk4
diskutil unmountDisk /dev/diskN
xz -dc t95-2gb-armbian-*.img.xz | sudo dd of=/dev/rdiskN bs=4m
diskutil eject /dev/diskN
```

**Windows (or any OS):** write the `.img.xz` file with balenaEtcher or Raspberry
Pi Imager ("Use custom"). Both can read `.xz` directly.

## 3. Boot

1. Insert the card in the box with the power off.
2. Connect HDMI and Ethernet, then power on.
3. Allwinner chips try the SD card first, so it should boot from the card. If
   the box starts Android instead, the card was not accepted as bootable: re-write
   it, try another card, or try the `toc0` bootloader (below).
4. First login on Armbian: log in as `root` with password `1234`; it then makes
   you set a new password and create a user.

If nothing appears on HDMI, connect a 3.3 V USB-serial adapter to the board's
`uart0` pads (115200 baud, 8N1) and keep the log. See the README for what to
check next.

## 4. Writing a standalone bootloader (only if you need to)

The release also has two standalone bootloaders:

| File | When to use |
|---|---|
| `t95-2gb-u-boot-egon-*.bin` | default; the same kind of boot header the image uses |
| `t95-2gb-u-boot-toc0-*.bin` | signed (throwaway key) variant; try it if the `egon` one does not boot |

They replace only the bootloader, at 8 KiB of the card, and leave the partitions
alone. Write one onto a card that already has the Armbian image (or onto a blank
card to test only the bootloader):

```sh
sudo dd if=t95-2gb-u-boot-egon-*.bin of=/dev/sdX bs=1k seek=8 conv=fsync,notrunc
sync
```

- `seek=8` with `bs=1k` is the 8 KiB offset; `notrunc` keeps the rest of the card.
- Run it **after** writing the image, since writing the image overwrites the
  area.
- To go back, write the Armbian image again.

## LibreELEC

LibreELEC images are written the same way. They are `.img.gz`, so use
`gzip -dc image.img.gz | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync`.
CI does not currently build this image (see the README), so you need one built
elsewhere.

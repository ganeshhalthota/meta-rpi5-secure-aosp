"""
Utility: Disk image builder.

Handles low-level disk image construction:
  - allocating the image file
  - creating a partition table:
      GPT → sgdisk  (supports explicit partition numbers natively)
      MBR → fdisk   (interactive commands piped to stdin; supports
                     extended/logical partitions automatically)
  - loop-mounting via losetup + kpartx
  - copying partition images with dd
  - creating empty filesystems (ext4, fat32)
  - copying extra files into mounted partitions
  - cleanup and optional zip compression

YAML partition fields
---------------------
  name             : partition label
  partition_number : (optional) explicit partition number; defaults to
                     sequential position in the list.  For GPT, sgdisk
                     places the partition at exactly that slot.  For MBR,
                     gaps are auto-filled with 1 MiB type-0 empty entries.
  size             : size in MiB (omit or leave empty → fill remaining space)
  format           : fat32 | ext4 | ext3 | ext2 | raw
  flags            : boot  (GPT → EFI System Partition type ef00;
                            MBR → bootable flag)
  img              : path to a pre-built image to dd into the partition
  extra_files      : list of {src, dst} or {content, src} entries
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import time
from datetime import datetime


class DiskImage:
    def __init__(self, image_data: dict):
        self._validate(image_data)
        self._image_data = image_data
        date_time = datetime.now().strftime("%Y%m%d%H%M")
        variant = image_data.get("build_variant", "unknown")
        img_name = f"{image_data['image_name']}-{variant}-{date_time}.img"
        self._img_path = os.path.join(image_data["output_dir"], img_name)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self) -> str:
        """Build the disk image and return its path."""
        self._create_image_file()
        self._create_partitions()
        loopdev = self._map_loop_device()

        try:
            sequential_number = 1
            for partition_info in self._image_data["partitions"]:
                part_name = partition_info["name"]
                # Use explicit partition_number when provided, else sequential.
                partition_number = partition_info.get("partition_number", sequential_number)
                partition_dev    = f"p{partition_number}"

                if "img" in partition_info and partition_info["img"]:
                    self._copy_partition(loopdev, partition_dev, partition_info["img"])
                elif partition_info["format"] in ("ext4", "ext3", "ext2"):
                    self._create_filesystem(loopdev, partition_dev, part_name)
                    if "selinux_context" in partition_info:
                        if ("e2fsdroid" in self._image_data
                                and "selinux_file_contexts" in self._image_data):
                            self._apply_selinux_context_e2fsdroid(
                                loopdev, partition_number, part_name,
                                self._image_data["e2fsdroid"],
                                self._image_data["selinux_file_contexts"],
                            )
                        else:
                            self._apply_selinux_root_context(
                                loopdev, partition_number, partition_info["selinux_context"]
                            )
                elif partition_info["format"] == "fat32":
                    self._run_cmd([
                        "sudo", "mkfs.vfat", "-F", "32",
                        "-n", part_name.upper(),
                        f"/dev/mapper/{loopdev}{partition_dev}",
                    ])

                if "extra_files" in partition_info and partition_info["extra_files"]:
                    self._copy_extra_files(loopdev, partition_number, partition_info["extra_files"])

                sequential_number += 1

        except Exception as e:
            print(f"Error during image building: {e}")
            print("Attempting cleanup...")
            self._cleanup(loopdev)
            raise

        self._cleanup(loopdev)

        return self._img_path

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate(image_data: dict) -> None:
        required = ("image_name", "output_dir", "partition_scheme", "sdcard_size", "partitions")
        for key in required:
            if key not in image_data:
                raise ValueError(f"DiskImage: required key '{key}' missing from image_data")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_cmd(self, cmd: list) -> None:
        print(f"Running: {' '.join(str(c) for c in cmd)}")
        subprocess.run(cmd, check=True)

    def _create_image_file(self) -> None:
        if os.path.exists(self._img_path):
            raise FileExistsError(f"{self._img_path} already exists!")
        print(f"Creating image file {self._img_path}...")
        img_size_bytes = int(self._image_data["sdcard_size"]) * 1024 * 1024
        self._run_cmd(["sudo", "fallocate", "-l", str(img_size_bytes), self._img_path])
        self._run_cmd(["sync"])

    # ------------------------------------------------------------------
    # Partition-table creation — dispatcher
    # ------------------------------------------------------------------

    def _create_partitions(self) -> None:
        scheme = self._image_data["partition_scheme"].lower()
        if scheme == "gpt":
            self._create_partitions_gpt()
        else:
            self._create_partitions_mbr()

    # ------------------------------------------------------------------
    # GPT via sgdisk
    # ------------------------------------------------------------------

    def _create_partitions_gpt(self) -> None:
        """Create GPT partitions using sgdisk.

        sgdisk natively supports explicit partition numbers, so no
        gap-filling is required.  Each partition is added with:

            sgdisk -n <num>:0:+<size>M  -c <num>:<name>  <img>

        The start-sector argument ``0`` tells sgdisk to use the next
        available aligned sector automatically.
        """
        print("Creating GPT partition table using sgdisk...")

        # Wipe any existing partition data and create a fresh empty GPT.
        self._run_cmd(["sudo", "sgdisk", "-o", self._img_path])

        sequential_number = 1
        for partition_info in self._image_data["partitions"]:
            part_name  = partition_info["name"]
            part_num   = partition_info.get("partition_number", sequential_number)

            # Size argument: "+<N>M" for a fixed size, "0" to fill the rest.
            if partition_info.get("size"):
                size_arg = f"+{partition_info['size']}M"
            else:
                size_arg = "0"

            print(f"  Creating GPT partition {part_num}: {part_name}  size={size_arg}")
            self._run_cmd([
                "sudo", "sgdisk",
                "-n", f"{part_num}:0:{size_arg}",
                "-c", f"{part_num}:{part_name}",
                self._img_path,
            ])

            if partition_info.get("flags") == "boot":
                # ef00 = EFI System Partition — the GPT equivalent of the
                # MBR bootable flag, required by the RPi firmware.
                self._run_cmd([
                    "sudo", "sgdisk",
                    "-t", f"{part_num}:ef00",
                    self._img_path,
                ])

            sequential_number += 1

    # ------------------------------------------------------------------
    # MBR via fdisk
    # ------------------------------------------------------------------

    def _create_partitions_mbr(self) -> None:
        """Create MBR partitions using fdisk.

        Supports both pure-primary and extended/logical layouts:

        - If any partition has ``partition_number`` >= 5, an extended
          partition is automatically inserted at the lowest available
          primary slot (1–4).
        - Extended partition size = sum of all logical partition sizes
          + 4 MiB overhead (matching the mkimg.sh formula).
        - Logical partitions are created in ascending order of partition
          number; fdisk assigns them numbers 5, 6, 7 … automatically.
        - Primary partitions other than p1 and the extended slot are
          created last so that a "fill remaining" partition (no ``size``
          field) works correctly.

        fdisk creation order
        --------------------
        1. p1  (if defined)
        2. extended partition  (auto-inserted when logical partitions exist)
        3. logical partitions p5, p6, p7 … in ascending order
        4. remaining primary partitions p2, p3, p4 … in ascending order
           (excluding p1 and the extended slot)
        """
        print("Creating MBR partition table using fdisk...")

        # ---------------------------------------------------------------- #
        # Build partition-number → info mapping                            #
        # ---------------------------------------------------------------- #
        partitions_by_num: dict[int, dict] = {}
        sequential_number = 1
        for partition_info in self._image_data["partitions"]:
            part_num = partition_info.get("partition_number", sequential_number)
            partitions_by_num[part_num] = partition_info
            sequential_number += 1

        logical_nums = sorted(k for k in partitions_by_num if k >= 5)
        primary_nums = sorted(k for k in partitions_by_num if k <= 4)

        # ---------------------------------------------------------------- #
        # Find a free primary slot for the extended partition (if needed)  #
        # ---------------------------------------------------------------- #
        extended_num: int | None = None
        if logical_nums:
            for candidate in range(1, 5):
                if candidate not in partitions_by_num:
                    extended_num = candidate
                    break
            if extended_num is None:
                raise ValueError(
                    "MBR: all four primary slots (1–4) are occupied; "
                    "no room for the extended partition required by "
                    f"logical partitions {logical_nums}."
                )

        # ---------------------------------------------------------------- #
        # Calculate extended partition size                                #
        # sum of logical sizes + 4 MiB overhead (matches mkimg.sh)        #
        # ---------------------------------------------------------------- #
        extended_size_mib = 0
        if extended_num is not None:
            for num in logical_nums:
                pi = partitions_by_num[num]
                if pi.get("size"):
                    extended_size_mib += int(pi["size"])
            extended_size_mib += 4  # overhead buffer (matches mkimg.sh: +4M)

        # ---------------------------------------------------------------- #
        # Build fdisk command sequence                                     #
        # ---------------------------------------------------------------- #
        cmds: list[str] = ["o"]  # new empty DOS partition table

        # 1. p1
        if 1 in partitions_by_num:
            p1 = partitions_by_num[1]
            size_arg = f"+{p1['size']}M" if p1.get("size") else ""
            cmds += ["n", "p", "1", "", size_arg]

        # 2. Extended partition (auto-inserted)
        if extended_num is not None:
            cmds += ["n", "e", str(extended_num), "", f"+{extended_size_mib}M"]

        # 3. Logical partitions (p5+) in ascending order.
        #    fdisk assigns numbers 5, 6, 7 … automatically.
        for num in logical_nums:
            pi = partitions_by_num[num]
            size_arg = f"+{pi['size']}M" if pi.get("size") else ""
            cmds += ["n", "l", "", size_arg]

        # 4. Remaining primary partitions (skip p1 and the extended slot)
        for num in sorted(primary_nums):
            if num == 1:
                continue
            pi = partitions_by_num[num]
            size_arg = f"+{pi['size']}M" if pi.get("size") else ""
            cmds += ["n", "p", str(num), "", size_arg]

        # Set non-default partition types
        for num in sorted(partitions_by_num.keys()):
            pi = partitions_by_num[num]
            if pi.get("format") == "fat32":
                cmds += ["t", str(num), "c"]  # W95 FAT32 LBA

        # Set bootable flags
        for num in sorted(partitions_by_num.keys()):
            pi = partitions_by_num[num]
            if pi.get("flags") == "boot":
                cmds += ["a", str(num)]

        # Write partition table
        cmds.append("w")

        fdisk_input = "\n".join(cmds) + "\n"
        print(f"fdisk input:\n{fdisk_input}")
        subprocess.run(
            ["sudo", "fdisk", self._img_path],
            input=fdisk_input,
            text=True,
            check=True,
        )
        self._run_cmd(["sync"])

    # ------------------------------------------------------------------
    # MBR type-code helper
    # ------------------------------------------------------------------

    @staticmethod
    def _mbr_type_code(fs_type: str) -> str:
        """Return the MBR partition type hex code for a given filesystem."""
        mapping = {
            "fat32": "b",   # W95 FAT32
            "fat16": "e",   # W95 FAT16 (LBA)
            "ext4":  "83",  # Linux filesystem
            "ext3":  "83",
            "ext2":  "83",
            "raw":   "83",  # Linux (generic fallback)
            "swap":  "82",  # Linux swap
        }
        return mapping.get(fs_type.lower(), "83")

    # ------------------------------------------------------------------
    # Loop-device management
    # ------------------------------------------------------------------

    def _map_loop_device(self) -> str:
        print("Mapping loop device...")

        # 1. Proactively ensure basic loop nodes 0-7 exist in /dev.
        #    In some Docker containers, these nodes may be missing even if
        #    the kernel supports loop devices.
        for i in range(8):
            node = f"/dev/loop{i}"
            if not os.path.exists(node):
                # Major number 7 is for loop devices. Minor is the index.
                # We use sudo as we are in a privileged container or on host.
                try:
                    subprocess.run(["sudo", "mknod", node, "b", "7", str(i)],
                                   capture_output=True, check=False)
                except Exception:
                    pass

        # 2. Use 'losetup --find --show' for atomic allocation.
        #    We use a retry loop to handle transient "No such file or directory"
        #    errors, which usually mean a device node was just deleted or
        #    not yet fully created in the /dev devtmpfs.
        loopdev_path = None
        for attempt in range(1, 4):
            try:
                # --find: first free loop device
                # --show: print its name
                result = subprocess.run(
                    ["sudo", "losetup", "--find", "--show", self._img_path],
                    capture_output=True, text=True, check=True
                )
                loopdev_path = result.stdout.strip()
                if not loopdev_path:
                    raise RuntimeError("losetup returned empty output")
                break
            except subprocess.CalledProcessError as e:
                print(f"  losetup failed (attempt {attempt}/3): {e.stderr or e}")
                if attempt == 3:
                    raise
                time.sleep(1)

        print(f"  Attached {self._img_path} to {loopdev_path}")

        # 3. Map partitions with kpartx.
        #    Sometimes there's a race between loop attachment and partition mapping.
        #    Using -av (add verbose) or a small delay helps.
        print("  Mapping partitions with kpartx...")
        # Add a tiny settling delay for the kernel to see the new loop device.
        time.sleep(0.5)
        result = subprocess.run(
            ["sudo", "kpartx", "-av", loopdev_path],
            capture_output=True, text=True, check=True
        )
        print(f"  kpartx output:\n{result.stdout}")

        mapper_name = os.path.basename(loopdev_path)
        print(f"  Partitions mapped as /dev/mapper/{mapper_name}pX")
        return mapper_name

    def _copy_partition(self, loopdev: str, partition: str, src_img) -> None:
        print(f"Copying {src_img} to {partition}...")
        if not os.path.exists(src_img):
            raise FileNotFoundError(f"Source image not found: {src_img}")
        src_size = os.path.getsize(src_img)
        print(f"  Source image size: {src_size / (1024 * 1024):.2f} MiB")
        self._run_cmd([
            "sudo", "dd",
            f"if={src_img}",
            f"of=/dev/mapper/{loopdev}{partition}",
            "bs=1M", "conv=notrunc",
        ])

    def _copy_extra_files(self, loopdev: str, partition_number: int, extra_files: list) -> None:
        print(f"Copying extra files to partition {partition_number}...")
        mount_point = tempfile.mkdtemp()
        print(f"  Created temporary mount point: {mount_point}")
        try:
            self._run_cmd(["sudo", "mount", f"/dev/mapper/{loopdev}p{partition_number}", mount_point])
            for file_info in extra_files:
                if "src" in file_info:
                    if not os.path.exists(file_info["src"]):
                        raise FileNotFoundError(
                            f"extra_file src not found: {file_info['src']} "
                            f"(required for dst: {file_info['dst']})"
                        )
                    dst_path = os.path.join(mount_point, file_info["dst"])
                    print(f"  Copying {file_info['src']} to {dst_path}")
                    self._run_cmd(["sudo", "cp", file_info["src"], dst_path])
                elif "content" in file_info:
                    dst_path = os.path.join(mount_point, file_info["src"])
                    print(f"  Creating file {dst_path}")
                    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
                        tmp.write(file_info["content"])
                        tmp_path = tmp.name
                    self._run_cmd(["sudo", "cp", tmp_path, dst_path])
                    os.unlink(tmp_path)
            self._run_cmd(["sudo", "sync"])
        finally:
            self._run_cmd(["sudo", "umount", mount_point])
            os.rmdir(mount_point)
            print("  Removed temporary mount point")

    def _create_filesystem(self, loopdev: str, partition: str, label: str) -> None:
        print(f"Creating filesystem on {partition} with label {label}...")
        self._run_cmd(["sudo", "mkfs.ext4", f"/dev/mapper/{loopdev}{partition}", "-I", "512", "-L", label])

    def _apply_selinux_context_e2fsdroid(
        self, loopdev: str, partition_number: int, part_name: str,
        e2fsdroid_bin: str, file_contexts: str
    ) -> None:
        partition_device = f"/dev/mapper/{loopdev}p{partition_number}"
        mount_point_path = f"/{part_name}"
        print(f"Applying SELinux context via e2fsdroid to p{partition_number} ({mount_point_path})...")

        # Without -e, e2fsdroid uses sparse_io_manager which expects Android sparse
        # image format and fails with EINVAL on plain ext4 from mkfs.ext4. The -e flag
        # switches to unix_io_manager for regular ext4 images.
        # Shadow-copy through a plain file because sparse_io_manager also fails on
        # /dev/mapper block devices.
        with tempfile.NamedTemporaryFile(suffix=f"_{part_name}.img", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            self._run_cmd(["sudo", "dd", f"if={partition_device}", f"of={tmp_path}", "bs=1M"])
            # -e: use unix_io_manager (regular ext4); default is sparse_io_manager
            # which only opens Android sparse images and fails (EINVAL) on plain ext4.
            self._run_cmd([
                "sudo", e2fsdroid_bin,
                "-e",
                "-S", file_contexts,
                "-a", mount_point_path,
                tmp_path,
            ])
            self._run_cmd(["sudo", "dd", f"if={tmp_path}", f"of={partition_device}", "bs=1M", "conv=notrunc"])
            print(f"  e2fsdroid SELinux context applied for {mount_point_path}")
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _apply_selinux_root_context(self, loopdev: str, partition_number: int, context: str) -> None:
        print(f"Applying SELinux root context '{context}' to partition p{partition_number}...")
        mount_point = tempfile.mkdtemp()
        try:
            self._run_cmd(["sudo", "mount", f"/dev/mapper/{loopdev}p{partition_number}", mount_point])
            # Set null-terminated security.selinux xattr on the root inode so
            # Android's first-stage vold can access the partition before any
            # restorecon runs in second-stage init.
            value = (context + "\x00").encode("ascii")
            subprocess.run(
                ["sudo", "python3", "-c",
                 f"import os; os.setxattr({mount_point!r}, b'security.selinux', {value!r})"],
                check=True,
            )
            print(f"  SELinux context set: {context}")
        finally:
            try:
                subprocess.run(["sudo", "umount", mount_point], check=False)
            except Exception:
                pass
            try:
                os.rmdir(mount_point)
            except OSError:
                pass

    def _cleanup(self, loopdev: str) -> None:
        print("Cleaning up loop device...")
        self._run_cmd(["sudo", "kpartx", "-d", f"/dev/{loopdev}"])
        self._run_cmd(["sudo", "losetup", "-d", f"/dev/{loopdev}"])

        print(f"  Changing ownership of {self._img_path}...")
        import pwd
        try:
            username = os.getenv("SUDO_USER") or os.getenv("USER")
            if not username:
                username = pwd.getpwuid(os.getuid()).pw_name
            if username and username != "root":
                self._run_cmd(["sudo", "chown", f"{username}:{username}", self._img_path])
                print(f"  Changed ownership to {username}:{username}")
            else:
                print("  Skipping ownership change (running as root or user not detected)")
        except Exception as e:
            print(f"  Warning: Could not change ownership: {e}")

        print("  Cleanup completed successfully!")

    def compress_tar_gz_split(self, split_size: int = 2 * 1024 ** 3) -> list:
        """
        Compress the image into a gzip-compressed tar archive and split it
        into chunks of *split_size* bytes (default: 2 GiB).

        Split files are named  <image>.img.tar.gz.aa, .ab, .ac, …

        To reassemble on the target machine::

            cat <image>.img.tar.gz.* | tar -xzf -

        Returns a sorted list of the created part-file paths.
        """
        import glob

        img_dir  = os.path.dirname(self._img_path)
        img_name = os.path.basename(self._img_path)
        prefix   = self._img_path + ".tar.gz."

        split_gb = split_size / (1024 ** 3)
        print(f"Compressing {img_name} to tar.gz split by {split_gb:.2f} GiB ...")
        cmd = (
            f"tar -czf - -C {img_dir} {img_name}"
            f" | split -b {split_size} - {prefix}"
        )
        subprocess.run(cmd, shell=True, check=True)

        parts = sorted(glob.glob(prefix + "*"))
        print(f"Created {len(parts)} archive part(s):")
        for p in parts:
            size_mb = os.path.getsize(p) / (1024 * 1024)
            print(f"  {p}  ({size_mb:.1f} MiB)")
        return parts

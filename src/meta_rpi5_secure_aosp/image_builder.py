
import os
import subprocess
from datetime import datetime

class ImageBuilder:
    def __init__(self, image_data: dict):
        self.validate(image_data)
        self._image_data = image_data
        date_time = datetime.now().strftime("%Y%m%d%H%M")
        img_name = f"{image_data['image_name']}-{date_time}.img"
        self._img_path = os.path.join(image_data['output_dir'], img_name)

    def validate(self, image_data: dict):
        if 'image_name' not in image_data:
            raise Exception("image_name is not specified")
        if 'output_dir' not in image_data:
            raise Exception("output_dir is not specified")
        if 'partition_scheme' not in image_data:
            raise Exception("partition_scheme is not specified")
        if 'sdcard_size' not in image_data:
            raise Exception("sdcard_size is not specified")
        if 'partitions' not in image_data:
            raise Exception("partitions is not specified")

    def run_cmd(self, cmd):
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

    def create_image_file(self):
        if os.path.exists(self._img_path):
            raise FileExistsError(f"{self._img_path} already exists!")
        print(f"Creating image file {self._img_path}...")
        img_size_bytes = int(self._image_data['sdcard_size']) * 1024 * 1024
        self.run_cmd(["sudo", "fallocate", "-l", str(img_size_bytes), self._img_path])
        self.run_cmd(["sync"])

    def create_partitions(self):
        print("Creating partitions using parted...")
        # Create partition table
        self.run_cmd(["sudo", "parted", "--script", self._img_path, "mklabel", self._image_data['partition_scheme']])

        partition_number = 1
        partition_start = 1
        for partition_info in self._image_data['partitions']:
            part_name = partition_info['name']
            part_format = partition_info['format']
            if 'size' in partition_info:
                part_size = partition_info['size']
            else:
                part_size = int(self._image_data['sdcard_size']) - partition_start

            self.add_partition(name=part_name,
                               fs_type=part_format,
                               start=partition_start,
                               end=part_size,
                               partition_number=partition_number)

            # increment for partition number
            partition_number += 1
            # Compute the start of next partition
            partition_start += part_size

        # Boot partition
        self.add_partition("primary", "fat32", "1MiB", f"{self.boot_size+1}MiB")

        # Extended partition
        start_ext = self.boot_size + 1
        end_ext = start_ext + self.extended_size
        self.add_partition("extended", "", f"{start_ext}MiB", f"{end_ext}MiB")

        # Logical partitions inside extended
        current_start = start_ext
        self.add_partition("logical", "ext4", f"{current_start}MiB", f"{current_start+self.system_size}MiB")
        current_start += self.system_size
        self.add_partition("logical", "ext4", f"{current_start}MiB", f"{current_start+self.vendor_size}MiB")
        current_start += self.vendor_size
        self.add_partition("logical", "ext4", f"{current_start}MiB", f"{current_start+self.metadata_size}MiB")

        # Userdata partition (primary)
        self.add_partition("primary", "ext4", f"{end_ext}MiB", "100%")

    def add_partition(self, name, fs_type, start, end, partition_number):
        # Create partition
        cmd = ["sudo", "parted", "--script", self._img_path, "mkpart", name, fs_type, start, end]
        self.run_cmd(cmd)
        # Assign name explicitly (important for AVB)
        self.run_cmd(["sudo", "parted", "--script", self._img_path, "name", partition_number, name])

    def map_loop_device(self):
        print("Mapping loop device...")
        result = subprocess.run(["sudo", "kpartx", "-av", self._img_path], capture_output=True, text=True, check=True)
        loopdev = None
        for line in result.stdout.splitlines():
            if "add map" in line:
                loopdev = line.split()[-1].replace("p1", "")
                break
        if not loopdev:
            raise RuntimeError("Unable to find loop device!")
        print(f"Image mounted as /dev/{loopdev}")
        return loopdev

    def copy_partition(self, loopdev, partition, src_img):
        print(f"Copying {src_img} to {partition}...")
        self.run_cmd(["sudo", "dd", f"if={src_img}", f"of=/dev/mapper/{loopdev}{partition}", "bs=1M"])

    def create_filesystem(self, loopdev, partition, label):
        print(f"Creating filesystem on {partition} with label {label}...")
        self.run_cmd(["sudo", "mkfs.ext4", f"/dev/mapper/{loopdev}{partition}", "-I", "512", "-L", label])

    def cleanup(self, loopdev):
        print("Cleaning up loop device...")
        self.run_cmd(["sudo", "kpartx", "-d", f"/dev/{loopdev}"])
        self.run_cmd(["sudo", "losetup", "-d", f"/dev/{loopdev}"])
        self.run_cmd(["sudo", "chown", f"{os.getenv('USER')}:{os.getenv('USER')}", self._img_path])

    def build_image(self):
        self.create_image_file()
        self.create_partitions()
        loopdev = self.map_loop_device()
        self.copy_partition(loopdev, "p1", os.path.join(self.output_dir, "boot.img"))
        self.copy_partition(loopdev, "p5", os.path.join(self.output_dir, "system.img"))
        self.copy_partition(loopdev, "p6", os.path.join(self.output_dir, "vendor.img"))
        self.create_filesystem(loopdev, "p7", "metadata")
        self.create_filesystem(loopdev, "p3", "userdata")
        self.cleanup(loopdev)

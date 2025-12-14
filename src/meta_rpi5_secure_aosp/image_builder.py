
import os
import subprocess
from datetime import datetime

class ImageBuilder:
    def __init__(self, version, target_product, output_dir):
        self.version = version
        self.date = datetime.now().strftime("%Y%m%d")
        self.target = target_product.replace("aosp_", "")
        self.img_name = f"{self.version}-{self.date}-{self.target}.img"
        self.img_path = os.path.join(output_dir, self.img_name)
        self.output_dir = output_dir

        # Partition sizes in MiB
        self.boot_size = 128
        self.system_size = 3072
        self.vendor_size = 384
        self.metadata_size = 16
        self.extended_size = self.system_size + self.vendor_size + self.metadata_size + 4
        self.img_size_bytes = 15360000000  # ~15GB

    def run_cmd(self, cmd):
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)

    def create_image_file(self):
        if os.path.exists(self.img_path):
            raise FileExistsError(f"{self.img_path} already exists!")
        print(f"Creating image file {self.img_path}...")
        self.run_cmd(["sudo", "fallocate", "-l", str(self.img_size_bytes), self.img_path])
        self.run_cmd(["sync"])

    def create_partitions(self):
        print("Creating partitions using parted...")
        # Create partition table
        self.run_cmd(["sudo", "parted", "--script", self.img_path, "mklabel", "msdos"])

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

    def add_partition(self, part_type, fs_type, start, end):
        cmd = ["sudo", "parted", "--script", self.img_path, "mkpart", part_type]
        if fs_type:
            cmd.append(fs_type)
        cmd += [start, end]
        self.run_cmd(cmd)

    def map_loop_device(self):
        print("Mapping loop device...")
        result = subprocess.run(["sudo", "kpartx", "-av", self.img_path], capture_output=True, text=True, check=True)
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
        self.run_cmd(["sudo", "chown", f"{os.getenv('USER')}:{os.getenv('USER')}", self.img_path])

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


if __name__ == "__main__":
    builder = ImageBuilder("RaspberryVanillaAOSP16", os.getenv("TARGET_PRODUCT", "aosp_rpi"), os.getenv("ANDROID_PRODUCT_OUT", "/path/to/output"))
    builder.build_image()

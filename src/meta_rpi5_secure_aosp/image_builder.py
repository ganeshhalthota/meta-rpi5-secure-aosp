
import os
import subprocess
from datetime import datetime

class ImageBuilder:
    def __init__(self, image_data: dict, compress: bool = False):
        self.validate(image_data)
        self._image_data = image_data
        self._compress = compress
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
        partition_start = 1  # Start at 1MiB
        for partition_info in self._image_data['partitions']:
            part_name = partition_info['name']
            part_format = partition_info['format']

            # Calculate partition size
            if 'size' in partition_info and partition_info['size']:
                part_size = int(partition_info['size'])
                partition_end = partition_start + part_size
            else:
                # Use remaining space (100%)
                partition_end = "100%"

            # Format start and end for parted command
            start_str = f"{partition_start}MiB"
            end_str = f"{partition_end}MiB" if isinstance(partition_end, int) else partition_end

            print(f"  Creating partition {partition_number}: {part_name} ({start_str} -> {end_str})")

            self.add_partition(name=part_name,
                               fs_type=part_format,
                               start=start_str,
                               end=end_str,
                               partition_number=str(partition_number))

            # Set boot flag if specified
            if 'flags' in partition_info and partition_info['flags']:
                self.run_cmd(["sudo", "parted", "--script", self._img_path, "set", str(partition_number), partition_info['flags'], "on"])

            # increment for partition number
            partition_number += 1
            # Compute the start of next partition (only if we have a fixed size)
            if isinstance(partition_end, int):
                partition_start = partition_end

    def add_partition(self, name, fs_type, start, end, partition_number):
        # Create partition
        cmd = ["sudo", "parted", "--script", self._img_path, "mkpart", name]
        if fs_type and fs_type.lower() != 'raw':
            cmd.append(fs_type)
        cmd.extend([start, end])
        self.run_cmd(cmd)
        # Assign name explicitly (important for AVB)
        self.run_cmd(["sudo", "parted", "--script", self._img_path, "name", partition_number, name])

    def map_loop_device(self):
        print("Mapping loop device...")

        # Step 1: Find a free loop device
        result = subprocess.run(["sudo", "losetup", "-f"], capture_output=True, text=True, check=True)
        loopdev = result.stdout.strip()
        if not loopdev:
            raise RuntimeError("Unable to find free loop device!")
        print(f"  Found free loop device: {loopdev}")

        # Step 2: Attach the image to the loop device
        print(f"  Attaching {self._img_path} to {loopdev}...")
        self.run_cmd(["sudo", "losetup", loopdev, self._img_path])

        # Step 3: Map the partitions using kpartx
        print(f"  Mapping partitions with kpartx...")
        result = subprocess.run(["sudo", "kpartx", "-av", loopdev], capture_output=True, text=True, check=True)
        print(f"  kpartx output:\n{result.stdout}")

        # Extract the mapper device name (e.g., loop0 from /dev/loop0)
        mapper_name = os.path.basename(loopdev)
        print(f"  Partitions mapped as /dev/mapper/{mapper_name}pX")

        return mapper_name

    def copy_partition(self, loopdev, partition, src_img):
        print(f"Copying {src_img} to {partition}...")
        # Check if source image exists
        if not os.path.exists(src_img):
            raise FileNotFoundError(f"Source image not found: {src_img}")

        # Get source image size
        src_size = os.path.getsize(src_img)
        print(f"  Source image size: {src_size / (1024*1024):.2f} MiB")

        # Use dd with conv=notrunc to avoid issues with partition size
        self.run_cmd(["sudo", "dd", f"if={src_img}", f"of=/dev/mapper/{loopdev}{partition}", "bs=1M", "conv=notrunc"])

    def copy_extra_files(self, loopdev, partition_number, extra_files):
        print(f"Copying extra files to partition {partition_number}...")

        # Create a temporary mount point
        import tempfile
        mount_point = tempfile.mkdtemp()
        print(f"  Created temporary mount point: {mount_point}")

        try:
            # Mount the partition
            self.run_cmd(["sudo", "mount", f"/dev/mapper/{loopdev}p{partition_number}", mount_point])

            # Copy each extra file
            for file_info in extra_files:
                if "src" in file_info and os.path.exists(file_info["src"]):
                    # Copy from existing file
                    dst_path = os.path.join(mount_point, file_info["dst"])
                    print(f"  Copying {file_info['src']} to {dst_path}")
                    self.run_cmd(["sudo", "cp", file_info["src"], dst_path])
                elif "content" in file_info:
                    # Create file with specified content
                    dst_path = os.path.join(mount_point, file_info["src"])
                    print(f"  Creating file {dst_path}")
                    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
                        temp_file.write(file_info["content"])
                        temp_path = temp_file.name

                    self.run_cmd(["sudo", "cp", temp_path, dst_path])
                    os.unlink(temp_path)

            # Sync to ensure all writes are flushed
            self.run_cmd(["sudo", "sync"])
        finally:
            # Unmount the partition
            self.run_cmd(["sudo", "umount", mount_point])

            # Remove the temporary mount point
            os.rmdir(mount_point)
            print("  Removed temporary mount point")

    def create_filesystem(self, loopdev, partition, label):
        print(f"Creating filesystem on {partition} with label {label}...")
        self.run_cmd(["sudo", "mkfs.ext4", f"/dev/mapper/{loopdev}{partition}", "-I", "512", "-L", label])

    def cleanup(self, loopdev):
        print("Cleaning up loop device...")

        # Step 1: Remove partition mappings
        print(f"  Removing partition mappings...")
        self.run_cmd(["sudo", "kpartx", "-d", f"/dev/{loopdev}"])

        # Step 2: Detach the loop device
        print(f"  Detaching loop device /dev/{loopdev}...")
        self.run_cmd(["sudo", "losetup", "-d", f"/dev/{loopdev}"])

        # Step 3: Change ownership of the image file
        print(f"  Changing ownership of {self._img_path}...")
        # Get the actual user (not root) - try multiple methods
        import pwd
        try:
            # Try SUDO_USER first (when running with sudo)
            username = os.getenv('SUDO_USER')
            if not username:
                # Fall back to USER environment variable
                username = os.getenv('USER')
            if not username:
                # Fall back to current effective user
                username = pwd.getpwuid(os.getuid()).pw_name

            if username and username != 'root':
                self.run_cmd(["sudo", "chown", f"{username}:{username}", self._img_path])
                print(f"  Changed ownership to {username}:{username}")
            else:
                print(f"  Skipping ownership change (running as root or user not detected)")
        except Exception as e:
            print(f"  Warning: Could not change ownership: {e}")

        print("  Cleanup completed successfully!")

    def compress_image(self):
        print("Compressing image to zip")
        self.run_cmd(["zip", self._img_path + ".zip", self._img_path])

    def build_image(self):
        self.create_image_file()
        self.create_partitions()
        loopdev = self.map_loop_device()

        try:
            # Process each partition
            partition_number = 1
            for partition_info in self._image_data['partitions']:
                part_name = partition_info['name']
                partition_dev = f"p{partition_number}"

                # If there's an image file to copy, copy it
                if 'img' in partition_info and partition_info['img']:
                    self.copy_partition(loopdev, partition_dev, partition_info['img'])
                # Otherwise, create an empty filesystem
                elif partition_info['format'] in ['ext4', 'ext3', 'ext2']:
                    self.create_filesystem(loopdev, partition_dev, part_name)
                elif partition_info['format'] == 'fat32':
                    self.run_cmd(["sudo", "mkfs.vfat", "-F", "32", "-n", part_name.upper(), f"/dev/mapper/{loopdev}{partition_dev}"])

                # If there are extra files to copy to this partition
                if 'extra_files' in partition_info and partition_info['extra_files']:
                    self.copy_extra_files(loopdev, partition_number, partition_info['extra_files'])

                partition_number += 1
        except Exception as e:
            print(f"Error during image building: {e}")
            print("Attempting cleanup...")
            self.cleanup(loopdev)
            raise

        self.cleanup(loopdev)

        if self._compress:
            print(f"Compressing image to zip file")
            self.compress_image()

        return self._img_path

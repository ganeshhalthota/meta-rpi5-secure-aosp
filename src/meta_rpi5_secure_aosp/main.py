#!/usr/bin/env python3
"""
RPi5 Secure AOSP Builder - Smart stage + code selection
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from image_builder import ImageBuilder

def get_default_workspace() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent.resolve()
    else:
        return Path(__file__).resolve().parent.parent.parent

console = Console()

@click.command()
@click.option(
    "--workspace", "-w",
    type=click.Path(exists=True, file_okay=False, writable=True, path_type=Path),
    default=get_default_workspace,
    show_default="directory containing the binary",
    help="Workspace root (contains u-boot/, rpi5-aosp/, config/, avb/)",
)
@click.option(
    "--stage", "-s",
    type=click.Choice(["all", "sync", "build", "sign", "sdcard"], case_sensitive=False),
    default="all",
    show_default=True,
    help="High-level stage: all, sync, build, sign, sdcard"
)
@click.option(
    "--code", "-c",
    type=click.Choice(["all", "uboot", "aosp"], case_sensitive=False),
    default="all",
    show_default=True,
    help="Which code to process: all, uboot, or aosp"
)
@click.option("--config",
              type=click.Path(exists=True, dir_okay=False, path_type=Path),
              default=lambda: Path(click.get_current_context().params["workspace"]) / "config" / "rpi5.yaml",
              show_default="workspace/config/rpi5.yaml")
@click.option("--avb-key",
              type=click.Path(exists=True, dir_okay=False, path_type=Path),
              default=lambda: Path(click.get_current_context().params["workspace"]) / "avb" / "avb_private_key.pem",
              show_default="workspace/avb/avb_private_key.pem")
def main(workspace: Path, stage: str, code: str, config: Path, avb_key: Path) -> None:
    """RPi5 Secure AOSP Builder - flexible stage + code selection"""

    uboot_dir   = workspace / "u-boot"
    aosp_dir    = workspace / "rpi5-aosp"
    sdcard_dir  = workspace / "sdcard"

    # Resolve which code paths are active
    do_uboot = code in {"all", "uboot"}
    do_aosp  = code in {"all", "aosp"}

    # Resolve which stages are active
    do_sync   = stage in {"all", "sync"}
    do_build  = stage in {"all", "build"}
    do_sign   = stage in {"all", "sign"}
    do_sdcard = stage in {"all", "sdcard"}

    # Define partition configuration - sizes in MB
    partition_config = {
        "boot": {"size": "256", "format": "fat32", "flags": "boot"},
        "system": {"size": "4096", "format": "ext4"},
        "vendor": {"size": "512", "format": "ext4"},
        "vbmeta": {"size": "4", "format": "raw"},
        "userdata": {"size": "", "format": "ext4"}  # Empty size means use remaining space
    }

    # Convert MB to bytes for signing
    partition_sizes_bytes = {
        name: int(config["size"]) * 1024 * 1024 if config["size"] else 0
        for name, config in partition_config.items()
    }

    console.print(Panel.fit(
        f"[bold magenta]RPi5 Secure AOSP Builder[/]\n"
        f"[dim]Workspace :[/] {workspace}\n"
        f"[dim]Stage     :[/] {stage}\n"
        f"[dim]Code      :[/] {code} -> U-Boot={'Yes' if do_uboot else 'No'}, AOSP={'Yes' if do_aosp else 'No'}\n"
        f"[dim]Config    :[/] {config}\n"
        f"[dim]AVB Key   :[/] {avb_key}\n"
        f"[dim]Actions   :[/] {'Sync, ' if do_sync else ''}{'Build, ' if do_build else ''}{'Sign, ' if do_sign else ''}{'SD Card' if do_sdcard else ''}",
        border_style="magenta"
    ))

    def run(cmd: str, cwd: Path, silent: bool = False) -> None:
        if not silent:
            rel = cwd.relative_to(workspace) if cwd.is_relative_to(workspace) else cwd
            console.log(f"[bold green]+$[/] [dim]{rel}[/] {cmd}")
        subprocess.run(cmd, shell=True, check=True, cwd=cwd, text=True)

    # ------------------------------------------------------------------
    # Stage: Sync
    # ------------------------------------------------------------------
    if do_sync:
        console.print("\n[bold blue]Stage: Sync[/]")
        from xml.etree import ElementTree as ET
        from xml.dom import minidom

        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:

            if do_uboot:
                if uboot_dir.exists():
                    progress.add_task("Updating u-boot", total=None)
                    run("git fetch --all --prune", cwd=uboot_dir)
                    run("git reset --hard origin/master", cwd=uboot_dir)
                    run("git clean -fdx", cwd=uboot_dir)
                else:
                    progress.add_task("Cloning u-boot", total=None)
                    run("git clone https://github.com/u-boot/u-boot.git u-boot", cwd=workspace)

            if do_aosp:
                repo_cmd = "repo" if shutil.which("repo") else "python3 -m repo"

                if (aosp_dir / ".repo").exists():
                    progress.add_task("Syncing AOSP", total=None)
                    run(f"{repo_cmd} sync -j 8 --no-tags --optimized-fetch --current-branch", cwd=aosp_dir)
                else:
                    aosp_dir.mkdir(parents=True, exist_ok=True)
                    progress.add_task("repo init", total=None)
                    run(f"{repo_cmd} init -u https://android.googlesource.com/platform/manifest -b android-16.0.0_r4 --depth=1 --no-tags --current-branch --repo-branch aosp/stable --no-repo-verify", cwd=aosp_dir)

                    manifest_dir = aosp_dir / ".repo" / "local_manifests"
                    manifest_dir.mkdir(parents=True, exist_ok=True)

                    progress.add_task("Downloading + patching manifest", total=None)
                    run ("curl -L -o manifest_brcm_rpi.xml "
                         "https://raw.githubusercontent.com/ganeshhalthota/android_local_manifest/android-16.0/manifest_brcm_rpi.xml",
                         cwd=manifest_dir)
                    run ("curl -L -o remove_projects.xml "
                         "https://raw.githubusercontent.com/ganeshhalthota/android_local_manifest/android-16.0/remove_projects.xml",
                         cwd=manifest_dir)

                    progress.add_task("Final repo sync", total=None)
                    run(f"{repo_cmd} sync -j 8 --no-tags --optimized-fetch --current-branch", cwd=aosp_dir)

        console.print("[green]Sync completed[/]\n")

    # ------------------------------------------------------------------
    # Stage: Build
    # ------------------------------------------------------------------
    if do_build:
        console.print("[bold blue]Stage: Build[/]")

        if do_uboot:
            if not uboot_dir.exists():
                raise click.ClickException("u-boot/ missing — run sync first")
            console.print("-> Building U-Boot")
            run("CROSS_COMPILE=aarch64-linux-gnu- make rpi_arm64_defconfig", cwd=uboot_dir)
            run("CROSS_COMPILE=aarch64-linux-gnu- make -j$(nproc)", cwd=uboot_dir)

        if do_aosp:
            if not (aosp_dir / ".repo").exists():
                raise click.ClickException("rpi5-aosp/ missing — run sync first")
            console.print("-> Building AOSP")
            run("""bash -c 'source build/envsetup.sh && lunch aosp_rpi5_car-bp4a-eng && make bootimage systemimage vendorimage -j $(nproc)'""", cwd=aosp_dir)

        console.print("[green]Build completed[/]\n")

    # ------------------------------------------------------------------
    # Stage: Sign
    # ------------------------------------------------------------------
    if do_sign:
        console.print("[bold blue]Stage: Signing images with AVB[/]")

        # Look for avbtool in AOSP build output first, then in PATH
        avbtool_path = aosp_dir / "out/host/linux-x86/bin/avbtool"
        if avbtool_path.exists():
            avbtool_cmd = str(avbtool_path)
            console.print(f"Using avbtool from AOSP build: {avbtool_cmd}")
        elif shutil.which("avbtool"):
            avbtool_cmd = "avbtool"
            console.print("Using avbtool from PATH")
        else:
            raise click.ClickException("avbtool not found in AOSP build or PATH. Please build AOSP first or install Android Verified Boot tools.")

        # Define the images to sign
        images_to_sign = []

        if do_aosp:
            boot_img = aosp_dir / "out/target/product/rpi5/boot.img"
            system_img = aosp_dir / "out/target/product/rpi5/system.img"
            vendor_img = aosp_dir / "out/target/product/rpi5/vendor.img"

            if not boot_img.exists() or not system_img.exists() or not vendor_img.exists():
                raise click.ClickException("AOSP images missing — run build first")

            images_to_sign.extend([boot_img, system_img, vendor_img])

        # Sign each image with AVB
        for img in images_to_sign:
            img_name = img.name
            console.print(f"-> Signing {img_name}")

            # Create a signed copy with .signed extension
            signed_img = img.with_suffix(".signed.img")

            # Sign the image with AVB
            vbmeta_img_name = f'vbmeta_{img_name.split(".")[0]}.img'
            partition_name = img_name.split('.')[0]

            # Use predefined partition size
            if partition_name in partition_sizes_bytes:
                partition_size = partition_sizes_bytes[partition_name]
                console.print(f"   Using predefined partition size for {partition_name}: {partition_size} bytes ({partition_config[partition_name]['size']} MB)")
            else:
                # Fallback to file size if partition not defined
                partition_size_cmd = f"stat -c%s {img}"
                partition_size = subprocess.check_output(partition_size_cmd, shell=True, text=True, cwd=workspace).strip()
                console.print(f"   Using file size for {partition_name}: {partition_size} bytes")

            run(f"{avbtool_cmd} add_hash_footer --image {img} \
                --partition_name {partition_name} \
                --partition_size {partition_size} \
                --key {avb_key} \
                --algorithm SHA256_RSA4096 \
                --output_vbmeta_image {img.parent / vbmeta_img_name}",
                cwd=workspace)

            # Replace original with signed version
            shutil.copy2(img, img.with_suffix(".unsigned.img"))  # Backup original
            run(f"{avbtool_cmd} append_vbmeta_image --image {img} \
                --partition_size {partition_size} \
                --vbmeta_image {img.parent / vbmeta_img_name}",
                cwd=workspace)

        # Create a combined vbmeta image for all partitions
        console.print("-> Creating combined vbmeta image")
        vbmeta_images = [str(img.parent / f'vbmeta_{img.name.split(".")[0]}.img') for img in images_to_sign]
        vbmeta_args = " ".join([f"--include_descriptors_from_image {img}" for img in vbmeta_images])
        combined_vbmeta = aosp_dir / "out/target/product/rpi5/vbmeta.img"

        run(f"{avbtool_cmd} make_vbmeta_image \
            --output {combined_vbmeta} \
            --algorithm SHA256_RSA4096 \
            --key {avb_key} \
            {vbmeta_args}",
            cwd=workspace)

        console.print(f"-> Combined vbmeta image created at {combined_vbmeta}")

        console.print("[green]Signing completed[/]\n")

    # ------------------------------------------------------------------
    # Stage: sdcard
    # ------------------------------------------------------------------
    if do_sdcard:
        console.print("[bold blue]Stage: Generating sdcard image[/]")
        sdcard_dir.mkdir(exist_ok=True)

        # define the partitions and sizes
        # image size - 24576MB (24GB)
        # GPT partition scheme
        # vbmeta - 4MB (if signing is enabled)
        # boot - 256MB (boot.img is 128M + u-boot.bin, giving extra space for safety)
        # system - 4096MB (system.img is 3.0G, giving extra space)
        # vendor - 512MB (vendor.img is 384M, giving extra space)
        # userdata - remaining

        # Check if signed images exist and use them if available
        boot_img = str(aosp_dir / "out/target/product/rpi5/boot.img")
        system_img = str(aosp_dir / "out/target/product/rpi5/system.img")
        vendor_img = str(aosp_dir / "out/target/product/rpi5/vendor.img")
        vbmeta_img = None

        # Use signed images if they exist
        if do_sign or (do_aosp and Path(boot_img).exists()):
            console.print("Using signed images for SD card creation")
            # Check for combined vbmeta image
            combined_vbmeta = aosp_dir / "out/target/product/rpi5/vbmeta.img"
            if combined_vbmeta.exists():
                vbmeta_img = str(combined_vbmeta)
                console.print(f"Found combined vbmeta image: {vbmeta_img}")
            else:
                # Look for individual vbmeta images
                boot_vbmeta = aosp_dir / "out/target/product/rpi5/vbmeta_boot.img"
                if boot_vbmeta.exists():
                    vbmeta_img = str(boot_vbmeta)
                    console.print(f"Using boot vbmeta image: {vbmeta_img}")

        # Define partitions list
        partitions = []

        # Add vbmeta partition if signing is enabled and vbmeta image exists
        if do_sign and vbmeta_img:
            partitions.append({
                "name": "vbmeta",
                "size": partition_config["vbmeta"]["size"],
                "format": partition_config["vbmeta"]["format"],
                "img": vbmeta_img
            })
            console.print("Added vbmeta partition to SD card image")

        # Add standard partitions
        partitions.extend([
            {
                "name": "boot",
                "size": partition_config["boot"]["size"],
                "format": partition_config["boot"]["format"],
                "flags": partition_config["boot"]["flags"],
                "img": boot_img,
                "extra_files": [
                    {
                        "src": str(uboot_dir / "u-boot.bin"),
                        "dst": "u-boot.bin"
                    },
                    {
                        "src": "config.txt",
                        "content": "# Raspberry Pi 5 boot configuration\n\n# Load U-Boot\nkernel=u-boot.bin\n\n# GPU memory\ngpu_mem=256\n"
                    }
                ]
            },
            {
                "name": "system",
                "size": partition_config["system"]["size"],
                "format": partition_config["system"]["format"],
                "img": system_img
            },
            {
                "name": "vendor",
                "size": partition_config["vendor"]["size"],
                "format": partition_config["vendor"]["format"],
                "img": vendor_img
            },
            {
                "name": "userdata",
                "size": partition_config["userdata"]["size"],
                "format": partition_config["userdata"]["format"]
            },
        ])

        image_data = {
            "output_dir": sdcard_dir,
            "image_name": "rpi5-aosp",
            "partition_scheme": "gpt",
            "sdcard_size": "24576",
            "partitions": partitions
        }
        image_builder = ImageBuilder(image_data=image_data, compress=True)
        image_path = image_builder.build_image()
        console.print(f"[bold green]Image ready in:[/] {image_path}\n")

    console.print("[bold green]All requested stages completed successfully![/]")

if __name__ == "__main__":
    main()

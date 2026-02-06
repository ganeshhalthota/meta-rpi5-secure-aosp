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
    type=click.Choice(["all", "sync", "build", "sdcard"], case_sensitive=False),
    default="all",
    show_default=True,
    help="High-level stage: all, sync, build, sdcard"
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
    do_sdcard = stage in {"all", "sdcard"}

    console.print(Panel.fit(
        f"[bold magenta]RPi5 Secure AOSP Builder[/]\n"
        f"[dim]Workspace :[/] {workspace}\n"
        f"[dim]Stage     :[/] {stage}\n"
        f"[dim]Code      :[/] {code} -> U-Boot={'Yes' if do_uboot else 'No'}, AOSP={'Yes' if do_aosp else 'No'}\n"
        f"[dim]Config    :[/] {config}\n"
        f"[dim]AVB Key   :[/] {avb_key}",
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
    # Stage: sdcard
    # ------------------------------------------------------------------
    if do_sdcard:
        console.print("[bold blue]Stage: Generating sdcard image[/]")
        sdcard_dir.mkdir(exist_ok=True)

        # define the partitions and sizes
        # image size - 24576MB (24GB)
        # GPT partition scheme
        # boot - 256MB (boot.img is 128M, giving extra space for safety)
        # system - 4096MB (system.img is 3.0G, giving extra space)
        # vendor - 512MB (vendor.img is 384M, giving extra space)
        # userdata - remaining
        image_data = {
            "output_dir": sdcard_dir,
            "image_name": "rpi5-aosp",
            "partition_scheme": "gpt",
            "sdcard_size": "24576",
            "partitions" : [
                {
                    "name": "boot",
                    "size": "256",
                    "format": "fat32",
                    "flags": "boot",
                    "img": str(aosp_dir / "out/target/product/rpi5/boot.img")
                },
                {
                    "name": "system",
                    "size": "4096",
                    "format": "ext4",
                    "img": str(aosp_dir / "out/target/product/rpi5/system.img")
                },
                {
                    "name": "vendor",
                    "size": "512",
                    "format": "ext4",
                    "img": str(aosp_dir / "out/target/product/rpi5/vendor.img")
                },
                {
                    "name": "userdata",
                    "size": "",             # All remaining space to be used for userdata
                    "format": "ext4"
                },
            ]
        }
        image_builder = ImageBuilder(image_data)
        image_path = image_builder.build_image()
        console.print(f"[bold green]Image ready in:[/] {image_path}\n")

    console.print("[bold green]All requested stages completed successfully![/]")

if __name__ == "__main__":
    main()

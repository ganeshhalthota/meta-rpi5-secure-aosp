"""
Stage: SD Card
Assembles the final SD-card image from partition images.
"""

from __future__ import annotations

import yaml

from meta_rpi5_secure_aosp.context import BuildContext
from meta_rpi5_secure_aosp.utils.disk_image import DiskImage


def run(ctx: BuildContext) -> None:
    """Build the SD-card image using ImageBuilder."""
    ctx.console.print("[bold blue]Stage: Generating sdcard image[/]")

    ctx.sdcard_dir.mkdir(exist_ok=True)

    with open(ctx.sdcard_config, "r") as f:
        image_data = yaml.safe_load(f)

    # Make paths in image_data absolute
    image_data["output_dir"] = ctx.sdcard_dir

    for part in image_data["partitions"]:
        if "img" in part:
            img_path   = ctx.aosp_dir / part["img"]
            signed_path = img_path.with_suffix(".signed.img")
            if ctx.signing_enabled and signed_path.exists():
                part["img"] = signed_path
                ctx.console.print(
                    f"   Using signed image for {part['name']}: {signed_path.name}"
                )
            else:
                part["img"] = img_path

        if "extra_files" in part:
            for extra_file in part["extra_files"]:
                if "src" in extra_file and not extra_file.get("content"):
                    extra_file["src"] = ctx.workspace / extra_file["src"]

    disk = DiskImage(image_data=image_data)
    image_path = disk.build()
    ctx.console.print(f"[bold green]Image ready in:[/] {image_path}\n")

    ctx.console.print("[bold blue]Compressing image to tar.gz (split by 0.5 GiB)...[/]")
    parts = disk.compress_tar_gz_split(split_size=512 * 1024 * 1024)
    ctx.console.print(
        f"[bold green]{len(parts)} archive part(s) created in:[/] {ctx.sdcard_dir}\n"
    )
    ctx.console.print(
        "[dim]To reassemble:  cat *.img.tar.gz.* | tar -xzf -[/]\n"
    )

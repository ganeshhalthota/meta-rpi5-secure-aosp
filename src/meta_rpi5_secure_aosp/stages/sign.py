"""
Stage: Sign
Signs AOSP partition images with Android Verified Boot (AVB).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import click
import yaml

from meta_rpi5_secure_aosp.context import BuildContext
from meta_rpi5_secure_aosp.utils.avb import AvbTool


def _run_fs_tool(cmd: list[str], ok_codes: set[int] | None = None) -> None:
    if ok_codes is None:
        ok_codes = {0}
    result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode not in ok_codes:
        raise click.ClickException(
            f"Command failed: {' '.join(cmd)}\n{result.stdout}"
        )


def _shrink_ext4_image_for_avb(ctx: BuildContext, image: Path, target_size_bytes: int) -> None:
    """
    Shrink an ext4 image file so AVB footer metadata can fit in partition size.
    """
    target_kib = target_size_bytes // 1024
    if target_kib == 0:
        raise click.ClickException(f"Invalid AVB target size for {image.name}: {target_size_bytes}")

    ctx.console.print(
        f"   Resizing {image.name} to <= {target_size_bytes} bytes "
        f"({target_kib} KiB) to fit AVB hashtree footer"
    )

    # e2fsck returns 0 (clean) or 1 (fixed errors); both are acceptable here.
    _run_fs_tool(["e2fsck", "-fy", str(image)], ok_codes={0, 1})
    _run_fs_tool(["resize2fs", "-f", str(image), f"{target_kib}K"])
    _run_fs_tool(["truncate", "-s", str(target_size_bytes), str(image)])

    final_size = AvbTool.get_file_size(image)
    if final_size > target_size_bytes:
        raise click.ClickException(
            f"Failed to shrink {image.name} to AVB limit. "
            f"final_size={final_size}, target={target_size_bytes}"
        )


def run(ctx: BuildContext) -> None:
    """Sign partition images with AVB using the key in ctx.avb_key."""
    ctx.console.print("[bold blue]Stage: Signing images with AVB[/]")

    with open(ctx.sdcard_config, "r") as f:
        sdcard_data = yaml.safe_load(f)

    partition_config = {p["name"]: p for p in sdcard_data["partitions"]}
    partition_sizes_bytes = {
        name: int(cfg["size"]) * 1024 * 1024 if cfg.get("size") else 0
        for name, cfg in partition_config.items()
    }

    avb_config = ctx.rpi5_config["avb"]

    # Support both old and new config formats for backward compatibility
    if "sign_algorithm" in avb_config:
        sign_algorithm = avb_config["sign_algorithm"]
        hash_algorithm = avb_config.get("hash_algorithm", "sha256")
    else:
        # Backward compatibility: treat 'algorithm' as hash_algorithm
        sign_algorithm = "SHA256_RSA4096"
        hash_algorithm = avb_config.get("algorithm", "sha256")

    avb = AvbTool(
        aosp_dir=ctx.aosp_dir,
        avb_key=ctx.avb_key,
        run=ctx.run,
        sign_algorithm=sign_algorithm,
        hash_algorithm=hash_algorithm,
    )
    ctx.console.print(f"Using avbtool: {avb._cmd}")

    product_out = ctx.aosp_dir / "out/target/product/rpi5"

    # Partitions to sign with hashtree footer (dm-verity)
    # boot.img is intentionally excluded — RPi5 firmware loads it without verification
    hashtree_partitions = []
    if ctx.do_aosp:
        system_img = product_out / "system.img"
        vendor_img = product_out / "vendor.img"

        if not system_img.exists() or not vendor_img.exists():
            raise click.ClickException("AOSP images missing — run build first")

        hashtree_partitions = [system_img, vendor_img]

    signed_images = []

    for img in hashtree_partitions:
        partition_name = img.stem          # e.g. "system", "vendor"
        signed_img     = img.with_suffix(".signed.img")

        ctx.console.print(f"-> Signing {img.name} with hashtree footer (dm-verity)")

        if partition_name in partition_sizes_bytes and partition_sizes_bytes[partition_name] > 0:
            partition_size = partition_sizes_bytes[partition_name]
            ctx.console.print(
                f"   Using predefined partition size for {partition_name}: "
                f"{partition_size} bytes ({partition_config[partition_name]['size']} MB)"
            )
        else:
            partition_size = AvbTool.get_file_size(img)
            ctx.console.print(f"   Using file size for {partition_name}: {partition_size} bytes")

        shutil.copy2(img, signed_img)

        max_payload_size = avb.calc_max_image_size(
            partition_name=partition_name,
            partition_size=partition_size,
        )
        signed_size = AvbTool.get_file_size(signed_img)
        if signed_size > max_payload_size:
            ctx.console.print(
                f"   {partition_name}.img is too large for AVB footer in this partition "
                f"({signed_size} > {max_payload_size})"
            )
            _shrink_ext4_image_for_avb(
                ctx=ctx,
                image=signed_img,
                target_size_bytes=max_payload_size,
            )

        # We don't use sidecar vbmeta descriptors; we point make_vbmeta_image
        # directly at the signed partition images which now contain the footer.
        avb.add_hashtree_footer(
            image=signed_img,
            partition_name=partition_name,
            partition_size=partition_size,
        )
        signed_images.append(signed_img)

    # Combined vbmeta image
    ctx.console.print("-> Creating combined vbmeta image")
    combined_vbmeta = product_out / "vbmeta.img"
    avb.make_vbmeta_image(output=combined_vbmeta, include_images=signed_images)
    ctx.console.print(f"-> Combined vbmeta image created at {combined_vbmeta.name}")

    ctx.console.print("[green]Signing completed[/]\n")

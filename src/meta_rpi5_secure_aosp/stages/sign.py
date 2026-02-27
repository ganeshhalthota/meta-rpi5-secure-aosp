"""
Stage: Sign
Signs AOSP partition images with Android Verified Boot (AVB).
"""

from __future__ import annotations

import shutil

import click
import yaml

from meta_rpi5_secure_aosp.context import BuildContext
from meta_rpi5_secure_aosp.utils.avb import AvbTool


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

    avb = AvbTool(
        aosp_dir=ctx.aosp_dir,
        avb_key=ctx.avb_key,
        run=ctx.run,
        algorithm=ctx.rpi5_config["avb"]["algorithm"],
    )
    ctx.console.print(f"Using avbtool: {avb._cmd}")

    images_to_sign = []

    if ctx.do_aosp:
        product_out = ctx.aosp_dir / "out/target/product/rpi5"
        boot_img   = product_out / "boot.img"
        system_img = product_out / "system.img"
        vendor_img = product_out / "vendor.img"

        if not boot_img.exists() or not system_img.exists() or not vendor_img.exists():
            raise click.ClickException("AOSP images missing — run build first")

        images_to_sign.extend([boot_img, system_img, vendor_img])

    vbmeta_sidecar_images: list = []

    for img in images_to_sign:
        partition_name = img.stem          # e.g. "boot", "system", "vendor"
        signed_img     = img.with_suffix(".signed.img")
        vbmeta_img     = img.parent / f"vbmeta_{partition_name}.img"

        ctx.console.print(f"-> Signing {img.name}")

        if partition_name in partition_sizes_bytes:
            partition_size = partition_sizes_bytes[partition_name]
            ctx.console.print(
                f"   Using predefined partition size for {partition_name}: "
                f"{partition_size} bytes ({partition_config[partition_name]['size']} MB)"
            )
        else:
            partition_size = AvbTool.get_file_size(img)
            ctx.console.print(f"   Using file size for {partition_name}: {partition_size} bytes")

        shutil.copy2(img, signed_img)

        avb.add_hash_footer(
            image=signed_img,
            partition_name=partition_name,
            partition_size=partition_size,
            vbmeta_output=vbmeta_img,
        )
        avb.append_vbmeta_image(
            image=signed_img,
            partition_size=partition_size,
            vbmeta_image=vbmeta_img,
        )
        vbmeta_sidecar_images.append(vbmeta_img)

    # Combined vbmeta image
    ctx.console.print("-> Creating combined vbmeta image")
    combined_vbmeta = ctx.aosp_dir / "out/target/product/rpi5/vbmeta.img"
    avb.make_vbmeta_image(output=combined_vbmeta, include_images=vbmeta_sidecar_images)
    ctx.console.print(f"-> Combined vbmeta image created at {combined_vbmeta}")

    ctx.console.print("[green]Signing completed[/]\n")

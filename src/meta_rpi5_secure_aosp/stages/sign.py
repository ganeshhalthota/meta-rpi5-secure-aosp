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

    # Get AVB public key for storage in boot partition
    # (used by U-Boot for verification)
    avb_pubkey_dir = ctx.workspace / "keys"
    avb_pubkey_dir.mkdir(exist_ok=True)
    avb_pubkey_path = avb_pubkey_dir / "avb_pubkey.bin"

    if ctx.avb_pubkey and ctx.avb_pubkey.exists():
        # Use pre-existing public key from config
        ctx.console.print(f"-> Using AVB public key from config: {ctx.avb_pubkey}")
        shutil.copy2(ctx.avb_pubkey, avb_pubkey_path)
        ctx.console.print(f"   Public key copied to {avb_pubkey_path.name}")
    else:
        # Fallback: extract from private key
        ctx.console.print("-> Extracting AVB public key from private key")
        avb.extract_public_key(output=avb_pubkey_path)
        ctx.console.print(f"   Public key extracted to {avb_pubkey_path.name}")

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

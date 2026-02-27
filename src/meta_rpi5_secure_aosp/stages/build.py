"""
Stage: Build
Compiles u-boot and/or AOSP from source.
"""

from __future__ import annotations

import click

from meta_rpi5_secure_aosp.context import BuildContext


def run(ctx: BuildContext) -> None:
    """Build u-boot and/or AOSP depending on ctx.do_uboot / ctx.do_aosp."""
    ctx.console.print("[bold blue]Stage: Build[/]")

    if ctx.do_uboot:
        if not ctx.uboot_dir.exists():
            raise click.ClickException("u-boot/ missing — run sync first")
        ctx.console.print("-> Building U-Boot")
        ctx.run("CROSS_COMPILE=aarch64-linux-gnu- make rpi_arm64_defconfig", cwd=ctx.uboot_dir)
        ctx.run("CROSS_COMPILE=aarch64-linux-gnu- make -j$(nproc)", cwd=ctx.uboot_dir)

    if ctx.do_aosp:
        if not (ctx.aosp_dir / ".repo").exists():
            raise click.ClickException("rpi5-aosp/ missing — run sync first")
        ctx.console.print("-> Building AOSP")
        ctx.run(
            "bash -c 'source build/envsetup.sh && "
            "lunch aosp_rpi5_car-bp4a-eng && "
            "make bootimage systemimage vendorimage -j $(nproc)'",
            cwd=ctx.aosp_dir,
        )

    ctx.console.print("[green]Build completed[/]\n")

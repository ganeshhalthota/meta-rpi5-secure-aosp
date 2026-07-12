"""
Stage: Build
Compiles u-boot and/or AOSP from source.
"""

from __future__ import annotations

import re
from pathlib import Path

import click

from meta_rpi5_secure_aosp.context import BuildContext


def _avb_fail_policy(ctx: BuildContext) -> str:
    policy = ctx.rpi5_config.get("avb", {}).get("uboot_fail_policy") or getattr(ctx, "avb_fail_policy", None)
    if not policy:
        policy = "fail_closed"
    valid = {"fail_closed", "fail_open"}
    if policy not in valid:
        raise click.ClickException(
            f"Invalid avb.uboot_fail_policy={policy!r}. Expected one of: {', '.join(sorted(valid))}"
        )
    return policy


def _prepare_boot_script_source(ctx: BuildContext, boot_cmd: str, signing_enabled: bool) -> str:
    src = ctx.config_dir / "uboot/boot_avb.cmd" if signing_enabled else ctx.config_dir / "uboot/boot.cmd"
    if str(boot_cmd) != str(src):
        src = Path(boot_cmd)

    content = src.read_text(encoding="utf-8")
    rendered = content.replace("__SELINUX_MODE__", getattr(ctx, "selinux_mode", "permissive"))
    rendered = rendered.replace("__BOOT_STATE_ARGS__", getattr(ctx, "boot_state_args", ""))
    rendered = rendered.replace("__CMDLINE_PROFILE_ARGS__", getattr(ctx, "cmdline_profile_args", ""))
    rendered = rendered.replace("__ENCRYPTION_ARGS__", getattr(ctx, "encryption_args", ""))
    if signing_enabled:
        policy = _avb_fail_policy(ctx)
        rendered = rendered.replace("__AVB_FAIL_POLICY__", policy)

    cache_dir = ctx.workspace / ".cache"
    cache_dir.mkdir(exist_ok=True)
    out = cache_dir / f"{src.stem}.generated.cmd"
    out.write_text(rendered, encoding="utf-8")
    return str(out)


def _aosp_lunch_target(ctx: BuildContext) -> str:
    variant = getattr(ctx, "build_variant", None) or ctx.rpi5_config.get("aosp", {}).get("build_variant", "userdebug")
    valid = {"eng", "userdebug", "user"}
    if variant not in valid:
        raise click.ClickException(
            f"Invalid aosp.build_variant={variant!r}. Expected one of: {', '.join(sorted(valid))}"
        )
    return f"aosp_rpi5_car-bp4a-{variant}"


def _format_c_array_hex(data: bytes, per_line: int = 10) -> str:
    lines: list[str] = []
    for i in range(0, len(data), per_line):
        chunk = data[i:i + per_line]
        lines.append("\t" + ", ".join(f"0x{byte:02x}" for byte in chunk) + ",")
    return "\n".join(lines)


def _sync_uboot_avb_root_key(ctx: BuildContext) -> None:
    if not ctx.avb_pubkey or not ctx.avb_pubkey.exists():
        raise click.ClickException(
            "Signing is enabled but avb.public_key is missing. "
            "Set avb.public_key to a valid AVB public key file."
        )

    avb_verify_c = ctx.uboot_dir / "common/avb_verify.c"
    if not avb_verify_c.exists():
        raise click.ClickException(f"U-Boot AVB source file not found: {avb_verify_c}")

    key_bytes = ctx.avb_pubkey.read_bytes()
    replacement = (
        f"static const unsigned char avb_root_pub[{len(key_bytes)}] = {{\n"
        f"{_format_c_array_hex(key_bytes)}\n"
        "};"
    )

    text = avb_verify_c.read_text(encoding="utf-8")
    pattern = re.compile(
        r"static const unsigned char avb_root_pub\[\d+\]\s*=\s*\{.*?\n\};",
        re.DOTALL,
    )
    if not pattern.search(text):
        raise click.ClickException("Failed to locate avb_root_pub[] in common/avb_verify.c")

    updated = pattern.sub(replacement, text, count=1)
    if updated != text:
        avb_verify_c.write_text(updated, encoding="utf-8")
        ctx.console.print(
            f"   Synced U-Boot AVB root key from {ctx.avb_pubkey} "
            f"({len(key_bytes)} bytes)"
        )
    else:
        ctx.console.print("   U-Boot AVB root key already matches configured public key")


def _enable_uboot_avb_kconfig(ctx: BuildContext) -> None:
    """
    Enable AVB command support and required dependencies in U-Boot config.

    AVB_VERIFY depends on LIBAVB/MMC/PARTITION_UUIDS/FASTBOOT, and LIBAVB
    depends on ANDROID_BOOT_IMAGE.
    """
    enable_symbols = [
        "CONFIG_ANDROID_BOOT_IMAGE",
        # CONFIG_FASTBOOT is hidden (no prompt). Enable via a selecting symbol.
        "CONFIG_UDP_FUNCTION_FASTBOOT",
        "CONFIG_LIBAVB",
        "CONFIG_AVB_VERIFY",
        "CONFIG_CMD_AVB",
    ]

    for symbol in enable_symbols:
        ctx.run(f"./scripts/config --enable {symbol}", cwd=ctx.uboot_dir)

    # Hidden FASTBOOT/AVB buffer symbols need concrete hex values; if left
    # empty, Kconfig restarts interactively and blocks non-interactive builds.
    ctx.run("./scripts/config --set-val CONFIG_FASTBOOT_BUF_ADDR 0x10000000", cwd=ctx.uboot_dir)
    ctx.run("./scripts/config --set-val CONFIG_AVB_BUF_ADDR 0x10000000", cwd=ctx.uboot_dir)
    ctx.run("./scripts/config --set-val CONFIG_FASTBOOT_BUF_SIZE 0x7000000", cwd=ctx.uboot_dir)
    ctx.run("./scripts/config --set-val CONFIG_AVB_BUF_SIZE 0x7000000", cwd=ctx.uboot_dir)

    ctx.run("CROSS_COMPILE=aarch64-linux-gnu- make olddefconfig", cwd=ctx.uboot_dir)

    dotconfig = ctx.uboot_dir / ".config"
    if not dotconfig.exists():
        raise click.ClickException(f"U-Boot config file missing after olddefconfig: {dotconfig}")

    cfg = dotconfig.read_text(encoding="utf-8")
    required = [
        "CONFIG_ANDROID_BOOT_IMAGE",
        "CONFIG_FASTBOOT",
        "CONFIG_LIBAVB",
        "CONFIG_AVB_VERIFY",
        "CONFIG_CMD_AVB",
        "CONFIG_FASTBOOT_BUF_ADDR=0x10000000",
        "CONFIG_AVB_BUF_ADDR=0x10000000",
    ]
    missing = []
    for sym in required:
        if "=" in sym:
            if sym not in cfg:
                missing.append(sym)
        else:
            if f"{sym}=y" not in cfg:
                missing.append(sym)
    if missing:
        raise click.ClickException(
            "Failed to enable required U-Boot AVB symbols:\n"
            + "\n".join(f"  - {sym}" for sym in missing)
            + "\n"
            "Check U-Boot Kconfig dependencies for this board defconfig "
            "(FASTBOOT is selected via UDP_FUNCTION_FASTBOOT)."
        )


def _build_kernel(ctx: BuildContext) -> None:
    """Cross-compile the kernel Image and deploy it to the prebuilt tree."""
    kernel_cfg = ctx.rpi5_config.get("kernel", {})
    repo_url = kernel_cfg.get("repo_url")

    if not repo_url:
        ctx.console.print(
            "[yellow]Skipping kernel build: kernel.repo_url not set in config "
            "(prebuilt Image will be used)[/]"
        )
        return

    if not ctx.kernel_dir.exists():
        raise click.ClickException(
            f"{ctx.kernel_dir.name}/ missing — run sync --code kernel first"
        )

    defconfig = kernel_cfg.get("defconfig", "android_rpi5_defconfig")
    cross = "ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-"

    ctx.console.print(f"   Using defconfig: {defconfig}")
    ctx.run(f"{cross} make {defconfig}", cwd=ctx.kernel_dir)

    # android_rpi5_defconfig sets CONFIG_EXTRA_FIRMWARE="regulatory.db" and
    # CONFIG_EXTRA_FIRMWARE_DIR="../vendor/brcm/rpi5/proprietary/vendor/firmware".
    # That relative path assumes the kernel lives inside the AOSP tree. Our
    # standalone checkout has no adjacent vendor/ directory, so clear the value
    # in .config before building. The regulatory.db is loaded from the vendor
    # partition at runtime; it does not need to be embedded in the kernel Image.
    ctx.run(
        "./scripts/config --set-str CONFIG_EXTRA_FIRMWARE ''",
        cwd=ctx.kernel_dir,
    )
    ctx.run(f"{cross} make olddefconfig", cwd=ctx.kernel_dir)
    ctx.run(f"{cross} make Image -j$(nproc)", cwd=ctx.kernel_dir)

    built_image = ctx.kernel_dir / "arch/arm64/boot/Image"
    if not built_image.exists():
        raise click.ClickException(
            f"Kernel build did not produce {built_image}. Check build output."
        )

    prebuilt_dir = ctx.aosp_dir / "device/brcm/rpi5-kernel"
    prebuilt_dir.mkdir(parents=True, exist_ok=True)
    ctx.run(f"cp {built_image} {prebuilt_dir / 'Image'}", cwd=ctx.workspace)
    ctx.console.print(f"   Deployed Image -> {prebuilt_dir / 'Image'}")


def run(ctx: BuildContext) -> None:
    """Build kernel and/or u-boot and/or AOSP depending on ctx flags."""
    ctx.console.print("[bold blue]Stage: Build[/]")

    if ctx.do_kernel:
        ctx.console.print("-> Building Kernel")
        _build_kernel(ctx)

    if ctx.do_uboot:
        if not ctx.uboot_dir.exists():
            raise click.ClickException(f"{ctx.uboot_dir.name}/ missing — run sync first")
        ctx.console.print("-> Building U-Boot")
        ctx.run("CROSS_COMPILE=aarch64-linux-gnu- make rpi_arm64_defconfig", cwd=ctx.uboot_dir)

        if ctx.signing_enabled:
            ctx.console.print("   Enabling AVB Kconfig options in U-Boot")
            _enable_uboot_avb_kconfig(ctx)
            _sync_uboot_avb_root_key(ctx)

        ctx.run("CROSS_COMPILE=aarch64-linux-gnu- make -j$(nproc)", cwd=ctx.uboot_dir)

        # Compile U-Boot boot script for Android
        if ctx.signing_enabled:
            ctx.console.print("-> Compiling U-Boot boot script with AVB support (boot_avb.scr)")
            boot_cmd = ctx.config_dir / "uboot/boot_avb.cmd"
            boot_scr = ctx.uboot_dir / "boot_avb.scr"
        else:
            ctx.console.print("-> Compiling U-Boot boot script (boot.scr)")
            boot_cmd = ctx.config_dir / "uboot/boot.cmd"
            boot_scr = ctx.uboot_dir / "boot.scr"

        mkimage = ctx.uboot_dir / "tools/mkimage"
        boot_cmd_src = _prepare_boot_script_source(ctx, str(boot_cmd), ctx.signing_enabled)
        ctx.run(
            f"{mkimage} -C none -A arm64 -T script -d {boot_cmd_src} {boot_scr}",
            cwd=ctx.uboot_dir,
        )

    if ctx.do_aosp and not (ctx.aosp_dir / ".repo").exists():
        raise click.ClickException("rpi5-aosp/ missing — run sync first")

    # Always compile boot script (needed for SD card regardless of whether U-Boot was rebuilt)
    # This ensures boot.scr exists even when running with --code aosp
    if ctx.do_aosp or ctx.do_uboot:
        if ctx.signing_enabled:
            boot_cmd = ctx.config_dir / "uboot/boot_avb.cmd"
            boot_scr = ctx.uboot_dir / "boot_avb.scr"
            script_name = "boot_avb.scr"
        else:
            boot_cmd = ctx.config_dir / "uboot/boot.cmd"
            boot_scr = ctx.uboot_dir / "boot.scr"
            script_name = "boot.scr"

        # Skip if already compiled during U-Boot build
        if not boot_scr.exists():
            # Try U-Boot's mkimage first, fall back to system mkimage
            mkimage = ctx.uboot_dir / "tools/mkimage"
            if not mkimage.exists():
                mkimage = "mkimage"  # system mkimage (from u-boot-tools package)
                ctx.console.print(f"-> Compiling U-Boot boot script using system mkimage ({script_name})")
            else:
                ctx.console.print(f"-> Compiling U-Boot boot script ({script_name})")

            # Ensure u-boot directory exists
            ctx.uboot_dir.mkdir(exist_ok=True)

            boot_cmd_src = _prepare_boot_script_source(ctx, str(boot_cmd), ctx.signing_enabled)
            ctx.run(
                f"{mkimage} -C none -A arm64 -T script -d {boot_cmd_src} {boot_scr}",
                cwd=ctx.workspace,
            )

    if ctx.signing_enabled and not ctx.do_uboot:
        ctx.console.print(
            "[yellow]Warning:[/] signing enabled with --code aosp. "
            "U-Boot AVB key is compiled-in; rebuild U-Boot after AVB key changes."
        )

    if ctx.do_aosp:
        ctx.console.print("-> Building AOSP")
        lunch_target = _aosp_lunch_target(ctx)
        ctx.console.print(f"   Using lunch target: {lunch_target}")
        encryption_mode = getattr(ctx, "encryption_mode", "disabled")
        if ctx.signing_enabled:
            extra_flags = "RPI5_ENABLE_AVB=true"
            if encryption_mode == "fbe":
                extra_flags += " RPI5_ENABLE_FBE=true"
            ctx.run(
                "bash -c 'source build/envsetup.sh && "
                f"lunch {lunch_target} && "
                f"{extra_flags} make bootimage systemimage vendorimage -j 6'",
                cwd=ctx.aosp_dir,
            )
        else:
            ctx.run(
                "bash -c 'source build/envsetup.sh && "
                f"lunch {lunch_target} && "
                "make bootimage systemimage vendorimage -j 6'",
                cwd=ctx.aosp_dir,
            )

    ctx.console.print("[green]Build completed[/]\n")

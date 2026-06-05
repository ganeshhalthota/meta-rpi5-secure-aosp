from __future__ import annotations

from pathlib import Path

import click
import pytest

import meta_rpi5_secure_aosp.stages.build as build_mod
from tests.conftest import make_stage_ctx


def test_avb_fail_policy_defaults_and_valid_values(tmp_path: Path) -> None:
    ctx = make_stage_ctx(tmp_path, rpi5_config={})
    assert build_mod._avb_fail_policy(ctx) == "fail_closed"

    ctx2 = make_stage_ctx(tmp_path, rpi5_config={"avb": {"uboot_fail_policy": "fail_open"}})
    assert build_mod._avb_fail_policy(ctx2) == "fail_open"


def test_avb_fail_policy_invalid_value_raises(tmp_path: Path) -> None:
    ctx = make_stage_ctx(tmp_path, rpi5_config={"avb": {"uboot_fail_policy": "bad"}})
    with pytest.raises(click.ClickException):
        build_mod._avb_fail_policy(ctx)


def test_prepare_boot_script_source_renders_policy(tmp_path: Path) -> None:
    ctx = make_stage_ctx(tmp_path, signing_enabled=True, rpi5_config={"avb": {"uboot_fail_policy": "fail_open"}})
    src = ctx.config_dir / "uboot/boot_avb.cmd"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("setenv avb __AVB_FAIL_POLICY__", encoding="utf-8")

    out = build_mod._prepare_boot_script_source(ctx, str(src), signing_enabled=True)
    rendered = Path(out).read_text(encoding="utf-8")

    assert "__AVB_FAIL_POLICY__" not in rendered
    assert "fail_open" in rendered


def test_prepare_boot_script_source_renders_mode_placeholders(tmp_path: Path) -> None:
    ctx = make_stage_ctx(
        tmp_path,
        signing_enabled=False,
        selinux_mode="enforcing",
        boot_state_args="androidboot.verifiedbootstate=green",
        cmdline_profile_args="quiet loglevel=4",
        encryption_args="androidboot.fde_mode=enabled",
    )
    src = ctx.config_dir / "uboot/boot.cmd"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_text("selinux=__SELINUX_MODE__ __CMDLINE_PROFILE_ARGS__ __BOOT_STATE_ARGS__ __ENCRYPTION_ARGS__", encoding="utf-8")

    out = build_mod._prepare_boot_script_source(ctx, str(src), signing_enabled=False)
    rendered = Path(out).read_text(encoding="utf-8")
    assert "__SELINUX_MODE__" not in rendered
    assert "__BOOT_STATE_ARGS__" not in rendered
    assert "__CMDLINE_PROFILE_ARGS__" not in rendered
    assert "__ENCRYPTION_ARGS__" not in rendered
    assert "selinux=enforcing" in rendered
    assert "quiet loglevel=4" in rendered
    assert "androidboot.verifiedbootstate=green" in rendered
    assert "androidboot.fde_mode=enabled" in rendered


def test_aosp_lunch_target_uses_variant_and_validates(tmp_path: Path) -> None:
    ctx = make_stage_ctx(tmp_path, build_variant="userdebug")
    assert build_mod._aosp_lunch_target(ctx) == "aosp_rpi5_car-bp4a-userdebug"

    bad = make_stage_ctx(tmp_path, build_variant="invalid")
    with pytest.raises(click.ClickException):
        build_mod._aosp_lunch_target(bad)


def test_sync_uboot_avb_root_key_updates_file(tmp_path: Path) -> None:
    ctx = make_stage_ctx(tmp_path)
    ctx.avb_pubkey.parent.mkdir(parents=True, exist_ok=True)
    ctx.avb_pubkey.write_bytes(b"\x01\x02\x03")
    avb_verify = ctx.uboot_dir / "common/avb_verify.c"
    avb_verify.parent.mkdir(parents=True, exist_ok=True)
    avb_verify.write_text(
        "static const unsigned char avb_root_pub[1] = {\n\t0x00,\n};\n",
        encoding="utf-8",
    )

    build_mod._sync_uboot_avb_root_key(ctx)
    updated = avb_verify.read_text(encoding="utf-8")
    assert "avb_root_pub[3]" in updated
    assert "0x01" in updated


def test_enable_uboot_avb_kconfig_runs_expected_commands(tmp_path: Path) -> None:
    ctx = make_stage_ctx(tmp_path)
    ctx.uboot_dir.mkdir(parents=True, exist_ok=True)
    (ctx.uboot_dir / ".config").write_text(
        "\n".join(
            [
                "CONFIG_ANDROID_BOOT_IMAGE=y",
                "CONFIG_FASTBOOT=y",
                "CONFIG_LIBAVB=y",
                "CONFIG_AVB_VERIFY=y",
                "CONFIG_CMD_AVB=y",
                "CONFIG_FASTBOOT_BUF_ADDR=0x10000000",
                "CONFIG_AVB_BUF_ADDR=0x10000000",
            ]
        ),
        encoding="utf-8",
    )

    build_mod._enable_uboot_avb_kconfig(ctx)
    cmds = [c for c, _ in ctx.run_calls]
    assert any("./scripts/config --enable CONFIG_LIBAVB" in c for c in cmds)
    assert any("make olddefconfig" in c for c in cmds)


def test_build_run_uboot_path_invokes_mkimage(tmp_path: Path) -> None:
    ctx = make_stage_ctx(
        tmp_path,
        do_uboot=True,
        do_aosp=False,
        signing_enabled=False,
        rpi5_config={"aosp": {"tag": "tag1"}},
    )
    ctx.uboot_dir.mkdir(parents=True, exist_ok=True)
    mkimage = ctx.uboot_dir / "tools/mkimage"
    mkimage.parent.mkdir(parents=True, exist_ok=True)
    mkimage.write_text("", encoding="utf-8")
    boot_cmd = ctx.config_dir / "uboot/boot.cmd"
    boot_cmd.parent.mkdir(parents=True, exist_ok=True)
    boot_cmd.write_text("boot", encoding="utf-8")

    build_mod.run(ctx)
    cmds = [c for c, _ in ctx.run_calls]
    assert any("make rpi_arm64_defconfig" in c for c in cmds)
    assert any("make -j$(nproc)" in c for c in cmds)
    assert any(" -T script -d " in c and "boot.scr" in c for c in cmds)


def test_build_run_aosp_requires_repo(tmp_path: Path) -> None:
    ctx = make_stage_ctx(tmp_path, do_uboot=False, do_aosp=True, signing_enabled=False, rpi5_config={"aosp": {"tag": "t"}})
    with pytest.raises(click.ClickException):
        build_mod.run(ctx)


def test_build_kernel_invokes_defconfig_and_image(tmp_path: Path) -> None:
    ctx = make_stage_ctx(
        tmp_path,
        do_kernel=True,
        do_uboot=False,
        do_aosp=False,
        rpi5_config={
            "kernel": {
                "repo_url": "https://example.invalid/kernel.git",
                "ref": "abc",
                "dir": "rpi5-kernel-src",
                "defconfig": "android_rpi5_defconfig",
            },
        },
    )
    ctx.kernel_dir.mkdir(parents=True, exist_ok=True)
    # Stub out the Image so the deploy step does not fail
    image_path = ctx.kernel_dir / "arch/arm64/boot/Image"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(b"\x00kernel\x00")
    prebuilt_dir = ctx.aosp_dir / "device/brcm/rpi5-kernel"
    prebuilt_dir.mkdir(parents=True, exist_ok=True)

    build_mod._build_kernel(ctx)

    cmds = [c for c, _ in ctx.run_calls]
    assert any("make android_rpi5_defconfig" in c for c in cmds)
    assert any("--set-str CONFIG_EXTRA_FIRMWARE" in c for c in cmds)
    assert any("make olddefconfig" in c for c in cmds)
    assert any("make Image -j$(nproc)" in c for c in cmds)
    assert any("cp" in c and "Image" in c for c in cmds)


def test_build_kernel_skipped_when_no_repo_url(tmp_path: Path) -> None:
    ctx = make_stage_ctx(
        tmp_path,
        do_kernel=True,
        do_uboot=False,
        do_aosp=False,
        rpi5_config={},  # No kernel: section
    )
    build_mod._build_kernel(ctx)  # Should not raise
    assert not ctx.run_calls  # No commands run


def test_build_kernel_raises_when_dir_missing(tmp_path: Path) -> None:
    ctx = make_stage_ctx(
        tmp_path,
        do_kernel=True,
        do_uboot=False,
        do_aosp=False,
        rpi5_config={
            "kernel": {
                "repo_url": "https://example.invalid/kernel.git",
                "ref": "abc",
                "dir": "rpi5-kernel-src",
            },
        },
    )
    # kernel_dir does not exist on disk
    with pytest.raises(click.ClickException, match="missing — run sync"):
        build_mod._build_kernel(ctx)


def test_build_run_kernel_before_aosp(tmp_path: Path) -> None:
    """Kernel build must appear before AOSP make in the command sequence."""
    ctx = make_stage_ctx(
        tmp_path,
        do_kernel=True,
        do_uboot=False,
        do_aosp=True,
        rpi5_config={
            "aosp": {"tag": "t", "build_variant": "userdebug"},
            "kernel": {
                "repo_url": "https://example.invalid/kernel.git",
                "ref": "abc",
                "dir": "rpi5-kernel-src",
                "defconfig": "android_rpi5_defconfig",
            },
        },
    )
    # Set up kernel dir with stubbed Image
    ctx.kernel_dir.mkdir(parents=True, exist_ok=True)
    image_path = ctx.kernel_dir / "arch/arm64/boot/Image"
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(b"\x00kernel\x00")
    prebuilt_dir = ctx.aosp_dir / "device/brcm/rpi5-kernel"
    prebuilt_dir.mkdir(parents=True, exist_ok=True)
    # Set up AOSP .repo to satisfy the check
    (ctx.aosp_dir / ".repo").mkdir(parents=True, exist_ok=True)
    # Set up boot.cmd for boot script compilation
    boot_cmd = ctx.config_dir / "uboot/boot.cmd"
    boot_cmd.parent.mkdir(parents=True, exist_ok=True)
    boot_cmd.write_text("boot", encoding="utf-8")

    build_mod.run(ctx)

    cmds = [c for c, _ in ctx.run_calls]
    kernel_idx = next(i for i, c in enumerate(cmds) if "make android_rpi5_defconfig" in c)
    aosp_idx = next(i for i, c in enumerate(cmds) if "lunch" in c or "bootimage" in c)
    assert kernel_idx < aosp_idx, "Kernel build must run before AOSP build"


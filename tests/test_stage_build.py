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

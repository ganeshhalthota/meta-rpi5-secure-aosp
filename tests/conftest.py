from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from rich.console import Console


def make_stage_ctx(tmp_path: Path, **overrides):  # noqa: ANN003
    run_calls: list[tuple[str, Path]] = []

    def _run(cmd: str, cwd: Path, silent: bool = False) -> None:  # noqa: ARG001
        run_calls.append((cmd, cwd))

    defaults = dict(
        project_root=tmp_path,
        config_dir=tmp_path / "config",
        workspace=tmp_path / "work",
        uboot_dir=tmp_path / "work" / "u-boot",
        aosp_dir=tmp_path / "work" / "rpi5-aosp",
        sdcard_dir=tmp_path / "work" / "sdcard",
        avb_key=tmp_path / "config" / "keys" / "avb.pem",
        avb_pubkey=tmp_path / "config" / "keys" / "avb_pkmd.bin",
        sdcard_config=tmp_path / "config" / "sdcard.yaml",
        sdcard_data={},
        rpi5_config={},
        do_uboot=True,
        do_aosp=True,
        signing_enabled=False,
        build_variant="userdebug",
        selinux_mode="permissive",
        boot_state_override="none",
        boot_state_args="",
        avb_fail_policy="fail_closed",
        cmdline_profile="legacy",
        cmdline_profile_args="",
        encryption_mode="disabled",
        encryption_args="",
        run=_run,
        console=Console(record=True),
        run_calls=run_calls,
    )
    defaults.update(overrides)

    ctx = SimpleNamespace(**defaults)
    ctx.config_dir.mkdir(parents=True, exist_ok=True)
    ctx.workspace.mkdir(parents=True, exist_ok=True)
    ctx.sdcard_dir.mkdir(parents=True, exist_ok=True)
    return ctx

from pathlib import Path

from rich.console import Console

from meta_rpi5_secure_aosp.context import BuildContext


def test_build_context_dataclass_fields() -> None:
    console = Console()

    ctx = BuildContext(
        project_root=Path("/tmp/project"),
        config_dir=Path("/tmp/project/config"),
        workspace=Path("/tmp/work"),
        uboot_dir=Path("/tmp/work/u-boot"),
        aosp_dir=Path("/tmp/work/rpi5-aosp"),
        sdcard_dir=Path("/tmp/work/sdcard"),
        avb_key=Path("/tmp/key.pem"),
        avb_pubkey=None,
        sdcard_config=Path("/tmp/project/config/sdcard.yaml"),
        sdcard_data={"partitions": []},
        rpi5_config={"aosp": {"tag": "test"}},
        do_uboot=True,
        do_aosp=False,
        signing_enabled=False,
        build_variant="userdebug",
        selinux_mode="permissive",
        boot_state_override="none",
        boot_state_args="",
        avb_fail_policy="fail_closed",
        cmdline_profile="legacy",
        cmdline_profile_args="",
        run=lambda cmd, cwd: None,
        console=console,
    )

    assert ctx.project_root == Path("/tmp/project")
    assert ctx.do_uboot is True
    assert ctx.do_aosp is False
    assert ctx.console is console

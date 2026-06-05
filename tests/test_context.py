from pathlib import Path

from rich.console import Console

from meta_rpi5_secure_aosp.context import BuildContext


def _make_ctx(**overrides) -> BuildContext:
    console = Console()
    defaults = dict(
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
        do_kernel=False,
        do_uboot=True,
        do_aosp=False,
        kernel_dir=Path("/tmp/work/rpi5-kernel-src"),
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
        run=lambda cmd, cwd: None,
        console=console,
    )
    defaults.update(overrides)
    return BuildContext(**defaults)


def test_build_context_dataclass_fields() -> None:
    ctx = _make_ctx()

    assert ctx.project_root == Path("/tmp/project")
    assert ctx.do_kernel is False
    assert ctx.do_uboot is True
    assert ctx.do_aosp is False
    assert ctx.kernel_dir == Path("/tmp/work/rpi5-kernel-src")
    assert isinstance(ctx.console, Console)


def test_build_context_avb_pubkey_accepts_path() -> None:
    pubkey = Path("/tmp/avb_pkmd.bin")
    ctx = _make_ctx(avb_pubkey=pubkey)
    assert ctx.avb_pubkey == pubkey


def test_build_context_run_callable_is_stored_and_invokable() -> None:
    calls: list[tuple] = []
    ctx = _make_ctx(run=lambda cmd, cwd: calls.append((cmd, cwd)))
    ctx.run("echo hi", Path("/tmp"))
    assert calls == [("echo hi", Path("/tmp"))]

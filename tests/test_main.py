from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

import meta_rpi5_secure_aosp.main as main_mod


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def _make_configs(
    tmp_path: Path,
    enable_signing: bool = False,
    include_encryption_partitions: bool = False,
) -> tuple[Path, Path]:
    config_dir = tmp_path / "config"
    sdcard_cfg = config_dir / "sdcard.yaml"
    sdcard_sign_cfg = config_dir / "sdcard_signed.yaml"
    parts = []
    if include_encryption_partitions:
        parts = [
            {"name": "userdata", "type": "ext4"},
            {"name": "metadata", "type": "ext4"},
        ]
    _write_yaml(sdcard_cfg, {"partitions": parts})
    _write_yaml(sdcard_sign_cfg, {"partitions": parts})
    _write_yaml(
        config_dir / "rpi5.yaml",
        {
            "aosp": {"tag": "android-14", "manifest_url": "https://example.invalid"},
            "avb": {"private_key": "keys/avb.pem"},
            "sdcard": {
                "enable_signing": enable_signing,
                "config": "sdcard.yaml",
                "sign_config": "sdcard_signed.yaml",
            },
            "encryption": {"mode": "disabled"},
            "uboot": {"dir": "u-boot-custom"},
        },
    )
    (config_dir / "keys").mkdir(parents=True, exist_ok=True)
    (config_dir / "keys" / "avb.pem").write_text("dummy", encoding="utf-8")
    return config_dir / "rpi5.yaml", sdcard_cfg


def test_get_default_paths_not_frozen() -> None:
    assert main_mod.get_default_workspace().exists()
    assert main_mod.get_default_config().name == "rpi5_aosp.yaml"


def test_main_stage_dispatch_without_sign(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    workspace = tmp_path / "work"
    workspace.mkdir()
    cfg, _ = _make_configs(tmp_path, enable_signing=False)

    calls: list[str] = []
    monkeypatch.setattr(main_mod.sync, "run", lambda ctx: calls.append("sync"))
    monkeypatch.setattr(main_mod.patch, "run", lambda ctx: calls.append("patch"))
    monkeypatch.setattr(main_mod.build, "run", lambda ctx: calls.append("build"))
    monkeypatch.setattr(main_mod.sign, "run", lambda ctx: calls.append("sign"))
    monkeypatch.setattr(main_mod.sdcard, "run", lambda ctx: calls.append("sdcard"))

    result = CliRunner().invoke(
        main_mod.main,
        ["--workspace", str(workspace), "--stage", "all", "--code", "all", "--config", str(cfg)],
    )

    assert result.exit_code == 0, result.output
    assert calls == ["sync", "patch", "build", "sdcard"]


def test_main_stage_dispatch_sdcard_sign_enabled(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    workspace = tmp_path / "work"
    workspace.mkdir()
    cfg, _ = _make_configs(tmp_path, enable_signing=True)

    calls: list[str] = []
    monkeypatch.setattr(main_mod.sync, "run", lambda ctx: calls.append("sync"))
    monkeypatch.setattr(main_mod.patch, "run", lambda ctx: calls.append("patch"))
    monkeypatch.setattr(main_mod.build, "run", lambda ctx: calls.append("build"))
    monkeypatch.setattr(main_mod.sign, "run", lambda ctx: calls.append("sign"))
    monkeypatch.setattr(main_mod.sdcard, "run", lambda ctx: calls.append("sdcard"))

    result = CliRunner().invoke(
        main_mod.main,
        ["--workspace", str(workspace), "--stage", "sdcard", "--code", "aosp", "--config", str(cfg)],
    )

    assert result.exit_code == 0, result.output
    assert calls == ["sign", "sdcard"]


def test_main_fails_when_sdcard_config_missing(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    cfg, _ = _make_configs(tmp_path, enable_signing=False)
    missing = tmp_path / "config" / "missing.yaml"

    result = CliRunner().invoke(
        main_mod.main,
        [
            "--workspace",
            str(workspace),
            "--stage",
            "sdcard",
            "--config",
            str(cfg),
            "--sdcard-config",
            str(missing),
        ],
    )

    assert result.exit_code != 0
    assert "sdcard config not found" in result.output


def test_main_mode_overrides_are_propagated_to_context(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    workspace = tmp_path / "work"
    workspace.mkdir()
    cfg, _ = _make_configs(tmp_path, enable_signing=False, include_encryption_partitions=True)
    captured: dict[str, object] = {}

    monkeypatch.setattr(main_mod.sync, "run", lambda ctx: None)
    monkeypatch.setattr(main_mod.patch, "run", lambda ctx: None)
    monkeypatch.setattr(
        main_mod.build,
        "run",
        lambda ctx: captured.update(
            {
                "build_variant": ctx.build_variant,
                "selinux_mode": ctx.selinux_mode,
                "boot_state_override": ctx.boot_state_override,
                "boot_state_args": ctx.boot_state_args,
                "avb_fail_policy": ctx.avb_fail_policy,
                "cmdline_profile": ctx.cmdline_profile,
                "cmdline_profile_args": ctx.cmdline_profile_args,
                "encryption_mode": ctx.encryption_mode,
                "encryption_args": ctx.encryption_args,
                "signing_enabled": ctx.signing_enabled,
            }
        ),
    )
    monkeypatch.setattr(main_mod.sign, "run", lambda ctx: None)
    monkeypatch.setattr(main_mod.sdcard, "run", lambda ctx: None)

    result = CliRunner().invoke(
        main_mod.main,
        [
            "--workspace",
            str(workspace),
            "--stage",
            "build",
            "--config",
            str(cfg),
            "--build-variant",
            "user",
            "--selinux-mode",
            "enforcing",
            "--boot-state-override",
            "green",
            "--cmdline-profile",
            "production",
            "--avb-fail-policy",
            "fail_closed",
            "--encryption-mode",
            "fde",
            "--signing",
            "enabled",
        ],
    )

    assert result.exit_code == 0, result.output
    assert captured == {
        "build_variant": "user",
        "selinux_mode": "enforcing",
        "boot_state_override": "green",
        "boot_state_args": "androidboot.verifiedbootstate=green androidboot.vbmeta.device_state=locked",
        "avb_fail_policy": "fail_closed",
        "cmdline_profile": "production",
        "cmdline_profile_args": "quiet loglevel=4",
        "encryption_mode": "fde",
        "encryption_args": "androidboot.fde_mode=enabled",
        "signing_enabled": True,
    }


def test_main_rejects_insecure_boot_state_without_opt_in(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    cfg, _ = _make_configs(tmp_path, enable_signing=False)

    result = CliRunner().invoke(
        main_mod.main,
        [
            "--workspace",
            str(workspace),
            "--stage",
            "build",
            "--config",
            str(cfg),
            "--boot-state-override",
            "orange",
        ],
    )

    assert result.exit_code != 0
    assert "allow-insecure-boot-state" in result.output


def test_main_defaults_build_variant_to_userdebug(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    workspace = tmp_path / "work"
    workspace.mkdir()
    cfg, _ = _make_configs(tmp_path, enable_signing=False)
    captured: dict[str, object] = {}

    monkeypatch.setattr(main_mod.sync, "run", lambda ctx: None)
    monkeypatch.setattr(main_mod.patch, "run", lambda ctx: None)
    monkeypatch.setattr(main_mod.build, "run", lambda ctx: captured.update({"build_variant": ctx.build_variant}))
    monkeypatch.setattr(main_mod.sign, "run", lambda ctx: None)
    monkeypatch.setattr(main_mod.sdcard, "run", lambda ctx: None)

    result = CliRunner().invoke(
        main_mod.main,
        ["--workspace", str(workspace), "--stage", "build", "--config", str(cfg)],
    )

    assert result.exit_code == 0, result.output
    assert captured["build_variant"] == "userdebug"


def test_main_rejects_fde_without_signing(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    cfg, _ = _make_configs(tmp_path, enable_signing=False)

    result = CliRunner().invoke(
        main_mod.main,
        [
            "--workspace",
            str(workspace),
            "--stage",
            "build",
            "--config",
            str(cfg),
            "--encryption-mode",
            "fde",
        ],
    )

    assert result.exit_code != 0
    assert "requires signing to be enabled" in result.output


def test_main_rejects_fde_when_required_partitions_missing(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    cfg, _ = _make_configs(tmp_path, enable_signing=True, include_encryption_partitions=False)

    result = CliRunner().invoke(
        main_mod.main,
        [
            "--workspace",
            str(workspace),
            "--stage",
            "build",
            "--config",
            str(cfg),
            "--encryption-mode",
            "fde",
        ],
    )

    assert result.exit_code != 0
    assert "requires SD card partitions" in result.output


def test_main_rejects_fbe_without_signing(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    cfg, _ = _make_configs(tmp_path, enable_signing=False)

    result = CliRunner().invoke(
        main_mod.main,
        [
            "--workspace",
            str(workspace),
            "--stage",
            "build",
            "--config",
            str(cfg),
            "--encryption-mode",
            "fbe",
        ],
    )

    assert result.exit_code != 0
    assert "requires signing to be enabled" in result.output


def test_main_rejects_fbe_when_required_partitions_missing(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    cfg, _ = _make_configs(tmp_path, enable_signing=True, include_encryption_partitions=False)

    result = CliRunner().invoke(
        main_mod.main,
        [
            "--workspace",
            str(workspace),
            "--stage",
            "build",
            "--config",
            str(cfg),
            "--encryption-mode",
            "fbe",
        ],
    )

    assert result.exit_code != 0
    assert "requires SD card partitions" in result.output


def test_main_fbe_mode_sets_correct_encryption_args(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    workspace = tmp_path / "work"
    workspace.mkdir()
    cfg, _ = _make_configs(tmp_path, enable_signing=True, include_encryption_partitions=True)
    captured: dict[str, object] = {}

    monkeypatch.setattr(main_mod.sync, "run", lambda ctx: None)
    monkeypatch.setattr(main_mod.patch, "run", lambda ctx: None)
    monkeypatch.setattr(
        main_mod.build,
        "run",
        lambda ctx: captured.update(
            {
                "encryption_mode": ctx.encryption_mode,
                "encryption_args": ctx.encryption_args,
            }
        ),
    )
    monkeypatch.setattr(main_mod.sign, "run", lambda ctx: None)
    monkeypatch.setattr(main_mod.sdcard, "run", lambda ctx: None)

    result = CliRunner().invoke(
        main_mod.main,
        [
            "--workspace",
            str(workspace),
            "--stage",
            "build",
            "--config",
            str(cfg),
            "--encryption-mode",
            "fbe",
            "--signing",
            "enabled",
        ],
    )

    assert result.exit_code == 0, result.output
    assert captured["encryption_mode"] == "fbe"
    assert captured["encryption_args"] == "androidboot.encryption_mode=fbe"


def test_main_invalid_encryption_mode_rejected(tmp_path: Path) -> None:
    workspace = tmp_path / "work"
    workspace.mkdir()
    cfg, _ = _make_configs(tmp_path, enable_signing=False)

    result = CliRunner().invoke(
        main_mod.main,
        [
            "--workspace",
            str(workspace),
            "--stage",
            "build",
            "--config",
            str(cfg),
            "--encryption-mode",
            "invalid_mode",
        ],
    )

    assert result.exit_code != 0

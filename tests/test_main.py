from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

import meta_rpi5_secure_aosp.main as main_mod


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


def _make_configs(tmp_path: Path, enable_signing: bool = False) -> tuple[Path, Path]:
    config_dir = tmp_path / "config"
    sdcard_cfg = config_dir / "sdcard.yaml"
    sdcard_sign_cfg = config_dir / "sdcard_signed.yaml"
    _write_yaml(sdcard_cfg, {"partitions": []})
    _write_yaml(sdcard_sign_cfg, {"partitions": []})
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

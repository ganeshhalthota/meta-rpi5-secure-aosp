from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import click
import pytest

import meta_rpi5_secure_aosp.stages.patch as patch_mod
from tests.conftest import make_stage_ctx


def test_resolve_aosp_project_dir_prefers_existing_mapping(tmp_path: Path) -> None:
    ctx = SimpleNamespace(aosp_dir=tmp_path / "aosp")
    (ctx.aosp_dir / "device/brcm/rpi5").mkdir(parents=True, exist_ok=True)

    resolved = patch_mod._resolve_aosp_project_dir(ctx, "device_brcm_rpi5")
    assert resolved == ctx.aosp_dir / "device/brcm/rpi5"


def test_already_applied_requires_forward_fail_and_reverse_ok(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    class R:
        def __init__(self, code: int):
            self.returncode = code
            self.stdout = ""
            self.stderr = ""

    responses = [R(1), R(0)]
    monkeypatch.setattr(patch_mod.subprocess, "run", lambda *a, **k: responses.pop(0))
    assert patch_mod._already_applied(tmp_path / "x.patch", tmp_path) is True


def test_check_patch_raises_click_exception_on_conflict(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    ctx = make_stage_ctx(tmp_path)

    class R:
        returncode = 1
        stderr = "conflict"

    monkeypatch.setattr(patch_mod.subprocess, "run", lambda *a, **k: R())
    with pytest.raises(click.ClickException):
        patch_mod._check_patch(ctx, tmp_path / "x.patch", tmp_path, "uboot")


def test_run_skips_when_no_patch_root(tmp_path: Path) -> None:
    ctx = make_stage_ctx(tmp_path, do_uboot=True, do_aosp=True)
    patch_mod.run(ctx)
    assert ctx.run_calls == []


def test_run_calls_apply_patch_dir_for_uboot_and_aosp(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    ctx = make_stage_ctx(tmp_path, do_uboot=True, do_aosp=True)
    patches_root = ctx.project_root / "patches"
    (patches_root / "uboot").mkdir(parents=True, exist_ok=True)
    (patches_root / "aosp" / "device_brcm_rpi5").mkdir(parents=True, exist_ok=True)
    (ctx.aosp_dir / "device/brcm/rpi5").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(patch_mod, "_is_git_project_under", lambda *a, **k: True)

    calls: list[tuple[Path, Path, str]] = []

    def _fake_apply(ctx_arg, patch_dir, target_dir, label):  # noqa: ANN001
        calls.append((patch_dir, target_dir, label))
        return True

    monkeypatch.setattr(patch_mod, "_apply_patch_dir", _fake_apply)
    patch_mod.run(ctx)

    labels = [c[2] for c in calls]
    assert "u-boot" in labels
    assert "aosp/device_brcm_rpi5" in labels

from __future__ import annotations

from pathlib import Path

import meta_rpi5_secure_aosp.stages.sync as sync_mod
from tests.conftest import make_stage_ctx


def test_sync_clones_uboot_and_inits_aosp(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    ctx = make_stage_ctx(
        tmp_path,
        rpi5_config={
            "aosp": {
                "tag": "tag1",
                "manifest_url": "https://example.invalid/manifest",
                "local_manifests": [{"filename": "lm.xml", "url": "https://example.invalid/lm.xml"}],
            },
            "uboot": {"repo_url": "https://example.invalid/u-boot.git", "ref": "main"},
        },
    )

    monkeypatch.setattr(sync_mod.shutil, "which", lambda _: None)
    sync_mod.run(ctx)

    cmds = [c for c, _ in ctx.run_calls]
    assert any("git clone https://example.invalid/u-boot.git u-boot" in c for c in cmds)
    assert any("python3 -m repo init" in c for c in cmds)
    assert any("curl -L -o lm.xml https://example.invalid/lm.xml" in c for c in cmds)
    assert any("python3 -m repo sync -j 8" in c for c in cmds)


def test_sync_updates_existing_trees(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    ctx = make_stage_ctx(
        tmp_path,
        rpi5_config={
            "aosp": {"tag": "tag1", "manifest_url": "u", "local_manifests": []},
            "uboot": {"repo_url": "u", "ref": "origin/master"},
        },
    )
    ctx.uboot_dir.mkdir(parents=True, exist_ok=True)
    (ctx.aosp_dir / ".repo").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(sync_mod.shutil, "which", lambda _: "/usr/bin/repo")
    sync_mod.run(ctx)

    cmds = [c for c, _ in ctx.run_calls]
    assert "git fetch --all --prune" in cmds
    assert "git clean -fdx" in cmds
    assert any(c.startswith("repo sync -j 8") for c in cmds)


def test_sync_kernel_clones_when_absent(tmp_path: Path) -> None:
    ctx = make_stage_ctx(
        tmp_path,
        do_kernel=True,
        rpi5_config={
            "aosp": {"tag": "t", "manifest_url": "u", "local_manifests": []},
            "kernel": {
                "repo_url": "https://example.invalid/kernel.git",
                "ref": "abc1234",
                "dir": "rpi5-kernel-src",
            },
        },
    )
    sync_mod.run(ctx)

    cmds = [c for c, _ in ctx.run_calls]
    assert any(
        "git clone https://example.invalid/kernel.git rpi5-kernel-src" in c for c in cmds
    )
    assert any("git checkout --force abc1234" in c for c in cmds)
    assert any("git reset --hard abc1234" in c for c in cmds)


def test_sync_kernel_updates_existing(tmp_path: Path) -> None:
    ctx = make_stage_ctx(
        tmp_path,
        do_kernel=True,
        rpi5_config={
            "aosp": {"tag": "t", "manifest_url": "u", "local_manifests": []},
            "kernel": {
                "repo_url": "https://example.invalid/kernel.git",
                "ref": "abc1234",
                "dir": "rpi5-kernel-src",
            },
        },
    )
    ctx.kernel_dir.mkdir(parents=True, exist_ok=True)
    sync_mod.run(ctx)

    cmds = [c for c, _ in ctx.run_calls]
    assert "git fetch --all --prune" in cmds
    assert any("git reset --hard abc1234" in c for c in cmds)
    # No clone when dir already exists
    assert not any("git clone" in c for c in cmds)


def test_sync_kernel_skipped_when_no_repo_url(tmp_path: Path) -> None:
    """When kernel.repo_url is absent, sync silently skips — no git commands run."""
    ctx = make_stage_ctx(
        tmp_path,
        do_kernel=True,
        rpi5_config={
            "aosp": {"tag": "t", "manifest_url": "u", "local_manifests": []},
            # No kernel: section at all
        },
    )
    sync_mod.run(ctx)

    cmds = [c for c, _ in ctx.run_calls]
    assert not any("kernel" in c.lower() and "git" in c for c in cmds)


def test_sync_kernel_not_triggered_when_do_kernel_false(tmp_path: Path) -> None:
    ctx = make_stage_ctx(
        tmp_path,
        do_kernel=False,
        rpi5_config={
            "aosp": {"tag": "t", "manifest_url": "u", "local_manifests": []},
            "kernel": {
                "repo_url": "https://example.invalid/kernel.git",
                "ref": "abc1234",
            },
        },
    )
    sync_mod.run(ctx)

    cmds = [c for c, _ in ctx.run_calls]
    assert not any("git clone" in c and "kernel" in c for c in cmds)

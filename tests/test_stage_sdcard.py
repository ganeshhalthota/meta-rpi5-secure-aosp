from __future__ import annotations

import pytest
from pathlib import Path

import yaml

import meta_rpi5_secure_aosp.stages.sdcard as sdcard_mod
from tests.conftest import make_stage_ctx


def _make_fake_disk_image_cls(ctx, captured: dict):
    class FakeDiskImage:
        def __init__(self, image_data: dict):
            captured["image_data"] = image_data

        def build(self) -> str:
            return str(ctx.sdcard_dir / "sd.img")

        def compress_tar_gz_split(self, split_size: int) -> list[str]:  # noqa: ARG002
            return ["p1"]

    return FakeDiskImage


def _write_simple_config(ctx, img_rel: Path) -> None:
    sd_cfg = {
        "image_name": "sd",
        "output_dir": "x",
        "partition_scheme": "gpt",
        "sdcard_size": 4096,
        "partitions": [{"name": "system", "img": str(img_rel)}],
    }
    ctx.sdcard_config.parent.mkdir(parents=True, exist_ok=True)
    ctx.sdcard_config.write_text(yaml.safe_dump(sd_cfg), encoding="utf-8")


def test_sdcard_run_prefers_signed_images_and_rewrites_extra_files(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    ctx = make_stage_ctx(tmp_path, signing_enabled=True)
    ctx.aosp_dir.mkdir(parents=True, exist_ok=True)
    ctx.uboot_dir.mkdir(parents=True, exist_ok=True)
    (ctx.project_root / "config" / "uboot").mkdir(parents=True, exist_ok=True)

    img_rel = Path("out/target/product/rpi5/system.img")
    img = ctx.aosp_dir / img_rel
    img.parent.mkdir(parents=True, exist_ok=True)
    img.write_bytes(b"orig")
    signed = img.with_suffix(".signed.img")
    signed.write_bytes(b"signed")

    sd_cfg = {
        "image_name": "sd",
        "output_dir": "x",
        "partition_scheme": "gpt",
        "sdcard_size": 4096,
        "partitions": [
            {
                "name": "system",
                "img": str(img_rel),
                "extra_files": [
                    {"src": "u-boot/boot.scr", "dst": "boot.scr"},
                    {"src": "config/uboot/boot.cmd", "dst": "boot.cmd"},
                    {"src": "misc/readme.txt", "dst": "readme.txt"},
                ],
            }
        ],
    }
    ctx.sdcard_config.parent.mkdir(parents=True, exist_ok=True)
    ctx.sdcard_config.write_text(yaml.safe_dump(sd_cfg), encoding="utf-8")

    captured: dict = {}

    class FakeDiskImage:
        def __init__(self, image_data: dict):
            captured["image_data"] = image_data

        def build(self) -> str:
            return str(ctx.sdcard_dir / "sd.img")

        def compress_tar_gz_split(self, split_size: int) -> list[str]:  # noqa: ARG002
            return ["p1", "p2"]

    monkeypatch.setattr(sdcard_mod, "DiskImage", FakeDiskImage)
    sdcard_mod.run(ctx)

    part = captured["image_data"]["partitions"][0]
    assert part["img"] == signed
    assert part["extra_files"][0]["src"] == ctx.uboot_dir / "boot.scr"
    assert part["extra_files"][1]["src"] == ctx.project_root / "config/uboot/boot.cmd"
    assert part["extra_files"][2]["src"] == ctx.workspace / "misc/readme.txt"


def test_sdcard_run_uses_unsigned_image_when_signing_disabled(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    ctx = make_stage_ctx(tmp_path, signing_enabled=False)
    ctx.aosp_dir.mkdir(parents=True, exist_ok=True)

    img_rel = Path("out/target/product/rpi5/system.img")
    img = ctx.aosp_dir / img_rel
    img.parent.mkdir(parents=True, exist_ok=True)
    img.write_bytes(b"orig")
    signed = img.with_suffix(".signed.img")
    signed.write_bytes(b"signed")

    _write_simple_config(ctx, img_rel)

    captured: dict = {}
    monkeypatch.setattr(sdcard_mod, "DiskImage", _make_fake_disk_image_cls(ctx, captured))
    sdcard_mod.run(ctx)

    assert captured["image_data"]["partitions"][0]["img"] == img


def test_sdcard_run_falls_back_to_unsigned_when_signed_missing(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    ctx = make_stage_ctx(tmp_path, signing_enabled=True)
    ctx.aosp_dir.mkdir(parents=True, exist_ok=True)

    img_rel = Path("out/target/product/rpi5/system.img")
    img = ctx.aosp_dir / img_rel
    img.parent.mkdir(parents=True, exist_ok=True)
    img.write_bytes(b"orig")
    # no .signed.img created

    _write_simple_config(ctx, img_rel)

    captured: dict = {}
    monkeypatch.setattr(sdcard_mod, "DiskImage", _make_fake_disk_image_cls(ctx, captured))
    sdcard_mod.run(ctx)

    assert captured["image_data"]["partitions"][0]["img"] == img


def test_sdcard_run_skips_src_rewrite_for_content_extra_files(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    ctx = make_stage_ctx(tmp_path, signing_enabled=False)
    ctx.aosp_dir.mkdir(parents=True, exist_ok=True)

    sd_cfg = {
        "image_name": "sd",
        "output_dir": "x",
        "partition_scheme": "gpt",
        "sdcard_size": 4096,
        "partitions": [
            {
                "name": "boot",
                "extra_files": [
                    {"content": "console=ttyAMA0", "dst": "cmdline.txt"},
                ],
            }
        ],
    }
    ctx.sdcard_config.parent.mkdir(parents=True, exist_ok=True)
    ctx.sdcard_config.write_text(yaml.safe_dump(sd_cfg), encoding="utf-8")

    captured: dict = {}
    monkeypatch.setattr(sdcard_mod, "DiskImage", _make_fake_disk_image_cls(ctx, captured))
    sdcard_mod.run(ctx)

    extra = captured["image_data"]["partitions"][0]["extra_files"][0]
    assert extra["content"] == "console=ttyAMA0"
    assert "src" not in extra


def test_sdcard_run_raises_when_config_missing(tmp_path: Path) -> None:
    ctx = make_stage_ctx(tmp_path)
    # sdcard_config path does not exist on disk
    with pytest.raises(OSError):
        sdcard_mod.run(ctx)

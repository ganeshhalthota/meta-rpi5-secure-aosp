from __future__ import annotations

from pathlib import Path

import click
import pytest
import yaml

import meta_rpi5_secure_aosp.stages.sign as sign_mod
from tests.conftest import make_stage_ctx


def test_derive_hash_algorithm_from_sign() -> None:
    assert sign_mod._derive_hash_algorithm_from_sign("SHA512_RSA4096") == "sha512"
    assert sign_mod._derive_hash_algorithm_from_sign("sha256_rsa2048") == "sha256"
    assert sign_mod._derive_hash_algorithm_from_sign("invalid") == "sha256"


def test_resolve_avb_algorithms_new_and_legacy() -> None:
    assert sign_mod._resolve_avb_algorithms({"sign_algorithm": "SHA512_RSA4096"}) == (
        "SHA512_RSA4096",
        "sha512",
    )
    assert sign_mod._resolve_avb_algorithms({"algorithm": "SHA256_RSA2048"}) == (
        "SHA256_RSA2048",
        "sha256",
    )
    assert sign_mod._resolve_avb_algorithms({"algorithm": "sha512"}) == (
        "SHA256_RSA4096",
        "sha512",
    )


def test_run_fs_tool_raises_on_failure(monkeypatch) -> None:  # noqa: ANN001
    class R:
        def __init__(self, code: int):
            self.returncode = code
            self.stdout = "bad"

    monkeypatch.setattr(sign_mod.subprocess, "run", lambda *a, **k: R(2))
    with pytest.raises(click.ClickException):
        sign_mod._run_fs_tool(["false"])


def test_shrink_ext4_image_checks_final_size(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    ctx = make_stage_ctx(tmp_path)
    calls: list[list[str]] = []
    monkeypatch.setattr(sign_mod, "_run_fs_tool", lambda cmd, ok_codes=None: calls.append(cmd))
    monkeypatch.setattr(sign_mod.AvbTool, "get_file_size", staticmethod(lambda _p: 1024))

    img = tmp_path / "x.img"
    img.write_bytes(b"x")
    sign_mod._shrink_ext4_image_for_avb(ctx, img, target_size_bytes=2048)
    assert any(cmd[0] == "e2fsck" for cmd in calls)


def test_sign_run_happy_path(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    ctx = make_stage_ctx(
        tmp_path,
        do_aosp=True,
        rpi5_config={"avb": {"sign_algorithm": "SHA256_RSA4096", "hash_algorithm": "sha256"}},
    )
    product_out = ctx.aosp_dir / "out/target/product/rpi5"
    product_out.mkdir(parents=True, exist_ok=True)
    (product_out / "system.img").write_bytes(b"sys")
    (product_out / "vendor.img").write_bytes(b"ven")
    ctx.sdcard_config.parent.mkdir(parents=True, exist_ok=True)
    ctx.sdcard_config.write_text(
        yaml.safe_dump({"partitions": [{"name": "system", "size": 1024}, {"name": "vendor", "size": 1024}]}),
        encoding="utf-8",
    )

    class FakeAvbTool:
        last_instance = None

        def __init__(self, **kwargs):  # noqa: ANN003
            self._cmd = "avbtool"
            self.added: list[Path] = []
            self.vbmeta_calls: list[tuple[Path, list[Path]]] = []
            FakeAvbTool.last_instance = self

        @staticmethod
        def get_file_size(path: Path) -> int:
            return path.stat().st_size

        def calc_max_image_size(self, partition_name: str, partition_size: int) -> int:  # noqa: ARG002
            return 4096

        def add_hashtree_footer(self, image: Path, partition_name: str, partition_size: int) -> None:  # noqa: ARG002
            self.added.append(image)

        def make_vbmeta_image(self, output: Path, include_images: list[Path]) -> None:
            self.vbmeta_calls.append((output, include_images))
            output.write_bytes(b"vbmeta")

    monkeypatch.setattr(sign_mod, "AvbTool", FakeAvbTool)
    monkeypatch.setattr(sign_mod.shutil, "copy2", lambda src, dst: dst.write_bytes(Path(src).read_bytes()))

    sign_mod.run(ctx)

    tool = FakeAvbTool.last_instance
    assert tool is not None
    assert len(tool.added) == 2
    assert (product_out / "vbmeta.img").exists()


def test_sign_run_requires_images_when_do_aosp(tmp_path: Path) -> None:
    ctx = make_stage_ctx(
        tmp_path,
        do_aosp=True,
        rpi5_config={"avb": {"sign_algorithm": "SHA256_RSA4096"}},
    )
    ctx.sdcard_config.parent.mkdir(parents=True, exist_ok=True)
    ctx.sdcard_config.write_text(yaml.safe_dump({"partitions": []}), encoding="utf-8")

    with pytest.raises(click.ClickException):
        sign_mod.run(ctx)

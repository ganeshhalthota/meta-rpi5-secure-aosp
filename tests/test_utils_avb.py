from __future__ import annotations

from pathlib import Path

import click
import pytest

from meta_rpi5_secure_aosp.utils.avb import AvbTool


def test_locate_prefers_built_avbtool(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    aosp_dir = tmp_path / "aosp"
    built = aosp_dir / "out/host/linux-x86/bin/avbtool"
    built.parent.mkdir(parents=True, exist_ok=True)
    built.write_text("", encoding="utf-8")
    monkeypatch.setattr("meta_rpi5_secure_aosp.utils.avb.shutil.which", lambda _: "/usr/bin/avbtool")
    assert AvbTool._locate(aosp_dir) == str(built)


def test_locate_fallback_to_path(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    aosp_dir = tmp_path / "aosp"
    monkeypatch.setattr("meta_rpi5_secure_aosp.utils.avb.shutil.which", lambda _: "/usr/bin/avbtool")
    assert AvbTool._locate(aosp_dir) == "avbtool"


def test_locate_raises_when_missing(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    aosp_dir = tmp_path / "aosp"
    monkeypatch.setattr("meta_rpi5_secure_aosp.utils.avb.shutil.which", lambda _: None)
    with pytest.raises(click.ClickException):
        AvbTool._locate(aosp_dir)


def test_add_hashtree_footer_builds_command(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    calls: list[tuple[str, Path]] = []
    aosp_dir = tmp_path / "aosp"
    built = aosp_dir / "out/host/linux-x86/bin/avbtool"
    built.parent.mkdir(parents=True, exist_ok=True)
    built.write_text("", encoding="utf-8")
    key = tmp_path / "key.pem"
    key.write_text("x", encoding="utf-8")

    tool = AvbTool(
        aosp_dir=aosp_dir,
        avb_key=key,
        run=lambda cmd, cwd: calls.append((cmd, cwd)),
        sign_algorithm="SHA512_RSA4096",
        hash_algorithm="sha512",
    )
    out = tmp_path / "v.img"
    tool.add_hashtree_footer(
        image=tmp_path / "system.signed.img",
        partition_name="system",
        partition_size=1234,
        vbmeta_output=out,
    )

    cmd, cwd = calls[0]
    assert "add_hashtree_footer" in cmd
    assert "--hash_algorithm sha512" in cmd
    assert "--output_vbmeta_image" in cmd
    assert cwd == tmp_path


def test_calc_max_image_size_parse_and_error(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    aosp_dir = tmp_path / "aosp"
    key = tmp_path / "key.pem"
    key.write_text("x", encoding="utf-8")
    monkeypatch.setattr(AvbTool, "_locate", staticmethod(lambda _: "avbtool"))
    tool = AvbTool(aosp_dir=aosp_dir, avb_key=key, run=lambda cmd, cwd: None)

    monkeypatch.setattr("meta_rpi5_secure_aosp.utils.avb.subprocess.check_output", lambda *a, **k: "info\n4096\n")
    assert tool.calc_max_image_size("system", 8192) == 4096

    monkeypatch.setattr("meta_rpi5_secure_aosp.utils.avb.subprocess.check_output", lambda *a, **k: "not-an-int")
    with pytest.raises(click.ClickException):
        tool.calc_max_image_size("system", 8192)


def test_get_file_size(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    path = tmp_path / "x.img"
    path.write_bytes(b"abc")
    monkeypatch.setattr("meta_rpi5_secure_aosp.utils.avb.subprocess.check_output", lambda *a, **k: "3")
    assert AvbTool.get_file_size(path) == 3

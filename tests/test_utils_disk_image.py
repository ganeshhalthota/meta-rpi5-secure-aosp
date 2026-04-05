from __future__ import annotations

from pathlib import Path

import pytest

from meta_rpi5_secure_aosp.utils.disk_image import DiskImage


def _image_data(tmp_path: Path) -> dict:
    return {
        "image_name": "sdcard",
        "output_dir": str(tmp_path),
        "partition_scheme": "gpt",
        "sdcard_size": 512,
        "partitions": [{"name": "boot", "size": 64, "format": "fat32", "flags": "boot"}],
    }


def test_validate_requires_keys(tmp_path: Path) -> None:
    data = _image_data(tmp_path)
    del data["partition_scheme"]
    with pytest.raises(ValueError):
        DiskImage(data)


def test_mbr_type_code_mapping() -> None:
    assert DiskImage._mbr_type_code("fat32") == "b"
    assert DiskImage._mbr_type_code("ext4") == "83"
    assert DiskImage._mbr_type_code("unknown") == "83"


def test_create_partitions_dispatch(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    disk = DiskImage(_image_data(tmp_path))
    calls: list[str] = []
    monkeypatch.setattr(disk, "_create_partitions_gpt", lambda: calls.append("gpt"))
    monkeypatch.setattr(disk, "_create_partitions_mbr", lambda: calls.append("mbr"))
    disk._create_partitions()
    assert calls == ["gpt"]

    disk._image_data["partition_scheme"] = "mbr"
    disk._create_partitions()
    assert calls == ["gpt", "mbr"]


def test_create_partitions_gpt_runs_sgdisk_commands(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    data = _image_data(tmp_path)
    data["partitions"] = [
        {"name": "boot", "partition_number": 1, "size": 64, "format": "fat32", "flags": "boot"},
        {"name": "system", "partition_number": 5, "format": "ext4"},
    ]
    disk = DiskImage(data)
    calls: list[list[str]] = []
    monkeypatch.setattr(disk, "_run_cmd", lambda cmd: calls.append(cmd))
    disk._create_partitions_gpt()

    joined = [" ".join(c) for c in calls]
    assert any("sgdisk -o" in c for c in joined)
    assert any("sgdisk -n 1:0:+64M -c 1:boot" in c for c in joined)
    assert any("sgdisk -t 1:ef00" in c for c in joined)
    assert any("sgdisk -n 5:0:0 -c 5:system" in c for c in joined)


def test_create_partitions_mbr_builds_fdisk_script(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    data = _image_data(tmp_path)
    data["partition_scheme"] = "mbr"
    data["partitions"] = [
        {"name": "boot", "partition_number": 1, "size": 64, "format": "fat32", "flags": "boot"},
        {"name": "system", "partition_number": 5, "size": 128, "format": "ext4"},
    ]
    disk = DiskImage(data)
    monkeypatch.setattr(disk, "_run_cmd", lambda cmd: None)

    seen_input: dict[str, str] = {}

    def _fake_run(cmd, **kwargs):  # noqa: ANN001
        if cmd[:2] == ["sudo", "fdisk"]:
            seen_input["script"] = kwargs["input"]
        class R:
            stdout = ""
        return R()

    monkeypatch.setattr("meta_rpi5_secure_aosp.utils.disk_image.subprocess.run", _fake_run)
    disk._create_partitions_mbr()

    script = seen_input["script"]
    assert "\no\n" in f"\n{script}"
    assert "\nn\np\n1\n" in script
    assert "\nn\ne\n" in script
    assert "\na\n1\n" in script
    assert "\nt\n1\nc\n" in script


def test_compress_tar_gz_split_returns_parts_sorted(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    disk = DiskImage(_image_data(tmp_path))
    disk._img_path = str(tmp_path / "sdcard.img")
    Path(disk._img_path).write_bytes(b"x")

    def _fake_run(cmd, shell, check):  # noqa: ANN001
        assert shell is True
        assert check is True
        (tmp_path / "sdcard.img.tar.gz.ab").write_bytes(b"2")
        (tmp_path / "sdcard.img.tar.gz.aa").write_bytes(b"1")

    monkeypatch.setattr("meta_rpi5_secure_aosp.utils.disk_image.subprocess.run", _fake_run)
    parts = disk.compress_tar_gz_split(split_size=64)
    assert parts == [
        str(tmp_path / "sdcard.img.tar.gz.aa"),
        str(tmp_path / "sdcard.img.tar.gz.ab"),
    ]

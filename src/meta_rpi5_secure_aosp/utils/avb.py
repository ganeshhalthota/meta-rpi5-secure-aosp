"""
Utility: Android Verified Boot (AVB) tool wrapper.

Wraps ``avbtool`` commands for signing partition images and building
combined vbmeta images.  Has no knowledge of the build pipeline or
BuildContext — it only needs the avbtool binary, the AVB key, and a
shell-runner callable.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Callable

import click


class AvbTool:
    """
    Thin wrapper around the ``avbtool`` binary.

    Parameters
    ----------
    aosp_dir:
        Path to the AOSP checkout.  The tool first looks for avbtool in
        ``<aosp_dir>/out/host/linux-x86/bin/avbtool``, then falls back to
        whatever is on ``$PATH``.
    avb_key:
        Path to the RSA private key PEM file used for signing.
    run:
        A callable with signature ``run(cmd: str, cwd: Path) -> None`` that
        executes a shell command (typically the ``_run`` helper from main.py
        passed through BuildContext).
    """

    def __init__(
        self,
        aosp_dir: Path,
        avb_key: Path,
        run: Callable[[str, Path], None],
        algorithm: str = "SHA256_RSA4096",
    ) -> None:
        self._cmd       = self._locate(aosp_dir)
        self._avb_key   = avb_key
        self._algorithm = algorithm
        self._run       = run
        self._workspace = aosp_dir.parent  # used as cwd for avbtool calls

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_hash_footer(
        self,
        image: Path,
        partition_name: str,
        partition_size: int,
        vbmeta_output: Path,
    ) -> None:
        """
        Add an AVB hash footer to *image* and write the per-partition
        vbmeta descriptor to *vbmeta_output*.

        The image is modified **in-place** — callers should pass a
        ``.signed`` copy rather than the original build output.
        """
        self._run(
            f"{self._cmd} add_hash_footer "
            f"--image {image} "
            f"--partition_name {partition_name} "
            f"--partition_size {partition_size} "
            f"--key {self._avb_key} "
            f"--algorithm {self._algorithm} "
            f"--output_vbmeta_image {vbmeta_output}",
            cwd=self._workspace,
        )

    def append_vbmeta_image(
        self,
        image: Path,
        partition_size: int,
        vbmeta_image: Path,
    ) -> None:
        """Append a vbmeta image to the end of *image*."""
        self._run(
            f"{self._cmd} append_vbmeta_image "
            f"--image {image} "
            f"--partition_size {partition_size} "
            f"--vbmeta_image {vbmeta_image}",
            cwd=self._workspace,
        )

    def make_vbmeta_image(self, output: Path, include_images: list[Path]) -> None:
        """
        Create a combined vbmeta image at *output* that chains descriptors
        from all images in *include_images*.
        """
        descriptors = " ".join(
            f"--include_descriptors_from_image {img}" for img in include_images
        )
        self._run(
            f"{self._cmd} make_vbmeta_image "
            f"--output {output} "
            f"--algorithm {self._algorithm} "
            f"--key {self._avb_key} "
            f"{descriptors}",
            cwd=self._workspace,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _locate(aosp_dir: Path) -> str:
        """
        Return the path/command for avbtool.

        Search order:
          1. ``<aosp_dir>/out/host/linux-x86/bin/avbtool``  (AOSP build output)
          2. ``avbtool`` on ``$PATH``

        Raises ``click.ClickException`` if neither is found.
        """
        built = aosp_dir / "out/host/linux-x86/bin/avbtool"
        if built.exists():
            return str(built)
        if shutil.which("avbtool"):
            return "avbtool"
        raise click.ClickException(
            "avbtool not found in AOSP build output or PATH. "
            "Build AOSP first or install the Android Verified Boot tools."
        )

    @staticmethod
    def get_file_size(path: Path) -> int:
        """Return the size of *path* in bytes (fallback when partition size is unknown)."""
        return int(
            subprocess.check_output(f"stat -c%s {path}", shell=True, text=True).strip()
        )

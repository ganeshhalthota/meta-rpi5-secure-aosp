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
        sign_algorithm: str = "SHA256_RSA4096",
        hash_algorithm: str = "sha256",
    ) -> None:
        self._cmd            = self._locate(aosp_dir)
        self._avb_key        = avb_key
        self._sign_algorithm = sign_algorithm
        self._hash_algorithm = hash_algorithm
        self._run            = run
        self._workspace      = aosp_dir.parent  # used as cwd for avbtool calls
        self._aosp_host_bin  = aosp_dir / "out/host/linux-x86/bin"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_hash_footer(
        self,
        image: Path,
        partition_name: str,
        partition_size: int,
        vbmeta_output: Path | None = None,
    ) -> None:
        """
        Add an AVB hash footer to *image* and optionally write the
        per-partition vbmeta descriptor to *vbmeta_output*.

        The image is modified **in-place** — callers should pass a
        ``.signed`` copy rather than the original build output.
        """
        cmd = (
            f"{self._cmd} add_hash_footer "
            f"--image {image} "
            f"--partition_name {partition_name} "
            f"--partition_size {partition_size} "
            f"--key {self._avb_key} "
            f"--algorithm {self._sign_algorithm}"
        )
        if vbmeta_output:
            cmd += f" --output_vbmeta_image {vbmeta_output}"

        self._run(self._with_path(cmd), cwd=self._workspace)

    def add_hashtree_footer(
        self,
        image: Path,
        partition_name: str,
        partition_size: int,
        vbmeta_output: Path | None = None,
    ) -> None:
        """
        Add an AVB hashtree footer (dm-verity) to *image* and optionally
        write the per-partition vbmeta descriptor to *vbmeta_output*.

        The image is modified **in-place**.
        """
        cmd = (
            f"{self._cmd} add_hashtree_footer "
            f"--image {image} "
            f"--partition_name {partition_name} "
            f"--partition_size {partition_size} "
            f"--key {self._avb_key} "
            f"--algorithm {self._sign_algorithm} "
            f"--hash_algorithm {self._hash_algorithm} "
            # f"--fec_num_roots 0"
        )
        if vbmeta_output:
            cmd += f" --output_vbmeta_image {vbmeta_output}"

        self._run(self._with_path(cmd), cwd=self._workspace)

    def calc_max_image_size(self, partition_name: str, partition_size: int) -> int:
        """
        Return the maximum payload size (bytes) that can fit in *partition_size*
        after AVB hashtree/FEC metadata is added.
        """
        cmd = (
            f"{self._cmd} add_hashtree_footer "
            f"--partition_name {partition_name} "
            f"--partition_size {partition_size} "
            f"--calc_max_image_size"
        )
        out = subprocess.check_output(
            self._with_path(cmd),
            shell=True,
            text=True,
            cwd=self._workspace,
        ).strip()
        try:
            return int(out.splitlines()[-1].strip())
        except (ValueError, IndexError) as e:
            raise click.ClickException(
                f"Failed to parse avbtool --calc_max_image_size output for {partition_name!r}: {out}"
            ) from e

    def extract_public_key(self, output: Path) -> None:
        """Extract the AVB public key from the RSA private key."""
        cmd = (
            f"{self._cmd} extract_public_key "
            f"--key {self._avb_key} "
            f"--output {output}"
        )
        self._run(self._with_path(cmd), cwd=self._workspace)

    def append_vbmeta_image(
        self,
        image: Path,
        partition_size: int,
        vbmeta_image: Path,
    ) -> None:
        """Append a vbmeta image to the end of *image*."""
        cmd = (
            f"{self._cmd} append_vbmeta_image "
            f"--image {image} "
            f"--partition_size {partition_size} "
            f"--vbmeta_image {vbmeta_image}"
        )
        self._run(self._with_path(cmd), cwd=self._workspace)

    def make_vbmeta_image(self, output: Path, include_images: list[Path]) -> None:
        """
        Create a combined vbmeta image at *output* that chains descriptors
        from all images in *include_images*.
        """
        descriptors = " ".join(
            f"--include_descriptors_from_image {img}" for img in include_images
        )
        cmd = (
            f"{self._cmd} make_vbmeta_image "
            f"--output {output} "
            f"--algorithm {self._sign_algorithm} "
            f"--key {self._avb_key} "
            f"{descriptors}"
        )
        self._run(self._with_path(cmd), cwd=self._workspace)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _with_path(self, cmd: str) -> str:
        """
        Prepend AOSP host bin directory to PATH for the command.

        This ensures tools like 'fec' are available when avbtool needs them.
        """
        if self._aosp_host_bin.exists():
            return f"export PATH={self._aosp_host_bin}:$PATH && {cmd}"
        return cmd

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

"""
Shared build context passed between all pipeline stages.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from rich.console import Console


@dataclass
class BuildContext:
    project_root: Path
    config_dir: Path
    workspace: Path
    uboot_dir: Path
    aosp_dir: Path
    sdcard_dir: Path
    avb_key: Path
    avb_pubkey: Path | None
    sdcard_config: Path
    sdcard_data: dict
    rpi5_config: dict
    do_uboot: bool
    do_aosp: bool
    signing_enabled: bool
    run: Callable[[str, Path], None]
    console: Console

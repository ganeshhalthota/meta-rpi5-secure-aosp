#!/usr/bin/env python3
"""
RPi5 Secure AOSP Builder - Smart stage + code selection
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.panel import Panel

from meta_rpi5_secure_aosp.context import BuildContext
from meta_rpi5_secure_aosp.stages import build, patch, sdcard, sign, sync


def get_default_workspace() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent.resolve()
    else:
        return Path(__file__).resolve().parent.parent.parent


def get_default_config() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent.resolve() / "config" / "rpi5_aosp.yaml"
    else:
        return Path(__file__).resolve().parent.parent.parent / "config" / "rpi5_aosp.yaml"


console = Console()


@click.command()
@click.option(
    "--workspace", "-w",
    type=click.Path(exists=True, file_okay=False, writable=True, path_type=Path),
    default=get_default_workspace,
    show_default="directory containing the binary",
    help="Workspace root (contains u-boot/, rpi5-aosp/, sdcard/)",
)
@click.option(
    "--stage", "-s",
    type=click.Choice(["all", "sync", "patch", "build", "sdcard"], case_sensitive=False),
    default="all",
    show_default=True,
    help="Pipeline stage to run: all, sync, patch, build, sdcard",
)
@click.option(
    "--code", "-c",
    type=click.Choice(["all", "uboot", "aosp"], case_sensitive=False),
    default="all",
    show_default=True,
    help="Which code to process: all, uboot, or aosp",
)
@click.option(
    "--config",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=get_default_config,
    show_default="<package-root>/config/rpi5_aosp.yaml",
    help="Path to the rpi5 build configuration yaml file",
)
@click.option(
    "--sdcard-config",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Path to the sdcard configuration yaml file (overrides rpi5_aosp.yaml default)",
)
def main(
    workspace: Path,
    stage: str,
    code: str,
    config: Path,
    sdcard_config: Path,
) -> None:
    """RPi5 Secure AOSP Builder — flexible stage + code selection."""

    # ------------------------------------------------------------------ #
    # Load rpi5 build config                                             #
    # ------------------------------------------------------------------ #
    with open(config, "r") as f:
        rpi5_config = yaml.safe_load(f)

    # Derive AVB key path from config (relative to the config file's directory)
    avb_key = (config.parent / rpi5_config["avb"]["private_key"]).resolve()

    # Derive AVB public key path from config if available (optional, with fallback to extraction)
    avb_pubkey = (
        (config.parent / rpi5_config["avb"]["public_key"]).resolve()
        if rpi5_config["avb"].get("public_key")
        else None
    )

    # Read signing flag from rpi5 config (authoritative source)
    signing_enabled = rpi5_config["sdcard"].get("enable_signing", False)

    # Resolve sdcard config: CLI override takes precedence, else auto-select based on signing flag
    if sdcard_config is None:
        if signing_enabled:
            sdcard_config = config.parent / rpi5_config["sdcard"]["sign_config"]
        else:
            sdcard_config = config.parent / rpi5_config["sdcard"]["config"]

    if not sdcard_config.exists():
        raise click.ClickException(f"sdcard config not found: {sdcard_config}")

    with open(sdcard_config, "r") as f:
        sdcard_data = yaml.safe_load(f)

    # ------------------------------------------------------------------ #
    # Resolve which code paths and stages are active                     #
    # ------------------------------------------------------------------ #
    do_uboot = code in {"all", "uboot"}
    do_aosp  = code in {"all", "aosp"}

    do_sync   = stage in {"all", "sync"}
    do_patch  = stage in {"all", "patch"}
    do_build  = stage in {"all", "build"}
    do_sdcard = stage in {"all", "sdcard"}

    do_sign = signing_enabled and stage in {"all", "sdcard"}

    aosp_tag = rpi5_config["aosp"]["tag"]

    # ------------------------------------------------------------------ #
    # Banner                                                             #
    # ------------------------------------------------------------------ #
    avb_pubkey_source = "from config" if avb_pubkey else "will extract from private key"
    console.print(Panel.fit(
        f"[bold magenta]RPi5 Secure AOSP Builder[/]\n"
        f"[dim]Workspace :[/] {workspace}\n"
        f"[dim]Stage     :[/] {stage}\n"
        f"[dim]Code      :[/] {code} -> "
        f"U-Boot={'Yes' if do_uboot else 'No'}, AOSP={'Yes' if do_aosp else 'No'}\n"
        f"[dim]Config    :[/] {config}\n"
        f"[dim]AOSP Tag  :[/] {aosp_tag}\n"
        f"[dim]AVB Key   :[/] {avb_key}\n"
        f"[dim]AVB PubKey:[/] {avb_pubkey_source}\n"
        f"[dim]SD Card   :[/] {sdcard_config}\n"
        f"[dim]Signing   :[/] {'Enabled' if signing_enabled else 'Disabled'} (by config)\n"
        f"[dim]Actions   :[/] "
        f"{'Sync, ' if do_sync else ''}"
        f"{'Patch, ' if do_patch else ''}"
        f"{'Build, ' if do_build else ''}"
        f"{'Sign, ' if do_sign else ''}"
        f"{'SD Card' if do_sdcard else ''}",
        border_style="magenta",
    ))

    # ------------------------------------------------------------------ #
    # Shell-runner helper                                                #
    # ------------------------------------------------------------------ #
    def _run(cmd: str, cwd: Path, silent: bool = False) -> None:
        if not silent:
            rel = cwd.relative_to(workspace) if cwd.is_relative_to(workspace) else cwd
            console.log(f"[bold green]+$[/] [dim]{rel}[/] {cmd}")
        subprocess.run(cmd, shell=True, check=True, cwd=cwd, text=True)

    # ------------------------------------------------------------------ #
    # Build shared context                                               #
    # ------------------------------------------------------------------ #
    ctx = BuildContext(
        workspace=workspace,
        uboot_dir=workspace / "u-boot",
        aosp_dir=workspace / "rpi5-aosp",
        sdcard_dir=workspace / "sdcard",
        avb_key=avb_key,
        avb_pubkey=avb_pubkey,
        sdcard_config=sdcard_config,
        sdcard_data=sdcard_data,
        rpi5_config=rpi5_config,
        do_uboot=do_uboot,
        do_aosp=do_aosp,
        signing_enabled=signing_enabled,
        run=_run,
        console=console,
    )

    # ------------------------------------------------------------------ #
    # Pipeline                                                           #
    # ------------------------------------------------------------------ #
    if do_sync:   sync.run(ctx)
    if do_patch:  patch.run(ctx)
    if do_build:  build.run(ctx)
    if do_sign:   sign.run(ctx)
    if do_sdcard: sdcard.run(ctx)

    console.print("[bold green]All requested stages completed successfully![/]")


if __name__ == "__main__":
    main()

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

_BUILD_VARIANTS = {"eng", "userdebug", "user"}
_SELINUX_MODES = {"permissive", "enforcing"}
_BOOT_STATE_OVERRIDES = {"none", "green", "orange"}
_AVB_FAIL_POLICIES = {"fail_closed", "fail_open"}
_CMDLINE_PROFILES = {"legacy", "debug", "production"}
_ENCRYPTION_MODES = {"disabled", "fde", "fbe"}


def _cfg_get(cfg: dict, *keys: str, default):  # noqa: ANN001
    value = cfg
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value


def _choice_or_fail(name: str, value: str, allowed: set[str]) -> str:
    if value not in allowed:
        allowed_list = ", ".join(sorted(allowed))
        raise click.ClickException(f"Invalid {name}={value!r}. Expected one of: {allowed_list}")
    return value


def _resolve_mode_options(
    rpi5_config: dict,
    *,
    build_variant_override: str | None,
    selinux_mode_override: str | None,
    boot_state_override: str | None,
    signing_override: str | None,
    avb_fail_policy_override: str | None,
    cmdline_profile_override: str | None,
    encryption_mode_override: str | None,
    allow_insecure_boot_state: bool,
) -> dict:
    build_variant = _choice_or_fail(
        "aosp.build_variant",
        (build_variant_override or _cfg_get(rpi5_config, "aosp", "build_variant", default="userdebug")).lower(),
        _BUILD_VARIANTS,
    )
    selinux_mode = _choice_or_fail(
        "boot.selinux_mode",
        (selinux_mode_override or _cfg_get(rpi5_config, "boot", "selinux_mode", default="permissive")).lower(),
        _SELINUX_MODES,
    )
    resolved_boot_state = _choice_or_fail(
        "boot.state_override",
        (boot_state_override or _cfg_get(rpi5_config, "boot", "state_override", default="none")).lower(),
        _BOOT_STATE_OVERRIDES,
    )
    avb_fail_policy = _choice_or_fail(
        "avb.uboot_fail_policy",
        (avb_fail_policy_override or _cfg_get(rpi5_config, "avb", "uboot_fail_policy", default="fail_closed")).lower(),
        _AVB_FAIL_POLICIES,
    )
    cmdline_profile = _choice_or_fail(
        "boot.cmdline_profile",
        (cmdline_profile_override or _cfg_get(rpi5_config, "boot", "cmdline_profile", default="legacy")).lower(),
        _CMDLINE_PROFILES,
    )
    encryption_mode = _choice_or_fail(
        "encryption.mode",
        (encryption_mode_override or _cfg_get(rpi5_config, "encryption", "mode", default="disabled")).lower(),
        _ENCRYPTION_MODES,
    )

    config_signing_enabled = bool(rpi5_config["sdcard"].get("enable_signing", False))
    if signing_override is None:
        signing_enabled = config_signing_enabled
    else:
        signing_enabled = signing_override == "enabled"

    allow_insecure = allow_insecure_boot_state or bool(
        _cfg_get(rpi5_config, "boot", "allow_insecure_boot_state", default=False)
    )
    if resolved_boot_state == "orange" and not allow_insecure:
        raise click.ClickException(
            "boot.state_override='orange' is insecure. "
            "Pass --allow-insecure-boot-state for test-only runs."
        )
    if signing_enabled and avb_fail_policy == "fail_open" and not allow_insecure:
        raise click.ClickException(
            "avb fail-open policy is insecure. "
            "Pass --allow-insecure-boot-state for test-only runs."
        )

    boot_state_args = {
        "none": "",
        "green": "androidboot.verifiedbootstate=green androidboot.vbmeta.device_state=locked",
        "orange": "androidboot.verifiedbootstate=orange androidboot.vbmeta.device_state=unlocked",
    }[resolved_boot_state]
    cmdline_profile_args = {
        "legacy": "",
        "debug": "ignore_loglevel loglevel=7",
        "production": "quiet loglevel=4",
    }[cmdline_profile]
    encryption_args = {
        "disabled": "",
        # Expose the selected mode to Android userspace and logs.
        "fde": "androidboot.fde_mode=enabled",
        "fbe": "androidboot.encryption_mode=fbe",
    }[encryption_mode]

    return {
        "build_variant": build_variant,
        "selinux_mode": selinux_mode,
        "boot_state_override": resolved_boot_state,
        "boot_state_args": boot_state_args,
        "avb_fail_policy": avb_fail_policy,
        "cmdline_profile": cmdline_profile,
        "cmdline_profile_args": cmdline_profile_args,
        "encryption_mode": encryption_mode,
        "encryption_args": encryption_args,
        "signing_enabled": signing_enabled,
    }


def _validate_encryption_prerequisites(mode_options: dict, sdcard_data: dict) -> None:
    mode = mode_options["encryption_mode"]
    if mode not in ("fde", "fbe"):
        return

    label = f"encryption.mode='{mode}'"

    if not mode_options["signing_enabled"]:
        raise click.ClickException(
            f"{label} requires signing to be enabled "
            "(set sdcard.enable_signing=true or pass --signing enabled)."
        )
    if mode_options["avb_fail_policy"] != "fail_closed":
        raise click.ClickException(
            f"{label} requires avb.uboot_fail_policy='fail_closed'."
        )

    parts = sdcard_data.get("partitions", [])
    part_names = {p.get("name") for p in parts if isinstance(p, dict)}
    missing = [name for name in ("userdata", "metadata") if name not in part_names]
    if missing:
        raise click.ClickException(
            f"{label} requires SD card partitions: "
            + ", ".join(missing)
            + f". Current config: {sorted(name for name in part_names if name)}"
        )


@click.command()
@click.option(
    "--workspace", "-w",
    type=click.Path(exists=True, file_okay=False, writable=True, path_type=Path),
    default=get_default_workspace,
    show_default="directory containing the binary",
    help="Workspace root (contains U-Boot source, rpi5-aosp/, sdcard/)",
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
@click.option(
    "--build-variant",
    type=click.Choice(sorted(_BUILD_VARIANTS), case_sensitive=False),
    default=None,
    help="Override AOSP lunch variant per run (eng/userdebug/user)",
)
@click.option(
    "--selinux-mode",
    type=click.Choice(sorted(_SELINUX_MODES), case_sensitive=False),
    default=None,
    help="Override androidboot.selinux mode for boot scripts",
)
@click.option(
    "--boot-state-override",
    type=click.Choice(sorted(_BOOT_STATE_OVERRIDES), case_sensitive=False),
    default=None,
    help="Override androidboot verified boot/device state for test scenarios",
)
@click.option(
    "--signing",
    type=click.Choice(["enabled", "disabled"], case_sensitive=False),
    default=None,
    help="Override sdcard.enable_signing per run",
)
@click.option(
    "--avb-fail-policy",
    type=click.Choice(sorted(_AVB_FAIL_POLICIES), case_sensitive=False),
    default=None,
    help="Override AVB U-Boot fail policy per run",
)
@click.option(
    "--cmdline-profile",
    type=click.Choice(sorted(_CMDLINE_PROFILES), case_sensitive=False),
    default=None,
    help="Optional boot cmdline profile (legacy/debug/production)",
)
@click.option(
    "--encryption-mode",
    type=click.Choice(sorted(_ENCRYPTION_MODES), case_sensitive=False),
    default=None,
    help="Select encryption mode (disabled/fde/fbe)",
)
@click.option(
    "--allow-insecure-boot-state",
    is_flag=True,
    default=False,
    help="Allow insecure test-only settings (orange state or AVB fail_open).",
)
def main(
    workspace: Path,
    stage: str,
    code: str,
    config: Path,
    sdcard_config: Path,
    build_variant: str | None,
    selinux_mode: str | None,
    boot_state_override: str | None,
    signing: str | None,
    avb_fail_policy: str | None,
    cmdline_profile: str | None,
    encryption_mode: str | None,
    allow_insecure_boot_state: bool,
) -> None:
    """RPi5 Secure AOSP Builder — flexible stage + code selection."""

    # ------------------------------------------------------------------ #
    # Load rpi5 build config                                             #
    # ------------------------------------------------------------------ #
    config_dir = config.parent.resolve()
    project_root = config_dir.parent

    with open(config, "r") as f:
        rpi5_config = yaml.safe_load(f)

    # Derive AVB key path from config (relative to the config file's directory)
    avb_key = (config.parent / rpi5_config["avb"]["private_key"]).resolve()

    # Resolve U-Boot source directory (relative to workspace)
    uboot_cfg = rpi5_config.get("uboot", {})
    uboot_dir_name = uboot_cfg.get("dir", "u-boot")
    uboot_dir = workspace / uboot_dir_name

    # Derive AVB public key path from config if available (optional, with fallback to extraction)
    avb_pubkey = (
        (config.parent / rpi5_config["avb"]["public_key"]).resolve()
        if rpi5_config["avb"].get("public_key")
        else None
    )

    mode_options = _resolve_mode_options(
        rpi5_config,
        build_variant_override=build_variant.lower() if build_variant else None,
        selinux_mode_override=selinux_mode.lower() if selinux_mode else None,
        boot_state_override=boot_state_override.lower() if boot_state_override else None,
        signing_override=signing.lower() if signing else None,
        avb_fail_policy_override=avb_fail_policy.lower() if avb_fail_policy else None,
        cmdline_profile_override=cmdline_profile.lower() if cmdline_profile else None,
        encryption_mode_override=encryption_mode.lower() if encryption_mode else None,
        allow_insecure_boot_state=allow_insecure_boot_state,
    )

    # Keep config map in sync so stage modules that read config remain compatible.
    rpi5_config.setdefault("aosp", {})["build_variant"] = mode_options["build_variant"]
    rpi5_config.setdefault("boot", {})["selinux_mode"] = mode_options["selinux_mode"]
    rpi5_config["boot"]["state_override"] = mode_options["boot_state_override"]
    rpi5_config["boot"]["cmdline_profile"] = mode_options["cmdline_profile"]
    rpi5_config.setdefault("avb", {})["uboot_fail_policy"] = mode_options["avb_fail_policy"]
    rpi5_config.setdefault("encryption", {})["mode"] = mode_options["encryption_mode"]
    rpi5_config.setdefault("sdcard", {})["enable_signing"] = mode_options["signing_enabled"]

    signing_enabled = mode_options["signing_enabled"]

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
    _validate_encryption_prerequisites(mode_options, sdcard_data)

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
        f"[dim]U-Boot Dir:[/] {uboot_dir}\n"
        f"[dim]AOSP Tag  :[/] {aosp_tag}\n"
        f"[dim]AVB Key   :[/] {avb_key}\n"
        f"[dim]AVB PubKey:[/] {avb_pubkey_source}\n"
        f"[dim]SD Card   :[/] {sdcard_config}\n"
        f"[dim]Signing   :[/] {'Enabled' if signing_enabled else 'Disabled'}\n"
        f"[dim]Variant   :[/] {mode_options['build_variant']}\n"
        f"[dim]SELinux   :[/] {mode_options['selinux_mode']}\n"
        f"[dim]Boot State:[/] {mode_options['boot_state_override']}\n"
        f"[dim]AVB Policy:[/] {mode_options['avb_fail_policy']}\n"
        f"[dim]Profile   :[/] {mode_options['cmdline_profile']}\n"
        f"[dim]Encryption:[/] {mode_options['encryption_mode']}\n"
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
        project_root=project_root,
        config_dir=config_dir,
        workspace=workspace,
        uboot_dir=uboot_dir,
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
        build_variant=mode_options["build_variant"],
        selinux_mode=mode_options["selinux_mode"],
        boot_state_override=mode_options["boot_state_override"],
        boot_state_args=mode_options["boot_state_args"],
        avb_fail_policy=mode_options["avb_fail_policy"],
        cmdline_profile=mode_options["cmdline_profile"],
        cmdline_profile_args=mode_options["cmdline_profile_args"],
        encryption_mode=mode_options["encryption_mode"],
        encryption_args=mode_options["encryption_args"],
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

"""
Stage: Patch
Applies git patch files (.patch) to the u-boot and/or AOSP source trees.

Patch directory layout expected under <workspace>/patches/:

  patches/
  ├── uboot/
  │   ├── 0001-some-fix.patch
  │   └── 0002-another-fix.patch
  └── aosp/
      ├── device_brcm_rpi5/          ← matches subdirectory inside rpi5-aosp/
      │   └── 0001-car-config.patch
      └── kernel_rpi/
          └── 0001-driver-fix.patch

Patches are applied with ``git am --3way`` so each patch becomes a proper
commit in the working tree.  Pass ``--check`` first to detect conflicts early.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import click

from meta_rpi5_secure_aosp.context import BuildContext

# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(ctx: BuildContext) -> None:
    """Apply all patches found under <workspace>/patches/ to the source trees."""
    ctx.console.print("\n[bold blue]Stage: Patch[/]")

    patches_root = ctx.workspace / "patches"

    if not patches_root.exists():
        ctx.console.print(
            f"[yellow]No patches directory found at {patches_root} — skipping patch stage.[/yellow]"
        )
        return

    applied_any = False

    if ctx.do_uboot:
        uboot_patches_dir = patches_root / "uboot"
        if uboot_patches_dir.exists():
            applied_any |= _apply_patch_dir(ctx, uboot_patches_dir, ctx.uboot_dir, label="u-boot")
        else:
            ctx.console.print(f"[dim]No uboot patch directory at {uboot_patches_dir} — skipping.[/dim]")

    if ctx.do_aosp:
        aosp_patches_dir = patches_root / "aosp"
        if aosp_patches_dir.exists():
            # Each subdirectory of patches/aosp/ maps to a project path inside rpi5-aosp/
            project_dirs = sorted(p for p in aosp_patches_dir.iterdir() if p.is_dir())
            if project_dirs:
                for project_patch_dir in project_dirs:
                    target_dir = ctx.aosp_dir / project_patch_dir.name
                    if not target_dir.exists():
                        ctx.console.print(
                            f"[yellow]Warning: AOSP project directory {target_dir} does not exist "
                            f"— skipping patches in {project_patch_dir.name}.[/yellow]"
                        )
                        continue
                    applied_any |= _apply_patch_dir(
                        ctx,
                        project_patch_dir,
                        target_dir,
                        label=f"aosp/{project_patch_dir.name}",
                    )
            else:
                ctx.console.print(f"[dim]No project subdirectories in {aosp_patches_dir} — skipping.[/dim]")
        else:
            ctx.console.print(f"[dim]No aosp patch directory at {aosp_patches_dir} — skipping.[/dim]")

    if applied_any:
        ctx.console.print("[green]Patch stage completed[/]\n")
    else:
        ctx.console.print("[dim]Patch stage: nothing to apply[/]\n")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _apply_patch_dir(ctx: BuildContext, patch_dir: Path, target_dir: Path, label: str) -> bool:
    """
    Apply all *.patch files in *patch_dir* to *target_dir* using ``git am --3way``.

    Returns True if at least one patch was applied, False if the directory was
    empty or contained no .patch files.
    """
    patches = sorted(patch_dir.glob("*.patch"))
    if not patches:
        ctx.console.print(f"[dim]  [{label}] No *.patch files found in {patch_dir}[/dim]")
        return False

    ctx.console.print(f"  [bold cyan][{label}][/] Applying {len(patches)} patch(es) from {patch_dir}")

    for patch_file in patches:
        ctx.console.print(f"    -> {patch_file.name}")
        _check_patch(ctx, patch_file, target_dir, label)
        ctx.run(f"git am --3way {patch_file}", cwd=target_dir)

    return True


def _check_patch(ctx: BuildContext, patch_file: Path, target_dir: Path, label: str) -> None:
    """
    Dry-run ``git apply --check`` before actually applying.
    Raises ClickException on failure so the user gets a clear error message.
    """
    result = subprocess.run(
        ["git", "apply", "--check", str(patch_file)],
        cwd=target_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise click.ClickException(
            f"[{label}] Patch {patch_file.name} would not apply cleanly:\n{result.stderr.strip()}\n"
            "Fix the patch or run 'git am --abort' in the target directory and retry."
        )

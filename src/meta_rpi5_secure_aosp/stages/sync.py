"""
Stage: Sync
Clones or updates the u-boot and AOSP source trees.
"""

from __future__ import annotations

import shlex
import shutil

from rich.progress import Progress, SpinnerColumn, TextColumn

from meta_rpi5_secure_aosp.context import BuildContext


def run(ctx: BuildContext) -> None:
    """Clone or update source trees based on ctx.do_kernel / ctx.do_uboot / ctx.do_aosp."""
    ctx.console.print("\n[bold blue]Stage: Sync[/]")

    aosp_cfg = ctx.rpi5_config["aosp"]
    tag = aosp_cfg["tag"]
    manifest_url = aosp_cfg["manifest_url"]
    local_manifests = aosp_cfg["local_manifests"]
    uboot_cfg = ctx.rpi5_config.get("uboot", {})
    uboot_repo_url = uboot_cfg.get("repo_url", "https://github.com/u-boot/u-boot.git")
    uboot_ref = uboot_cfg.get("ref", "origin/master")
    kernel_cfg = ctx.rpi5_config.get("kernel", {})
    kernel_repo_url = kernel_cfg.get("repo_url")
    kernel_ref = kernel_cfg.get("ref", "android-16.0")

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=ctx.console) as progress:

        if ctx.do_kernel:
            if not kernel_repo_url:
                ctx.console.print(
                    "[yellow]Skipping kernel sync: kernel.repo_url not set in config "
                    "(prebuilt Image will be used)[/]"
                )
            elif ctx.kernel_dir.exists():
                progress.add_task(f"Updating kernel at {kernel_ref}", total=None)
                ctx.run("git fetch --all --prune", cwd=ctx.kernel_dir)
                ctx.run(f"git checkout --force {shlex.quote(kernel_ref)}", cwd=ctx.kernel_dir)
                ctx.run(f"git reset --hard {shlex.quote(kernel_ref)}", cwd=ctx.kernel_dir)
            else:
                progress.add_task(f"Cloning kernel from {kernel_repo_url}", total=None)
                ctx.run(
                    f"git clone {shlex.quote(kernel_repo_url)} {shlex.quote(ctx.kernel_dir.name)}",
                    cwd=ctx.workspace,
                )
                ctx.run(f"git checkout --force {shlex.quote(kernel_ref)}", cwd=ctx.kernel_dir)
                ctx.run(f"git reset --hard {shlex.quote(kernel_ref)}", cwd=ctx.kernel_dir)

        if ctx.do_uboot:
            if ctx.uboot_dir.exists():
                progress.add_task(f"Updating u-boot at {uboot_ref}", total=None)
                ctx.run("git fetch --all --prune", cwd=ctx.uboot_dir)
                ctx.run(f"git checkout --force {shlex.quote(uboot_ref)}", cwd=ctx.uboot_dir)
                ctx.run(f"git reset --hard {shlex.quote(uboot_ref)}", cwd=ctx.uboot_dir)
                ctx.run("git clean -fdx", cwd=ctx.uboot_dir)
            else:
                progress.add_task(f"Cloning u-boot from {uboot_repo_url}", total=None)
                ctx.run(
                    f"git clone {shlex.quote(uboot_repo_url)} {shlex.quote(ctx.uboot_dir.name)}",
                    cwd=ctx.workspace,
                )
                ctx.run(f"git checkout --force {shlex.quote(uboot_ref)}", cwd=ctx.uboot_dir)
                ctx.run(f"git reset --hard {shlex.quote(uboot_ref)}", cwd=ctx.uboot_dir)
                ctx.run("git clean -fdx", cwd=ctx.uboot_dir)

        if ctx.do_aosp:
            repo_cmd = "repo" if shutil.which("repo") else "python3 -m repo"

            if (ctx.aosp_dir / ".repo").exists():
                progress.add_task("Syncing AOSP", total=None)
                ctx.run(
                    f"{repo_cmd} sync -j 8 --no-tags --optimized-fetch --current-branch",
                    cwd=ctx.aosp_dir,
                )
            else:
                ctx.aosp_dir.mkdir(parents=True, exist_ok=True)

                progress.add_task("repo init", total=None)
                ctx.run(
                    f"{repo_cmd} init "
                    f"-u {manifest_url} "
                    f"-b {tag} --depth=1 --no-tags --current-branch",
                    cwd=ctx.aosp_dir,
                )

                manifest_dir = ctx.aosp_dir / ".repo" / "local_manifests"
                manifest_dir.mkdir(parents=True, exist_ok=True)

                progress.add_task("Downloading + patching manifest", total=None)
                for lm in local_manifests:
                    ctx.run(
                        f"curl -L -o {lm['filename']} {lm['url']}",
                        cwd=manifest_dir,
                    )

                progress.add_task("Final repo sync", total=None)
                ctx.run(
                    f"{repo_cmd} sync -j 8 --no-tags --optimized-fetch --current-branch",
                    cwd=ctx.aosp_dir,
                )

    ctx.console.print("[green]Sync completed[/]\n")

# Project TODO

Last updated: 2026-04-03

## P0 (High Priority)

- [ ] Finalize AVB algorithm refactor
  - Owner: Coding
  - Status check:
    - Implemented: split `sign_algorithm` and `hash_algorithm` in AVB tooling and sign stage.
      - `src/meta_rpi5_secure_aosp/utils/avb.py`
      - `src/meta_rpi5_secure_aosp/stages/sign.py`
      - `config/rpi5_uboot_aosp.yaml`
    - Implemented: migrated legacy config and hardened fallback mapping.
      - `config/rpi5_aosp.yaml` now uses `avb.sign_algorithm` + `avb.hash_algorithm`
      - `src/meta_rpi5_secure_aosp/stages/sign.py` now classifies legacy `avb.algorithm` values:
        - sign token (`SHA*_RSA*`) -> treated as `sign_algorithm`
        - hash token (`sha*`) -> treated as `hash_algorithm`
    - Remaining:
      - Migrate legacy config `config/rpi5_aosp.yaml` from `avb.algorithm` to explicit `avb.sign_algorithm` + `avb.hash_algorithm`.
      - Harden backward-compat logic in sign stage so legacy `algorithm` values like `SHA256_RSA4096` are not misinterpreted as a hash algorithm.
  - Validation tasks:
    - [ ] Run signing flow using `config/rpi5_uboot_aosp.yaml` and verify `vbmeta.img` is produced.
    - [ ] Run signing flow using migrated `config/rpi5_aosp.yaml` and verify no regression.
    - [ ] Verify generated avbtool commands include correct `--algorithm` and `--hash_algorithm`.
  - Evidence to capture:
    - command output logs for both config paths
    - resulting image artifacts (`*.signed.img`, `vbmeta.img`)

- [ ] AVB validation test matrix on hardware (negative + positive cases)
  - Owner: Mixed (Coding + Validation)
  - Requested cases:
    - [ ] Use different AVB public key to validate failure behavior
    - [ ] 3.1 U-Boot AVB validation failure path
    - [ ] 3.2 `vbmeta` partition missing/corrupted data -> boot failure
    - [ ] 3.3 `vbmeta` from different build (hash mismatch) -> boot failure
  - Additional recommended cases:
    - [ ] Tamper one block in `system.img` after signing -> dm-verity failure at boot/runtime
    - [ ] Tamper one block in `vendor.img` after signing -> dm-verity failure
    - [ ] Remove `vbmeta` partition entry from SD-card layout -> verify expected fail-closed behavior
    - [ ] Corrupt vbmeta header/magic/version fields -> verify early AVB reject
    - [ ] Mismatch partition size between signed image assumptions and SD layout -> verify failure mode and logs
    - [ ] Validate AVB behavior with `fail_closed` vs `fail_open` policy placeholder in U-Boot script
    - [ ] Regression: known-good signed build must still boot successfully (control case)
  - Evidence to capture:
    - U-Boot logs, kernel boot logs, and pass/fail matrix in `notes/`

- [ ] Configurable build and security mode options (requested + extensions)
  - Owner: Coding
  - Requested options:
    - [ ] Build variant option: default `userdebug`, selectable `user` (and optional `eng` for development)
    - [ ] Boot state option: configurable `androidboot.verifiedbootstate` / device_state for test scenarios (orange/green and related states)
    - [ ] SELinux mode option: selectable `permissive` or `enforcing`
  - Additional recommended options:
    - [ ] CLI/config override for signing toggle (`sdcard.enable_signing`) per run
    - [ ] Explicit AVB fail policy option (`fail_closed` / `fail_open`) with clear defaulting
    - [ ] Configurable AVB algorithms (`sign_algorithm`, `hash_algorithm`) across all active configs
    - [ ] Optional boot cmdline profile switch (debug vs production verbosity)
  - Validation tasks:
    - [ ] Build variant:
      - [ ] `userdebug` remains default when no variant provided.
      - [ ] `user` build path completes and artifacts are generated.
      - [ ] Verify expected property differences (`ro.build.type`, debugability) on booted image.
    - [ ] Boot state option:
      - [ ] Verify configured state is reflected in kernel cmdline and runtime properties.
      - [ ] Ensure production-safe mode does not allow forcing insecure state unless explicitly enabled for testing.
      - [ ] Confirm AVB success/failure paths still set consistent state semantics.
    - [ ] SELinux mode option:
      - [ ] Verify cmdline reflects chosen mode (`androidboot.selinux=`...).
      - [ ] Enforcing mode boot test with service health checks.
      - [ ] Permissive mode boot test captures AVC denials for policy iteration.
    - [ ] Additional options:
      - [ ] Signing toggle override uses correct SD-card config and sign stage behavior.
      - [ ] AVB fail policy toggle follows expected reset/fallback behavior.
      - [ ] Boot cmdline profile toggle does not break normal boot.
  - Evidence to capture:
    - build logs for each option combination tested
    - U-Boot/kernel logs showing effective bootargs and verification path
    - runtime property dump (`getprop`) snapshots per mode
    - summary matrix in `notes/`

- [ ] TARA analysis (Threat Analysis and Risk Assessment)
  - Owner: User (non-coding)
  - Deliverable: threat model, attack tree/surface, mitigation mapping, residual risk list
  - Validation tasks:
    - [ ] Map each identified threat to an implemented or planned mitigation.
    - [ ] Assign severity and likelihood to each threat.
    - [ ] Review residual risks with mentor and record accepted risks.
  - Evidence to capture:
    - TARA document version in repo
    - review notes with action items

- [ ] Security feature roadmap after AVB enablement
  - Owner: Mixed
  - Scope:
    - SELinux enforcing validation
    - Full-disk encryption (FDE) feasibility/legacy compatibility assessment
    - File-based encryption (FBE) + metadata encryption
    - Rollback index / anti-rollback validation
    - Signed update flow hardening (before OTA rollout)
  - Validation tasks:
    - [ ] For each feature, define enablement preconditions and expected boot/runtime indicators.
    - [ ] Define at least one negative test and one recovery path.
    - [ ] Track dependency blockers (kernel config, hardware capability, userspace support).
  - Evidence to capture:
    - feature readiness checklist in `notes/`

- [ ] SE policy migration checklist for AOSP upgrades
  - Owner: Mixed
  - Scope:
    - policy compatibility when upgrading Android release tag
    - vendor/system sepolicy merge conflicts
    - neverallow rule breakage and policy API changes
  - Validation tasks:
    - [ ] Build with `SELINUX_IGNORE_NEVERALLOWS=false` and ensure no policy compile errors.
    - [ ] Run sepolicy diff between old and new release baselines and review new denials.
    - [ ] Verify boot completes with SELinux enforcing and no blocking `avc: denied` loops.
    - [ ] Confirm critical services/daemons start under enforcing mode after migration.
  - Evidence to capture:
    - build logs (policy compile)
    - boot logs (`dmesg`/`logcat`) with SELinux status and denials summary
    - migration note in `notes/`

## P1 (Important)

- [ ] Add automated regression coverage for AVB command construction
  - Owner: Coding
  - Target:
    - `src/meta_rpi5_secure_aosp/utils/avb.py`
    - `src/meta_rpi5_secure_aosp/stages/sign.py`
  - Goal: ensure command flags are stable for both new and legacy AVB config formats.
  - Validation tasks:
    - [ ] Add tests for both config formats (`sign_algorithm/hash_algorithm` and legacy `algorithm`).
    - [ ] Assert command strings include expected flags and values.
  - Evidence to capture:
    - test results output and changed test files

- [ ] Introduce a standard validation runner script for pre-merge checks
  - Owner: Coding
  - Expected baseline:
    - shell syntax checks
    - Python compile/import checks
    - lightweight stage smoke checks
  - Validation tasks:
    - [ ] Script exits non-zero when any check fails.
    - [ ] Script prints a clear pass/fail summary per check.
    - [ ] Dry-run on unchanged branch and changed branch.
  - Evidence to capture:
    - sample run logs for pass and fail paths

- [x] Remove conversational/transcript-style content from migrated reference docs
  - Owner: Coding
  - Primary file:
    - `notes/security/enabling_avb.md` (Referenced via `GEMINI.md`)
  - Validation tasks:
    - [ ] Remove chat-like narrative and keep only technical decisions/instructions.
    - [ ] Verify internal links/path references are valid post-cleanup.
  - Evidence to capture:
    - before/after diff and manual content review checklist

- [ ] Boot-up understanding study pack
  - Owner: User (non-coding)
  - Requested topics:
    - [ ] 4.1 Overall boot stages
    - [ ] 4.2 Boot stages within kernel
    - [ ] 4.3 Boot stages of Android
  - Suggested output:
    - One concise technical note per topic under `notes/`
  - Validation tasks:
    - [ ] Include sequence diagrams/timelines for each stage set.
    - [ ] Cross-reference each stage to actual logs from this platform.
    - [ ] Peer review with mentor for correctness.
  - Evidence to capture:
    - three notes under `notes/` with references

- [ ] Thesis LaTeX report
  - Owner: User (non-coding)
  - Deliverable:
    - `report/` folder structure
    - chapter outline and bibliography starter
    - traceability to experiments and validation logs
  - Validation tasks:
    - [ ] Compile LaTeX successfully with zero fatal errors.
    - [ ] Ensure each chapter maps to evidence in `notes/` and logs.
    - [ ] Maintain citation list for standards/specs/docs used.
  - Evidence to capture:
    - successful build artifact (`.pdf`)
    - chapter-to-evidence mapping table

## P3 (Last / After Core Security Work)

- [ ] OTA workstream (keep as final phase)
  - Owner: Mixed
  - Candidate scope:
    - Signed OTA payload generation and verification
    - A/B update flow (if platform constraints allow)
    - Update rollback and recovery scenarios
  - Validation tasks:
    - [ ] Successful signed OTA apply on known-good baseline.
    - [ ] Negative test: tampered payload rejected.
    - [ ] Recovery test: interrupted update recovers without bricking.
  - Evidence to capture:
    - OTA logs, slot state transitions, and post-update boot verification

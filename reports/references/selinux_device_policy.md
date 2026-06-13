# Write SELinux Device Policy — Android Documentation

- **URL:** https://source.android.com/docs/security/features/selinux/device-policy
- **Publisher:** Android Open Source Project (Google)
- **BibTeX key:** `selinux_device_policy`
- **Accessed:** January 2026

---

## Overview

Guide for writing device-specific SELinux policies during Android device bring-up.

## Device Bring-up Process

### Step 1 — Start in Permissive Mode

Begin in permissive mode: "denials are logged but not enforced." Allows policy development
without blocking other tasks.

### Step 2 — Transition to Enforcing Mode

Move to enforcing as quickly as possible — ideally within two weeks — to catch security issues
during real-world testing.

### Step 3 — Proper Labelling

Address denials by correctly labelling device files (block devices, audio, video, sensors)
using predefined types rather than granting broad permissions.

### Step 4 — Service Domains

Create dedicated SELinux domains for new init-launched services:
```
type foo, domain;
type foo_exec, exec_type, file_type;
init_daemon_domain(foo)
```

## Common Mistakes to Avoid

| Mistake | Correct Approach |
|---------|----------------|
| `allow { domain -untrusted_app }` (negation) | Explicitly allow only required domains |
| Debug permissions in production | Use `userdebug_or_eng` conditions |
| Device policy > 10% of total policy | Indicates overprivileged domains or dead code |
| Granting `dac_override` capability | Fix file permissions instead |

## Policy Size Guideline

Device customisations should represent only **5–10%** of total policy. Larger percentages
indicate overprivileged domains or dead code that must be removed.

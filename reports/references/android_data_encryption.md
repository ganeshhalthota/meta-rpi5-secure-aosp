# Android Data Encryption in Depth — Quarkslab

- **URL:** https://blog.quarkslab.com/android-data-encryption-in-depth.html
- **Publisher:** Quarkslab (security research blog)
- **BibTeX key:** `android_data_encryption`
- **Accessed:** March--April 2026

---

## Overview

Comprehensive technical analysis of Android File-Based Encryption (FBE) and its resilience
against sophisticated attackers with access to multiple software vulnerabilities.

## Background: Android FBE

Android requires FBE from Android 10 onward. FBE operates at the file level using Linux
`fscrypt`. Each file has its own encryption key.

### Encryption Categories

| Category | Availability |
|----------|-------------|
| Device Encrypted (DE) | Immediately after boot |
| Credential Encrypted (CE) | Only after user authentication |

## CE Key Derivation Mechanisms

### 1 — TrustZone with Gatekeeper

Gatekeeper trusted application validates user credentials and generates authentication tokens:
- Password stretching via `scrypt`
- HMAC-based verification
- Throttling to prevent brute-force
- Authentication tokens gate access to encryption-bound keys

### 2 — Security Chip with Weaver

Dedicated hardware stores key-value pairs in hardware slots with built-in throttling after
failed access attempts. Adds a hardware root of trust beyond TrustZone.

## Proof-of-Concept Demonstrations

### Gatekeeper PoC (MediaTek / Samsung A22)

- Boot ROM exploitation via MTKClient
- Patching bootloaders and TrustZone OS (TEEGRIS)
- Modifying Gatekeeper to accept any credentials
- Extracting encrypted synthetic password values
- Brute-force credential recovery from leaked cryptographic material

### Weaver PoC (Titan M)

- Exploited CVE-2022-20233 on Titan M security chip
- Obtained arbitrary memory read on chip
- Extracted stored Weaver keys from flash
- Performed credential brute-forcing against security implementation

## Key Findings

Well-designed architecture requires multiple exploitation vectors. Even after successful
exploitation, attackers face computational challenge of password cracking — strong passphrases
remain the final barrier.

## Relevance

Provides context for Android encryption architecture in the context of AVB and secure boot:
- AVB protects boot-time integrity; FBE protects data at rest
- Compromising one does not automatically compromise the other
- Credential security is orthogonal to verified boot state

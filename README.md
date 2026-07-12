# meta-rpi5-secure-aosp

**RPi5 Secure AOSP Builder - Docker Workflow**

This project provides an automated, containerized workflow to build a secure AOSP (Android Open Source Project) image for the Raspberry Pi 5. The tool orchestrates all necessary steps, from syncing source code (U-Boot + AOSP) to generating a final, signable SD card image with Android Verified Boot (AVB) integration.

## Project Goals

The overarching goal of the project is to replicate the commercial boot-up workflow and learn the essentials of a secure boot-up process. 

Currently, the project implements the following boot chain:
`RPi5 Bootloader -> U-Boot -> Kernel -> AOSP`

### High-Level Future Goals
1. Implement an A/B partition scheme for all partitions apart from the boot partition.
2. Include OP-TEE in the boot chain for enhanced security features.
3. Enable AOSP security features.
4. **Hardware & Boot-Level Security**: Integrate ARM Trusted Firmware-A (TF-A), Anti-Rollback Protection, and explore Raspberry Pi's native Hardware Root of Trust (OTP/eFuses).
5. **Kernel-Level Security**: Implement Kernel Hardening (KASLR, CFI) and enable the Linux Lockdown LSM.
6. **File System Security**: Configure File-Based Encryption (FBE) backed by a Hardware Keystore.
7. **AOSP System & HAL Security**: Bridge OP-TEE to Android user space via Keymaster/KeyMint and Gatekeeper HALs.
8. **User-Process Level Security**: Enforce strict SELinux policies (Enforcing Mode) and sandbox native processes using Seccomp-BPF.

## Documentation

- **[Development & Setup Guide](docs/development.md)**: Instructions on setting up the environment, docker wrapper usage, available commands, and troubleshooting.
- **[Architecture Overview](docs/architecture.md)**: Detailed explanation of the project's high-level and low-level design, including container orchestration, python builder workflow, and image generation process.

## Dependencies

For generating PDF reports from the LaTeX sources (via `scripts/generate_final_report.sh`), install the following packages on your host machine:

```bash
sudo apt install texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended latexmk
```

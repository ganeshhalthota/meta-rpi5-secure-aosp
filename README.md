# meta-rpi5-secure-aosp

**RPi5 Secure AOSP Builder - Docker Workflow**

This project provides an automated, containerized workflow to build a secure AOSP (Android Open Source Project) image for the Raspberry Pi 5. The tool orchestrates all necessary steps, from syncing source code (U-Boot + AOSP) to generating a final, signable SD card image with Android Verified Boot (AVB) integration.

## Documentation

- **[Development & Setup Guide](docs/development.md)**: Instructions on setting up the environment, docker wrapper usage, available commands, and troubleshooting.
- **[Architecture Overview](docs/architecture.md)**: Detailed explanation of the project's high-level and low-level design, including container orchestration, python builder workflow, and image generation process.

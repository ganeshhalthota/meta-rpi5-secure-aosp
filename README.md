```bash
# Development (Using wrapper script)
./docker_run.sh --help
./docker_run.sh all
./docker_run.sh sdcard --config ./myconfig.yaml --avb-key ./keys/mykey.pem

# After building with PyInstaller
dist/rpi5-build --help
dist/rpi5-build all
dist/rpi5-build sdcard --config /path/to/rpi5.yaml --avb-key /path/to/key.pem

# Interactive Shell
./docker_run.sh --shell
```

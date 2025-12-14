```bash
# Development (poetry)
poetry run rpi5-build --help
poetry run rpi5-build all
poetry run rpi5-build sdcard --config ./myconfig.yaml --avb-key ./keys/mykey.pem

# After building with PyInstaller
dist/rpi5-build --help
dist/rpi5-build all
dist/rpi5-build sdcard --config /path/to/rpi5.yaml --avb-key /path/to/key.pem
```

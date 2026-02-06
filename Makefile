.PHONY: help shell sync build sdcard all clean clean-all

# Default target
help:
	@echo "RPi5 AOSP Builder - Docker Wrapper"
	@echo ""
	@echo "Usage:"
	@echo "  make shell              - Start interactive shell in container"
	@echo "  make sync               - Sync U-Boot and AOSP sources"
	@echo "  make sync-uboot         - Sync only U-Boot"
	@echo "  make sync-aosp          - Sync only AOSP"
	@echo "  make build              - Build U-Boot and AOSP"
	@echo "  make build-uboot        - Build only U-Boot"
	@echo "  make build-aosp         - Build only AOSP"
	@echo "  make sdcard             - Generate SD card image"
	@echo "  make all                - Run all stages (sync + build + sdcard)"
	@echo "  make clean              - Remove generated images"
	@echo "  make clean-all          - Remove all build artifacts and workspace"
	@echo ""
	@echo "Advanced:"
	@echo "  make run CMD='...'      - Run custom command in container"
	@echo "  make binary             - Build PyInstaller binary"

# Start interactive shell
shell:
	@./docker_run.sh --shell

# Sync stages
sync:
	@./docker_run.sh /opt/run_src.sh --stage sync

sync-uboot:
	@./docker_run.sh /opt/run_src.sh --stage sync --code uboot

sync-aosp:
	@./docker_run.sh /opt/run_src.sh --stage sync --code aosp

# Build stages
build:
	@./docker_run.sh /opt/run_src.sh --stage build

build-uboot:
	@./docker_run.sh /opt/run_src.sh --stage build --code uboot

build-aosp:
	@./docker_run.sh /opt/run_src.sh --stage build --code aosp

# SD card image generation
sdcard:
	@./docker_run.sh /opt/run_src.sh --stage sdcard

# Run all stages
all:
	@./docker_run.sh /opt/run_src.sh --stage all

# Custom command
run:
	@./docker_run.sh $(CMD)

# Build PyInstaller binary
binary:
	@./docker_run.sh --build-binary

# Cleanup
clean:
	@echo "Removing generated SD card images..."
	@rm -rf work/sdcard/*.img
	@echo "Done!"

clean-all:
	@echo "WARNING: This will remove all build artifacts and workspace!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf work/; \
		echo "Workspace cleaned!"; \
	else \
		echo "Cancelled."; \
	fi

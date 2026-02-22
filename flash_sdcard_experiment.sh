#!/bin/bash

time sudo dd if=work/sdcard/rpi5-aosp-202602090017.img of=/dev/sdf bs=1M status=progress conv=fsync
time sudo dd if=work/sdcard/rpi5-aosp-202602090017.img of=/dev/sdf bs=4M status=progress conv=fsync
time sudo dd if=work/sdcard/rpi5-aosp-202602090017.img of=/dev/sdf bs=8M status=progress conv=fsync

time sudo dd if=work/sdcard/rpi5-aosp-202602090017.img of=/dev/sdf bs=1M status=progress conv=fsync oflag=direct
time sudo dd if=work/sdcard/rpi5-aosp-202602090017.img of=/dev/sdf bs=4M status=progress conv=fsync oflag=direct
time sudo dd if=work/sdcard/rpi5-aosp-202602090017.img of=/dev/sdf bs=8M status=progress conv=fsync oflag=direct

# Then verify manually (very slow unless you script a fast hash)
# sudo dd if=/dev/sdf bs=4M count=<size_in_4MiB_blocks> | xxhsum -c -

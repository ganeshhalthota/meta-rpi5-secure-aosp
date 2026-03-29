#!/bin/bash

# Setup required:
# sudo apt install minicom
# sudo usermod -aG dialout $USER

minicom -b 115200 -8 -D /dev/ttyACM0 -C ./logs/serial_$(date +%Y%m%d_%H%M%S).log

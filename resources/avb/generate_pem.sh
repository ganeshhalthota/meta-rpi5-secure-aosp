openssl genrsa -out avb_private_key.pem 4096
./work/rpi5-aosp/out/host/linux-x86/bin/avbtool extract_public_key --key resources/avb/avb_private_key.pem --output resources/avb/avb_public_key.bin

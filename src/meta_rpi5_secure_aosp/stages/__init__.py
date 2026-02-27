"""
Pipeline stage modules for RPi5 Secure AOSP Builder.

Stages (in execution order):
  sync   – clone / repo-sync source trees
  patch  – apply git patches to uboot and/or aosp
  build  – compile uboot and/or aosp
  sign   – sign images with AVB
  sdcard – assemble the SD-card image
"""

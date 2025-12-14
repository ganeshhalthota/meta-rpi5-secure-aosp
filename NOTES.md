aosp build partition table -

```bash
Disk /dev/sdg: 124735488 sectors, 59.5 GiB
Model: SD  Transcend
Sector size (logical/physical): 512/512 bytes
Disk identifier (GUID): D7BE3995-CBF7-4D7B-82D4-F3A4531764C8
Partition table holds up to 128 entries
Main partition table begins at sector 2 and ends at sector 33
First usable sector is 34, last usable sector is 124735454
Partitions will be aligned on 2048-sector boundaries
Total free space is 94737469 sectors (45.2 GiB)

Number  Start (sector)    End (sector)  Size       Code  Name
   1            2048          264191   128.0 MiB   0700  Microsoft basic data
   2          264192         5507071   2.5 GiB     8300  Linux filesystem
   3         5507072         6031359   256.0 MiB   8300  Linux filesystem
   4         6031360        29999999   11.4 GiB    8300  Linux filesystem
➜  ~ sudo fdisk -l /dev/sdg
Disk /dev/sdg: 59.48 GiB, 63864569856 bytes, 124735488 sectors
Disk model: SD  Transcend
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: dos
Disk identifier: 0x03e5da64

Device     Boot   Start      End  Sectors  Size Id Type
/dev/sdg1  *       2048   264191   262144  128M  c W95 FAT32 (LBA)
/dev/sdg2        264192  5507071  5242880  2.5G 83 Linux
/dev/sdg3       5507072  6031359   524288  256M 83 Linux
/dev/sdg4       6031360 29999999 23968640 11.4G 83 Linux

```

build root partition table -

```bash
Disk /dev/sdg: 62333952 sectors, 29.7 GiB
Model: SD  Transcend
Sector size (logical/physical): 512/512 bytes
Disk identifier (GUID): A1895DB1-BCA9-4C38-8D2A-4492F018CFEC
Partition table holds up to 128 entries
Main partition table begins at sector 2 and ends at sector 33
First usable sector is 34, last usable sector is 62333918
Partitions will be aligned on 1-sector boundaries
Total free space is 62022622 sectors (29.6 GiB)

Number  Start (sector)    End (sector)  Size       Code  Name
   1               1           65536   32.0 MiB    0700  Microsoft basic data
   2           65537          311296   120.0 MiB   8300  Linux filesystem
➜  ~ sudo fdisk -l /dev/sdg
Disk /dev/sdg: 29.72 GiB, 31914983424 bytes, 62333952 sectors
Disk model: SD  Transcend
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: dos
Disk identifier: 0x00000000

Device     Boot Start    End Sectors  Size Id Type
/dev/sdg1  *        1  65536   65536   32M  c W95 FAT32 (LBA)
/dev/sdg2       65537 311296  245760  120M 83 Linux

```

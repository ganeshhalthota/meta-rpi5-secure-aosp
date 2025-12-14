ll /prj/qct/asw/SABin/Linux
ll /prj/qct/asw/SABin/Linux/Parasoft/
ll /prj/qct/asw/SABin/Linux/Parasoft/cpptest_standard/
cd ghalthot/epics/11159_nord_qnx/08_cust/QXA.QA.7.0_hy11_build/qnx_ap/b
cd ghalthot/epics/11159_nord_qnx/08_cust/QXA.QA.7.0_hy11_build/qnx_ap/
source setenv_sdp800.sh 
make clean && make
cd ../
perl /pkg/qct/qctss/linux/ubuntu/22.04/bin/packit.pl -build=t -nodb -noreadme -file=QXA.QA.6.0.sdp800.txt -client=GEN5.QHS -release=109 -newformat=QXA.QA.7.0 -verbose
ll
perl /pkg/qct/qctss/linux/ubuntu/22.04/bin/packit.pl -build=t -nodb -noreadme -file=QXA.QA.7.0.sdp800.txt -client=GEN5.QHS -release=109 -newformat=QXA.QA.7.0 -verbose
cp -rp b/ hy11_compiletest/
rsync -aucv HY11_1/qnx_ap/ hy11_compiletest/qnx_ap/
rsync -aucv FEAT-API-QNX/qnx_ap/ hy11_compiletest/qnx_ap/
rsync -aucv FEAT-SRC-UFS/qnx_ap/ hy11_compiletest/qnx_ap/
rsync -aucv FEAT-SRC-PCI/qnx_ap/ hy11_compiletest/qnx_ap/
cd hy11_compiletest/qnx_ap/
source setenv_sdp800.sh --external $PWD/../../qnx_ap/qnx_bins/prebuilt_SDP800
make clean && make
find ../../qnx_ap/ -name plms
vim setenv_sdp800.sh 
ls
ls qnx_bins/
cp -rp ../../qnx_ap/qnx_bins/prebuilt_SDP800_floating_patches/ qnx_bins/
source setenv_sdp800.sh --external $PWD/../../qnx_ap/qnx_bins/prebuilt_SDP800
make clean && make
ll qnx_bins/
ll qnx_bins/prebuilt_SDP800_floating_patches/
ll qnx_bins/prebuilt_SDP800_floating_patches/target/
ll qnx_bins/prebuilt_SDP800_floating_patches/target/qnx/
tree qnx_bins/prebuilt_SDP800_floating_patches/target/qnx/
cd ../../qnx_ap/
source setenv_sdp800.sh 
less qnx_bins/qnx_toolchain.qxa_qa.pack 
cd ../
perl /pkg/qct/qctss/linux/ubuntu/22.04/bin/packit.pl -build=t -nodb -noreadme -file=QXA.QA.7.0.sdp800.txt -client=GEN5.QHS -release=109 -newformat=QXA.QA.7.0 -verbose
ll
find . -name prebuilt_SDP800_floating_patches
tree ./qnx_ap/qnx_bins/prebuilt_SDP800_floating_patches/target/qnx/
ll
cd FEAT-SRC-UFS/
tree FEAT-SRC-UFS/
cd ../
grep -rn 'plms' qnx_ap/target/filesets/
vim qnx_ap/target/filesets/qc.plt.plms.build
vim qnx_ap/target/filesets/nord.ivi.build
ll
rm -rf hy11_compiletest/
cd qnx_ap/
source setenv_sdp800.sh 
cd ../
perl /pkg/qct/qctss/linux/ubuntu/22.04/bin/packit.pl -build=t -nodb -noreadme -file=QXA.QA.7.0.sdp800.txt -client=GEN5.QHS -release=109 -newformat=QXA.QA.7.0 -verbose
rm -rf hy11_compiletest/
cp -rp b/ hy11_compiletest/
ll
rsync -aucv HY11_1/qnx_ap/ hy11_compiletest/qnx_ap/
cd hy11_compiletest/qnx_ap/
ls
source setenv_sdp800.sh -nqp --external $PWD/../../qnx_ap/qnx_bins/prebuilt_SDP800
make clean && make
cd ../../qnx_ap/
source setenv_sdp800.sh -nqp
cd ghalthot/epics/11159_nord_qnx/08_cust/QXA.QA.7.0_hy11_build
ll
cd qnx_ap/
diff setenv_sdp800.sh build/setenv_sdp800.sh 
cp build/setenv_sdp800.sh .
source setenv_sdp800.sh -nqp
cd ../hy11_compiletest/qnx_ap/
cp ../../qnx_ap/build/setenv_sdp800.sh .
vim setenv_sdp800.sh 
source setenv_sdp800.sh -nqp --external $PWD/../../qnx_ap/qnx_bins/prebuilt_SDP800
echo $MKIFS_PATH
vim target/filesets/nord.ivi.build 
grep -rn '__PLMS_ENABLE__' target/hypervisor/host/variant_config/
vim  target/hypervisor/host/variant_config/nord_la.txt
make clean && make
cat target/hypervisor/host/variant_config/nord_la.txt 
cd ../../qnx_ap/
less build/packfile/compiletest.qxa_qa.pack 
vim setenv_sdp800.sh 
source setenv_sdp800.sh 
cd ../
perl /pkg/qct/qctss/linux/ubuntu/22.04/bin/packit.pl -build=t -nodb -noreadme -file=QXA.QA.7.0.sdp800.txt -client=GEN5.QHS -release=109 -newformat=QXA.QA.7.0 -verbose
rm -rf FEAT-* HY* SRC/
rm -rf b/
ll
rm -rf hy11_compiletest/
perl /pkg/qct/qctss/linux/ubuntu/22.04/bin/packit.pl -build=t -nodb -noreadme -file=QXA.QA.7.0.sdp800.txt -client=GEN5.QHS -release=109 -newformat=QXA.QA.7.0 -verbose
ll
cp -rp b/ hy11_compiletest/
cd hy11_compiletest/qnx_ap/
ll
cd ../../
rsync -aucv HY11_1/qnx_ap/ hy11_compiletest/qnx_ap/
cd hy11_compiletest/qnx_ap/
l
source setenv_sdp800.sh --external $PWD/../../qnx_ap/qnx_bins/prebuilt_SDP800
l qnx_bins/
make clean && make
ll ../
cd ../../
ll
ll 
ll hy11_compiletest/qnx_ap/qnx_bins/
ll hy11_compiletest/qnx_ap/qnx_bins/prebuilt_SDP800_floating_patches/
cd hy11_compiletest/qnx_ap/
source setenv_sdp800.sh 
source setenv_sdp800.sh --external $PWD/../../qnx_ap/qnx_bins/prebuilt_SDP800
ll qnx_bins/prebuilt_SDP800_floating_patches/
echo $MKIFS_PATH
make
make images 2>&1 | tee make_images.log
ll qnx_bins/prebuilt_SDP800_floating_patches/qnx/aarch64le/
ll qnx_bins/prebuilt_SDP800_floating_patches/qnx/aarch64le/usr/sbin/plms
find . -name plms
ll ./install/aarch64le/etc/system/config/plms
source setenv_sdp800.sh -nqp --external $PWD/../../qnx_ap/qnx_bins/prebuilt_SDP800
make images 2>&1 | tee make_images.log
cd ../../
cd ghalthot/epics/11159_nord_qnx/08_cust/QXA.QA.7.0_hy11_build
ll
rm -rf FEAT-* b hy11_compiletest/ HY* SRC/
cd qnx_ap/
less build/packfile/compiletest.qxa_qa.pack 
source setenv_sdp800.sh 
cd ../
cd ghalthot/epics/11159_nord_qnx/08_cust/QXA.QA.7.0_hy11_build
perl /pkg/qct/qctss/linux/ubuntu/22.04/bin/packit.pl -build=t -nodb -noreadme -file=QXA.QA.7.0.sdp800.txt -client=GEN5.QHS -release=109 -newformat=QXA.QA.7.0 -verbose
cp -rp b/ hy11_compiletest/
rsync -aucv HY11_1/qnx_ap/ hy11_compiletest/qnx_ap/
cd hy11_compiletest/qnx_ap/
ll
source setenv_sdp800.sh -nqp --external $PWD/../../qnx_ap/qnx_bins/prebuilt_SDP800
echo $MKIFS_PATH
make clean && make 2>&1 | tee make.log
cd ../../qnx_ap/
cd ../
perl /pkg/qct/qctss/linux/ubuntu/22.04/bin/packit.pl -build=t -nodb -noreadme -file=QXA.QA.7.0.sdp800.txt -client=GEN5.QHS -release=109 -newformat=QXA.QA.7.0 -verbose
rm -rf hy11_compiletest/
cp -rp b/ hy11_compiletest/
rsync -aucv HY11_1/qnx_ap/ hy11_compiletest/qnx_ap/
cd hy11_compiletest/qnx_ap/
source setenv_sdp800.sh -nqp --external $PWD/../../qnx_ap/qnx_bins/prebuilt_SDP800
make clean && make 2>&1 | tee make.log
cd ../../
cd ghalthot/epics/11159_nord_qnx/08_cust/QXA.QA.7.0_hy11_build
ll
which packbuild.sh 
less /usr/bin/packbuild.sh
cd ghalthot/epics/11159_nord_qnx/08_cust/QXA.QA.7.0_hy11_build
packbuild.sh 
ll FEAT-SRC-UFS/qnx_ap/AMSS/platform/hwdrivers/wired_peripherals/storage/ufs_bsp/
ll FEAT-SRC-UFS/qnx_ap/AMSS/platform/hwdrivers/wired_peripherals/storage/ufs_bsp/public/amss/
cd ghalthot/epics/11159_nord_qnx/08_cust/QXA.QA.7.0_hy11_build
packbuild.sh 
cd ghalthot/epics/11159_nord_qnx/08_cust/QXA.QA.7.0_hy11_build
packbuild.sh 
cd HY11_CompileTest/
ll
cd qnx_ap/
ll
grep -rn 'storage/ufs_bsp/public/amss/' Makefile 
vim Makefile 
make 
source setenv_sdp800.sh --external $PWD/../../qnx_ap/qnx_bins/prebuilt_SDP800
make
cd ../../
less qnx_ap/target/target.qxa_qa.pack 
packbuild.sh 
vim /usr/bin/packbuild.sh 
cp /usr/bin/packbuild.sh .
vim packbuild.sh 
./packbuild.sh 
vim HY11_CompileTest/qnx_ap/Makefile 
cd qnx_ap/build
./copy_script.sh 
git d
cd ../
source setenv_sdp800.sh 
cd ../
./packbuild.sh 
tree FEAT-SRC-UFS/
find SRC/ -name '*.dep'
find SRC/ -name '*.pinfo'
find FEAT-API-QNX/ -name '*.pinfo'
find FEAT-API-QNX/ -name '*.dep'
find FEAT-SRC-UFS/ -name '*.dep'
./qnx_ap/tools/cmake/bin/cmake -v
./qnx_ap/tools/cmake/bin/cmake --version
which cmake
find SRC/ -name '*.o'
find SRC/ -name '*.dep'
find SRC/ -name '*.pinfo'
cd ghalthot/epics/11159_nord_qnx/08_cust/QXA.QA.7.0_hy11_build
ll
cp /usr/bin/packbuild.sh .
ll
./packbuild.sh 
vim HY11_CompileTest/qnx_ap/Makefile 
find SRC/ -name '*.dep'
find SRC/ -name '*.pinfo'
find SRC/ -name '*.o'
find FEAT-API-QN -name '*.o'
find FEAT-API-QNX -name '*.o'
find FEAT-SRC-UFS/ -name '*.o'
ll FEAT-SRC-UFS/qnx_ap/AMSS/platform/hwdrivers/wired_peripherals/storage/ufs_bsp/aarch64/so-le/
vim packbuild.sh 
packbuild.sh 
./packbuild.sh 
vim packbuild.sh 
./pack
./packbuild.sh 
vim packbuild.sh 
./pack
ll
ll pack
ll packtools/
./packbuild.sh 
find . -name vmm_vmid.h
vim packbuild.sh 
./packbuild.sh 
vim ./packbuild.sh 
which packbuild.sh 
rm pack
rm packbuild.sh 
ll
packbuild.sh 
cd ghalthot/epics/11159_nord_qnx/08_cust/QXA.QA.7.0_hy11_build
ll
packbuild.sh 
cd ghalthot/epics/11159_nord_qnx/08_cust/QXA.QA.7.0_hy11_build
packbuild.sh 
cd HY11_CompileTest/qnx_ap/
source setenv_sdp800.sh --external $PWD/../../qnx_ap/qnx_bins/prebuilt_SDP800
make clean
make
cd ../../
packbuild.sh 
cd qnx_ap/AMSS/
cd ../
make clean && make
ll AMSS/pcie_c2c/
source setenv_sdp800.sh 
make clean && make
find . -name vmm_vmid.h
ll AMSS/platform/qal/vm/clients/vmm_client/
cd ghalthot/epics/11159_nord_qnx/08_cust/QXA.QA.7.0_hy11_build
ll
packbuild.sh 
less qnx_ap/build/packtools/Makefile-HY11-TOP 
packbuild.sh 
cd ghalthot/epics/11159_nord_qnx/08_cust/QXA.QA.7.0_hy11_build
ll
less qnx_ap/qnx_bins/qnx_toolchain.qxa_qa.pack 
pack
packbuild.sh 
cd ghalthot/epics/11159_nord_qnx/08_cust/AU_QXA.QA.7.0_137_build
packbuild.sh 
find . -name sdp800_license
packbuild.sh 
less qnx_ap/qnx_bins/qnx_toolchain.qxa_qa.pack 
packbuild.sh 
cd ghalthot/epics/11159_nord_qnx/08_cust/QXA.QA.7.0_hy11_build
packbuild.sh 
cd ghalthot/epics/11159_nord_qnx/08_cust/AU_QXA.QA.7.0_153_build/
packbuild.sh 
find . -name asmoff_uefi.c
find . -name smp_start.S

find . -name camera_metadata_tags.h
find . -name autogen.mk
ll HY11_CompileTest/qnx_ap/AMSS/multimedia/qcamera/camera_qcx/camx-common/build/infrastructure/android/
ll HY11_CompileTest/qnx_ap/AMSS/multimedia/qcamera/camera_qcx/camx-common/build/infrastructure/android/common.mk 
vim HY11_CompileTest/qnx_ap/AMSS/multimedia/qcamera/camera_qcx/camx-common/build/infrastructure/
find . -name opencv_modules.hpp
find . -name features2d.hpp
find . -name whiner
ll FEAT-SRC-QCAMERA-C1SDZT/qnx_ap/AMSS/multimedia/qcamera/camera_qcx/camx/build/infrastructure/android/
ll FEAT-SRC-QCAMERA-C1SDZT/qnx_ap/AMSS/multimedia/qcamera/camera_qcx/camx/build/infrastructure/android/whiner/
find . -name tcpb
find . -name graphics.h
find . -name camera_metadata_stub.cpp
find . -name boost
find . -name boost | less
ll ./qnx_ap/dcservices/oss/
ll ./qnx_ap/dcservices/oss/dcservices_oss.qxa_qa.pack 
vim ./qnx_ap/dcservices/oss/dcservices_oss.qxa_qa.pack 
find . -name dcservices/
find . -name dcservices
find . -name hal_mdp.h 
find . -name mdp_commit.c 
find . -name /mdp_main.c
find . -name mdp_main.c
find . -name apt_fastrpc_test.h 
find . -name apt_api_suite
find . -name auto_sec_test
find . -name fastrpc_calc64_test
find . -name platform -type d
ll SRC/qnx_ap/test/platform
find . -name lemans_abl
find . -name qcgpio_test
find . -name scmi
find . -name runtime
find . -name nnc
find . -name prebuilt_SDP800_floating_patches
ll FEAT-API-QNX/qnx_ap/qnx_bins/
ll FEAT-API-QNX/qnx_ap/qnx_bins/prebuilt_SDP800_patches/
ll FEAT-API-QNX/qnx_ap/qnx_bins/prebuilt_SDP800_patches/target/
ll FEAT-API-QNX/qnx_ap/qnx_bins/prebuilt_SDP800_patches/target/qnx/usr/include/KHR/
ll FEAT-API-QNX/qnx_ap/qnx_bins/prebuilt_SDP800_patches/target/qnx/usr/include/WF/
find . -name script.c
find . -name audio_a2b
ll ./SRC/qnx_ap/AMSS/multimedia/audio/audio_elite/audio_driver/audio_a2b/
ll ./SRC/qnx_ap/AMSS/multimedia/audio/audio_elite/audio_driver/audio_a2b/prebuilt/
vim qnx_ap/test/multimedia/test_multimedia.qxa_qa.pack 
find . -name a2bstack
find . -name 'a2bstack*'
find . -name 'qcraft'
find . -name 'fadas_dev'
find . -name 'json.hpp'
find . -name 'merc_test_app'
tree ./SRC/qnx_ap/AMSS/multimedia/audio/audio_common/merc_test_app
find . -name adi_a2b_datatypes.h 
find . -name 'pal_*.h'
find . -name 'neon'
find . -name 'fadasHwFeatures.cpp'
find . -name fadas-noship
find . -name fadasTensor.h 
find . -name hal_mdp.h 
find . -name mdp_commit.c
find . -name mdp_main.c
find . -name *.deps
find qnx_ap/src/ -name *.deps
cd ghalthot/epics/11159-nord_qnx/00_impv/QXA.QA.7.0_impv_bld/qnx_ap/
cd build/
./copy_script.sh 
cd ../
source setenv_sdp800.sh 
cd build
./copy_script.sh 
cd ../
source setenv_sdp800.sh 
make clean && make
cd ../
packbuild.sh 
cd ghalthot/epics/11159-nord_qnx/02_build_rearch/QXA.QA.7.0_build_rearch-bld/
packbuild.sh 
ll qnx_ap/
cd qnx_ap/
source setenv_sdp800.sh 
cd ghalthot/epics/11159-nord_qnx/02_build_rearch/QXA.QA.7.0_build_rearch-bld/
packbuild.sh 
ls /pkg/qct/software/cmake/3.23.1/bin/
cd ghalthot/epics/11159-nord_qnx/02_build_rearch/QXA.QA.7.0_build_rearch-bld/
packbuild.sh 
ls /pkg/qct/software/
ls /pkg/qct/software/cmake/
cd ghalthot/epics/11159-nord_qnx/02_build_rearch/QXA.QA.7.0_build_rearch-bld/
packbuild.sh 
pushd qnx_ap/qnx_bins/
diff license/licenses prebuilt_SDP800_patches/patchset/sdp800_license/licenses 
cd -
packbuild.sh 
sed -i '/camera.qxa_qa.pack/d' qnx_ap/build/packfile/QXA.QA.7.0.txt 
cd qnx_ap/build
git s
git do packfile/
git co packfile/
git s
cd ghalthot/epics/11159-nord_qnx/02_build_rearch/QXA.QA.7.0_build_rearch-bld/
packbuild.sh 
which packbuild.sh 
cp /usr/bin/packbuild.sh .
mv packbuild.sh packb.sh
vim packb.sh 
./packb.sh 
vi qnx_ap/setenv_sdp800.sh 
cd ghalthot/epics/11159-nord_qnx/00_impv/QXA.QA.7.0_impv_bld/
packbuild.sh 
cd qnx_ap/target/
git d
git s
cd ghalthot/epics/11159-nord_qnx/02_build_rearch/QXA.QA.7.0_build_rearch-bld/
les qnx_ap/build/setenv_sdp800.sh 
less qnx_ap/build/setenv_sdp800.sh 
packbuild.sh 
ll
ll HY11_CompileTest/qnx_ap/setenv_sdp800.sh 
less HY11_CompileTest/qnx_ap/setenv_sdp800.sh 
packbuild.sh 
cd ghalthot/epics/11159-nord_qnx/02_build_rearch/QXA.QA.7.0_build_rearch-bld/
packbuild.sh 
cd ../
cd ghalthot/epics/11159-nord_qnx/02_build_rearch/QXA.QA.7.0_build_rearch-bld/
packbuild.sh 
cd qnx_ap/build
git log -1
git s
git d
cd ../
cd build
./copy_script.sh 
cd ../
source setenv_
source setenv_sdp800.sh 
vim packfile/QXA.QA.7.0.txt 
cd ghalthot/epics/11159-nord_qnx/00_impv/QXA.QA.7.0_impv_bld/
packbuild.sh 
cd qnx_ap/
source setenv_sdp800.sh 
cd target/
git d
git d filesets/qc.plt.common.mifs.files.build
git d hypervisor/host/build_files/tftp.build.tmpl
cd ../
make images
find qnx_bins/ -name '*ldd*'
which ldd
ldd install/aarch64le/bin/spi_service
make images
less target/filesets/qc.plt.common.mifs.files.build 
make images
grep -rn '"filePermissions.txt' target/filesets/
grep -rn 'filePermissions.txt' target/filesets/
ll target/filesets/filePermissions.txt 
cd build
git lg
cd ../
ll target/hypervisor/host/out_nord/
ll target/hypervisor/host/out_nord/ifs*
cd ../../
ll
cd ghalthot/epics/11159-nord_qnx/00_impv/QXA.QA.7.0_um-bld/
which packbuild.sh 
cp /usr/bin/packbuild.sh .
vim packbuild.sh 
./packbuild.sh 
cd qnx_ap/
source setenv_sdp800.sh 
less target/filesets/qc.plt.common.mifs.files.build 
cd target/
git d
git s
git d filesets/qc.plt.common.mifs.files.build
git d hypervisor/host/build_files/tftp.build.tmpl
ll
vim Makefile 
less ../Makefile 
make install
git s
git d filesets/qc.plt.common.mifs.files.build
git d 
git s
cd ghalthot/epics/11159-nord_qnx/00_impv/QXA.QA.7.0_um-bld/
vim ./packbuild.sh 
ll
cd ghalthot/epics/11159-nord_qnx/00_impv/QXA.QA.7.0_um-bld
ll
ll ../
cd ghalthot/epics/11159-nord_qnx/00_impv/
ll
cd QXA.QA.7.0_um-bld
../packbuild.sh 
less qnx_ap/target/filesets/qc.plt.common.mifs.files.build 
../packbuild.sh 
cd qnx_ap/target/
git d
git s
git diff --cached 
cd ../
cd target/
git s
git d --cached 
cd ghalthot/epics/11159-nord_qnx/00_impv/
cd QXA.QA.7.0_impv/
cd qnx_ap/build/
./copy_script.sh 
cd ../
source setenv_sdp800.sh 
make clean && make
vim setenv_sdp800.sh 
source setenv_sdp800.sh --np 8
make clean && make
cd ghalthot/epics/11159-nord_qnx/00_impv/QXA.QA.7.0_um-bld/
vim ../packbuild.sh 
less qnx_ap/build/setenv_sdp800.sh 
vim ../packbuild.sh 
man tar
ls
vim ../packbuild.sh 
cd qnx_ap/
source setenv_sdp800.sh 
cp ../../QXA.QA.7.0_um/qnx_ap/target/filesets/qc.plt.common.mifs.files.build target/filesets/ ; cp ../../QXA.QA.7.0_um/qnx_ap/target/hypervisor/host/build_files/init_mifs.build.tmpl target/hypervisor/host/build_files/ ;  cp ../../QXA.QA.7.0_um/qnx_ap/target/hypervisor/host/build_files/tftp.build.tmpl target/hypervisor/host/build_files/ ; make images
cd ../../
cp QXA.QA.7.0_um/qnx_ap/target/filesets/common.qnx.early.storage.build QXA.QA.7.0_um-bld/qnx_ap/target/filesets/
cp QXA.QA.7.0_um/qnx_ap/target/filesets/qc.plt.common.mifs.files.build QXA.QA.7.0_um-bld/qnx_ap/target/filesets/
cp QXA.QA.7.0_um/qnx_ap/target/filesets/qnx.plt.common.mifs.lib.build QXA.QA.7.0_um-bld/qnx_ap/target/filesets/
cp QXA.QA.7.0_um/qnx_ap/target/hypervisor/host/build_files/init_mifs.build.tmpl QXA.QA.7.0_um-bld/qnx_ap/target/hypervisor/host/build_files/
cd -
make images
cp ../../QXA.QA.7.0_um/qnx_ap/target/filesets/qc.plt.common.mifs.files.build target/filesets/ ; cp ../../QXA.QA.7.0_um/qnx_ap/target/hypervisor/host/build_files/init_mifs.build.tmpl target/hypervisor/host/build_files/ ;  make images
cd ../
vim flash.bat
cd -
cp ../../QXA.QA.7.0_um/qnx_ap/target/filesets/qc.plt.common.mifs.files.build target/filesets/ ; cp ../../QXA.QA.7.0_um/qnx_ap/target/hypervisor/host/build_files/init_mifs.build.tmpl target/hypervisor/host/build_files/ ;  make images
cd ../../QXA.QA.7.0_um/qnx_ap/target/
git s
git status --porcelain 
git status --porcelain | awk '{print $2}'
realpath ../../../QXA.QA.7.0_um-bld/qnx_ap/target/
chmod +x copy_modified_files.sh 
./copy_modified_files.sh 
cd ../../../QXA.QA.7.0_um-bld/qnx_ap/
make images
cd target/
git s
git d
cd ../
pushd ../../QXA.QA.7.0_um/qnx_ap/target/ && ./copy_modified_files.sh && popd && make images
pushd ../../QXA.QA.7.0_um/qnx_ap/target/ && ./copy_modified_files.sh && popd 
grep -rn 'random' target/filesets/
grep -rn 'random' target/hypervisor/host/out_nord/
cd ghalthot/epics/11159-nord_qnx/QXA.QA.7.0_hw_review/
packbuild.sh 
cd ghalthot/epics/11159-nord_qnx/QXA.QA.7.0_hw_review/
packbuild.sh 
cd ghalthot/epics/11159-nord_qnx/QXA.QA.7.0_hw_review/
packbuild.sh 
vim ../packbuild.sh 
cd qnx_ap/
source setenv_sdp800.sh 
cd target/
git s
git lg
git s
git s | grep common.qnx.early
git s | grep common.qnx
git s | grep 'ec.core'
git s | grep 'qc.core'
git s | grep 'qc.plt'
git s | grep 'qc.wl'
git s | grep 'qnx.data'
cd ../
make images
cd ghalthot/epics/11159-nord_qnx/QXA.QA.7.0_hw_review/
packbuild.sh 
cd qnx_ap/
make -C target/ clean
make images
ll
source setenv_sdp800.sh 
make -C target/ clean
make images
make -C target/ clean
make images
cd ../
ll
du -sh qnx_ap/test/
ll
ll HY11_1/qnx_ap/prebuilt
cd ../
ll
cd ghalthot/epics/11159-nord_qnx/QXA.QA.7.0_hw_review/
cd qnx_ap/
cd ../
packbuild.sh 
cd qnx_ap/
source setenv_sdp800.sh 
make 
make clean && make
cd ghalthot/epics/11159-nord_qnx/03_work/QXA.QA.7.0_img_size_check/
cd qnx_ap/build/
./copy_script.sh 
cd ../
source setenv_sdp800.sh 
make clean && make
cd ghalthot/epics/11159-nord_qnx/03_work/QXA.QA.7.0_hy11_build/qnx_ap/build/
./copy_script.sh 
cd ../../
which packbuild.sh
cp /usr/bin/packbuild.sh .
ll
cd qnx_ap/
cd -
ll
cd qnx_ap/
ll
cd ../
ls
less ./packbuild.sh 
source packbuild.sh 
cd -
source packbuild.sh 
cd -
source ./packbuild.sh 
./packbuild.sh 
ls
rm -rf HY11_CompileTest/
./packbuild.sh 
cd qnx_ap/
vim sa_env.sh 
cd ../
cd ghalthot/epics/11159-nord_qnx/03_work/QXA.QA.7.0_hy11_build/
ll
./packbuild.sh 
cd ghalthot/epics/11159-nord_qnx/03_work/AU_QXA.QA.7.0.r1_28-bld1/
less ../AU_QXA.QA.7.0.r1_28-bld/packbuild.sh 
cd qnx_ap/target/
git log -2
git reset --hard HEAD~1
git log -2
cd ../../
../AU_QXA.QA.7.0.r1_28-bld/packbuild.sh 
find qnx_ap/AMSS/multimedia/audio/audio_qnx/ -name *.pack
find qnx_ap/AMSS/multimedia/audio/ -name *.pack
find qnx_ap/AMSS/multimedia/audio/ -name '*.pack'
grep audio qnx_ap/setenv_qc.sh 
vim qnx_ap/AMSS/multimedia/audio/audio_qnx/audio_elite/audio_elite.qxa_qa.pack
who
who -a
cd ghalthot/epics/11159-nord_qnx/03_work/AU_QXA.QA.7.0.r1_28-bld_disp_patch/qnx_ap/
cd ../
../AU_QXA.QA.7.0.r1_28-bld/packbuild.sh 
cd ghalthot/learning/qnx/QXA.QA.7.0_sec-bld
ls
packbuild.sh 
ll
rm -rf FEAT-* SRC/ HY* 
cd qnx_ap/
source setenv_sdp800.sh 
make -C rsa/ 
make -C rsa/ install
vim rsa/Makefile 
vim rsa/rsa_signature_verify_cert/Makefile 
vim rsa/rsa_signature_verify_cert/aarch64/le/Makefile 
vim rsa/rsa_signature_verify_cert/common.mk 
find qnx_bins/ -name '*ssl*'
find qnx_bins/ -name '*certi*'
make -C rsa/rsa_signature_verify_cert/ install
grep -rn 'X509_STORE_CTX' qnx_bins/prebuilt_SDP800/
find qnx_bins/prebuilt_SDP800/ -name ssl.h
grep -rn 'X509_STORE_CTX' qnx_bins/prebuilt_SDP800/target/qnx/usr/include/
cd ghalthot/learning/proj/inprogress/10_rpi_sec/rpi5-uboot-bld
ll
make rpi_arm64_defconfig
make -j `nproc`
export CROSS_COMPILE=aarch64-linux-gnu-
make -j `nproc`
cd ghalthot/learning/proj/inprogress/10_rpi_sec/rpi5-aosp-bld
cd ghalthot/learning/proj/inprogress/10_rpi_sec/rpi5-aosp-base-bld
../build_aosp.sh 
cd ghalthot/learning/proj/inprogress/10_rpi_sec/rpi5-aosp-base-bld/
../build_aosp.sh 
find rpi5-mkimg.sh
vim rpi5-mkimg.sh 
cat ../build_aosp.sh 
source build/envsetup.sh
lunch aosp_rpi5-bp2a-userdebug
./rpi5-mkimg.sh
cd ghalthot/learning/proj/inprogress/10_rpi_sec/rpi5-aosp-car-bld
../build_aosp.sh car
cat ../build_aosp.sh car
./rpi5-mkimg.sh 
source build/envsetup.sh
lunch aosp_rpi5_car-bp2a-userdebug
ls /sbin
./rpi5-mkimg.sh 
cd ghalthot/epics/11159-nord_qnx/QXA.QA.7.0_certicom-bld/qnx_ap/build/
./copy_script.sh 
cd ../
source setenv_sdp800.sh 
find . -name '*certicom*'
vim ./qnx_bins/prebuilt_SDP800/target/qnx/usr/help/eclipse/plugins/com.qnx.doc.security.system/topic/manual/qcrypto_certicom_plugin.html
find qnx_bins/ -name libsbge.so
find qnx_bins/ -name libsbgse.so
find qnx_bins/ -name libcerticom.so
find . -name '*sbgse*'
grep -rni 'qcrypto-openssl' target/filesets/
find qnx_bins/prebuilt_SDP800/ -name libqcrypto.so.1.0
ls qnx_bins/prebuilt_SDP800/target/qnx/aarch64le/usr/lib/
cd qnx_bins/prebuilt_SDP800
find . -name libqcrypto.so.1
find . -name libqcrypto.so
find . -name libcrypto.so
grep 'libcrypto.so' ../../target/filesets/
grep -r 'libcrypto.so' ../../target/filesets/
find . -name qcrypto-openssl-3.so
grep -rn 'qcrypto-openssl-3.so' ../../target/filesets/
grep -rn 'libqcrypto' ../../target/filesets/
grep -rn 'qcrypto-certicom.so' ../../target/filesets/
grep -rn '*certicom*' ../../target/filesets/
find . -name '*certicom*'
find . -name '*openssl*'
ll ./target/qnx/aarch64le/lib/dll/qcrypto-openssl-3.so ./target/qnx/aarch64le/lib/dll/qcrypto-certicom.so
cd ../../../
cd qnx_ap/build
./copy_script.sh 
cd ../
source setenv_sdp800.sh 
make clean
make
cd rsa/
make clean
make
cd ../
find . -name *rsa_signature_verify_*'
find . -name '*rsa_signature_verify_*'
vim setenv_sdp800.sh 
cd target/
git d
git s
git d
cd ../rsa/
make clean
make
cd ../
find . -name '*rsa_signature_verify_*'
cd rsa/
git d
cd -
cd rsa/
make install
grep MKIFS_ ../setenv_sdp800.sh | grep aarch64le/bin/
grep MKIFS_ ../setenv_sdp800.sh 
grep MKIFS_ ../setenv_sdp800.sh | grep aarch64le/bin
cd ../target/
git d filesets/
cd ../
make images
cd ghalthot/learning/proj/inprogress/10_rpi_sec/rpi5-aosp-base-bld/
source build/envsetup.sh
lunch aosp_rpi5-bp2a-userdebug
ll
cd device/bcrm/rpi5
cd device/brcm/rpi5/
git status
git diff
git checkout .
cd -
./rpi5-mkimg.sh 
rm /local/mnt/workspace/ghalthot/learning/proj/inprogress/10_rpi_sec/rpi5-aosp-base-bld/out/target/product/rpi5/RaspberryVanillaAOSP16-20250920-rpi5.img
./rpi5-mkimg.sh 
cd ghalthot/learning/proj/inprogress/10_rpi_sec/rpi5-aosp-car-bld
ll
source build/envsetup.sh
lunch aosp_rpi5_car-bp2a-userdebug
cat ../build_aosp.sh 
make bootimage systemimage vendorimage -j$(nproc)
cat ../build_aosp.sh 
./rpi5-mkimg.sh 
cd ghalthot/learning/proj/inprogress/10_rpi_sec/rpi5-uboot-bld
ll ../
../build_uboot.sh 
ll
cd ghalthot/05_boot/u-boot-rpi5/
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- rpi_arm64_defconfig
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j$(nproc)
ll
echo $UID
ll arch/arm64
ls arch/
find . -name 'rpi_*'
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- rpi_arm64_defconfig
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j$(nproc)
cd ../
ll
cp -r u-boot-rpi5/ u-boot-rpi5-build
cd u-boot-rpi5-build/
ll config
ls
ll configs/
cd ghalthot/05_boot/u-boot-rpi5-build/
ls configs/
ls configs/rpi_*
make rpi_arm64_defconfig
CROSS_COMPILE=aarch64-linux-gnu- ARCH=arm64 make
ll arch/ar
make clean
git co next 
make rpi_arm64_defconfig
vim configs/rpi_arm64_defconfig 
make CROSS_COMPILE=aarch64-linux-gnu- ARCH=arm64
make ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu-
ll arch/
ll arch/ar
ll arch/arm/
l arch/arm/
find arch/ -name '*rpi*'
/opt/run_src.sh --help
rm -rf rpi5-aosp ; /opt/run_src.sh -s sync -c aosp
ll
/opt/run_src.sh -s build -c uboot
/opt/run_src.sh -s build -c aosp
/opt/run_src.sh -h
/opt/run_src.sh --help
cat /opt/run_src.sh 
curl -L -o manifest_brcm_rpi.xml https://raw.githubusercontent.com/ganeshhalthota/android_local_manifest/android-16.0/manifest_brcm_rpi.xml
rm manifest_brcm_rpi.xml 
curl -L -o remove_projects.xml https://raw.githubusercontent.com/ganeshhalthota/android_local_manifest/android-16.0/remove_projects.xml
ll
rm remove_projects.xml 
ll
/opt/run_src.sh --help
/opt/run_src.sh -s sdcard
parted
parted --script -h
cd u-boot/
make menuconfig
cd ../
ll
source .venv/bin/activate
python3 /opt/test_img_gen.py 
export ANDROID_PRODUCT_OUT=/workspace/rpi5-aosp/out/target/product/rpi5/
python3 /opt/test_img_gen.py 
rm rpi5-aosp/out/target/product/rpi5/RaspberryVanillaAOSP16-2* ; python3 /opt/test_img_gen.py 
rm -f rpi5-aosp/out/target/product/rpi5/RaspberryVanillaAOSP16-2* ; python3 /opt/test_img_gen.py 
gdisk -l /workspace/rpi5-aosp/out/target/product/rpi5/RaspberryVanillaAOSP16-20251212-rpi.img
sudo parted --script /workspace/rpi5-aosp/out/target/product/rpi5/RaspberryVanillaAOSP16-20251212-rpi.img name -h
ls -al rpi5-aosp/out/target/product/rpi5/boot.img 
python3 /opt/test_img_gen.py 
ls -al /dev/
ls  /dev/
losetup -l
sudo kpartx -av /workspace/rpi5-aosp/out/target/product/rpi5/RaspberryVanillaAOSP16-20251213-rpi.img
sudo kpartx -d /workspace/rpi5-aosp/out/target/product/rpi5/RaspberryVanillaAOSP16-20251213-rpi.img
losetup -l
sudo losetup -d /dev/loop3
losetup -l
losetup -h

sudo losetup -d /dev/loop3
losetup -h
losetup -l
sudo kpartx -d /dev/loop3 
losetup -l
sudo kpartx -av /workspace/rpi5-aosp/out/target/product/rpi5/RaspberryVanillaAOSP16-20251213-rpi.img
sudo kpartx -d /workspace/rpi5-aosp/out/target/product/rpi5/RaspberryVanillaAOSP16-20251213-rpi.img
losetup -l
sudo kpartx -d /dev/loop3 
losetup -l
sudo losetup -d /dev/loop3
losetup -l
python3 /opt/test_img_gen.py 
rm -f rpi5-aosp/out/target/product/rpi5/RaspberryVanillaAOSP16-2* ; python3 /opt/test_img_gen.py 
find rpi5-aosp/ -name *vbmeta*
find rpi5-aosp/out/target/product/rpi5/ -name *vbmeta*
find rpi5-aosp/ -name avbtool 
rm -f rpi5-aosp/out/target/product/rpi5/RaspberryVanillaAOSP16-2* ; python3 /opt/test_img_gen.py 
sudo kpartx -d /dev/loop3 
losetup -l
sudo losetup -d /dev/loop3
losetup -l
rm -f rpi5-aosp/out/target/product/rpi5/RaspberryVanillaAOSP16-2* ; python3 /opt/test_img_gen.py 
cd rpi5-aosp/out/target/product/rpi5/
tar czf RaspberryVanillaAOSP16-20251213-rpi.img.tgz RaspberryVanillaAOSP16-20251213-rpi.img 
cd ../../../

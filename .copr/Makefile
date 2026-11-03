# copr SCM build, method make_srpm: copr runs
#   make -f .copr/Makefile srpm outdir=<dir> spec=<spec>
# in a chroot with network; the SRPM has the dist tag undefined, copr adds the
# chroot's when it builds the binaries
top := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)

srpm:
	command -v rpmbuild >/dev/null && command -v curl >/dev/null || dnf -y install rpm-build curl
	AWSLC_OUT=$(top)/.build/copr $(top)/scripts/build-srpm.sh
	cp $(top)/.build/copr/rpm/*.src.rpm $(outdir)

.PHONY: srpm

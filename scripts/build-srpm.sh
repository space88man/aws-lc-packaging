#!/bin/bash
# build source RPMs into out/rpm/ for copr
#   scripts/build-srpm.sh              -> aws-lc-V-R.src.rpm (dist undefined)
#   scripts/build-srpm.sh '' .el9 .el10 -> plus aws-lc-V-R.el9/.el10.src.rpm
set -euo pipefail
. "$(dirname "$0")/lib.sh"
check_versions
fetch_upstream

stage=$TOP/.build/rpm
rm -rf "$stage"
mkdir -p "$stage" "$OUT/rpm"
cp "$TOP/rpm/aws-lc.spec" "$TOP"/patches/*.patch "$stage/"
ln -s "$TARBALL" "$stage/"

[ $# -gt 0 ] || set -- ''
for dist in "$@"; do
	if [ -n "$dist" ]; then
		dflag=(--define "dist $dist")
	else
		dflag=(--undefine dist)
	fi
	rpmbuild -bs --define "_sourcedir $stage" --define "_srcrpmdir $OUT/rpm" \
		"${dflag[@]}" "$stage/aws-lc.spec"
done

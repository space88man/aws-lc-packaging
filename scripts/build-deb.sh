#!/bin/bash
# build the Debian package on a Debian host (dpkg-dev, build deps from
# debian/control); output in out/deb/. Arguments go to dpkg-buildpackage
# (default -us -uc; -S for a source package only).
#   the +ds orig tarball is the pinned upstream tarball minus Files-Excluded
#   (deb/debian/copyright), packed reproducibly; it is kept in .cache/
set -euo pipefail
. "$(dirname "$0")/lib.sh"
check_versions
fetch_upstream
umask 022

dsver=$AWSLC_VERSION+ds
orig=$CACHE/aws-lc_$dsver.orig.tar.xz

repack() {
	local tmp epoch top ex
	tmp=$(mktemp -d "$CACHE/repack.XXXXXX")
	tar xzf "$TARBALL" -C "$tmp"
	top=$tmp/aws-lc-$AWSLC_VERSION
	[ -d "$top" ] || die "unexpected tarball layout: no aws-lc-$AWSLC_VERSION/"
	epoch=$(stat -c %Y "$top")
	# Files-Excluded: continuation lines up to the next field
	sed -n '/^Files-Excluded:/,/^[^ ]/{/^ /p}' "$TOP/deb/debian/copyright" |
		while read -r ex; do
			(cd "$top" && eval "rm -rf -- $ex")
		done
	mv "$top" "$tmp/aws-lc-$dsver"
	tar -C "$tmp" --sort=name --format=gnu --owner=0 --group=0 --numeric-owner \
		--mtime="@$epoch" --clamp-mtime -cf - "aws-lc-$dsver" |
		xz -T1 -6 >"$orig.part"
	mv -f "$orig.part" "$orig"
	rm -rf "$tmp"
}

[ -f "$orig" ] || repack
echo "${AWSLC_DS_ORIG_SHA256:-}  $orig" | sha256sum -c --status ||
	echo "${0##*/}: warning: $orig differs from AWSLC_DS_ORIG_SHA256 (tar/xz versions?)" >&2

stage=$TOP/.build/deb
rm -rf "$stage"
mkdir -p "$stage" "$OUT/deb"
cp "$orig" "$stage/"
tar xJf "$orig" -C "$stage"
# -L: debian/patches links into patches/
cp -aL "$TOP/deb/debian" "$stage/aws-lc-$dsver/"

[ $# -gt 0 ] || set -- -us -uc
(cd "$stage/aws-lc-$dsver" && dpkg-buildpackage "$@")
find "$stage" -maxdepth 1 -type f \
	-exec cp -t "$OUT/deb/" {} +
ls -1 "$OUT/deb"

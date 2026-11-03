# shellcheck shell=bash
# shared by the build scripts: paths, pinned upstream, idempotent fetch

TOP=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
# shellcheck source=../upstream.lock
. "$TOP/upstream.lock"
CACHE=${AWSLC_CACHE:-$TOP/.cache}
OUT=${AWSLC_OUT:-$TOP/out}
TARBALL=$CACHE/aws-lc-$AWSLC_VERSION.tar.gz

die() { echo "${0##*/}: $*" >&2; exit 1; }

sha_ok() { echo "$AWSLC_SHA256  $1" | sha256sum -c --status; }

# download the pinned tarball unless a verified copy is in the cache
fetch_upstream() {
	local tmp
	[ -f "$TARBALL" ] && sha_ok "$TARBALL" && return 0
	mkdir -p "$CACHE"
	tmp=$TARBALL.part.$$
	curl -fsSL --retry 3 -o "$tmp" "$AWSLC_URL" || { rm -f "$tmp"; die "download failed: $AWSLC_URL"; }
	if ! sha_ok "$tmp"; then
		local got
		got=$(sha256sum <"$tmp" | cut -d' ' -f1)
		rm -f "$tmp"
		die "sha256 mismatch for $AWSLC_URL: got $got, upstream.lock has $AWSLC_SHA256"
	fi
	mv -f "$tmp" "$TARBALL"
}

# the spec and debian/changelog must package the pinned version
check_versions() {
	local spec deb
	spec=$(sed -n 's/^Version:[[:space:]]*//p' "$TOP/rpm/aws-lc.spec")
	deb=$(sed -n '1s/^aws-lc (\([^+-]*\).*/\1/p' "$TOP/deb/debian/changelog")
	[ "$spec" = "$AWSLC_VERSION" ] || die "rpm/aws-lc.spec Version $spec != upstream.lock $AWSLC_VERSION"
	[ "$deb" = "$AWSLC_VERSION" ] || die "deb/debian/changelog $deb != upstream.lock $AWSLC_VERSION"
}

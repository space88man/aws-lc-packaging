# aws-lc-packaging

RPM and Debian packaging for [AWS-LC](https://github.com/aws/aws-lc) in upstream's distribution-packaging mode
(`ENABLE_DIST_PKG`): `libcrypto-awslc.so.1` / `libssl-awslc.so.1` (symbols versioned `AWS_LC_1.0`), headers in
`include/aws-lc`, `pkg-config aws-lc`, tools prefixed `aws-lc-`. Installs beside the system OpenSSL.

| | packages | built for |
|---|---|---|
| RPM `rpm/aws-lc.spec` | `aws-lc-libs`, `aws-lc` (tools), `aws-lc-devel` | EL9, EL10 ([copr beaveryoga/AWS-LC](https://copr.fedorainfracloud.org/coprs/beaveryoga/AWS-LC/)) |
| Debian `deb/debian/` | `libcrypto-awslc1`, `libssl-awslc1`, `libaws-lc-dev`, `aws-lc-tools` | Debian 13 (trixie) |

Unofficial: not affiliated with or endorsed by Amazon or the AWS-LC project. Users include Kamailio's tls module
(`-DTLS_BUILD_WITH=AWSLC`).

## Layout

- `upstream.lock`: pinned upstream version, tag tarball URL and sha256 (+ the repacked Debian orig sha256).
- `patches/`: patches carried for both formats, DEP-3 headers. `deb/debian/patches/` links here; the RPM spec lists
  them as `PatchN`.
- `scripts/fetch.sh`: download the pinned tarball into `.cache/`; a verified copy is reused, a bad one replaced.
- `scripts/build-srpm.sh [dist ...]`: source RPMs into `out/rpm/` (`'' .el9 .el10` gives all three copr inputs).
- `scripts/build-deb.sh [dpkg-buildpackage args]`: on Debian; repacks the `+ds` orig (Files-Excluded in
  `deb/debian/copyright`, reproducible tar + xz), stages `debian/` with the patches dereferenced, builds into `out/deb/`.

Nothing upstream is vendored: `.cache/`, `.build/` and `out/` are ignored.

## Releases

- New packaging revision: bump `Release` (spec, `%changelog`) and/or `debian/changelog`.
- New upstream: update `upstream.lock` (`sha256sum` of the tag tarball), spec `Version`, `debian/changelog`; the
  scripts refuse a version mismatch. Rebase `patches/` (drop what upstream merged); refresh `AWSLC_DS_ORIG_SHA256`.
- RPM binaries: `rpmbuild --rebuild out/rpm/aws-lc-*.src.rpm` (or mock). copr: SCM source, clone URL of this repo,
  build method `make_srpm` (`.copr/Makefile` runs `scripts/build-srpm.sh`), or upload the SRPMs.
- Debian binaries: `scripts/build-deb.sh` (default `-us -uc`), then `lintian -I --pedantic out/deb/*.changes`.

## Patches

- `c_rehash-dist-pkg-name.patch`: with `ENABLE_DIST_PKG` the tool is `aws-lc-openssl`, but `aws-lc-c_rehash` looks
  for `openssl` beside itself and always fails. Not forwarded yet.

## License

The packaging files are available under Apache-2.0 OR ISC (`LICENSE`), as `debian/copyright` states for `debian/*`.
AWS-LC is not in this repository; the packages ship its `LICENSE`, and its licenses are listed in the spec `License`
tag and in `deb/debian/copyright`.

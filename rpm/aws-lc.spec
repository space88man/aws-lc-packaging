# Packaging repo: https://github.com/space88man/aws-lc-packaging
# Build: scripts/build-srpm.sh there fetches Source0
# (pinned in upstream.lock) and the shared patch, then runs rpmbuild -bs for
# copr (epel-9/epel-10 chroots); rpmbuild --rebuild or mock for binaries.
# Built in copr beaveryoga/AWS-LC.
#
# AWS-LC in distribution-packaging mode (ENABLE_DIST_PKG): it installs beside the
# system OpenSSL without clashing:
#   libcrypto-awslc.so.1 / libssl-awslc.so.1 (SONAME = ABI version), symbols
#   versioned AWS_LC_1.0; headers in include/aws-lc/openssl; tools prefixed
#   aws-lc-. The OpenSSL shim (include/openssl, libssl.so links) stays off.
#
# Package split as for OpenSSL: aws-lc-libs (libraries), aws-lc (command line
# tools), aws-lc-devel. Up to 5.12.0-1 aws-lc held the libraries and
# aws-lc-tools the tools.
#
# ENABLE_CRYPTO_POLICIES: SSL_CTX_new() seeds ciphers, protocol bounds, groups
# and signature algorithms from the system crypto-policies OpenSSL back-end
# (/etc/crypto-policies/back-ends/opensslcnf.config), as the system OpenSSL
# does; best-effort, and the application's own SSL_CTX settings override it.
#
# Go and Perl are disabled: the pre-generated sources and assembly in the tarball
# are used, and the build needs no network (copr). %%check runs the gtest suites
# that need neither Go nor network (upstream's run_minimal_tests):
# crypto_test, urandom_test and ssl_test. Skip them with --without check.
# As in upstream's crypto-policies CI, the suites run with the policy file
# pointed away (they assert the built-in defaults), then the CryptoPolicy tests
# run against the system policy.

%bcond_without check

%global abi_version 1

Name:           aws-lc
Version:        5.13.0
Release:        1%{?dist}
Summary:        Command line tools for AWS-LC

# AWS-LC code: Apache-2.0 OR ISC; BoringSSL-derived: ISC or Apache-2.0;
# OpenSSL-derived: Apache-2.0; mlkem/mldsa-native: Apache-2.0 OR ISC OR MIT;
# fiat-crypto: MIT; s2n-bignum: Apache-2.0 OR ISC OR MIT-0;
# jitterentropy: BSD-3-Clause; Keccak/AES reference code: CC0-1.0
License:        (Apache-2.0 OR ISC) AND Apache-2.0 AND ISC AND MIT AND (Apache-2.0 OR ISC OR MIT) AND (Apache-2.0 OR ISC OR MIT-0) AND BSD-3-Clause AND CC0-1.0
URL:            https://github.com/aws/aws-lc
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz
# dist-pkg installs the tool as aws-lc-openssl; c_rehash looked for "openssl"
Patch0:         c_rehash-dist-pkg-name.patch

# assembly for x86_64 and aarch64; other arches fall back to C
ExclusiveArch:  x86_64 aarch64

BuildRequires:  cmake >= 3.12
BuildRequires:  ninja-build
BuildRequires:  gcc
BuildRequires:  gcc-c++
%if %{with check}
# the system policy file for the CryptoPolicy tests
BuildRequires:  crypto-policies
%endif

Requires:       %{name}-libs%{?_isa} = %{version}-%{release}
# up to 5.12.0-1 the tools were in aws-lc-tools
Obsoletes:      %{name}-tools < 5.12.0-2
Provides:       %{name}-tools = %{version}-%{release}
Provides:       %{name}-tools%{?_isa} = %{version}-%{release}

%description
AWS-LC is a general-purpose cryptographic library maintained by the AWS
Cryptography team, based on code from the Google BoringSSL project and the
OpenSSL project.

This package holds the aws-lc-bssl and aws-lc-openssl command line tools and
the aws-lc-c_rehash script; the libraries are in %{name}-libs.

%package        libs
Summary:        General-purpose cryptographic and TLS library from AWS
# read by SSL_CTX_new() (ENABLE_CRYPTO_POLICIES), as for openssl-libs
Requires:       crypto-policies

%description    libs
AWS-LC is a general-purpose cryptographic library maintained by the AWS
Cryptography team, based on code from the Google BoringSSL project and the
OpenSSL project. It provides libcrypto and libssl with an OpenSSL-compatible
API.

This build uses distribution-packaging names (libcrypto-awslc, libssl-awslc,
include/aws-lc) and versioned symbols, so it installs beside the system OpenSSL.
TLS contexts honour the system-wide crypto-policies.

%package        devel
Summary:        Development files for AWS-LC
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}

%description    devel
Headers (in %{_includedir}/aws-lc/openssl), linker symlinks, pkg-config files
(aws-lc, libcrypto-awslc, libssl-awslc) and CMake package files for building
against AWS-LC.

%prep
%autosetup -p1

%build
# RelWithDebInfo: -O2 -g as in the distribution flags, plus
# BORINGSSL_RELEASE_BUILD (a non-release build type adds dispatch test hooks)
%cmake -GNinja \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    -DBUILD_SHARED_LIBS=ON \
    -DENABLE_DIST_PKG=ON \
    -DDISABLE_GO=ON \
    -DDISABLE_PERL=ON \
    -DENABLE_SOURCE_MODIFICATION=OFF \
    -DENABLE_CRYPTO_POLICIES=ON \
    -DBUILD_TESTING=%{?with_check:ON}%{!?with_check:OFF}
%cmake_build

%install
%cmake_install

%if %{with check}
%check
cd %{__cmake_builddir}
export AWSLC_CRYPTO_POLICY_FILE=/nonexistent/aws-lc-crypto-policy-disabled
./crypto/crypto_test
./crypto/urandom_test
./ssl/ssl_test
env --unset=AWSLC_CRYPTO_POLICY_FILE AWSLC_CRYPTO_POLICY_TEST_REQUIRE_SYSTEM=1 \
    ./ssl/ssl_test --gtest_filter='CryptoPolicy*'
%endif

%files
%{_bindir}/aws-lc-bssl
%{_bindir}/aws-lc-openssl
%{_bindir}/aws-lc-c_rehash

%files libs
%license LICENSE
%doc README.md
%{_libdir}/libcrypto-awslc.so.%{abi_version}
%{_libdir}/libcrypto-awslc.so.%{version}
%{_libdir}/libssl-awslc.so.%{abi_version}
%{_libdir}/libssl-awslc.so.%{version}

%files devel
%doc API-CONVENTIONS.md PORTING.md docs/SymbolVersioning.md
%{_includedir}/aws-lc/
%{_libdir}/libcrypto-awslc.so
%{_libdir}/libssl-awslc.so
%{_libdir}/pkgconfig/aws-lc.pc
%{_libdir}/pkgconfig/libcrypto-awslc.pc
%{_libdir}/pkgconfig/libssl-awslc.pc
# upstream installs the CMake packages as <libdir>/{crypto,ssl}/cmake
%{_libdir}/crypto/
%{_libdir}/ssl/

%changelog
* Sat Nov 07 2026 S-P Chan <shihping.chan@gmail.com> - 5.13.0-1
- Update to AWS-LC v5.13.0

* Tue Nov 03 2026 S-P Chan <shihping.chan@gmail.com> - 5.12.0-3
- aws-lc-c_rehash: find the tool as aws-lc-openssl; it always failed before

* Mon Nov 02 2026 S-P Chan <shihping.chan@gmail.com> - 5.12.0-2
- Split as for OpenSSL: libraries move to aws-lc-libs, aws-lc holds the
  command line tools and replaces aws-lc-tools

* Mon Nov 02 2026 S-P Chan <shihping.chan@gmail.com> - 5.12.0-1
- Initial package: AWS-LC v5.12.0, distribution-packaging mode, system
  crypto-policies enabled

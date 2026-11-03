#!/bin/bash
# fetch the pinned upstream tarball into .cache/ (no-op when present and verified)
set -euo pipefail
. "$(dirname "$0")/lib.sh"
fetch_upstream
echo "$TARBALL"

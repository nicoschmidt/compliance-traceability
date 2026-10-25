#!/usr/bin/env bash
# Managed by ai-dev-process.
#
# Print every field on the project board and the options of every single
# select. Read-only. Run this whenever a handover script complains that a
# field or an option does not exist — the board is the authority, not the
# scripts beside this file.
#
#   bash scripts/process/show-board.sh

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$(git -C "$HERE" rev-parse --show-toplevel)"

# shellcheck source=gh-board.sh
source "$HERE/gh-board.sh"
board_connect
echo
board_show

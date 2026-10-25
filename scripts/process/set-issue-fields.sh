#!/usr/bin/env bash
# Managed by ai-dev-process.
#
# Set the size and iteration fields of an issue that already exists. Use when
# an issue was created but its fields were not set — for instance because a
# refinement session turned an idea into ready work, or a script failed halfway.
#
#   bash scripts/process/set-issue-fields.sh 13 S Backlog
#
# Status is never set here: it is the maintainer's judgement, not a fact.

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$(git -C "$HERE" rev-parse --show-toplevel)"

if [ "$#" -ne 3 ]; then
  echo "usage: bash scripts/process/$(basename "$0") <issue number> <size> <iteration>"
  echo "  e.g. bash scripts/process/$(basename "$0") 13 S Backlog"
  exit 1
fi

# shellcheck source=gh-board.sh
source "$HERE/gh-board.sh"
board_connect

set_issue_fields "$1" "$2" "$3"

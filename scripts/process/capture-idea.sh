#!/usr/bin/env bash
# Managed by ai-dev-process.
#
# Capture an idea as an issue labelled `idea`, in seconds. It is refined later
# and never worked on as it is (.claude/rules/process/workflow.md).
#
#   bash scripts/process/capture-idea.sh "Retro should read merged PR reviews"
#   bash scripts/process/capture-idea.sh --process "Handover blocks are too long" "Two lines of detail"
#
# --process   also label it `process`: about the way of working, read by the retro
# Board fields are not set: an idea has no size yet.

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$(git -C "$HERE" rev-parse --show-toplevel)"

labels="idea"
if [ "${1:-}" = "--process" ]; then
  labels="idea,process"
  shift
fi

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ] || [ -z "$1" ]; then
  echo "usage: bash scripts/process/$(basename "$0") [--process] <title> [details]"
  exit 1
fi

title="$1"
details="${2:-}"
body="### What came to mind

${details:-_No details. The title is the idea._}

---
Captured in passing. Refined before any work starts."

url="$(gh issue create --label "$labels" --title "$title" --body "$body")" || {
  echo "Not captured: gh issue create failed. Labels missing? Run:"
  echo "  bash scripts/process/setup-labels.sh"
  exit 1
}
echo "captured $url"

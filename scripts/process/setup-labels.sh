#!/usr/bin/env bash
# Managed by ai-dev-process.
#
# Create the labels the process relies on where they are missing. Existing
# labels are left as they are — their colour and description belong to the
# project — unless --update is given.
#
#   bash scripts/process/setup-labels.sh
#   bash scripts/process/setup-labels.sh --update
#   GH_REPO=owner/name bash scripts/process/setup-labels.sh

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$(git -C "$HERE" rev-parse --show-toplevel)"

command -v gh >/dev/null || { echo "gh is not installed."; exit 1; }

update=0
case "${1:-}" in
  '') ;;
  --update) update=1 ;;
  *) echo "usage: bash scripts/process/$(basename "$0") [--update]"; exit 1 ;;
esac

# An empty array expands safely under `set -u` only in bash 4.4 and later;
# macOS ships bash 3.2, hence the ${x[@]+...} form below.
repo_args=()
if [ -n "${GH_REPO:-}" ]; then repo_args=(--repo "$GH_REPO"); fi

existing="$(gh label list --limit 500 --json name -q '.[].name' ${repo_args[@]+"${repo_args[@]}"})" || {
  echo "Could not list the labels."
  exit 1
}

failed=0
while IFS='|' read -r name color description; do
  [ -n "$name" ] || continue
  if grep -qxF "$name" <<< "$existing"; then
    if [ "$update" -eq 0 ]; then
      echo "exists   $name"
      continue
    fi
    if gh label edit "$name" --color "$color" --description "$description" ${repo_args[@]+"${repo_args[@]}"} >/dev/null; then
      echo "updated  $name"
    else
      echo "FAILED   $name"; failed=1
    fi
  elif gh label create "$name" --color "$color" --description "$description" ${repo_args[@]+"${repo_args[@]}"} >/dev/null; then
    echo "created  $name"
  else
    echo "FAILED   $name"; failed=1
  fi
done <<'LABELS'
idea|FBCA04|Captured in passing; refined before any work starts
process|5319E7|About the way of working; read by the retro
type:feature|0E8A16|A capability the application should have
type:bug|D73A4A|Something behaves differently from what it should
type:spike|1D76DB|A time-boxed investigation that answers a question
type:chore|C5DEF5|Tooling, dependencies, process upkeep
LABELS

exit "$failed"

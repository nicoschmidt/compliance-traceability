#!/usr/bin/env bash
# Managed by ai-dev-process.
#
# Verify that every file installed by ai-dev-process is unchanged since it was
# installed. Read-only. Runs in CI.
#
#   bash scripts/process/check-kit.sh
#
# A file that differs was edited in this repository. Either the change belongs
# upstream (an issue in the process repository), or it is a project matter and
# belongs in CLAUDE.md as a parameter or a deviation. Then restore the file:
#
#   git checkout origin/main -- <path>

set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(git -C "$HERE" rev-parse --show-toplevel)"
LOCK="$ROOT/.ai-dev-process.lock"

sha() {
  if command -v sha256sum >/dev/null; then
    sha256sum "$1" | cut -d' ' -f1
  else
    shasum -a 256 "$1" | cut -d' ' -f1
  fi
}

[ -f "$LOCK" ] || { echo "No .ai-dev-process.lock in $ROOT. Was the kit installed?"; exit 1; }

version="$(sed -n 's/^version //p' "$LOCK")"
changed=0
missing=0
count=0
while read -r expected path; do
  case "$expected" in ''|'#'*|version|source|role) continue ;; esac
  count=$((count + 1))
  if [ ! -f "$ROOT/$path" ]; then
    echo "missing  $path"
    missing=$((missing + 1))
  elif [ "$(sha "$ROOT/$path")" != "$expected" ]; then
    echo "changed  $path"
    changed=$((changed + 1))
  fi
done < "$LOCK"

if [ "$changed" -eq 0 ] && [ "$missing" -eq 0 ]; then
  echo "ai-dev-process $version: all $count managed files unchanged"
  exit 0
fi
echo
echo "ai-dev-process $version: $changed changed, $missing missing, of $count managed files."
echo "Managed files are changed upstream, or overridden in CLAUDE.md under"
echo "'Process deviations' — never edited here."
exit 1

#!/usr/bin/env bash
# Managed by ai-dev-process.
#
# Exercise capture-idea.sh and setup-labels.sh against a stand-in for gh, put
# first on PATH. No credentials, nothing is written to GitHub.
#
#   bash scripts/process/test-capture-idea.sh

set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
FAILURES=0
STUB="$(mktemp -d)"
export GH_LOG="$STUB/calls"

cat > "$STUB/gh" <<'STANDIN'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "$GH_LOG"
if [ "${GH_FAIL:-}" = "1" ]; then exit 1; fi
case "$1 $2" in
  "issue create") echo "https://github.com/example-owner/example-repo/issues/23" ;;
  "label list") printf '%s\n' ${GH_EXISTING_LABELS:-} ;;
  "label create"|"label edit") ;;
  *) echo "unexpected gh call: $*" >&2; exit 1 ;;
esac
STANDIN
chmod +x "$STUB/gh"
export PATH="$STUB:$PATH"

check() {
  if [ "$2" = "$3" ]; then
    echo "  ok    $1"
  else
    echo "  FAIL  $1"
    echo "        expected: $2"
    echo "        actual:   $3"
    FAILURES=$((FAILURES + 1))
  fi
}

echo "an idea with a title only"
: > "$GH_LOG"
out="$(bash "$HERE/capture-idea.sh" "Retro reads review comments" 2>&1)"; code=$?
check "succeeds" "0" "$code"
check "reports the url" "captured https://github.com/example-owner/example-repo/issues/23" "$out"
check "labels it idea" "1" "$(grep -c -- '--label idea --title Retro reads review comments' "$GH_LOG")"

echo "a process idea with details"
: > "$GH_LOG"
out="$(bash "$HERE/capture-idea.sh" --process "Shorter handover blocks" "They scroll off screen" 2>&1)"; code=$?
check "succeeds" "0" "$code"
check "labels it idea and process" "1" "$(grep -c -- '--label idea,process' "$GH_LOG")"
check "carries the details" "1" "$(grep -c 'They scroll off screen' "$GH_LOG")"

echo "no title"
: > "$GH_LOG"
out="$(bash "$HERE/capture-idea.sh" 2>&1)"; code=$?
check "fails" "1" "$code"
check "calls nothing" "" "$(cat "$GH_LOG")"

echo "gh fails"
out="$(GH_FAIL=1 bash "$HERE/capture-idea.sh" "Anything" 2>&1)"; code=$?
check "fails" "1" "$code"
check "reports no capture" "0" "$(grep -c '^captured' <<<"$out")"

echo "labels in a repository that has none"
: > "$GH_LOG"
out="$(bash "$HERE/setup-labels.sh" 2>&1)"; code=$?
check "succeeds" "0" "$code"
check "creates six labels" "6" "$(grep -c '^label create' "$GH_LOG")"
check "without --repo by default" "0" "$(grep -c -- '--repo' "$GH_LOG")"
: > "$GH_LOG"
out="$(GH_REPO=o/r bash "$HERE/setup-labels.sh" 2>&1)"; code=$?
check "passes GH_REPO through" "7" "$(grep -c -- '--repo o/r' "$GH_LOG")"

echo "labels in a repository that has some"
: > "$GH_LOG"
out="$(GH_EXISTING_LABELS="type:feature type:bug" bash "$HERE/setup-labels.sh" 2>&1)"; code=$?
check "succeeds" "0" "$code"
check "creates only the four missing" "4" "$(grep -c '^label create' "$GH_LOG")"
check "leaves existing ones alone" "0" "$(grep -c '^label edit' "$GH_LOG")"
check "reports them" "2" "$(grep -c '^exists' <<<"$out")"
: > "$GH_LOG"
out="$(GH_EXISTING_LABELS="type:feature type:bug" bash "$HERE/setup-labels.sh" --update 2>&1)"; code=$?
check "--update edits the existing ones" "2" "$(grep -c '^label edit' "$GH_LOG")"
out="$(bash "$HERE/setup-labels.sh" --colour 2>&1)"; code=$?
check "an unknown option fails" "1" "$code"
out="$(GH_FAIL=1 bash "$HERE/setup-labels.sh" 2>&1)"; code=$?
check "fails loudly when gh fails" "1" "$code"

rm -rf "$STUB"
echo
if [ "$FAILURES" -eq 0 ]; then
  echo "all checks passed"
else
  echo "$FAILURES check(s) failed"
  exit 1
fi

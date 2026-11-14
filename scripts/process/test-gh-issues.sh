#!/usr/bin/env bash
# Managed by ai-dev-process.
#
# Exercise gh-issues.sh against a stand-in for gh. Needs no credentials and
# writes nothing to GitHub: every gh call is answered from files below, and
# the write calls are recorded instead of sent.
#
#   bash scripts/process/test-gh-issues.sh
#
# Run this after changing gh-issues.sh. Twice a broken helper reached the
# maintainer because nothing could call the real gh; a stand-in can.

set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d)"
ISSUES="$WORK/issues"          # number|title|milestone, one per line
MILESTONES_DB="$WORK/ms"       # repo|title|state, one per line
CALLS="$WORK/calls"            # key|arguments, one per gh call
EDITS="$WORK/edits"            # number|milestone, one per gh issue edit
FAILURES=0

reset() { : > "$ISSUES"; : > "$MILESTONES_DB"; : > "$CALLS"; : > "$EDITS"; }

argval() {             # argval <flag> <args…>: the value after the flag
  local flag="$1"; shift
  while [ "$#" -gt 0 ]; do
    if [ "$1" = "$flag" ]; then echo "$2"; return 0; fi
    shift
  done
}

gh() {
  local key repo title ms n a
  if [ "$1" = "api" ]; then
    if [[ " $* " == *" -f "* ]]; then key="api create milestone"; else key="api milestones"; fi
  else
    key="$1 $2"
  fi
  echo "$key|$*" >> "$CALLS"
  if [ -n "${GH_FAIL:-}" ] && [ "$key" = "$GH_FAIL" ]; then
    echo "stand-in refused: $*" >&2
    return 1
  fi
  case "$key" in
    "issue list")
      jq -R -s --arg r "$GH_REPO" 'split("\n") | map(select(length > 0) | split("|")
        | {number: (.[0] | tonumber), title: .[1], url: "https://github.com/\($r)/issues/\(.[0])"})' "$ISSUES" ;;
    "issue create")
      if [ -n "${FIXTURE_ISSUE_URL+set}" ]; then echo "$FIXTURE_ISSUE_URL"; return 0; fi
      title="$(argval --title "$@")"; ms="$(argval --milestone "$@")"
      n=$(( 17 + $(wc -l < "$ISSUES") ))
      echo "$n|$title|$ms" >> "$ISSUES"
      echo "https://github.com/$GH_REPO/issues/$n" ;;
    "issue edit")
      echo "$3|$(argval --milestone "$@")" >> "$EDITS" ;;
    "api milestones")
      repo="${2#repos/}"; repo="${repo%%/milestones*}"
      { grep -F -- "$repo|" "$MILESTONES_DB" || true; } | jq -R -s 'split("\n") | map(select(length > 0)
        | split("|") | {title: .[1], state: .[2]})' ;;
    "api create milestone")
      repo="${2#repos/}"; repo="${repo%%/milestones*}"
      for a in "$@"; do case "$a" in title=*) title="${a#title=}" ;; esac; done
      echo "$repo|$title|open" >> "$MILESTONES_DB"
      echo '{"number": 1}' ;;
    *) echo "unexpected gh call: $*" >&2; return 2 ;;
  esac
}

check() {              # check <description> <expected> <actual>
  if [ "$2" = "$3" ]; then
    echo "  ok    $1"
  else
    echo "  FAIL  $1"
    echo "        expected: $2"
    echo "        actual:   $3"
    FAILURES=$((FAILURES + 1))
  fi
}
calls() { grep -c "^$1|" "$CALLS"; }

export GH_REPO="example-owner/example-repo"
# shellcheck source=gh-issues.sh
source "$HERE/gh-issues.sh"

echo "owner/name from the git remote"
tmp="$(mktemp -d)"
git -C "$tmp" init -q
git -C "$tmp" remote add origin "git@github.com:an-owner/a-repo.git"
check "ssh remote" "an-owner/a-repo" "$(cd "$tmp" && repo_from_remote)"
git -C "$tmp" remote set-url origin "https://github.com/an-owner/a-repo.git"
check "https remote" "an-owner/a-repo" "$(cd "$tmp" && repo_from_remote)"
git -C "$tmp" remote set-url origin "https://github.com/an-owner/a-repo"
check "https remote without .git" "an-owner/a-repo" "$(cd "$tmp" && repo_from_remote)"
git -C "$tmp" remote remove origin
( cd "$tmp" && repo_from_remote ) >/dev/null 2>&1
check "no remote fails" "1" "$?"

echo "the project's repositories from .ai-dev-process.conf"
check "no conf: this repository" "example-owner/example-repo" "$(cd "$tmp" && project_repos)"
printf 'home_repo=o/home\nmember_repos=o/a  o/b \n' > "$tmp/.ai-dev-process.conf"
check "home first, then the members" "o/home o/a o/b" "$(cd "$tmp" && project_repos | tr '\n' ' ' | sed 's/ $//')"
printf 'home_repo=<owner>/<repository>\nmember_repos=\n' > "$tmp/.ai-dev-process.conf"
check "a placeholder counts as unset" "example-owner/example-repo" "$(cd "$tmp" && project_repos)"
rm -rf "$tmp"

echo "a new issue into a milestone"
reset
echo "example-owner/example-repo|003 Export|open" >> "$MILESTONES_DB"
out="$(create_issue "type:feature" "003 Export" "Export as CSV" <<< "A body"; echo "number=$LAST_ISSUE_NUMBER")"; code=$?
check "succeeds" "0" "$code"
check "reports it" "1" "$(grep -c '^created  https://github.com/example-owner/example-repo/issues/17' <<<"$out")"
check "sets the number" "number=17" "$(grep '^number=' <<<"$out")"
check "creates it in the milestone" "17|Export as CSV|003 Export" "$(cat "$ISSUES")"

echo "a new issue without a milestone"
reset
out="$(create_issue "idea" "" "Just an idea" <<< "A body")"; code=$?
check "succeeds" "0" "$code"
check "passes no --milestone" "0" "$(grep '^issue create|' "$CALLS" | grep -c -- '--milestone')"
check "looks up no milestone" "0" "$(calls 'api milestones')"

echo "a milestone the repository does not have"
reset
printf 'example-owner/example-repo|002 Scene|open\nexample-owner/example-repo|001 First|closed\n' >> "$MILESTONES_DB"
out="$(create_issue "type:feature" "003 Typo" "Export as CSV" <<< "A body")"; code=$?
check "fails" "1" "$code"
check "creates nothing" "0" "$(calls 'issue create')"
check "lists the open milestones" "002 Scene" "$(grep -E '^    ' <<<"$out" | sed 's/^ *//')"

echo "a closed milestone"
reset
echo "example-owner/example-repo|001 First|closed" >> "$MILESTONES_DB"
out="$(create_issue "type:feature" "001 First" "Export as CSV" <<< "A body")"; code=$?
check "fails" "1" "$code"
check "says it is closed" "1" "$(grep -c "is closed" <<<"$out")"
check "creates nothing" "0" "$(calls 'issue create')"

echo "an issue with the same title exists"
reset
echo "example-owner/example-repo|003 Export|open" >> "$MILESTONES_DB"
printf '5|Another title|\n9|Export as CSV|\n12|Export as CSV, longer|\n' > "$ISSUES"
out="$(create_issue "type:feature" "003 Export" "Export as CSV" <<< "A body"; echo "number=$LAST_ISSUE_NUMBER")"; code=$?
check "succeeds" "0" "$code"
check "reuses its number" "number=9" "$(grep '^number=' <<<"$out")"
check "says so" "1" "$(grep -c '^exists .*/issues/9 .*reused' <<<"$out")"
check "creates nothing" "0" "$(calls 'issue create')"
check "puts it into the milestone" "9|003 Export" "$(cat "$EDITS")"

echo "the same title twice, as a handover script run twice"
reset
for run in 1 2; do
  out="$(create_issue "type:bug" "" "Run me twice" <<< "A body" || exit 1)"; code=$?
  check "run $run succeeds" "0" "$code"
done
check "one issue exists" "1" "$(wc -l < "$ISSUES" | tr -d ' ')"

echo "several issues with that title"
reset
printf '30|Twin|\n21|Twin|\n' > "$ISSUES"
out="$(create_issue "type:bug" "" "Twin" <<< "A body"; echo "number=$LAST_ISSUE_NUMBER")"
check "reuses the oldest" "number=21" "$(grep '^number=' <<<"$out")"

# Handovers call the helpers as `create_issue … || exit 1`. Under `||` bash
# suspends `set -e` inside the function, so each gh call must be checked by
# the helper itself. Each case runs the documented form and asserts that the
# caller stops, and that the message names the step that failed.
echo "gh failing, called as a handover calls the helpers"
for step in "api milestones" "issue list" "issue create"; do
  reset
  echo "example-owner/example-repo|003 Export|open" >> "$MILESTONES_DB"
  out="$(GH_FAIL="$step"
         { create_issue "type:bug" "003 Export" "A title" <<< "A body" || exit 1
           echo "CARRIED ON"; } 2>&1)"; code=$?
  check "$step fails: the caller exits non-zero" "1" "$code"
  check "$step fails: the caller does not carry on" "0" "$(grep -c 'CARRIED ON' <<<"$out")"
  check "$step fails: the message names it" "1" "$(grep -c "^gh $step failed" <<<"$out")"
done
reset
echo "example-owner/example-repo|003 Export|open" >> "$MILESTONES_DB"
echo "9|A title|" > "$ISSUES"
out="$(GH_FAIL="issue edit"
       { create_issue "type:bug" "003 Export" "A title" <<< "A body" || exit 1
         echo "CARRIED ON"; } 2>&1)"; code=$?
check "issue edit fails: the caller exits non-zero" "1" "$code"
check "issue edit fails: the caller does not carry on" "0" "$(grep -c 'CARRIED ON' <<<"$out")"
check "issue edit fails: the message names it" "1" "$(grep -c '^gh issue edit failed' <<<"$out")"

echo "gh answers issue create without an issue url"
reset
out="$(FIXTURE_ISSUE_URL=""
       { create_issue "type:bug" "" "A title" <<< "A body" || exit 1
         echo "CARRIED ON"; } 2>&1)"; code=$?
check "the caller exits non-zero" "1" "$code"
check "the caller does not carry on" "0" "$(grep -c 'CARRIED ON' <<<"$out")"
check "nothing is reported as created" "0" "$(grep -c '^created' <<<"$out")"

echo "set_milestone"
reset
echo "example-owner/example-repo|003 Export|open" >> "$MILESTONES_DB"
out="$(set_milestone 44 "003 Export")"; code=$?
check "succeeds" "0" "$code"
check "edits the issue" "44|003 Export" "$(cat "$EDITS")"
reset
out="$({ set_milestone "" "003 Export" || exit 1; echo "CARRIED ON"; } 2>&1)"; code=$?
check "without an issue number: the caller exits non-zero" "1" "$code"
check "without an issue number: edits nothing" "" "$(cat "$EDITS")"

echo "ensure_milestone in every repository of the project"
tmp="$(mktemp -d)"
git -C "$tmp" init -q
printf 'home_repo=o/home\nmember_repos=o/code\n' > "$tmp/.ai-dev-process.conf"
reset
out="$(cd "$tmp" && ensure_milestone "003 Export" "Users can take the report into a spreadsheet.")"; code=$?
check "succeeds" "0" "$code"
check "creates it in both" "o/home|003 Export|open o/code|003 Export|open" "$(tr '\n' ' ' < "$MILESTONES_DB" | sed 's/ $//')"
check "passes the description" "2" "$(grep '^api create milestone|' "$CALLS" | grep -c 'description=Users can take the report into a spreadsheet.')"
: > "$CALLS"
out="$(cd "$tmp" && ensure_milestone "003 Export" "Users can take the report into a spreadsheet.")"; code=$?
check "run again: succeeds" "0" "$code"
check "run again: creates nothing" "0" "$(calls 'api create milestone')"
check "run again: says both exist" "2" "$(grep -c '^exists   milestone' <<<"$out")"
reset
echo "o/code|003 Export|closed" >> "$MILESTONES_DB"
out="$(cd "$tmp" && { ensure_milestone "003 Export" "D" || exit 1; echo "CARRIED ON"; } 2>&1)"; code=$?
check "a closed one: the caller exits non-zero" "1" "$code"
check "a closed one: says so" "1" "$(grep -c 'is closed' <<<"$out")"
reset
out="$(cd "$tmp" && GH_FAIL="api create milestone" && { ensure_milestone "003 Export" "D" || exit 1; echo "CARRIED ON"; } 2>&1)"; code=$?
check "create fails: the caller exits non-zero" "1" "$code"
check "create fails: the message names it" "1" "$(grep -c '^gh api create milestone failed' <<<"$out")"
check "create fails: stops at the first repository" "1" "$(calls 'api create milestone')"
reset
out="$(cd "$tmp" && ensure_milestone "003 Export" "D" o/code)"; code=$?
check "named repositories only" "o/code|003 Export|open" "$(cat "$MILESTONES_DB")"
rm -rf "$tmp"

rm -rf "$WORK"
echo
if [ "$FAILURES" -eq 0 ]; then
  echo "all checks passed"
else
  echo "$FAILURES check(s) failed"
  exit 1
fi

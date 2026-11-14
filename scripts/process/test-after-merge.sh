#!/usr/bin/env bash
# Managed by ai-dev-process.
#
# Exercise after-merge.sh with real git repositories in a temporary project
# folder and a stand-in for gh. Writes nothing to GitHub.
#
#   bash scripts/process/test-after-merge.sh

set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="$(mktemp -d)"
FAILURES=0
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t

# A stand-in gh: `gh pr list` answers $FIXTURE_PRS, or fails when GH_FAIL is set.
mkdir -p "$WORK/bin"
cat > "$WORK/bin/gh" <<'STANDIN'
#!/usr/bin/env bash
if [ -n "${GH_FAIL:-}" ]; then echo "stand-in refused: $*" >&2; exit 1; fi
case "$1 $2" in
  "pr list") echo "${FIXTURE_PRS:-[]}" ;;
  *) echo "unexpected gh call: $*" >&2; exit 2 ;;
esac
STANDIN
chmod +x "$WORK/bin/gh"
export PATH="$WORK/bin:$PATH"

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

# setup: a project folder with a repository whose branch feat/44-export was
# pushed and then merged on origin by rebase (same change, new commit).
# Sets REPO, ORIGIN, HEAD_SHA. Leaves the repository on the branch.
setup() {
  local case_dir="$WORK/$1"
  mkdir -p "$case_dir/project"
  ORIGIN="$case_dir/origin.git"
  git init -q --bare -b main "$ORIGIN"
  REPO="$case_dir/project/app"
  git init -q -b main "$REPO"
  git -C "$REPO" remote add origin "$ORIGIN"
  mkdir -p "$REPO/scripts/process"
  cp "$HERE/after-merge.sh" "$REPO/scripts/process/"
  git -C "$REPO" add -A && git -C "$REPO" commit -q -m init && git -C "$REPO" push -q origin main
  git -C "$REPO" switch -q -c feat/44-export
  echo "export" > "$REPO/export.txt"
  git -C "$REPO" add -A && git -C "$REPO" commit -q -m "feat: export"
  git -C "$REPO" push -q -u origin feat/44-export 2>/dev/null
  HEAD_SHA="$(git -C "$REPO" rev-parse HEAD)"
  # the rebase merge, done in a second clone
  git clone -q "$ORIGIN" "$case_dir/merger" 2>/dev/null
  git -C "$case_dir/merger" cherry-pick "$HEAD_SHA" >/dev/null
  git -C "$case_dir/merger" push -q origin main
  echo "body" > "$case_dir/project/pr-44-body.md"
}
merged() { echo "[{\"number\": 45, \"headRefOid\": \"$HEAD_SHA\", \"mergedAt\": \"2026-11-14T20:00:00Z\"}]"; }
run() { ( cd "$REPO" && bash scripts/process/after-merge.sh "$@" ) 2>&1; }
has_local() { git -C "$REPO" rev-parse -q --verify "refs/heads/$1" >/dev/null && echo yes || echo no; }
has_remote() { [ -n "$(git -C "$REPO" ls-remote --heads origin "refs/heads/$1")" ] && echo yes || echo no; }

echo "merged by rebase, nothing else on the branch"
setup a
out="$(FIXTURE_PRS="$(merged)" run feat/44-export)"; code=$?
check "succeeds" "0" "$code"
check "is on main" "main" "$(git -C "$REPO" branch --show-current)"
check "main has the merged change" "yes" "$([ -f "$REPO/export.txt" ] && echo yes || echo no)"
check "deletes the local branch" "no" "$(has_local feat/44-export)"
check "deletes the remote branch" "no" "$(has_remote feat/44-export)"
check "removes the pull request body" "no" "$([ -f "$WORK/a/project/pr-44-body.md" ] && echo yes || echo no)"
check "names the pull request" "1" "$(grep -c 'merged as #45' <<<"$out")"

echo "merged, but the local branch has a commit the pull request did not"
setup b
echo "later" > "$REPO/later.txt"
git -C "$REPO" add -A && git -C "$REPO" commit -q -m "feat: later"
out="$(FIXTURE_PRS="$(merged)" run feat/44-export)"; code=$?
check "succeeds" "0" "$code"
check "keeps the local branch" "yes" "$(has_local feat/44-export)"
check "says why" "1" "$(grep -c '^kept     feat/44-export (local)' <<<"$out")"
check "still deletes the remote branch, which is at the merged commit" "no" "$(has_remote feat/44-export)"

echo "merged, but the remote branch got a commit after the merge"
setup c
echo "late" > "$REPO/late.txt"
git -C "$REPO" add -A && git -C "$REPO" commit -q -m "feat: late" && git -C "$REPO" push -q origin feat/44-export 2>/dev/null
out="$(FIXTURE_PRS="$(merged)" run feat/44-export)"; code=$?
check "keeps the remote branch" "yes" "$(has_remote feat/44-export)"
check "keeps the local branch too" "yes" "$(has_local feat/44-export)"

echo "the remote branch was already deleted on merge"
setup d
git -C "$REPO" push -q origin --delete feat/44-export 2>/dev/null
out="$(FIXTURE_PRS="$(merged)" run feat/44-export)"; code=$?
check "succeeds" "0" "$code"
check "deletes the local branch" "no" "$(has_local feat/44-export)"
check "says the remote one is gone" "1" "$(grep -c '^gone     feat/44-export (remote)' <<<"$out")"

echo "not merged"
setup e
out="$(FIXTURE_PRS="[]" run feat/44-export)"; code=$?
check "succeeds" "0" "$code"
check "keeps the local branch" "yes" "$(has_local feat/44-export)"
check "keeps the remote branch" "yes" "$(has_remote feat/44-export)"
check "keeps the pull request body" "yes" "$([ -f "$WORK/e/project/pr-44-body.md" ] && echo yes || echo no)"
check "says why" "1" "$(grep -c 'no merged pull request' <<<"$out")"

echo "gh fails"
setup f
out="$(GH_FAIL=1 run feat/44-export)"; code=$?
check "fails" "1" "$code"
check "names the step" "1" "$(grep -c '^gh pr list failed' <<<"$out")"
check "keeps the local branch" "yes" "$(has_local feat/44-export)"

echo "without a branch, or with main"
out="$(run)"; check "no argument fails" "1" "$?"
out="$(run main)"; check "main is refused" "1" "$?"

rm -rf "$WORK"
echo
if [ "$FAILURES" -eq 0 ]; then
  echo "all checks passed"
else
  echo "$FAILURES check(s) failed"
  exit 1
fi

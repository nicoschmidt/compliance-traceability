#!/usr/bin/env bash
# Managed by ai-dev-process.
#
# Clean up after a pull request was merged, whatever the merge method:
#
#   bash scripts/process/after-merge.sh feat/44-export-csv
#
# Switches to main and fast-forwards it to origin/main. Deletes the local branch only when GitHub
# reports its pull request as merged and the branch points at that pull
# request's last commit; otherwise keeps it and says why. Deletes the remote
# branch on the same condition, if it still exists. Removes the pull request
# body ../pr-<issue>-body.md from the project folder, if it is there.
#
# Why not `git branch -d`: a rebase or squash merge rewrites the commits, so
# git calls the branch "not fully merged" although its content is on main,
# and the usual answer, `git branch -D`, throws away whatever was not pushed.
# The pull request's head commit is exact under every merge method.

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(git -C "$HERE" rev-parse --show-toplevel)"
cd "$ROOT"

fail() { echo "$1 failed: $2" >&2; exit 1; }

branch="${1:-}"
if [ "$#" -ne 1 ] || [ -z "$branch" ]; then
  echo "usage: bash scripts/process/$(basename "$0") <branch>"
  exit 1
fi
case "$branch" in
  main|master) echo "refusing to clean up '$branch'"; exit 1 ;;
esac
command -v gh >/dev/null || { echo "gh is not installed."; exit 1; }
command -v jq >/dev/null || { echo "jq is not installed: brew install jq"; exit 1; }

git fetch --prune origin || fail "git fetch" "could not update from origin"
git switch main || fail "git switch" "could not switch to main"
git merge --ff-only origin/main >/dev/null \
  || fail "git merge --ff-only" "main could not be fast-forwarded to origin/main"

prs="$(gh pr list --head "$branch" --state merged --limit 20 --json number,headRefOid,mergedAt)" \
  || fail "gh pr list" "could not ask GitHub whether $branch was merged"
pr="$(jq -r 'sort_by(.mergedAt) | last | .number // empty' <<<"$prs")" \
  || fail "gh pr list" "its answer is not a list of pull requests"
head="$(jq -r 'sort_by(.mergedAt) | last | .headRefOid // empty' <<<"$prs")"

if [ -z "$pr" ]; then
  echo "kept     $branch: GitHub reports no merged pull request for it"
  exit 0
fi

# The local branch
if local_sha="$(git rev-parse -q --verify "refs/heads/$branch")"; then
  if [ "$local_sha" = "$head" ]; then
    git branch -D "$branch" >/dev/null || fail "git branch -D" "could not delete $branch"
    echo "deleted  $branch (local), merged as #$pr"
  else
    echo "kept     $branch (local): it is at ${local_sha:0:7}, pull request #$pr ended at ${head:0:7};"
    echo "         look at what is not merged: git log --oneline $head..$branch"
  fi
else
  echo "gone     $branch (local)"
fi

# The remote branch
remote="$(git ls-remote --heads origin "refs/heads/$branch")" \
  || fail "git ls-remote" "could not read the branches on origin"
remote_sha="${remote%%[[:space:]]*}"
if [ -z "$remote" ]; then
  echo "gone     $branch (remote)"
elif [ "$remote_sha" = "$head" ]; then
  git push origin --delete "$branch" >/dev/null 2>&1 || fail "git push --delete" "could not delete $branch on origin"
  git fetch --prune origin >/dev/null 2>&1 || true
  echo "deleted  $branch (remote)"
else
  echo "kept     $branch (remote): it has commits pull request #$pr did not merge"
fi

# The pull request body in the project folder
issue="$(sed -n 's|^[a-z]*/\([0-9][0-9]*\)-.*|\1|p' <<<"$branch")"
if [ -n "$issue" ] && [ -f "../pr-$issue-body.md" ]; then
  rm "../pr-$issue-body.md"
  echo "removed  ../pr-$issue-body.md"
fi

#!/usr/bin/env bash
# Managed by ai-dev-process.
#
# Shared helpers for handing over issues with their label and milestone
# already set, and for creating an iteration's milestone in every repository
# of the project. Sourced by the one-off create-*.sh scripts that live in the
# project folder. Not run on its own.
#
#   source scripts/process/gh-issues.sh
#   issues_connect
#   create_issue "type:feature" "003 Export" "Export the report as CSV" < ../issue-export-body.md || exit 1
#   set_milestone 44 "003 Export" || exit 1
#   ensure_milestone "003 Export" "Users can take the report into a spreadsheet." || exit 1
#
# Needs gh and jq, and no `project` scope: nothing here touches a board.
# The repository comes from the git remote of the checkout the script runs in,
# or from GH_REPO=owner/name for one run. The project's repositories come from
# .ai-dev-process.conf at the top of that checkout (home_repo, member_repos).
#
# Every failure is propagated explicitly, every gh call included. Handovers
# call these helpers as `create_issue … || exit 1`, and under `||`, `&&`, `if`
# and `!` bash suspends `set -e` for everything the function runs: a check left
# to `set -e` is no check, and a failed gh call was once followed by a success
# message. Each message names the gh step that failed.

GH_REPO="${GH_REPO:-}"
LAST_ISSUE_URL=""
LAST_ISSUE_NUMBER=""

# conf_get <key>: the value from .ai-dev-process.conf at the top of the current
# checkout. Empty when the file or the key is missing, or the value is still a
# <placeholder>. The file is read, never sourced: it is data, not code.
conf_get() {
  local root file value
  root="$(git rev-parse --show-toplevel 2>/dev/null)" || return 0
  file="$root/.ai-dev-process.conf"
  [ -f "$file" ] || return 0
  value="$(sed -n "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*//p" "$file" | tail -n 1)"
  value="${value%"${value##*[![:space:]]}"}"
  case "$value" in *'<'*) value="" ;; esac
  printf '%s' "$value"
}

# owner/name from the git remote of the current checkout.
repo_from_remote() {
  local url
  url="$(git remote get-url origin 2>/dev/null)" || return 1
  url="${url%.git}"
  url="${url#git@github.com:}"
  url="${url#ssh://git@github.com/}"
  url="${url#https://github.com/}"
  case "$url" in
    */*) echo "$url" ;;
    *) return 1 ;;
  esac
}

issues_connect() {
  command -v gh >/dev/null || { echo "gh is not installed."; return 1; }
  command -v jq >/dev/null || { echo "jq is not installed: brew install jq"; return 1; }
  command -v git >/dev/null || { echo "git is not installed."; return 1; }
  if [ -z "$GH_REPO" ]; then
    GH_REPO="$(repo_from_remote)" || {
      echo "Could not read owner/name from the git remote of $(pwd)."
      echo "Run this from the repository, or set GH_REPO=owner/name."
      return 1
    }
  fi
  export GH_REPO
  echo "Repository: $GH_REPO"
}

# project_repos: the home repository and the members from .ai-dev-process.conf,
# one per line. Just GH_REPO when the conf names no home repository.
project_repos() {
  local home members r
  home="$(conf_get home_repo)"
  members="$(conf_get member_repos)"
  if [ -z "$home" ]; then
    echo "$GH_REPO"
    return 0
  fi
  echo "$home"
  for r in $members; do echo "$r"; done
}

# milestone_state <title> <repo>: sets MILESTONE_STATE to open, closed or
# nothing, and MILESTONES to the repository's list, for a message. Not a
# command substitution: that would run it in a subshell and throw both away.
# Fails only when gh does.
MILESTONES=""
MILESTONE_STATE=""
milestone_state() {
  MILESTONE_STATE=""
  MILESTONES="$(gh api "repos/$2/milestones?state=all&per_page=100")" \
    || { echo "gh api milestones failed for $2."; return 1; }
  MILESTONE_STATE="$(jq -r --arg t "$1" \
    'first(.[] | select(.title == $t) | .state) // empty' <<<"$MILESTONES")" \
    || { echo "gh api milestones answered something that is not a list, for $2."; return 1; }
}

# milestone_check <title>: succeeds if the repository has an open milestone of
# that title; otherwise says why and lists the open ones it does have.
milestone_check() {
  local title="$1"
  milestone_state "$title" "$GH_REPO" || return 1
  case "$MILESTONE_STATE" in
    open) return 0 ;;
    closed) echo "Milestone '$title' in $GH_REPO is closed." ;;
    *)
      echo "No milestone '$title' in $GH_REPO. Its open milestones:"
      jq -r '.[] | select(.state == "open") | "    \(.title)"' <<<"$MILESTONES"
      ;;
  esac
  return 1
}

# set_milestone <issue number> <milestone title>: puts an existing issue into
# a milestone, which is what makes a refined issue ready.
set_milestone() {
  local n="$1" milestone="$2"
  [[ "$n" =~ ^[0-9]+$ ]] || { echo "'$n' is not an issue number; no milestone set."; return 1; }
  milestone_check "$milestone" || return 1
  gh issue edit "$n" --milestone "$milestone" >/dev/null \
    || { echo "gh issue edit failed: #$n was not put into '$milestone'."; return 1; }
  echo "         #$n milestone = $milestone"
}

# create_issue <label> <milestone title, or ""> <title>, body on stdin.
#
# An issue with exactly this title, open or closed, is reused instead of
# created again, and put into the milestone. A handover script that failed
# halfway can then simply be run again; run twice, it once created every
# issue twice. The lookup lists the issues rather than searching them,
# because the search index lags behind a create by seconds. The milestone is
# checked before anything is created.
create_issue() {
  local label="$1" milestone="$2" title="$3" body issues existing url
  local -a args
  body="$(cat)"
  LAST_ISSUE_URL=""
  LAST_ISSUE_NUMBER=""
  if [ -n "$milestone" ]; then
    milestone_check "$milestone" || return 1
  fi
  issues="$(gh issue list --state all --limit 1000 --json number,title,url)" \
    || { echo "gh issue list failed: could not check whether '$title' exists."; return 1; }
  existing="$(jq -r --arg t "$title" \
    '[.[] | select(.title == $t)] | sort_by(.number) | first | .url // empty' <<<"$issues")" \
    || { echo "gh issue list answered something that is not a list of issues."; return 1; }
  if [ -n "$existing" ]; then
    LAST_ISSUE_URL="$existing"
    LAST_ISSUE_NUMBER="${existing##*/}"
    echo "exists   $existing   (same title; reused, not created again)"
    if [ -n "$milestone" ]; then
      set_milestone "$LAST_ISSUE_NUMBER" "$milestone" || return 1
    fi
    return 0
  fi
  args=(--label "$label" --title "$title" --body "$body")
  if [ -n "$milestone" ]; then args+=(--milestone "$milestone"); fi
  url="$(gh issue create "${args[@]}")" \
    || { echo "gh issue create failed: '$title' was not created."; return 1; }
  if ! [[ "${url##*/}" =~ ^[0-9]+$ ]]; then
    echo "gh issue create answered '$url', which names no issue; check whether '$title' exists."
    return 1
  fi
  LAST_ISSUE_URL="$url"
  LAST_ISSUE_NUMBER="${url##*/}"
  echo "created  $url"
  if [ -n "$milestone" ]; then echo "         milestone = $milestone"; fi
}

# ensure_milestone <title> <description> [repo ...]: an open milestone of this
# title in each repository, created where it is missing. Without repositories:
# every repository of the project (project_repos). A closed milestone of the
# same title is an error, not something to reopen silently.
ensure_milestone() {
  local title="$1" description="$2" repo
  local -a repos
  shift 2
  if [ "$#" -gt 0 ]; then
    repos=("$@")
  else
    while IFS= read -r repo; do
      [ -n "$repo" ] && repos+=("$repo")
    done < <(project_repos)
  fi
  for repo in "${repos[@]}"; do
    milestone_state "$title" "$repo" || return 1
    case "$MILESTONE_STATE" in
      open) echo "exists   milestone '$title' in $repo" ;;
      closed)
        echo "Milestone '$title' in $repo is closed: reopen it on GitHub, or choose another title."
        return 1
        ;;
      *)
        gh api "repos/$repo/milestones" -f title="$title" -f description="$description" >/dev/null \
          || { echo "gh api create milestone failed: '$title' was not created in $repo."; return 1; }
        echo "created  milestone '$title' in $repo"
        ;;
    esac
  done
}

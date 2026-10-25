#!/usr/bin/env bash
# Managed by ai-dev-process.
#
# Shared helpers for handing over issues with their board fields already set.
# Sourced by the other scripts in this directory, and by the one-off
# create-*.sh scripts that live beside the repository. Not run on its own.
#
# Needs the `project` scope, which `gh auth login` does not grant:
#
#   gh auth refresh -s project
#
# Field and option identifiers are resolved by name every run. A field name is
# given as a `|`-separated list of candidates, because the board's own wording
# is the authority and this file is not: the first candidate that exists wins.
# Run scripts/process/show-board.sh to see what the board actually calls things.

# Nothing here names a person, a repository or a board. The repository comes
# from the git remote of the checkout the script is run in; the board from
# .ai-dev-process.conf at the top of that checkout (board_owner,
# board_number). Each can be overridden for one run:
#
#   GH_REPO=owner/name        the repository these issues belong to
#   PROJECT_OWNER=name        the board's owner
#   PROJECT_NUMBER=n          the board's number
#   FIELD_SIZE, FIELD_ITERATION   candidate names for the two fact fields
#
# Without either, the board's owner is the repository's owner, and the board
# is that owner's only one — which stops working the day a second board exists.
GH_REPO="${GH_REPO:-}"
OWNER="${PROJECT_OWNER:-}"
NUMBER="${PROJECT_NUMBER:-}"

BOARD_FIELD_ID=""
BOARD_FIELD_NAME=""
LAST_ISSUE_URL=""
LAST_ISSUE_NUMBER=""

FIELD_SIZE="${FIELD_SIZE:-Size|Größe}"
FIELD_ITERATION="${FIELD_ITERATION:-Iteration}"

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
board_repo() {
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

board_connect() {
  command -v gh >/dev/null || { echo "gh is not installed."; return 1; }
  command -v jq >/dev/null || { echo "jq is not installed: brew install jq"; return 1; }
  command -v git >/dev/null || { echo "git is not installed."; return 1; }

  if [ -z "$GH_REPO" ]; then
    GH_REPO="$(board_repo)" || {
      echo "Could not read owner/name from the git remote of $(pwd)."
      echo "Run this from the repository, or set GH_REPO=owner/name."
      return 1
    }
  fi
  local from="environment"
  [ -n "$OWNER" ] || OWNER="$(conf_get board_owner)"
  [ -n "$OWNER" ] || OWNER="${GH_REPO%%/*}"
  if [ -z "$NUMBER" ]; then
    NUMBER="$(conf_get board_number)"
    from=".ai-dev-process.conf"
  fi
  case "$NUMBER" in
    '') ;;
    *[!0-9]*) echo "The board number '$NUMBER' (from $from) is not a number."; return 1 ;;
  esac

  if [ -z "$NUMBER" ]; then
    local projects count
    projects="$(gh project list --owner "$OWNER" --format json)"
    count="$(jq '.projects | length' <<<"$projects")"
    if [ "$count" != "1" ]; then
      echo "Found $count projects for owner '$OWNER', and no board_number in .ai-dev-process.conf."
      echo "Write the right one there, as board_number=<n>, or set it for one run:"
      jq -r '.projects[] | "  PROJECT_NUMBER=\(.number)  \(.title)"' <<<"$projects"
      return 1
    fi
    NUMBER="$(jq -r '.projects[0].number' <<<"$projects")"
    from="the owner's only board"
  fi

  PROJECT_ID="$(gh project view "$NUMBER" --owner "$OWNER" --format json | jq -r '.id')"
  FIELDS="$(gh project field-list "$NUMBER" --owner "$OWNER" --format json)"
  echo "Board: $OWNER #$NUMBER ($from)   repository: $GH_REPO"
}

board_show() {         # every field, and the options of every single select
  jq -r '.fields[] | "\(.name)  [\(.type)]" +
           ((.options // []) | map("\n    \(.name)") | join(""))' <<<"$FIELDS"
}

# Sets BOARD_FIELD_ID and BOARD_FIELD_NAME. Not a command substitution: that
# would run it in a subshell and throw both away.
board_field_id() {     # board_field_id "Size|Größe"
  local candidates="$1" name id
  BOARD_FIELD_ID=""
  BOARD_FIELD_NAME=""
  while IFS= read -r name; do
    [ -n "$name" ] || continue
    id="$(jq -r --arg f "$name" '.fields[] | select(.name == $f) | .id' <<<"$FIELDS")"
    if [ -n "$id" ] && [ "$id" != "null" ]; then
      BOARD_FIELD_ID="$id"
      BOARD_FIELD_NAME="$name"
      return 0
    fi
  done < <(tr '|' '\n' <<<"$candidates")
  return 1
}

board_set_field() {    # board_set_field <item-id> <"A|B"> <option name>
  local item="$1" candidates="$2" option="$3" option_id
  if ! board_field_id "$candidates"; then
    echo "No field named any of '$candidates' on this board. What it has:"
    board_show
    return 1
  fi
  option_id="$(jq -r --arg f "$BOARD_FIELD_NAME" --arg o "$option" \
    '.fields[] | select(.name == $f) | .options[]? | select(.name == $o) | .id' <<<"$FIELDS")"
  if [ -z "$option_id" ] || [ "$option_id" = "null" ]; then
    echo "Field '$BOARD_FIELD_NAME' has no option '$option'. Options it has:"
    jq -r --arg f "$BOARD_FIELD_NAME" \
      '.fields[] | select(.name == $f) | .options[]? | "    \(.name)"' <<<"$FIELDS"
    return 1
  fi
  gh project item-edit --id "$item" --project-id "$PROJECT_ID" \
    --field-id "$BOARD_FIELD_ID" --single-select-option-id "$option_id" >/dev/null
  echo "         $BOARD_FIELD_NAME = $option"
}

board_item_for_issue() {   # board_item_for_issue <issue number> -> item id
  local n="$1" item
  item="$(gh project item-list "$NUMBER" --owner "$OWNER" --format json --limit 500 \
    | jq -r --argjson n "$n" \
      'first(.items[] | select(.content.type == "Issue" and .content.number == $n) | .id) // empty')"
  if [ -z "$item" ]; then
    item="$(gh project item-add "$NUMBER" --owner "$OWNER" \
      --url "https://github.com/$GH_REPO/issues/$n" \
      --format json | jq -r '.id')"
  fi
  echo "$item"
}

# Every failure is propagated explicitly. Leaving that to `set -e` in the
# calling script means a failed lookup is followed by a success message.
set_issue_fields() {   # set_issue_fields <issue number> <size> <iteration>
  local n="$1" size="$2" iteration="$3" item
  item="$(board_item_for_issue "$n")" || return 1
  board_set_field "$item" "$FIELD_SIZE" "$size" || return 1
  board_set_field "$item" "$FIELD_ITERATION" "$iteration" || return 1
  echo "set      #$n   size: $size   iteration: $iteration"
}

# create_issue <label> <size> <iteration> <title>, body on stdin.
# Status is never set here: it is the maintainer's judgement, not a fact.
create_issue() {
  local label="$1" size="$2" iteration="$3" title="$4" body url
  body="$(cat)"
  url="$(gh issue create --label "$label" --title "$title" --body "$body")"
  LAST_ISSUE_URL="$url"
  LAST_ISSUE_NUMBER="${url##*/}"
  echo "created  $url"
  set_issue_fields "$LAST_ISSUE_NUMBER" "$size" "$iteration" || return 1
}

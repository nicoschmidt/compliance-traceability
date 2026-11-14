<!-- Managed by ai-dev-process. Do not edit in a project: change it upstream, or record a deviation in CLAUDE.md. -->

# Handover

The maintainer performs every step that reaches GitHub: creating issues,
pushing, opening pull requests, reviewing, merging, cleaning up. Those steps
are gates, and they stay manual deliberately. The single exception is a
dictated `idea` issue (`workflow.md`).

## Manual does not mean unassisted

**Every manual step is handed over ready to run.** For each one, provide:

- the exact text where text is needed — issue body, pull request body —
  written to a file **beside** the repository, never inside it
- the exact command as a copy-paste block, with real values filled in: real
  issue numbers, branch names and paths, no placeholder left to resolve
- the steps in the order they must be executed

Never tell the maintainer to "create an issue", "open a pull request" or "set
the field". Hand over the artefact and the command. The maintainer's work is
reading, judging and executing — never composing. A command that still holds a
placeholder, or a step that arrives as an instruction, is a defect.

## Facts arrive set, on the issue

- An issue arrives with its facts in the same block that creates it: its
  `type:` label and, once it is refined, its milestone
  (`gh issue create --label … --milestone …`). Nothing is set on a board.
- **Readiness is the maintainer's judgement**, and it is made visibly: by
  assigning the milestone in refinement, in a command the maintainer reads
  before running it. No status is kept by hand, and none is handed over.
- Milestone titles and labels are read from GitHub at run time, not from
  memory and not from an older script. A lookup that fails prints what the
  repository does have.
- **Commands run in the project folder** (`repositories.md`) and name no
  absolute path, because where the project folder lives differs per machine
  and per developer. A copy-paste block starts with `cd <repository>` and
  ends with `cd ..`, so the next block starts in the project folder again; a
  script in the project folder starts with
  `cd "$(dirname "$0")/<repository>"`, so it runs from anywhere. A `gh` call
  aimed at another repository carries `--repo owner/name`. A block that does
  not say which repository it runs in is a defect.
- Where a step genuinely cannot be a command — a review, a merge, a repository
  setting — name the exact path through the interface.

## Scripts that write to GitHub are run before they are handed over

A handover script is exercised against a stand-in for `gh` first, and fails
loudly rather than reporting a success it did not achieve. An environment
without credentials has otherwise never run the script at all, and the
maintainer discovering that by pasting it is not a review, it is a wasted
evening. The harness is `scripts/process/test-gh-issues.sh`.

## Content beside the repository, tooling inside it

The line runs between **content and tooling**, not between one-off and
reusable.

- **Content is not committed.** A drafted issue body, a pull request body, and
  the one-off `create-*.sh` that carries one live beside the repository, in
  the project folder (`../pr-<n>-body.md` seen from inside the repository).
  Inside, they would be a second task list next to GitHub issues. Delete them
  once they have run.
- **Tooling is committed**, under `scripts/`. It carries no work items — it
  creates an issue, sets its milestone, tests itself — and it changes in the same
  reviewed commit as the rules it implements.

## The one thing the assistant does itself

The assistant creates the local branch, because it cannot commit without one.
A local branch reaches nobody, so it is not a gate — the push is. The
maintainer is free to rename or discard it.

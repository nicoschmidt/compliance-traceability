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

## Facts are set, judgements are not

- Board fields that are facts about the work — size, iteration — arrive set:
  `gh project item-edit` in the same block as `gh issue create`, through
  `scripts/process/gh-board.sh`.
- **Status is the maintainer's click.** Moving a card to `Ready`, `In review`
  or `Done` is a judgement about whether the work is there yet; handing it over
  as a command would hand over the judgement with it.
- The board is the one named in `.ai-dev-process.conf`; the helpers read it
  from there. Field and option names come from the board, read at run time —
  not from memory and not from an older script. A lookup that fails prints
  what the board does have.
- Every block says which repository it runs in: a `cd` to its absolute path,
  or `--repo owner/name`. In a project of several repositories, a command
  without one is a defect.
- Where a step genuinely cannot be a command — a review, a merge, a repository
  setting — name the exact path through the interface.

## Scripts that write to GitHub are run before they are handed over

A handover script is exercised against a stand-in for `gh` first, and fails
loudly rather than reporting a success it did not achieve. An environment
without credentials has otherwise never run the script at all, and the
maintainer discovering that by pasting it is not a review, it is a wasted
evening. The harness is `scripts/process/test-gh-board.sh`.

## Content beside the repository, tooling inside it

The line runs between **content and tooling**, not between one-off and
reusable.

- **Content is not committed.** A drafted issue body, a pull request body, and
  the one-off `create-*.sh` that carries one live beside the repository
  (`../pr-<n>-body.md`, `../create-*.sh`). Inside, they would be a second task
  list next to GitHub issues. Delete them once they have run.
- **Tooling is committed**, under `scripts/`. It carries no work items — it
  reads the board, sets a field, tests itself — and it changes in the same
  reviewed commit as the rules it implements.

## The one thing the assistant does itself

The assistant creates the local branch, because it cannot commit without one.
A local branch reaches nobody, so it is not a gate — the push is. The
maintainer is free to rename or discard it.

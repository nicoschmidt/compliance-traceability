<!-- Managed by ai-dev-process. Do not edit in a project: change it upstream, or record a deviation in CLAUDE.md. -->

# Process

How work moves through this project, written for the maintainer.

The rules are in `.claude/rules/process/` and in `CLAUDE.md`, and they are
binding. This document is the walkthrough: what to do next, and where to
click. **Where the two disagree, the rules win** — and that is a defect to
fix, not a choice to make.

## Where am I?

| What the maintainer wants | What to do next |
| --- | --- |
| Something came to mind, no time now | Capture it as an `idea` issue — see [Capture](#capture). Seconds, not minutes. |
| The inbox is filling up | A refinement session: `/ai-dev-process:refine-backlog` |
| Start something new | Is there a ready issue? If not, refine one. Then set it to `Ready`; the assistant creates the branch. |
| Work was prepared in a chat session | Read the local branch diff, push it, open the pull request. |
| A pull request is open | Review it, tick the definition of done, merge. |
| A pull request was merged | Run the cleanup block in step 8 below; card to `Done`. |
| A decision that is hard to reverse | Write the ADR **before** the code: `/ai-dev-process:write-adr` |
| An iteration goal is reached | Retro: `/ai-dev-process:close-iteration` |
| Something feels too big | Set its size to `L`. It is cut before it enters an iteration. |
| The process itself gets in the way | Capture a `process` idea. The retro will find it. |
| Lost the thread | Open the board, filter `Status: In progress`. That is what is actually started. |

## Capture

An idea is captured where it occurs, in whichever way is nearest:

- **Phone or browser:** New issue → **Idea**. The title is enough.
- **Terminal:**
  `bash scripts/process/capture-idea.sh "<title>"` — add `--process` for the
  way of working. For an idea about the whole project, from a member
  repository: `GH_REPO=<home repository> bash scripts/process/capture-idea.sh "<title>"`.
- **A chat session:** say "Idee: …". The assistant writes the title and a
  prefilled link to the Idea form; one tap submits it.
- **Claude Code:** say "capture: …". It creates the issue directly — the one
  GitHub step it may take itself.

Ideas are never worked on as they are. Ideas about the process stay in this
repository with the `process` label until the retro decides whether they are
`[project]` or `[generic]`.

## Refinement

A refinement session empties the inbox. For each open `idea` issue:

- **close** it as not planned, with one line why — most ideas deserve this,
  and that is fine
- **merge** it into an existing issue, and close it as a duplicate
- **transfer** it to the process repository when it is clearly generic
- **refine** it: rewrite it to a template, checkable acceptance criteria, size
  and iteration — until it meets the definition of ready in
  `.claude/rules/process/workflow.md`

Every outcome is handed over as one block to paste. `Ready` stays a click.

## What the maintainer gets handed, and what they do

The maintainer owns every step that reaches GitHub, and composes none of them.
For each step the assistant hands over the finished artefact and the command:
the issue text, the pull request body, the exact `git`/`gh` invocation with
real numbers and paths. Size and iteration arrive set; status does not.

Drafted bodies live beside the repository (`../pr-<n>-body.md`,
`../create-*.sh`) and are never committed. The tooling they use lives under
`scripts/process/`.

So the maintainer's part is: read it, judge it, paste it. A command with a
placeholder still in it, or a step that arrives as an instruction rather than
a command, is a defect — say so.

## The standard cycle

1. **Issue.** From refinement, or written directly from a template: feature,
   bug or spike.
   → *Handed over:* the body and a block that creates the issue and sets size
   and iteration. Needs the `project` scope once: `gh auth refresh -s project`
2. **`Ready`.** → *The maintainer's click.*
3. **Branch.** `<type>/<issue>-<slug>`, created by the assistant so it can
   commit. → *Nothing to do;* the branch stays local until step 5.
4. **Work.** Chat for product and architecture; Claude Code against the code.
5. **`In review`.** → *Handed over:* `../pr-<n>-body.md`, plus `git push` and
   `gh pr create --body-file …` with the values filled in. Read the body first.
6. **Review.** Tick the checklist for real. Line-level changes as review
   suggestions; questions about the goal on the issue; "is this even right" in
   a chat session. → *The maintainer's alone.*
7. **Merge.** → *The maintainer's alone.* The assistant never merges.
8. **After.** → *Handed over,* with the branch name filled in:

   ```bash
   git switch main && git pull
   git branch -d <branch>                  # local
   git push origin --delete <branch>       # remote, if it still exists
   git fetch --prune
   ```

   `gh repo edit --delete-branch-on-merge` makes the remote half unnecessary.

## Several repositories

A project may be one repository or several; `.ai-dev-process.conf` names the
board, the home repository and the members, and
`.claude/rules/process/repositories.md` says what lives where. In short:

- vision, ADRs, iterations and epics are in the home repository; code and
  data, with their own issues, in the members
- all repositories are checked out beside each other; a member's `CLAUDE.md`
  imports the home repository's
- one board for all of them; one issue and one pull request per repository
  for work that spans several, under an epic in the home repository
- nothing from a private repository reaches a public one

## When something goes wrong

**Branch has fallen behind `main`**

```bash
git switch main && git pull
git switch <branch> && git rebase main
```

**Committed on `main` by accident** — do not push. The pre-commit hook should
have stopped it; check `git config core.hooksPath` says `.githooks`. Then:

```bash
git branch <rescue-branch>          # keeps the commits
git reset --hard origin/main        # main back to the remote state
git switch <rescue-branch>
```

**Two pieces of work want the same file.** Put them on one branch and say so
in the pull request, or finish the first and rebase the second.

**An iteration keeps growing.** Cut the goal, move the remainder to issues.

**A decision was made without an ADR.** Stop, write it, then continue.

**A handover script says it found several boards.** `board_number` in
`.ai-dev-process.conf` is not set yet. `gh project list --owner <owner>`
shows the numbers; write the right one there, in every repository of the
project.

**A handover script says a field or an option does not exist.** The board is
the authority:

```bash
bash scripts/process/show-board.sh
```

**CI says a managed file changed.** It was edited here. Restore it, and put
the change where it belongs — upstream, or as a deviation in `CLAUDE.md`:

```bash
bash scripts/process/check-kit.sh
```

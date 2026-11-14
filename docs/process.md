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
| Start something new | Is there a ready issue in the current milestone? If not, refine one: putting it in a milestone makes it ready. The assistant checks, then creates the branch. |
| Something matters more right now | Write it as an issue in the current milestone, or in a new milestone before it. It is never built without an issue. |
| Work was prepared in a chat session | Read the local branch diff, push it, open the pull request. |
| A pull request is open | Review it, tick the definition of done, merge. |
| A pull request was merged | Run the cleanup block in step 8 below. |
| A decision that is hard to reverse | Write the ADR **before** the code: `/ai-dev-process:write-adr` |
| An iteration goal is reached, or its milestone is empty | Move what is open, close the milestone, retro: `/ai-dev-process:close-iteration` |
| Something feels too big | Cut it into issues that each fit one pull request, before it enters a milestone. |
| The process itself gets in the way | Capture a `process` idea. The retro will find it. |
| Lost the thread | Open the current milestone: its open issues with a linked pull request are in review, the rest are still to do. |

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
- **refine** it: rewrite it to a template, checkable acceptance criteria, what
  it needs, and a milestone — until it meets the definition of ready in
  `.claude/rules/process/workflow.md`

Every outcome is handed over as one block to paste. Putting an issue in a
milestone is the decision that it is ready.

## What the maintainer gets handed, and what they do

The maintainer owns every step that reaches GitHub, and composes none of them.
For each step the assistant hands over the finished artefact and the command:
the issue text, the pull request body, the exact `git`/`gh` invocation with
real numbers and paths. Label and milestone arrive set; no status is kept by
hand.

Drafted bodies live beside the repository, in the project folder
(`pr-<n>-body.md`, `create-*.sh`), and are never committed. Every command
handed over runs in the project folder and names no absolute path. The tooling they use lives under
`scripts/process/`.

So the maintainer's part is: read it, judge it, paste it. A command with a
placeholder still in it, or a step that arrives as an instruction rather than
a command, is a defect — say so.

## The standard cycle

1. **Issue.** From refinement, or written directly from a template: feature,
   bug or spike.
   → *Handed over:* the body and a block that creates the issue with its label
   and milestone.
2. **Ready.** It is in a milestone, with a `type:` label and no `idea`. → *The
   maintainer's decision, made by the milestone.* The assistant checks it
   before it starts, and stops if it does not hold.
3. **Branch.** `<type>/<issue>-<slug>`, created by the assistant so it can
   commit. → *Nothing to do;* the branch stays local until step 5.
4. **Work.** Chat for product and architecture; Claude Code against the code.
5. **Pull request.** → *Handed over:* `../pr-<n>-body.md`, plus `git push` and
   `gh pr create --body-file …` with the values filled in. Read the body first.
6. **Review.** Tick the checklist for real. Line-level changes as review
   suggestions; questions about the goal on the issue; "is this even right" in
   a chat session. Something that should be different before the merge goes
   back to the session: it commits the correction to the same branch, says
   whether it looks like an extension instead, and hands over the push and the
   amended criterion for the issue. → *The maintainer's alone.*
7. **Merge.** → *The maintainer's alone.* The assistant never merges.
8. **After.** → *Handed over,* with the branch name filled in:

   ```bash
   cd <repository>
   bash scripts/process/after-merge.sh <branch>
   cd ..
   ```

   It deletes the branch only where it is at the merged pull request's last
   commit, under any merge method, and keeps it with the reason otherwise.
   `gh repo edit --delete-branch-on-merge` saves it the remote half.

## Several repositories

A project may be one repository or several; `.ai-dev-process.conf` names the
home repository and the members, and `.claude/rules/process/repositories.md`
says what lives where. In short:

- vision, ADRs and iterations are in the home repository; code and data, with
  their own issues, in the members
- all repositories are checked out in the project folder; a member's
  `CLAUDE.md` imports the home repository's
- an iteration is a milestone of the same title in every repository with
  issues in it; work that spans several repositories is one issue and one
  pull request per repository, in that milestone
- nothing from a private repository reaches a public one

## When something goes wrong

**Branch has fallen behind `main`**, or it started before the previous pull
request was merged:

```bash
git fetch origin
git switch <branch> && git rebase origin/main
git push --force-with-lease      # only if the branch was pushed already
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

**An iteration keeps growing.** Check that every addition is an issue in the
milestone. When the goal is met, close the milestone and move the rest on.

**A decision was made without an ADR.** Stop, write it, then continue.

**CI says a managed file changed.** It was edited here. Restore it, and put
the change where it belongs — upstream, or as a deviation in `CLAUDE.md`:

```bash
bash scripts/process/check-kit.sh
```

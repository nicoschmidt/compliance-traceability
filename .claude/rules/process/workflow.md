<!-- Managed by ai-dev-process. Do not edit in a project: change it upstream, or record a deviation in CLAUDE.md. -->

# Workflow

Binding for every assistant working in this repository. Project-specific
values — languages, the iteration's done criterion, extra rules — are in
`CLAUDE.md` under **Process parameters** (in a member repository, the home
repository's `CLAUDE.md`, which it imports). Where `CLAUDE.md` records a
**Process deviation**, the deviation wins. Which repositories belong to the
project, and where each kind of work lives, is in `repositories.md`.

## Issues are the only task list

- GitHub issues are the single source of truth for work items. No TODO files,
  no backlog in markdown, no list in a branch.
- An issue lives in the repository whose contents it changes; work for the
  whole project, and the epics, live in the home repository.
- **No work without an issue.** Before the first edit, name the issue and the
  branch. If no issue exists, write one first — or, where the environment
  cannot create it, draft it and hand it over (see `handover.md`).

## Ideas are captured at once, and refined later

An idea noticed in passing is worth seconds now and is gone by the next
session. So capturing it is cheap and refining it is a separate step.

- **Capture** is an issue with the label `idea`: a title, and a line or two if
  they come for free. Nothing else is required — no acceptance criteria, no
  size. The `Idea` issue template is exactly that.
- Observations about the *way of working* rather than the product carry the
  label `process` as well. The retro reads them; see `iterations.md`.
- When the maintainer mentions an idea in passing ("we should…", "at some
  point…"), offer to capture it — one sentence, not a discussion.
- Creating an `idea` issue that the maintainer has dictated is the one
  GitHub-facing step an assistant with credentials may take directly. An idea
  commits nobody to anything, and capture must cost seconds. Everything else in
  `handover.md` still applies.
- **An `idea` issue is never worked on.** It leaves the inbox only through
  refinement (below).

## Definition of ready

Refinement turns an idea into work, or closes it. An issue is ready when:

1. it uses one of the templates — feature, bug or spike — and carries the
   matching `type:` label instead of `idea`
2. its acceptance criteria are checkable statements, not intentions
3. it is small enough for one pull request; anything sized `L` is cut first
4. it names what it needs: the ADR it depends on, or "none"
5. size and iteration are set on the board

Moving it to `Ready` on the board stays the maintainer's click.

## Branches, commits, pull requests

- **Never commit to `main`.** Not for documentation, not for a one-line fix,
  not because the change is obviously correct. There is no threshold below
  which this stops applying. The `.githooks/pre-commit` hook refuses such a
  commit; it is a backstop, not the rule.
- Branch name: `<type>/<issue>-<slug>`, for example
  `feat/42-export-csv`. Branch types are listed in `CLAUDE.md`.
  Every branch has an issue, so every branch carries its number.
- GitHub numbers issues and pull requests in one sequence. Read the number
  from GitHub; never predict it.
- One pull request per issue. The body references the issue (`Closes #n`) and
  fills in the template rather than restating the commits.
- **Never merge your own pull request.** The maintainer reviews and merges.
- Commits use Conventional Commits: `feat:`, `fix:`, `docs:`, `test:`,
  `refactor:`, `chore:`. The message carries the reasoning — a chat window
  does not survive, a commit message does.

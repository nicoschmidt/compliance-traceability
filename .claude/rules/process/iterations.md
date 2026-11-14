<!-- Managed by ai-dev-process. Do not edit in a project: change it upstream, or record a deviation in CLAUDE.md. -->

# Iterations

An iteration is a unit of work with one goal. The **done criterion** — what
"the goal is reached" means in this project, such as "playable at the table" —
and the **iteration box** are process parameters in `CLAUDE.md`.

## An iteration is a milestone

- Each iteration is a GitHub milestone titled `NNN <short goal>`, with its
  goal as one sentence in the milestone's description. Its scope is the issues
  in that milestone. In a project of several repositories, every repository
  with issues in the iteration has a milestone of the same title.
- The goal names something the project's users can do afterwards that they
  could not do before.
- Iterations are cut small: one goal, a few issues. The **current iteration**
  is the open milestone with the lowest number. Later iterations may be
  planned as open milestones too; their goals change when an earlier one
  teaches something.
- A larger aim, such as an MVP — the first state after which the users would
  choose to use the result — is not an iteration. It is a named state in
  `docs/vision.md` of the home repository, reached by several iterations.
- Nobody keeps status by hand. An issue's state, its pull request and its
  milestone show where the work is, to every session that can read the
  repository.

## Scope

- **When the box is scope** (the default): the iteration ends when its goal
  meets the done criterion, not when a date arrives.
- **Scope may be added at any time**: into the current milestone, or as a new
  milestone that comes before it, when the maintainer wants something now.
  Before it is built, it is an issue in that milestone. Nothing is built that
  no issue in a milestone shows.
- **When the goal is met, the iteration ends**, even with issues still open.
  They move to the next milestone or back to refinement, and the milestone is
  closed. Small iterations and this move replace a cut order planned ahead.
- **When the box is time**: the milestone has a due date. The iteration ends
  on it, and what is open moves on in the same way.
- **An upgrade of ai-dev-process** happens between iterations, so it is the
  first issue of the next iteration's milestone. It needs no iteration of its
  own; what it teaches goes into that iteration's retro.

## Every iteration ends with a retro

The retro is a file in `docs/iterations/` of the home repository,
`NNN-<short-goal>.md` from `docs/iterations/TEMPLATE.md`, written when the
milestone closes: what shipped against the goal, what moved on, and the
process learnings. Its input is not memory:

- the open and closed issues labelled `process` since the iteration started,
  in every repository of the project
- the issues of the milestone, and the pull requests merged for them, with
  what their reviews had to correct: the review comments, and the commits
  with their authors, where a correction is a commit of its own
  (`workflow.md`, corrections in review)
- the issues that moved on, and why

Each process learning is marked:

- `[project]` — true for this project only. It becomes a change to
  `CLAUDE.md` (a parameter, a hard rule, or a deviation), through an issue.
- `[generic]` — would be true for another project too. It goes to the process
  repository named in `CLAUDE.md`: the `process` issue is transferred there, or
  a new one is drafted. It is not patched into the files managed by
  ai-dev-process here.

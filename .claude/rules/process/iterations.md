<!-- Managed by ai-dev-process. Do not edit in a project: change it upstream, or record a deviation in CLAUDE.md. -->

# Iterations

An iteration is a unit of work with one goal. The **done criterion** — what
"the goal is reached" means in this project, such as "playable at the table" —
and the **iteration box** are process parameters in `CLAUDE.md`.

- The goal is one sentence, and it names something the project's users can do
  afterwards that they could not do before.
- **When the box is scope** (the default): the iteration ends when its goal
  meets the done criterion, not when a date arrives. Scope must then be cut
  rather than stretched: if the goal turns out too large, the goal shrinks and
  the remainder becomes issues. An iteration that keeps growing is the failure
  mode this guards against, since nothing else stops it.
- **When the box is time**: the iteration ends on its date, and what is not
  done returns to refinement.
- An iteration has a file in `docs/iterations/` of the home repository, from
  `docs/iterations/TEMPLATE.md`, written before it starts with goal and out of
  scope filled in. Its scope may hold issues of every repository of the
  project. Status is not kept there; it is on the board.
- A milestone such as the MVP is not a unit of work. It is the first iteration
  after which the users would choose to use the result, and it is reached by
  iterations like any other.

## Every iteration ends with a retro

The retro note is the iteration file's **Result** and **Process learnings**
sections. Its input is not memory:

- the open and closed issues labelled `process` since the iteration started,
  in every repository of the project
- the pull requests merged in it, and what their reviews had to correct
- the issues that were cut, and why

Each process learning is marked:

- `[project]` — true for this project only. It becomes a change to
  `CLAUDE.md` (a parameter, a hard rule, or a deviation), through an issue.
- `[generic]` — would be true for another project too. It goes to the process
  repository named in `CLAUDE.md`: the `process` issue is transferred there, or
  a new one is drafted. It is not patched into the files managed by
  ai-dev-process here.

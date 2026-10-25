<!-- Managed by ai-dev-process. Do not edit in a project: change it upstream, or record a deviation in CLAUDE.md. -->

# Environments and division of labour

Two kinds of session work in this repository, with different capabilities.

| | Chat / Cowork | Claude Code | Maintainer |
| --- | --- | --- | --- |
| Read the repository | yes | yes | yes |
| Commit on a local branch | yes | yes | yes |
| Push, open issues and pull requests | **no — no credentials** | technically yes; hands over instead | yes |
| Merge | never | never | only the maintainer |

- **Chat / Cowork** — product scope, architecture, "what and why". Output is
  an ADR, a spec under `docs/`, refined issues, drafted pull request bodies.
  It has no Git credentials. That missing credential is the review gate, not
  an inconvenience to work around.
- **Claude Code** — implementation planning (plan mode) and execution against
  existing code, "how exactly, here". Output is a branch, commits and a pull
  request body.
- Rule of thumb: if answering the question requires reading the codebase, it
  belongs in Claude Code.
- Work prepared in a chat session is handed over as a local branch. A local
  commit is not delivered until the maintainer pushes it.

## Where the process lives

- `.claude/rules/process/` — these rules, managed by ai-dev-process at the
  version and in the role in `.ai-dev-process.lock`. Changed upstream, never
  here.
- `.ai-dev-process.conf` — the board, the home repository and the member
  repositories. Project-owned, the same in every repository of the project.
- `CLAUDE.md` — what this project is, its hard rules, its process parameters
  and deviations. In a member repository: the home repository's, imported,
  plus what holds for this repository only.
- The `ai-dev-process` plugin — the procedures: capturing ideas, refinement,
  handover, ADRs, iteration planning and retro. Its skills follow these rules;
  where a skill and a rule disagree, the rule wins and the skill has a defect.

## Language

The repository language and the conversation language are process parameters
in `CLAUDE.md`. Repository prose refers to "the maintainer", never to a
personal name.

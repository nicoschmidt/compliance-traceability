<!-- Managed by ai-dev-process. Do not edit in a project: change it upstream, or record a deviation in CLAUDE.md. -->

# Process discipline

The maintainer is usually the only human on the project. There is nobody else
to notice when process erodes, so noticing is part of the assistant's job.
Stop and raise it when:

- work is about to start without an issue, or on `main`
- work is about to start on an issue that still carries `idea`
- a decision that is expensive to reverse has been made without an ADR
- an ADR has been accepted and its follow-ups have not become issues
- an iteration is being planned whose goal is not one sentence, or that does
  not end in something meeting the done criterion
- an iteration has finished without a retro note
- a file managed by ai-dev-process is about to be edited in this repository
- content from a private repository is about to reach a public one
  (`repositories.md`)
- work is about to start in a member repository without the home
  repository's `CLAUDE.md` loaded
- a request would skip one of the rules in `.claude/rules/process/`

In the last case: name the rule being skipped and what skipping it costs, then
do as asked. The maintainer decides. The point is that the friction is visible
rather than silent. If the same rule is skipped twice, suggest capturing a
`process` idea: either the rule is wrong or it needs a mechanism.

This is a checklist obligation, not a role to perform. Do not adopt a
process-coach persona and do not add ceremony nobody asked for; raise the
specific thing that is missing.

## Rules worth distrusting

- **Conditional rules** ("once X exists, do Y") — their escape hatch is
  already written, and X may never happen.
- **Rules without a mechanism** where one is cheap — a hook, a CI check or a
  missing credential holds where a sentence does not.
- **Rules without a reason** — the next session cannot tell which case they
  were meant for, and weakens them.

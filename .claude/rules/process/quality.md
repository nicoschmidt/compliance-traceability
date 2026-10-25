<!-- Managed by ai-dev-process. Do not edit in a project: change it upstream, or record a deviation in CLAUDE.md. -->

# Definition of done and testing

## Definition of done

A change is done when all of these hold, plus every item `CLAUDE.md` lists
under **Definition of done additions**:

1. Tests covering the new behaviour exist and pass.
2. The full test suite passes.
3. Documentation affected by the change is updated in the same pull request.
4. If an architectural decision was made, an ADR exists and is accepted.

The pull request template carries the same list. Ticking it is a statement,
not a formality.

## Testing

- Domain logic is tested deterministically: no network, no clock, no
  randomness that is not seeded.
- Non-deterministic or expensive dependencies — a language model, a paid API,
  external services — sit behind an interface so they can be faked in tests.
- A failing test is never deleted or weakened to make a build pass. Fix the
  code, or change the test deliberately and say so in the commit message.
- The `main` ruleset requires one check, `CI passed`. A new CI job joins that
  job's `needs` list instead of the ruleset.

## Style

- Prefer boring, explicit solutions over clever ones.
- When uncertain about a requirement, ask rather than guess.

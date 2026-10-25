<!-- Managed by ai-dev-process. Do not edit in a project: change it upstream, or record a deviation in CLAUDE.md. -->

# Decision records

Every decision that is expensive to reverse is recorded as an ADR in
`docs/adr/` of the home repository (`repositories.md`) **before** the code
implementing it is written — in whichever repository that code lives. That includes
technology choices, interface and data-format decisions, deployment shape, and
anything that crosses a component boundary. Naming a variable does not need
one; choosing a persistence format does.

- Format: MADR, from `docs/adr/0000-template.md`. Numbered sequentially, never
  renumbered. Statuses: `proposed`, `accepted`, `rejected`,
  `superseded by ADR-XXXX`.
- An accepted ADR is immutable **in substance**: its decision, reasoning and
  consequences are never rewritten. To change a decision, write a new ADR and
  set the old one to `superseded by ADR-XXXX`. Typography, broken links and the
  redaction of personal data may be corrected in place.
- Accepting an ADR updates, in the same commit, the index in
  `docs/adr/README.md` and the derived `docs/architecture.md`. Where the
  decision shapes a member repository, that repository's
  `docs/architecture.md` is updated by its own pull request, in its own words.
- An accepted ADR's follow-ups become issues before the ADR's pull request is
  merged.
- An ADR written after the fact is worth much less: the options not taken are
  already forgotten. If a decision is noticed without one, stop, write it, then
  continue.

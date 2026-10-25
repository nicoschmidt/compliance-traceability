# Working agreements for AI assistants

This repository is a **member** of the compliance-traceability project. What
holds for the whole project — what it is, its hard rules, its process
parameters — is in the home repository's `CLAUDE.md`, imported here from the
checkout beside this one:

@../compliance-traceability-project/CLAUDE.md

Claude Code asks once to allow that import, because it lies outside this
repository. If the home repository is not checked out beside this one, stop
and say so: without it, the project's hard rules are missing from the session.

The way of working is [ai-dev-process](https://github.com/nicoschmidt/ai-dev-process),
at the version in `.ai-dev-process.lock`, in `.claude/rules/process/`. The
board and the other repositories are named in `.ai-dev-process.conf`.

## What this repository is

The public part of the project, under the MIT licence: the code (`ctm/`,
the scripts, the web viewer in `backend/` and `frontend/`), the schemas, the
methodology specification (`docs/`), the master list of common requirements
(`catalogue/`) and the public packs of EU law (`packs/`). It works on its own
with the public packs, and loads the private packs from the checkout beside
it when `ctm.local.json`, `--pack` or `CTM_PACKS` names them. `README.md`
describes the store, the tools and the workflow.

## Hard rules for this repository

- **Everything committed here is published.** The project's hard rule on
  licensed and confidential content applies with full force: not in files,
  commit messages, branch names, issues, pull request bodies or review
  comments. A public issue may refer to a private one by its number only.
- **`ctm.local.json` and `data/` are never committed.** Both are git-ignored:
  the first points at the private packs, the second holds generated
  workbooks, which are as confidential as the packs they were built with.
- **Decisions are ADRs in the home repository**, not new rows in § 10 of the
  specification, which only maps the former D numbers. Catalogue decisions
  stay in `catalogue/decisions.json`.

## Definition of done additions

- `python check_catalogue.py catalogue --fmt` is clean, if the catalogue
  changed.
- `schemas/` is regenerated (`python -m ctm.schemas`), if the model changed.
- The private repository's tests pass, if packs could be affected.

## Process deviations

None.

## Commands

```bash
# once per clone
git config core.hooksPath .githooks
pip install -e ".[dev,web]"
cp ctm.local.json.example ctm.local.json      # loads the private packs from the checkout beside

# tests, as CI runs them (CI has no private packs)
pytest
cd frontend && npm ci && npm test && cd ..
python check_catalogue.py catalogue
bash scripts/process/check-kit.sh
```

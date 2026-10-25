# Architecture

What holds in this repository: its parts, their boundaries, and the
contracts it shares with the other repositories of the project. The method
itself — information model, processes, catalogue structure, the rules for
what may be stored where — is in
[the specification](Compliance_Traceability_Methodology_Spec.md), §§ 4–8.
The decisions behind this are ADRs in the project's home repository; their
numbers are given for those who can follow them.

## Parts

- **The store.** The catalogue is a set of JSON files, the single source of
  truth, defined by one data model (`ctm/model.py`); the JSON Schemas in
  `schemas/` are generated from it (ADR-0010).
- **The master list and the packs.** `catalogue/` holds every common
  requirement. Each source document is a pack in the same format, public or
  private; the public packs of EU law are in `packs/` (ADR-0039). Coverage
  links carry the conditions and guidance that apply only because of their
  source (ADR-0040).
- **The tools.** `check_catalogue.py` checks a release, `make_catalogue.py`
  generates the read-only catalogue workbook, `build_project.py` creates and
  rebuilds project workbooks. All of them load the master list, the public
  packs and any packs named by `--pack`, `CTM_PACKS` or `ctm.local.json`.
- **The web viewer.** `backend/` (FastAPI) and `frontend/` (React, Vite)
  browse the same store and compute applicability with the same code as the
  workbooks (`ctm/project.py`).

## Boundaries

- References point from a pack to the master list only, never back.
- Licensed text never reaches this repository. A workbook built with
  private packs loaded is as confidential as those packs, and is written to
  the git-ignored `data/`.
- Without the private packs, the master list still lists every requirement,
  but not which source it gives compliance against.

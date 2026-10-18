# Compliance Traceability Toolkit

Implements spec v0.3.8, §§ 8.1 and 8.3. Requires Python 3.9+, `openpyxl` and `pydantic` 2 (`pip install -e .[dev]`).
The end-to-end test needs LibreOffice to recalculate the formulas.

The catalogue is stored as JSON, which is the single source of truth. The data model in `ctm/model.py` defines
every file. The catalogue workbook is generated from the JSON and is read-only. Project workbooks are where assessors,
clients and reviewers work.

**Master list and packs (spec § 8.3).** `catalogue/` is the public **master list**: every common requirement (CR),
the catalogue-wide decisions and the list of known packs. Each source document is a **pack** with the same format,
public or private: its raw text, our annotations, its source requirements (SRs) and their coverage links to the master
list. The public packs (Machinery Regulation, AI Act, MR-AIDA) are in `packs/` and loaded by default. Licensed
standards are private packs kept elsewhere, e.g. in a private repository, and loaded on request. Without a pack, its
CRs are still listed, but nothing says which source they give compliance against.

## Catalogue store

```
catalogue/                        master list (public)
  catalogue.json                  baseline ID, known packs (public ones with their default path)
  common_requirements.json        all CRs
  decisions.json                  catalogue-wide decision log (one ID sequence across master list and packs)
packs/<PACK>/                     one pack per source document; the same layout in a private repository
  pack.json                       pack ID, sources, amending acts, required packs
  sources/<SD>/raw.json           source text in its native structure (verbatim law; licensed text only in private packs)
  sources/<SD>/derived.json       SD record, our judgement per provision (role, scope, short label), SRs with their links
  sources/<ACT>/raw.json          amending act of the pack: replace / insert / delete operations applied to the pack's
                                  raw text at load time (MR: MR-COR, OMN-MR; AIA: OMN)
  decisions.json                  optional: decisions specific to this source
projects/<P>.json                 project seeds (PRJ, BASIS, TAGS, OBJECTS, EV) for build_project.py --init
ctm.local.json                    local only (git-ignored): extra packs to load, see ctm.local.json.example
schemas/*.schema.json             JSON Schemas generated from ctm/model.py (each file links its schema via "$schema")
```

Data conventions:

- **IDs:** an SP ID is `<SD>:<ref>`, where `ref` is the raw provision's native reference.
- **Enumerations** store register keys from `ctm/vocab.py` (e.g. `COVERS`, `ATOMIC`). Labels appear only in the workbooks.
- **Applicability rules and project tags** use the rule vocabulary (`AI.learning = dynamic`).
- **Licensed sources** may keep verbatim text in `raw.json` (internal store); workbook exports omit it unless
  `make_catalogue.py --internal` is used (spec § 7).
- **CR hierarchy vs refinement:** `parent_cr` builds the assessed hierarchy (selection, roll-up); `refines` records
  non-hierarchical refinements typed FULL/PARTLY. Full refinements carry a `set` (usually the refining source); a
  complete set substitutes the refined leaf CR in projects that select it (D0033, D0045).
- **Coverage links** are nested in their SR and identified by (SR, CR); `L<nnnn>` IDs are generated at export, in
  catalogue order. A link may carry a `condition` (applicability rule) and `guidance` that apply only because of that
  source: per source, the links on the nearest linked CR (leaf to root) decide; a CR applies if its own rule holds and
  the condition of at least one source of the project basis holds (D0044).
- **Adding a source:** create `packs/<SD>/pack.json` and `sources/<SD>/raw.json` + `derived.json`, link its SRs to
  CRs of the master list (add new CRs there), and list the pack in `known_packs` of `catalogue/catalogue.json`.

## Loading packs

Every tool loads the master list, its public packs and the extra packs given by, in this order: `--pack DIR`
(repeatable; a pack or a directory of packs), the environment variable `CTM_PACKS` (paths separated by `:` on
macOS/Linux, `;` on Windows), or `ctm.local.json` in the repository root. `--public-only` ignores the extra packs,
`--no-packs` loads the master list alone. CRs that only a known but unloaded pack reaches are counted as `UNREACHED`
by the check; orphans are warned only when all known packs are loaded.

```bash
cp ctm.local.json.example ctm.local.json      # {"packs": ["../compliance-traceability-private/packs"]}
python check_catalogue.py catalogue           # master list + public packs + configured packs
python check_catalogue.py catalogue --public-only
```

## Files

| Path | Purpose |
|---|---|
| `ctm/model.py` | Data model (pydantic) of every JSON file |
| `ctm/vocab.py` | Controlled vocabularies (register lists) |
| `ctm/store.py` | Load / validate / consolidate / save the store; export as workbook tables |
| `ctm/checks.py` | Catalogue release check |
| `ctm/schemas.py` | `python -m ctm.schemas` regenerates `schemas/` after a model change |
| `ctm/schema.py` | Workbook layout (sheets, columns, widths, actors) |
| `ctm/register.py` | Writes / reads the REGISTER sheet and its defined names |
| `ctm/rules.py` | Applicability rule parser / evaluator |
| `ctm/rollup.py` | Python reference implementation of the roll-up rules (used by the test) |
| `check_catalogue.py` | Release check of a JSON catalogue (`--fmt` rewrites files in canonical form first) |
| `make_catalogue.py` | Generate the catalogue workbook from a JSON catalogue |
| `build_project.py` | Create project input sheets (`--init [--seed]`) / build check items and views |
| `tools/backbone_metrics.py` | Checkpoint metrics of a catalogue |
| `tests/test_model.py` | Model, store, schema and checker tests (pytest) |
| `tests/test_phase1.py` | End-to-end test of the workbooks (sample fixture in `tests/fixtures/`) |
| `tests/fixtures/sample/` | Sample master list (`catalogue/`) with public packs (`packs/`); `extra_packs/DEMO` is a synthetic private pack |

## Typical workflow

```bash
# catalogue: edit the JSON files, then
python check_catalogue.py catalogue --fmt                                   # canonical format (master list + packs) + release check
python make_catalogue.py catalogue data/Catalogue_CAT-2026.1-draft.xlsx     # generated, read-only workbook
                                                                           # (--internal: include licensed text, internal use only)
                                                                           # a workbook built with packs is as confidential as the packs

# project
python build_project.py data/Catalogue_CAT-2026.1-draft.xlsx data/P26901.xlsx --init --seed ../compliance-traceability-private/projects/P26901.json
python build_project.py data/Catalogue_CAT-2026.1-draft.xlsx data/P26901.xlsx   # generates CI + views; re-run after any input change
```

Rebuilding keeps every entry in the CI sheet (matched by CI ID `<object>/<CR>`). It also keeps manual
applicability overrides, and moves check items that no longer exist to `CI_ORPHANED`. A `.bak` copy is written first.

## Tests

```bash
pytest                                              # tests/test_model.py: public catalogue + sample fixtures
python tests/test_phase1.py OUTDIR path/to/recalc.py
```

`recalc.py` is any script that recalculates an .xlsx with LibreOffice and prints a JSON status.

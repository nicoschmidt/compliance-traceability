# Checkpoint — Phase 2, step 3: ISO/IEC TR 5469

**Date:** 10 Oct 2026 · **Catalogue:** `CAT-2026.1-draft` (JSON store) · **Pilot project:** P26901 · **Spec:** v0.3.6 · **Decisions:** D0034–D0039

*Internal: raw.json of this source contains licensed text.*

## 1 Source onboarded

| | TR 5469:2024 |
|---|---|
| Provisions listed | 888. Clauses 1–11, Annexes A–D, 25 tables row by row, figure captions. Images and bibliography entries are not listed. |
| Atomised | 303 provisions (285 atomic, 5 lead-in, 18 measure tables) |
| Informative / structural | 585 (introduction, clause 5, definitions, notes, examples, literature discussion, Annex B examples, Annex D mapping, table rows) |
| Source requirements | 117, all *Derived* (rule A8: author, rationale, clause anchor). Our wording; the verbatim text is only in `raw.json`. |
| Coverage links | 180 (86 *Covers*, 90 *Covers partly*, 4 *Context*) |
| Out of catalogue scope | 0 |

**Source file.** The markdown export has OCR artefacts. The parser corrects the ones that affect structure:
- Annex C is headed "Annex E".
- "8. 7" is read as 8.7.
- Table A.5 has a two-line caption.
- The second classification axis of 6.2 is displaced.
- Sentences split at page breaks are rejoined.

Remaining artefacts (e.g. "Gee" for gcc in Table 3, a truncated NOTE in 9.3.4) are left as exported. If text is quoted internally, use the PDF.

## 2 Granularity: from the draft checklist to the catalogue

The draft checklist (63 items) was used as input, not copied (D0035).

- **Split.** Coarse items were split into separately verifiable SRs:
  - 8.3 → explainability evaluation, architecture partitioning, input recording;
  - 9.3.2-2 → hazardous scenarios, quantitative targets;
  - 9.4.2-3 → the four toolchain attributes + tool criticality;
  - 10.2.1 → one SR per architecture option.
- **Kept.** Detailed items stay one-to-one, e.g. 9.3.3 A1–D4 and 11.5.2.
- **Gaps closed.** Clauses the draft did not cover now have SRs: 6.2 classification, Table 1 learning modes, 9.2.5 update planning, 9.3.6 test oracles, 11.1, 11.3 and Annexes A and C.
- **Traceability.** Every SR notes the draft item it comes from (`notes`). The mapping is in Annex 1 below.
- **Examples.** The draft's PASS criteria and guidance went into the new CRs' acceptance criteria and guidance. The examples were rewritten for person detection at a stationary machine (the draft used a mobile robot).

## 3 Overlap with the existing catalogue

| | Links | CRs |
|---|---|---|
| Onto existing CRs | **111 of 180 (62 %)** | 59 reused: 27 from the legal backbone, 32 from TS 22440-1 |
| Onto new TR CRs | 69 | 43 new (38 assessable, 5 group parents) |

The reuse ratio is 10 % for TS 22440-1 and 62 % for TR 5469. The TR mostly discusses measures that the TS and the law already require, so the derived SRs land on those CRs:
- monitors and back-up → ROB.004, ROB.008–011;
- drift → ODD.002, PERF.001.4;
- robustness tests → VV.003.7;
- statistical demonstration → PERF.004.3;
- data management → DATA.004;
- attacks → SEC.006.

TR 5469 reaches 35 of the 184 legal CRs: 27 directly and 8 more through refinements.

**New CRs (TR-specific methods)**

| Domain | New | Content |
|---|---|---|
| GEN | 8 | Technology-element inventory; per-element classification and treatment on **TE objects** (GEN.006.1/.2, Annex A); three-stage principle: properties, methods, acceptance argument (GEN.007.1–3) |
| VV | 14 | Coverage metrics (VV.007); system-level testing: strategy, scenario catalogue, execution, physical tests (VV.008.1–4); virtual testing toolchain qualification (VV.009.1–5, rule `dev.virtual_testing = yes`); fault injection and timing simulation (VV.010); feedback of findings and incidents (VV.011); test oracles (VV.012) |
| DATA | 4 | HARA-driven data design: criteria a–c of 9.3.3 with the low/middle/high levels of Annex C (DATA.008.1–3) |
| MODEL | 5 | Explainability evaluation per recipient; reward hacking and safe exploration (rule `AI.rl`); robust learning (10.3.2 + C.5); validity of explanations (9.6, 10.3.4) |
| RM | 4 | AI-relevant hazardous scenarios in ODD terms; technology maturity; fault model per element (11.5.2); PFMEA of offline training (11.5.3) |
| ROB | 3 | Random hardware faults of the AI platform (8.6); fault injection into the model (9.4.4); safety logic kept outside the ML model |
| ODD, HO, LOG | 4 | ODD bounded for data and test design; environment complexity; level of automation and supervision; input recording for incident analysis |

**Typed refinements (D0036)**
- *Full* (substitution in TR projects):
  - CR.ODD.001 ← ODD.003;
  - CR.DATA.001.1.6 ← DATA.008.2 + DATA.008.3;
  - CR.DATA.001.1.7 ← DATA.008.2.
  - Residual legal aspects were added to the refiners' acceptance criteria.
- *Partly*: 49 relations, including to TS CRs (RM.017.1, DATA.003.4, VV.004, MODEL.004 …).
- *Full* is used only where the refined CR has no full set yet. The model supports one set of full refinements per CR. Adding a TR refiner to a CR that TS 22440-1 already refines fully would switch off the TS substitution in projects without the TR.

## 4 Pilot project P26901

- **Basis:** MR + AIA (UC1a) + TS 22440-1 (UC2) + **TR 5469 (UC2-G)**.
- **Tags:**
  - new `AI.rl = no`;
  - `dev.virtual_testing` deliberately not set (assessor to confirm, Q2).
- **New objects:** three TE objects under AIF-01:
  - trained detector (expected Class II);
  - inference software stack (Class I);
  - inference hardware (Class I).
- **Check items:** 257 → **302** (275 applicable, 27 not applicable by rule).
  - +48 TR check items;
  - −3 substituted (ODD.001, DATA.001.1.6, DATA.001.1.7).
  - Substituted CRs in total: 9 → 12.

| Level | Applicable | Not applicable by rule | of which new (TR) |
|---|---|---|---|
| AIF | 78 | 5 | 23 (2 N/A: reward hacking, safe exploration) |
| PRD | 99 | 15 | 1 |
| SF | 50 | — | 12 (2 safety functions × 6) |
| ORG | 31 | 1 | — |
| DEV | 11 | 6 | 6 (5 toolchain items "assessor to confirm") |
| TE | 6 | — | 6 (3 elements × 2) |

**Success criterion 4.** The view `V_CL_TR5469` regenerates the TR checklist in clause order with the familiar columns (Clause, Requirement, PASS criteria, Guidance, Evidence, Compliance statement, Assessor remarks, Verdict, Reviewer remarks).
- It has 236 rows, because each row is one SR × check item.
- These rows point to **115 distinct check items** (100 CRs).
- 67 of the 115 are shared with MR/AIA/TS and are assessed once.
- The repetition of shared check items is the case for the **combined checklist view** (open Phase 3 task, D0039).

## 5 Checks

- Catalogue checker: 0 errors, 0 warnings.
- pytest: 35 passed, with the updated snapshot counts (code change request § 2).
- `tests/test_phase1.py`: ALL PASS.
- LibreOffice recalculation:
  - Catalogue workbook: 10,821 formulas.
  - Project workbook: 73,808 formulas.
  - 0 errors in both.
- Excel roll-up = Python reference for all 4,384 statuses.
- Licensed text: no verbatim TR text in either workbook (0 of 598 probes).

## 6 Open questions for the project owner

1. **Annex C requirement levels (D0037).**
   - Working assumption: SIL 1/2/3 (PL b–c / d / e) → low / middle / high.
   - This gives *middle* for the pilot.
   - Confirm, or name another mapping (e.g. AI-SC).
2. **`dev.virtual_testing`.** Does the pilot use simulation or digital-twin results in the safety argument? If no, the five VV.009 check items become N/A.
3. **TE objects.** Three element groups as TE objects (6 check items). Is that workable, or should GEN.006 be assessed on AIF-01 as one classification matrix?
4. **Rule `TS.SWTC != I`** on the ML-specific TR CRs (DATA.008, MODEL.008/009, ROB.014, RM.022, VV.012). Agree?
5. **Alternative refinement sets.** Should a CR be substitutable by *either* the TS set *or* the TR set? This would be a model change (OR of AND-sets). Proposed: later, after the pilot review.
6. **Still open from P2-2:** D17 (corrigendum), D22 (AI-SC 3), D23 (`dev.ai_tools`), D24 (granularity), D25 ("should" provisions).

## 7 Next step

Step 4: prEN 18228 (ENQ). It tests Annex ZA correspondences and the two-hop presumption (§ 5.3). After that, the Phase 3 pilot review, including the combined checklist view.

---

## Annex 1 — Draft checklist item → SR → CR

New CRs are marked *. SR numbers are `SR.TR5469.nnnn`.

| Draft item | Topic | SRs | CRs |
|---|---|---|---|
| 7.1 | Technology element identification | 6 | GEN.005* |
| 7.2 | Element classification | 1, 2, 3, 7 | GEN.002, GEN.006.1*, GEN.006.2* |
| 7.3 (#4–6) | Properties, methods, acceptance criteria | 8, 9, 10 | GEN.007.1*, .2*, .3* |
| 8.1 | Property and risk-factor analysis | 11 | RM.003, GEN.007.1* |
| 8.2 | Automation level | 13, 14 | HO.015*, HO.002, ROB.009 |
| 8.3 | Transparency and explainability | 15, 17, 81 | MODEL.005*, HO.005, LOG.009*, LOG.002, ROB.015*, ROB.007 |
| 8.4.1 | ODD complexity | 18 | ODD.004*, ODD.001 |
| 8.4.2.1 / 8.4.2.2 | Data drift / concept drift | 20 / 23 | ODD.002, RM.003, PERF.001.4 |
| 8.4.3.1 / 8.4.3.2 | Reward hacking / safe exploration | 25 / 26 | MODEL.006*, MODEL.007* |
| 8.5.1 / 8.5.3 | Security / adversarial resilience | 27 / 29 | SEC.005, SEC.006 |
| 8.6 / 8.7 | Hardware / maturity | 32 / 33 | ROB.013* / RM.020* |
| 9.3.2-1 | ODD definition | 37, 38 | ODD.003* (fully refines ODD.001) |
| 9.3.2-2 | HARA with AI hazardous scenarios | 39, 40 | RM.019*, DATA.008.1*, PERF.001.2, FS.001 |
| 9.3.2-3 | Coverage metrics | 41 | VV.007* |
| 9.3.3-A1 | Hazard → data attributes | 43 | DATA.008.1* |
| 9.3.3-B1…B4 | Test data per risk, bias, gap closure | 44, 45, 46 | DATA.008.2*, DATA.001.1.6, DATA.001.1.7, DATA.006 |
| 9.3.3-C1…C4 | Diversity, process bias, volume, shift factors | 47, 48, 49 | DATA.008.3*, DATA.001.1.2, DATA.003.4 |
| 9.3.3-D1 | Split independence, overfitting | 50 | DATA.003.4, VV.006 (context) |
| 9.3.3-D2 / D3 / D4 | Robustness / stability tests / data integrity | 51 / 52 / 53 | MODEL.008* / VV.003.7, VV.003.10 / SEC.003, DATA.004, DATA.001.1.2 |
| 9.3.4 | AI metrics | 56, 57, 58 | PERF.001.1, PERF.001.4, PERF.004.3, PMM.002 |
| 9.3.5-1, 9.4.1-1 | Test planning, test strategy | 59, 64 | VV.008.1* |
| 9.3.5-2 | System-level scenario catalogue | 65, 66 | VV.008.2*, PERF.004.3 |
| 9.3.5-3, 9.4.3-2, 9.5 | Feedback of findings / incidents, monitoring | 75, 78 | VV.011*, RM.011, RM.017.3, PMM.002, LOG.003 |
| 9.4.1-2 | Testing of safety mechanisms | 62 | ROB.004, ROB.008, ROB.009 |
| 9.4.1-3 | Component-level HARA test results | 63 | PERF.001.3 (substituted by TS refiners), PERF.004.3 |
| 9.4.1-4 | System-level HARA test results | 67 | VV.008.3* |
| 9.4.2-1 / 9.4.2-3 | Virtual testing set-up / toolchain qualification | 70 / 71–74 | VV.009.1* / VV.009.2–5* |
| 9.4.2-2 | Fault injection, timing simulation | 69 | VV.010* |
| 9.4.3-1 | Physical testing | 68 | VV.008.4* |
| 9.4.4 | Hardware random-failure evaluation | 76 | ROB.014* |
| 9.6 | Explainability | 79 | MODEL.009* |
| 10.1 | Risk mitigation strategy | 81 | ROB.015*, ROB.007 |
| 10.2.1–10.2.5 | Architecture, monitors, supervisor, redundancy, statistics | 82–93 | ROB.006, ROB.008–011, PERF.002, PERF.004.3, DATA.003.4, VV.008.2* |
| 10.3.2 / 10.3.3 / 10.3.4 | Robust learning / compression / attention | 94 / 95 / 96 | MODEL.008* / MODEL.003 / MODEL.009* |
| 10.3.5 | Data and parameter protection | 97, 98, 99 | DATA.004, SEC.003, ROB.012, SEC.006 |
| 11.2 / 11.4 | Life cycle / documentation | 101–103 / 104 | QMS.003, CHG.008 / TD.017, TD.002.2.4 |
| 11.5.2 / 11.5.3 | Fault model / PFMEA | 105 / 106 | RM.021* / RM.022* |
| — (not in draft) | 33 SRs: Table 1 (learning modes), 8.1.2, 8.2-5, 8.3-5, 8.4.1-6, 8.4.2.1-4/-5, 8.4.2.2 (updates), 8.5.2, 8.5.3-5/-9, 9.1, 9.2.1, 9.2.5, 9.3.1.1, 9.3.2-4, 9.3.3-2, 9.3.3 d) XAI, 9.3.6 (2), 9.5-1, 11.1, Annex A (7), Annex C (4) | 4, 5, 12, 16, 19, 21, 22, 24, 28, 30, 31, 34–36, 42, 54, 55, 60, 61, 77, 80, 100, 107–117 | GEN.003, RM.012, CHG.002, CHG.008, VV.012*, GEN.006.2*, ROB.004, ROB.010, PERF.001.3, RM.017.1, DATA.008.1–3*, MODEL.008* … |

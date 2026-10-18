# Checkpoint — Phase 2, step 1: legal backbone (MR Annex III + AI Act)

**Date:** 9 Oct 2026 · **Catalogue:** `Catalogue_CAT-2026.1-draft.xlsx` · **Pilot project:** `Project_P26901_pilot.xlsx` · **Spec:** v0.3.1

## 1 Sources onboarded

| | MR Annex III | AI Act |
|---|---|---|
| Provisions listed (rule A10) | 723 | 170 |
| Atomised (in catalogue scope) | 100 | 114 |
| Out of catalogue scope | 438 = 270 physical/general (D1) + 168 in machine-type chapters 2, 4, 5, 6 (deferred to Phase 5) | — |
| Not applicable (catalogue) | — | 20 (biometric, financial institutions, Section A integration, authority tasks) |
| Structural (umbrella, lead-in, definition, scope, informative) | 185 | 36 |
| Source requirements | 102 (2 provisions split) | 114 |

The anticipated delegated act (`MR-AIDA`) is registered but not populated. AIA provisions serve as proxy (decision D0003; please confirm).

## 2 Common requirements and links

- **160 common requirements:** 150 assessable leaves and 10 parents (risk reduction, performance, data, oversight, supervisory function, technical documentation, QMS).
- **By object level (leaves):** PRD 91 · AIF 28 · ORG 18 · SF 13.
- **By domain:** TD 24 · RM 17 · INFO 17 · HO 15 · FS 14 · QMS 13 · DATA 11 · LOG 8 · SEC 7 · CHG 5 · ROB 5 · PERF 4 · INC 3 · PMM 3 · VV 2 · GEN 1 · ODD 1.
- **258 links:** 187 *Covers*, 65 *Covers partly*, 6 *Supports – process*.
- **Overlap between the regulations:** 29 requirements are reached from both MR and AIA, 46 from MR only, 82 from AIA only.
- **Reuse ratio:** 36 of 126 AIA links (29 %) landed on requirements already created from MR. This confirms Step 1: the AIA mainly *adds* content (data, technical documentation, QMS, IFU items, logging purposes).

## 3 Checks

- Catalogue checker: 0 errors, 0 warnings (no gaps, no orphans, all rules valid).
- Pilot project: 163 check items (149 Applicable, 14 N/A by rule – self-evolving, mobile, supervisory function, fundamental rights).
- Recalculated in LibreOffice: 0 formula errors (22,474 formulas).
- Excel roll-up identical to the Python reference implementation for all 1,269 statuses.
- For comparison: the Step-1 matrix had 710 rows.

## 4 What the deduplication did

- **Protective-function provisions:** nine MR provisions that a camera-based protective function realises (1.2.2 ¶5, 1.2.3 ¶4, 1.3.7 ¶1, 1.3.8.2 ¶1(c), 1.4.3 ¶1(a)(b), 3.2.1 ¶1, 3.3 ¶5, 3.3.3 ¶6(ii), 3.5.1 ¶3) and AIA 15(1) now lead to:
  - **one** protective-function requirement per safety function (CR.FS.009); and
  - **one** performance requirement per AI function (CR.PERF.001, 4 children).
  In Step 1, Art 15(4) alone had 39 links.
- **Duplicate MR wording:** MR 1.2.1 ¶4 and 1.2.6 ¶2 share their wording. They merged into four requirements (FS.002–005), each tested for both trigger conditions.
- **Overlapping principles:** MR general principle 1, 1.1.2 and AIA Art 9 converged on one risk-management group (RM.001–RM.015, incl. RM.006 with three priority steps).

## 5 Open questions for the project owner

1. **Reporting of out-of-boundary provisions.** 95 of 161 MR top-level sections roll up as *Not assessed*, because they contain physical provisions outside the AI-component boundary. Is this the reporting you want? The alternative is a separate status, e.g. *Outside assessment boundary*, that does not rank with *Not assessed* in the conformity statement.
2. **Deferred machine-type chapters.** Chapters 2, 4, 5 and 6 are deferred to Phase 5, including five AI-relevant provisions (2.3(c), 2.4.3, 4.1.2.6, 4.2.2, 5.4). Please confirm.
3. **`MR-AIDA` as proxy** (D0003): confirm or reject.
4. **Granularity of Annex IV.** It is atomised into 23 content checks (TD.002.x). Keep them, or merge them into fewer document-section checks?
5. **Assessment-object levels.** PRD dominates (91 items, mostly IFU, TD and oversight). The TE and DEV levels are not used yet; they will appear with TS 22440-1 (technology elements, toolchain) in step 2.

## 6 Next step

Step 2: ISO/IEC CD TS 22440-1. It tests the classification-dependent requirements (usage level × technology class, integrity) and the rated measure tables (rule A7), and we expect mainly child requirements under PERF, ROB, DATA, MODEL and VV.

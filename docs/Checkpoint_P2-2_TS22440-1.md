# Checkpoint — Phase 2, step 2: ISO/IEC CD TS 22440-1

**Date:** 10 Oct 2026 · **Catalogue:** `CAT-2026.1-draft` (JSON store) · **Pilot project:** P26901 · **Spec:** v0.3.4 · **Decisions:** D0025–D0032

*Internal: this report contains information about a committee draft.*

## 1 Source onboarded

| | TS 22440-1 (CD) |
|---|---|
| Provisions listed | 812. Clauses 1–9, Annexes A–D, 9 tables row by row. Figures and bibliography entries are not listed. |
| Atomised | 288 provisions (atomic, lead-in, measure table) |
| Informative / structural | 524 (foreword, introduction, objectives, notes, examples, Annex D, table headers) |
| Source requirements | 198 (191 *shall*, 7 *should*). All are paraphrased; the verbatim text is only in `raw.json` (D0025). |
| Coverage links | 205 (192 *Covers*, 13 *Covers partly*) |
| Out of catalogue scope | 0 (the whole TS is AI functional safety) |

**Measure tables (rule A7):**
- Annex A: 15 mitigations. Each has one source requirement with the AUL-A1 and AUL-A2 ratings and the low/high effectiveness definitions.
- Annex B: 13 test-method groups.
- Annex C: 3 qualification methods.

## 2 Common requirements

**78 new common requirements** (72 assessable, 6 group parents).

| Domain | New | Content |
|---|---|---|
| VV | 17 | Annex B test-method groups VV.003.1–13 (rules by AI-SC), test completeness, validation of the installed function, independent assessment |
| DATA | 10 | Dataset archive; data properties, metrics and requirements (DATA.003 group); data management system; augmentation; synthetic test data; label errors |
| QMS | 8 | Functional-safety life cycle applied (DEV); functional-safety management for AI (QMS.004 group: competence, procedures, configuration management incl. datasets, roles) |
| PERF | 7 | Runtime uncertainty quantification; uncertainty quantification after training; statistical demonstration of the residual failure rate (PERF.004 group) |
| ROB | 7 | System-level failure analysis; architecture; non-AI back-up; AI monitor; redundancy; monitor specification; input filtering |
| TOOL (new domain) | 7 | AI-based development tools (Annex C), rule `dev.ai_tools = yes` |
| RM | 6 | AI use justified against alternatives; AI fault analysis (RM.017 group); mitigation selection per Annex A |
| MODEL | 4 | Model selection, training process, optimisation and compression, explainability |
| GEN | 3 | AUL/SWTC classification; permitted requirement set and learning mode; AUL-C |
| FS, TD, ODD, HO, CHG, INFO, PMM | 11 | Integrity target (SIL/AIP → AI-SC), AI-specific HW/SW requirements, life-cycle documentation, mitigation rationale in the TD, drift of ODD parameters, operator decisions on AI output, modification impact analysis, IFU on unintended behaviour, periodic audits |

**Reused requirements from the legal backbone:** 20. They are reached by 21 of the 205 links (10 %).
- Hazard and risk analysis: RM.001, RM.003, RM.004, RM.006, RM.011.
- Data governance: DATA.001.1.2 and DATA.001.1.5.
- Performance: PERF.001.3 and PERF.001.4.
- Robustness, oversight, security: ROB.004, HO.003, SEC.003, SEC.006.
- Technical documentation: TD.002.2.2, TD.002.2.4, TD.002.2.7.
- Other: FS.001, VV.001, INFO.004, PMM.002.

**Why the reuse ratio is low:**
- Deliberate: refinements from the TS are stand-alone requirements, not children of the legal ones (D0026). A project selects all children of a linked requirement, so TS detail placed under an AI Act requirement would appear in projects that do not use the TS.
- In substance, the TS mainly adds the "how": rated measures, the statistical demonstration and the life-cycle process.
- Where the TS measure and a legal requirement are the same, the legal requirement is reused, for example drift detection (PERF.001.4) and oversight (HO.003).

## 3 Pilot project P26901

- **Basis:** MR + AIA (UC1a) + TS 22440-1 (UC2).
- **Tags:**
  - `TS.AUL = A1` and `TS.SWTC = II` (already set).
  - `INT.AISC = 3` is **new**. It follows from PL d ≈ SIL 2 → AI-SC 3 (TS Table 3).
  - `dev.ai_tools = no` is **new**.
- **New object:** DEV-01 (data and training pipeline).
- **Check items:** 188 → **266** (241 applicable, 25 not applicable by rule).

| Level | Applicable | Not applicable by rule |
|---|---|---|
| AIF | 69 | 3 |
| PRD | 98 | 15 |
| SF | 38 | — |
| ORG | 31 | 1 |
| DEV | 5 | 6 (AI-based tools) |

**Effect of AI-SC 3:**
- All 15 Annex A mitigations apply. Most are *highly recommended* at high effectiveness, among them redundancy, monitors, a non-AI back-up and system-level analysis with fault insertion.
- 12 of the 13 Annex B test groups apply. Formal methods apply too, as *recommended* only.

## 4 Checks

- Catalogue checker: 0 errors, 0 warnings.
- pytest: 32 passed (with the updated snapshot counts).
- `tests/test_phase1.py`: ALL PASS.
- LibreOffice recalculation:
  - Catalogue workbook: 8,302 formulas.
  - Project workbook: 54,769 formulas.
  - 0 errors in both.
- Excel roll-up = Python reference for all 3,300 statuses. This includes SP hierarchies down to 6 levels.
- Licensed text: the catalogue and project workbooks contain no verbatim TS text (0 of 812 SPs).

## 5 Observations on the draft (comment candidates)

1. **"shall" in notes and examples.** Normative wording appears where it is not allowed: 8.2.2.1 Note 2, 6.5.2.5 Note 1 d), B.1 Note 1 (legend) and C.6.2.3 Example 2.
2. **8.3.3.3:** optimisation and compression "shall be used in accordance with Table A.1", but the table rates the measure R/HR. "shall be considered" would fit better.
3. **8.1 vs A.1:** 8.1 says all clause 8 requirements apply unless the tables exempt them. A.1 allows lower or no mitigation based on the AI fault risk. These two statements are in tension.
4. **Table cross-references:**
   - Tables A.1/A.2 cite TS 22440-2 clauses 8.2–8.13.
   - Table B.1 cites 9.2.13–9.2.20, which do not exist in Part 1.
   - Table A.3 has no effectiveness definition for "uncertainty quantification to verify performance after training".
5. **Editorial errors:**
   - 8.3.2.2.2 has a duplicated "shall … shall be used".
   - 8.3.4.1 starts with a stray reference "IEC 62443-3-2:2020 [26]", and its note ends with "and".
   - 5.2.2.3 uses "needs to be used" instead of an ISO verbal form.
   - 6.4.2.11 mixes *shall* and *should* in one requirement.
   - 6.4.2.8 refers to Figure 3, but Figure 5 seems to be meant.
   - 6.4.2.20 says to use "diverse training hardware during verification", which is unclear.
6. **AUL-A2 oversight:** Table A.2 rates "system enabling oversight by user" as "–" for every AI-SC, while 8.4.2.3.6 requires oversight "when necessary".

## 6 Open questions for the project owner

1. **AI-SC 3 for the pilot.** Confirm PL d → SIL 2 → AI-SC 3. AI-SC 2 would lower the required effectiveness from *high* to *low* for most mitigations, and make 3 of them *recommended* instead of *highly recommended* (redundancy, input filtering, uncertainty after training).
2. **`dev.ai_tools = no`.** Does the pilot product use AI-assisted labelling or similar tools? If yes, the six TOOL check items apply.
3. **Granularity.**
   - 266 check items in total; the TS adds 78. Workable?
   - Alternatively, the 13 test-method groups (VV.003.x) could become one check item with a method matrix as evidence.
4. **"should" provisions.** The 7 recommendations are listed and linked to the requirement under which an assessor would look at them, worded as recommendations in the CR. Keep them, or drop them from the checklist?
5. **Code changes** (see the code change request):
   - SP depth 6.
   - Licensed-text export.
   - Domain TOOL and tag `dev.ai_tools`.
   - Optional: a non-hierarchical `refines` attribute for the CR relations of D0026.

## 7 Next step

Step 3: ISO/IEC TR 5469 + the client checklist (derived requirements, rule A8; the checklist is regenerated as view `V_CL_TR5469`).

---

## Addendum (10 Oct 2026): refinements and substitution (D0033, spec v0.3.5)

TS requirements now record which legal requirements they refine, typed **Full** or **Partly**.

- **Full:** the TS requirements together satisfy the legal requirement. In a project with the TS in its basis, the legal requirement has **no check items of its own**. Its status comes from the TS check items, and the legal provisions still roll up through it.
- **Partly:** the TS adds detail to part of the legal requirement. Both are assessed, and `V_CR` shows the relation so the same evidence can be used.

Where a full refinement needed an aspect only the law has, that aspect was added to the TS requirement's acceptance criterion. Examples: thresholds dated before testing (AIA Art 9(8)) and statistical properties regarding persons (AIA Art 10(3)).

**Result in the pilot:**
- Check items: 266 → **257** (9 legal requirements substituted).
- Applicable items: 241 → **232**.
- Excel roll-up = Python reference for 3,291 statuses; 0 formula errors.
- Example: AIA Art 15(1) in `V_CL_AIA` now lists the TS check items (PERF.004.x, VV.003.2/3/7/8, RM.018, ROB.006) in place of PERF.001.1–3 and ROB.003.

**Why the reduction is moderate:**
- The TS reaches 51 of the 184 legal requirements, by direct link or refinement. For 9 it says everything the law requires.
- For the other 36 it adds AI-specific depth to a broader legal requirement, which therefore still needs its own check. Examples:
  - Hazard identification: generic hazards plus AI faults.
  - QMS: AIA Art 17 is broader than functional-safety management.
  - Safety-function specification: function, response and timing besides the integrity target.
- The remaining legal requirements (logging, IFU, oversight, incidents, CE marking, conformity assessment, physical) are not addressed by the TS.

The bigger saving lies in **evidence**: partial refinements point to the same work products (HARA, data specification, test report). A combined checklist view could list partial refinements under their legal requirement as one review step; this is proposed for Phase 3.

| Legal CR (substituted) | Title | Full refinements (TS 22440-1) |
|---|---|---|
| DATA.001.1.3 | Preparation operations | DATA.003.3, DATA.004 |
| DATA.001.1.8 | Data gaps | DATA.003.1, DATA.005 |
| DATA.001.2 | Data relevant, representative, error-free, complete | DATA.003.1, DATA.003.4, DATA.007 |
| DATA.001.3 | Data reflect the setting of use | DATA.003.2 |
| PERF.001.1 | Performance metrics selected and justified | PERF.004.2 |
| PERF.001.2 | Acceptance thresholds prior-defined | PERF.004.1, PERF.004.2, PERF.004.3 |
| PERF.001.3 | Verified performance meets thresholds | PERF.004.3, VV.003.2, VV.003.3 |
| ROB.003 | Resilience to errors, faults and environment | RM.018, ROB.006, VV.003.7, VV.003.8 |
| VV.001 | Test strategy across development | VV.003, VV.004 |

| Legal CR (still assessed) | Title | Partial refinements |
|---|---|---|
| CHG.001 | Safety-function limits; hazardous modifications prevented | GEN.003 |
| DATA.001.1.1 | Design choices | DATA.003.2 |
| DATA.001.1.5 | Availability, quantity, suitability | DATA.003.4 |
| DATA.001.1.6 | Bias examination | DATA.003.1 |
| FS.001 | Safety functions specified | FS.016, FS.017 |
| HO.004 | Automation bias addressed | HO.014 |
| HO.005 | Interpretable outputs and information | HO.014, MODEL.004 |
| INFO.004 | IFU: characteristics, capabilities and limitations | INFO.022 |
| INFO.014 | IFU: residual risks and protective measures | INFO.022 |
| ODD.001 | Operational design domain specified | ODD.002 |
| PERF.001.4 | Performance consistent over the lifecycle | ODD.002, VV.003.8 |
| PMM.001 | Post-market monitoring system | PMM.005 |
| PMM.002 | Active performance data collection | PMM.005 |
| QMS.001 | Documented quality management system | QMS.004.1, QMS.004.5 |
| QMS.001.1 | QMS: Regulatory-compliance strategy incl. conformity assessment and modification management | CHG.008, QMS.004.3 |
| QMS.001.12 | QMS: Resource management incl. security of supply | QMS.004.2 |
| QMS.001.13 | QMS: Accountability framework | QMS.004.6 |
| QMS.001.2 | QMS: Design, design control and design verification | QMS.003 |
| QMS.001.3 | QMS: Development, quality control and quality assurance | QMS.003 |
| QMS.001.6 | QMS: Data management systems and procedures | DATA.004, QMS.004.4 |
| RM.003 | Hazards identified incl. AI-specific hazard sources | RM.017.1 |
| RM.004 | Risks estimated | RM.017.2 |
| RM.005 | Risks evaluated; residual risk acceptable | RM.018 |
| RM.006 | Risk reduction in the order of priority | RM.016 |
| RM.006.2 | Protective and mitigation measures | RM.018 |
| RM.011 | Post-market data fed back into risk management | RM.017.3 |
| ROB.001 | Single faults do not lead to hazardous situations | ROB.006, ROB.007, ROB.010 |
| ROB.002 | Protective-device failure leads to safe state | ROB.008 |
| ROB.004 | AI logic errors detected and controlled | PERF.002, ROB.008, ROB.009, ROB.011 |
| SEC.003 | Critical software and data identified and protected | DATA.004 |
| SEC.004 | Installed safety software identifiable | QMS.004.4 |
| TD.001 | Technical documentation established and current | TD.017 |
| TD.002.2.1 | TD: Development methods incl. third-party pre-trained components | MODEL.002 |
| TD.002.2.2 | TD: Design specifications, logic, key choices, trade-offs | MODEL.001 |
| TD.002.5 | TD: Risk management system description | TD.018 |
| TD.003 | Documentation retained for at least 10 years | DATA.002 |

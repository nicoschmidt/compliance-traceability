# Checkpoint — Phase 2, step 1b: Machinery Regulation completed

**Date:** 9 Oct 2026 · **Catalogue:** `CAT-2026.1-draft` (JSON store) · **Pilot project:** P26901 · **Spec:** v0.3.3 · **Decisions:** D0014–D0023

## 1 What was added

| Part of the MR | Treatment |
|---|---|
| Arts 1, 2, 3, 9, 17, 52, 54 | Listed. Scope, definitions, transitional and application dates (*Scope* / *Definition*) |
| Arts 6, 7 | ¶1 *Scope*; Commission and Member State procedures *Not applicable (catalogue)* |
| Art 8 | ¶1 *Scope*; ¶2 partly completed machinery (PCM, out of catalogue scope); new ¶3–4 from Omnibus Art 3(1) |
| **Art 10** (manufacturer obligations) | Fully atomised: 21 SRs |
| Art 11, 22, Annex IV Part B, Annex V Part B | PCM: listed, out of catalogue scope (D0015) |
| Art 18 | ¶2 atomised (a person carrying out a substantial modification is assessed as the manufacturer, D0023) |
| Art 19 | Supply-chain identification, 10 years |
| Art 20 | Presumption ¶1, 6, 9 and new ¶10 (Omnibus Art 3(2), legal bridge to AIA standards) *Scope*; Commission procedure *N/A* |
| **Arts 21, 23, 24, 25** | DoC, CE marking, conformity assessment routes: atomised |
| Annexes I, II | Listed, *Scope* (classification lists) |
| **Annex IV Part A** | Atomised per point (granularity as agreed) |
| **Annex V Part A** | DoC particulars, one SR each |
| **Annexes VI–X** (modules A, B, C, H, G) | Manufacturer obligations atomised; notified-body tasks *N/A* |
| Not ingested (D0014) | Arts 4, 5, 12–16, 26–51, 53 (other actors and authorities); Annex XI (PCM assembly instructions); Annex XII (correlation table) |

Two new amending acts are applied at load time:
- **`OMN-MR`** (Omnibus Art 3 → MR):
  - Art 8 ¶3–4: delegated acts must reflect AIA Ch. III Sec. 2 and Arts 17, 19, 72, 73. These are exactly the AIA provisions in the catalogue, so the `MR-AIDA` proxy (D0003) now has a legal basis.
  - Art 20(10): presumption via AIA harmonised standards.
- **`MR-COR`** (corrigendum OJ L 169, 4.7.2023): the MR applies from **20 January 2027**, not 14 January 2027 as printed in the OJ of 29.6.2023. Other dates shift by six days.

## 2 Metrics

| | Step 1 | Step 1b | Change |
|---|---|---|---|
| MR provisions listed | 723 | 1,244 | +521 |
| MR atomised (in scope) | 100 | 250 | +150 |
| MR out of catalogue scope | 438 | 490 | +52 (PCM) |
| MR structural / no requirement | 185 | 504 | +319 |
| MR source requirements | 102 | 221 | +119 |
| Common requirements | 160 | 187 | +27 |
| Coverage links | 258 | 384 | +126 (115 *Covers*, 10 *Covers partly*, 1 *Supports – process*) |
| Pilot check items | 163 | 188 | +25 (174 applicable, 14 N/A by rule) |

**Reuse ratio:** 24 of the 125 new counting links (19 %) point to requirements that already existed. They land mainly on the technical documentation and QMS requirements: Annex IV ↔ AIA Annex IV, and module H quality system ↔ AIA Art 17. The ratio is low because conformity assessment, the DoC and CE marking were new to the catalogue. For a safety component under AIA Section B, these obligations come only from the MR. The AIA's own Arts 16, 43, 47–49 are not in the catalogue (Omnibus Art 3(1) lists only Ch. III Sec. 2 and Arts 17, 19, 72, 73).

**Requirements reached from both regulations:** 45 (previously 29).

## 3 New common requirements (27)

- **CONF** (new domain), 11 requirements:
  - CONF.001: conformity assessment carried out.
    - .1 Annex I classification.
    - .2 permitted route, **OR** of: .2.1 module A, .2.2 B+C, .2.3 H, .2.4 G, with rules by `AI.cat`.
  - CONF.002: EU declaration of conformity.
  - CONF.003: CE marking.
  - CONF.004: production / series conformity.
  - CONF.005: DoC supplied / accessible ≥ 10 years.
- **TD:**
  - TD.003: retention ≥ 10 years.
  - TD.011: protective measures per EHSR.
  - TD.012: drawings and schemes.
  - TD.013: verification reports.
  - TD.014: production means.
  - TD.015: DoCs of incorporated products.
  - TD.016: source code / programming logic on request.
- **INFO:**
  - INFO.018: product identification.
  - INFO.019: manufacturer contact on the product.
  - INFO.020: digital IFU.
  - INFO.021: paper safety information for non-professional users.
- **Other:**
  - PMM.004: sample testing / complaint register.
  - INC.004: corrective action, withdrawal, recall.
  - INC.005: cooperation on authority request.
  - QMS.002: supply-chain identification.
  - CHG.007: changes notified to the notified body.

**Refined:**
- TD.002.7: now neutral wording covering standards, common specifications and other solutions for MR and AIA.
- INFO.001: IFU must identify the product model.

## 4 Findings relevant to the pilot (B15 camera protective device)

1. **Route.** Annex I Part B item 15 allows module A only if the product follows category-specific harmonised standards that cover *all* relevant EHSRs (Art 25(3) ¶2–3). No cited standard covers ML-based person detection. In practice this means **notified-body involvement (B+C, H or G)** unless that changes. CONF.001.2.1 states this as acceptance criterion and guidance.
2. **Model updates.** Under module B or H, every modification that may affect conformity must be notified to the notified body, and the certificate reviewed (Annex VII 7.2–7.4, Annex IX 3.5). Retraining, new weights, changed thresholds or a changed ODD are candidates. CHG.007 makes this a separate check, linked in guidance to pre-determined changes (CHG.002).
3. **Source code.** Annex IV(m) and Art 10(3) require that the source code / programming logic of the safety-related software is available on request. For a CNN, TD.016 guidance includes the model architecture and trained parameters.
4. **Scenario check.** In the pilot workbook:
   - Inputs: route B+C = Pass, other routes N/A, classification = Pass, CHG.007 = Fail.
   - Results: CONF.001 = Pass (OR group), MR Art 25 = Pass, Annex VII = Fail.
   - Excel roll-up = Python reference for all 2,134 statuses.

## 5 Checks

- Catalogue checker: 0 errors, 0 warnings.
- pytest: 32 passed (after updating the snapshot counts, see code change request).
- `tests/test_phase1.py`: ALL PASS.
- LibreOffice recalculation: catalogue 5,835 formulas, project 32,939 formulas, 0 errors.

## 6 Open questions for the project owner

1. **PCM provisions in the report.** Annex IV and Annex V roll up as *Not assessed* in the pilot because their Part B (PCM) is out of catalogue scope. For a product that is not PCM, these provisions are really "not applicable".
   - Proposal: add a scoping tag `prod.type` (machinery / related product / PCM; code change). Atomise PCM content in Phase 5 with rules, so it becomes *N/A by rule* instead of *Not assessed*.
   - Until then, the current reporting stays.
2. **Corrigendum dates.** EUR-Lex is blocked from here. The dates come from a secondary summary of the corrigendum. Please confirm against OJ L 169, 4.7.2023 (or upload it).
3. **Unlisted articles.** Is the A10 clarification acceptable? Articles addressed only to other actors stay unlisted, with the scope logged (D0014).
4. **Optional tags to replace manual N/A** (code change): `conf.module` (A / B+C / H / G), `ifu.digital`, `use.non_professional`. Without them, assessors set the routes not chosen, and INFO.020 / INFO.021, to *N/A – feature absent* by hand.
> **Update (D0024):** questions 1 and 4 are partly resolved. The tags `prod.type`, `conf.module`, `ifu.digital` and `use.non_professional` now exist. Rules are set on CONF.001.2.1–4, CHG.007, INFO.020 and INFO.021. In the pilot, three routes are now N/A by rule, and so is INFO.021 (seed: `conf.module = B+C`, `use.non_professional = no`; `ifu.digital` left undetermined). Partly-completed-machinery content still needs atomising before `prod.type` takes effect.

5. **`MR-AIDA` proxy (D0003):** still awaiting confirmation; Omnibus Art 3(1) now supports it.

## 7 Next step

Step 2: ISO/IEC CD TS 22440-1 (unchanged plan, § 12).

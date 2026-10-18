"""Workbook layout: sheets and columns of the catalogue and project workbooks (spec v0.3, sections 4 and 8).

The data model itself is ctm/model.py; this module only defines how it is laid out in Excel. Column keys and `lst`
bindings must match the model fields and their Vocab lists (asserted by tests/test_model.py).
`lst` binds a column to a REGISTER list (drop-down + validation).
`actor` drives header colour in project sheets: system / author / client / assessor / reviewer.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Col:
    key: str
    label: str
    width: int = 14
    lst: Optional[str] = None      # REGISTER list name
    actor: str = 'author'
    required: bool = False
    note: str = ''


# ---------------------------------------------------------------- catalogue sheets
CATALOGUE = {
    'SD': [
        Col('sd_id', 'SD ID', 12, required=True, note='Short code, e.g. MR, AIA, TS22440-1'),
        Col('title', 'Title', 50, required=True),
        Col('edition', 'Edition / version', 16),
        Col('doc_type', 'Document type', 18, 'SDTYPE', required=True),
        Col('lifecycle_status', 'Lifecycle status', 16, 'SDSTATUS', required=True),
        Col('status_date', 'Status date', 12),
        Col('normative_strength', 'Normative strength', 22, 'STRENGTH', required=True),
        Col('legal_link', 'Legal link (hEN: act / request)', 26),
        Col('licence_class', 'Licence class', 20, 'LICENCE', required=True),
        Col('notes', 'Notes', 40),
    ],
    'SP': [
        Col('sp_id', 'SP ID', 26, required=True, note='<SD>:<native ref>'),
        Col('sd_id', 'SD ID', 10, required=True),
        Col('native_ref', 'Native reference', 18, required=True),
        Col('seq', 'Seq (native order)', 9, required=True),
        Col('parent_sp', 'Parent SP', 24),
        Col('role', 'Role', 16, 'SPROLE', required=True),
        Col('heading', 'Heading', 30),
        Col('label', 'Short label', 30),
        Col('text', 'Text (verbatim law only; empty for licensed sources)', 60),
        Col('condition_text', 'Condition in text', 28),
        Col('in_catalogue_scope', 'In catalogue scope?', 11, 'YN', required=True,
            note='no = listed, not atomised (ingestion-scope rule)'),
        Col('scope_note', 'Scope note', 28),
    ],
    'SR': [
        Col('sr_id', 'SR ID', 18, required=True, note='SR.<SD>.<nnnn>'),
        Col('sp_refs', 'SP refs (; separated)', 30, required=True),
        Col('statement', 'Statement (law verbatim / standard paraphrase)', 60, required=True),
        Col('obligation', 'Obligation', 11, 'OBLIG', required=True),
        Col('origin', 'Origin', 10, 'ORIGIN', required=True),
        Col('author', 'Author', 12),
        Col('date', 'Date', 11),
        Col('rationale', 'Rationale (mandatory if Derived)', 34),
        Col('parameters', 'Parameters (e.g. AI-SC=2)', 18),
        Col('measure_rating', 'Measure rating (HR/R/–)', 14),
        Col('coverage_complete', 'Coverage complete?', 11, 'YN', required=True),
        Col('notes', 'Notes', 30),
    ],
    'CR': [
        Col('cr_id', 'CR ID', 16, required=True, note='CR.<DOMAIN>.<nnn>[.<n>]'),
        Col('domain', 'Domain', 9, 'DOMAIN', required=True),
        Col('title', 'Title', 34, required=True),
        Col('statement', 'Statement (neutral wording)', 60, required=True),
        Col('parent_cr', 'Parent CR', 16),
        Col('decomposition', 'Decomposition', 9, 'DECOMP'),
        Col('refines', 'Refines (non-hierarchical; ; separated)', 20),
        Col('refines_full', 'Refines fully = substitutes (; separated, [set])', 22),
        Col('cr_type', 'CR type', 16, 'CRTYPE', required=True),
        Col('object_level', 'Object level', 9, 'OBJLEVEL', required=True),
        Col('verification_method', 'Verification method', 18, 'VMETHOD'),
        Col('acceptance_criterion', 'Acceptance criterion (PASS criteria)', 44),
        Col('criterion_source', 'Criterion source', 18),
        Col('assessor_guidance', 'Assessor guidance', 44),
        Col('expected_evidence', 'Expected evidence (work products)', 28),
        Col('lifecycle_phase', 'Lifecycle phase', 16, 'PHASE'),
        Col('applicability_rule', 'Applicability rule', 34, note='TRUE or expression over scoping tags'),
        Col('tension_flag', 'Tension?', 9, 'YN'),
        Col('status', 'Status', 10, 'CRSTATUS', required=True),
        Col('author', 'Author', 12),
        Col('notes', 'Notes', 30),
    ],
    'LINK_SR_CR': [
        Col('link_id', 'Link ID', 10, required=True),
        Col('sr_id', 'SR ID', 18, required=True),
        Col('cr_id', 'CR ID', 16, required=True),
        Col('link_type', 'Link type', 17, 'LINKTYPE', required=True),
        Col('condition', 'Condition (source-specific applicability)', 30, note='empty = always; rule vocabulary'),
        Col('guidance', 'Guidance (source-specific)', 36),
        Col('rationale', 'Rationale', 50),
        Col('author', 'Author', 12),
        Col('date', 'Date', 11),
    ],
    'CORR': [
        Col('corr_id', 'Corr ID', 10, required=True),
        Col('basis', 'Basis', 22, 'CORRBASIS', required=True),
        Col('claimant_sd', 'Claimant SD', 12, required=True),
        Col('from_sp', 'From SP (claimant clause)', 24, required=True),
        Col('to_sp', 'To SP (legal provision)', 24, required=True),
        Col('declared_coverage', 'Declared coverage', 16, 'ZACOV', required=True),
        Col('remarks', 'Remarks', 40),
    ],
    'DECISIONS': [
        Col('dec_id', 'Decision ID', 11, required=True),
        Col('date', 'Date', 11, required=True),
        Col('author', 'Author', 12, required=True),
        Col('type', 'Type', 18, 'DECTYPE', required=True),
        Col('affected_ids', 'Affected IDs', 30, required=True),
        Col('rationale', 'Rationale', 60, required=True),
        Col('source_refs', 'Source refs', 30),
    ],
}

# formula check columns appended to catalogue sheets (author aids; recalculated in Excel)
CATALOGUE_CHECKS = {
    'SP': ['sd_ok', 'parent_ok'],
    'SR': ['n_counting_links'],
    'CR': ['parent_ok', 'n_in_links'],
    'LINK_SR_CR': ['counts', 'sr_ok', 'cr_ok'],
    'CORR': ['from_ok', 'to_ok'],
}

# ---------------------------------------------------------------- project input sheets
PROJECT_INPUT = {
    'BASIS': [
        Col('sd_id', 'SD ID', 12, actor='assessor', required=True),
        Col('edition', 'Edition', 16, actor='assessor'),
        Col('use_case', 'Use case', 10, 'USECASE', actor='assessor'),
        Col('note', 'Note', 40, actor='assessor'),
    ],
    'TAGS': [
        Col('tag', 'Tag', 26, actor='system', required=True),
        Col('group', 'Group', 22, actor='system'),
        Col('value', 'Value', 14, actor='assessor'),
        Col('note', 'Description / note', 60, actor='system'),
    ],
    'OBJECTS': [
        Col('object_id', 'Object ID', 18, actor='assessor', required=True, note='<P>-<LEVEL>-<nn>'),
        Col('level', 'Level', 8, 'OBJLEVEL', actor='assessor', required=True),
        Col('name', 'Name', 30, actor='assessor'),
        Col('description', 'Description', 50, actor='assessor'),
        Col('parent_object', 'Parent object', 18, actor='assessor'),
    ],
    'EV': [
        Col('ev_id', 'Evidence ID', 16, actor='client', required=True, note='<P>-EV-<nnn> (fixed width)'),
        Col('title', 'Title', 40, actor='client'),
        Col('client_doc_id', 'Client document ID', 18, actor='client'),
        Col('version', 'Version', 9, actor='client'),
        Col('date', 'Date', 11, actor='client'),
        Col('type', 'Work-product type', 22, 'EVTYPE', actor='client'),
        Col('owner', 'Owner', 14, actor='client'),
        Col('confidentiality', 'Confidentiality', 14, actor='client'),
        Col('location', 'Location / link', 30, actor='client'),
    ],
}

PRJ_FIELD_KEYS = [('project_id', 'Project ID'), ('client', 'Client'), ('product', 'Product'),
                  ('description', 'Description'), ('use_cases', 'Use case(s)'), ('catalogue_baseline', 'Catalogue baseline'),
                  ('boundary_statement', 'Boundary statement'),
                  ('agreed_exclusions', 'Agreed exclusions (with agreement reference)'), ('assessor', 'Assessor'),
                  ('reviewer', 'Reviewer'), ('start_date', 'Start date')]
PRJ_FIELDS = [lab for _, lab in PRJ_FIELD_KEYS]

# CI sheet: editable fields preserved across rebuilds
CI_EDITABLE = ['applicability', 'applicability_justification', 'evidence_refs', 'client_statement',
               'assessor_remarks', 'verdict', 'finding_severity', 'reviewer_remarks', 'reviewer_signoff']
CI_COLS = [
    Col('ci_id', 'CI ID', 30, actor='system'),
    Col('object_id', 'Object', 16, actor='system'),
    Col('level', 'Level', 7, actor='system'),
    Col('cr_id', 'CR ID', 16, actor='system'),
    Col('domain', 'Domain', 8, actor='system'),
    Col('title', 'Requirement (title)', 30, actor='system'),
    Col('statement', 'Requirement statement', 50, actor='system'),
    Col('acceptance_criterion', 'PASS criteria', 40, actor='system'),
    Col('assessor_guidance', 'Guidance', 40, actor='system'),
    Col('expected_evidence', 'Expected evidence', 24, actor='system'),
    Col('rule_applicability', 'Rule result (auto)', 14, actor='system'),
    Col('applicability', 'Applicability', 18, 'APPL', actor='assessor'),
    Col('applicability_justification', 'Applicability justification', 30, actor='assessor'),
    Col('evidence_refs', 'Evidence (IDs + section)', 26, actor='client'),
    Col('client_statement', 'Compliance statement', 36, actor='client'),
    Col('assessor_remarks', 'Assessor remarks', 36, actor='assessor'),
    Col('verdict', 'Verdict', 11, 'VERDICT', actor='assessor'),
    Col('finding_severity', 'Finding severity', 13, 'SEV', actor='assessor'),
    Col('reviewer_remarks', 'Reviewer remarks', 30, actor='reviewer'),
    Col('reviewer_signoff', 'Reviewer sign-off (name, date)', 18, actor='reviewer'),
    Col('status', 'Status (derived)', 16, actor='system'),
    Col('excl_idx', '_excl_idx', 6, actor='system'),
    Col('find_idx', '_find_idx', 6, actor='system'),
]

ACTOR_FILL = {'system': 'D9D9D9', 'author': 'D9D9D9', 'client': 'DDEBF7', 'assessor': 'FFF2CC', 'reviewer': 'E2EFDA'}
HEADER_FILL = '1F3864'

CR_MAX_DEPTH = 3   # levels below a root CR handled by roll-up columns
SP_MAX_DEPTH = 6   # levels below a root SP

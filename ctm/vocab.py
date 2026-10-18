"""Controlled vocabularies (spec § 6.3): the single definition of every enumeration.

Each list holds (key, label, colour, attribute, description) entries. Data files store **keys**; labels are display
text written into the REGISTER sheet of generated workbooks. Exception: applicability rules and project tag values use
the rule vocabulary (TAG labels and value labels), as defined in spec § 4.6.
"""
from typing import Annotated

from pydantic import AfterValidator, WithJsonSchema

# (key, label, colour, attribute, description)
DEFAULT = {
    'VERDICT': [
        ('PASS', 'Pass', 'C6EFCE', '', 'Requirement met (applicable items only)'),
        ('FAIL', 'Fail', 'FFC7CE', '', 'Requirement not met'),
        ('INFO', 'Info needed', 'FFEB9C', '', 'Evidence insufficient; returned to client'),
        ('PEND', 'Pending', 'EDEDED', '', 'Not yet assessed'),
    ],
    'APPL': [
        ('APPLICABLE', 'Applicable', 'FFFFFF', '', 'Item must be assessed'),
        ('NA_FEAT', 'N/A – feature absent', 'F2F2F2', '', 'Feature/system type not present (rule or assessor)'),
        ('NA_HAZ', 'N/A – hazard absent', 'F2F2F2', '', 'Hazard absent per risk assessment (reference required)'),
        ('INHERITED', 'Inherited', 'E2EFDA', '', 'Assessed elsewhere (ORG-level CI, host-machine DoC, certificate)'),
        ('NIS', 'Not in scope (agreed)', 'F4B084', '', 'Deliberately not assessed by agreement; disclosed in report'),
    ],
    'SEV': [
        ('MAJOR', 'Major', 'FF7C80', '', 'Nonconformity affecting safety/compliance'),
        ('MINOR', 'Minor', 'FFC000', '', 'Nonconformity of limited impact'),
        ('OBS', 'Observation', 'BDD7EE', '', 'Improvement potential; may be raised on Pass'),
    ],
    'ROLLUP': [
        ('PASS', 'Pass', 'C6EFCE', '', 'All counted items pass'),
        ('FAIL', 'Fail', 'FFC7CE', '', 'At least one counted item fails'),
        ('GAP', 'Gap', 'FF7C80', '', 'Catalogue gap: coverage incomplete or provision not atomised'),
        ('NOTASS', 'Not assessed', 'F4B084', '', 'At least one item not in scope (agreed)'),
        ('OOS', 'Out of catalogue scope', 'F8CBAD', '', 'Provision listed but not atomised (ingestion-scope rule)'),
        ('OPEN', 'Open', 'FFEB9C', '', 'At least one item pending / info needed'),
        ('NA', 'N/A', 'F2F2F2', '', 'Not applicable'),
        ('NOTINST', 'Not instantiated', 'EDEDED', '', 'No assessment object of the CR level in this project'),
        ('NOREQ', 'No requirement', 'FFFFFF', '', 'Definition / scope / informative provision'),
    ],
    'LINKTYPE': [
        ('COVERS', 'Covers', 'C6EFCE', 'yes', 'CR alone satisfies the SR'),
        ('PARTLY', 'Covers partly', 'FFEB9C', 'yes', 'CR satisfies part of the SR'),
        ('SUP_METHOD', 'Supports – method', 'DDEBF7', 'no', 'CR provides method / acceptance criterion'),
        ('SUP_PROCESS', 'Supports – process', 'DDEBF7', 'no', 'CR is a process producing evidence for the SR'),
        ('CONTEXT', 'Context', 'F2F2F2', 'no', 'Informative relationship'),
    ],
    'SPROLE': [
        ('UMBRELLA', 'Umbrella', '', 'children', 'Verdict rolled up from children'),
        ('ATOMIC', 'Atomic', '', 'own', 'Expressed by one or more SRs'),
        ('LEADIN', 'Lead-in', '', 'children', 'Chapeau without own content'),
        ('DEF', 'Definition', '', 'none', 'Glossary / term alignment'),
        ('SCOPE', 'Scope/Applicability', '', 'none', 'Applicability statement'),
        ('INFO', 'Informative', '', 'none', 'Note / example'),
        ('MTABLE', 'Measure table', '', 'own', 'Table of rated measures'),
        ('CATNA', 'Not applicable (catalogue)', '', 'none', 'Provision cannot apply to products in catalogue scope (e.g. biometric, financial institutions, authority tasks); decision logged'),
    ],
    'OBLIG': [('SHALL', 'Shall', '', '', ''), ('SHOULD', 'Should', '', '', ''), ('MAY', 'May', '', '', ''),
              ('DERIVED', 'Derived', '', '', 'Written by us from an informative source')],
    'ORIGIN': [('LITERAL', 'Literal', '', '', ''), ('DERIVED', 'Derived', '', '', 'Author + rationale mandatory')],
    'SDTYPE': [('REG', 'Regulation', '', '', ''), ('DA', 'Delegated/implementing act', '', '', ''),
               ('HEN', 'hEN', '', '', 'Harmonised European standard (candidate)'), ('EN', 'EN', '', '', ''),
               ('IS', 'ISO/IEC IS', '', '', ''), ('TS', 'TS', '', '', ''), ('TR', 'TR', '', '', ''),
               ('GUIDE', 'Guidance', '', '', ''), ('INHOUSE', 'In-house framework', '', '', '')],
    'SDSTATUS': [('ANTICIPATED', 'Anticipated', '', '', 'Not yet adopted (e.g. MR delegated act)'),
                 ('DRAFT', 'Draft', '', '', 'CD/DIS/ENQ/FprEN'), ('PUBLISHED', 'Published', '', '', ''),
                 ('CITED', 'Cited in OJ', '', '', 'Confers presumption of conformity'),
                 ('WITHDRAWN', 'Withdrawn', '', '', '')],
    'STRENGTH': [('BINDING', 'Binding law', '', '', ''), ('PRESUMPTION', 'Presumption-conferring', '', '', ''),
                 ('NORMATIVE', 'Voluntary normative', '', '', ''), ('INFORMATIVE', 'Informative', '', '', '')],
    'LICENCE': [('PUBLIC', 'Public domain', '', '', ''), ('LICENSED', 'Licensed (internal only)', '', '', ''),
                ('CLIENT', 'Client-confidential', '', '', '')],
    'CRTYPE': [('DESIGN', 'Design property', '', '', ''), ('TEST', 'Verification/test', '', '', ''),
               ('DOC', 'Document content', '', '', ''), ('PROCESS', 'Process', '', '', ''),
               ('ORG', 'Organisational', '', '', ''), ('IFU', 'Information for use', '', '', '')],
    'OBJLEVEL': [('ORG', 'ORG', '', '', 'Organisation (manufacturer / provider)'),
                 ('PRD', 'PRD', '', '', 'Product: machine or safety component placed on the market'),
                 ('SF', 'SF', '', '', 'Safety function'), ('AIF', 'AIF', '', '', 'AI function / AI component'),
                 ('TE', 'TE', '', '', 'Technology element (TR 5469 7.1 / TS 22440 5.2)'),
                 ('DEV', 'DEV', '', '', 'Development process / toolchain')],
    'VMETHOD': [('DOCREV', 'Document review', '', '', ''), ('ANALYSIS', 'Analysis/calculation', '', '', ''),
                ('WITNESS', 'Test witnessing', '', '', ''), ('TESTREC', 'Test-record review', '', '', ''),
                ('INSPECT', 'Inspection', '', '', ''), ('INTERVIEW', 'Interview', '', '', ''),
                ('AUDIT', 'Process audit', '', '', '')],
    'CRSTATUS': [('DRAFT', 'Draft', '', '', ''), ('RELEASED', 'Released', '', '', 'Included in a catalogue baseline'),
                 ('DEPRECATED', 'Deprecated', '', '', 'Replacement named in notes; excluded from projects')],
    'DECOMP': [('AND', 'AND', '', '', 'All applicable children required'),
               ('OR', 'OR', '', '', 'At least one child; choice justified')],
    'REFCOV': [('FULL', 'Full', '', '', 'Together with the other full refinements of the same CR, satisfies it completely; '
                                        'in a project that selects them, the refined CR is substituted (no own CIs)'),
               ('PARTLY', 'Partly', '', '', 'Adds detail to part of the refined CR; the refined CR is still assessed')],
    'DOMAIN': [(k, k, '', '', d) for k, d in [
        ('GEN', 'Scope, classification, boundary'), ('RM', 'Risk management'),
        ('ODD', 'Operational design domain & specification'), ('DATA', 'Data & data governance'),
        ('MODEL', 'Model selection, creation, optimisation, explainability'),
        ('PERF', 'Performance, accuracy, uncertainty'), ('ROB', 'Robustness, fault control, architecture'),
        ('SEC', 'Cybersecurity & protection against corruption'),
        ('FS', 'Safety-function behaviour & integrity'), ('HO', 'Human oversight & HMI'),
        ('LOG', 'Logging & traceability'), ('CHG', 'Learning, change & modification management'),
        ('VV', 'Verification, validation & testing'), ('INFO', 'Information for use, marking, warnings'),
        ('TD', 'Technical documentation'), ('QMS', 'Quality management'), ('PMM', 'Post-market monitoring'),
        ('INC', 'Incidents & corrective action'), ('CONF', 'Conformity assessment, declaration & marking'), ('TOOL', 'AI-based development tools'),
        ('PHYS', 'Physical hazards')]],
    'PHASE': [(k, l, '', '', '') for k, l in [
        ('CONCEPT', 'Concept & classification'), ('REQ', 'Requirements & ODD'), ('DATA', 'Data'),
        ('DEV', 'Design & development'), ('VV', 'Verification & validation'),
        ('DEPLOY', 'Deployment & operation'), ('POST', 'Post-market')]],
    'YN': [('YES', 'yes', '', '', ''), ('NO', 'no', '', '', '')],
    'YNT': [('YES', 'yes', '', '', ''), ('NO', 'no', '', '', ''), ('TBD', 'tbd', '', '', 'To be determined')],
    'ZACOV': [('COVERED', 'Covered', '', '', ''), ('PARTIAL', 'Partially covered', '', '', '')],
    'CORRBASIS': [('ZA', 'Annex ZA', '', '', 'Claim in a harmonised standard; needs OJ citation'),
                  ('LEGAL', 'Legal bridge', '', '', 'Claim made by law, e.g. MR Art 20(10)')],
    'DECTYPE': [(k, l, '', '', '') for k, l in [
        ('MERGE', 'Merge'), ('SPLIT', 'Split'), ('DERIVED', 'Derived SR'), ('LINK', 'Link type'),
        ('REFINE', 'Refinement'), ('CATNA', 'Catalogue N/A'), ('CONFLICT', 'Conflict resolution'),
        ('CRITERION', 'Acceptance criterion'), ('SCOPE', 'Ingestion scope'), ('OTHER', 'Other')]],
    'USECASE': [('UC1A', 'UC1a', '', '', 'Regulation, legal requirements'),
                ('UC1B', 'UC1b', '', '', 'Regulation via harmonised standards'),
                ('UC2', 'UC2', '', '', 'Specific standard'), ('UC2G', 'UC2-G', '', '', 'Guidance / TR')],
    'EVTYPE': [(k, l, '', '', '') for k, l in [
        ('ODD', 'ODD specification'), ('HARA', 'Risk assessment / HARA'),
        ('SRS', 'Safety requirements specification'), ('ARCH', 'Architecture description'),
        ('DMP', 'Data management plan'), ('DATASHEET', 'Data set documentation'),
        ('MODELDOC', 'Model documentation'), ('VVPLAN', 'V&V plan'), ('VVREP', 'V&V / test report'),
        ('FMEA', 'FMEA / FTA'), ('IFU', 'Instructions for use'), ('TD', 'Technical documentation'),
        ('QMS', 'QMS procedure'), ('PMM', 'PMM plan / records'), ('INC', 'Incident procedure / records'),
        ('CERT', 'Certificate / DoC'), ('OTHER', 'Other')]],
    'AICAT': [
        ('A5', 'A5', '', '', 'Safety component with self-evolving behaviour (MR Annex I Part A item 5)'),
        ('A6', 'A6', '', '', 'Machinery with embedded self-evolving safety system (Part A item 6)'),
        ('B15', 'B15', '', '', 'AI-based protective device detecting persons, not self-evolving (Part B 15)'),
        ('B17', 'B17', '', '', 'AI-based logic unit for safety functions, not self-evolving (Part B 17)'),
        ('SC', 'SC', '', '', 'Other AI safety component (Annex II, MR Art 3(3), AIA Art 6(1b))'),
        ('NSF', 'NSF', '', '', 'AI not a safety function (AIA Art 6(1a))'),
        ('NSF_SE', 'NSF-SE', '', '', 'AI not a safety function, self-evolving')],
    'LEARNING': [('STATIC', 'static', '', '', 'Offline learning only'), ('DYNAMIC', 'dynamic', '', '', 'Online / continual learning')],
    'USAGELVL': [(k, k, '', '', 'Usage level of the AI technology (TR 5469 6.2)') for k in ['A1', 'A2', 'B1', 'B2', 'C', 'D']],
    'TECHCLASS': [(k, k, '', '', 'AI technology class (TR 5469 6.2)') for k in ['I', 'II', 'III']],
    'PL': [(k.upper(), k, '', '', 'ISO 13849-1 performance level') for k in ['a', 'b', 'c', 'd', 'e']],
    'SIL': [('S1', '1', '', '', ''), ('S2', '2', '', '', ''), ('S3', '3', '', '', '')],
    'AISC': [('S1', '1', '', '', 'Required systematic capability of the AI part (scale of the applied AI standard)'), ('S2', '2', '', '', ''), ('S3', '3', '', '', '')],
    'PRODTYPE': [('MACH', 'machinery', '', '', 'Machinery (MR Art 3(1))'),
                 ('RELPROD', 'related-product', '', '', 'Related product (MR Art 2(1)(a)-(e)): interchangeable equipment, safety '
                                                        'component, lifting accessory, chains/ropes/webbing, removable '
                                                        'mechanical transmission device'),
                 ('PCM', 'PCM', '', '', 'Partly completed machinery (MR Art 3(10))')],
    'CONFMOD': [('A', 'A', '', '', 'Internal production control (MR Annex VI)'),
                ('B_C', 'B+C', '', '', 'EU type-examination + conformity to type based on internal production control '
                                       '(MR Annexes VII + VIII)'),
                ('H', 'H', '', '', 'Conformity based on full quality assurance (MR Annex IX)'),
                ('G', 'G', '', '', 'Conformity based on unit verification (MR Annex X)')],
    'ORGSIZE': [('SME', 'SME', '', '', ''), ('SMC', 'SMC', '', '', ''), ('LARGE', 'Large', '', '', '')],
    # scoping tags: key = name-safe id, label = tag as used in rules, attribute = value list, description = group | text
    'TAG': [
        ('AI_CAT', 'AI.cat', '', 'AICAT', 'AI system category | Combined MR classification / Step-2 category'),
        ('AI_LEARNING', 'AI.learning', '', 'LEARNING', 'AI system category | Static or dynamic (online) learning'),
        ('AI_RL', 'AI.rl', '', 'YN', 'AI system category | Reinforcement learning or other reward-based optimisation used (TR 5469 8.4.3)'),
        ('AIA_HR', 'AIA.high_risk_6_1', '', 'YNT', 'AIA classification | High-risk under AIA Art 6(1)'),
        ('AI_USAGE', 'AI.usage_level', '', 'USAGELVL', 'AI classification | Usage level A1, A2, B1, B2, C, D (TR 5469 6.2)'),
        ('AI_TECHCLASS', 'AI.tech_class', '', 'TECHCLASS', 'AI classification | AI technology class I, II, III (TR 5469 6.2)'),
        ('INT_PL', 'INT.PL', '', 'PL', 'Integrity level | Required performance level'),
        ('INT_SIL', 'INT.SIL', '', 'SIL', 'Integrity level | Required SIL'),
        ('INT_AISC', 'INT.AISC', '', 'AISC', 'Integrity level | Required systematic capability of the AI part (scale of the applied AI standard)'),
        ('SYS_CTRL', 'sys.control_system', '', 'YN', 'System type | Safety-related part of a control system / logic unit'),
        ('SYS_PROT', 'sys.protective_device', '', 'YN', 'System type | Person/obstacle detection, ESPE-type device'),
        ('SYS_GUARD', 'sys.guard_interlock', '', 'YN', 'System type | Guard / interlocking'),
        ('SYS_REMOTE', 'sys.remote_control', '', 'YN', 'System type | Remote control'),
        ('SYS_WIRELESS', 'sys.wireless_control', '', 'YN', 'System type | Wireless control'),
        ('SYS_SUPERV', 'sys.supervisory_function', '', 'YN', 'System type | Supervisory function (MR 3.2.4)'),
        ('SYS_HMI', 'sys.hmi', '', 'YN', 'System type | Operator information / interaction'),
        ('FEAT_MOBILE', 'feat.mobile', '', 'YN', 'Machine feature | Mobility (MR ch. 3)'),
        ('FEAT_AMM', 'feat.autonomous_mobile', '', 'YN', 'Machine feature | Autonomous mobile machinery'),
        ('FEAT_LIFT', 'feat.lifting', '', 'YN', 'Machine feature | Lifting operations (MR ch. 4)'),
        ('FEAT_LIFTP', 'feat.lifting_persons', '', 'YN', 'Machine feature | Lifting of persons (MR ch. 6)'),
        ('PROD_TYPE', 'prod.type', '', 'PRODTYPE', 'Product | Machinery, related product or partly completed machinery (PCM)'),
        ('CONF_MODULE', 'conf.module', '', 'CONFMOD', 'Conformity assessment | Module chosen under MR Art 25: A, B+C, H or G'),
        ('IFU_DIGITAL', 'ifu.digital', '', 'YN', 'Information for use | Instructions for use supplied in digital format (MR Art 10(7))'),
        ('USE_NONPRO', 'use.non_professional', '', 'YN', 'Information for use | Intended for, or foreseeably used by, non-professional users (MR Art 10(7))'),
        ('DEV_AI_TOOLS', 'dev.ai_tools', '', 'YN', 'Development | AI-based software tools used to develop the safety-related product (TS 22440-1 Annex C)'),
        ('DEV_VIRTUAL_TESTING', 'dev.virtual_testing', '', 'YN', 'Development | Virtual test results (simulation, digital twin, MIL/SIL/HIL) used in the safety argument (TR 5469 9.4.2)'),
        ('ORG_SIZE', 'org.size', '', 'ORGSIZE', 'Organisation | Size (SME/SMC proportionality)'),
        ('SCOPE_FR', 'scope.FR', '', 'YN', 'Scope option | Include fundamental-rights requirements (default no)'),
    ],
}

class VocabRef:
    """Marker in a field's metadata naming the register list the field is bound to."""
    def __init__(self, lst):
        self.lst = lst

    def __repr__(self):
        return f'VocabRef({self.lst!r})'


def keys(lst):
    return [e[0] for e in DEFAULT[lst]]


def labels(lst):
    return [e[1] for e in DEFAULT[lst]]


def label_of(lst, key):
    for e in DEFAULT[lst]:
        if e[0] == key:
            return e[1]
    raise KeyError((lst, key))


def key_of(lst, label):
    for e in DEFAULT[lst]:
        if e[1] == label:
            return e[0]
    raise KeyError((lst, label))


def attr_of(lst, key):
    for e in DEFAULT[lst]:
        if e[0] == key:
            return e[3]
    raise KeyError((lst, key))


def Vocab(lst):
    """str type restricted to the keys of register list `lst` (validated, and an enum in the JSON Schema)."""
    allowed = keys(lst)

    def check(v):
        if v not in allowed:
            raise ValueError(f'{v!r} is not a key of register list {lst} {allowed}')
        return v
    return Annotated[str, AfterValidator(check), WithJsonSchema({'type': 'string', 'enum': allowed,
                                                                 'description': f'Key of register list {lst}'}),
                     VocabRef(lst)]

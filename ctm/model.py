"""Data model of the catalogue store (spec § 4): the single definition of every JSON file.

Layout (spec § 8.3, see ctm/store.py):
  master list directory (catalogue/)
    catalogue.json                  CatalogueManifest – baseline ID, known packs
    common_requirements.json        CommonRequirementsFile – every CR (public master list)
    decisions.json                  DecisionsFile
  pack directory (packs/<PACK>/), one per source document; same format for public and private packs
    pack.json                       PackManifest
    sources/<SD>/raw.json           RawDocument      – legal / standard text in its native structure (what the text says)
    sources/<SD>/derived.json       SourceCatalogue  – SD record, per-provision judgements, source requirements + links
    sources/<ACT>/raw.json          AmendingAct      – amendments applied to a raw document of the pack at load time
    decisions.json                  DecisionsFile (optional)
A project seed (projects/<P>.json) is a ProjectSeed.

Conventions: enumerated fields hold register keys (ctm/vocab.py); empty optional text is ''; IDs follow spec § 6.1.
Applicability rules and project tags use the rule vocabulary (TAG labels / value labels, spec § 4.6).
"""
import datetime as dt
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from . import vocab
from .vocab import Vocab

Text = Annotated[str, StringConstraints(min_length=1)]   # required, non-empty


class Model(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)


class FileModel(Model):
    """Top level of a JSON file; "$schema" points to the generated JSON Schema (editor support only)."""
    schema_ref: Optional[str] = Field(None, alias='$schema')


# ------------------------------------------------------------------------------------------------ raw layer
ProvisionKind = Literal['section', 'article', 'annex', 'paragraph', 'subparagraph', 'point', 'subpoint', 'definition']


class RawProvision(Model):
    """One unit of the source's native structure. Text is verbatim; text of licensed sources is internal only and
    stripped from exports (spec § 7)."""
    ref: Text = Field(description='Native reference, unique in the document; SP ID = <SD>:<ref>')
    parent: Optional[str] = Field(None, description='ref of the parent provision')
    kind: Optional[ProvisionKind] = None
    heading: str = ''
    text: str = ''
    verbatim: bool = Field(True, description='false if the text is condensed or otherwise not the official wording')
    note: str = ''


class RawDocument(FileModel):
    doc_id: Text
    title: Text
    oj_ref: str = ''
    source_url: str = ''
    extracted: str = Field('', description='How and from what the text was extracted')
    provisions: list[RawProvision] = Field(description='In document order (defines SP sequence)')


class Amendment(Model):
    """replace: new text/heading for target_ref. delete: removes target_ref and its descendants.
    insert: adds `provisions` (a block in document order) after insert_after and its descendants."""
    op: Literal['replace', 'insert', 'delete']
    amending_ref: Text = Field(description='Provision of the amending act, e.g. "Art 1(9)(a) Reg. (EU) 2026/1744"')
    target_ref: Optional[str] = None
    text: Optional[str] = None
    heading: Optional[str] = None
    insert_after: Optional[str] = None
    provisions: list[RawProvision] = []
    note: str = ''

    @model_validator(mode='after')
    def _shape(self):
        if self.op in ('replace', 'delete') and not self.target_ref:
            raise ValueError(f'{self.op} needs target_ref')
        if self.op == 'replace' and self.text is None and self.heading is None:
            raise ValueError('replace needs text and/or heading')
        if self.op == 'insert' and (not self.provisions or not self.insert_after):
            raise ValueError('insert needs provisions and insert_after')
        return self


class AmendingAct(FileModel):
    doc_id: Text
    title: Text
    amends: Text = Field(description='doc_id of the raw document the amendments apply to')
    oj_ref: str = ''
    source_url: str = ''
    amendments: list[Amendment] = Field(description='Applied in order')


# ------------------------------------------------------------------------------------------------ source layer
class SourceDocument(Model):
    sd_id: Text
    title: Text
    edition: str = ''
    doc_type: Vocab('SDTYPE')
    lifecycle_status: Vocab('SDSTATUS')
    status_date: Optional[dt.date] = None
    normative_strength: Vocab('STRENGTH')
    legal_link: str = ''
    licence_class: Vocab('LICENCE')
    notes: str = ''


class ProvisionAnnotation(Model):
    """Our judgement on one raw provision (rule A10: every provision gets one)."""
    ref: Text
    role: Vocab('SPROLE')
    in_catalogue_scope: bool
    scope_note: str = ''
    label: str = Field('', description='Short label (our wording)')
    condition_text: str = ''


class CoverageLink(Model):
    """SR -> CR coverage link (spec § 4.5). Identity is (sr_id, cr); author/date default to the SR's.
    `condition` restricts when this source requires the CR (and its descendants): in a project, a leaf CR is applicable
    if its own rule holds and, for at least one source of the basis, a condition of that source's nearest linking CR
    holds (spec § 4.5, § 5.4). `guidance` is source-specific assessor guidance added to the check items it selects."""
    cr: Text
    type: Vocab('LINKTYPE')
    condition: str = Field('', description='Applicability rule (rule vocabulary, spec § 4.6); empty = always')
    guidance: str = Field('', description='Source-specific guidance shown with the check items this link selects')
    rationale: str = ''
    author: str = ''
    date: Optional[dt.date] = None


class SourceRequirement(Model):
    sr_id: Text = Field(pattern=r'^SR\.[A-Za-z0-9\-]+\.\d{4}$')
    sp_refs: list[Text] = Field(min_length=1, description='SP IDs (<SD>:<ref>) of this source document')
    statement: Text
    obligation: Vocab('OBLIG')
    origin: Vocab('ORIGIN')
    author: str = ''
    date: Optional[dt.date] = None
    rationale: str = ''
    parameters: str = ''
    measure_rating: str = ''
    coverage_complete: bool
    notes: str = ''
    links: list[CoverageLink] = []


class Correspondence(Model):
    """Declared SP <-> SP correspondence claimed by this source document (spec § 4.10)."""
    corr_id: Text = Field(pattern=r'^C\d{4}$')
    basis: Vocab('CORRBASIS')
    from_sp: Text
    to_sp: Text
    declared_coverage: Vocab('ZACOV')
    remarks: str = ''


class SourceCatalogue(FileModel):
    """derived.json of one source document."""
    sd: SourceDocument
    provisions: list[ProvisionAnnotation] = []
    requirements: list[SourceRequirement] = []
    correspondences: list[Correspondence] = []


# ------------------------------------------------------------------------------------------------ catalogue layer
class Refinement(Model):
    """Non-hierarchical refinement of another CR (D0026). FULL: the FULL refinements of `cr` with the same `set`
    together satisfy it completely; a project that selects a complete set substitutes `cr` (no own CIs, status from
    the refining CRs, D0033, D0045). Several sets (e.g. one per standard) may refine the same CR. PARTLY: information
    only; `cr` is still assessed."""
    cr: Text
    coverage: Vocab('REFCOV') = 'PARTLY'
    set: str = Field('', description='Full-refinement set, usually the source it comes from (FULL only)')
    note: str = ''


class CommonRequirement(Model):
    cr_id: Text = Field(pattern=r'^CR\.[A-Z]+\.\d{3}(\.\d+)*$')
    title: Text
    statement: Text
    parent_cr: str = ''
    decomposition: Optional[Vocab('DECOMP')] = None
    refines: list['Refinement'] = Field([], description='CRs this CR refines without being their child (D0026, D0033)')
    cr_type: Vocab('CRTYPE')
    object_level: Vocab('OBJLEVEL')
    verification_method: Optional[Vocab('VMETHOD')] = None
    acceptance_criterion: str = ''
    criterion_source: str = ''
    assessor_guidance: str = ''
    expected_evidence: str = ''
    lifecycle_phase: Optional[Vocab('PHASE')] = None
    applicability_rule: str = 'TRUE'
    tension_flag: bool = False
    status: Vocab('CRSTATUS')
    author: str = ''
    notes: str = ''

    @property
    def domain(self):
        return self.cr_id.split('.')[1]

    @field_validator('cr_id')
    @classmethod
    def _domain_known(cls, v):
        if v.split('.')[1] not in vocab.keys('DOMAIN'):
            raise ValueError(f'domain of {v} is not a key of register list DOMAIN')
        return v


class CommonRequirementsFile(FileModel):
    requirements: list[CommonRequirement]


class Decision(Model):
    dec_id: Text = Field(pattern=r'^D\d{4}$')
    date: dt.date
    author: Text
    type: Vocab('DECTYPE')
    affected_ids: Text
    rationale: Text
    source_refs: str = ''


class DecisionsFile(FileModel):
    decisions: list[Decision]


class KnownPack(Model):
    """A pack the master list is built from (spec § 8.3). Public packs give their default location; private packs are
    found via --pack, CTM_PACKS or ctm.local.json. CRs reached only by packs that are not loaded are not orphans."""
    pack_id: Text
    title: str = ''
    access: Literal['public', 'private']
    path: str = Field('', description='Default location relative to the master list directory (loaded by default)')


class CatalogueManifest(FileModel):
    """catalogue.json of the master list."""
    baseline: Text = Field(description='Catalogue baseline ID, e.g. CAT-2026.1-draft')
    title: str = ''
    known_packs: list[KnownPack] = Field([], description='All packs of this baseline, in catalogue order')


class PackManifest(FileModel):
    """pack.json: one source document (plus its amending acts) with its SRs and coverage links to the master list."""
    pack_id: Text = Field(pattern=r'^[A-Za-z0-9\-]+$')
    title: str = ''
    requires: list[Text] = Field([], description='Packs whose provisions the correspondences of this pack reference')
    sources: list[Text] = Field(min_length=1, description='SD IDs; each has sources/<SD>/derived.json '
                                                          '(+ raw.json unless the SD has no provisions)')
    amending_acts: list[Text] = Field([], description='Amending acts in sources/<ACT>/raw.json, applied in order to '
                                                      'raw documents of this pack')


# ------------------------------------------------------------------------------------------------ project seed
class ProjectHeader(Model):
    project_id: Text = Field(pattern=r'^P\d{5}$')
    client: str = ''
    product: str = ''
    description: str = ''
    use_cases: str = ''
    catalogue_baseline: str = ''
    boundary_statement: str = ''
    agreed_exclusions: str = ''
    assessor: str = ''
    reviewer: str = ''
    start_date: Optional[dt.date] = None


class BasisEntry(Model):
    sd_id: Text
    edition: str = ''
    use_case: Optional[Vocab('USECASE')] = None
    note: str = ''


class AssessmentObject(Model):
    object_id: Text
    level: Vocab('OBJLEVEL')
    name: str = ''
    description: str = ''
    parent_object: str = ''


class EvidenceItem(Model):
    ev_id: Text = Field(pattern=r'^P\d{5}-EV-\d{3}$')
    title: str = ''
    client_doc_id: str = ''
    version: str = ''
    date: Optional[dt.date] = None
    type: Optional[Vocab('EVTYPE')] = None
    owner: str = ''
    confidentiality: str = ''
    location: str = ''


class ProjectSeed(FileModel):
    """Initial content of a project workbook's input sheets (build_project.py --init --seed)."""
    prj: ProjectHeader
    basis: list[BasisEntry] = []
    tags: dict[str, str] = Field({}, description='Tag -> value, in the rule vocabulary (e.g. "AI.learning": "static")')
    objects: list[AssessmentObject] = []
    ev: list[EvidenceItem] = []

    @field_validator('tags')
    @classmethod
    def _tags_known(cls, tags):
        lists = {e[1]: e[3] for e in vocab.DEFAULT['TAG']}
        for t, v in tags.items():
            if t not in lists:
                raise ValueError(f'unknown tag {t!r}')
            if v and v not in vocab.labels(lists[t]):
                raise ValueError(f'value {v!r} not allowed for tag {t} {vocab.labels(lists[t])}')
        return tags


FILE_MODELS = {
    'catalogue': CatalogueManifest,
    'pack': PackManifest,
    'raw': RawDocument,
    'amendments': AmendingAct,
    'derived': SourceCatalogue,
    'common_requirements': CommonRequirementsFile,
    'decisions': DecisionsFile,
    'project': ProjectSeed,
}

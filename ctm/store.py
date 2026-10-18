"""Catalogue store: load / validate / save the JSON files of ctm/model.py and export them as workbook tables.

load_catalogue(root, packs=None, defaults=True) -> Catalogue
                                 master list at root + packs (spec § 8.3), validated, amendments applied,
                                 raw provisions joined with their annotations
resolve_packs(root, packs=None, defaults=True)
                                 pack directories: public packs of the master list (defaults) + extra packs from the
                                 explicit list > env CTM_PACKS > ctm.local.json next to root
write_model(model, path)         canonical JSON (2-space indent, UTF-8, model field order, defaults omitted)
format_tree(root, packs=())      rewrite every JSON file of the master list (and the given packs) in canonical form
to_tables(cat)                   {sheet: [row dict]} with register labels, as written into the catalogue workbook
"""
import json
import os
from dataclasses import dataclass, field
from typing import Optional

from pydantic import BaseModel, ValidationError

from . import vocab
from .model import (AmendingAct, CatalogueManifest, CommonRequirementsFile, DecisionsFile, PackManifest, ProjectSeed,
                    RawDocument, SourceCatalogue)

SCHEMA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'schemas')
SCHEMA_FILE = {CatalogueManifest: 'catalogue', PackManifest: 'pack', RawDocument: 'raw', AmendingAct: 'amendments',
               SourceCatalogue: 'derived', CommonRequirementsFile: 'common_requirements', DecisionsFile: 'decisions',
               ProjectSeed: 'project'}
LOCAL_CONFIG = 'ctm.local.json'      # {"packs": ["<pack or directory of packs, relative to this file>", ...]}; not committed
PACK_FILE = 'pack.json'              # marks a pack directory


class CatalogueError(Exception):
    """A file is missing or does not match its model."""


@dataclass
class SourceProvision:
    """Raw provision (after amendments) joined with its annotation."""
    sp_id: str
    sd_id: str
    ref: str
    seq: int
    parent_sp: str
    kind: Optional[str]
    heading: str
    text: str
    verbatim: bool
    amended_by: list
    role: str
    in_catalogue_scope: bool
    scope_note: str
    label: str
    condition_text: str


@dataclass
class Catalogue:
    root: str
    manifest: CatalogueManifest                     # master list manifest (known packs)
    sources: dict                                   # sd_id -> SourceCatalogue
    raw: dict                                       # sd_id -> RawDocument (consolidated)
    sds: dict                                       # sd_id -> SourceDocument
    sps: dict                                       # sp_id -> SourceProvision (catalogue order)
    srs: dict                                       # sr_id -> SourceRequirement
    sr_sd: dict                                     # sr_id -> sd_id of the file it is in
    crs: dict                                       # cr_id -> CommonRequirement
    decisions: list
    corr: list                                      # [(claimant sd_id, Correspondence)]
    acts: dict = field(default_factory=dict)        # act doc_id -> AmendingAct
    load_errors: list = field(default_factory=list)
    packs: dict = field(default_factory=dict)       # pack_id -> (directory, PackManifest), in load order
    pack_of_sd: dict = field(default_factory=dict)  # sd_id / act doc_id -> pack_id

    def missing_packs(self):
        """Known packs of the master list that are not loaded."""
        return [k.pack_id for k in self.manifest.known_packs if k.pack_id not in self.packs]

    def links(self):
        """[(link_id, sr_id, CoverageLink)] in catalogue order; link IDs are generated (spec § 6.1)."""
        out = []
        for sr_id, sr in self.srs.items():
            for l in sr.links:
                out.append((f'L{len(out) + 1:04d}', sr_id, l))
        return out


# ------------------------------------------------------------------------------------------------ files
def read_model(path, cls):
    try:
        with open(path, encoding='utf-8') as f:
            return cls.model_validate(json.load(f))
    except FileNotFoundError:
        raise CatalogueError(f'{path}: file missing') from None
    except json.JSONDecodeError as ex:
        raise CatalogueError(f'{path}: invalid JSON: {ex}') from None
    except ValidationError as ex:
        raise CatalogueError(f'{path}: {ex}') from None


def dumps_model(model: BaseModel, path):
    data = model.model_dump(mode='json', by_alias=True, exclude_defaults=True)
    data.pop('$schema', None)
    rel = os.path.relpath(os.path.join(SCHEMA_DIR, SCHEMA_FILE[type(model)] + '.schema.json'),
                          os.path.dirname(os.path.abspath(path)))
    return json.dumps({'$schema': rel.replace(os.sep, '/'), **data}, indent=2, ensure_ascii=False) + '\n'


def write_model(model: BaseModel, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(dumps_model(model, path))
    return path


def is_pack(d):
    return os.path.exists(os.path.join(d, PACK_FILE))


def catalogue_files(root):
    """[(path, model class)] of every file of a master list directory or of a pack directory. The master list needs
    catalogue.json, common_requirements.json and decisions.json; a pack needs pack.json and its source files,
    decisions.json is optional."""
    if is_pack(root):
        man_path = os.path.join(root, PACK_FILE)
        man = read_model(man_path, PackManifest)
        out = [(man_path, PackManifest)]
        for sd in man.sources:
            raw = os.path.join(root, 'sources', sd, 'raw.json')
            if os.path.exists(raw):
                out.append((raw, RawDocument))
            out.append((os.path.join(root, 'sources', sd, 'derived.json'), SourceCatalogue))
        for act in man.amending_acts:
            out.append((os.path.join(root, 'sources', act, 'raw.json'), AmendingAct))
        p = os.path.join(root, 'decisions.json')
        if os.path.exists(p):
            out.append((p, DecisionsFile))
        return out
    return [(os.path.join(root, 'catalogue.json'), CatalogueManifest),
            (os.path.join(root, 'common_requirements.json'), CommonRequirementsFile),
            (os.path.join(root, 'decisions.json'), DecisionsFile)]


def pack_dirs(path):
    """A pack directory, or every pack directly inside a directory of packs (sorted by name)."""
    path = os.path.abspath(path)
    if is_pack(path) or not os.path.isdir(path):
        return [path]
    return [os.path.join(path, d) for d in sorted(os.listdir(path)) if is_pack(os.path.join(path, d))]


def default_packs(root):
    """Pack directories named by the known packs of the master list at root (public packs)."""
    man = read_model(os.path.join(root, 'catalogue.json'), CatalogueManifest)
    return [os.path.normpath(os.path.join(os.path.abspath(root), k.path)) for k in man.known_packs if k.path]


def resolve_packs(root, packs=None, defaults=True):
    """Pack directories loaded with the master list at root (spec § 8.3): the public packs named in its catalogue.json
    (unless defaults=False), then the extra packs, in this order of precedence: the explicit list (packs=[] means none)
    > environment variable CTM_PACKS (os.pathsep-separated) > ctm.local.json in the directory above root (the
    repository root), paths relative to that file. A path may be one pack or a directory of packs."""
    if packs is not None:
        extra = [os.path.abspath(p) for p in packs]
    elif os.environ.get('CTM_PACKS') is not None:
        extra = [os.path.abspath(p) for p in os.environ['CTM_PACKS'].split(os.pathsep) if p.strip()]
    else:
        extra = []
        cfg = os.path.join(os.path.dirname(os.path.abspath(root)), LOCAL_CONFIG)
        if os.path.exists(cfg):
            with open(cfg, encoding='utf-8') as f:
                rel = json.load(f).get('packs', [])
            extra = [os.path.normpath(os.path.join(os.path.dirname(cfg), p)) for p in rel]
    out = []
    for d in (default_packs(root) if defaults else []) + [x for p in extra for x in pack_dirs(p)]:
        if d not in out:
            out.append(d)
    return out


def format_tree(root, packs=()):
    """Rewrite all files of the master list at root and of the given pack directories in canonical form; returns the
    paths that changed."""
    changed = []
    for d in [root, *packs]:
        for path, cls in catalogue_files(d):
            new = dumps_model(read_model(path, cls), path)
            with open(path, encoding='utf-8') as f:
                old = f.read()
            if new != old:
                with open(path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(new)
                changed.append(path)
    return changed


def load_project_seed(path):
    return read_model(path, ProjectSeed)


# ------------------------------------------------------------------------------------------------ amendments
def _subtree_end(provs, i):
    """Index after the last descendant of provs[i] (descendants follow their ancestor in document order)."""
    inside = {provs[i].ref}
    j = i + 1
    while j < len(provs) and provs[j].parent in inside:
        inside.add(provs[j].ref)
        j += 1
    return j


def apply_amendments(doc: RawDocument, act: AmendingAct, errors):
    """Return (consolidated document, {ref: [amending_ref]}). Problems are appended to errors."""
    provs = list(doc.provisions)
    amended = {}
    for n, a in enumerate(act.amendments, 1):
        where = f'{act.doc_id} amendment {n} ({a.amending_ref})'
        idx = {p.ref: i for i, p in enumerate(provs)}
        if a.op == 'insert':
            if a.insert_after not in idx:
                errors.append(f'{where}: insert_after {a.insert_after} not in {doc.doc_id}'); continue
            dup = [p.ref for p in a.provisions if p.ref in idx]
            if dup:
                errors.append(f'{where}: {", ".join(dup)} already in {doc.doc_id}'); continue
            at = _subtree_end(provs, idx[a.insert_after])
            provs[at:at] = a.provisions
            for p in a.provisions:
                amended.setdefault(p.ref, []).append(a.amending_ref)
            continue
        if a.target_ref not in idx:
            errors.append(f'{where}: target {a.target_ref} not in {doc.doc_id}'); continue
        i = idx[a.target_ref]
        if a.op == 'delete':
            del provs[i:_subtree_end(provs, i)]
        else:
            upd = {k: v for k, v in (('text', a.text), ('heading', a.heading)) if v is not None}
            provs[i] = provs[i].model_copy(update=upd)
            amended.setdefault(a.target_ref, []).append(a.amending_ref)
    return doc.model_copy(update={'provisions': provs}), amended


# ------------------------------------------------------------------------------------------------ load
def load_catalogue(root, packs=None, defaults=True) -> Catalogue:
    """Master list at root plus the packs resolved by resolve_packs(root, packs, defaults). Packs are loaded in the
    order of the known packs of the master list, unknown packs after them. Packs add sources, amending acts (applied
    to raw documents of the same pack) and decisions; nothing is overwritten (duplicate IDs are load errors).
    Cross-pack references are checked by ctm.checks (spec § 8.3)."""
    root = os.path.abspath(root)
    errors = []
    if is_pack(root):
        raise CatalogueError(f'{root}: is a pack; give the master list directory (catalogue/) and load packs with it')
    man_master = read_model(os.path.join(root, 'catalogue.json'), CatalogueManifest)
    known = [k.pack_id for k in man_master.known_packs]
    found = []
    for d in resolve_packs(root, packs, defaults):
        if not is_pack(d):
            errors.append(f'PACK {d}: no {PACK_FILE} (not a pack)'); continue
        found.append((d, read_model(os.path.join(d, PACK_FILE), PackManifest)))
    found.sort(key=lambda x: known.index(x[1].pack_id) if x[1].pack_id in known else len(known))
    packs_loaded, pack_of_sd = {}, {}
    raw, amended_by, acts, sources, order = {}, {}, {}, {}, []
    crs, decisions = {}, []
    for c in read_model(os.path.join(root, 'common_requirements.json'), CommonRequirementsFile).requirements:
        if c.cr_id in crs: errors.append(f'CR {c.cr_id}: duplicate ID'); continue
        crs[c.cr_id] = c
    decisions += read_model(os.path.join(root, 'decisions.json'), DecisionsFile).decisions
    for d, man in found:
        files = dict(catalogue_files(d))
        pid = man.pack_id
        if pid in packs_loaded:
            errors.append(f'PACK {pid}: loaded twice ({packs_loaded[pid][0]}, {d})'); continue
        packs_loaded[pid] = (d, man)
        src = lambda sd, f: os.path.join(d, 'sources', sd, f)
        for sd in man.sources:
            if sd in pack_of_sd:
                errors.append(f'SD {sd}: defined in packs {pack_of_sd[sd]} and {pid}'); continue
            pack_of_sd[sd] = pid; order.append(sd); amended_by[sd] = {}
            if src(sd, 'raw.json') in files:
                raw[sd] = read_model(src(sd, 'raw.json'), RawDocument)
        for act_id in man.amending_acts:
            act = acts[act_id] = read_model(src(act_id, 'raw.json'), AmendingAct)
            pack_of_sd.setdefault(act_id, pid)
            if act.amends not in raw or pack_of_sd.get(act.amends) != pid:
                errors.append(f'{act_id}: amends {act.amends}, which is not a raw document of pack {pid}'); continue
            raw[act.amends], amd = apply_amendments(raw[act.amends], act, errors)
            for k, v in amd.items():
                amended_by[act.amends].setdefault(k, []).extend(v)
        for sd in man.sources:
            if pack_of_sd.get(sd) != pid: continue
            sc = sources[sd] = read_model(src(sd, 'derived.json'), SourceCatalogue)
            if sc.sd.sd_id != sd:
                errors.append(f'sources/{sd}/derived.json: sd_id is {sc.sd.sd_id}')
            if sd in raw and raw[sd].doc_id != sd:
                errors.append(f'sources/{sd}/raw.json: doc_id is {raw[sd].doc_id}')
        p = os.path.join(d, 'decisions.json')
        if p in files:
            decisions += read_model(p, DecisionsFile).decisions

    sps, srs, sr_sd, corr = {}, {}, {}, []
    for sd in order:
        if sd not in sources: continue
        provs = raw[sd].provisions if sd in raw else []
        ann = {}
        for a in sources[sd].provisions:
            if a.ref in ann: errors.append(f'SP {sd}:{a.ref}: annotated twice')
            ann[a.ref] = a
        seen = set()
        for i, p in enumerate(provs, 1):
            sp_id = f'{sd}:{p.ref}'
            if p.ref in seen:
                errors.append(f'SP {sp_id}: duplicate ref in raw text'); continue
            seen.add(p.ref)
            a = ann.get(p.ref)
            if a is None:
                errors.append(f'SP {sp_id}: provision has no annotation (rule A10: list every provision)'); continue
            sps[sp_id] = SourceProvision(
                sp_id=sp_id, sd_id=sd, ref=p.ref, seq=i * 10, parent_sp=f'{sd}:{p.parent}' if p.parent else '',
                kind=p.kind, heading=p.heading, text=p.text, verbatim=p.verbatim, amended_by=amended_by[sd].get(p.ref, []),
                role=a.role, in_catalogue_scope=a.in_catalogue_scope, scope_note=a.scope_note, label=a.label,
                condition_text=a.condition_text)
        for ref in ann.keys() - seen:
            errors.append(f'SP {sd}:{ref}: annotation without provision in raw text')
        for r in sources[sd].requirements:
            if r.sr_id in srs: errors.append(f'SR {r.sr_id}: duplicate ID'); continue
            srs[r.sr_id] = r; sr_sd[r.sr_id] = sd
        corr += [(sd, c) for c in sources[sd].correspondences]

    return Catalogue(root=root, manifest=man_master, sources=sources, raw=raw, sds={sd: s.sd for sd, s in sources.items()},
                     sps=sps, srs=srs, sr_sd=sr_sd, crs=crs, decisions=decisions, corr=corr, acts=acts,
                     load_errors=errors, packs=packs_loaded, pack_of_sd=pack_of_sd)


def refines_full_text(c):
    """Export form of the full refinements of a CR: "CR.X; CR.Y [SET]" (set in brackets when given)."""
    return '; '.join(x.cr + (f' [{x.set}]' if x.set else '') for x in c.refines if x.coverage == 'FULL')


# ------------------------------------------------------------------------------------------------ export
def _lab(lst, key):
    return vocab.label_of(lst, key) if key else ''


def _yn(b):
    return vocab.label_of('YN', 'YES' if b else 'NO')


def _d(d):
    return d.isoformat() if d else ''


def to_tables(cat: Catalogue, internal=False):
    """Catalogue as {sheet: [row dict keyed by ctm.schema Col.key]}, values as register labels.
    Verbatim text of licensed sources is omitted unless internal=True (spec § 7)."""
    t = {}
    t['SD'] = [dict(sd_id=s.sd_id, title=s.title, edition=s.edition, doc_type=_lab('SDTYPE', s.doc_type),
                    lifecycle_status=_lab('SDSTATUS', s.lifecycle_status), status_date=_d(s.status_date),
                    normative_strength=_lab('STRENGTH', s.normative_strength), legal_link=s.legal_link,
                    licence_class=_lab('LICENCE', s.licence_class), notes=s.notes) for s in cat.sds.values()]
    t['SP'] = [dict(sp_id=p.sp_id, sd_id=p.sd_id, native_ref=p.ref, seq=p.seq, parent_sp=p.parent_sp,
                    role=_lab('SPROLE', p.role), heading=p.heading, label=p.label,
                    text=p.text if internal or cat.sds[p.sd_id].licence_class != 'LICENSED' else '',
                    condition_text=p.condition_text, in_catalogue_scope=_yn(p.in_catalogue_scope),
                    scope_note=p.scope_note) for p in cat.sps.values()]
    t['SR'] = [dict(sr_id=r.sr_id, sp_refs='; '.join(r.sp_refs), statement=r.statement,
                    obligation=_lab('OBLIG', r.obligation), origin=_lab('ORIGIN', r.origin), author=r.author,
                    date=_d(r.date), rationale=r.rationale, parameters=r.parameters, measure_rating=r.measure_rating,
                    coverage_complete=_yn(r.coverage_complete), notes=r.notes) for r in cat.srs.values()]
    t['CR'] = [dict(cr_id=c.cr_id, domain=c.domain, title=c.title, statement=c.statement, parent_cr=c.parent_cr,
                    decomposition=_lab('DECOMP', c.decomposition), refines='; '.join(x.cr for x in c.refines),
                    refines_full=refines_full_text(c), cr_type=_lab('CRTYPE', c.cr_type),
                    object_level=_lab('OBJLEVEL', c.object_level),
                    verification_method=_lab('VMETHOD', c.verification_method),
                    acceptance_criterion=c.acceptance_criterion, criterion_source=c.criterion_source,
                    assessor_guidance=c.assessor_guidance, expected_evidence=c.expected_evidence,
                    lifecycle_phase=_lab('PHASE', c.lifecycle_phase), applicability_rule=c.applicability_rule,
                    tension_flag=_yn(c.tension_flag), status=_lab('CRSTATUS', c.status), author=c.author,
                    notes=c.notes) for c in cat.crs.values()]
    t['LINK_SR_CR'] = [dict(link_id=lid, sr_id=sr_id, cr_id=l.cr, link_type=_lab('LINKTYPE', l.type),
                            condition=l.condition, guidance=l.guidance,
                            rationale=l.rationale, author=l.author or cat.srs[sr_id].author,
                            date=_d(l.date or cat.srs[sr_id].date)) for lid, sr_id, l in cat.links()]
    t['CORR'] = [dict(corr_id=c.corr_id, basis=_lab('CORRBASIS', c.basis), claimant_sd=sd, from_sp=c.from_sp,
                      to_sp=c.to_sp, declared_coverage=_lab('ZACOV', c.declared_coverage), remarks=c.remarks)
                 for sd, c in sorted(cat.corr, key=lambda x: x[1].corr_id)]
    t['DECISIONS'] = [dict(dec_id=d.dec_id, date=_d(d.date), author=d.author, type=_lab('DECTYPE', d.type),
                           affected_ids=d.affected_ids, rationale=d.rationale, source_refs=d.source_refs)
                      for d in cat.decisions]
    return t


def seed_inputs(seed: ProjectSeed):
    """Project seed -> (prj, basis, tags, objects, ev) in workbook form (labels), for build_project.init_project."""
    from .schema import PRJ_FIELD_KEYS
    h = seed.prj.model_dump()
    prj = {lab: (_d(h[k]) if k == 'start_date' else h[k]) for k, lab in PRJ_FIELD_KEYS}
    basis = [dict(sd_id=b.sd_id, edition=b.edition, use_case=_lab('USECASE', b.use_case), note=b.note) for b in seed.basis]
    objects = [dict(o.model_dump(), level=_lab('OBJLEVEL', o.level)) for o in seed.objects]
    ev = [dict(e.model_dump(), date=_d(e.date), type=_lab('EVTYPE', e.type)) for e in seed.ev]
    return prj, basis, dict(seed.tags), objects, ev

"""Web viewer API: serves the consolidated catalogue and evaluates project seeds with ctm.project (local use only).

create_app(root, packs=None, defaults=True, internal=False, projects=(), static_dir=None) -> FastAPI

GET  /api/catalogue              {meta, vocab, tables}: the catalogue tables of store.to_tables() (register labels)
POST /api/reload                 reload the JSON store (after editing the catalogue or packs)
GET  /api/projects               project seeds found in the project directories
GET  /api/projects/{pid}         one seed (JSON)
POST /api/project/evaluate       {seed, tags?} -> selection, rule results, CIs and checklist views of the seed;
                                 tags override the seed's tags ('' unsets a tag)
POST /api/applicability          {basis, tags} -> rule results of the CRs the basis selects (no objects, no CIs)

Verbatim text of licensed sources is only served with internal=True (spec § 7).
"""
import glob
import json
import os
from typing import Optional

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import ValidationError

from ctm import vocab
from ctm.model import ProjectSeed
from ctm.project import checklist_rows, register_from_vocab, select_project
from ctm.store import CatalogueError, load_catalogue, seed_inputs, to_tables


class _State:
    def __init__(self, root, packs, defaults, internal, projects):
        self.root, self.packs, self.defaults, self.internal = root, packs, defaults, internal
        self.projects = [p for p in projects if p]
        self.reg = register_from_vocab()
        self.load()

    def load(self):
        cat = load_catalogue(self.root, self.packs, self.defaults)
        t = to_tables(cat, internal=self.internal)
        for r in t['SP']:                           # extras the workbook does not carry
            p = cat.sps[r['sp_id']]
            r.update(kind=p.kind or '', amended_by=list(p.amended_by))
        self.tables = t
        self.catalogue = dict(
            meta=dict(baseline=cat.manifest.baseline, title=cat.manifest.title, internal=self.internal,
                      packs=[dict(pack_id=k, title=m.title, sources=list(m.sources)) for k, (_, m) in cat.packs.items()],
                      missing_packs=cat.missing_packs(), load_errors=list(cat.load_errors),
                      licensed=[s.sd_id for s in cat.sds.values() if s.licence_class == 'LICENSED']),
            vocab={lst: [dict(key=k, label=lab, colour=col or '', attr=attr or '', desc=desc or '')
                         for k, lab, col, attr, desc in entries] for lst, entries in vocab.DEFAULT.items()},
            tables=t)

    def seeds(self):
        """{project_id: (path, ProjectSeed | None, error)} of all seed files (later directories win)."""
        out = {}
        for d in self.projects:
            for path in sorted(glob.glob(os.path.join(d, '*.json'))):
                try:
                    with open(path, encoding='utf-8') as f:
                        data = json.load(f)
                    if not isinstance(data, dict) or 'prj' not in data:
                        continue                    # not a seed (other JSON in the folder)
                    seed = ProjectSeed.model_validate(data)
                    out[seed.prj.project_id] = (path, seed, '')
                except (ValueError, ValidationError) as ex:
                    out[os.path.splitext(os.path.basename(path))[0]] = (path, None, str(ex))
        return out


def _validation_error(ex):
    return HTTPException(422, detail=json.loads(ex.json(include_url=False)))


def _seed_with_tags(seed: dict, tags: Optional[dict]):
    data = dict(seed)
    if tags:
        merged = dict(data.get('tags') or {})
        for k, v in tags.items():
            if v in ('', None):
                merged.pop(k, None)
            else:
                merged[k] = v
        data['tags'] = merged
    try:
        return ProjectSeed.model_validate(data)
    except ValidationError as ex:
        raise _validation_error(ex) from None


def _result(res):
    return {True: True, False: False}.get(res)


def _evaluate(state, basis, tags, objects):
    S = select_project(state.tables, state.reg, basis, tags, objects)
    substitutes = {}
    for x, ys in S.subst.items():
        for y in ys:
            substitutes.setdefault(y, []).append(x)
    crs = {}
    for k in S.crs:
        leaf = k in S.rule_res
        d = dict(leaf=leaf, leaves=S.leaves(k), expanded=S.expand(k), substituted_by=S.subst.get(k, []),
                 substitutes=substitutes.get(k, []))
        if leaf:
            res, unk = S.rule_res[k]
            d.update(eff_rule=S.eff_rule[k], result=_result(res), unknown=unk, guidance=S.guid[k])
        crs[k] = d
    return S, crs


def create_app(root, packs=None, defaults=True, internal=False, projects=(), static_dir=None):
    state = _State(root, packs, defaults, internal, projects)
    app = FastAPI(title='Compliance Traceability viewer', docs_url='/api/docs', openapi_url='/api/openapi.json')
    app.state.ctm = state

    @app.get('/api/catalogue')
    def catalogue():
        return state.catalogue

    @app.post('/api/reload')
    def reload():
        try:
            state.load()
        except CatalogueError as ex:
            raise HTTPException(500, detail=str(ex)) from None
        return state.catalogue['meta']

    @app.get('/api/projects')
    def projects_list():
        out = []
        for pid, (path, seed, err) in sorted(state.seeds().items()):
            if seed:
                out.append(dict(project_id=pid, product=seed.prj.product, client=seed.prj.client,
                                basis=[b.sd_id for b in seed.basis], file=os.path.basename(path)))
            else:
                out.append(dict(project_id=pid, file=os.path.basename(path), error=err))
        return out

    @app.get('/api/projects/{pid}')
    def project_seed(pid: str):
        path, seed, err = state.seeds().get(pid, (None, None, 'unknown project'))
        if not seed:
            raise HTTPException(404, detail=err)
        return seed.model_dump(mode='json', exclude={'schema_ref'}, exclude_none=True)

    @app.post('/api/project/evaluate')
    def project_evaluate(seed: dict = Body(...), tags: Optional[dict] = Body(None)):
        sd = _seed_with_tags(seed, tags)
        prj, basis, tags_, objects, _ = seed_inputs(sd)
        known = {r['sd_id'] for r in state.tables['SD']}
        basis_ids = [b['sd_id'] for b in basis]
        S, crs = _evaluate(state, basis_ids, tags_, objects)
        views = {}
        for sd_id in basis_ids:
            views[sd_id] = [dict(sp_id=p['sp_id'], clause=p['native_ref'], heading=heading, sr_id=r['sr_id'],
                                 cr_id=cr, ci_id=c['ci_id'] if c else None)
                            for p, heading, r, cr, c in checklist_rows(S, sd_id)]
        return dict(
            seed=sd.model_dump(mode='json', exclude={'schema_ref'}, exclude_none=True),
            tags=tags_, objects=objects, basis=basis,
            missing_sources=[b for b in basis_ids if b not in known],
            selection=dict(sp=list(S.sp), sr=list(S.sr)),
            crs=crs,
            cis=[{k: c[k] for k in ('ci_id', 'object_id', 'level', 'cr_id', 'rule_applicability',
                                     'applicability_justification')} for c in S.ci_rows],
            views=views,
            counts=dict(ci=len(S.ci_rows), cr=len(S.crs), sr=len(S.sr), sp=len(S.sp), links=len(S.links),
                        substituted=len(S.subst)))

    @app.post('/api/applicability')
    def applicability(basis: list = Body(...), tags: dict = Body({})):
        try:
            ProjectSeed.model_validate(dict(prj=dict(project_id='P00000'), tags={k: v for k, v in tags.items() if v}))
        except ValidationError as ex:
            raise _validation_error(ex) from None
        _, crs = _evaluate(state, basis, {k: v for k, v in tags.items() if v}, [])
        return dict(crs=crs)

    if static_dir and os.path.isdir(static_dir):
        static_dir = os.path.abspath(static_dir)

        @app.get('/{path:path}', include_in_schema=False)
        def spa(path: str):
            if path.startswith('api/'):
                raise HTTPException(404)
            f = os.path.abspath(os.path.join(static_dir, path))
            if path and f.startswith(static_dir + os.sep) and os.path.isfile(f):
                return FileResponse(f)
            return FileResponse(os.path.join(static_dir, 'index.html'))

    return app

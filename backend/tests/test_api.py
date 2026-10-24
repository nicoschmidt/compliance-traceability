"""Web viewer API on the sample fixtures (pytest; needs fastapi and httpx)."""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import pytest                                                                         # noqa: E402

pytest.importorskip('fastapi')
pytest.importorskip('httpx')
from fastapi.testclient import TestClient                                             # noqa: E402

from backend.app import create_app                                                    # noqa: E402
from ctm.project import register_from_vocab, select_project                           # noqa: E402
from ctm.store import load_catalogue, load_project_seed, seed_inputs, to_tables       # noqa: E402

FIX = os.path.join(ROOT, 'tests', 'fixtures')
SAMPLE = os.path.join(FIX, 'sample', 'catalogue')
EXTRA = os.path.join(FIX, 'extra_packs')
SEED = os.path.join(FIX, 'sample_project.json')


def client(**kw):
    return TestClient(create_app(SAMPLE, kw.pop('packs', []), projects=[FIX], **kw))


def seed_json():
    with open(SEED, encoding='utf-8') as f:
        return json.load(f)


def test_catalogue_omits_licensed_text():
    for internal in (False, True):
        c = client(packs=[EXTRA], internal=internal)
        cat = c.get('/api/catalogue').json()
        assert 'DEMO' in cat['meta']['licensed']
        demo = [r for r in cat['tables']['SP'] if r['sd_id'] == 'DEMO']
        assert demo and any(r['text'] for r in demo) == internal
        assert all('kind' in r for r in cat['tables']['SP'])
        assert {'TAG', 'LINKTYPE'} <= set(cat['vocab'])


def test_projects_list_and_seed():
    c = client()
    lst = c.get('/api/projects').json()
    assert [p['project_id'] for p in lst] == ['P26001']          # sample_ci_entries.json is not a seed
    seed = c.get('/api/projects/P26001').json()
    assert seed['prj']['project_id'] == 'P26001' and '$schema' not in seed
    assert c.get('/api/projects/P99999').status_code == 404


def test_evaluate_matches_select_project():
    c = client()
    j = c.post('/api/project/evaluate', json={'seed': seed_json()}).json()
    _, basis, tags, objects, _ = seed_inputs(load_project_seed(SEED))
    sel = select_project(to_tables(load_catalogue(SAMPLE, [])), register_from_vocab(),
                         [b['sd_id'] for b in basis], tags, objects)
    assert [x['ci_id'] for x in j['cis']] == [x['ci_id'] for x in sel.ci_rows]
    assert list(j['crs']) == list(sel.crs)
    assert {k: v['substituted_by'] for k, v in j['crs'].items() if v['substituted_by']} == sel.subst
    for k, (res, unk) in sel.rule_res.items():
        assert (j['crs'][k]['result'], j['crs'][k]['unknown']) == (res, unk)
    assert set(j['views']) == {b['sd_id'] for b in basis}


def test_evaluate_tag_overrides():
    c = client()
    base = c.post('/api/project/evaluate', json={'seed': seed_json()}).json()
    unset = c.post('/api/project/evaluate', json={'seed': seed_json(), 'tags': {'AI.learning': ''}}).json()
    assert 'AI.learning' in base['tags'] and 'AI.learning' not in unset['tags']


def test_invalid_seed_is_422():
    c = client()
    r = c.post('/api/project/evaluate', json={'seed': seed_json(), 'tags': {'bogus.tag': 'x'}})
    assert r.status_code == 422 and 'unknown tag' in json.dumps(r.json())
    assert c.post('/api/project/evaluate', json={'seed': {'prj': {'project_id': 'X'}}}).status_code == 422


def test_applicability():
    c = client()
    j = c.post('/api/applicability', json={'basis': ['TR5469'], 'tags': {}}).json()
    assert j['crs'] and all(v['result'] is not False for v in j['crs'].values() if v['leaf'])
    assert c.post('/api/applicability', json={'basis': ['TR5469'], 'tags': {'nope': 'x'}}).status_code == 422

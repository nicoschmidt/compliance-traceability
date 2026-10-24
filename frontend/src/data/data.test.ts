import { describe, expect, it } from 'vitest'
import type { CatalogueData, CrEval, CrRow, Evaluation, LinkRow, SpRow, SrRow } from '../api'
import { buildIndex, decisionsMentioning } from './catalogue'
import { hrefFor, readTags, tokenize, writeTags, type RouteCtx } from './ids'
import { buildCrTree, buildDocTree, collectIds, filterTree, flatten, pathTo, projectCtx, searchTree, type TreeNode } from './tree'

const sp = (sp_id: string, parent_sp = '', seq = 0, extra: Partial<SpRow> = {}): SpRow => ({
  sp_id, sd_id: sp_id.split(':')[0], native_ref: sp_id.split(':')[1], seq, parent_sp, role: 'Atomic', heading: '',
  label: '', text: `text of ${sp_id}`, condition_text: '', in_catalogue_scope: 'yes', scope_note: '', kind: 'article',
  amended_by: [], ...extra,
})
const sr = (sr_id: string, sp_refs: string): SrRow => ({
  sr_id, sp_refs, statement: `statement ${sr_id}`, obligation: 'shall', origin: 'Verbatim', author: '', date: '',
  rationale: '', parameters: '', measure_rating: '', coverage_complete: 'yes', notes: '',
})
const cr = (cr_id: string, parent_cr = '', extra: Partial<CrRow> = {}): CrRow => ({
  cr_id, domain: cr_id.split('.')[1], title: `title ${cr_id}`, statement: '', parent_cr, decomposition: '', refines: '',
  refines_full: '', cr_type: '', object_level: 'PRD', verification_method: '', acceptance_criterion: '',
  criterion_source: '', assessor_guidance: '', expected_evidence: '', lifecycle_phase: '', applicability_rule: 'TRUE',
  tension_flag: 'no', status: 'Released', author: '', notes: '', ...extra,
})
const link = (sr_id: string, cr_id: string, link_type = 'Covers', condition = ''): LinkRow => ({
  link_id: '', sr_id, cr_id, link_type, condition, guidance: '', rationale: '', author: '', date: '',
})

const DATA: CatalogueData = {
  meta: { baseline: 'T', title: 't', internal: false, licensed: ['TR'], missing_packs: [], load_errors: [], packs: [] },
  vocab: {
    YN: [{ key: 'YES', label: 'yes', colour: '', attr: '', desc: '' }, { key: 'NO', label: 'no', colour: '', attr: '', desc: '' }],
    LINKTYPE: [{ key: 'COVERS', label: 'Covers', colour: '00AA00', attr: 'yes', desc: '' },
      { key: 'CONTEXT', label: 'Context', colour: '', attr: 'no', desc: '' }],
  },
  tables: {
    SD: [{ sd_id: 'MR', title: 'Machinery', edition: '', doc_type: '', lifecycle_status: '', status_date: '', normative_strength: '', legal_link: '', licence_class: '', notes: '' },
      { sd_id: 'TR', title: 'Report', edition: '', doc_type: '', lifecycle_status: '', status_date: '', normative_strength: '', legal_link: '', licence_class: 'Licensed', notes: '' }],
    SP: [sp('MR:1', '', 10), sp('MR:1.1', 'MR:1', 20), sp('MR:1.2(a)', 'MR:1', 30), sp('MR:2', '', 40), sp('TR:5', '', 10)],
    SR: [sr('SR.MR.0001', 'MR:1.1'), sr('SR.MR.0002', 'MR:1.2(a); MR:2'), sr('SR.TR.0001', 'TR:5')],
    CR: [cr('CR.RM.001'), cr('CR.RM.001.1', 'CR.RM.001'), cr('CR.RM.001.2', 'CR.RM.001'), cr('CR.VV.001'),
      cr('CR.VV.002', '', { refines: 'CR.VV.001', refines_full: 'CR.VV.001 [TR]' })],
    LINK_SR_CR: [link('SR.MR.0001', 'CR.RM.001'), link('SR.MR.0002', 'CR.VV.001'), link('SR.MR.0002', 'CR.RM.001.2', 'Context'),
      link('SR.TR.0001', 'CR.VV.002', 'Covers', 'AI.usage_level = A1')],
    CORR: [],
    DECISIONS: [{ dec_id: 'D0001', date: '', author: '', type: '', affected_ids: 'CR.RM.001; SR.MR.0001', rationale: 'see MR:1.2(a).', source_refs: '' }],
  },
}
const ix = buildIndex(DATA)

const ids = (ns: TreeNode[]) => ns.map(n => n.id)
const leaf = (result: boolean | null, extra: Partial<CrEval> = {}): CrEval =>
  ({ leaf: true, leaves: [], expanded: [], substituted_by: [], substitutes: [], result, eff_rule: 'X', unknown: [], ...extra })

describe('index', () => {
  it('builds hierarchies and reverse links', () => {
    expect(ix.spRoots.get('MR')).toEqual(['MR:1', 'MR:2'])
    expect(ix.spChildren.get('MR:1')).toEqual(['MR:1.1', 'MR:1.2(a)'])
    expect(ix.srBySp.get('MR:2')).toEqual(['SR.MR.0002'])
    expect(ix.srSd.get('SR.MR.0002')).toBe('MR')
    expect(ix.crChildren.get('CR.RM.001')).toEqual(['CR.RM.001.1', 'CR.RM.001.2'])
    expect(ix.refinedBy.get('CR.VV.001')).toEqual([{ cr: 'CR.VV.002', full: true, set: 'TR' }])
    expect([...ix.counting]).toEqual(['Covers'])
    expect(decisionsMentioning(ix, 'CR.RM.001').map(d => d.dec_id)).toEqual(['D0001'])
    expect(decisionsMentioning(ix, 'CR.RM.001.1')).toEqual([])
  })
})

describe('document tree', () => {
  it('nests SP > SR > CR, SRs under every referenced SP, counting links only', () => {
    const t = buildDocTree(ix, 'MR')
    expect(ids(t)).toEqual(['MR:1', 'MR:2'])
    const [p1, p2] = t
    expect(ids(p1.children)).toEqual(['MR:1.1', 'MR:1.2(a)'])
    expect(ids(p1.children[0].children)).toEqual(['SR.MR.0001'])
    expect(ids(p1.children[0].children[0].children)).toEqual(['CR.RM.001'])
    expect(ids(p1.children[0].children[0].children[0].children)).toEqual(['CR.RM.001.1', 'CR.RM.001.2'])
    expect(ids(p2.children)).toEqual(['SR.MR.0002'])
    expect(ids(p2.children[0].children)).toEqual(['CR.VV.001'])     // Context link left out
    expect(ids(buildDocTree(ix, 'MR', { allLinks: true })[1].children[0].children)).toEqual(['CR.VV.001', 'CR.RM.001.2'])
  })

  it('shows full refinements as a group in the CR tree', () => {
    const vv1 = buildCrTree(ix).find(n => n.id === 'CR.VV.001')!
    expect(vv1.children.map(c => c.title)).toEqual(['refined fully by [TR]'])
    expect(ids(vv1.children[0].children)).toEqual(['CR.VV.002'])
  })
})

describe('applicability filter', () => {
  const applic: Record<string, CrEval> = {
    'CR.RM.001': { leaf: false, leaves: ['CR.RM.001.1', 'CR.RM.001.2'], expanded: ['CR.RM.001.1', 'CR.RM.001.2'], substituted_by: [], substitutes: [] },
    'CR.RM.001.1': leaf(false), 'CR.RM.001.2': leaf(false), 'CR.VV.001': leaf(null),
  }
  it('hides N/A CRs, their SRs, and provisions left without requirements', () => {
    const t = filterTree(buildDocTree(ix, 'MR', { applic }), { active: true, showNA: false, onlyWithReqs: true })
    expect(ids(t)).toEqual(['MR:1', 'MR:2'])
    expect(ids(t[0].children)).toEqual(['MR:1.2(a)'])                // MR:1.1 lost SR.MR.0001 (all leaves N/A)
    expect(t[1].children[0].children[0].status).toBe('unknown')
  })
  it('keeps N/A items muted when requested', () => {
    const t = filterTree(buildDocTree(ix, 'MR', { applic }), { active: true, showNA: true, onlyWithReqs: false })
    const c = t[0].children[0].children[0].children[0]
    expect([c.id, c.status, c.muted]).toEqual(['CR.RM.001', 'na', true])
  })
})

describe('project tree', () => {
  const ev = {
    seed: { prj: { project_id: 'P00001' }, basis: [], tags: {}, objects: [] },
    tags: {}, basis: [{ sd_id: 'TR' }], missing_sources: [],
    objects: [{ object_id: 'P00001-PRD-01', level: 'PRD' }],
    selection: { sp: ['TR:5'], sr: ['SR.TR.0001'] },
    crs: { 'CR.VV.002': leaf(true), 'CR.VV.001': leaf(true, { substituted_by: ['CR.VV.002'] }) },
    cis: [{ ci_id: 'P00001-PRD-01/CR.VV.002', object_id: 'P00001-PRD-01', level: 'PRD', cr_id: 'CR.VV.002', rule_applicability: 'Applicable', applicability_justification: '' }],
    views: {}, counts: {},
  } as unknown as Evaluation
  it('ends in check items and shows substitution', () => {
    const ctx = projectCtx(ev)
    const t = buildDocTree(ix, 'TR', { project: ctx })
    expect(ids(t[0].children[0].children[0].children)).toEqual(['P00001-PRD-01/CR.VV.002'])
    const crt = buildCrTree(ix, { project: ctx })
    const vv1 = crt.find(n => n.id === 'CR.VV.001')!
    expect([vv1.status, vv1.children[0].title, vv1.children[0].children[0].id]).toEqual(['subst', 'substituted by', 'CR.VV.002'])
  })
})

describe('search, flatten, paths', () => {
  it('keeps matches with their ancestors and opens the path', () => {
    const t = buildDocTree(ix, 'MR')
    const s = searchTree(t, 'rm.001.2')
    expect(s.hits).toBe(1)
    const rows = flatten(s.nodes, k => s.expand.has(k))
    expect(rows.map(r => r.node.id)).toEqual(['MR:1', 'MR:1.1', 'SR.MR.0001', 'CR.RM.001', 'CR.RM.001.2'])
    expect(pathTo(t, 'SR.MR.0002')!.length).toBe(3)
    expect(collectIds(t).has('CR.RM.001.1')).toBe(true)
  })
})

describe('ID links', () => {
  it('finds known IDs in text, trimming SP refs', () => {
    const tok = tokenize(ix, 'See SR.MR.0001, CR.RM.001.2. and (MR:1.2(a)) or D0001; not CR.XX.999 nor MR:9.')
    expect(tok.filter(t => typeof t !== 'string').map(t => (t as { id: string }).id))
      .toEqual(['SR.MR.0001', 'CR.RM.001.2', 'MR:1.2(a)', 'D0001'])
    expect(tok.map(t => (typeof t === 'string' ? t : t.text)).join('')).toBe('See SR.MR.0001, CR.RM.001.2. and (MR:1.2(a)) or D0001; not CR.XX.999 nor MR:9.')
  })
  it('stays in the view when the ID is there, otherwise goes home', () => {
    const ctx: RouteCtx = { mode: 'catalogue', view: 'MR', viewIds: new Set(['CR.RM.001']), search: '?t=a:b' }
    expect(hrefFor(ix, 'CR.RM.001', 'cr', ctx)).toBe('/catalogue/MR?t=a%3Ab&sel=CR.RM.001')
    expect(hrefFor(ix, 'SR.TR.0001', 'sr', ctx)).toBe('/catalogue/TR?t=a%3Ab&sel=SR.TR.0001')
    expect(hrefFor(ix, 'D0001', 'dec', ctx)).toBe('/catalogue/DEC?sel=D0001')
    const p: RouteCtx = { mode: 'project', pid: 'P1', view: 'TR', viewIds: new Set(), search: '', basis: new Set(['TR']) }
    expect(hrefFor(ix, 'MR:1', 'sp', p)).toBe('/catalogue/MR?sel=MR%3A1')
    expect(hrefFor(ix, 'SR.TR.0001', 'sr', p)).toBe('/project/P1/TR?sel=SR.TR.0001')
  })
  it('round-trips tags in the query string', () => {
    const q = writeTags(new URLSearchParams('sel=X'), { 'INT.PL': 'd', 'AI.learning': '' })
    expect(readTags(q)).toEqual({ 'AI.learning': '', 'INT.PL': 'd' })
    expect(q.get('sel')).toBe('X')
  })
})
